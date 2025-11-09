import os
import logging
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

TOKEN = os.getenv("TOKEN")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# ✅ Handlers
async def start(update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ ربات فعاله")

async def echo(update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"پیام دریافت شد:\n{update.message.text}")

# ✅ Main
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    port = int(os.environ.get("PORT", 10000))

    app.run_webhook(
        listen="0.0.0.0",
        port=port,
        webhook_url=f"{os.getenv('RENDER_EXTERNAL_URL')}/{TOKEN}"
    )

if __name__ == "__main__":
    main()
