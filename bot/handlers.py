from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters

# --- نمونه‌ی نمایش ظرفیت روزهای هفته (پر/خالی) ---
def _week_keyboard(availability: dict) -> InlineKeyboardMarkup:
    # availability: {"شنبه": True, "یکشنبه": False, ...}
    rows = []
    row = []
    for day, is_free in availability.items():
        emoji = "🟢" if is_free else "🔴"
        row.append(InlineKeyboardButton(f"{day} {emoji}", callback_data=f"day:{day}"))
        if len(row) == 2:
            rows.append(row); row = []
    if row:
        rows.append(row)
    return InlineKeyboardMarkup(rows)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام 👋 ربات فعاله. از /days برای دیدن ظرفیت هفته استفاده کن.")

async def days(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # فعلاً دمو (بعداً از storage میاریم)
    demo = {
        "شنبه": True, "یکشنبه": False, "دوشنبه": True, "سه‌شنبه": True,
        "چهارشنبه": False, "پنجشنبه": True, "جمعه": False
    }
    await update.message.reply_text(
        "وضعیت روزهای هفته:",
        reply_markup=_week_keyboard(demo)
    )

async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data.startswith("day:"):
        day = query.data.split(":", 1)[1]
        await query.edit_message_text(f"روز انتخابی: {day} ✅")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"پیامت رسید: {update.message.text}")

def register_handlers(app):
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("days", days))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    app.add_handler(  # برای دکمه‌ها
        __import__("telegram.ext").ext.CallbackQueryHandler(on_callback)
    )
