# Bazada allaqachon saqlangan 3D fayllarni saytga mos .obj ga aylantiradi.
#
# Kerak, chunki aylantirish YUKLASH paytida bo'ladi (`_committed is False`
# bo'lganda). Deploy'dan oldin yuklangan .glb fayllar bazada xom holda
# yotadi va sahifada ko'rinmaydi — ularni bir marta shu skript tozalaydi.
#
# Ishlatish:  venv/bin/python manage.py shell < konvert_mavjud.py
import pathlib

from django.core.files.base import ContentFile

from frontend import model3d
from frontend.models import BoshSahifaSozlamalari, Robot


def tozala(obj, maydon, nom):
    f = getattr(obj, maydon, None)
    if not f or not f.name:
        print(f"  {nom}: fayl yo'q, o'tkazildi")
        return False
    if f.name.lower().endswith(".obj"):
        print(f"  {nom}: allaqachon .obj ({f.name})")
        return False
    try:
        f.open("rb")
        baytlar = f.read()
    except FileNotFoundError:
        print(f"  {nom}: XATO — fayl diskda yo'q ({f.name})")
        return False
    finally:
        try:
            f.close()
        except Exception:
            pass

    try:
        yangi, matn, info = model3d.konvert(f.name, baytlar)
    except model3d.KonvertXato as e:
        print(f"  {nom}: XATO — {e}")
        return False

    eski = f.name
    f.save(pathlib.Path(yangi).name, ContentFile(matn.encode("utf-8")), save=False)
    obj.save()
    print(f"  {nom}: {eski}  ->  {f.name}")
    print(f"           {info['vertex']} vertex, {info['uchburchak']} uchburchak")
    for o in info.get("ogohlantirish", []):
        print(f"           ! {o}")
    return True


print("\n== Bosh sahifa ==")
s = BoshSahifaSozlamalari.objects.first()
if s:
    tozala(s, "hero_3d_model", "hero_3d_model")
else:
    print("  sozlama yozuvi yo'q")

print("\n== Robotlar ==")
topildi = False
for r in Robot.objects.all():
    if r.model_3d and r.model_3d.name:
        topildi = True
        tozala(r, "model_3d", r.slug)
if not topildi:
    print("  3D modelli robot yo'q")
print()
