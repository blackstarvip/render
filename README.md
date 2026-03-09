# eMaktab Bot — Render.com Deployment

Python Flask + Selenium bot. InfinityFree PHP saytidan HTTP so'rovlarni qabul qilib, eMaktab ga login qiladi.

---

## 🏗️ Arxitektura

```
[O'qituvchi brauzer]
        │
        ▼ AJAX
[InfinityFree — PHP sayt]
  index.php / teacher/dashboard.php
        │
        ▼ HTTP POST (JSON + X-API-Key)
[Render.com — Flask Bot API]
  POST /api/login
        │
        ▼ Selenium + Chrome
[eMaktab login.emaktab.uz]
        │
        ▼ success/error/captcha
[PHP ← JSON javob]
        │
        ▼ SQLite DB yangilanadi
[O'qituvchi ekranida natija]
```

---

## 🚀 Render.com ga Deploy

### 1. GitHub Repository yaratish

```bash
# Faqat render-bot/ papkasini yuklang
cd render-bot/
git init
git add .
git commit -m "eMaktab bot initial"
git remote add origin https://github.com/SIZNING_USERNAME/emaktab-bot.git
git push -u origin main
```

### 2. Render.com da Web Service yaratish

1. [render.com](https://render.com) ga kiring
2. **New** → **Web Service**
3. GitHub repo ni ulang → `emaktab-bot` ni tanlang
4. Sozlamalar:

| Maydon | Qiymat |
|--------|--------|
| Name | `emaktab-bot` |
| Runtime | `Python 3` |
| Build Command | (render.yaml avtomatik oladi) |
| Start Command | `gunicorn app:app --workers 2 --timeout 120 --bind 0.0.0.0:$PORT` |
| Plan | Free |

### 3. Environment Variables o'rnatish

Render Dashboard → **Your Service** → **Environment** → **Add Environment Variable**:

| Key | Value |
|-----|-------|
| `BOT_API_KEY` | `python3 -c "import secrets; print(secrets.token_hex(32))"` bilan hosil qiling |
| `EMAKTAB_URL` | `https://login.emaktab.uz` |

### 4. Deploy

**Deploy** tugmasini bosing. Build log ni kuzating (Chrome o'rnatilishi ~2-3 daqiqa).

Deploy tugagach URL ko'rinadi: `https://emaktab-bot.onrender.com`

---

## ⚙️ PHP Saytini Sozlash

`config/config.php` faylini yangilang:

```php
// Render dan olgan URL
define('RENDER_BOT_URL', 'https://emaktab-bot.onrender.com');

// Render Environment da o'rnatgan BOT_API_KEY bilan bir xil!
define('RENDER_API_KEY', 'your-secret-key-here');

define('BOT_TIMEOUT', 90);  // Cold start uchun 90s
```

---

## 🔍 Tekshirish

```bash
# Health check
curl https://emaktab-bot.onrender.com/health

# Login test
curl -X POST https://emaktab-bot.onrender.com/api/login \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-secret-key" \
  -d '{"emaktab_login":"test","emaktab_password":"test","student_id":1}'
```

Admin Panel → **Bot Sozlamalari** → **Ulanishni Tekshirish**

---

## ⏱️ Cold Start Haqida

Render **free plan** da server 15 daqiqa faoliyatsizlikdan keyin uxlab qoladi.

**Birinchi so'rov:** 30–60 soniya kutish zarur.

**Yechimlar:**
1. **Render Paid** ($7/oy) — doim aktiv
2. **Cron job** — har 10 daqiqada `/health` ga so'rov (UptimeRobot bepul)
3. **PHP da retry** — xato bo'lsa 1 marta qayta urinish

### UptimeRobot bilan "doim yoqib" turish (bepul):
1. [uptimerobot.com](https://uptimerobot.com) ga kiring
2. **Add New Monitor** → HTTP(s)
3. URL: `https://emaktab-bot.onrender.com/health`
4. Interval: **5 minutes**

---

## 📁 Fayl Tarkibi

```
render-bot/
├── app.py             # Flask API (asosiy)
├── selenium_runner.py # Selenium login logikasi
├── requirements.txt   # Python kutubxonalari
├── render.yaml        # Render deploy konfiguratsiyasi
├── .env.example       # Muhit o'zgaruvchilari namuna
└── .gitignore
```

---

## 🔒 Xavfsizlik

- `X-API-Key` header har so'rovda tekshiriladi
- API kalit kamida 32 ta random belgi bo'lishi kerak
- `.env` faylini hech qachon GitHub ga yuklaman
- Render da "Secret" sifatida saqlash mumkin
