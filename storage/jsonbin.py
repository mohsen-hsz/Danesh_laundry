import httpx
import os

JSONBIN_ID = os.getenv("JSONBIN_ID")
JSONBIN_KEY = os.getenv("JSONBIN_KEY")
BASE = "https://api.jsonbin.io/v3/b"

HEADERS = {"X-Master-Key": JSONBIN_KEY} if JSONBIN_KEY else {}

async def get_data():
    if not (JSONBIN_ID and JSONBIN_KEY):
        return None
    url = f"{BASE}/{JSONBIN_ID}"
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(url, headers=HEADERS)
        r.raise_for_status()
        return r.json().get("record")

async def put_data(payload: dict):
    if not (JSONBIN_ID and JSONBIN_KEY):
        return None
    url = f"{BASE}/{JSONBIN_ID}"
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.put(url, headers=HEADERS, json=payload)
        r.raise_for_status()
        return r.json()
