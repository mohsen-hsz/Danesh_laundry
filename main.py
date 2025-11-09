import os
import logging
from flask import Flask, request
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    ConversationHandler,
    filters
)
import asyncio

# === JSONBin funcs ===
from jsonbin import reserve, get_day_slots

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

TOKEN = os.getenv("TOKEN")
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")

app = Flask(__name__)

# ✅ Create Application (GLOBAL, single event loop)
application = Application.builder().token(TOKEN).build()


# === Conversation states ===
FULLNAME, DAY, SLOT = range(3)


# === Commands ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام 👋\nبرای رزرو شستشو، دستور /reserve را بزنید."
    )


async def reserve_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "لطفاً نام و نام‌خانوادگی خود را وارد کنید:"
    )
    return FULLNAME


async def ask_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["full_name"] = update.message.text.strip()

    keyboard = [
        ["شنبه", "یکشنبه", "دوشنبه"],
        ["سه‌شنبه", "چهارشنبه", "پنجشنبه"],
        ["جمعه"],
    ]

    markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)

    await update.message.reply_text(
        "لطفاً روز مورد نظر خود را انتخاب کنید:",
        reply_markup=markup,
    )
    return DAY


async def ask_slot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["day"] = update.message.text.strip()

    keyboard = [["18-19", "19-20", "20-21"]]
    markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)

    await update.message.reply_text(
        "لطفاً بازه زمانی مورد نظر را انتخاب کنید:",
        reply_markup=markup,
    )
    return SLOT


async def reserve_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    slot_map = {
        "18-19": 1,
        "19-20": 2,
        "20-21": 3,
    }

    slot_choice = update.message.text.strip()

    if slot_choice not in slot_map:
        await update.message.reply_text(
            "❌ بازه نامعتبر است. دوباره انتخاب کنید."
        )
        return SLOT

    slot = slot_map[slot_choice]
    day = context.user_data["day"]
    full_name = context.user_data["full_name"]
    telegram_id = update.effective_user.id

    ok, msg = reserve(day, slot, full_name, telegram_id)

    await update.message.reply_text(msg, reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✅ عملیات لغو شد.",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


# === Conversation Handler ===
conv_handler = ConversationHandler(
    entry_points=[CommandHandler("reserve", reserve_start)],
    states={
        FULLNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_day)],
        DAY: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_slot)],
        SLOT: [MessageHandler(filters.TEXT & ~filters.COMMAND, reserve_done)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)

application.add_handler(conv_handler)
application.add_handler(CommandHandler("start", start))


# === Webhook ===
WEBHOOK_PATH = f"/{TOKEN}"
WEBHOOK_URL = f"{RENDER_EXTERNAL_URL}{WEBHOOK_PATH}"


@app.post(WEBHOOK_PATH)
async def webhook():
    """Receive telegram update via webhook"""
    try:
        data = request.get_json(force=True)
        update = Update.de_json(data, application.bot)
        await application.process_update(update)
    except Exception as e:
        print("WEBHOOK ERROR:", e)
    return "ok"


@app.get("/")
def index():
    return "✅ Bot Running"


async def setup_webhook():
    info = await application.bot.get_webhook_info()
    if info.url != WEBHOOK_URL:
        await application.bot.delete_webhook()
        await application.bot.set_webhook(url=WEBHOOK_URL)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(application.initialize())
    loop.run_until_complete(setup_webhook())

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
