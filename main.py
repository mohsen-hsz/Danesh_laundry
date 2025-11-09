import os
import requests
from flask import Flask

app = Flask(__name__)

JSONBIN_ID = os.getenv("JSONBIN_ID")
JSONBIN_KEY = os.getenv("JSONBIN_KEY")

@app.route("/")
def index():
    return "✅ Test JSONBin by /testdb"

@app.route("/testdb")
def testdb():
    if not JSONBIN_ID or not JSONBIN_KEY:
        return "❌ JSONBIN_ID or JSONBIN_KEY not found in env"

    url = f"https://api.jsonbin.io/v3/b/{JSONBIN_ID}"

    headers = {
        "X-Master-Key": JSONBIN_KEY
    }

    try:
        r = requests.get(url, headers=headers)
        return f"STATUS: {r.status_code}\n\nRESPONSE:\n{r.text}"
    except Exception as e:
        return f"❌ ERROR: {e}"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 Test server running on {port}")
    app.run(host="0.0.0.0", port=port)
