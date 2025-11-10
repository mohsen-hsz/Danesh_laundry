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

from jsonbin import reserve   # فایل jsonbin.py

# ------------------------
# logging
# ------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ------------------------
# ENV
# ------------------------
TOKEN = os.getenv("TOKEN")
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")

if not TOKEN or not RENDER_EXTERNAL_URL:
    raise RuntimeError("TOKEN یا RENDER_EXTERNAL_URL تعریف نشده")

WEBHOOK_PATH = f"/{TOKEN}"
WEBHOOK_URL  = f"{RENDER_EXTERNAL_URL}{WEBHOOK_PATH}"

# ------------------------
# Flask
# ------------------------
app = Flask(__name__)

# ------------------------
# Telegram app
# ------------------------
application = Application.builder().token(TOKEN).build()

# Conversation states
FULLNAME, DAY, SLOT = range(3)

# ------------------------
# Bot Handlers
# ------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام! با /reserve می‌تونی رزرو کنی.")

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
    msg = update.message.text.strip()
    if msg not in slot_map:
        await update.message.reply_text("❌ بازه نامعتبر است.")
        return SLOT

    slot = slot_map[msg]
    day = context.user_data["day"]
    full_name = context.user_data["full_name"]
    telegram_id = update.effective_user.id

    ok, res = reserve(day, slot, full_name, telegram_id)
    await update.message.reply_text(res, reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

async def cancel(update, context):
    await update.message.reply_text("لغو شد ✅", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# register handlers
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

# ------------------------
# Async Loop Thread
# ------------------------
tg_loop: asyncio.AbstractEventLoop | None = None

def run_loop():
    global tg_loop
    tg_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(tg_loop)
    tg_loop.run_forever()

loop_thread = threading.Thread(target=run_loop, name="tg-loop", daemon=True)
loop_thread.start()


def submit(coro):
    if tg_loop is None:
        raise RuntimeError("Event loop not ready!")
    return asyncio.run_coroutine_threadsafe(coro, tg_loop)

# delay bootstrap until loop is ready
def bootstrap_application():
    submit(application.initialize()).result()

    async def setup_webhook():
        info = await application.bot.get_webhook_info()
        if info.url != WEBHOOK_URL:
            await application.bot.delete_webhook()
            await application.bot.set_webhook(WEBHOOK_URL)

    submit(setup_webhook()).result()
    submit(application.start()).result()
    logger.info("✅ BOT READY | Webhook → %s", WEBHOOK_URL)


# =========================
# Wait loop becomes ready
# =========================
def wait_for_loop():
    import time
    for _ in range(50):
        if tg_loop is not None:
            return True
        time.sleep(0.1)
    return False

if wait_for_loop():
    bootstrap_application()
else:
    raise RuntimeError("Event loop failed to start")

# ------------------------
# WEBHOOK ROUTE
# ------------------------
@app.route(WEBHOOK_PATH, methods=["POST"])
def webhook():
    try:
        data = request.get_json(force=True)
        update = Update.de_json(data, application.bot)
        submit(application.process_update(update))
    except Exception as e:
        logger.exception("WEBHOOK ERROR: %s", e)
    return "ok", 200


@app.route("/")
def index():
    return "✅ Bot Running"


# ------------------------
# FLASK MAIN
# ------------------------
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    logger.info("Flask running on port %s", port)
    app.run(host="0.0.0.0", port=port)
