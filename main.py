# main.py
import os
import json
import requests
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

# -----------------------
# محیط (از Render یا GitHub Secrets خوانده می‌شوند)
# -----------------------
TOKEN = os.getenv('8439374401:AAFN1JdCkTHK3uee5wquHyCTZHYByUk4ljU')              # توکن تلگرام (BotFather)
JSONBIN_ID = os.getenv('691062a5ae596e708f4dfd76')    # bin id از JSONBin
JSONBIN_KEY = os.getenv('$$2a$10$AQl3rws35jnF0RJXuK0lq.c/NbCcDFJOBA3FqhNi2.vEG9cfQE2tS')  # API Key از JSONBin

if not TOKEN or not JSONBIN_ID or not JSONBIN_KEY:
    raise SystemExit("ERROR: TOKEN, JSONBIN_ID or JSONBIN_KEY not set in environment variables.")

BASE_URL = f"https://api.jsonbin.io/v3/b/{JSONBIN_ID}"
HEADERS = {
    "Content-Type": "application/json",
    "X-Master-Key": JSONBIN_KEY
}

# -----------------------
# توابع خواندن/نوشتن امن روی JSONBin
# -----------------------
def load_remote():
    """دریافت JSON از JSONBin"""
    r = requests.get(BASE_URL, headers=HEADERS, timeout=10)
    r.raise_for_status()
    payload = r.json()
    return payload.get("record", {})

def save_remote(data):
    """ذخیره (PUT) داده در JSONBin"""
    r = requests.put(BASE_URL, headers=HEADERS, json=data, timeout=10)
    r.raise_for_status()
    return r.json()

# -----------------------
# تولید اسلات‌های نیم‌ساعته (قابل تغییر)
# -----------------------
def generate_slots(start_hour=17, start_min=30, end_hour=23, step=30):
    slots = []
    h = start_hour
    m = start_min
    while (h < end_hour) or (h == end_hour and m == 0):
        slots.append(f"{h:02d}:{m:02d}")
        m += step
        if m >= 60:
            h += 1
            m -= 60
    return slots

def make_default_data():
    days = ["شنبه","یکشنبه","دوشنبه","سه‌شنبه","چهارشنبه","پنجشنبه","جمعه"]
    slot_list = generate_slots(17,30,23,30)
    slots = {d: {s: None for s in slot_list} for d in days}
    return {"meta": {"version":1}, "slots": slots}

# -----------------------
# بارگذاری اولیه (اگر خالی یا خراب بود، مقدار پیش‌فرض می‌سازد)
# -----------------------
try:
    reservations = load_remote()
    if not reservations:
        reservations = make_default_data()
        save_remote(reservations)
except Exception as e:
    # خطای ارتباط با JSONBin -> می‌زنیم مقدار محلی اولیه و اجازه میدیم که کار کند
    print("⚠️ خطا در ارتباط با JSONBin:", e)
    reservations = make_default_data()

# -----------------------
# UI و دستورات
# -----------------------
main_keyboard = [["📅 نمایش روزها", "🧺 رزرو روز"]]
reply_markup = ReplyKeyboardMarkup(main_keyboard, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام 👋\nربات رزرو لباس‌شویی فعال است.", reply_markup=reply_markup)

async def show_days(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "🧺 وضعیت اسلات‌ها:\n\n"
    slots = reservations.get("slots", {})
    for day, day_slots in slots.items():
        booked_count = sum(1 for v in day_slots.values() if v is not None)
        total = len(day_slots)
        text += f"{day}: {booked_count}/{total} رزرو شده\n"
    await update.message.reply_text(text)

async def reserve_slot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # فرمت پیشنهادی: /reserve شنبه 18:00
    if len(context.args) < 2:
        await update.message.reply_text("فرمت: /reserve <روز> <ساعت>\nمثال: /reserve سه‌شنبه 18:00")
        return

    day = context.args[0]
    time = context.args[1]

    slots = reservations.get("slots", {})
    if day not in slots:
        await update.message.reply_text("❌ نام روز نامعتبر است.")
        return
    if time not in slots[day]:
        await update.message.reply_text("❌ زمان نامعتبر است. از قالب HH:MM استفاده کن.")
        return
    if slots[day][time] is not None:
        await update.message.reply_text("❌ این بازه قبلاً رزرو شده.")
        return

    user = update.effective_user
    reserve_info = {
        "user_id": user.id,
        "username": user.username,
        "full_name": user.full_name,
        "reserved_at": __import__("datetime").datetime.utcnow().isoformat()
    }
    slots[day][time] = reserve_info

    # ذخیره به JSONBin
    try:
        save_remote(reservations)
    except Exception as e:
        await update.message.reply_text("❗ خطا در ذخیره‌سازی ابری: رزرو محلی انجام شد اما ممکن است همگام‌سازی نشود.")
        print("Save error:", e)
        return

    await update.message.reply_text(f"✅ رزرو انجام شد: {day} - {time}")

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == "📅 نمایش روزها":
        await show_days(update, context)
    elif text == "🧺 رزرو روز":
        await update.message.reply_text("برای رزرو، از دستور زیر استفاده کن:\n/reserve سه‌شنبه 18:00")
    else:
        await update.message.reply_text("دستور نامعتبر.")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("days", show_days))
    app.add_handler(CommandHandler("reserve", reserve_slot))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_buttons))
    print("🤖 Bot running (using JSONBin for storage)...")
    app.run_polling()

if __name__ == "__main__":
    main()
