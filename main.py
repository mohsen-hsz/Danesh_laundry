import os
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler
import asyncio

from handlers import start


TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise Exception("❌ BOT_TOKEN not found in environment!")

BASE_URL = os.getenv("RENDER_EXTERNAL_URL")
WEBHOOK_URL = f"{BASE_URL}/{TOKEN}"


application = Application.builder().token(TOKEN).build()
application.add_handler(CommandHandler("start", start))


app = Flask(__name__)


@app.post(f"/{TOKEN}")
def process_webhook():
    update = Update.de_json(request.json, application.bot)
    asyncio.run(application.process_update(update))
    return "OK", 200


@app.get("/")
def index():
    return "✅ Bot running", 200


async def setup_webhook():
    await application.bot.delete_webhook(drop_pending_updates=True)
    await application.bot.set_webhook(WEBHOOK_URL)
    print(f"✅ Webhook set → {WEBHOOK_URL}")


def main():
    asyncio.run(setup_webhook())
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
