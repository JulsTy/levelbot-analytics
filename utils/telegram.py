# utils/telegram.py — safe version

import requests
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

def send_message(text):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return  # Not configured — do not send

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    try:
        response = requests.post(url, data=payload, timeout=5)
        if response.status_code != 200:
            print(f"❗Telegram error: {response.status_code} {response.text}")
    except Exception as e:
        print(f"❗️Telegram exception: {e}")

