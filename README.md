# BotQur

**BotQur** — O'zbekistonda robototexnika va dasturlash bo'yicha ta'lim beruvchi markaz uchun veb-sayt. Sayt ikki qismdan iborat: **Django** backend (admin panel, ma'lumotlar bazasi, API) va **Next.js** frontend (statik eksport qilingan, Django tomonidan shablon sifatida xizmat qiladi).

🔗 Jonli sayt: [botqur.uz](https://botqur.uz)

---

## Mundarija

- [Arxitektura](#arxitektura)
- [Texnologiyalar](#texnologiyalar)
- [Loyiha tuzilishi](#loyiha-tuzilishi)
- [Imkoniyatlar](#imkoniyatlar)
- [Mahalliy (local) o'rnatish](#mahalliy-local-ornatish)
- [Frontend'ni qayta build qilish](#frontendni-qayta-build-qilish)
- [Muhit o'zgaruvchilari (.env)](#muhit-ozgaruvchilari-env)
- [Migratsiyalar](#migratsiyalar)
- [Production'ga joylashtirish](#productionga-joylashtirish)

---

## Arxitektura

Bu loyiha odatiy Django yoki odatiy Next.js loyihasidan farq qiladi — ikkalasi birlashtirilgan:

1. **Next.js** (`frontend-src/` — manba kod) sayt dizayni, animatsiyalari va interaktiv qismlarini (3D robot ko'rinishi, formalar, galereyalar) React orqali yaratadi.
2. Loyiha **statik HTML+JS+CSS** fayllariga eksport qilinadi (`next build`, `output: "export"`).
3. Bu statik fayllar **Django**ning `frontend` ilovasi ichiga (`frontend/templates/`, `frontend/nextassets/`) joylashtiriladi va Django ularni oddiy shablon sifatida qaytaradi.
4. Sahifadagi **dinamik qismlar** (robotlar ro'yxati, musobaqalar, murojaat formasi, nizom fayllari, 3D model) build vaqtida emas, **sahifa ochilgach brauzerda JavaScript orqali** Django REST bo'lmagan oddiy JSON API'lardan (`/api/...`) so'raladi. Shu tufayli admin panelda ma'lumot o'zgartirilganda, **sayt qayta build qilinmasdan** darhol yangilanadi.

```
Brauzer → Nginx → Gunicorn → Django (frontend ilovasi)
                                 ├── HTML shablon qaytaradi (frontend/templates/)
                                 ├── Statik JS/CSS/rasm xizmat qiladi (frontend/nextassets/)
                                 └── JSON API (/api/robotlar/, /api/musobaqalar/, /api/murojaat/ va h.k.)
                                        ↑
                              Sahifadagi JS shu yerdan ma'lumot oladi
```

> **Muhim:** `frontend/templates/` va `frontend/nextassets/` papkalari — Next.js build'ining **natijasi** (avtomatik generatsiya qilinadi), qo'lda tahrirlanmaydi. Ularni Git orqali emas, alohida (zip/`scp`) joylashtirish tavsiya etiladi — sababi [Production'ga joylashtirish](#productionga-joylashtirish) bo'limida.

---

## Texnologiyalar

**Backend**
- Python 3.10+, Django
- SQLite (ma'lumotlar bazasi)
- Gunicorn (WSGI server)

**Frontend**
- Next.js 16 (App Router, statik eksport)
- React, TypeScript
- Tailwind CSS
- Framer Motion (animatsiyalar)
- Three.js / @react-three/fiber (3D robot ko'rinishi, `.obj` format)

**Infratuzilma**
- Nginx (statik fayllar + teskari proksi)
- systemd (Gunicorn xizmatini boshqarish)
- Let's Encrypt (SSL)

---

## Loyiha tuzilishi

```
botqur/
├── manage.py
├── BotQur/                    # Django sozlamalari (settings, urls, wsgi)
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── frontend/                  # Asosiy Django ilovasi
│   ├── models.py              # Robot, Musobaqa, ContactRequest va h.k.
│   ├── admin.py                # Admin panel sozlamalari
│   ├── views.py                # Sahifa va API view'lari
│   ├── urls.py
│   ├── migrations/
│   ├── templates/botqur/      # Next.js build natijasi (HTML)
│   └── nextassets/            # Next.js build natijasi (JS/CSS/rasm)
├── robots/                    # (legacy, ishlatilmaydi)
└── frontend-src/               # Next.js loyihasining MANBA kodi
    ├── src/
    │   ├── app/                # Sahifalar (App Router)
    │   ├── components/         # React komponentlari
    │   └── lib/                 # API funksiyalari, yordamchi kod
    └── public/                  # Statik fayllar (logotip, hero 3D model)
```

---

## Imkoniyatlar

Quyidagi bo'limlar **to'liq admin panel orqali boshqariladi** (qayta build qilish shart emas):

| Bo'lim | Admin manzili | Izoh |
|---|---|---|
| Robotlar | `/admin/frontend/robot/` | Nomi, narxi, tavsifi, rasm galereyasi, video, `.obj` 3D model |
| Musobaqalar | `/admin/frontend/musobaqa/` | Format, yosh oralig'i, tavsif, sana, manzil, galereya |
| Musobaqa nizomlari | `/admin/frontend/musobaqanizom/` | Har bir musobaqa uchun PDF nizom fayli |
| Murojaatlar | `/admin/frontend/contactrequest/` | Saytdan kelgan barcha murojaatlar (ism, telefon, qaysi robot/musobaqa) |

Qo'shimcha:
- **Murojaat formasi** — telefon raqami formatini tekshiradi, robot sahifasida tezkor so'rov oynasi (popover) orqali ham yuboriladi
- **3D robot ko'rinishi** — `.obj` format, avtomatik markazlashtirish/masshtablash, Blender eksportidagi Z-up/Y-up orientatsiya farqini avtomatik tuzatish
- **Bosh sahifadagi hero 3D model** — kodga qattiq yozilgan (statik), admin orqali o'zgartirilmaydi

---

## Mahalliy (local) o'rnatish

### 1. Backend (Django)

```bash
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Sayt: `http://127.0.0.1:8000`, admin panel: `http://127.0.0.1:8000/admin/`

### 2. Frontend (Next.js) — faqat dizayn/kod ustida ishlash uchun

```bash
cd frontend-src
npm install
npm run dev
```

Bu `http://localhost:3000`da **alohida** (Django'siz) ishga tushadi — tez ko'rish/tahrirlash uchun qulay, lekin dinamik ma'lumotlar (`/api/...`) ishlamaydi, chunki Django ishlamayapti.

---

## Frontend'ni qayta build qilish

Har safar `frontend-src/` ichida (dizayn, matn, komponent) o'zgarish qilinganda, statik fayllarni qayta generatsiya qilish kerak:

```bash
cd frontend-src
npm run build
```

Bu `frontend-src/out/` papkasida statik HTML/JS/CSS yaratadi. Shundan so'ng quyidagilarni Django'ning `frontend/` ilovasiga ko'chiring:

| `out/` dagi manba | Django'dagi manzil |
|---|---|
| `out/index.html` | `frontend/templates/botqur/home.html` |
| `out/404.html` | `frontend/templates/botqur/404.html` |
| `out/musobaqalar/<slug>/index.html` | `frontend/templates/botqur/musobaqalar/<slug>.html` |
| `out/robotlar/shell/index.html` | `frontend/templates/botqur/robotlar/shell.html` |
| `out/_next/` | `frontend/nextassets/_next/` |
| `out/brand/` | `frontend/nextassets/brand/` |
| `out/hero/` | `frontend/nextassets/hero/` |
| `out/media/` | `frontend/nextassets/botqur-media/` *(nom almashtiriladi — pastga qarang)* |
| `out/favicon.ico` | `frontend/nextassets/favicon.ico` |

> **Nega `media/` → `botqur-media/`?** Django'ning o'z `MEDIA_URL` (`/media/`) admin panelda yuklangan fayllar (rasm, video, `.obj`, PDF) uchun band. Next.js'ning statik `media/` papkasi bilan nom to'qnashmasligi uchun, barcha HTML fayllar ichidagi `/media/...` havolalari `/botqur-media/...` ga almashtiriladi:
> ```bash
> find frontend/templates -name "*.html" -exec sed -i 's#"/media/#"/botqur-media/#g' {} +
> ```

---

## Muhit o'zgaruvchilari (.env)

Loyiha ildizida (`manage.py` yonida) `.env` fayl yarating:

```
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=uzun-tasodifiy-maxfiy-kalit
DJANGO_ALLOWED_HOSTS=botqur.uz,www.botqur.uz
```

`settings.py` bu qiymatlarni `os.environ.get(...)` orqali o'qiydi.

---

## Migratsiyalar

```bash
python manage.py makemigrations frontend
python manage.py migrate
```

> **Eslatma:** production serverda migratsiya fayllari (`frontend/migrations/*.py`) Git orqali boshqariladi. Yangi migratsiya qo'shilganda, uni **Git'ga commit qilib push qiling** — serverda keyin shunchaki `git pull && python manage.py migrate` kifoya, qayta `makemigrations` ishlatish shart emas (va tavsiya etilmaydi — mos kelmaslik xavfi bor).

---

## Production'ga joylashtirish

Qisqacha oqim (to'liq qo'llanma alohida `DEPLOY.md` faylida):

1. **Backend kodi** (`BotQur/`, `frontend/*.py`, `migrations/`) — Git orqali (`git pull`)
2. **Frontend build natijasi** (`frontend/templates/`, `frontend/nextassets/`) — **Git orqali EMAS**, to'g'ridan-to'g'ri `scp`/zip orqali serverga joylashtiriladi

   Sabab: bu papkalarda o'nlab avtomatik generatsiya qilingan, hash-nomli fayllar bor (masalan `2dpvtt9pc7ayk.css`). Git orqali boshqarish osongina versiyalar mos kelmasligiga (eski HTML + yangi JS yoki aksincha) olib keladi. Shu sabab `.gitignore`ga qo'shilgan:
   ```
   frontend/templates/
   frontend/nextassets/
   ```

3. Fayllarni joylashtirgandan keyin:
   ```bash
   python manage.py migrate
   python manage.py collectstatic --noinput
   sudo systemctl restart gunicorn
   ```

4. Nginx `/var/www/botqur/frontend/nextassets/` ichidagi papkalarni (`_next`, `brand`, `hero`, `botqur-media`) to'g'ridan-to'g'ri (Django orqali emas) xizmat qiladi — tezlik uchun.

---

## Litsenziya

Ichki loyiha — barcha huquqlar BotQur jamoasiga tegishli.
