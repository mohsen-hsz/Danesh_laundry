import os
import logging
import asyncio
from flask import Flask, request
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

TOKEN = os.getenv("TOKEN") or "YOUR_TOKEN_HERE"
RENDER_URL = os.getenv("RENDER_EXTERNAL_URL") or "https://danesh-laundry.onrender.com"
WEBHOOK_URL = f"{RENDER_URL}/{TOKEN}"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s — %(name)s — %(levelname)s — %(message)s",
)
log = logging.getLogger("main")

app = Flask(__name__)

# ✅ Single global loop
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

# ✅ telegram application on top of SAME loop
application: Application = (
    ApplicationBuilder()
    .token(TOKEN)
    .updater(None)
    .build()
)


# ─────────── handlers ───────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ ربات آماده است")


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"پیام دریافت شد:\n{update.message.text}")


application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))


# ─────────── webhook endpoint ───────────
@app.post(f"/{TOKEN}")
def webhook():
    data = request.get_json()

    if not data:
        return "no json", 400

    update = Update.de_json(data, application.bot)

    # ✅ Use shared loop
    loop.create_task(application.process_update(update))

    return "ok"


@app.get("/")
def home():
    return "Bot Running ✅"


# ─────────── init webhook ───────────
async def setup():
    await application.initialize()
    await application.bot.delete_webhook(drop_pending_updates=True)
    await application.bot.set_webhook(WEBHOOK_URL)
    log.info(f"✅ Webhook set: {WEBHOOK_URL}")


if __name__ == "__main__":
    loop.run_until_complete(setup())

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
