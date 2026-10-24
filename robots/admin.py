from django.contrib import admin
from .models import RobotKit, KitComponent, Competition


class KitComponentInline(admin.TabularInline):
    model = KitComponent
    extra = 1

@admin.register(RobotKit)
class RobotKitAdmin(admin.ModelAdmin):
    list_display = ('name', 'competition', 'price_uzs', 'stock_quantity', 'is_active')
    inlines = [KitComponentInline]


@admin.register(Competition)
class CompetitionAdmin(admin.ModelAdmin):
    list_display = ('name', 'format_label', 'is_active')


admin.site.site_header = "Robot Competition Boshqaruv Paneli"
admin.site.site_title = "Robot Admin"
admin.site.index_title = "Boshqaruv Tizimiga Xush Kelibsiz"