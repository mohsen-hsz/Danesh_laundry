import os
import logging
import threading
import asyncio
from flask import Flask, request
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

#  ✅ اضافه مهم — اتصال jsonbin
from jsonbin import reserve


# --- تنظیمات لاگ ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# --- متغیرهای محیطی ---
TOKEN = os.getenv("TOKEN")
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")

if not TOKEN:
    raise ValueError("❌ TOKEN is missing in environment variables.")
if not RENDER_EXTERNAL_URL:
    raise ValueError("❌ RENDER_EXTERNAL_URL is missing in environment variables.")

# --- Flask app ---
app = Flask(__name__)

# --- ساخت ربات ---
application = Application.builder().token(TOKEN).build()

# 🧩 initialize کردن application (خیلی مهم!)
asyncio.get_event_loop().run_until_complete(application.initialize())


# ===============================
# ✅ دستورات ربات
# ===============================

# ---------- /start ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام 👋 من ربات نوبت‌دهی هستم. برای تست ذخیره‌سازی /reserve_test را بزن ✅")

# ---------- /help ----------
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("💡 برای تست سیستم رزرو:\n/reserve_test را ارسال کن")


# ---------- ✅ تست رزرو واقعی ----------
async def reserve_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    # تاریخ تست — امروز
    from datetime import datetime
    date = datetime.now().strftime("%Y-%m-%d")

    # اسلات تست
    slot = 1

    # نام تست
    full_name = user.full_name if user.full_name else "Test User"

    ok, msg = reserve(date, slot, full_name, user.id)

    await update.message.reply_text(msg)


# ---------- دریافت متن معمولی ----------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    await update.message.reply_text(f"پیامت دریافت شد: {text}")


# ✅ ثبت Handler ها
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("help", help_command))
application.add_handler(CommandHandler("reserve_test", reserve_test))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))


# ===============================
# ✅ Webhook
# ===============================
WEBHOOK_PATH = f"/{TOKEN}"
WEBHOOK_URL = f"{RENDER_EXTERNAL_URL}{WEBHOOK_PATH}"

@app.route(WEBHOOK_PATH, methods=["POST"])
def webhook():
    try:
        update = Update.de_json(request.get_json(force=True), application.bot)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(application.process_update(update))
        loop.close()
    except Exception as e:
        logging.error(f"Webhook error: {e}")
    return "ok", 200


@app.route("/")
def index():
    return "✅ ربات فعاله — از /reserve_test برای تست ذخیره‌سازی استفاده کن"


# ---------- تنظیم Webhook ----------
async def set_webhook():
    webhook_info = await application.bot.get_webhook_info()
    if webhook_info.url != WEBHOOK_URL:
        logging.info(f"🔄 Setting new webhook to: {WEBHOOK_URL}")
        await application.bot.delete_webhook()
        await application.bot.set_webhook(url=WEBHOOK_URL)
    else:
        logging.info("✅ Webhook already set correctly.")


# ✅ اجرای Flask
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))

    # راه‌اندازی webhook قبل از اجرا
    asyncio.get_event_loop().run_until_complete(set_webhook())

    logging.info(f"🚀 Starting Flask on port {port}")
    app.run(host="0.0.0.0", port=port)
