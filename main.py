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

# ───── ENV ──────────────────────────────────────────────────────
TOKEN = os.getenv("TOKEN") or "8439374401:AAFaFj5NvFaCDB5HvpReQUQ89mNtjYGB6EM"
RENDER_URL = os.getenv("RENDER_EXTERNAL_URL") or "https://danesh-laundry.onrender.com"
WEBHOOK_URL = f"{RENDER_URL}/{TOKEN}"

# ───── Logging ─────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s — %(name)s — %(levelname)s — %(message)s",
)
log = logging.getLogger("main")

# ───── Flask ───────────────────────────────────────────────────
app = Flask(__name__)

# ───── Telegram Application ─────────────────────────────────────
application: Application = (
    ApplicationBuilder()
    .token(TOKEN)
    .updater(None)   # لازم برای Webhook
    .build()
)


# ───── Handlers ────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ ربات آماده است، پیام بفرستید")


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"پیام دریافت شد:\n\n{update.message.text}")


application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))


# ───── Webhook endpoint ────────────────────────────────────────
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    data = request.get_json()

    if not data:
        return "no data", 400

    update = Update.de_json(data, application.bot)

    # اجرای امن async
    asyncio.run(application.process_update(update))

    return "ok"


# ───── Root Check ─────────────────────────────────────────────
@app.route("/", methods=["GET"])
def index():
    return "Bot Running ✅"


# ───── Init & Set Webhook ─────────────────────────────────────
async def setup():
    """Initialize bot & set webhook"""
    await application.initialize()
    await application.bot.delete_webhook(drop_pending_updates=True)
    await application.bot.set_webhook(WEBHOOK_URL)
    log.info(f"✅ Webhook set: {WEBHOOK_URL}")


if __name__ == "__main__":
    # Set webhook on startup
    asyncio.run(setup())

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
