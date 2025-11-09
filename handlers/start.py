from telegram import Update
from telegram.ext import ContextTypes
from utils.keyboard import main_keyboard


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام 👋 من ربات نوبت‌دهی هستم.\nیکی از گزینه‌هارو انتخاب کن:",
        reply_markup=main_keyboard()
    )
