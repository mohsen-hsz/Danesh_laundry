from telegram import Update
from telegram.ext import CommandHandler, ContextTypes, MessageHandler, filters


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام 👋 لطفاً روز و ساعت رو ارسال کن")


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("برای رزرو روز و ساعت پیام بده ✅")


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"پیام شما: {update.message.text}")


def register_commands(app):
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, echo)
    )
