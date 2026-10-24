"""
Minimal GLB/glTF o'qigich — faqat standart kutubxona.

Nega o'zimiz yozyapmiz: botqur.uz faqat `OBJLoader` bilan keladi,
GLTFLoader bundle'da umuman yo'q. Shuning uchun GLB'ni OBJ'ga
aylantiramiz va material ranglarini vertex rangga pishiramiz.

Nega numpy'siz: bu modul serverda ham (Django yuklash paytida
konvertatsiya uchun) ishlaydi, u yerda numpy o'rnatilmagan va
faqat shu ish uchun prod'ga bog'liqlik qo'shish arzimaydi.

Qo'llab-quvvatlanadi: GLB (binar) va .gltf (JSON + embedded base64),
node ierarxiyasi va transformlari, indekslangan va indekssiz
primitivlar, `baseColorFactor`, `COLOR_0` vertex ranglari.

Qo'llab-quvvatlanmaydi (aniq xato beradi): Draco siqilishi, sparse
accessor. Teksturalar vertex rangga sig'maydi — ularning o'rniga
materialning asosiy rangi olinadi (xato emas, ogohlantirish).
"""
import base64
import json
import pathlib
import struct

# glTF komponent turi → (struct kodi, bayt)
_KOMPONENT = {
    5120: ("b", 1),   # BYTE
    5121: ("B", 1),   # UNSIGNED_BYTE
    5122: ("h", 2),   # SHORT
    5123: ("H", 2),   # UNSIGNED_SHORT
    5125: ("I", 4),   # UNSIGNED_INT
    5126: ("f", 4),   # FLOAT
}
_NORM_MAX = {5120: 127.0, 5121: 255.0, 5122: 32767.0, 5123: 65535.0}
_SON = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}

CHEKLOV_VERTEX = 2_000_000      # mantiqsiz kattalikdan himoya


class GlbXato(Exception):
    pass


# ------------------------------------------------------------- konteyner

def _konteyner(yol: pathlib.Path):
    xom = yol.read_bytes()
    if xom[:4] == b"glTF":
        if len(xom) < 12:
            raise GlbXato("GLB fayli juda kichik — buzilgan bo'lishi mumkin")
        _, versiya, _ = struct.unpack("<III", xom[:12])
        if versiya != 2:
            raise GlbXato(f"glTF {versiya}-versiya qo'llab-quvvatlanmaydi (2 kerak)")
        js = bin_ = None
        off = 12
        while off + 8 <= len(xom):
            uzunlik, turi = struct.unpack("<II", xom[off:off + 8])
            tana = xom[off + 8: off + 8 + uzunlik]
            if len(tana) < uzunlik:
                raise GlbXato("GLB bo'lagi kesilgan — fayl to'liq yuklanmagan bo'lishi mumkin")
            if turi == 0x4E4F534A:          # 'JSON'
                js = json.loads(tana.decode("utf-8"))
            elif turi == 0x004E4942:        # 'BIN'
                bin_ = tana
            off += 8 + uzunlik + (-uzunlik % 4)
        if js is None:
            raise GlbXato("GLB ichida JSON bo'lagi yo'q")
        return js, bin_
    try:
        return json.loads(xom.decode("utf-8")), None
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise GlbXato("fayl na GLB, na .gltf — ichida 'glTF' imzosi ham, JSON ham yo'q")


def _buferlar(js, bin_, yol: pathlib.Path):
    chiqdi = []
    for b in js.get("buffers", []):
        uri = b.get("uri")
        if uri is None:
            if bin_ is None:
                raise GlbXato("bufer GLB binar bo'lagiga ishora qilyapti, lekin u yo'q")
            chiqdi.append(bin_)
        elif uri.startswith("data:"):
            chiqdi.append(base64.b64decode(uri.split(",", 1)[1]))
        else:
            p = yol.parent / uri
            if not p.exists():
                raise GlbXato(f"tashqi bufer topilmadi: {uri} "
                              f"(.gltf o'rniga .glb eksport qiling — hammasi bitta faylda bo'ladi)")
            chiqdi.append(p.read_bytes())
    return chiqdi


# ------------------------------------------------------------- accessor

def _accessor(js, buferlar, idx, normalla=False):
    """Ro'yxatlar ro'yxati qaytaradi: [[x,y,z], ...]"""
    a = js["accessors"][idx]
    if "sparse" in a:
        raise GlbXato("sparse accessor qo'llab-quvvatlanmaydi")
    ct = a["componentType"]
    if ct not in _KOMPONENT:
        raise GlbXato(f"noma'lum componentType: {ct}")
    kod, bayt = _KOMPONENT[ct]
    son = _SON[a["type"]]
    adet = a["count"]
    if adet > CHEKLOV_VERTEX:
        raise GlbXato(f"accessor juda katta ({adet} element)")
    if "bufferView" not in a:
        return [[0.0] * son for _ in range(adet)]

    bv = js["bufferViews"][a["bufferView"]]
    xom = buferlar[bv["buffer"]]
    bosh = bv.get("byteOffset", 0) + a.get("byteOffset", 0)
    zich = son * bayt
    qadam = bv.get("byteStride") or zich
    kerak = bosh + (adet - 1) * qadam + zich
    if kerak > len(xom):
        raise GlbXato("accessor bufer chegarasidan oshdi — fayl buzilgan")

    birlik = struct.Struct("<" + kod * son)
    chiq = [list(birlik.unpack_from(xom, bosh + i * qadam)) for i in range(adet)]

    if normalla and a.get("normalized") and ct in _NORM_MAX:
        m = _NORM_MAX[ct]
        chiq = [[v / m for v in satr] for satr in chiq]
    return chiq


