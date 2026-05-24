# Texnik Topshiriq (TZ)
## OSINT MVP — Ochiq Manba Razvedka Tizimi

**Versiya:** 1.0  
**Sana:** 2026-05-24  
**Holat:** Bajarilgan (MVP)

---

## 1. Loyiha haqida umumiy ma'lumot

**OSINT MVP** — bu foydalanuvchining raqamli izini ochiq manbalarda qidirish, to'plash va sun'iy intellekt yordamida tahlil qilish uchun mo'ljallangan veb-ilova.

Tizim 11 ta ijtimoiy tarmoq va platforma bo'yicha parallel ravishda ma'lumot to'playdi, IP-manzil, telefon raqam, email va rasmlar bo'yicha qidiruvlar o'tkazadi hamda barcha topilmalarni Google Gemini AI yordamida o'zbek tilida razvedka hisoboti ko'rinishida taqdim etadi.

---

## 2. Texnik stek

| Qatlam | Texnologiya |
|--------|-------------|
| Backend | Python 3.11, FastAPI, Uvicorn |
| Ma'lumotlar bazasi | SQLite + SQLAlchemy 2.0 (async) + aiosqlite |
| Autentifikatsiya | JWT (HS256, 7 kun) + bcrypt |
| HTTP klient | httpx (async) |
| AI tahlil | Google Gemini API (gemini-2.5-pro va boshqalar) |
| Frontend | Vanilla HTML/CSS/JavaScript (SPA, ~1060 qator) |
| Xarita | Leaflet.js + OpenStreetMap |
| Email tekshiruv | holehe, dnspython, phonenumbers, Pillow |
| Deploy | Docker + Docker Compose |

---

## 3. Fayl tuzilmasi

