import os
import logging
from flask import Flask, request
from telegram import Update
from telegram.ext import Application

from handlers.commands import register_commands
from webhook_setup import setup_webhook


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

TOKEN = os.getenv("TOKEN")
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")

if not TOKEN:
    raise ValueError("TOKEN not set!")

app = Flask(__name__)

application = Application.builder().token(TOKEN).build()

# ثبت هندلرها
register_commands(application)


# ---------------- Webhook route ----------------
@app.route(f"/{TOKEN}", methods=["POST"])
async def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    await application.process_update(update)
    return "ok", 200


@app.route("/")
def index():
    return "Bot active ✅"


if __name__ == "__main__":
    import asyncio
    asyncio.run(setup_webhook(application, TOKEN, RENDER_EXTERNAL_URL))

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
