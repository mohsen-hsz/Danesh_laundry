import os
import requests
from datetime import datetime
from zoneinfo import ZoneInfo  # ✅ جایگزین pytz

JSONBIN_KEY = os.getenv("JSONBIN_KEY")
JSONBIN_ID  = os.getenv("JSONBIN_ID")

if not JSONBIN_KEY or not JSONBIN_ID:
    raise RuntimeError("❌ JSONBIN_KEY / JSONBIN_ID missing in environment")

BASE_URL = f"https://api.jsonbin.io/v3/b/{JSONBIN_ID}"


def today_str():
    """Return today date in Iran timezone (YYYY-MM-DD)"""
    return datetime.now(ZoneInfo("Asia/Tehran")).strftime("%Y-%m-%d")


def get_data():
    r = requests.get(BASE_URL, headers={"X-Master-Key": JSONBIN_KEY})
    if r.status_code != 200:
        raise RuntimeError("❌ JSONBIN read error")
    return r.json()["record"]


def save_data(data: dict):
    r = requests.put(BASE_URL, json=data, headers={"X-Master-Key": JSONBIN_KEY})
    if r.status_code != 200:
        raise RuntimeError("❌ JSONBIN write error")


# ------------------------------------------------
# RESET
# ------------------------------------------------
def need_reset(data=None):
    """Return True if it's time to reset (جمعه 00:00 به وقت ایران)"""
    if data is None:
        data = get_data()

    last_reset = data.get("last_reset", "")
    now = datetime.now(ZoneInfo("Asia/Tehran"))

    # جمعه = weekday() == 4 (Monday=0 ... Friday=4)
    if now.weekday() != 4:
        return False

    # اگر امروز جمعه است و هنوز برای امروز reset نشده:
    return last_reset != today_str()


def reset_reservations():
    """Reset all days + save last_reset"""
    data = {
        "last_reset": today_str(),
        "شنبه": False,
        "یکشنبه": False,
        "دوشنبه": False,
        "سه‌شنبه": False,
        "چهارشنبه": False,
        "پنجشنبه": False,
        "جمعه": False
    }
    save_data(data)
    return True


# ------------------------------------------------
# RESERVE
# ------------------------------------------------
def reserve(day, slot, full_name, telegram_id):
    data = get_data()

    # اگر لازم است (اولین تعامل بعد از جمعه 00:00)، ریست کنیم
    if need_reset(data):
        reset_reservations()
        data = get_data()

    # اگر برای این روز رزروی وجود دارد، اجازه نده
    if data.get(day) not in (False, None):
        return False, "❌ این روز قبلاً رزرو شده است."

    data[day] = {
        "slot": slot,
        "name": full_name,
        "id": telegram_id
    }
    save_data(data)
    return True, "✅ رزرو با موفقیت ثبت شد."


# ------------------------------------------------
# CANCEL
# ------------------------------------------------
def cancel_reservation(telegram_id):
    data = get_data()

    removed = False
    for day, val in data.items():
        if isinstance(val, dict) and val.get("id") == telegram_id:
            data[day] = False
            removed = True

    if removed:
        save_data(data)
        return True, "✅ رزرو شما لغو شد."
    else:
        return False, "❌ رزروی برای شما یافت نشد."
