import os
import sys
import time
import random
import asyncio
import logging
from collections import deque
from dotenv import load_dotenv
from telethon import TelegramClient, events
from telethon.tl.types import User
from google import genai
from google.genai import types

# ── Logging sozlamalari ───────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("UserBot")

# ── .env faylni yuklash ──────────────────────────────────────────────
load_dotenv()

API_ID_RAW = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
OWNER_NAME = os.getenv("OWNER_NAME", "Muhammadsodiq")
ALLOWED_RAW = os.getenv("ALLOWED", "")
PAUSE_MINUTES_RAW = os.getenv("PAUSE_MINUTES", "10")

if not API_ID_RAW or not API_HASH:
    logger.error("Xatolik: .env faylida API_ID yoki API_HASH topilmadi!")
    sys.exit(1)

try:
    API_ID = int(API_ID_RAW)
except ValueError:
    logger.error("Xatolik: API_ID butun son (integer) bo'lishi shart!")
    sys.exit(1)

try:
    PAUSE_MINUTES = float(PAUSE_MINUTES_RAW)
except ValueError:
    PAUSE_MINUTES = 10.0

# ALLOWED ro'yxatini tozalash va tayyorlash
ALLOWED_SET: set[str] = set()
if ALLOWED_RAW.strip():
    for item in ALLOWED_RAW.split(","):
        cleaned = item.strip().lower().lstrip("@")
        if cleaned:
            ALLOWED_SET.add(cleaned)

# ── Gemini mijozi va tizim prompti ───────────────────────────────────
ai_client = None
if GEMINI_API_KEY:
    try:
        ai_client = genai.Client(api_key=GEMINI_API_KEY)
    except Exception as e:
        logger.error(f"Gemini mijozini initsializatsiya qilishda xatolik: {e}")
else:
    logger.error("Xatolik: .env faylida GEMINI_API_KEY topilmadi!")

SYSTEM_PROMPT = (
    f"Sen {OWNER_NAME}ning shaxsiy yordamchisisan. "
    f"U hozir band bo'lsa, uning nomidan o'zbek tilida (lotin yozuvida) samimiy, "
    f"qisqa (1-3 gap) va do'stona javob ber. Ba'zan emoji ishlat (masalan 😊). "
    f"O'zingni {OWNER_NAME}ning yordamchisi sifatida tanishtir va u bo'sh "
    f"bo'lganda o'zi javob berishini ayt. Aniq nima kerakligini so'ra. "
    f"Parol, karta raqami, kod kabi maxfiy ma'lumotlarni hech qachon so'rama va "
    f"qabul qilma, odam yuborsa yubormaslikni ayt."
)

# ── Holat va xotira boshqaruvi ───────────────────────────────────────
# Har bir chat_id uchun oxirgi 12 ta xabar: {chat_id: deque(maxlen=12)}
# Element: {"role": "user"|"model", "text": "..."}
chat_history: dict[int, deque] = {}

# Har bir chat_id uchun oxirgi marta egasi yozgan vaqt (timestamp): {chat_id: float}
owner_last_active: dict[int, float] = {}

# Bir vaqtning o'zida bir xil chatga javob qaytarishda poyga holatini oldini olish uchun
chat_locks: dict[int, asyncio.Lock] = {}


def is_user_allowed(user: User) -> bool:
    """Foydalanuvchi ALLOWED ro'yxatiga to'g'ri keladimi yoki yo'qligini tekshiradi."""
    if not ALLOWED_SET:
        return True
    
    uid_str = str(user.id)
    if uid_str in ALLOWED_SET:
        return True
    
    if user.username and user.username.lower() in ALLOWED_SET:
        return True
        
    return False


def is_chat_paused(chat_id: int) -> bool:
    """Agar hisob egasi chatga yozgan bo'lsa va PAUSE_MINUTES o'tmagan bo'lsa True qaytaradi."""
    if chat_id not in owner_last_active:
        return False
    passed_seconds = time.time() - owner_last_active[chat_id]
    return passed_seconds < (PAUSE_MINUTES * 60)


def add_to_history(chat_id: int, role: str, text: str):
    """Chat tarixiga xabar qo'shadi (maksimal 12 ta saqlanadi)."""
    if chat_id not in chat_history:
        chat_history[chat_id] = deque(maxlen=12)
    chat_history[chat_id].append({"role": role, "text": text})


async def get_gemini_reply(chat_id: int, new_message_text: str) -> str | None:
    """Gemini AI orqali suhbat kontekstini inobatga olgan holda javob oladi."""
    if not ai_client:
        logger.error("Gemini mijozi mavjud emas.")
        return None

    # Tarixni tayyorlash
    contents = []
    if chat_id in chat_history:
        for item in chat_history[chat_id]:
            role = item["role"]  # "user" yoki "model"
            contents.append(
                types.Content(
                    role=role,
                    parts=[types.Part.from_text(text=item["text"])]
                )
            )

    # Yangi xabarni qo'shish
    contents.append(
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=new_message_text)]
        )
    )

    try:
        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.7,
        )

        response = await asyncio.to_thread(
            ai_client.models.generate_content,
            model=GEMINI_MODEL,
            contents=contents,
            config=config,
        )

        if response and response.text:
            return response.text.strip()
        return None
    except Exception as e:
        logger.error(f"Gemini API bilan muloqotda xatolik yuz berdi: {e}")
        return None


