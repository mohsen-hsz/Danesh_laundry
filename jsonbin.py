import os
import requests
from datetime import datetime, timedelta

JSONBIN_ID = os.getenv("JSONBIN_ID")
JSONBIN_KEY = os.getenv("JSONBIN_KEY")

BASE_URL = f"https://api.jsonbin.io/v3/b/{JSONBIN_ID}"

HEADERS = {
    "Content-Type": "application/json",
    "X-Master-Key": JSONBIN_KEY   # اگر زمانی نیاز شد میشه X-Access-Key
}


# ✅ پیدا کردن شنبه هفته فعلی
def get_current_week_start():
    today = datetime.now()
    weekday = today.weekday()

    # شنبه = weekday → 5
    delta = (weekday - 5) % 7
    saturday = today - timedelta(days=delta)

    return saturday.strftime("%Y-%m-%d")


# ✅ خواندن دیتا از JSONBin + ریست هفتگی
def load_data():
    r = requests.get(BASE_URL, headers=HEADERS)

    if r.status_code != 200:
        raise Exception("❌ JSONBin load error")

    data = r.json()["record"]

    current_sat = get_current_week_start()

    if data.get("week_start") != current_sat:
        # ریست هفتگی
        data = {
            "week_start": current_sat,
            "reservations": []
        }
        save_data(data)

    return data


# ✅ ذخیره در JSONBin
def save_data(data):
    r = requests.put(BASE_URL, headers=HEADERS, json=data)

    if r.status_code not in (200, 201):
        print("❌ Save error:", r.text)
        return False

    return True


# ✅ رزرو جدید
def reserve(date, slot, full_name, telegram_id):
    data = load_data()

    # جلوگیری از رزرو گذشته
    today = datetime.now().strftime("%Y-%m-%d")
    if date < today:
        return False, "❌ امکان رزرو تاریخ گذشته وجود ندارد"

    # چک اینکه اسلات قبلاً رزرو شده یا نه
    for r in data["reservations"]:
        if r["date"] == date and r["slot"] == slot:
            return False, "❌ این بازه زمانی قبلاً رزرو شده"

    # اضافه کردن رزرو
    data["reservations"].append({
        "date": date,
        "slot": slot,
        "full_name": full_name,
        "telegram_id": telegram_id
    })

    save_data(data)
    return True, "✅ رزرو با موفقیت ثبت شد"


# ✅ لغو رزرو
def cancel_reservation(date, slot, telegram_id):
    data = load_data()

    before = len(data["reservations"])

    data["reservations"] = [
        r for r in data["reservations"]
        if not (r["date"] == date and r["slot"] == slot and r["telegram_id"] == telegram_id)
    ]

    if len(data["reservations"]) == before:
        return False, "❌ رزروی مطابق اطلاعات وارد شده یافت نشد"

    save_data(data)
    return True, "✅ رزرو لغو شد"


# ✅ وضعیت اسلات‌های یک روز
def get_day_slots(date):
    data = load_data()

    taken = {r["slot"] for r in data["reservations"] if r["date"] == date}

    result = []

    for slot in [1, 2, 3]:
        if slot in taken:
            result.append({"slot": slot, "status": "taken"})
        else:
            result.append({"slot": slot, "status": "free"})

    return result
