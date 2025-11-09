import os
import asyncio
from flask import Flask, request
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, ContextTypes,
    MessageHandler, ConversationHandler, filters
)

from jsonbin import (
    fetch_db, save_db, reset_if_needed,
    get_available_days, get_free_slots, reserve_time
)

BOT_TOKEN = os.getenv("BOT_TOKEN")

ASK_NAME, ASK_DAY, ASK_TIME = range(3)

FA_DAYS = ["شنبه", "یک‌شنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنج‌شنبه", "جمعه"]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام! برای رزرو /reserve را بزنید ✅")


async def reserve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("لطفاً نام و نام خانوادگی خود را وارد کنید:")
    return ASK_NAME


async def ask_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text

    db = reset_if_needed(fetch_db())
    days = get_available_days(db)

    if not days:
        await update.message.reply_text("هیچ روز آزادی موجود نیست ❌")
        return ConversationHandler.END

    keyboard = [[FA_DAYS[d]] for d in days]
    await update.message.reply_text(
        "لطفاً روز را انتخاب کنید:",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    )

    return ASK_DAY


async def ask_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    day_text = update.message.text
    if day_text not in FA_DAYS:
        await update.message.reply_text("روز نامعتبر است ❌")
        return ConversationHandler.END

    day_index = FA_DAYS.index(day_text)
    context.user_data["day"] = day_index

    db = reset_if_needed(fetch_db())
    free_slots = get_free_slots(db, day_index)

    if not free_slots:
        await update.message.reply_text("تمام بازه‌های این روز پر شده‌اند ❌")
        return ConversationHandler.END

    keyboard = [[s] for s in free_slots]
    await update.message.reply_text(
        "لطفاً بازه زمانی را انتخاب کنید:",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    )
    return ASK_TIME


async def finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    slot = update.message.text
    name = context.user_data.get("name")
    day = context.user_data.get("day")

    db = reset_if_needed(fetch_db())
    free_slots = get_free_slots(db, day)

    if slot not in free_slots:
        await update.message.reply_text("این بازه قبلاً پر شده ❌")
        return ConversationHandler.END

    reserve_time(db, name, day, slot)
    await update.message.reply_text("✅ رزرو شما با موفقیت ثبت شد")

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("لغو شد ❌")
    return ConversationHandler.END


############################################
#   FLASK WEBHOOK
############################################
app = Flask(__name__)
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)


application = Application.builder().token(BOT_TOKEN).build()

conv_handler = ConversationHandler(
    entry_points=[CommandHandler("reserve", reserve)],
    states={
        ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_day)],
        ASK_DAY: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_time)],
        ASK_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, finish)],
    },
    fallbacks=[CommandHandler("cancel", cancel)]
)

application.add_handler(CommandHandler("start", start))
application.add_handler(conv_handler)


def bootstrap():
    loop.run_until_complete(application.initialize())
    loop.run_until_complete(application.start())
    loop.run_until_complete(
        application.bot.set_webhook(os.getenv("RENDER_EXTERNAL_URL"))
    )


@app.post(f"/{BOT_TOKEN}")
async def webhook():
    data = request.get_json(force=True)
    update = Update.de_json(data, application.bot)
    await application.process_update(update)
    return "ok"


@app.get("/")
def home():
    return "Bot is Up ✅"


if __name__ == "__main__":
    bootstrap()
    app.run(host="0.0.0.0", port=10000)
