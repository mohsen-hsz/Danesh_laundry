import os
import logging
import threading
import asyncio
from flask import Flask, request
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    ConversationHandler,
    filters,
)

# توابع ذخیره‌سازی
from jsonbin import reserve  # فایل jsonbin.py که قبلاً ساختیم

# --- لاگ ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- ENV ---
TOKEN = os.getenv("TOKEN")
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")
if not TOKEN or not RENDER_EXTERNAL_URL:
    raise RuntimeError("TOKEN یا RENDER_EXTERNAL_URL تعریف نشده")

# --- Flask ---
app = Flask(__name__)

# --- Telegram Application (بدون اجرا) ---
application = Application.builder().token(TOKEN).build()

# === حالت‌های مکالمه
FULLNAME, DAY, SLOT = range(3)

# === دستورات ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام! برای رزرو /reserve را بزنید.")

async def reserve_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("نام و نام‌خانوادگی را وارد کنید:")
    return FULLNAME

async def ask_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["full_name"] = update.message.text.strip()
    keyboard = [
        ["شنبه", "یکشنبه", "دوشنبه"],
        ["سه‌شنبه", "چهارشنبه", "پنجشنبه"],
        ["جمعه"],
    ]
    await update.message.reply_text(
        "روز مورد نظر را انتخاب کنید:",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True),
    )
    return DAY

async def ask_slot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["day"] = update.message.text.strip()
    keyboard = [["18-19", "19-20", "20-21"]]
    await update.message.reply_text(
        "بازه زمانی را انتخاب کنید:",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True),
    )
    return SLOT

async def reserve_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    slot_map = {"18-19": 1, "19-20": 2, "20-21": 3}
    slot_choice = update.message.text.strip()
    if slot_choice not in slot_map:
        await update.message.reply_text("❌ بازه نامعتبر است. دوباره انتخاب کنید.")
        return SLOT

    slot = slot_map[slot_choice]
    day = context.user_data["day"]
    full_name = context.user_data["full_name"]
    telegram_id = update.effective_user.id

    ok, msg = reserve(day, slot, full_name, telegram_id)
    await update.message.reply_text(msg, reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("لغو شد ✅", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# === ثبت هندلرها
conv = ConversationHandler(
    entry_points=[CommandHandler("reserve", reserve_start)],
    states={
        FULLNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_day)],
        DAY: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_slot)],
        SLOT: [MessageHandler(filters.TEXT & ~filters.COMMAND, reserve_done)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)
application.add_handler(conv)
application.add_handler(CommandHandler("start", start))

# --- Webhook ---
WEBHOOK_PATH = f"/{TOKEN}"
WEBHOOK_URL = f"{RENDER_EXTERNAL_URL}{WEBHOOK_PATH}"

# ---------------------------
#   لوپ سراسری در ترد جدا
# ---------------------------
_app_loop: asyncio.AbstractEventLoop | None = None

def _start_event_loop():
    """Run a dedicated asyncio loop forever in a background thread."""
    global _app_loop
    _app_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(_app_loop)
    _app_loop.run_forever()

# ترد لوپ را بالا می‌آورد
_loop_thread = threading.Thread(target=_start_event_loop, name="tg-app-loop", daemon=True)
_loop_thread.start()

def submit(coro: asyncio.coroutines):
    """اجرای ایمن کوروتین‌ها روی لوپ بک‌گراند"""
    if _app_loop is None:
        raise RuntimeError("Event loop not ready")
    return asyncio.run_coroutine_threadsafe(coro, _app_loop)

# راه‌اندازی اپ و وبهوک داخل همان لوپ
def bootstrap_application():
    # initialize / start / set_webhook داخل همان لوپ
    submit(application.initialize()).result()
    # set webhook
    async def _setup():
        info = await application.bot.get_webhook_info()
        if info.url != WEBHOOK_URL:
            await application.bot.delete_webhook()
            await application.bot.set_webhook(url=WEBHOOK_URL)
    submit(_setup()).result()
    # (اختیاری) start internal components
    submit(application.start()).result()
    logger.info("✅ Telegram application ready with webhook: %s", WEBHOOK_URL)

bootstrap_application()

# ---------------------------
#   Flask routes (sync)
# ---------------------------
@app.route(WEBHOOK_PATH, methods=["POST"])
def webhook():
    try:
        data = request.get_json(force=True)
        update = Update.de_json(data, application.bot)
        submit(application.process_update(update))  # به لوپ بک‌گراند می‌فرستیم
    except Exception as e:
        logger.exception("WEBHOOK ERROR: %s", e)
    return "ok", 200

@app.route("/")
def index():
    return "✅ Bot Running"

# ---------------------------
#   Run Flask
# ---------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    logger.info("🚀 Flask running on port %s", port)
    app.run(host="0.0.0.0", port=port)
