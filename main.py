import os
import logging
from flask import Flask, request
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)
import asyncio

# --- تنظیمات اولیه ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# --- بارگذاری متغیرهای محیطی ---
TOKEN = os.getenv("TOKEN")
JSONBIN_ID = os.getenv("JSONBIN_ID")
JSONBIN_KEY = os.getenv("JSONBIN_KEY")
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")

if not TOKEN:
    raise ValueError("❌ TOKEN is missing in environment variables.")
if not RENDER_EXTERNAL_URL:
    raise ValueError("❌ RENDER_EXTERNAL_URL is missing in environment variables.")
if not JSONBIN_ID or not JSONBIN_KEY:
    logging.warning("⚠️ JSONBIN credentials not set. JSONBIN features will be disabled.")

# --- Flask app برای Webhook ---
app = Flask(__name__)

# --- ساخت ربات ---
application = Application.builder().token(TOKEN).build()

# --- دستورات ربات ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام 👋 من ربات نوبت‌دهی هستم. لطفاً روز و ساعت مورد نظر خودت رو بفرست.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("برای رزرو زمان فقط روز و ساعت رو بفرست 😊")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    await update.message.reply_text(f"پیامت دریافت شد: {text}")

# --- افزودن هندلرها ---
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("help", help_command))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# --- آدرس Webhook ---
WEBHOOK_PATH = f"/{TOKEN}"
WEBHOOK_URL = f"{RENDER_EXTERNAL_URL}{WEBHOOK_PATH}"

# --- Flask Endpoint برای دریافت پیام از Telegram ---
@app.route(WEBHOOK_PATH, methods=["POST"])
def webhook():
    try:
        update = Update.de_json(request.get_json(force=True), application.bot)
        application.update_queue.put_nowait(update)
    except Exception as e:
        logging.error(f"Webhook error: {e}")
    return "ok", 200

# --- برای تست در مرورگر ---
@app.route("/")
def index():
    return "✅ ربات با موفقیت فعاله!"

# --- تابع راه‌اندازی Webhook ---
async def set_webhook():
    webhook_info = await application.bot.get_webhook_info()
    if webhook_info.url != WEBHOOK_URL:
        logging.info(f"Setting new webhook to: {WEBHOOK_URL}")
        await application.bot.delete_webhook()
        await application.bot.set_webhook(url=WEBHOOK_URL)
    else:
        logging.info("Webhook already set correctly.")

# --- اجرای برنامه ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))

    # تنظیم webhook قبل از شروع Flask
    asyncio.get_event_loop().run_until_complete(set_webhook())

    logging.info(f"Starting Flask app on port {port} ...")
    app.run(host="0.0.0.0", port=port)
