"""Cloudflare R2 (S3-mos) uchun imzolangan havolalar (2026-09-27).

Dars rejalari mediasi (rasm, audio) Vercel funksiyasi ichida turganda
bundle 225 MB chegarasiga yetib qolgan edi. Media R2 da yopiq bucket'da
saqlanadi; server ruxsatni tekshirib, qisqa muddatli imzolangan havola
beradi. boto3 ataylab ishlatilmaydi — u bundle'ga ~80 MB qo'shardi;
AWS SigV4 imzosi standart kutubxona bilan hisoblanadi.

Muhit o'zgaruvchilari: R2_ACCOUNT_ID, R2_ACCESS_KEY_ID,
R2_SECRET_ACCESS_KEY, R2_BUCKET. Birortasi bo'lmasa enabled() False —
chaqiruvchi mahalliy fayllarga qaytadi.
"""
import hashlib
import hmac
import os
from datetime import datetime, timezone
from urllib.parse import quote

_KEYS = ("R2_ACCOUNT_ID", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY", "R2_BUCKET")


def enabled() -> bool:
    return all(os.environ.get(k) for k in _KEYS)


def _hmac(key: bytes, msg: str) -> bytes:
    return hmac.new(key, msg.encode(), hashlib.sha256).digest()


def presign(method: str, key: str, expires: int = 7200, now: datetime = None) -> str:
    """S3 SigV4 query-imzoli havola. Vaqt soat boshiga yaxlitlanadi:
    bir soat ichida bir fayl uchun havola bir xil bo'ladi va brauzer
    keshidan foydalanadi; 2 soatlik muddat esa kamida 1 soat qoldiradi."""
    acct, ak = os.environ["R2_ACCOUNT_ID"], os.environ["R2_ACCESS_KEY_ID"]
    sk, bucket = os.environ["R2_SECRET_ACCESS_KEY"], os.environ["R2_BUCKET"]
    host = f"{acct}.r2.cloudflarestorage.com"
    t = (now or datetime.now(timezone.utc)).replace(minute=0, second=0, microsecond=0)
    amz_date, day = t.strftime("%Y%m%dT%H%M%SZ"), t.strftime("%Y%m%d")
    scope = f"{day}/auto/s3/aws4_request"
    uri = "/" + quote(bucket, safe="") + "/" + quote(key, safe="/-_.~")
    q = {
        "X-Amz-Algorithm": "AWS4-HMAC-SHA256",
        "X-Amz-Credential": f"{ak}/{scope}",
        "X-Amz-Date": amz_date,
        "X-Amz-Expires": str(expires),
        "X-Amz-SignedHeaders": "host",
    }
    qs = "&".join(f"{quote(k, safe='-_.~')}={quote(v, safe='-_.~')}" for k, v in sorted(q.items()))
    creq = "\n".join([method, uri, qs, f"host:{host}", "", "host", "UNSIGNED-PAYLOAD"])
    sts = "\n".join(["AWS4-HMAC-SHA256", amz_date, scope, hashlib.sha256(creq.encode()).hexdigest()])
    k = _hmac(_hmac(_hmac(_hmac(("AWS4" + sk).encode(), day), "auto"), "s3"), "aws4_request")
    sig = hmac.new(k, sts.encode(), hashlib.sha256).hexdigest()
    return f"https://{host}{uri}?{qs}&X-Amz-Signature={sig}"
