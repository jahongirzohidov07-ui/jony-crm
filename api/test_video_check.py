# -*- coding: utf-8 -*-
"""Video tekshiruvi (2026-09-26).

Jahongir: "videoni yuklaganda tahlil qiladigan funksiya ... oxiridaggi
tel raqam qoyilmagan, oxirida logo animation qoshilmagan".

AI tarmoqqa chiqmaydi: video_check.AI["call"] soxta javob bilan.
"""
import os
import sys
import json

os.environ["DATABASE_URL"] = "sqlite:////tmp/verify_vc/db.sqlite"
os.makedirs("/tmp/verify_vc", exist_ok=True)
if os.path.exists("/tmp/verify_vc/db.sqlite"):
    os.remove("/tmp/verify_vc/db.sqlite")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import date                            # noqa: E402
from fastapi.testclient import TestClient           # noqa: E402
import main, models, roles                          # noqa: E402
import entry                                        # noqa: F401,E402
import video_check as vc                            # noqa: E402
from database import SessionLocal                   # noqa: E402
from auth import hash_password                      # noqa: E402

c = TestClient(main.app)
db = SessionLocal()
fails = []


def ck(n, got, want):
    ok = got == want
    print(("OK   " if ok else "XATO ") + f"{n}: {got}"
          + ("" if ok else f"   (kutilgan {want})"))
    if not ok:
        fails.append(n)


br = models.Branch(name="Maktab")
db.add(br)
db.commit()
for un, role in (("marhabo", roles.SMM_MANAGER), ("ustoz", roles.TEACHER)):
    db.add(models.User(username=un, password_hash=hash_password("jonyjony"),
                       role=role, full_name=un.title(), branch_id=br.id,
                       is_active=1))
db.commit()


def tok(un):
    return {"Authorization": "Bearer " + c.post(
        "/api/auth/login", json={"username": un, "password": "jonyjony"}
    ).json()["access_token"]}


HS, HT = tok("marhabo"), tok("ustoz")
ct = models.Content(title="Olimpiada reels", platform="instagram",
                    planned_date=date.today(), status="editing",
                    branch_id=br.id)
db.add(ct)
db.commit()
FR = [{"t": 0.5, "end": False, "data": "data:image/jpeg;base64,AAAA"},
      {"t": 28.0, "end": True, "data": "data:image/jpeg;base64,BBBB"},
      {"t": 29.5, "end": True, "data": "data:image/jpeg;base64,CCCC"}]
SEEN = {}

def ai_bad(frames, meta):
    SEEN["n"] = len(frames)
    return {"phone_at_end": False, "phone_text": "", "logo_at_end": True,
            "logo_animated": False, "subtitles": True,
            "hook_text_start": True, "notes_uz": "Oxirida raqam yo'q"}

def ai_good(frames, meta):
    return {"phone_at_end": True, "phone_text": "+998 90 123 45 67",
            "logo_at_end": True, "logo_animated": True, "subtitles": True,
            "hook_text_start": True, "notes_uz": ""}

def ai_down(frames, meta):
    raise RuntimeError("no-key")


def chk(res, key):
    return next((x for x in res["checks"] if x["key"] == key), {})


print("=== 1. MUAMMOLI VIDEO: raqam yo'q, logo qimirlamaydi, gorizontal ===")
vc.AI["call"] = ai_bad
r = c.post(f"/api/content/{ct.id}/video-check", headers=HS, json={
    "file_name": "reel.mp4", "duration": 30, "width": 1920, "height": 1080,
    "frames": FR})
j = r.json()
ck("javob 200", r.status_code, 200)
ck("AI'ga 3 kadr ketdi", SEEN.get("n"), 3)
ck("umumiy: tuzatish kerak", j["ok"], False)
ck("9:16 emas deb topdi", chk(j, "ratio").get("ok"), False)
ck("oxirida raqam yo'q deb topdi", chk(j, "phone_at_end").get("ok"), False)
ck("  izohi aniq", "telefon raqam" in chk(j, "phone_at_end").get("note", ""),
   True)
ck("logo bor", chk(j, "logo_at_end").get("ok"), True)
ck("logo animatsiyasi yo'q deb topdi", chk(j, "logo_animated").get("ok"),
   False)
ck("xulosada tuzatishlar sanalgan",
   "Oxirida telefon raqam" in j["summary"] and "Logo animatsiyasi"
   in j["summary"], True)

print("\n=== 2. TO'G'RI VIDEO ===")
vc.AI["call"] = ai_good
j = c.post(f"/api/content/{ct.id}/video-check", headers=HS, json={
    "file_name": "reel2.mp4", "duration": 32, "width": 1080, "height": 1920,
    "frames": FR}).json()
ck("hammasi joyida", (j["ok"], j["summary"]), (True, "Hammasi joyida"))
ck("topilgan raqam ko'rsatiladi", j["phone_text"], "+998 90 123 45 67")

print("\n=== 3. AI ISHLAMASA — QOIDA TEKSHIRUVI BARIBIR ===")
vc.AI["call"] = ai_down
j = c.post(f"/api/content/{ct.id}/video-check", headers=HS, json={
    "duration": 120, "width": 1080, "height": 1920, "frames": FR}).json()
ck("uzunlik xatosi topildi", chk(j, "duration").get("ok"), False)
ck("AI bandlari 'tekshirilmadi' (None)", chk(j, "phone_at_end").get("ok"),
   None)
ck("  sababi yozilgan", chk(j, "phone_at_end").get("note"),
   "AI kaliti sozlanmagan")

print("\n=== 4. TARIX VA HUQUQ ===")
rows = c.get(f"/api/content/{ct.id}/video-checks", headers=HS).json()["rows"]
ck("3 ta tekshiruv saqlandi, yangisi tepada",
   [x["ok"] for x in rows], [False, True, False])
ck("video fayl saqlanmaydi (faqat natija)",
   "data" in json.dumps(rows) and "BBBB" in json.dumps(rows), False)
ck("ustoz tekshira olmaydi",
   c.post(f"/api/content/{ct.id}/video-check", headers=HT,
          json={"frames": FR}).status_code, 403)
ck("juda katta kadr rad etiladi",
   c.post(f"/api/content/{ct.id}/video-check", headers=HS,
          json={"frames": [{"t": 1, "data": "x" * 700_000}]}).status_code,
   400)

print("\n" + ("HAMMASI OK" if not fails
              else f"{len(fails)} ta XATO: {fails}"))
sys.exit(1 if fails else 0)
