"""WEB PUSH (2026-10-03): imtihon ochilganda/boshlanganda o'quvchining
telefoniga bildirishnoma.

Tekshiriladi:
  1. Obuna: o'quvchi o'z qurilmasini yozadi; noto'g'ri obuna 400.
  2. Shifrlash RFC 8291 bo'yicha — brauzer tomoni (qabul qiluvchi kalit
     bilan) ochib, aynan yuborilgan xabarni o'qiydi.
  3. VAPID imzo — public kalit bilan tekshiriladi, aud = push servis.
  4. Examiner link ochsa va Start bossa — guruh o'quvchisiga xabar
     (havola ilovadagi imtihonga); boshqa guruhga yo'q.
  5. Push servis 410 desa — eskirgan obuna o'chadi.
"""
import base64
import json
import os
import sys
import tempfile
from datetime import timedelta

_DB = os.path.join(tempfile.gettempdir(), "push_test.db")
os.environ["DATABASE_URL"] = "sqlite:///" + _DB.replace("\\", "/")
if os.path.exists(_DB):
    os.remove(_DB)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient          # noqa: E402
import main, models, roles                          # noqa: E402
import entry  # noqa: F401,E402
import exam_online                                  # noqa: E402
import push                                         # noqa: E402
import common                                       # noqa: E402
from database import SessionLocal                   # noqa: E402
from auth import hash_password                      # noqa: E402
from cryptography.hazmat.primitives import hashes, serialization  # noqa: E402
from cryptography.hazmat.primitives.asymmetric import ec  # noqa: E402
from cryptography.hazmat.primitives.asymmetric.utils import encode_dss_signature  # noqa: E402
from cryptography.hazmat.primitives.ciphers.aead import AESGCM  # noqa: E402
from cryptography.hazmat.primitives.kdf.hkdf import HKDF  # noqa: E402

common._ensure_month_charges = lambda db, **kw: None
c = TestClient(main.app)
fails = []


def ck(name, got, want):
    ok = got == want
    print(("OK  " if ok else "XATO ") + name + f": {got}"
          + ("" if ok else f"   (kutilgan {want})"))
    if not ok:
        fails.append(name)


def b64u(b):
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


def unb64u(s):
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


# --- Brauzer tomoni (qabul qiluvchi) ---
ua_priv = ec.generate_private_key(ec.SECP256R1())
ua_pub = ua_priv.public_key().public_bytes(
    serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)
auth = os.urandom(16)


def decrypt(body: bytes) -> bytes:
    salt, rs, idlen = body[:16], body[16:20], body[20]
    as_pub = body[21:21 + idlen]
    ct = body[21 + idlen:]
    shared = ua_priv.exchange(ec.ECDH(), ec.EllipticCurvePublicKey
                              .from_encoded_point(ec.SECP256R1(), as_pub))
    ikm = HKDF(algorithm=hashes.SHA256(), length=32, salt=auth,
               info=b"WebPush: info\x00" + ua_pub + as_pub).derive(shared)
    cek = HKDF(algorithm=hashes.SHA256(), length=16, salt=salt,
               info=b"Content-Encoding: aes128gcm\x00").derive(ikm)
    nonce = HKDF(algorithm=hashes.SHA256(), length=12, salt=salt,
                 info=b"Content-Encoding: nonce\x00").derive(ikm)
    pt = AESGCM(cek).decrypt(nonce, ct, None)
    assert pt.endswith(b"\x02")
    return pt[:-1]


SENT = []
STATUS = {"code": 201}


class _R:
    def __init__(self, code):
        self.status_code = code


def fake_post(url, content=None, timeout=None, headers=None):
    SENT.append({"url": url, "body": content, "headers": headers})
    return _R(STATUS["code"])


push.httpx.post = fake_post

TODAY = roles.local_today()
db = SessionLocal()
exam_online.seed_templates(db)
b = models.Branch(name="Zafar"); db.add(b); db.commit()
for un, role in [("asos", "founder"), ("exam", "examiner")]:
    db.add(models.User(username=un, password_hash=hash_password("x"),
                       full_name=un.title(), role=role, branch_id=b.id))
t = models.Teacher(full_name="Ustoz", branch_id=b.id); db.add(t); db.commit()
gA = models.Group(name="Apex", branch_id=b.id, teacher_id=t.id,
                  subject="english", level="step1")
gB = models.Group(name="Beta", branch_id=b.id, teacher_id=t.id,
                  subject="english", level="step1")
