import os
import requests
from datetime import datetime
from zoneinfo import ZoneInfo
import time
import threading

JSONBIN_KEY = os.getenv("JSONBIN_KEY")
JSONBIN_ID  = os.getenv("JSONBIN_ID")

BASE_URL = f"https://api.jsonbin.io/v3/b/{JSONBIN_ID}"
CAPACITY = 3


# ---------------------------------------------------------
#       کمک‌کننده زمان ایران
# ---------------------------------------------------------
def now_tehran():
    return datetime.now(ZoneInfo("Asia/Tehran"))


def today_str():
    return now_tehran().strftime("%Y-%m-%d")


# ---------------------------------------------------------
#          عملیات JSONBin
# ---------------------------------------------------------
def get_data():
    r = requests.get(BASE_URL, headers={"X-Master-Key": JSONBIN_KEY})
    return r.json()["record"]


def save_data(data: dict):
    requests.put(BASE_URL, json=data, headers={"X-Master-Key": JSONBIN_KEY})


# ---------------------------------------------------------
#       تشخیص نیاز به reset (هر شب ۰۰:۰۰)
# ---------------------------------------------------------
def need_reset(data=None):
    if data is None:
        data = get_data()

    last_reset = data.get("last_reset", "")
    today      = today_str()

    # اگر امروز reset نشده → باید reset کنیم
    return last_reset != today


# ---------------------------------------------------------
#              ریست کردن کل رزروها
# ---------------------------------------------------------
def reset_reservations():
    data = {"last_reset": today_str()}

    days = ["شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه",
            "چهارشنبه", "پنجشنبه", "جمعه"]

    for d in days:
        data[d] = [False] * CAPACITY

    save_data(data)
    print("🧹 RESET DONE (00:00 Tehran)")
    return True


# ---------------------------------------------------------
#     Thread پس‌زمینه → اجرا دقیق هر شب ۰۰:۰۰ تهران
# ---------------------------------------------------------
def auto_reset_worker():
    while True:
        try:
            now = now_tehran()

            # دقیقاً ساعت 00:00 → reset
            if now.hour == 0 and now.minute == 0:
                if need_reset():
                    reset_reservations()

            # چک هر 30 ثانیه
            time.sleep(30)

        except Exception as e:
            print("❌ Auto-reset error:", e)
            time.sleep(60)


threading.Thread(target=auto_reset_worker, daemon=True).start()

# ---------------------------------------------------------
#            بقیه توابع رزرو / کنسل
# ---------------------------------------------------------
def reserve(day, slot, full_name, telegram_id):
    data = get_data()

    if need_reset(data):
        reset_reservations()
        data = get_data()

    if day not in data:
        return False, "❌ روز نامعتبر"

    if slot < 0 or slot >= CAPACITY:
        return False, "❌ بازه نامعتبر"

    if data[day][slot] not in (False, None):
        return False, "❌ این بازه پر است"

    data[day][slot] = {"name": full_name, "id": telegram_id}
    save_data(data)

    return True, "✅ رزرو با موفقیت ثبت شد."


def cancel_reservation(telegram_id):
    data = get_data()
    removed = False

    days = ["شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه",
            "چهارشنبه", "پنجشنبه", "جمعه"]

    for d in days:
        for i in range(CAPACITY):
            slot = data[d][i]
            if isinstance(slot, dict) and slot.get("id") == telegram_id:
                data[d][i] = False
                removed = True

    if removed:
        save_data(data)
        return True, "🔄 رزرو شما لغو شد."
    else:
        return False, "❌ رزروی یافت نشد."
