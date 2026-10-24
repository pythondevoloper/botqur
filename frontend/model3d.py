"""
Yuklangan 3D modelni saytga mos `.obj` ga aylantiradi.

Bu modul admin paneldan fayl yuklanganda ishlaydi (frontend/models.py
dagi `save()` orqali). Maqsadi — foydalanuvchi `.glb` tashlasa ham
ishlasin, chunki saytning frontend'i faqat `OBJLoader` bilan keladi
va uni o'zgartirib bo'lmaydi (manba kod yo'q).

Uch narsa faylga "pishiriladi" — nega keraklgi botqur-3d/README.md da:

  1. Markazlashtirish — `Bot3D` da `position.sub(center)` masshtabdan
     OLDIN qo'llangan, three.js esa matritsani T·R·S tartibida tuzadi.
     Markazni kodning -90°X burilishidan KEYINGI koordinatada nolga
     keltiramiz (oddiy markazlashtirish yetmaydi: burilish AABB
     markazini siljitadi).
  2. Yo'nalish — kod Z-up kutadi; burilishni bekor qilib, modelni
     kameraga qaratib egamiz.
  3. Rang — `.mtl` va teksturalar o'qilmaydi; yagona yo'l — har
     vertexga rang yozish (`v x y z r g b`).
"""
import math
import pathlib
import tempfile

from . import glb_oqish

KAMERA = (2.2, 1.2, 2.6)          # saytdagi Bot3D kamerasi
STANDART_RANG = (245 / 255, 247 / 255, 246 / 255)      # oq — navbar yozuvi bilan bir xil
GLB_KENGAYTMA = (".glb", ".gltf")

# Oldindan burish: Tinkercad OBJ Z-up va teskari chiqadi; glTF allaqachon Y-up.
BURILISH_OBJ = (0.0, 0.0, 180.0)
BURILISH_GLB = (0.0, 0.0, 0.0)


class KonvertXato(Exception):
    """Foydalanuvchiga ko'rsatiladigan, tushunarli xato."""


# ----------------------------------------------------------------- geometriya

def _rodrigues(p, eksen, daraja):
    th = math.radians(daraja)
    c, s = math.cos(th), math.sin(th)
    kx, ky, kz = eksen
    x, y, z = p
    dot = kx * x + ky * y + kz * z
    cr = (ky * z - kz * y, kz * x - kx * z, kx * y - ky * x)
    return tuple(p[i] * c + cr[i] * s + eksen[i] * dot * (1 - c) for i in range(3))


def _euler(p, dx, dy, dz):
    x, y, z = p
    if dx:
        t = math.radians(dx); c, s = math.cos(t), math.sin(t)
        y, z = y * c - z * s, y * s + z * c
    if dy:
        t = math.radians(dy); c, s = math.cos(t), math.sin(t)
        x, z = x * c + z * s, -x * s + z * c
    if dz:
        t = math.radians(dz); c, s = math.cos(t), math.sin(t)
        x, y = x * c - y * s, x * s + y * c
    return (x, y, z)


def _R_kod(p):     x, y, z = p; return (x,  z, -y)     # sayt qo'llaydigan -90°X
def _R_teskari(p): x, y, z = p; return (x, -z,  y)


def _kamera_egilishi():
    n = math.dist((0, 0, 0), KAMERA)
    cd = tuple(c / n for c in KAMERA)
    toliq = math.degrees(math.acos(cd[2]))
    eks = (-cd[1], cd[0], 0.0)
    d = math.hypot(eks[0], eks[1])
    return toliq / 2, (eks[0] / d, eks[1] / d, 0.0)


# ----------------------------------------------------------------- OBJ o'qish

def _obj_oqish(matn):
    V, F = [], []
    for ln in matn.splitlines():
        t = ln.split()
        if not t:
            continue
        if t[0] == "v":
            try:
                V.append((float(t[1]), float(t[2]), float(t[3])))
            except (IndexError, ValueError):
                raise KonvertXato("OBJ faylda buzilgan `v` qatori bor.")
        elif t[0] == "f":
            idx = []
            for qism in t[1:]:
                try:
                    i = int(qism.split("/")[0])
                except ValueError:
                    continue
                idx.append(i - 1 if i > 0 else len(V) + i)
            for k in range(1, len(idx) - 1):
                F.append((idx[0], idx[k], idx[k + 1]))
    if not V:
        raise KonvertXato("Faylda birorta ham vertex topilmadi — bu Wavefront OBJ emas. "
                          "ZIP arxiv yuklagan bo'lsangiz, ichidagi .obj ni yuklang.")
    return V, F


# ----------------------------------------------------------------- asosiy