db.add_all([gA, gB]); db.commit()
GA = gA.id


def mk(name, gid, phone):
    u = models.User(username=phone, password_hash=hash_password("jonyjony"),
                    full_name=name, role=roles.STUDENT, branch_id=b.id,
                    is_active=1)
    db.add(u); db.commit()
    s = models.Student(full_name=name, branch_id=b.id, group_id=gid,
                       status="active", phone=phone, user_id=u.id,
                       enrolled_date=TODAY - timedelta(days=60))
    db.add(s); db.commit()


mk("Ali", gA.id, "998900000001")
mk("Vali", gB.id, "998900000002")
db.close()


def tok(u, p):
    return {"Authorization": "Bearer " + c.post("/api/auth/login", json={
        "username": u, "password": p}).json()["access_token"]}


HA, HV = tok("998900000001", "jonyjony"), tok("998900000002", "jonyjony")
H, HE = tok("asos", "x"), tok("exam", "x")

print("=== 1. Obuna ===")
key = c.get("/api/push/key", headers=HA).json()["key"]
ck("VAPID kalit (65 bayt)", len(unb64u(key)), 65)
ck("kalit o'zgarmaydi", c.get("/api/push/key", headers=HV).json()["key"], key)
ck("noto'g'ri obuna 400", c.post("/api/push/subscribe", headers=HA, json={
    "endpoint": "http://x", "keys": {}}).status_code, 400)
EP = "https://fcm.googleapis.com/fcm/send/abc123"
r = c.post("/api/push/subscribe", headers=HA, json={
    "endpoint": EP, "keys": {"p256dh": b64u(ua_pub), "auth": b64u(auth)}})
ck("obuna yozildi", r.status_code, 200)
c.post("/api/push/subscribe", headers=HV, json={
    "endpoint": "https://fcm.googleapis.com/fcm/send/vali",
    "keys": {"p256dh": b64u(ua_pub), "auth": b64u(auth)}})

print("\n=== 4. Imtihon ochildi / boshlandi ===")
EID = c.post(f"/api/groups/{GA}/exams", headers=H, json={
    "kind": "unit", "unit_no": 1, "date": TODAY.isoformat(),
    "max_score": 30}).json()["id"]
tpl = [x for x in c.get("/api/exam-templates", headers=HE).json()
       if x["level"] == "step1" and x["unit_no"] == 1][0]["id"]
r = c.post(f"/api/exams/{EID}/online", headers=HE, json={"template_id": tpl})
TOKEN = r.json()["online"]["token"]
ck("link ochilganda 1 ta xabar (faqat Apex)", [s["url"] for s in SENT], [EP])

print("\n=== 2-3. Shifr va imzo ===")
msg = json.loads(decrypt(SENT[0]["body"]))
ck("xabar ochildi", (msg["title"], msg["url"]),
   ("Imtihon", f"/student/exam/{TOKEN}?pwa=1"))
h = SENT[0]["headers"]
ck("sarlavhalar", (h["Content-Encoding"], h["TTL"]), ("aes128gcm", "3600"))
auth_h = h["Authorization"]
jwt = auth_h.split("t=")[1].split(",")[0]
k = auth_h.split("k=")[1]
hd, bd, sg = jwt.split(".")
pub = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), unb64u(k))
raw = unb64u(sg)
pub.verify(encode_dss_signature(int.from_bytes(raw[:32], "big"),
                                int.from_bytes(raw[32:], "big")),
           f"{hd}.{bd}".encode(), ec.ECDSA(hashes.SHA256()))
ck("imzo to'g'ri, aud = push servis",
   json.loads(unb64u(bd))["aud"], "https://fcm.googleapis.com")

SENT.clear()
c.post(f"/api/exams/{EID}/online/start", headers=HE,
       json={"minutes": 30, "countdown": 0})
ck("Start bosilganda xabar", json.loads(decrypt(SENT[0]["body"]))["title"],
   "Imtihon boshlandi!")

print("\n=== 5. Eskirgan obuna ===")
STATUS["code"] = 410
d = SessionLocal()
n = push.send_to_users(d, [d.query(models.Student).filter_by(
    full_name="Ali").first().user_id], "x", "y")
ck("410 — yetkazilmadi", n, 0)
ck("obuna o'chdi", d.query(push._PS).filter_by(endpoint=EP).count(), 0)
d.close()

print()
if fails:
    print(f"{len(fails)} ta XATO: {fails}")
    sys.exit(1)
print("HAMMASI OK")
