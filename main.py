import logging
import asyncio
from telegram.ext import Application
from aiohttp import web

from config import TOKEN, RENDER_EXTERNAL_URL, PORT
from bot.handlers import register_handlers

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s — %(name)s — %(levelname)s — %(message)s"
)
log = logging.getLogger("main")

WEBHOOK_PATH = f"/{TOKEN}"
WEBHOOK_URL = f"{RENDER_EXTERNAL_URL}{WEBHOOK_PATH}"

async def on_startup(app: Application):
    # مسیر Health برای Render
    async def health(_):
        return web.Response(text="OK ✅")
    app.web_app.router.add_get("/", health)

    # حذف وب‌هوک قبلی و ست کردن جدید
    info = await app.bot.get_me()
    log.info("Bot: @%s", info.username)
    await app.bot.delete_webhook(drop_pending_updates=True)
    await app.bot.set_webhook(url=WEBHOOK_URL)
    log.info("✅ Webhook set: %s", WEBHOOK_URL)

def main():
    application = Application.builder().token(TOKEN).build()
    register_handlers(application)

    # اجرای وب‌هوک داخلی PTB (aiohttp)
    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TOKEN,            # مسیر لوکال سرور
        webhook_url=WEBHOOK_URL,   # آدرسی که تلگرام صدا می‌زند
        post_init=on_startup,      # Health + set webhook
        drop_pending_updates=True,
        stop_signals=None          # Render سیگنال خاصی نمی‌فرسته؛ خنثی
    )

if __name__ == "__main__":
    main()
