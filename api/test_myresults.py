"""Ustozning o'z natijalari: retention, churn, LTV va ketganlar."""
import os, sys
from datetime import date, timedelta

os.environ["DATABASE_URL"] = "sqlite:////tmp/myres_test.db"
if os.path.exists("/tmp/myres_test.db"):
    os.remove("/tmp/myres_test.db")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
import main, models, roles
from database import SessionLocal
from auth import hash_password

client = TestClient(main.app)
fails = []


def ck(name, got, want):
    ok = got == want
    print(("OK  " if ok else "XATO ") + name + f": {got}"
          + ("" if ok else f"   (kutilgan {want})"))
    if not ok:
        fails.append(name)


def tok(u, p="x"):
    return {"Authorization": "Bearer " + client.post(
        "/api/auth/login", json={"username": u, "password": p}
    ).json()["access_token"]}


TODAY = date.today()
MONTH_START = TODAY.replace(day=1)

db = SessionLocal()
b = models.Branch(name="Zafar"); db.add(b); db.commit()
BID = b.id
db.add(models.User(username="asos", password_hash=hash_password("x"),
                   full_name="Asos", role="founder"))
db.commit()

# Uch ustoz: yaxshi, o'rtacha, yomon
T = {}
for name in ["Yaxshi Ustoz", "O'rta Ustoz", "Yomon Ustoz", "Yangi Ustoz"]:
    t = models.Teacher(full_name=name, branch_id=BID, is_active=1,
                       grade="senior", hired_date=TODAY - timedelta(days=400))
    db.add(t); db.commit()
    T[name] = t.id
    g = models.Group(name=f"{name} guruhi", teacher_id=t.id,
                     branch_id=BID)
    db.add(g); db.commit()
    T[name + "_g"] = g.id

# Akkauntlar
for name in ["Yaxshi Ustoz", "Yangi Ustoz"]:
    r = models.User(username=roles.login_from_name(name),
                    password_hash=hash_password("x"),
                    full_name=name, role="teacher", branch_id=BID)
    db.add(r); db.commit()
    db.query(models.Teacher).get(T[name]).user_id = r.id
    db.commit()
    T[name + "_login"] = r.username


def add_student(teacher, name, enrolled_days, left_days=None, reason=None):
    s = models.Student(
        full_name=name, branch_id=BID, group_id=T[teacher + "_g"],
        enrolled_date=TODAY - timedelta(days=enrolled_days),
        status="left" if left_days is not None else "active",
        left_date=(TODAY - timedelta(days=left_days)
                   if left_days is not None else None))
    db.add(s); db.commit()
    if reason:
        db.add(models.LeaveReason(student_id=s.id, reason=reason))
        db.commit()
    return s.id


# Yaxshi ustoz: 9 faol, 1 ketgan (uzoq o'qigan)
for i in range(9):
    add_student("Yaxshi Ustoz", f"Faol {i}", 300)
add_student("Yaxshi Ustoz", "Ketgan Aziz", 400, 5, "moved")

# O'rta ustoz: 7 faol, 3 ketgan
for i in range(7):
    add_student("O'rta Ustoz", f"O'rta faol {i}", 200)
for i in range(3):
    add_student("O'rta Ustoz", f"O'rta ketgan {i}", 200, 40, "price")

# Yomon ustoz: 4 faol, 6 ketgan (tez ketgan)
for i in range(4):
    add_student("Yomon Ustoz", f"Yomon faol {i}", 150)
for i in range(6):
    add_student("Yomon Ustoz", f"Yomon ketgan {i}", 90, 30, "teacher")

# Yangi ustozda atigi 2 ta o'quvchi — solishtirish uchun kam
add_student("Yangi Ustoz", "Yakka bola", 60)
add_student("Yangi Ustoz", "Ikkinchi", 50, 10, "teacher")

db.commit(); db.close()

H = tok("asos")
HY = tok(T["Yaxshi Ustoz_login"])
HN = tok(T["Yangi Ustoz_login"])

print("=== 1. O'Z KO'RSATKICHLARI ===")

d = client.get("/api/me/results", headers=HY).json()
ck("ustoz topildi", d["teacher"]["name"], "Yaxshi Ustoz")
ck("faol o'quvchilar", d["students"]["active"], 9)
ck("ketganlar", d["students"]["left"], 1)
ck("jami", d["students"]["total"], 10)

# churn = 1 / 10 = 10%
ck("churn foizi", d["churn"]["value"], 10.0)
ck("retention foizi", d["retention"]["value"], 90.0)

print("\n=== 2. MARKAZ O'RTACHASI BILAN SOLISHTIRISH ===")

# Boshqa ustozlar: o'rta 3/10=30%, yomon 6/10=60%. Yangi ustoz 2 ta
# o'quvchi bilan hisobga kirmaydi.
ck("o'rtacha churn (o'zisiz)", d["churn"]["centre_avg"], 45.0)
ck("kam ketgani yaxshi deb baholandi", d["churn"]["verdict"],
   "O'rtachadan yaxshi")
ck("rangi yashil", d["churn"]["tone"], "emerald")
ck("markaz o'rtacha retention", d["retention"]["centre_avg"], 55.0)

ck("churn bo'yicha 1-o'rin", d["churn"]["rank"], 1)
ck("solishtirilgan ustozlar", d["churn"]["peers"], 3)

print("\n=== 3. LTV — QANCHA OY QOLGAN ===")

# Faqat ketganlar bo'yicha: 400-5 = 395 kun ≈ 13 oy
ck("o'rtacha muddat hisoblandi", d["ltv"]["value"] > 12, True)
ck("izoh berilgan", "Faqat" in d["ltv"]["note"], True)
ck("uzoq o'qigani yaxshi", d["ltv"]["verdict"], "O'rtachadan yaxshi")

