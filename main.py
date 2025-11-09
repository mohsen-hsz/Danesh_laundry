import os
import logging
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

from jsonbin import reserve

logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("TOKEN")
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")

app = Flask(__name__)

# global app
application = Application.builder().token(TOKEN).build()

FULLNAME, DAY, SLOT = range(3)


# === handlers ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام! برای رزرو /reserve را بزنید.")


async def reserve_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("نام و نام خانوادگی را وارد کنید:")
    return FULLNAME


async def ask_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["full_name"] = update.message.text.strip()

    keyboard = [
        ["شنبه", "یکشنبه", "دوشنبه"],
        ["سه‌شنبه", "چهارشنبه", "پنجشنبه"],
        ["جمعه"],
    ]

    await update.message.reply_text(
        "لطفاً روز را انتخاب کنید:",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True),
    )

    return DAY


async def ask_slot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["day"] = update.message.text.strip()
    keyboard = [["18-19", "19-20", "20-21"]]
    await update.message.reply_text(
        "لطفاً بازه زمانی را انتخاب کنید:",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True),
    )
    return SLOT


async def reserve_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    slot_map = {"18-19": 1, "19-20": 2, "20-21": 3}
    slot_choice = update.message.text.strip()

    if slot_choice not in slot_map:
        await update.message.reply_text("❌ بازه نامعتبر است.")
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


# === Conversation handler
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


WEBHOOK_PATH = f"/{TOKEN}"
WEBHOOK_URL = f"{RENDER_EXTERNAL_URL}{WEBHOOK_PATH}"


# ✅ NON-ASYNC webhook → safe for Flask
@app.post(WEBHOOK_PATH)
def webhook():
    try:
        data = request.get_json(force=True)
        update = Update.de_json(data, application.bot)

        # process async safely WITHOUT async view
        asyncio.get_event_loop().create_task(application.process_update(update))

    except Exception as e:
        print("WEBHOOK ERROR:", e)

    return "ok"


@app.get("/")
def index():
    return "Bot Running ✅"


async def setup():
    info = await application.bot.get_webhook_info()
    if info.url != WEBHOOK_URL:
        await application.bot.delete_webhook()
        await application.bot.set_webhook(url=WEBHOOK_URL)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(application.initialize())
    loop.run_until_complete(setup())

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