```
OSINT/
├── app/
│   ├── main.py                   # FastAPI ilovasi, asosiy endpointlar
│   ├── auth.py                   # JWT, bcrypt, foydalanuvchi tekshiruvi
│   ├── db.py                     # Asinxron SQLAlchemy engine
│   ├── models.py                 # User, SearchHistory ORM modellari
│   ├── schemas.py                # Pydantic sxemalari
│   ├── collectors/               # 11 ta ijtimoiy tarmoq kollektori
│   │   ├── github.py
│   │   ├── gitlab.py
│   │   ├── linkedin.py
│   │   ├── instagram.py
│   │   ├── twitter.py
│   │   ├── tiktok.py
│   │   ├── youtube.py
│   │   ├── telegram.py
│   │   ├── pinterest.py
│   │   ├── steam.py
│   │   ├── hackernews.py
│   │   └── web_footprint.py      # DuckDuckGo dork qidiruvi
│   ├── lookup/                   # Maxsus qidiruvlar
│   │   ├── ip.py
│   │   ├── phone.py
│   │   ├── email_lookup.py
│   │   ├── holehe_check.py
│   │   └── image.py
│   └── routers/
│       ├── auth_router.py
│       ├── history_router.py
│       ├── profile_router.py
│       └── ai_router.py
├── static/
│   └── index.html                # SPA frontend
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

---

## 4. Ma'lumotlar bazasi modellari

### 4.1 User
```
id              INTEGER  PRIMARY KEY
username        VARCHAR(50)   UNIQUE, INDEX
email           VARCHAR(100)  UNIQUE, INDEX
hashed_password VARCHAR(255)
created_at      DATETIME      server default
```

### 4.2 SearchHistory
```
id          INTEGER  PRIMARY KEY
user_id     INTEGER  FK → users (cascade delete), INDEX
search_type VARCHAR(20)   (username / ip / phone / email / holehe / image / profile)
query       VARCHAR(500)
result      TEXT          (JSON formatida)
searched_at DATETIME      server default, INDEX
```

---

## 5. API endpointlari

### 5.1 Autentifikatsiya `/auth`

| Metod | Yo'l | Tavsif |
|-------|------|--------|
| POST | `/auth/register` | Ro'yxatdan o'tish (username, email, password) |
| POST | `/auth/login` | Kirish → JWT token |
| GET | `/auth/me` | Joriy foydalanuvchi ma'lumoti |

**Qoidalar:**
- Parol: kamida 6 belgi
- Username: 3–50 belgi
- Token muddati: 7 kun
- Saqlash: `localStorage['osint_token']`

---

### 5.2 Qidiruvlar (asosiy)

| Metod | Yo'l | Parametr | Tavsif |
|-------|------|----------|--------|
| GET | `/search` | `username` | 11 ta platforma bo'yicha parallel qidiruv |
| GET | `/profile` | `username` | To'liq profil: ijtimoiy + web + email pivot |
| GET | `/ip` | `address` | IP geolokatsiya (ip-api.com) |
| GET | `/phone` | `number` | Telefon tahlili (phonenumbers) |
| GET | `/email` | `address` | Email tekshiruvi (MX + SMTP + Gravatar + EmailRep) |
| GET | `/holehe` | `email` | 120+ xizmatda email qidiruvi |
| GET | `/image` | `url` | EXIF tahlil + teskari qidiruv linklari |

**Eslatma:** Autentifikatsiya ixtiyoriy. Kirgan foydalanuvchilar uchun barcha natijalar tarixga saqlanadi.

---

### 5.3 Tarix `/history`

| Metod | Yo'l | Tavsif |
|-------|------|--------|
| GET | `/history/` | Qidiruv tarixi (limit, offset, search_type filtri) |
| DELETE | `/history/{id}` | Bitta yozuvni o'chirish |

**Talab:** JWT token majburiy.

---

### 5.4 AI tahlil `/ai`

| Metod | Yo'l | Tavsif |
|-------|------|--------|
| POST | `/ai/analyze` | JSON profil → streaming razvedka hisoboti |

**AI tizimi:**
- Model zanjiri: `gemini-2.5-pro → gemini-2.5-flash → gemini-2.0-flash → gemini-1.5-flash`
- Rate limit (429) yoki overload (503) bo'lsa keyingi modelga o'tadi
- Temperature: 0.4
- Javob: **doim o'zbek tilida**
- Uzatish: HTTP streaming (Server-Sent Events uslubi)

**Hisobot bo'limlari (o'zbek tilida):**
1. Umumiy Xulosa
2. Kuchli Korrelyatsiyalar
3. Mumkin bo'lgan Shaxs Signallari
4. Xatti-harakatlar Tahlili
5. Texnik Signallar
6. Ijtimoiy Iz
7. Zaif / Ishonchsiz Natijalar
8. Qarama-qarshiliklar yoki Noaniqliklar
9. Keyingi Tavsiya Etilgan Qadamlar

---

## 6. Kollektorlar

Barcha kollektorlar `asyncio.gather()` orqali parallel ishga tushiriladi.

| Kollector | Manba | Ma'lumotlar |
|-----------|-------|-------------|
| GitHub | api.github.com | Ism, bio, followers, repos, joylashuv, email, Twitter |
| GitLab | gitlab.com/api/v4 | Ism, bio, avatar, veb-sayt, joylashuv |
| LinkedIn | linkedin.com | Ism, bio, avatar (meta teglari) |
| Instagram | instagram.com | Mavjudligi (JS-render cheklov) |
| Twitter/X | x.com | Mavjudligi (JS-render cheklov) |
| TikTok | tiktok.com | Mavjudligi (JS-render cheklov) |
| YouTube | youtube.com | Mavjudligi |
| Telegram | t.me | Ism, bio, tur (user/kanal/guruh/bot), obunachilар |
| Pinterest | pinterest.com | Ism (OG meta) |
| Steam | steamcommunity.com | Ism (OG meta) |
| Hacker News | firebase API | Karma, bio, ro'yxatdan o'tgan sana |
| Web Footprint | DuckDuckGo dorks | 4 ta dork pattern bo'yicha veb-izlar |

---

## 7. Lookup modullari

### 7.1 IP qidiruv
- Manba: `ip-api.com`
- Natija: mamlakat, viloyat, shahar, ZIP, kenglik/uzunlik, vaqt zonasi, ISP, AS, mobil/proxy/hosting belgilari, Google Maps linki

### 7.2 Telefon tahlili
- Kutubxona: `phonenumbers` (libphonenumber)
- Natija: xalqaro/E164/mahalliy format, mamlakat, operator, tur (mobil/stasionar/VOIP), vaqt zonasi

### 7.3 Email tekshiruvi (5 bosqichli)
1. Format validatsiyasi (regex)
2. MX yozuvlar (dnspython)
3. Gravatar (MD5 hash)
4. EmailRep (obro' + xavfsizlik buzilishlari)
5. SMTP tekshiruvi (RCPT TO握手) — catch-all provayderlar (Gmail, Outlook) uchun o'tkazib yuboriladi

### 7.4 Holehe
- 120+ xizmatda email aniqlash
- Dinamik modul yuklash
- Natija: topilgan xizmatlar, rate-limit holati

### 7.5 Rasm tahlili
- EXIF ma'lumotlari (kamera, GPS, dasturiy ta'minot, muallif)
- GPS: DMS → decimal konversiya → Google Maps linki
- Teskari qidiruv: Google Images, Yandex, TinEye, Bing linklari

---

## 8. Frontend (SPA)

**Texnologiya:** Sof HTML/CSS/JavaScript, ~1060 qator, tashqi kutubxonasiz (faqat Leaflet.js)

### Asosiy komponentlar:

- **Qidiruv paneli** — turi avtomatik aniqlanadi (username/IP/email/telefon/rasm-URL)
- **Natijalar bloki** — tur bo'yicha dinamik render
- **Xarita** — Leaflet.js + OpenStreetMap (IP va telefon uchun)
- **Foto galereyasi** — barcha ijtimoiy tarmoqlardan avatar lightbox
- **AI tahlil** — streaming Markdown render, kursor animatsiya
- **Tarix paneli** — sahifalangan, o'chirish tugmasi bilan
- **Auth modal** — login/register tablar, validatsiya, xato xabarlari

### Maxsus xususiyatlar:
- **Pivot qidiruv** — email/telefonga bosib to'g'ridan-to'g'ri qidiruv
- **JSON eksport** — so'nggi natijani buferga nusxalash
- **Markdown renderer** — AI javobini HTML ga aylantirish (sarlavhalar, ro'yxatlar, qalin, kod)

---

## 9. Autentifikatsiya tizimi

- Algoritm: HS256 JWT
- Parol: bcrypt (passlib)
- Token muddati: 7 kun
- Saqlash: `localStorage`
- Himoya: SQL injection — ORM; XSS — `e()` funksiya (HTML escape)
- Qidiruvlar: autentifikatsiya ixtiyoriy (anonim qidiruv mumkin)
- Tarix: faqat kirgan foydalanuvchilar uchun

---

## 10. Deploy

### Dockerfile
```dockerfile
FROM python:3.11-slim
WORKDIR /osint
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ ./app/
COPY static/ ./static/
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose
```yaml
services:
  web:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./data:/osint/data
    environment:
      SECRET_KEY: ${SECRET_KEY:-change-me-in-production}
      DATABASE_URL: sqlite+aiosqlite:////osint/data/osint.db
    restart: unless-stopped
```

