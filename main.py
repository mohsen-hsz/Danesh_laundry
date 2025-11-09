from flask import Flask, request
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

# ENV
TOKEN = os.environ.get("BOT_TOKEN")
JSONBIN_KEY = os.environ.get("JSONBIN_KEY")
WEBHOOK_URL = os.environ.get("RENDER_EXTERNAL_URL")  # → خود render می‌سازه

app = Flask(__name__)

# Init bot
application = Application.builder().token(TOKEN).build()


# ===== handlers =====

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام! 👋\nربات رزرو لباس‌شویی آماده‌ست.")


application.add_handler(CommandHandler("start", start))


# ===== Webhook endpoint =====
@app.route("/webhook", methods=["POST"])
def webhook():
    """Handle Telegram webhooks"""
    data = request.get_json(force=True)
    update = Update.de_json(data, application.bot)
    application.update_queue.put_nowait(update)
    return "ok"


@app.route("/")
def home():
    return "Bot running ✅"


# ===== set webhook =====
async def set_webhook():
    await application.bot.set_webhook(f"{WEBHOOK_URL}/webhook")


if __name__ == "__main__":
    print("✅ Starting Flask")

    # Start bot + Flask
    application.run_polling()  # still needed so handlers work

    # Set webhook
    import asyncio
    asyncio.run(set_webhook())

    # Run Flask
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 10000))
    )