print("\n=== 4. YETARLI MA'LUMOT YO'Q BO'LSA ===")

d2 = client.get("/api/me/results", headers=HN).json()
ck("yangi ustozda 2 ta o'quvchi", d2["students"]["total"], 2)
ck("yetarli emas deb belgilandi", d2["enough_data"], False)
ck("solishtirilmadi", d2["churn"]["verdict"],
   "Solishtirish uchun ma'lumot yetarli emas")
ck("o'rin berilmadi", d2["churn"]["rank"], None)
ck("sabab tushuntirildi", "kamida" in d2["hint"], True)
# Raqamning o'zi baribir chiqadi
ck("churn baribir hisoblandi", d2["churn"]["value"], 50.0)

print("\n=== 5. KETGANLAR RO'YXATI ===")

wins = {w["key"]: w for w in d["windows"]}
ck("4 ta oyna", len(d["windows"]), 4)
ck("oynalar nomi", [w["label"] for w in d["windows"]],
   ["Shu oyda", "Oxirgi 2 oy", "Oxirgi 6 oy", "Oxirgi 1 yil"])

ck("1 yilda 1 ta ketgan", wins["y1"]["count"], 1)
ck("6 oyda ham 1 ta", wins["m6"]["count"], 1)
ck("ketgan ismi", wins["y1"]["rows"][0]["name"], "Ketgan Aziz")
ck("guruhi ko'rsatilgan",
   wins["y1"]["rows"][0]["group"], "Yaxshi Ustoz guruhi")
ck("qancha o'qigani", wins["y1"]["rows"][0]["months"] > 12, True)
ck("sababi", wins["y1"]["rows"][0]["reason_label"],
   roles.LEAVE_REASON_LABELS["moved"])

print("\n=== 6. BIZGA BOG'LIQ VA BOG'LIQ EMAS ===")

# "moved" — ko'chib ketgan, ustozga bog'liq emas
ck("ko'chib ketish ustozga bog'liq emas",
   wins["y1"]["rows"][0]["controllable"], False)
ck("bog'liq bo'lmaganlar sanaldi", wins["y1"]["not_controllable"], 1)
ck("bog'liqlar yo'q", wins["y1"]["controllable"], 0)
ck("izoh berilgan", "bog'liq emas" in d["hint"], True)

# Yomon ustozda sabab "teacher" — bog'liq
db = SessionLocal()
yomon = db.query(models.Teacher).get(T["Yomon Ustoz"])
u = models.User(username="yomon", password_hash=hash_password("x"),
                full_name="Yomon Ustoz", role="teacher", branch_id=BID)
db.add(u); db.commit()
yomon.user_id = u.id; db.commit(); db.close()

HB = tok("yomon")
d3 = client.get("/api/me/results", headers=HB).json()
w3 = {w["key"]: w for w in d3["windows"]}
ck("yomon ustozda 6 ta ketgan", w3["m6"]["count"], 6)
ck("hammasi bizga bog'liq", w3["m6"]["controllable"], 6)
ck("churn yuqori", d3["churn"]["value"], 60.0)
ck("o'rtachadan past deb aytildi", d3["churn"]["verdict"],
   "O'rtachadan past")
ck("rangi sariq", d3["churn"]["tone"], "amber")

print("\n=== 7. SABABLAR KESIMI ===")

ck("sabab guruhlandi", len(d3["reasons"]), 1)
ck("sabab nomi", d3["reasons"][0]["label"],
   roles.LEAVE_REASON_LABELS["teacher"])
ck("soni", d3["reasons"][0]["count"], 6)
ck("bizga bog'liq", d3["reasons"][0]["controllable"], True)

print("\n=== 8. RUXSAT VA MAXFIYLIK ===")

ck("asoschi bu oynani ochmaydi",
   client.get("/api/me/results", headers=H).status_code, 403)

# Boshqa ustozlarning ismi CHIQMASLIGI kerak
import json
raw = json.dumps(d, ensure_ascii=False)
ck("boshqa ustoz ismi yo'q", "Yomon Ustoz" in raw, False)
ck("boshqa ustoz ismi yo'q 2", "O'rta Ustoz" in raw, False)
ck("boshqaning o'quvchisi yo'q", "Yomon ketgan" in raw, False)

print("\n=== 9. USTOZ YOZUVI ULANMAGAN ===")

db = SessionLocal()
lone = models.User(username="ulanmagan", password_hash=hash_password("x"),
                   full_name="Ulanmagan Kishi", role="teacher",
                   branch_id=BID)
db.add(lone); db.commit(); db.close()
r = client.get("/api/me/results", headers=tok("ulanmagan"))
ck("tushunarli xato", r.status_code, 404)
ck("nima qilish aytilgan", "HR" in r.json()["detail"], True)

print("\n=== 10. SOLISHTIRISH MANTIG'I ===")

ck("5% dan kam farq — o'rtacha",
   roles.compare_verdict(20.0, 20.5, lower_is_better=True)[0],
   "O'rtacha darajada")
ck("kam churn yaxshi",
   roles.compare_verdict(10.0, 30.0, lower_is_better=True)[0],
   "O'rtachadan yaxshi")
ck("ko'p churn yomon",
   roles.compare_verdict(50.0, 30.0, lower_is_better=True)[0],
   "O'rtachadan past")
ck("uzoq muddat yaxshi",
   roles.compare_verdict(12.0, 8.0)[0], "O'rtachadan yaxshi")
ck("ma'lumot yo'q", roles.compare_verdict(None, 8.0)[0],
   "Solishtirish uchun ma'lumot yetarli emas")

print()
if fails:
    print(f"XATOLAR ({len(fails)}): " + ", ".join(fails))
    sys.exit(1)
print("HAMMASI O'TDI")
