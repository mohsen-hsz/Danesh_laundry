from telegram import Update
from telegram.ext import ContextTypes

from services.jsonbin_service import get_days


async def show_days(update: Update, context: ContextTypes.DEFAULT_TYPE):

    data = await get_days()

    msg = "📅 وضعیت روزها:\n\n"

    for day, status in data.items():
        state = "✅ خالی" if not status else "❌ پر"
        msg += f"{day} → {state}\n"

    await update.message.reply_text(msg)
