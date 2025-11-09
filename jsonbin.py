import requests
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

JSONBIN_URL = "https://api.jsonbin.io/v3/b/.../latest"   # ✅ بن‌هات رو بذار
JSONBIN_WRITE_URL = "https://api.jsonbin.io/v3/b/..."
JSONBIN_KEY = "xxxx"

def fetch_db():
    headers = {"X-Master-Key": JSONBIN_KEY}
    res = requests.get(JSONBIN_URL, headers=headers)
    data = res.json()["record"]

    # ساختار اگر خالی بود
    if "week_start" not in data or "reservations" not in data:
        data = {"week_start":"", "reservations":[]}

    return data


def save_db(data):
    headers = {
        "Content-Type": "application/json",
        "X-Master-Key": JSONBIN_KEY,
    }
    requests.put(JSONBIN_WRITE_URL, headers=headers, json=data)


def get_current_week_start():
    """اولین شنبه همین هفته - بر اساس تهران"""
    now = datetime.now(ZoneInfo("Asia/Tehran"))
    weekday = now.weekday()   # شنبه = 5 ولی چون default Monday=0 → تنظیم لازم داریم
    # برای ایران: شنبه = 6 کاملاً بهتره
    # برای ساده‌سازی: شنبه → weekday=6

    # اگر هفته را از شنبه واقعی بخوایم (Saturday=5)
    # ولی برای ایران تقویم شنبه=6، بنابراین:
    shift = (now.weekday() - 5) % 7
    week_start = (now - timedelta(days=shift)).date()
    return str(week_start)


def reset_if_needed(db):
    """ریست هفتگی وقتی جمعه شب گذشته باشد"""
    now = datetime.now(ZoneInfo("Asia/Tehran")).date()

    if not db["week_start"]:
        db["week_start"] = get_current_week_start()
        db["reservations"] = []
        save_db(db)
        return db

    ws = datetime.fromisoformat(db["week_start"]).date()

    # اگر هفته جدید شروع شده
    if now >= ws + timedelta(days=7):
        db["week_start"] = get_current_week_start()
        db["reservations"] = []
        save_db(db)

    return db


def get_available_days(db):
    """بازگرداندن روزهایی که گذشته نیستند و full نیستند"""

    week_start = datetime.fromisoformat(db["week_start"]).date()
    now = datetime.now(ZoneInfo("Asia/Tehran")).date()

    valid_days = []
    for i in range(7):
        day = week_start + timedelta(days=i)
        if day < now:
            continue   # روز گذشته → حذف کنیم

        if not is_day_full(db, i):
            valid_days.append(i)

    return valid_days


def is_day_full(db, day_index):
    """اگر همه اسلات‌ها پر باشند"""
    slots = get_free_slots(db, day_index)
    return len(slots) == 0


def get_free_slots(db, day_index):
    """اسلات‌های آزاد"""
    all_slots = [
        "09:00 - 11:00",
        "11:00 - 13:00",
        "13:00 - 15:00",
        "15:00 - 17:00",
        "17:00 - 19:00",
        "19:00 - 21:00",
    ]
    taken = [r["slot"] for r in db["reservations"] if r["day"] == day_index]
    return [s for s in all_slots if s not in taken]


def reserve_time(db, name, day_index, slot):
    db["reservations"].append({
        "name": name,
        "day": day_index,
        "slot": slot,
    })
    save_db(db)
