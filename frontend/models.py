from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.validators import FileExtensionValidator
from django.db import models

from . import model3d

# Admin'da qabul qilinadigan 3D formatlar. `.glb`/`.gltf` yuklanganda
# yuklash paytida `.obj` ga aylantiriladi — saytning frontend'i faqat
# three.js OBJLoader bilan keladi va uni o'zgartirib bo'lmaydi.
MODEL3D_KENGAYTMALAR = ["obj", "glb", "gltf"]

MODEL3D_HELP = (
    "Format: .obj, .glb yoki .gltf. Yuklanganda avtomatik tayyorlanadi — "
    "markazlashtiriladi, kameraga qaratiladi, GLB bo'lsa material ranglari "
    "saqlanadi. ZIP arxiv yuklamang (ichidagi faylni yuklang)."
)


def _3d_tayyorla(instance, maydon):
    """
    Yangi yuklangan 3D faylni saytga mos `.obj` ga aylantiradi.

    `_committed is False` — Django'ning o'zi ishlatadigan belgi: fayl
    tayinlangan, lekin hali omborga yozilmagan. Ya'ni bu aynan yangi
    yuklangan fayl; allaqachon saqlanganini qayta ishlamaymiz.
    """
    f = getattr(instance, maydon, None)
    if not f or getattr(f, "_committed", True):
        return None
    f.file.seek(0)
    baytlar = f.file.read()
    nom, matn, info = model3d.konvert(f.name, baytlar)
    f.save(nom, ContentFile(matn.encode("utf-8")), save=False)
    return info


class Model3DAralashmasi:
    """`clean()` da tekshiradi, `save()` da aylantiradi.

    Ikkiga bo'lish sababi: `clean()` dagi ValidationError admin'da
    chiroyli qizil xabar bo'lib chiqadi, `save()` dagisi esa 500 beradi.
    Dasturiy (admin'siz) saqlashda ham ishlashi uchun `save()` da ham
    bor — u holda xato oddiy istisno sifatida ko'tariladi.
    """

    MODEL3D_MAYDON = None

    def clean(self):
        super().clean()
        maydon = self.MODEL3D_MAYDON
        f = getattr(self, maydon, None)
        if not f or getattr(f, "_committed", True):
            return
        f.file.seek(0)
        try:
            model3d.konvert(f.name, f.file.read(), faqat_tekshir=True)
        except model3d.KonvertXato as e:
            raise ValidationError({maydon: str(e)})
        finally:
            f.file.seek(0)

    def save(self, *args, **kwargs):
        _3d_tayyorla(self, self.MODEL3D_MAYDON)
        return super().save(*args, **kwargs)



class ContactRequest(models.Model):
    """Bosh sahifadagi 'Murojaat yuborish' formasidan yoki robot
    sahifasidagi tezkor so'rov oynasidan kelgan ma'lumot."""

    ism = models.CharField("Ism", max_length=150)
    telefon = models.CharField("Telefon", max_length=32)
    xabar = models.TextField("Xabar", blank=True)
    robot = models.CharField(
        "Qaysi robot haqida",
        max_length=150,
        blank=True,
        help_text="Agar so'rov robot sahifasidan yuborilgan bo'lsa, shu yerda ko'rinadi.",
    )

    yaratilgan = models.DateTimeField("Yuborilgan vaqti", auto_now_add=True)
    korib_chiqildi = models.BooleanField("Ko'rib chiqildi", default=False)

    class Meta:
        verbose_name = "Murojaat"
        verbose_name_plural = "Murojaatlar"
        ordering = ["-yaratilgan"]

    def __str__(self):
        return f"{self.ism} — {self.telefon}"


