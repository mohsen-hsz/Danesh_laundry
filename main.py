import logging
import asyncio
from flask import Flask, request
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

BOT_TOKEN = "8439374401:AAFaFj5NvFaCDB5HvpReQUQ89mNtjYGB6EM"
WEBHOOK_URL = f"https://danesh-laundry.onrender.com/{BOT_TOKEN}"

logging.basicConfig(level=logging.INFO)
app = Flask(__name__)

# TELEGRAM BOT
application = ApplicationBuilder().token(BOT_TOKEN).build()

async def start(update: Update, context):
    await update.message.reply_text("ربات فعال است ✅")

async def echo(update: Update, context):
    msg = update.message.text
    await update.message.reply_text(f"پیام شما: {msg}")

application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))


@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(), application.bot)

    # اجرای ایمن در محیط غیر async
    asyncio.run(application.process_update(update))

    return "OK"


@app.route("/", methods=["GET"])
def index():
    return "Bot Running ✅"


async def set_webhook():
    await application.bot.delete_webhook()
    await application.bot.set_webhook(url=WEBHOOK_URL)
    logging.info("✅ Webhook set → " + WEBHOOK_URL)


if __name__ == "__main__":

    asyncio.run(set_webhook())
    app.run(host="0.0.0.0", port=10000)
