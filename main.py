import os
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = f"{os.getenv('RENDER_EXTERNAL_URL')}/{TOKEN}"

app = Flask(__name__)
application = Application.builder().token(TOKEN).build()


# ─────────  HANDLERS  ─────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot is running!")


application.add_handler(CommandHandler("start", start))


# ─────────  FLASK WEBHOOK  ─────────
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.update_queue.put_nowait(update)
    return "OK", 200


def main():
    application.bot.delete_webhook()

    # ✅ تنظیم webhook صحیح
    application.bot.set_webhook(WEBHOOK_URL)

    print("✅ Webhook set to", WEBHOOK_URL)

    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
