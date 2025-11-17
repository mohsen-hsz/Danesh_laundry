import os
import time
import threading
from datetime import datetime
from zoneinfo import ZoneInfo

import requests

# ==============================
# تنظیمات و ثابت‌ها
# ==============================
JSONBIN_KEY = os.getenv("JSONBIN_KEY")
JSONBIN_ID = os.getenv("JSONBIN_ID")
BOT_TOKEN = os.getenv("TOKEN") or os.getenv("TELEGRAM_TOKEN", "")

if not JSONBIN_KEY or not JSONBIN_ID:
    raise RuntimeError("❌ JSONBIN_KEY یا JSONBIN_ID در ENV تنظیم نشده است.")

BASE_URL = f"https://api.jsonbin.io/v3/b/{JSONBIN_ID}"
CAPACITY = 3  # تعداد اسلات‌های هر روز (18-19 ، 19-20 ، 20-21)


# ==============================
# کمک‌تابع‌های زمان
# ==============================
def now_tehran():
    return datetime.now(ZoneInfo("Asia/Tehran"))


def today_str():
    return now_tehran().strftime("%Y-%m-%d")


# ==============================
# خواندن / نوشتن JSONBin
# ==============================
def get_data():
    resp = requests.get(BASE_URL, headers={"X-Master-Key": JSONBIN_KEY})
    resp.raise_for_status()
    data = resp.json().get("record", {})
    return ensure_structure(data)


def save_data(data: dict):
    resp = requests.put(BASE_URL, json=data, headers={"X-Master-Key": JSONBIN_KEY})
    resp.raise_for_status()


# ==============================
# اطمینان از ساختار صحیح دیتا
# ==============================
def ensure_structure(data: dict) -> dict:
    days = ["شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه",
            "چهارشنبه", "پنجشنبه", "جمعه"]

    if "last_reset" not in data:
        data["last_reset"] = today_str()

    if "users" not in data or not isinstance(data["users"], list):
        data["users"] = []

    for d in days:
        if d not in data or not isinstance(data[d], list) or len(data[d]) != CAPACITY:
            data[d] = [False] * CAPACITY

    return data


# ==============================
# ثبت کاربر برای ارسال پیام عمومی
# ==============================
def register_user(chat_id: int):
    data = get_data()
    users = data.get("users", [])
    if chat_id not in users:
        users.append(chat_id)
        data["users"] = users
        save_data(data)


# ==============================
# ارسال پیام تلگرام
# ==============================
def send_telegram(chat_id: int, text: str):
    if not BOT_TOKEN:
        print("⚠️ TOKEN در ENV تنظیم نشده، امکان ارسال پیام نیست.")
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print("⚠️ خطا در ارسال پیام:", e)


def broadcast_to_all_users(text: str):
    data = get_data()
    users = data.get("users", [])
    print(f"📢 Broadcast به {len(users)} کاربر")
    for uid in users:
        send_telegram(uid, text)


# ==============================
# منطق ریست هفتگی
# ==============================
def need_reset(data=None) -> bool:
    """فقط جمعه و فقط اگر برای امروز last_reset ثبت نشده باشد."""
    if data is None:
        data = get_data()

    last_reset = data.get("last_reset", "")
    now = now_tehran()

    # جمعه = 4 (Monday=0)
    if now.weekday() != 4:
        return False

    return last_reset != today_str()


def reset_reservations():
    """پاک‌کردن تمام رزروها و نگه‌داشتن لیست users."""
    old_data = get_data()
    users = old_data.get("users", [])

    days = ["شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه",
            "چهارشنبه", "پنجشنبه", "جمعه"]

    new_data = {
        "last_reset": today_str(),
        "users": users
    }

    for d in days:
        new_data[d] = [False] * CAPACITY

    save_data(new_data)
    print("🧹 Weekly RESET done (جمعه 00:00 به وقت ایران)")

    # پیام به همه کاربران
    broadcast_to_all_users("📢 رزروهای این هفته ریست شدند. می‌توانید دوباره رزرو کنید!")

    return True


def auto_reset_worker():
    """Thread بک‌گراند برای ریست جمعه ساعت 00:00."""
    while True:
        try:
            now = now_tehran()
            if now.weekday() == 4 and now.hour == 0 and now.minute == 0:
                if need_reset():
                    reset_reservations()
            time.sleep(30)
        except Exception as e:
            print("❌ Auto-reset error:", e)
            time.sleep(60)


# شروع thread ریست خودکار
threading.Thread(target=auto_reset_worker, daemon=True, name="auto-reset").start()


# ==============================
# رزرو
# ==============================
def reserve(day: str, slot: int, full_name: str, telegram_id: int):
    """day: نام روز؛ slot: ایندکس 0..2؛ full_name, telegram_id."""
    register_user(telegram_id)

    data = get_data()

    # اگر جمعه شده و هنوز reset نشده
    if need_reset(data):
        reset_reservations()
        data = get_data()

    if day not in data:
        return False, "❌ روز واردشده معتبر نیست."

    if slot < 0 or slot >= CAPACITY:
        return False, "❌ بازه زمانی نامعتبر است."

    if data[day][slot] not in (False, None):
        return False, "❌ این بازه قبلاً رزرو شده است."

    data[day][slot] = {
        "name": full_name,
        "id": telegram_id
    }

    save_data(data)
    return True, "✅ رزرو با موفقیت ثبت شد."


# ==============================
# کنسل‌کردن
# ==============================
def cancel_reservation(telegram_id: int):
    register_user(telegram_id)

    data = get_data()
    removed = False

    days = ["شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه",
            "چهارشنبه", "پنجشنبه", "جمعه"]

    for d in days:
        slots = data.get(d, [])
        if not isinstance(slots, list):
            continue
        for i in range(len(slots)):
            cell = slots[i]
            if isinstance(cell, dict) and cell.get("id") == telegram_id:
                data[d][i] = False
                removed = True

    if removed:
        save_data(data)
        return True, "🔄 تمام رزروهای شما لغو شدند."
    else:
        return False, "❌ رزروی برای شما یافت نشد."


# ==============================
# تقویم هفتگی
# ==============================
def get_calendar() -> str:
    """متن وضعیت رزرو هفتگی را برمی‌گرداند."""
    data = get_data()

    days = ["شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه",
            "چهارشنبه", "پنجشنبه", "جمعه"]
    slot_labels = ["18-19", "19-20", "20-21"]

    text = "📅 *وضعیت رزرو هفتگی*\n\n"

    for d in days:
        text += f"📌 *{d}*\n"
        slots = data.get(d, [False] * CAPACITY)

        for i in range(CAPACITY):
            cell = slots[i] if i < len(slots) else False
            if not cell:
                text += f"▫️ {slot_labels[i]} → خالی\n"
            else:
                name = cell.get("name", "نامشخص")
                text += f"🔴 {slot_labels[i]} → رزرو شده توسط *{name}*\n"
        text += "\n"

    return text