from telethon.sessions import StringSession

# ── Telegram UserBot mijozi ──────────────────────────────────────────
# Agar TELEGRAM_SESSION muhit o'zgaruvchisi berilgan bo'lsa (Render / Cloud uchun),
# StringSession ishlatiladi, aks holda lokal "userbot.session" fayli qo'llanadi.
session_env = os.getenv("TELEGRAM_SESSION", "").strip()
session_target = StringSession(session_env) if session_env else "userbot"

client = TelegramClient(session_target, API_ID, API_HASH)



@client.on(events.NewMessage(outgoing=True))
async def handle_outgoing_message(event):
    """Hisob egasi (o'zingiz) shaxsiy chatga yozganda botni vaqtincha to'xtatish."""
    if not event.is_private:
        return
    
    chat_id = event.chat_id
    owner_last_active[chat_id] = time.time()
    
    if event.raw_text:
        add_to_history(chat_id, "model", event.raw_text)
    
    logger.info(f"Egasi chatga ({chat_id}) xabar yozdi. Bot {PAUSE_MINUTES} daqiqaga to'xtatildi.")


@client.on(events.NewMessage(incoming=True))
async def handle_incoming_message(event):
    """Kelgan shaxsiy xabarlarni qabul qilish va AI orqali javob berish."""
    # 1. Faqat shaxsiy chatlarga javob berish (guruh, kanal emas)
    if not event.is_private:
        return

    # Foydalanuvchini olish
    sender = await event.get_sender()
    if not isinstance(sender, User):
        return

    # Botlarga javob bermaslik
    if sender.bot:
        return

    # O'zimizga o'zimiz yozsak (Saved Messages)
    if sender.is_self:
        return

    chat_id = event.chat_id

    # 2. ALLOWED ro'yxatini tekshirish
    if not is_user_allowed(sender):
        return

    # 3. Agar egasi yozganidan so'ng PAUSE_MINUTES o'tmagan bo'lsa, javob bermaslik
    if is_chat_paused(chat_id):
        logger.info(f"Chat ({chat_id}) pauza holatida, javob berilmadi.")
        return

    # Xabar matni bo'sh bo'lmasligi kerak
    message_text = event.raw_text
    if not message_text or not message_text.strip():
        return

    # Bir xil chat uchun bir vaqtning o'zida bir nechta parallel javob yuborilishini oldini olish
    if chat_id not in chat_locks:
        chat_locks[chat_id] = asyncio.Lock()

    async with chat_locks[chat_id]:
        # Lock olingandan so'ng yana pauzani tekshirib qo'yamiz
        if is_chat_paused(chat_id):
            return

        logger.info(f"Yangi xabar qabul qilindi ({sender.id} - @{sender.username}): {message_text[:40]}...")

        # 4. Javob berishdan oldin 2-5 soniya kutish va 'typing' statusini yoqish
        delay = random.uniform(2.0, 5.0)
        try:
            async with client.action(chat_id, "typing"):
                # Typing ko'rsatib turganda parallel ravishda Gemini'dan javob olamiz
                gemini_task = asyncio.create_task(get_gemini_reply(chat_id, message_text))
                await asyncio.sleep(delay)
                reply_text = await gemini_task
        except Exception as e:
            logger.error(f"Typing yoki javob tayyorlash jarayonida xatolik: {e}")
            reply_text = None

        if reply_text:
            try:
                # Xabarni yuborish
                await event.reply(reply_text)
                
                # Tarixga qo'shish
                add_to_history(chat_id, "user", message_text)
                add_to_history(chat_id, "model", reply_text)
                logger.info(f"Javob muvaffaqiyatli yuborildi ({chat_id}).")
            except Exception as e:
                logger.error(f"Telegram orqali xabar yuborishda xatolik: {e}")
        else:
            logger.warning(f"Javob matni olinmadi, hech narsa yuborilmadi ({chat_id}).")


from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Bot is alive and running!")

    def log_message(self, format, *args):
        pass  # Health check loglarini ko'rsatmaslik


def run_http_server():
    port = int(os.getenv("PORT", "10000"))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    logger.info(f"Render uchun HTTP server {port}-portda ishga tushdi.")
    server.serve_forever()


async def main():
    logger.info("Telegram UserBot ishga tushirilmoqda...")
    # Render port talabi uchun HTTP serverni alohida threadda ishga tushiramiz
    threading.Thread(target=run_http_server, daemon=True).start()

    # client.start() orqali avtorizatsiya va ulanish tekshiriladi
    await client.start()
    
    me = await client.get_me()
    logger.info(f"Bot muvaffaqiyatli ulandi! Profil: {me.first_name} (@{me.username}) | ID: {me.id}")
    logger.info("Yangi xabarlar kutilmoqda...")
    
    await client.run_until_disconnected()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot to'xtatildi.")
    except Exception as e:
        logger.critical(f"Kutilmagan xatolik yuz berdi: {e}")

