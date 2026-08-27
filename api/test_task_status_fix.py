# -*- coding: utf-8 -*-
"""Vazifa statuslari ishlashi (2026-08-27).

Jahongir: "vazifalar bo'limida jarayondaga o'tkizsa jarayonga
o'tmayabdi vazifa, tekshriildiga otkizsayam o'tmayabdi. qayta
ishlashgayam otmayabdi, faqat bajarildiga ishlayabdi, bekor qilindi
ishladi qolgani ishlamayabdi."

SABAB. _task_status() muddati o'tgan har qanday OCHIQ vazifani
"late" deb qaytarardi va haqiqiy statusni butunlay bosib ketardi:
    Jarayonda     -> ekranda "Kechikdi" -> Jarayonda tabida yo'q
    Tekshiruvda   -> ekranda "Kechikdi" -> Tekshiruvda tabida yo'q
    Qayta ishlash -> ekranda "Kechikdi" -> o'sha tabda yo'q
Bajarildi va Bekor qilindi TASK_CLOSED ichida bo'lgani uchun
bosilmasdi — shuning uchun "faqat o'sha ikkitasi ishlayapti" deb
ko'rinardi. Aslida status BAZAGA yozilgan edi, ekran ko'rsatmasdi.

Test aynan shu holatni tekshiradi: MUDDATI O'TGAN vazifada har bir
status to'g'ri ko'rinishi va o'z tabida topilishi kerak.
"""
import os
import sys

os.environ["DATABASE_URL"] = "sqlite:////tmp/verify_taskst/db.sqlite"
os.makedirs("/tmp/verify_taskst", exist_ok=True)
if os.path.exists("/tmp/verify_taskst/db.sqlite"):
    os.remove("/tmp/verify_taskst/db.sqlite")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import date, timedelta                # noqa: E402
from fastapi.testclient import TestClient           # noqa: E402
import main, models, roles                          # noqa: E402
import entry                                        # noqa: F401,E402
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


b = models.Branch(name="Zafar")
db.add(b)
db.commit()
u = models.User(username="rahbar", password_hash=hash_password("jonyjony"),
                role=roles.FOUNDER, full_name="Jahongir", is_active=1)
db.add(u)
db.commit()
H = {"Authorization": "Bearer " + c.post(
    "/api/auth/login",
    json={"username": "rahbar", "password": "jonyjony"}
).json()["access_token"]}

# MUDDATI O'TGAN vazifa — xato aynan shunda chiqardi
kecha = (date.today() - timedelta(days=10)).isoformat()
r = c.post("/api/tasks", headers=H, json={
    "title": "Yangi xodim: surat va video",
    "assignee_id": u.id, "deadline": kecha,
    "branch_id": b.id, "priority": "normal"})
ck("vazifa yaratildi", r.status_code, 200)
tid = r.json()["id"]

print("\n=== HAR BIR STATUS ISHLAYDIMI ===")
for key, label in (("in_progress", "Jarayonda"),
                   ("review", "Tekshiruvda"),
                   ("rework", "Qayta ishlashga"),
                   ("new", "Yangi")):
    rr = c.put(f"/api/tasks/{tid}", headers=H, json={"status": key}).json()
    ck(f"{label}: status saqlandi", rr["status"], key)
    ck(f"{label}: yorliq to'g'ri", rr["status_label"], label)
    ck(f"{label}: kechikish belgisi ham bor", rr["overdue"], True)
    lst = c.get(f"/api/tasks?status_filter={key}", headers=H).json()
    ck(f"{label}: o'z tabida ko'rinadi",
       [x["id"] for x in lst["rows"]], [tid])
    ck(f"{label}: Kechikdi tabida ham bor",
       tid in [x["id"] for x in
               c.get("/api/tasks?status_filter=late", headers=H)
               .json()["rows"]], True)

print("\n=== YOPUVCHI STATUSLAR (avval ham ishlagan) ===")
rr = c.put(f"/api/tasks/{tid}", headers=H,
           json={"status": "done", "delay_reason": "kech qoldi"}).json()
ck("Bajarildi", rr["status"], "done")
ck("  yopilgach kechikish belgisi o'chadi", rr["overdue"], False)
rr = c.put(f"/api/tasks/{tid}", headers=H,
           json={"status": "cancelled"}).json()
ck("Bekor qilindi", rr["status"], "cancelled")

print("\n=== SANOQ ===")
c.put(f"/api/tasks/{tid}", headers=H, json={"status": "in_progress"})
d = c.get("/api/tasks", headers=H).json()
cnt = d["counts"]
ck("Jarayonda sanog'i 1", cnt.get("in_progress"), 1)
ck("Kechikdi sanog'i ham 1", cnt.get("late"), 1)
ck("umumiy ochiq vazifa 1", d["open"], 1)

print("\n=== MUDDATI O'TMAGAN VAZIFA ===")
ert = (date.today() + timedelta(days=5)).isoformat()
t2 = c.post("/api/tasks", headers=H, json={
    "title": "Kelasi hafta", "assignee_id": u.id,
    "deadline": ert, "branch_id": b.id}).json()["id"]
rr = c.put(f"/api/tasks/{t2}", headers=H,
           json={"status": "review"}).json()
ck("Tekshiruvda", rr["status"], "review")
ck("  kechikmagan", rr["overdue"], False)
lst = c.get("/api/tasks?status_filter=late", headers=H).json()
ck("Kechikdi tabida yo'q", t2 in [x["id"] for x in lst["rows"]], False)

print("\n=== 'late' STATUSINI QO'LDA QO'YIB BO'LMAYDI ===")
rr = c.put(f"/api/tasks/{t2}", headers=H, json={"status": "late"})
ck("rad etildi", rr.status_code, 400)

print("\n" + ("HAMMASI O'TDI" if not fails else "XATO: " + ", ".join(fails)))
sys.exit(1 if fails else 0)
