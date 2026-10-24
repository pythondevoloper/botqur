"""
Mavjud (frontendda oldindan mavjud bo'lgan) robotlarni bazaga
urug'lantiradi — shu tufayli admin panelni ochganingizda
ular allaqachon ro'yxatda bo'ladi, qo'lda qayta kiritish shart emas.

Eslatma: rasm/video/3D fayllar bu migratsiya orqali yuklanmaydi
(ular avval ham haqiqiy fayl sifatida mavjud emas edi, faqat
frontendda "agar fayl bo'lsa" degan shartli mantiq bor edi).
Kerak bo'lsa, admin panelda har bir robotga alohida rasm/video/
3D model (.obj) qo'shishingiz mumkin.
"""

from django.db import migrations

ROBOTS = [
    {
        "slug": 'botqur-strike',
        "nomi": 'BotQur Strike',
        "musobaqa": 'robofutbol',
        "narxi": 1450000,
        "qisqa_tavsif": 'Robofutbol nizomiga mos, tezkor va mustahkam korpusli hujumchi robot.',
        "afzalliklari": 'Yuqori tezlik — hujumga moslashtirilgan motor sxemasi\nZarbaga chidamli mustahkam korpus\nAniq boshqarish uchun past reaksiya vaqti',
        "qismlari": "Mikrokontroller platasi\n4x DC motor + g'ildiraklar\nMotor drayveri\nLi-ion batareya + quvvatlash moduli\nKorpus qismlari",
    },
    {
        "slug": 'botqur-guard',
        "nomi": 'BotQur Guard',
        "musobaqa": 'robofutbol',
        "narxi": 1390000,
        "qisqa_tavsif": "Himoyachi roliga mos, past markazli va yuqori manevrli robot to'plami.",
        "afzalliklari": "Past gravitatsiya markazi — ag'darilishga chidamli\nTez yo'nalish o'zgartirish imkoniyati\nTo'siqni oldindan sezuvchi sensor",
        "qismlari": "Mikrokontroller platasi\n4x DC motor + g'ildiraklar\nTo'siq sezish sensori\nLi-ion batareya + quvvatlash moduli\nKorpus qismlari",
    },
    {
        "slug": 'botqur-captain',
        "nomi": 'BotQur Captain',
        "musobaqa": 'robofutbol',
        "narxi": 1690000,
        "qisqa_tavsif": "Kengaytirilgan sensor to'plami bilan jamoa kapitani uchun mo'ljallangan robot.",
        "afzalliklari": 'Kamera moduli orqali maydonni kuzatish\nJamoa strategiyasini boshqarish imkoniyati\nEng yuqori tezlikli motor konfiguratsiyasi',
        "qismlari": 'Mikrokontroller platasi\n4x yuqori tezlikli motor\nKamera moduli\nLi-ion batareya + quvvatlash moduli\nKorpus qismlari',
    },
    {
        "slug": 'botqur-sumo-pro',
        "nomi": 'BotQur Sumo Pro',
        "musobaqa": 'sumo-robot',
        "narxi": 1650000,
        "qisqa_tavsif": 'Sumo-robot ringi uchun kuchli motor va past markazli mustahkam korpus.',
        "afzalliklari": "Yuqori momentli motorlar — kuchli itarish qobiliyati\nMetall korpus — og'irlik markazi past\nRaqib chekkasini aniq sezuvchi infraqizil sensorlar",
        "qismlari": 'Mikrokontroller platasi\n2x yuqori momentli motor\nInfraqizil chekka sensorlari\nMetall korpus qismlari',
    },
    {
        "slug": 'botqur-sumo-mini',
        "nomi": 'BotQur Sumo Mini',
        "musobaqa": 'sumo-robot',
        "narxi": 1190000,
        "qisqa_tavsif": 'Kichik toifadagi sumo musobaqalari uchun yengil va tezkor robot.',
        "afzalliklari": "Yengil korpus — tezkor manevr\nBoshlang'ichlar uchun sodda sozlash\nQulay narx / sifat nisbati",
        "qismlari": 'Mikrokontroller platasi\n2x DC motor\nInfraqizil chekka sensorlari\nYengil korpus qismlari',
    },
    {
        "slug": 'botqur-line-tracer',
        "nomi": 'BotQur Line Tracer',
        "musobaqa": 'chiziq-kuzatuvchi',
        "narxi": 890000,
        "qisqa_tavsif": 'Chiziq kuzatuvchi musobaqalari uchun yuqori aniqlikdagi sensor massivi bilan.',
        "afzalliklari": "5-kanalli sensor — chiziqni aniq kuzatish\nBoshlang'ichlar uchun oson kalibrlash\nBarqaror, silliq harakat",
        "qismlari": "Mikrokontroller platasi\n5-kanalli IQ sensor massivi\n2x DC motor\nKalibrlash qo'llanmasi",
    },
    {
        "slug": 'botqur-line-racer',
        "nomi": 'BotQur Line Racer',
        "musobaqa": 'chiziq-kuzatuvchi',
        "narxi": 1090000,
        "qisqa_tavsif": 'Tezkor toifa uchun kuchliroq motor va kengaytirilgan sensor massivi.',
        "afzalliklari": "8-kanalli sensor — yuqori aniqlik yuqori tezlikda\nKuchliroq motor — tezkor toifa uchun\nMusobaqa nizomiga to'liq mos konfiguratsiya",
        "qismlari": "Mikrokontroller platasi\n8-kanalli IQ sensor massivi\n2x yuqori tezlikli motor\nKalibrlash qo'llanmasi",
    },
]


def seed_robots(apps, schema_editor):
    Robot = apps.get_model("frontend", "Robot")
    for i, r in enumerate(ROBOTS):
        Robot.objects.get_or_create(
            slug=r["slug"],
            defaults={
                "nomi": r["nomi"],
                "musobaqa": r["musobaqa"],
                "narxi": r["narxi"],
                "qisqa_tavsif": r["qisqa_tavsif"],
                "afzalliklari": r["afzalliklari"],
                "qismlari": r["qismlari"],
                "tartib": i,
            },
        )


def remove_seeded_robots(apps, schema_editor):
    Robot = apps.get_model("frontend", "Robot")
    Robot.objects.filter(slug__in=[r["slug"] for r in ROBOTS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("frontend", "0002_robot_robotrasm"),
    ]

    operations = [
        migrations.RunPython(seed_robots, remove_seeded_robots),
    ]
