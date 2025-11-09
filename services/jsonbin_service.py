import os
import httpx

JSONBIN_ID = os.getenv("JSONBIN_ID")
JSONBIN_KEY = os.getenv("JSONBIN_KEY")

BASE_URL = f"https://api.jsonbin.io/v3/b/{JSONBIN_ID}"

headers = {
    "X-Master-Key": JSONBIN_KEY,
    "Content-Type": "application/json"
}


async def get_days():
    async with httpx.AsyncClient() as client:
        res = await client.get(BASE_URL, headers=headers)
        data = res.json()
        return data["record"]


async def update_days(new_data: dict):
    async with httpx.AsyncClient() as client:
        res = await client.put(BASE_URL, headers=headers, json=new_data)
        return res.json()
