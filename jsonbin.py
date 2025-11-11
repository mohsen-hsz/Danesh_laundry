import os
import requests
from datetime import datetime
from zoneinfo import ZoneInfo  # timezone

JSONBIN_KEY = os.getenv("JSONBIN_KEY")
JSONBIN_ID  = os.getenv("JSONBIN_ID")

if not JSONBIN_KEY or not JSONBIN_ID:
    raise RuntimeError("❌ JSONBIN_KEY / JSONBIN_ID missing in environment")

BASE_URL = f"https://api.jsonbin.io/v3/b/{JSONBIN_ID}"

CAPACITY = 3   # ✅ تعداد ظرفیت هر روز


def today_str():
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
    if data is None:
        data = get_data()

    last_reset = data.get("last_reset", "")
    now = datetime.now(ZoneInfo("Asia/Tehran"))

    # جمعه
    if now.weekday() != 4:
        return False

    return last_reset != today_str()


def reset_reservations():
    """Reset all days"""
    data = {
        "last_reset": today_str(),
    }

    days = ["شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه"]

    for d in days:
        data[d] = [False] * CAPACITY

    save_data(data)
    return True


# ------------------------------------------------
# RESERVE
# ------------------------------------------------
def reserve(day, slot, full_name, telegram_id):
    """slot ∈ [0,1,2]"""
    data = get_data()

    # اگر جمعه 00:00 شد reset کن
    if need_reset(data):
        reset_reservations()
        data = get_data()

    if day not in data:
        return False, "❌ روز نامعتبر"

    day_list = data[day]

    if not isinstance(day_list, list):
        # اگر ساختار قبلی بود → هیلش کن
        day_list = [False] * CAPACITY
        data[day] = day_list

    if slot < 0 or slot >= CAPACITY:
        return False, "❌ بازه نامعتبر"

    # اگر این سلول خالی نیست
    if day_list[slot] not in (False, None):
        return False, "❌ این بازه رزرو شده است."

    day_list[slot] = {
        "name": full_name,
        "id": telegram_id
    }

    save_data(data)
    return True, "✅ رزرو با موفقیت انجام شد."


# ------------------------------------------------
# CANCEL
# ------------------------------------------------
def cancel_reservation(telegram_id):
    data = get_data()

    days = ["شنبه", "یکشنبه", "دوشنبه", "چهارشنبه", "سه‌شنبه", "پنجشنبه", "جمعه"]

    removed = False

    for d in days:
        if isinstance(data.get(d), list):
            for i in range(CAPACITY):
                cell = data[d][i]
                if isinstance(cell, dict) and cell.get("id") == telegram_id:
                    data[d][i] = False
                    removed = True

    if removed:
        save_data(data)
        return True, "✅ رزرو شما لغو شد."
    else:
        return False, "❌ رزروی برای شما یافت نشد."
