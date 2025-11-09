import os
import logging
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

# handlers
from handlers.start import start
from handlers.show_days import show_days


TOKEN = os.getenv("TOKEN")
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")


logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
application = Application.builder().token(TOKEN).build()


application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.Regex("نمایش روزها"), show_days))


WEBHOOK_PATH = f"/{TOKEN}"
WEBHOOK_URL = f"{RENDER_EXTERNAL_URL}{WEBHOOK_PATH}"


@app.route(WEBHOOK_PATH, methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.update_queue.put_nowait(update)
    return "ok", 200


@app.route("/")
def index():
    return "✅ Bot Running"


async def set_webhook():
    await application.bot.set_webhook(WEBHOOK_URL)


if __name__ == "__main__":
    import asyncio

    asyncio.run(set_webhook())

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
