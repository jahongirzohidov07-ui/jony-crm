"""Telegram xabarnomalar.

TELEGRAM_BOT_TOKEN muhit o'zgaruvchisi o'rnatilgan bo'lsa ishlaydi;
o'rnatilmagan bo'lsa hamma funksiya jimgina False qaytaradi — platforma
botsiz ham to'liq ishlayveradi.

Ota-ona botga /start KOD yozadi (kod o'quvchi kartasida turadi), shu
bilan chat o'quvchiga bog'lanadi. Keyin unga boradi:
  - farzandi darsga kelmagani;
  - to'lov qabul qilingani (chek);
  - qarzdorlik eslatmasi (admin tugma bosganda).
"""
import json
import os
import urllib.request

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()


def enabled() -> bool:
    return bool(TOKEN)


def _call(method: str, payload: dict, timeout: int = 6):
    """Telegram API chaqiruvi. Xato bo'lsa None — hech qachon raise
    qilmaydi, chunki xabarnoma asosiy amalni to'xtatmasligi kerak."""
    if not TOKEN:
        return None
    try:
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{TOKEN}/{method}",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except Exception:
        return None


def send(chat_id, text: str) -> bool:
    if not chat_id:
        return False
    r = _call("sendMessage", {"chat_id": str(chat_id), "text": text})
    return bool(r and r.get("ok"))


def bot_info():
    """Bot @username — sozlanganini ko'rsatish uchun."""
    r = _call("getMe", {})
    if r and r.get("ok"):
        return r["result"].get("username")
    return None


def set_webhook(url: str) -> bool:
    r = _call("setWebhook", {"url": url})
    return bool(r and r.get("ok"))


def webhook_secret() -> str:
    """Webhook manzilini taxmin qilib bo'lmasligi uchun token'dan
    chiqarilgan qisqa imzo."""
    import hashlib
    return hashlib.sha256(("jony:" + TOKEN).encode()).hexdigest()[:24]
