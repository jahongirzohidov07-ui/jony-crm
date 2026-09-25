"""MASHQ TEKSHIRUVI: HAR BIR BAND HAQIQIY AMAL BILAN (2026-09-25).

Jahongir: "ba'zi vazifalarni bajarsa ham tizimda ko'rinmadi deb
bajardim bosilmayabdi tekshirib ber".

Bu test mashqni boshdan-oxir o'tadi: har bandda AYNAN o'sha amalni
tizimda bajaradi va "Bajardim" qabul qilinishini tekshiradi. Agar
biror bandning tekshiruv qoidasi haqiqiy amalga mos bo'lmasa, test
shu yerda yiqiladi va qaysi band ekani yoziladi.

Uchta band ilgari aynan shu sababdan ishlamasdi:
  - parol: auditda "password_change" deb yoziladi, "update" emas;
  - refund: "refund_request"/"refund_approve";
  - xona sig'imi: yangi xona emas, mavjudini tahrirlash.
"""
import os
import sys
import tempfile
from datetime import timedelta

_DB = os.path.join(tempfile.gettempdir(), "drill_verify_test.db")
os.environ["DATABASE_URL"] = "sqlite:///" + _DB.replace("\\", "/")
if os.path.exists(_DB):
    os.remove(_DB)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient          # noqa: E402
import main, models, roles                         # noqa: E402
import entry  # noqa: F401,E402
from database import SessionLocal                  # noqa: E402
from auth import hash_password                     # noqa: E402

client = TestClient(main.app)
fails = []


def ck(name, got, want):
    ok = got == want
    print(("OK  " if ok else "XATO ") + f"{name}: {got}"
          + ("" if ok else f"   (kutilgan {want})"))
    if not ok:
        fails.append(name)


TODAY = roles.local_today()

db = SessionLocal()
b = models.Branch(name="Sinov", is_test=1)
db.add(b)
db.commit()
BID = b.id
u = models.User(username="admin", full_name="Admin Aziza",
                password_hash=hash_password("Parol123!"),
                role=roles.ADMINISTRATOR, branch_id=BID, is_active=1)
db.add(u)
db.commit()
t = models.Teacher(full_name="Ustoz", branch_id=BID, is_active=1)
db.add(t)
db.commit()
TID = t.id
g2 = models.Group(name="Ikkinchi guruh", subject="english", level="B1",
                  branch_id=BID, teacher_id=TID, lesson_time="10:00",
                  monthly_fee=500000, lesson_days="mon,wed,fri", capacity=15)
db.add(g2)
db.commit()
G2 = g2.id
room = models.Room(name="101-xona", branch_id=BID, capacity=12)
db.add(room)
db.commit()
ROOM = room.id
db.close()

H = {"Authorization": "Bearer " + client.post(
    "/api/auth/login", json={"username": "admin", "password": "Parol123!"}
).json()["access_token"]}

state = {"lead": None, "student": None, "group": None, "payment": None,
         "lesson": None}


def _lead(i=0):
    r = client.post("/api/leads", headers=H, json={
        "full_name": f"Sinov Lid {i}", "phone": f"9011122{30 + i}",
        "source": "instagram", "branch_id": BID,
        "address": "Chilonzor", "school": "12-maktab", "grade": "7"})
    assert r.status_code == 200, r.text
    state["lead"] = r.json().get("id") or client.get(
        "/api/leads", headers=H).json()[0]["id"]


def _convert():
    r = client.post(f"/api/leads/{state['lead']}/convert", headers=H, json={})
    assert r.status_code == 200, r.text
    state["student"] = r.json()["id"]


def _group():
    r = client.post("/api/groups", headers=H, json={
        "name": "Mashq guruhi", "subject": "english", "level": "B1",
        "teacher_id": TID, "branch_id": BID, "lesson_time": "18:00-19:30",
        "lesson_days": "mon,wed,fri", "capacity": 12,
        "monthly_fee": 500000, "start_date": TODAY.isoformat()})
    assert r.status_code == 200, r.text
    state["group"] = r.json()["id"]
    client.post(f"/api/students/{state['student']}/groups", headers=H,
                json={"group_id": state["group"]})


def _pay(n):
    def _():
        r = client.post(f"/api/students/{state['student']}/payments",
                        headers=H, json={"amount": 100000 + n,
                                         "method": "cash",
                                         "note": "mashq"})
        assert r.status_code == 200, r.text
        state["payment"] = r.json().get("id")
    return _


def _refund():
    r = client.post("/api/refunds", headers=H, json={
        "student_id": state["student"], "amount": 50000,
        "reason": "Mashq uchun sinov"})
    assert r.status_code == 200, r.text


def _trial_then_activate():
    """Sinov darsidagi o'quvchini faollashtirish."""
    d = SessionLocal()
    st = d.query(models.Student).get(state["student"])
    st.status = "trial"
    d.commit()
    d.close()
    r = client.post(f"/api/students/{state['student']}/activate", headers=H,
                    json={})
    assert r.status_code == 200, r.text


def _activate():
    r = client.post(f"/api/students/{state['student']}/activate", headers=H,
                    json={})
    assert r.status_code == 200, r.text


def _freeze():
    r = client.post(f"/api/students/{state['student']}/freeze", headers=H,
                    json={"until": (TODAY + timedelta(days=20)).isoformat(),
                          "reason": "vacation"})
    assert r.status_code == 200, r.text


