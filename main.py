import json
import os
from typing import final
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

# -------------------------------
# تنظیمات پایه
# -------------------------------
TOKEN: final = '8439374401:AAFN1JdCkTHK3uee5wquHyCTZHYByUk4ljU'
BOT_USERNAME: final = '@lebas_shoii_bot'
DATA_FILE = "reservations.json"

# -------------------------------
# تابع خواندن و ذخیره داده‌ها
# -------------------------------
def load_reservations():
    if not os.path.exists(DATA_FILE):
        print("⚠️ فایل رزرو پیدا نشد، ایجاد شد.")
        data = {
            "شنبه": False,
            "یکشنبه": False,
            "دوشنبه": False,
            "سه‌شنبه": False,
            "چهارشنبه": False,
            "پنجشنبه": False,
            "جمعه": False
        }
        save_reservations(data)
        return data

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, dict):
                raise ValueError("فرمت JSON اشتباه است.")
            return data
    except (json.JSONDecodeError, ValueError):
        print("⚠️ فایل JSON خراب بود، فایل جدید ساخته شد.")
        data = {
            "شنبه": False,
            "یکشنبه": False,
            "دوشنبه": False,
            "سه‌شنبه": False,
            "چهارشنبه": False,
            "پنجشنبه": False,
            "جمعه": False
        }
        save_reservations(data)
        return data

def save_reservations(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# -------------------------------
# داده‌های رزرو از فایل
# -------------------------------
reservations = load_reservations()

# -------------------------------
# منوی اصلی
# -------------------------------
main_keyboard = [
    ["📅 نمایش روزها", "🧺 رزرو روز"],
]
reply_markup = ReplyKeyboardMarkup(main_keyboard, resize_keyboard=True)

# -------------------------------
# دستور start
# -------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام 👋\nبه ربات رزرو لباس‌شویی خوش اومدی!\nاز دکمه‌های زیر استفاده کن:",
        reply_markup=reply_markup
    )

# -------------------------------
# نمایش وضعیت روزها
# -------------------------------
async def show_days(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "🧺 وضعیت روزهای رزرو:\n\n"
    for day, reserved in reservations.items():
        status = "❌ پر شده" if reserved else "✅ خالی"
        text += f"{day}: {status}\n"
    await update.message.reply_text(text)

# -------------------------------
# رزرو روز
# -------------------------------
async def reserve_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) == 0:
        await update.message.reply_text("⚠️ لطفاً بعد از دستور، نام روز را بنویسید.\nمثال: /reserve دوشنبه")
        return

    day = context.args[0]

    if day not in reservations:
        await update.message.reply_text("❌ همچین روزی وجود ندارد. لطفاً یکی از روزهای هفته را بنویسید.")
        return

    if reservations[day]:
        await update.message.reply_text(f"❌ روز {day} قبلاً رزرو شده است.")
    else:
        reservations[day] = True
        save_reservations(reservations)
        await update.message.reply_text(f"✅ روز {day} با موفقیت رزرو شد.")

# -------------------------------
# پاسخ به دکمه‌ها
# -------------------------------
async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == "📅 نمایش روزها":
        await show_days(update, context)
    elif text == "🧺 رزرو روز":
        await update.message.reply_text("برای رزرو از دستور زیر استفاده کن:\nمثال:\n/reserve سه‌شنبه")
    else:
        await update.message.reply_text("❓ دستور نامعتبر است. از دکمه‌ها استفاده کن.")

# -------------------------------
# اجرای ربات
# -------------------------------
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("days", show_days))
    app.add_handler(CommandHandler("reserve", reserve_day))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_buttons))

    print(" Robot started...🤖")
    app.run_polling()

# -------------------------------
# اجرای برنامه
# -------------------------------
if __name__ == "__main__":
    main()