# ------------------------------------------------------------- matritsa

def _birlik():
    return [1.0, 0, 0, 0,  0, 1.0, 0, 0,  0, 0, 1.0, 0,  0, 0, 0, 1.0]


def _kopaytir(A, B):
    """4x4, qator-tartibli."""
    C = [0.0] * 16
    for i in range(4):
        for j in range(4):
            C[i * 4 + j] = sum(A[i * 4 + k] * B[k * 4 + j] for k in range(4))
    return C


def _nuqta(M, p):
    x, y, z = p
    return (
        M[0] * x + M[1] * y + M[2] * z + M[3],
        M[4] * x + M[5] * y + M[6] * z + M[7],
        M[8] * x + M[9] * y + M[10] * z + M[11],
    )


def _node_matritsa(n):
    if "matrix" in n:
        m = n["matrix"]                       # glTF ustun-tartibli → qator-tartibliga
        return [m[0], m[4], m[8],  m[12],
                m[1], m[5], m[9],  m[13],
                m[2], m[6], m[10], m[14],
                m[3], m[7], m[11], m[15]]
    M = _birlik()
    if "scale" in n:
        sx, sy, sz = n["scale"]
        M = _kopaytir([sx, 0, 0, 0,  0, sy, 0, 0,  0, 0, sz, 0,  0, 0, 0, 1], M)
    if "rotation" in n:
        x, y, z, w = n["rotation"]
        R = [1-2*(y*y+z*z), 2*(x*y-z*w),   2*(x*z+y*w),   0,
             2*(x*y+z*w),   1-2*(x*x+z*z), 2*(y*z-x*w),   0,
             2*(x*z-y*w),   2*(y*z+x*w),   1-2*(x*x+y*y), 0,
             0, 0, 0, 1]
        M = _kopaytir(R, M)
    if "translation" in n:
        tx, ty, tz = n["translation"]
        M = _kopaytir([1, 0, 0, tx,  0, 1, 0, ty,  0, 0, 1, tz,  0, 0, 0, 1], M)
    return M


# ------------------------------------------------------------- asosiy

def oqish(yol: pathlib.Path):
    """
    (vertexlar, yuzalar, ranglar, info) qaytaradi.
      vertexlar — [(x,y,z), ...]
      yuzalar   — [(i,j,k), ...]  0 dan boshlanadi
      ranglar   — [(r,g,b), ...]  0..1 sRGB, vertexlar bilan bir xil uzunlikda
    """
    yol = pathlib.Path(yol)
    js, bin_ = _konteyner(yol)

    for kerak in js.get("extensionsRequired", []):
        if "draco" in kerak.lower():
            raise GlbXato("model Draco bilan siqilgan — qo'llab-quvvatlanmaydi. "
                          "Eksport sozlamalarida Draco'ni o'chiring.")
        if "meshopt" in kerak.lower():
            raise GlbXato("model Meshopt bilan siqilgan — qo'llab-quvvatlanmaydi.")

    buferlar = _buferlar(js, bin_, yol)

    mat_rang, teksturali = [], 0
    for m in js.get("materials", []):
        pbr = m.get("pbrMetallicRoughness", {})
        if "baseColorTexture" in pbr:
            teksturali += 1
        f = pbr.get("baseColorFactor", [0.8, 0.8, 0.8, 1.0])
        mat_rang.append((float(f[0]), float(f[1]), float(f[2])))

    V, F, C = [], [], []
    korilgan = set()

    def yurish(ni, ota):
        if ni in korilgan:                    # sikldan himoya
            return
        korilgan.add(ni)
        n = js["nodes"][ni]
        M = _kopaytir(ota, _node_matritsa(n))
        if "mesh" in n:
            for prim in js["meshes"][n["mesh"]].get("primitives", []):
                if prim.get("mode", 4) != 4:  # faqat TRIANGLES
                    continue
                attr = prim.get("attributes", {})
                if "POSITION" not in attr:
                    continue
                taglik = len(V)
                for p in _accessor(js, buferlar, attr["POSITION"]):
                    V.append(_nuqta(M, p))
                sanoq = len(V) - taglik

                if "indices" in prim:
                    tekis = [i[0] for i in _accessor(js, buferlar, prim["indices"])]
                else:
                    tekis = list(range(sanoq))
                for k in range(0, len(tekis) - 2, 3):
                    F.append((taglik + tekis[k], taglik + tekis[k+1], taglik + tekis[k+2]))

                if "COLOR_0" in attr:
                    for c in _accessor(js, buferlar, attr["COLOR_0"], normalla=True):
                        C.append((c[0], c[1], c[2]))
                else:
                    mi = prim.get("material")
                    rang = mat_rang[mi] if mi is not None and mi < len(mat_rang) else (0.8, 0.8, 0.8)
                    C.extend([rang] * sanoq)
        for bola in n.get("children", []):
            yurish(bola, M)

    nodes = js.get("nodes", [])
    sahnalar = js.get("scenes")
    if sahnalar:
        ildizlar = sahnalar[js.get("scene", 0)].get("nodes", [])
    else:
        ildizlar = list(range(len(nodes)))
    for ni in ildizlar:
        yurish(ni, _birlik())

    if not V:
        raise GlbXato("faylda uchburchakli mesh topilmadi "
                      "(faqat chiziq/nuqta yoki bo'sh sahna bo'lishi mumkin)")
    assert len(C) == len(V), f"ichki xato: {len(C)} rang / {len(V)} vertex"
    return V, F, C, {"material": len(mat_rang), "teksturali_material": teksturali}
