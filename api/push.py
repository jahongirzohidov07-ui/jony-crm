"""WEB PUSH — TELEFONGA BILDIRISHNOMA (2026-10-03).

Jahongir: "Jony Student app yuklab olganlar uchun agar test bo'lsa
ularga notification bo'lib kelishi kerak, shundan kirishi kerak".

Jony Student — saytning o'zi (TWA / PWA). Web Push orqali ilova yopiq
bo'lsa ham telefonga xabar keladi (Android: Chrome bildirishnomasi
ilova nomi bilan; iPhone: uy ekraniga qo'shilgan PWA, iOS 16.4+).

Standart: RFC 8291 (aes128gcm shifrlash) + RFC 8292 (VAPID). Tashqi
kutubxona yo'q — faqat `cryptography` va `httpx`.

VAPID kalitlar birinchi chaqiruvda yaratiladi va bazada saqlanadi
(push_keys). Kalit o'zgarsa eski obunalar ishlamay qoladi — shuning
uchun u hech qachon qayta yaratilmaydi.
"""
import base64
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from urllib.parse import urlparse

import httpx
from fastapi import Body, Depends, HTTPException
from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.orm import Session

import models
from common import ensure_tables
from database import Base as _Base
from main import app, get_db, get_current_user

VAPID_SUB = "mailto:jahongirzohidov07@gmail.com"


if getattr(models, "PushSubscription", None) is None:
    class PushSubscription(_Base):
        """Bitta qurilmaning obunasi (bir odamda bir nechta bo'lishi
        mumkin: telefon + planshet)."""
        __tablename__ = "push_subscriptions"
        __table_args__ = {"extend_existing": True}

        id = Column(Integer, primary_key=True, index=True)
        user_id = Column(Integer, index=True, nullable=False)
        endpoint = Column(Text, nullable=False, unique=True)
        p256dh = Column(String, nullable=False)
        auth = Column(String, nullable=False)
        created_at = Column(DateTime, default=datetime.utcnow)
        last_ok_at = Column(DateTime, nullable=True)

    class PushKey(_Base):
        """VAPID kalit juftligi — bitta qator."""
        __tablename__ = "push_keys"
        __table_args__ = {"extend_existing": True}

        id = Column(Integer, primary_key=True)
        private_pem = Column(Text, nullable=False)
        public_b64 = Column(String, nullable=False)

    models.PushSubscription = PushSubscription
    models.PushKey = PushKey
    ensure_tables([PushSubscription.__table__, PushKey.__table__])

_PS = models.PushSubscription
_PK = models.PushKey


def _b64u(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


def _unb64u(s: str) -> bytes:
    s = s.strip()
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def vapid_keys(db: Session):
    """(private_key obyekti, public kalit base64url)."""
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import ec
    row = db.query(_PK).first()
    if row is None:
        key = ec.generate_private_key(ec.SECP256R1())
        pem = key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption()).decode()
        pub = key.public_key().public_bytes(
            serialization.Encoding.X962,
            serialization.PublicFormat.UncompressedPoint)
        row = _PK(id=1, private_pem=pem, public_b64=_b64u(pub))
        db.add(row)
        try:
            db.commit()
        except Exception:
            # Ikki so'rov bir vaqtda yaratgan bo'lsa — birinchisi qoladi
            db.rollback()
            row = db.query(_PK).first()
    key = serialization.load_pem_private_key(row.private_pem.encode(),
                                             password=None)
    return key, row.public_b64


def _vapid_header(key, pub_b64: str, endpoint: str) -> str:
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.hazmat.primitives.asymmetric.utils import (
        decode_dss_signature)
    u = urlparse(endpoint)
    head = _b64u(json.dumps({"typ": "JWT", "alg": "ES256"},
                            separators=(",", ":")).encode())
    body = _b64u(json.dumps({"aud": f"{u.scheme}://{u.netloc}",
                             "exp": int(time.time()) + 12 * 3600,
                             "sub": VAPID_SUB},
                            separators=(",", ":")).encode())
    signing = f"{head}.{body}".encode()
    der = key.sign(signing, ec.ECDSA(hashes.SHA256()))
    r, s = decode_dss_signature(der)
    sig = r.to_bytes(32, "big") + s.to_bytes(32, "big")
    return f"vapid t={head}.{body}.{_b64u(sig)}, k={pub_b64}"


def encrypt(payload: bytes, p256dh: str, auth: str) -> bytes:
    """RFC 8291 — aes128gcm kontent kodlash."""
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.kdf.hkdf import HKDF

    ua_pub = _unb64u(p256dh)
    auth_secret = _unb64u(auth)
    ua_key = ec.EllipticCurvePublicKey.from_encoded_point(
        ec.SECP256R1(), ua_pub)
    as_priv = ec.generate_private_key(ec.SECP256R1())
    as_pub = as_priv.public_key().public_bytes(
        serialization.Encoding.X962,
        serialization.PublicFormat.UncompressedPoint)
    shared = as_priv.exchange(ec.ECDH(), ua_key)
    ikm = HKDF(algorithm=hashes.SHA256(), length=32, salt=auth_secret,
               info=b"WebPush: info\x00" + ua_pub + as_pub).derive(shared)
    salt = os.urandom(16)
    cek = HKDF(algorithm=hashes.SHA256(), length=16, salt=salt,
               info=b"Content-Encoding: aes128gcm\x00").derive(ikm)
    nonce = HKDF(algorithm=hashes.SHA256(), length=12, salt=salt,
                 info=b"Content-Encoding: nonce\x00").derive(ikm)
    ct = AESGCM(cek).encrypt(nonce, payload + b"\x02", None)
    header = salt + (4096).to_bytes(4, "big") + bytes([len(as_pub)]) + as_pub
    return header + ct


