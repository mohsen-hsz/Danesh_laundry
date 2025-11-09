import os

TOKEN = os.getenv("TOKEN")
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL", "").rstrip("/")
PORT = int(os.getenv("PORT", "10000"))

# اگر ذخیره سازی می‌خوای:
JSONBIN_ID = os.getenv("JSONBIN_ID")
JSONBIN_KEY = os.getenv("JSONBIN_KEY")

if not TOKEN:
    raise RuntimeError("ENV TOKEN is missing")
if not RENDER_EXTERNAL_URL:
    raise RuntimeError("ENV RENDER_EXTERNAL_URL is missing (e.g. https://your-service.onrender.com)")
