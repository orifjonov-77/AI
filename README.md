# Telegram UserBot (Telethon) + Gemini AI 🤖

Ushbu loyiha sizning shaxsiy Telegram akkauntingizga ulanib, sizga shaxsiy chatda (Direct / Private Message) yozgan odamlarga avtomatik ravishda **"Muhammadsodiqning yordamchisiman"** deb samimiy va do'stona tarzda Gemini AI yordamida javob qaytaradi.

---

## 🌟 Asosiy imkoniyatlari

1. **Faqat shaxsiy chatlar**: Guruhlar, kanallar va botlarning xabarlariga e'tibor bermaydi.
2. **Konteksni eslab qolish**: Har bir foydalanuvchi bilan so'nggi 12 ta xabarni xotirada saqlaydi va Gemini'ga suhbat tarixi sifatida uzatadi.
3. **Pauza mexanizmi (`PAUSE_MINUTES`)**: Agar siz o'zingiz biror chatga yozsangiz, bot belgilangan daqiqa (masalan, 10 daqiqa) davomida o'sha chatga xalaqit bermaydi.
4. **Haqiqiy inson harakati**: Javob berishdan oldin 2–5 soniya tasodifiy kutadi va Telegram'da *"typing..."* (yozmoqda...) holatini ko'rsatadi.
5. **Filtrlash (`ALLOWED`)**: Bo'sh bo'lsa barcha shaxsiy chatlarga, to'ldirilgan bo'lsa faqat ko'rsatilgan username yoki ID egalariga javob beradi.
6. **Xavfsiz va barqaror**: Gemini API uzilib qolsa yoki limit tugasa bot to'xtab qolmaydi, faqat konsolga xatolikni qayd etadi. Maxfiy ma'lumotlar (.env, session) ehtiyotlanadi.

---

## 📁 Loyiha tarkibi

```text
C:\Users\777 comp service\Desktop\Ai\
├── bot.py             # Userbot asosiy kodi
├── requirements.txt   # Kerakli Python kutubxonalari
├── .env               # Maxfiy sozlamalar (API kalitlar)
├── .gitignore         # Git uchun e'tibordan chetda qoldiriladigan fayllar
└── README.md          # Qo'llanma
```

---

## ⚙️ O'rnatish va Ishga tushirish bosqichlari

### 1. Terminalni oching va loyiha papkasiga kiring

PowerShell yoki Buyruqlar satrida (CMD):

```powershell
cd "C:\Users\777 comp service\Desktop\Ai"
```

### 2. Kutubxonalarni o'rnatish

Kutubxonalar o'rnatilmagan bo'lsa:

```powershell
python -m pip install -r requirements.txt
```

### 3. `.env` faylini tekshiring

Loyiha papkasida `.env` fayli mavjudligiga va unda quyidagi o'zgaruvchilar to'g'ri kiritilganiga ishonch hosil qiling:

```env
API_ID=12345678
API_HASH=abcdef1234567890abcdef1234567890
GEMINI_API_KEY=AIzaSy...
GEMINI_MODEL=gemini-2.5-flash
OWNER_NAME=Muhammadsodiq
ALLOWED=
PAUSE_MINUTES=10
```

*Eslatma:* 
- `ALLOWED` bo'sh qoldirilsa, barcha shaxsiy chatlarga javob beradi. Agar faqat ma'lum kishilarga javob berishini xohlasangiz: `ALLOWED=username1,username2,123456789` shaklida vergul bilan ajratib yozing.
- `API_ID` va `API_HASH` [my.telegram.org](https://my.telegram.org) saytidan olinadi.

---

### 4. Botni birinchi marta ishga tushirish

Botni quyidagi buyruq orqali ishga tushiring:

```powershell
python bot.py
```

> ⚠️ **BIRINCHI ISHGA TUSHIRISHDA NIMA BO'LADI?**
> 
> Telethon bu userbot (shaxsiy akkaunt mijozi) bo'lgani sababli, konsolda sizdan:
> 1. **Telefon raqamingizni** so'raydi (masalan: `+998901234567`).
> 2. Telegram ilovangizga kelgan **tasdiqlash kodi**ni (login code) kiritishni so'raydi.
> 3. Agar akkauntingizda ikki bosqichli tekshiruv (2FA / Two-step verification) yoqilgan bo'lsa, **parolingizni** so'raydi.
> 
> Bularni bir marta kiritganingizdan so'ng, papkada `userbot.session` fayli yaratiladi va keyingi safar qayta kod so'ramaydi.

---

## 🛑 Botni to'xtatish

Botni to'xtatish uchun konsolda `Ctrl + C` tugmalarini bosing.
