from telegram import KeyboardButton, ReplyKeyboardMarkup

def main_keyboard():
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("🚀 رزرو روز")],
            [KeyboardButton("📅 نمایش روزها")],
        ],
        resize_keyboard=True
    )