# Musobaqa slug'lari — frontend (Next.js) tomonidagi
# src/lib/mock-data.ts bilan bir xil bo'lishi shart, aks holda
# nizom sahifada ko'rinmaydi. Yangi musobaqa qo'shilsa, ikkala
# joyda ham (bu yerda va mock-data.ts'da) qo'shish kerak.
MUSOBAQA_CHOICES = [
    ("robofutbol", "Robofutbol"),
    ("robocoding", "Robo Coders"),
    ("sumo-robot", "Robo Sumo"),
    ("chiziq-kuzatuvchi", "Chiziq bo'ylab yurish"),
    ("robo-war", "Robo War"),
    ("robot-sapyor", "Robot Sapyor"),
    ("gumanoid-robotlar", "Gumanoid robotlar"),
    ("suv-roboti", "Suv roboti"),
    ("first-global-decode", "First Global Decode"),
    ("robo-mission", "Robo Mission"),
]


# Nizom hujjati faqat PDF bo'ladi — sayt uni brauzerda ochib beradi,
# boshqa format esa yuklab olish tugmasini ishdan chiqaradi.
NIZOM_KENGAYTMA = "pdf"

NIZOM_HELP = (
    "Faqat PDF (.pdf). Word, rasm yoki ZIP qabul qilinmaydi — "
    "hujjatni avval PDF ga saqlab, so'ng yuklang."
)


def _bosh_baytlar(fayl, n=5):
    """
    Fayl boshidan `n` bayt o'qiydi va kursorni joyiga qaytaradi.

    Kursorni qaytarish shart: Django keyin faylni shu joydan o'qib
    saqlaydi, qaytarmasak omborga birinchi baytlari yo'q fayl tushadi.
    O'qib bo'lmasa (ombordagi eski fayl, yopilgan deskriptor) `None`
    qaytaradi — bunda imzo tekshiruvi o'tkazib yuboriladi.
    """
    try:
        joy = fayl.tell()
    except Exception:
        joy = 0
    try:
        fayl.seek(0)
        return fayl.read(n)
    except Exception:
        return None
    finally:
        try:
            fayl.seek(joy)
        except Exception:
            pass


def nizom_pdf_tekshir(fayl):
    """
    Nizom maydoniga faqat haqiqiy PDF o'tishini ta'minlaydi.

    Kengaytmaning o'zi yetarli emas — `.docx` ni `.pdf` deb qayta
    nomlash kifoya bo'lib qolardi. Shuning uchun faylning birinchi
    baytlari ham tekshiriladi: har bir PDF `%PDF-` bilan boshlanadi
    (PDF 32000-1, 7.5.2 "File Header").
    """
    nom = (getattr(fayl, "name", "") or "").lower()
    kengaytma = nom.rsplit(".", 1)[-1] if "." in nom else ""

    if kengaytma != NIZOM_KENGAYTMA:
        raise ValidationError(
            "Faqat PDF fayl yuklash mumkin "
            "(yuklangani: %(kengaytma)s). Hujjatni PDF ga saqlab qayta urinib ko'ring.",
            code="nizom_kengaytma",
            params={"kengaytma": f".{kengaytma}" if kengaytma else "kengaytmasiz fayl"},
        )

    bosh = _bosh_baytlar(fayl)
    if bosh is not None and not bosh.startswith(b"%PDF-"):
        raise ValidationError(
            "Fayl nomi .pdf, lekin ichi PDF emas. Haqiqiy PDF hujjat yuklang.",
            code="nizom_imzo",
        )


class MusobaqaNizom(models.Model):
    """
    Musobaqa nizomi (qoidalar hujjati, odatda PDF).

    Admin panelda fayl yuklansa, tegishli musobaqa sahifasida
    "Nizomni yuklab olish" tugmasi avtomatik faollashadi (frontend
    buni JS orqali /api/nizom/<slug>/ dan so'rab oladi).
    """

    slug = models.CharField(
        "Musobaqa", max_length=64, choices=MUSOBAQA_CHOICES, unique=True
    )
    fayl = models.FileField(
        "Nizom fayli (PDF)",
        upload_to="nizomlar/",
        validators=[nizom_pdf_tekshir],
        help_text=NIZOM_HELP,
    )
    yuklangan = models.DateTimeField("Yuklangan vaqti", auto_now=True)

    class Meta:
        verbose_name = "Musobaqa nizomi"
        verbose_name_plural = "Musobaqa nizomlari"

    def __str__(self):
        return self.get_slug_display()


