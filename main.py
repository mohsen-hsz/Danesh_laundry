import os
from flask import Flask, request
from telegram import Update
from telegram.ext import (
    Application, 
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters
)

# ===== ENV =====
TOKEN = os.environ.get("BOT_TOKEN")
WEBHOOK_URL = os.environ.get("RENDER_EXTERNAL_URL")   # e.g. https://danesh-laundry.onrender.com

# ===== Bot =====
application = Application.builder().token(TOKEN).build()

app = Flask(__name__)


# ----- Telegram handlers -----

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام! 👋\nربات رزرو لباس‌شویی آماده‌ست ✅"
    )

application.add_handler(CommandHandler("start", start))


# ===== Flask Webhook endpoint =====
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(force=True)
    update = Update.de_json(data, application.bot)
    application.update_queue.put_nowait(update)
    return "OK"


@app.route("/")
def home():
    return "Bot is running ✅"


# ===== Set webhook =====
async def set_webhook():
    full_url = f"{WEBHOOK_URL}/webhook"
    print("Setting webhook to:", full_url)
    await application.bot.set_webhook(full_url)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))

    import asyncio
    asyncio.run(set_webhook())

    print("✅ Flask running on port:", port)

    # Start flask ONLY
    app.run(host="0.0.0.0", port=port)
