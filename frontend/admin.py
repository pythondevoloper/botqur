from django.contrib import admin

from .models import (
    ContactRequest,
    MusobaqaNizom,
    Robot,
    RobotRasm,
    Musobaqa,
    MusobaqaRasm,
    BoshSahifaSozlamalari,
)


@admin.register(ContactRequest)
class ContactRequestAdmin(admin.ModelAdmin):
    """
    Murojaat faqat saytdagi formadan keladi (`views.contact_submit`).

    Admin qo'lda yozuv qo'shsa, ro'yxatda hech kim yubormagan murojaat
    paydo bo'lardi — keyin uni haqiqiysidan ajratib bo'lmaydi. Shuning
    uchun "Qo'shish" tugmasi o'chirilgan, mijoz yuborgan maydonlar esa
    faqat o'qish uchun. Admin boshqaradigan yagona narsa —
    `korib_chiqildi` holati (ro'yxatdan ham belgilash mumkin).
    """

    list_display = ("ism", "telefon", "robot", "yaratilgan", "korib_chiqildi")
    list_filter = ("korib_chiqildi", "yaratilgan")
    search_fields = ("ism", "telefon", "xabar", "robot")
    ordering = ("-yaratilgan",)
    list_editable = ("korib_chiqildi",)
    readonly_fields = ("ism", "telefon", "robot", "xabar", "yaratilgan")

    def has_add_permission(self, request):
        return False


@admin.register(MusobaqaNizom)
class MusobaqaNizomAdmin(admin.ModelAdmin):
    list_display = ("slug", "fayl", "yuklangan")

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        """
        Fayl tanlash oynasida faqat PDF ko'rinadi.

        Bu — qulaylik, tekshiruv emas: `accept` ni brauzerda aylanib
        o'tish oson (fayl tortib tashlash, "Hamma fayllar" ni tanlash).
        Haqiqiy to'siq — modeldagi `nizom_pdf_tekshir` validatori, u
        serverda ishlaydi va aylanib o'tilmaydi.
        """
        formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
        if db_field.name == "fayl" and formfield is not None:
            formfield.widget.attrs["accept"] = "application/pdf,.pdf"
        return formfield


class RobotRasmInline(admin.TabularInline):
    model = RobotRasm
    extra = 1


@admin.register(Robot)
class RobotAdmin(admin.ModelAdmin):
    list_display = ("nomi", "musobaqa", "narxi", "tartib", "faol", "yangilangan")
    list_filter = ("musobaqa", "faol")
    search_fields = ("nomi", "slug")
    prepopulated_fields = {"slug": ("nomi",)}
    inlines = [RobotRasmInline]
    fieldsets = (
        (None, {"fields": ("nomi", "slug", "musobaqa", "narxi", "faol", "tartib")}),
        ("Tavsif", {"fields": ("qisqa_tavsif", "afzalliklari", "qismlari")}),
        ("Media", {"fields": ("muqova_rasm", "video", "model_3d")}),
    )


class MusobaqaRasmInline(admin.TabularInline):
    model = MusobaqaRasm
    extra = 1


@admin.register(Musobaqa)
class MusobaqaAdmin(admin.ModelAdmin):
    list_display = ("slug", "format", "yosh_oraligi", "tartib", "yangilangan")
    inlines = [MusobaqaRasmInline]
    fieldsets = (
        (None, {"fields": ("slug", "format", "yosh_oraligi", "tartib")}),
        ("Tavsif", {"fields": ("tavsif", "jadval", "manzil")}),
        ("Media", {"fields": ("muqova_rasm", "video")}),
    )


@admin.register(BoshSahifaSozlamalari)
class BoshSahifaSozlamalariAdmin(admin.ModelAdmin):
    list_display = ("__str__", "yangilangan")

    def has_add_permission(self, request):
        return not BoshSahifaSozlamalari.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        obj = BoshSahifaSozlamalari.objects.first()
        if obj:
            from django.shortcuts import redirect

            return redirect("admin:frontend_boshsahifasozlamalari_change", obj.pk)
        return super().changelist_view(request, extra_context)