def robot_upload_path(instance, filename):
    slug = instance.slug if isinstance(instance, Robot) else instance.robot.slug
    return f"robotlar/{slug}/{filename}"


class Robot(Model3DAralashmasi, models.Model):
    """
    Robot to'plami — admin panelda boshqariladi, frontendda avtomatik
    ko'rinadi (bosh sahifadagi ro'yxatda va /robotlar/<slug>/ sahifasida).
    """

    slug = models.SlugField(
        "Slug (URL uchun)",
        max_length=64,
        unique=True,
        help_text="Lotin harflari, raqam va chiziqcha. Masalan: botqur-strike",
    )
    nomi = models.CharField("Nomi", max_length=150)
    musobaqa = models.CharField("Musobaqa", max_length=64, choices=MUSOBAQA_CHOICES)
    narxi = models.PositiveIntegerField("Narxi (so'm)")
    qisqa_tavsif = models.TextField("Qisqa tavsif")
    afzalliklari = models.TextField(
        "Afzalliklari",
        help_text="Har bir afzallikni alohida qatorga yozing.",
        blank=True,
    )
    qismlari = models.TextField(
        "To'plam tarkibi (qismlari)",
        help_text="Har bir qismni alohida qatorga yozing.",
        blank=True,
    )

    muqova_rasm = models.ImageField(
        "Muqova rasmi", upload_to=robot_upload_path, blank=True, null=True
    )
    video = models.FileField(
        "Video (mp4)",
        upload_to=robot_upload_path,
        blank=True,
        null=True,
        help_text="Ixtiyoriy — galereyaning birinchi katagida ko'rinadi.",
    )
    model_3d = models.FileField(
        "3D model (.obj / .glb)",
        upload_to=robot_upload_path,
        blank=True,
        null=True,
        validators=[FileExtensionValidator(MODEL3D_KENGAYTMALAR)],
        help_text=(
            "Ixtiyoriy — yuklansa, robot sahifasida '3D ko'rinish' "
            "tugmasi ostida aylantirib ko'rish mumkin bo'ladi. " + MODEL3D_HELP
        ),
    )

    faol = models.BooleanField(
        "Saytda ko'rinsin", default=True, help_text="O'chirilsa, sayt sahifasidan yashiriladi."
    )
    tartib = models.PositiveIntegerField(
        "Tartib raqami", default=0, help_text="Kichik raqam avval ko'rinadi."
    )

    yaratilgan = models.DateTimeField("Yaratilgan vaqti", auto_now_add=True)
    yangilangan = models.DateTimeField("Yangilangan vaqti", auto_now=True)

    MODEL3D_MAYDON = "model_3d"

    class Meta:
        verbose_name = "Robot"
        verbose_name_plural = "Robotlar"
        ordering = ["tartib", "nomi"]

    def __str__(self):
        return self.nomi

    def afzalliklari_royxati(self):
        return [s.strip() for s in self.afzalliklari.splitlines() if s.strip()]

    def qismlari_royxati(self):
        return [s.strip() for s in self.qismlari.splitlines() if s.strip()]


class RobotRasm(models.Model):
    """Robot galereyasidagi qo'shimcha rasmlar (muqovadan tashqari)."""

    robot = models.ForeignKey(Robot, related_name="rasmlar", on_delete=models.CASCADE)
    rasm = models.ImageField("Rasm", upload_to=robot_upload_path)
    tartib = models.PositiveIntegerField("Tartib raqami", default=0)

    class Meta:
        verbose_name = "Robot rasmi"
        verbose_name_plural = "Robot rasmlari"
        ordering = ["tartib", "id"]

    def __str__(self):
        return f"{self.robot.nomi} — rasm #{self.tartib}"


def musobaqa_upload_path(instance, filename):
    slug = instance.slug if isinstance(instance, Musobaqa) else instance.musobaqa.slug
    return f"musobaqalar/{slug}/{filename}"


