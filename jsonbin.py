import os
import requests
from datetime import datetime
from zoneinfo import ZoneInfo
import time
import threading

# ============================================================
#  LOAD ENV
# ============================================================
JSONBIN_KEY = os.getenv("JSONBIN_KEY")
JSONBIN_ID  = os.getenv("JSONBIN_ID")

if not JSONBIN_KEY or not JSONBIN_ID:
    raise RuntimeError("❌ JSONBIN_KEY / JSONBIN_ID is missing in ENV")

BASE_URL = f"https://api.jsonbin.io/v3/b/{JSONBIN_ID}"
CAPACITY = 3  # تعداد ظرفیت رزرو در هر روز


# ============================================================
#  HELPERS
# ============================================================
def today_str():
    """Return today's date in Iran timezone."""
    return datetime.now(ZoneInfo("Asia/Tehran")).strftime("%Y-%m-%d")


def now_tehran():
    """Return now() in Iran timezone."""
    return datetime.now(ZoneInfo("Asia/Tehran"))


# ============================================================
#  JSONBIN READ / WRITE
# ============================================================
def get_data():
    r = requests.get(BASE_URL, headers={"X-Master-Key": JSONBIN_KEY})
    if r.status_code != 200:
        raise RuntimeError("❌ ERROR reading JSONBin")
    return r.json()["record"]


def save_data(data: dict):
    r = requests.put(BASE_URL, json=data, headers={"X-Master-Key": JSONBIN_KEY})
    if r.status_code != 200:
        raise RuntimeError("❌ ERROR writing JSONBin")


# ============================================================
#  AUTO RESET LOGIC
# ============================================================
def need_reset(data=None):
    """Return True if it's Friday midnight (Tehran) and not reset yet."""
    if data is None:
        data = get_data()

    last_reset = data.get("last_reset", "")
    now = now_tehran()

    # جمعه == weekday 4  (Monday=0, Friday=4)
    if now.weekday() != 4:
        return False

    # هنوز reset امروز انجام نشده
    return last_reset != today_str()


def reset_reservations():
    """Reset all daily reservations."""
    data = {"last_reset": today_str()}

    days = ["شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه",
            "چهارشنبه", "پنجشنبه", "جمعه"]

    for d in days:
        data[d] = [False] * CAPACITY

    save_data(data)
    print("🧹 RESET: all reservations cleared.")

    return True


def auto_reset_worker():
    """Background thread checking periodic reset."""
    while True:
        try:
            if need_reset():
                print("🧹 Auto-RESET triggered at Friday midnight (Iran)")
                reset_reservations()
        except Exception as e:
            print("❌ Auto-reset error:", e)

        time.sleep(600)  # check every 10 minutes


# Launch auto reset in background
threading.Thread(target=auto_reset_worker, daemon=True).start()


# ============================================================
#  RESERVE
# ============================================================
def reserve(day, slot, full_name, telegram_id):
    """Reserve a slot (0,1,2) for a day."""
    data = get_data()

    # اگر لازم است reset انجام شود (جمعه نیمه شب)
    if need_reset(data):
        reset_reservations()
        data = get_data()

    if day not in data:
        return False, "❌ روز وارد شده معتبر نیست."

    # ساختار را تضمین می‌کنیم
    if not isinstance(data[day], list) or len(data[day]) != CAPACITY:
        data[day] = [False] * CAPACITY

    if slot < 0 or slot >= CAPACITY:
        return False, "❌ بازه زمانی نامعتبر است."

    # اگر اسلات پر باشد
    if data[day][slot] not in (False, None):
        return False, "❌ این بازه قبلاً رزرو شده است."

    # ذخیره
    data[day][slot] = {
        "name": full_name,
        "id": telegram_id
    }

    save_data(data)
    return True, "✅ رزرو با موفقیت ثبت شد."


# ============================================================
#  CANCEL
# ============================================================
def cancel_reservation(telegram_id):
    """Remove ALL reservations for this user."""
    data = get_data()
    removed = False

    days = ["شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه",
            "چهارشنبه", "پنجشنبه", "جمعه"]

    for d in days:
        if isinstance(data.get(d), list):
            for i in range(CAPACITY):
                cell = data[d][i]
                if isinstance(cell, dict) and cell.get("id") == telegram_id:
                    data[d][i] = False
                    removed = True

    if removed:
        save_data(data)
        return True, "🔄 رزرو شما لغو شد."
    else:
        return False, "❌ رزروی برای شما یافت نشد."
