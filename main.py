import os
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler
import asyncio

from handlers import start


# === ENV ===
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise Exception("❌ BOT_TOKEN not found in environment!")

# === Webhook URL ===
BASE_URL = os.getenv("RENDER_EXTERNAL_URL")
WEBHOOK_URL = f"{BASE_URL}/{TOKEN}"

# === PTB Application ===
application = Application.builder().token(TOKEN).build()

# === Add handlers ===
application.add_handler(CommandHandler("start", start))

# === Flask app ===
app = Flask(__name__)


@app.post(f"/{TOKEN}")
async def process_webhook():
    """Telegram sends update → pass to application """
    update = Update.de_json(request.json, application.bot)
    await application.process_update(update)
    return "OK", 200


@app.get("/")
def index():
    return "✅ Telegram bot is running", 200


async def setup_webhook():
    """Delete old webhook & set new one"""
    await application.bot.delete_webhook(drop_pending_updates=True)
    await application.bot.set_webhook(WEBHOOK_URL)
    print(f"✅ Webhook set: {WEBHOOK_URL}")


def main():
    # set webhook
    asyncio.run(setup_webhook())

    # run flask
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
