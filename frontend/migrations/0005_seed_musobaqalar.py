"""
Mavjud (frontendda oldindan mavjud bo'lgan) 10 ta musobaqa turini
bazaga urug'lantiradi — admin panelni ochganingizda ular
allaqachon ro'yxatda bo'ladi, qo'lda qayta kiritish shart emas.
"""

from django.db import migrations

MUSOBAQALAR = [
    {
        "slug": 'robofutbol',
        "format": 'Jamoaviy, 2+2 robot',
        "yosh_oraligi": '12–16 yosh',
        "tavsif": "Ikki jamoa robotlari to'p bilan o'ynaydi — tezlik, boshqaruv va strategiya sinaladi. Kelajak Muhandislari festivalining rasmiy turlaridan biri.",
        "jadval": "Sana tasdiqlanmoqda — tez orada e'lon qilinadi",
        "manzil": 'Toshkent shahri',
        "tartib": 0,
    },
    {
        "slug": 'robocoding',
        "format": 'Sport dasturlash (ACM qoidalari)',
        "yosh_oraligi": "O'quvchi va talabalar",
        "tavsif": "Kelajak Muhandislari doirasida o'tkaziladigan sport dasturlash musobaqasi — saralash bosqichi va Toshkentdagi final. Robot to'plami talab qilinmaydi, faqat dasturlash ko'nikmasi.",
        "jadval": 'Saralash bosqichi onlayn, final — Toshkentda',
        "manzil": 'Toshkent shahri (final bosqich)',
        "tartib": 1,
    },
    {
        "slug": 'sumo-robot',
        "format": 'Individual, avtonom robot',
        "yosh_oraligi": '12–16 yosh',
        "tavsif": 'Ikki avtonom robot ringda bir-birini chetga chiqarishga harakat qiladi — sensor va strategiya muhim.',
        "jadval": "Sana tasdiqlanmoqda — tez orada e'lon qilinadi",
        "manzil": 'Toshkent shahri',
        "tartib": 2,
    },
    {
        "slug": 'chiziq-kuzatuvchi',
        "format": 'Individual',
        "yosh_oraligi": '12–17 yosh',
        "tavsif": "Robot belgilangan chiziq bo'ylab eng tez va aniq harakatlanishi kerak bo'lgan klassik musobaqa turi (Line Following).",
        "jadval": "Sana tasdiqlanmoqda — tez orada e'lon qilinadi",
        "manzil": 'Toshkent shahri',
        "tartib": 3,
    },
    {
        "slug": 'robo-war',
        "format": 'Jamoaviy, jangovar robot',
        "yosh_oraligi": '14–18 yosh',
        "tavsif": 'Ikki jamoaning boshqariladigan jangovar robotlari ringda bir-biriga qarshi kurashadi — mustahkamlik, quvvat va taktika hal qiluvchi omil.',
        "jadval": "Sana tasdiqlanmoqda — tez orada e'lon qilinadi",
        "manzil": 'Toshkent shahri',
        "tartib": 4,
    },
    {
        "slug": 'robot-sapyor',
        "format": 'Individual, masofadan boshqariluvchi robot',
        "yosh_oraligi": '14–18 yosh',
        "tavsif": "Robot maxsus poligonda shartli portlovchi buyumni aniqlab, uni zararsizlantirish yoki xavfsiz joyga olib chiqishi kerak bo'lgan amaliy-texnik musobaqa turi.",
        "jadval": "Sana tasdiqlanmoqda — tez orada e'lon qilinadi",
        "manzil": 'Toshkent shahri',
        "tartib": 5,
    },
    {
        "slug": 'gumanoid-robotlar',
        "format": 'Individual, insonsimon robot',
        "yosh_oraligi": '14–18 yosh',
        "tavsif": "Ikki oyoqli yoki insonsimon konstruksiyaga ega robotlar yurish, muvozanat saqlash va belgilangan topshiriqlarni bajarish bo'yicha baholanadi.",
        "jadval": "Sana tasdiqlanmoqda — tez orada e'lon qilinadi",
        "manzil": 'Toshkent shahri',
        "tartib": 6,
    },
    {
        "slug": 'suv-roboti',
        "format": 'Individual, suv osti/usti roboti',
        "yosh_oraligi": '14–18 yosh',
        "tavsif": "Suv havzasida harakatlanuvchi robot belgilangan marshrut bo'ylab suzishi yoki suv ostidagi topshiriqlarni bajarishi kerak bo'lgan musobaqa turi.",
        "jadval": "Sana tasdiqlanmoqda — tez orada e'lon qilinadi",
        "manzil": 'Toshkent shahri',
        "tartib": 7,
    },
    {
        "slug": 'first-global-decode',
        "format": 'Jamoaviy (FTC formati)',
        "yosh_oraligi": '14–18 yosh',
        "tavsif": "FIRST Tech Challenge xalqaro formatiga mos jamoaviy robot musobaqasi — g'ildirakli robotlar maydonda ballar to'plash uchun aniq topshiriqlarni bajaradi.",
        "jadval": "Sana tasdiqlanmoqda — tez orada e'lon qilinadi",
        "manzil": 'Toshkent shahri',
        "tartib": 8,
    },
    {
        "slug": 'robo-mission',
        "format": 'Jamoaviy (WRO uslubida)',
        "yosh_oraligi": '10–16 yosh',
        "tavsif": 'World Robot Olympiad uslubidagi missiya-asosli musobaqa — robot maydondagi bir necha topshiriqni belgilangan vaqt ichida ketma-ket bajaradi.',
        "jadval": "Sana tasdiqlanmoqda — tez orada e'lon qilinadi",
        "manzil": 'Toshkent shahri',
        "tartib": 9,
    },
]


def seed_musobaqalar(apps, schema_editor):
    Musobaqa = apps.get_model("frontend", "Musobaqa")
    for m in MUSOBAQALAR:
        Musobaqa.objects.get_or_create(
            slug=m["slug"],
            defaults={k: v for k, v in m.items() if k != "slug"},
        )


def remove_seeded_musobaqalar(apps, schema_editor):
    Musobaqa = apps.get_model("frontend", "Musobaqa")
    Musobaqa.objects.filter(slug__in=[m["slug"] for m in MUSOBAQALAR]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("frontend", "0004_musobaqa_musobaqarasm"),
    ]

    operations = [
        migrations.RunPython(seed_musobaqalar, remove_seeded_musobaqalar),
    ]