### Muhit o'zgaruvchilari
| O'zgaruvchi | Tavsif | Majburiy |
|-------------|--------|---------|
| `SECRET_KEY` | JWT imzolash kaliti (≥32 belgi) | Ha (prod) |
| `DATABASE_URL` | SQLite fayl yo'li | Ixtiyoriy |
| `GOOGLE_API_KEY` | Gemini API kaliti *(hozir kodda hardcoded)* | Ha |

---

## 11. Ishlash ko'rsatkichlari

- Barcha kollektorlar parallel: ~5–15 sekund (tashqi API latensiyasiga qarab)
- Profil qurish: 12 ta parallel so'rov + email pivot
- AI streaming: birinchi token ~1–3 sekund, to'liq hisobot ~15–30 sekund
- SQLite: MVP uchun yetarli, yuqori yuk uchun PostgreSQL tavsiya etiladi

---

## 12. Keyingi bosqichlar (tavsiyalar)

| # | Tavsiya | Muhimligi |
|---|---------|-----------|
| 1 | `GOOGLE_API_KEY` ni environment variable ga ko'chirish | Kritik |
| 2 | Rate limiting (slowapi yoki nginx) qo'shish | Yuqori |
| 3 | SQLite → PostgreSQL ko'chirish (yuqori yuk uchun) | O'rta |
| 4 | CORS konfiguratsiyasi qo'shish | O'rta |
| 5 | Kesh qatlami (Redis) — takroriy qidiruvlar uchun | O'rta |
| 6 | Holehe uchun alohida httpx.AsyncClient pool | Past |
| 7 | HTTPS enforcement (reverse proxy: Nginx/Caddy) | Yuqori (prod) |

---

*Hujjat avtomatik tarzda loyiha kodi asosida tayyorlangan.*
