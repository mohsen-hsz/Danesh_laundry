import os
from flask import Flask, request
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# -------------------------
# 🔹 Load ENV token
# -------------------------
TOKEN = os.environ.get("BOT_TOKEN")

if not TOKEN:
    raise ValueError("❌ BOT_TOKEN is not set in environment variables.")


# -------------------------
# 🔹 Create Telegram Application
# -------------------------
application = Application.builder().token(TOKEN).build()


# -------------------------
# ✅ Handlers
# -------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام 👋 ربات به درستی وصله ✅")


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(update.message.text)


# Register handlers
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))


# -------------------------
# ✅ Flask Web Server
# -------------------------
app = Flask(__name__)


@app.get("/")
def index():
    return "Bot is running ✅"


@app.post("/")
def webhook():
    """
    Telegram webhook target
    """
    json_data = request.get_json(force=True)

    if not json_data:
        return "No JSON", 400

    update = Update.de_json(json_data, application.bot)

    # ✅ push update to PTB queue
    application.update_queue.put_nowait(update)
    return "ok", 200


# -------------------------
# ✅ Start both Flask + PTB
# -------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    print(f"✅ Server Running on port {port}")

    # ✅ Start PTB as async background
    application.run_webhook(
        listen="0.0.0.0",
        port=port,
        url_path="",
    )

    # Optional: Keep Flask active
    app.run(host="0.0.0.0", port=port)