def obj_matni(V, F, C, burilish, egilish=None):
    """Tayyorlangan geometriyadan OBJ matnini qaytaradi."""
    std_egilish, eks = _kamera_egilishi()
    egilish = std_egilish if egilish is None else egilish
    bx, by, bz = burilish

    tr = [_R_teskari(_rodrigues(_euler(p, bx, by, bz), eks, egilish)) for p in V]

    # markazni KOD burilishidan keyingi koordinatada nolga keltiramiz
    burilgan = [_R_kod(p) for p in tr]
    mark = [(min(v[i] for v in burilgan) + max(v[i] for v in burilgan)) / 2 for i in range(3)]
    off = _R_teskari(tuple(mark))
    tr = [(p[0] - off[0], p[1] - off[1], p[2] - off[2]) for p in tr]

    qatorlar = [
        "# botqur — admin yuklashida avtomatik tayyorlangan\n",
        "o botqur_hero\n",
    ]
    for (x, y, z), (r, g, b) in zip(tr, C):
        qatorlar.append("v %.5f %.5f %.5f %.5f %.5f %.5f\n" % (x, y, z, r, g, b))
    qatorlar.append("g botqur_hero\n")
    # usemtl SHART: usiz three.js OBJLoader material yaratmaydi va vertex
    # ranglar e'tiborga olinmaydi (OBJLoader, "Create materials" bo'limi).
    qatorlar.append("usemtl botqur\n")
    # s 0 = tekis soyalash; `vn` yozmaymiz, three.js normallarni shaderda hisoblaydi.
    qatorlar.append("s 0\n")
    for i, j, k in F:
        qatorlar.append(f"f {i+1} {j+1} {k+1}\n")

    burilgan = [_R_kod(p) for p in tr]
    olcham = [max(v[i] for v in burilgan) - min(v[i] for v in burilgan) for i in range(3)]
    return "".join(qatorlar), {"vertex": len(V), "uchburchak": len(F), "olcham": olcham}


def konvert(nom, baytlar, faqat_tekshir=False):
    """
    (yangi_nom, obj_matni, info) qaytaradi.
    `.obj` kelsa ham qayta tayyorlanadi — markazlashtirish baribir kerak.

    `faqat_tekshir=True` — fayl o'qiladi va tekshiriladi, lekin OBJ
    matni yasalmaydi. `clean()` shu rejimda chaqiradi, chunki unga
    faqat "bu fayl yaroqlimi?" degan javob kerak.
    """
    kengaytma = pathlib.Path(nom).suffix.lower()

    if kengaytma in GLB_KENGAYTMA:
        # glb_oqish fayl yo'li bilan ishlaydi — vaqtincha faylga yozamiz
        with tempfile.NamedTemporaryFile(suffix=kengaytma, delete=True) as tf:
            tf.write(baytlar)
            tf.flush()
            try:
                V, F, C, ginfo = glb_oqish.oqish(pathlib.Path(tf.name))
            except glb_oqish.GlbXato as e:
                raise KonvertXato(f"GLB o'qilmadi: {e}")
        burilish = BURILISH_GLB
        ogoh = []
        if ginfo["teksturali_material"]:
            ogoh.append(
                f"{ginfo['teksturali_material']} ta material tekstura ishlatadi. "
                f"Tekstura 3D ko'rinishda qo'llab-quvvatlanmaydi — ularning o'rniga "
                f"materialning asosiy rangi olindi."
            )
    elif kengaytma == ".obj":
        try:
            matn = baytlar.decode("utf-8", "replace")
        except Exception:
            raise KonvertXato("OBJ fayl matn sifatida o'qilmadi.")
        V, F = _obj_oqish(matn)
        C = [STANDART_RANG] * len(V)
        burilish = BURILISH_OBJ
        ogoh = []
    else:
        raise KonvertXato(
            f"'{kengaytma or nom}' qo'llab-quvvatlanmaydi. "
            f".obj, .glb yoki .gltf yuklang."
        )

    if not F:
        raise KonvertXato("Modelda uchburchak yuzalar yo'q — faqat chiziq yoki nuqta bo'lishi mumkin.")

    if faqat_tekshir:
        return None, None, {"vertex": len(V), "uchburchak": len(F), "ogohlantirish": ogoh}

    matn, info = obj_matni(V, F, C, burilish)
    info["ogohlantirish"] = ogoh

    eng = max(info["olcham"]) or 1
    if min(info["olcham"]) / eng < 0.12:
        ogoh.append("Model juda yassi — aylanganda qirrasiga kelib ko'rinmay qolishi mumkin.")
    if info["uchburchak"] > 50000:
        ogoh.append(f"{info['uchburchak']} uchburchak — telefonda sekinlashishi mumkin.")

    yangi_nom = pathlib.Path(nom).stem + ".obj"
    return yangi_nom, matn, info
