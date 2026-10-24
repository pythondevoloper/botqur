# 3D maydonlari: .glb/.gltf qabul qilish (yuklashda .obj ga aylantiriladi).
# Faqat validator + yorliq o'zgarishi — bazada hech narsa o'zgarmaydi.

import django.core.validators
from django.db import migrations, models
import frontend.models


class Migration(migrations.Migration):

    dependencies = [
        ('frontend', '0006_boshsahifasozlamalari_contactrequest_robot'),
    ]

    operations = [
        migrations.AlterField(
            model_name='boshsahifasozlamalari',
            name='hero_3d_model',
            field=models.FileField(blank=True, help_text="Bosh sahifaning o'ng tomonidagi katta aylanuvchi robot. Bo'sh qoldirilsa, kodda chizilgan oddiy o'rinbosar robot ko'rinadi. Format: .obj, .glb yoki .gltf. Yuklanganda avtomatik tayyorlanadi — markazlashtiriladi, kameraga qaratiladi, GLB bo'lsa material ranglari saqlanadi. ZIP arxiv yuklamang (ichidagi faylni yuklang).", null=True, upload_to='hero/', validators=[django.core.validators.FileExtensionValidator(['obj', 'glb', 'gltf'])], verbose_name='Bosh sahifadagi 3D robot (.obj / .glb)'),
        ),
        migrations.AlterField(
            model_name='robot',
            name='model_3d',
            field=models.FileField(blank=True, help_text="Ixtiyoriy — yuklansa, robot sahifasida '3D ko'rinish' tugmasi ostida aylantirib ko'rish mumkin bo'ladi. Format: .obj, .glb yoki .gltf. Yuklanganda avtomatik tayyorlanadi — markazlashtiriladi, kameraga qaratiladi, GLB bo'lsa material ranglari saqlanadi. ZIP arxiv yuklamang (ichidagi faylni yuklang).", null=True, upload_to=frontend.models.robot_upload_path, validators=[django.core.validators.FileExtensionValidator(['obj', 'glb', 'gltf'])], verbose_name='3D model (.obj / .glb)'),
        ),
    ]