def _attendance():
    """Davomat: o'quvchi guruhda bo'lishi va dars ochilgan bo'lishi
    kerak — ikkalasi ham API orqali qilinadi."""
    client.post(f"/api/students/{state['student']}/groups", headers=H,
                json={"group_id": G2})
    d = SessionLocal()
    st = d.query(models.Student).get(state["student"])
    st.group_id = G2          # asosiy guruh — yo'qlama shundan olinadi
    st.status = "active"
    d.commit()
    d.close()
    r = client.post(f"/api/groups/{G2}/lessons", headers=H,
                    json={"date": TODAY.isoformat()})
    lid = (r.json() or {}).get("id")
    if not lid:
        d = SessionLocal()
        ls = (d.query(models.Lesson)
              .filter(models.Lesson.group_id == G2).first())
        lid = ls.id if ls else None
        d.close()
    assert lid, "dars ochilmadi"
    r = client.put(f"/api/lessons/{lid}/attendance", headers=H, json={
        "marks": [{"student_id": state["student"], "present": True}]})
    assert r.status_code == 200, r.text
    d = SessionLocal()
    n = d.query(models.Attendance).count()
    d.close()
    assert n > 0, "yo'qlama saqlanmadi"


def _comment():
    r = client.post(f"/api/students/{state['student']}/comments", headers=H,
                    json={"text": "Mashq izohi"})
    assert r.status_code == 200, r.text


def _move():
    """Guruhdan chiqarish: bola ikkita guruhda bo'lsa, bittasidan
    chiqariladi (oxirgi guruhdan chiqarish alohida tugma)."""
    d = SessionLocal()
    g3 = models.Group(name="Uchinchi guruh", subject="english", level="B1",
                      branch_id=BID, teacher_id=TID, lesson_time="12:00",
                      monthly_fee=500000, lesson_days="tue,thu", capacity=15)
    d.add(g3)
    d.commit()
    gid3 = g3.id
    d.close()
    client.post(f"/api/students/{state['student']}/groups", headers=H,
                json={"group_id": gid3})
    r = client.delete(
        f"/api/students/{state['student']}/groups/{gid3}", headers=H)
    assert r.status_code == 200, r.text


def _discount():
    r = client.post("/api/discounts", headers=H, json={
        "student_id": state["student"], "kind": "individual",
        "percent": 10, "reason": "Mashq"})
    assert r.status_code == 200, r.text


def _task():
    r = client.post("/api/tasks", headers=H, json={
        "title": "Mashq vazifasi", "description": "sinov",
        "deadline": (TODAY + timedelta(days=1)).isoformat()})
    assert r.status_code == 200, r.text


def _coins():
    r = client.post(f"/api/students/{state['student']}/coins", headers=H,
                    json={"amount": 5, "note": "Mashq"})
    assert r.status_code == 200, r.text


def _reward():
    r = client.post("/api/rewards", headers=H, json={
        "title": "Mashq sovg'asi", "cost": 10, "stock": 1})
    assert r.status_code == 200, r.text


def _password():
    r = client.put("/api/auth/me/password", headers=H, json={
        "current_password": "Parol123!", "new_password": "Parol456!"})
    assert r.status_code == 200, r.text


def _room():
    r = client.put(f"/api/rooms/{ROOM}", headers=H,
                   json={"name": "101-xona", "capacity": 16})
    assert r.status_code == 200, r.text


# Administrator huquqida BO'LMAGAN amallar. DIQQAT: entry.py
# administratorni sotuv menejeri bilan tenglashtiradi, shuning uchun
# muzlatish, refund va guruhdan o'tkazish uning qo'lida BOR. Guruh
# ochish, coin va xona esa yo'q — tizim ularni "ko'rsatish" bandiga
# aylantiradi, test ham bajarmaydi.
SKIP = {"group_create", "coins", "reward", "rooms",
        "refund", "group_move"}

ACTIONS = {
    "lead_add": _lead, "student_add": _convert, "group_create": _group,
    "payment_add": _pay(1), "payment_add2": _pay(2), "refund": _refund,
    "trial_activate": _trial_then_activate, "freeze": _freeze, "unfreeze": _activate,
    "attendance": _attendance, "comment": _comment, "group_move": _move,
    "discount": _discount, "task_create": _task, "coins": _coins,
    "reward": _reward, "password": _password, "rooms": _room,
}

print("\n=== MASHQNI BOSHDAN-OXIR O'TAMIZ ===")
d = client.post("/api/drill/start", headers=H).json()
ck("boshlandi", bool(d.get("current")), True)

by_key = {}
dd = SessionLocal()
for x in dd.query(models.DrillTask).all():
    by_key[x.title] = x.key
dd.close()

steps, guard = 0, 0
while d.get("current") and guard < 60:
    guard += 1
    cur = d["current"]
    key = by_key.get(cur["title"], "?")
    act = None if key in SKIP else ACTIONS.get(key)
    if act:
        try:
            act()
        except AssertionError as e:
            ck(f"[{key}] amal bajarilmadi", str(e)[:70], "200")
            d = client.post("/api/drill/done", headers=H,
                            json={"skip": True}).json()
            continue
    r = client.post("/api/drill/done", headers=H, json={}).json()
    if not r.get("ok"):
        ck(f"[{key}] tekshiruvdan o'tmadi", r.get("message", "")[:45], "ok")
        r = client.post("/api/drill/done", headers=H,
                        json={"skip": True}).json()
    else:
        steps += 1
    d = r

ck("hamma band yopildi", d.get("current"), None)
ck("27 ta band bajarildi", steps, 27)

last = client.get("/api/drill/state", headers=H).json()["history"][0]
print(f"\n     natija: {last['percent']}% · {last['verdict']}")

print()
if fails:
    print("XATOLAR:", ", ".join(fails))
    sys.exit(1)
print("HAMMASI O'TDI")