def _send_one(key, pub_b64, sub_id, endpoint, p256dh, auth, data: bytes):
    """(sub_id, holat): "ok" | "gone" | "err"."""
    try:
        body = encrypt(data, p256dh, auth)
        r = httpx.post(endpoint, content=body, timeout=6.0, headers={
            "Content-Encoding": "aes128gcm",
            "Content-Type": "application/octet-stream",
            "TTL": "3600",
            "Urgency": "high",
            "Authorization": _vapid_header(key, pub_b64, endpoint),
        })
        if r.status_code in (404, 410):
            return sub_id, "gone"
        return sub_id, "ok" if r.status_code < 300 else "err"
    except Exception:
        return sub_id, "err"


def send_to_users(db: Session, user_ids, title: str, body: str,
                  url: str = "/student", tag: str | None = None) -> int:
    """Bu odamlarning barcha qurilmalariga xabar. Nechta qurilmaga
    ketgani qaytadi. Hech qachon xato tashlamaydi — bildirishnoma
    ketmasa ham asosiy amal (imtihon ochish) to'xtamasin."""
    try:
        ids = [int(u) for u in set(user_ids or []) if u]
        if not ids:
            return 0
        subs = db.query(_PS).filter(_PS.user_id.in_(ids)).all()
        if not subs:
            return 0
        key, pub = vapid_keys(db)
        data = json.dumps({"title": title, "body": body, "url": url,
                           "tag": tag}, ensure_ascii=False).encode()
        jobs = [(s.id, s.endpoint, s.p256dh, s.auth) for s in subs]
        with ThreadPoolExecutor(max_workers=8) as ex:
            res = list(ex.map(lambda j: _send_one(key, pub, *j, data), jobs))
        ok = 0
        now = datetime.utcnow()
        for sid, st in res:
            row = db.query(_PS).get(sid)
            if row is None:
                continue
            if st == "gone":
                db.delete(row)
            elif st == "ok":
                row.last_ok_at = now
                ok += 1
        db.commit()
        return ok
    except Exception as e:  # noqa: BLE001
        try:
            db.rollback()
        except Exception:
            pass
        print(f"[push] yuborilmadi: {e}")
        return 0


# ------------------------------------------------------------ route'lar --
@app.get("/api/push/key")
def push_key(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return {"key": vapid_keys(db)[1]}


@app.post("/api/push/subscribe")
def push_subscribe(payload: dict = Body(...), db: Session = Depends(get_db),
                   user=Depends(get_current_user)):
    ep = str(payload.get("endpoint") or "")
    keys = payload.get("keys") or {}
    p256dh, auth = str(keys.get("p256dh") or ""), str(keys.get("auth") or "")
    if not ep.startswith("https://") or not p256dh or not auth:
        raise HTTPException(400, "Obuna noto'g'ri")
    row = db.query(_PS).filter(_PS.endpoint == ep).first()
    if row is None:
        row = _PS(endpoint=ep, user_id=user.id, p256dh=p256dh, auth=auth)
        db.add(row)
    else:
        # Bitta telefonda boshqa o'quvchi kirsa — obuna unga o'tadi
        row.user_id, row.p256dh, row.auth = user.id, p256dh, auth
    db.commit()
    return {"ok": True}


@app.post("/api/push/unsubscribe")
def push_unsubscribe(payload: dict = Body(...), db: Session = Depends(get_db),
                     user=Depends(get_current_user)):
    ep = str(payload.get("endpoint") or "")
    db.query(_PS).filter(_PS.endpoint == ep,
                         _PS.user_id == user.id).delete()
    db.commit()
    return {"ok": True}


def notify_exam(db: Session, exam, online, started: bool) -> int:
    """Guruh o'quvchilariga imtihon xabari (link ochildi / boshlandi)."""
    try:
        import exam_online as EO
        import roles
        studs = EO._roster(db, exam.group_id)
        uids = [s.user_id for s in studs if getattr(s, "user_id", None)]
        title = exam.title or roles.exam_title(exam.kind, exam.unit_no)
        if started:
            t, b = "Imtihon boshlandi!", f"{title} — hoziroq kiring"
        else:
            t, b = "Imtihon", f"{title} ochildi — kirib, boshlanishini kuting"
        return send_to_users(db, uids, t, b,
                             url=f"/student/exam/{online.token}?pwa=1",
                             tag=f"exam-{online.token}")
    except Exception as e:  # noqa: BLE001
        print(f"[push] imtihon xabari: {e}")
        return 0

