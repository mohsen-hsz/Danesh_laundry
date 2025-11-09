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
    filters
)

# ✅ JSONBin functions
from jsonbin import reserve, get_day_slots

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

TOKEN = os.getenv("TOKEN")
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")

app = Flask(__name__)

application = Application.builder().token(TOKEN).build()
asyncio.get_event_loop().run_until_complete(application.initialize())

FULLNAME, DAY, SLOT = range(3)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام 👋\nبرای رزرو از /reserve استفاده کنید.")


async def reserve_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("نام و نام خانوادگی خود را وارد کنید:")
    return FULLNAME


async def ask_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["full_name"] = update.message.text.strip()

    keyboard = [["شنبه", "یکشنبه", "دوشنبه"],
                ["سه‌شنبه", "چهارشنبه", "پنجشنبه"],
                ["جمعه"]]

    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)

    await update.message.reply_text(
        "لطفا روز موردنظر را انتخاب کنید:",
        reply_markup=reply_markup,
    )
    return DAY


async def ask_slot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["day"] = update.message.text.strip()

    keyboard = [["18-19", "19-20", "20-21"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)

    await update.message.reply_text(
        "بازه زمانی را انتخاب کنید:",
        reply_markup=reply_markup
    )
    return SLOT


async def reserve_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    slot_text = update.message.text.strip()

    mapping = {
        "18-19": 1,
        "19-20": 2,
        "20-21": 3
    }

    if slot_text not in mapping:
        await update.message.reply_text("❌ انتخاب نامعتبر!", reply_markup=ReplyKeyboardRemove())
        return SLOT

    slot = mapping[slot_text]
    day_name = context.user_data["day"]
    full_name = context.user_data["full_name"]
    telegram_id = update.effective_user.id

    ok, msg = reserve(day_name, slot, full_name, telegram_id)

    await update.message.reply_text(msg, reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ عملیات لغو شد", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


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


# ✅ Webhook
WEBHOOK_PATH = f"/{TOKEN}"
WEBHOOK_URL = f"{RENDER_EXTERNAL_URL}{WEBHOOK_PATH}"

@app.route(WEBHOOK_PATH, methods=["POST"])
def webhook():
    try:
        update = Update.de_json(request.get_json(force=True), application.bot)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(application.process_update(update))
        loop.close()
    except:
        pass
    return "ok", 200


@app.route("/")
def index():
    return "✅ Bot Running"


async def set_webhook():
    info = await application.bot.get_webhook_info()
    if info.url != WEBHOOK_URL:
        await application.bot.delete_webhook()
        await application.bot.set_webhook(url=WEBHOOK_URL)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    asyncio.get_event_loop().run_until_complete(set_webhook())
    app.run(host="0.0.0.0", port=port)
