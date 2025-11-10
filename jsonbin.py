import os
import requests
from datetime import datetime, timedelta

JSONBIN_ID = os.getenv("JSONBIN_ID")
JSONBIN_KEY = os.getenv("JSONBIN_KEY")

BASE_URL = f"https://api.jsonbin.io/v3/b/{JSONBIN_ID}"

HEADERS = {
    "Content-Type": "application/json",
    "X-Master-Key": JSONBIN_KEY
}


# ✅ محاسبه شنبه هفته فعلی
def get_current_week_start():
    today = datetime.now()
    weekday = today.weekday()    # دوشنبه=0 ... یکشنبه=6
    delta = (weekday - 5) % 7    # شنبه = index=5
    saturday = today - timedelta(days=delta)
    return saturday.strftime("%Y-%m-%d")


# ✅ دریافت دیتا + ریست هفتگی
def load_data():
    r = requests.get(BASE_URL, headers=HEADERS)
    if r.status_code != 200:
        raise Exception("❌ JSONBin load error")

    data = r.json()["record"]
    current_week_start = get_current_week_start()

    if data.get("week_start") != current_week_start:
        data = {
            "week_start": current_week_start,
            "reservations": []
        }
        save_data(data)

    return data


# ✅ ذخیره
def save_data(data):
    r = requests.put(BASE_URL, headers=HEADERS, json=data)
    return r.status_code in (200, 201)


# ✅ تبدیل نام روز → تاریخ
def weekday_to_date(weekday_name):
    mapping = {
        "شنبه": 0,
        "یکشنبه": 1,
        "دوشنبه": 2,
        "سه‌شنبه": 3,
        "چهارشنبه": 4,
        "پنجشنبه": 5,
        "جمعه": 6,
    }

    if weekday_name not in mapping:
        return None

    data = load_data()
    week_start = datetime.strptime(data["week_start"], "%Y-%m-%d")
    return (week_start + timedelta(days=mapping[weekday_name])).strftime("%Y-%m-%d")


# ✅ رزرو
def reserve(day_name, slot, full_name, telegram_id):
    data = load_data()

    date = weekday_to_date(day_name)
    if not date:
        return False, "❌ روز نامعتبر است."

    # جلوگیری از رزرو تکراری
    for r in data["reservations"]:
        if r["date"] == date and r["slot"] == slot:
            return False, "❌ این بازه زمانی قبلاً رزرو شده است."

    data["reservations"].append({
        "date": date,
        "day": day_name,
        "slot": slot,
        "full_name": full_name,
        "telegram_id": telegram_id
    })

    save_data(data)
    return True, "✅ رزرو با موفقیت انجام شد."


# ✅ لغو رزرو کاربر
def cancel_reservation(telegram_id):
    data = load_data()
    res = data.get("reservations", [])

    new_res = [r for r in res if r["telegram_id"] != telegram_id]

    if len(new_res) == len(res):
        return False, "❌ شما رزروی ندارید."

    data["reservations"] = new_res
    save_data(data)

    return True, "✅ رزرو شما لغو شد."