class Musobaqa(models.Model):
    """
    Musobaqa turi haqida to'liq ma'lumot (bosh sahifadagi va
    /musobaqalar/<slug>/ sahifasidagi kontent) — admin paneldan
    boshqariladi.
    """

    slug = models.CharField(
        "Musobaqa", max_length=64, choices=MUSOBAQA_CHOICES, unique=True
    )
    format = models.CharField(
        "Format", max_length=150, help_text="Masalan: Jamoaviy, 2+2 robot"
    )
    yosh_oraligi = models.CharField(
        "Yosh oralig'i", max_length=100, help_text="Masalan: 12–16 yosh"
    )
    tavsif = models.TextField("Tavsif")
    jadval = models.CharField(
        "Sana / jadval",
        max_length=200,
        help_text="Masalan: Sana tasdiqlanmoqda — tez orada e'lon qilinadi",
    )
    manzil = models.CharField("Manzil", max_length=200)

    muqova_rasm = models.ImageField(
        "Muqova rasmi", upload_to=musobaqa_upload_path, blank=True, null=True
    )
    video = models.FileField(
        "Video (mp4)",
        upload_to=musobaqa_upload_path,
        blank=True,
        null=True,
        help_text="Ixtiyoriy — galereyaning birinchi katagida ko'rinadi.",
    )

    tartib = models.PositiveIntegerField(
        "Tartib raqami", default=0, help_text="Kichik raqam avval ko'rinadi."
    )

    yangilangan = models.DateTimeField("Yangilangan vaqti", auto_now=True)

    class Meta:
        verbose_name = "Musobaqa"
        verbose_name_plural = "Musobaqalar"
        ordering = ["tartib"]

    def __str__(self):
        return self.get_slug_display()


class MusobaqaRasm(models.Model):
    """Musobaqa galereyasidagi qo'shimcha rasmlar (muqovadan tashqari)."""

    musobaqa = models.ForeignKey(
        Musobaqa, related_name="rasmlar", on_delete=models.CASCADE
    )
    rasm = models.ImageField("Rasm", upload_to=musobaqa_upload_path)
    tartib = models.PositiveIntegerField("Tartib raqami", default=0)

    class Meta:
        verbose_name = "Musobaqa rasmi"
        verbose_name_plural = "Musobaqa rasmlari"
        ordering = ["tartib", "id"]

    def __str__(self):
        return f"{self.musobaqa.get_slug_display()} — rasm #{self.tartib}"


class BoshSahifaSozlamalari(Model3DAralashmasi, models.Model):
    """
    Bosh sahifaning umumiy (yagona) sozlamalari — hozircha faqat
    hero bo'limidagi katta 3D robot modeli. Kelajakda shu yerga
    boshqa umumiy sozlamalar ham qo'shilishi mumkin.

    Bu "singleton" model — bazada faqat BITTA yozuv bo'ladi (admin
    panelda "qo'shish" tugmasi ikkinchi marta ko'rinmaydi).
    """

    hero_3d_model = models.FileField(
        "Bosh sahifadagi 3D robot (.obj / .glb)",
        upload_to="hero/",
        blank=True,
        null=True,
        validators=[FileExtensionValidator(MODEL3D_KENGAYTMALAR)],
        help_text=(
            "Bosh sahifaning o'ng tomonidagi katta aylanuvchi robot. "
            "Bo'sh qoldirilsa, kodda chizilgan oddiy o'rinbosar robot "
            "ko'rinadi. " + MODEL3D_HELP
        ),
    )

    yangilangan = models.DateTimeField("Yangilangan vaqti", auto_now=True)

    class Meta:
        verbose_name = "Bosh sahifa sozlamalari"
        verbose_name_plural = "Bosh sahifa sozlamalari"

    def __str__(self):
        return "Bosh sahifa sozlamalari"

    MODEL3D_MAYDON = "hero_3d_model"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def olish(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
