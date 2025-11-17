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
    ConversationHandler,
    ContextTypes,
    filters,
)

from jsonbin import reserve, cancel_reservation, get_calendar, register_user

# ==============================
# تنظیم لاگ
# ==============================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ==============================
# ENV
# ==============================
TOKEN = os.getenv("TOKEN") or os.getenv("TELEGRAM_TOKEN")
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")

if not TOKEN or not RENDER_EXTERNAL_URL:
    raise RuntimeError("❌ متغیرهای محیطی TOKEN و RENDER_EXTERNAL_URL باید تنظیم شوند.")

WEBHOOK_PATH = f"/{TOKEN}"
WEBHOOK_URL = f"{RENDER_EXTERNAL_URL}{WEBHOOK_PATH}"

# ==============================
# Flask
# ==============================
app = Flask(__name__)

# ==============================
# Telegram Application
# ==============================
application = Application.builder().token(TOKEN).build()

FULLNAME, DAY, SLOT = range(3)

DAYS_KEYBOARD = [
    ["شنبه", "یکشنبه", "دوشنبه"],
    ["سه‌شنبه", "چهارشنبه", "پنجشنبه"],
    ["جمعه"],
]

SLOTS_KEYBOARD = [["18-19", "19-20", "20-21"]]
SLOT_MAP = {"18-19": 0, "19-20": 1, "20-21": 2}


# ==============================
# Handlers
# ==============================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user:
        register_user(user.id)

    text = (
        "سلام 👋\n"
        "این ربات برای رزرو لباس‌شویی است.\n\n"
        "دستورات:\n"
        "/reserve - ثبت رزرو جدید\n"
        "/cancel_reserve - لغو تمام رزروهای شما\n"
        "/calender - مشاهده وضعیت رزرو هفتگی\n"
    )
    await update.message.reply_text(text)


async def reserve_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user:
        register_user(user.id)

    await update.message.reply_text("لطفاً نام و نام خانوادگی خود را وارد کنید:")
    return FULLNAME


async def ask_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    full_name = (update.message.text or "").strip()
    if not full_name:
        await update.message.reply_text("❌ نام معتبر وارد کنید.")
        return FULLNAME

    context.user_data["full_name"] = full_name

    await update.message.reply_text(
        "روز موردنظر را انتخاب کنید:",
        reply_markup=ReplyKeyboardMarkup(DAYS_KEYBOARD, one_time_keyboard=True),
    )
    return DAY


async def ask_slot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    day = (update.message.text or "").strip()
    context.user_data["day"] = day

    await update.message.reply_text(
        "بازه زمانی موردنظر را انتخاب کنید:",
        reply_markup=ReplyKeyboardMarkup(SLOTS_KEYBOARD, one_time_keyboard=True),
    )
    return SLOT


async def reserve_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    slot_text = (update.message.text or "").strip()
    if slot_text not in SLOT_MAP:
        await update.message.reply_text("❌ بازه زمانی نامعتبر است. یک گزینه از کیبورد انتخاب کنید.")
        return SLOT

    slot_index = SLOT_MAP[slot_text]
    day = context.user_data.get("day")
    full_name = context.user_data.get("full_name")
    user = update.effective_user

    if not day or not full_name or not user:
        await update.message.reply_text("❌ خطای داخلی. دوباره /reserve را بزنید.", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

    ok, msg = reserve(day, slot_index, full_name, user.id)

    await update.message.reply_text(msg, reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


async def cancel_reserve_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user:
        await update.message.reply_text("❌ کاربر نامشخص.")
        return

    ok, msg = cancel_reservation(user.id)
    await update.message.reply_text(msg)


async def cancel_conv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("عملیات رزرو لغو شد.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


async def calender_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = get_calendar()
    await update.message.reply_text(text, parse_mode="Markdown")


# ==============================
# ConversationHandler
# ==============================
conv = ConversationHandler(
    entry_points=[CommandHandler("reserve", reserve_start)],
    states={
        FULLNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_day)],
        DAY: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_slot)],
        SLOT: [MessageHandler(filters.TEXT & ~filters.COMMAND, reserve_done)],
    },
    fallbacks=[CommandHandler("cancel", cancel_conv)],
)

application.add_handler(conv)
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("cancel_reserve", cancel_reserve_cmd))
application.add_handler(CommandHandler("calender", calender_cmd))


# ==============================
# Async loop + webhook
# ==============================
tg_loop = None


def run_loop():
    global tg_loop
    tg_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(tg_loop)
    tg_loop.run_forever()


threading.Thread(target=run_loop, daemon=True, name="tg-loop").start()


def wait_for_loop(timeout=5.0):
    import time

    start = time.time()
    while tg_loop is None and (time.time() - start) < timeout:
        time.sleep(0.1)
    return tg_loop is not None


def submit(coro):
    if tg_loop is None:
        raise RuntimeError("Event loop not ready")
    return asyncio.run_coroutine_threadsafe(coro, tg_loop)


def bootstrap():
    submit(application.initialize()).result()

    async def setup():
        await application.bot.delete_webhook()
        await application.bot.set_webhook(WEBHOOK_URL)

    submit(setup()).result()
    submit(application.start()).result()
    logger.info("✅ BOT READY | %s", WEBHOOK_URL)


# ==============================
# Flask routes
# ==============================
@app.route(WEBHOOK_PATH, methods=["POST"])
def webhook():
    try:
        data = request.get_json(force=True)
        update = Update.de_json(data, application.bot)
        application.update_queue.put_nowait(update)
    except Exception as e:
        logger.exception("WEBHOOK ERROR: %s", e)
    return "ok", 200


@app.route("/")
def index():
    return "✅ Bot Running", 200


# ==============================
# main
# ==============================
if __name__ == "__main__":
    if wait_for_loop():
        bootstrap()
    port = int(os.getenv("PORT", "5000"))
    logger.info("Flask running on port %d", port)
    app.run(host="0.0.0.0", port=port)
