"""BARABAN — lidlar testi oxiridagi sovg'a g'ildiragi (2026-09-25).

Jahongir: "shu testni bajargan oquvchiga oxirida baraban chiqishi
kerak va barabanda xar xil sovgalar skidkalar 10-100%gacha coinlar
10-100gacha bo'lishi kerak aylantirganda bittasiga tushsa shu sovga
avtomat unga otishi kerak".

Tekshiriladi (pul bor — hammasi):
  1. Bo'laklar seed'lanadi, o'rtacha chegirma ~13%.
  2. Test tugamasdan baraban chiqmaydi; tugagach chiqadi.
  3. SERVER tanlaydi, yozadi; ikkinchi bosish o'sha sovg'ani qaytaradi.
  4. Bir lidga BIR aylantirish: qayta test / bir xil telefon — yo'q.
  5. Og'irliklar ishlaydi: 20 000 tanlovda 100% ≈ 1%, 10 tanga ≈ 20%.
  6. TANGA: liddan o'quvchi ochilganda darrov CoinEntry, qayta emas.
  7. CHEGIRMA: faollashganda Discount(kind=wheel), faqat shu oy,
     faollashish hisobi 30% kam, keyingi oyda o'lik, qayta emas.
  8. Allaqachon FAOL o'quvchi (telefon mos): chegirma + shu oy hisobi
     qayta yoziladi (480 000 -> 384 000), ikkinchi urinish tegmaydi.
  9. 70%/100% — asoschiga Telegram (notify.send ushlab olinadi); 10% — yo'q.
 10. Sozlama: faqat asoschi; o'chirilgan bo'lak is_active=0, yo'qolmaydi.
 11. Lid ro'yxatida "wheel" maydoni.
"""
import os
import sys
import tempfile
from datetime import date, timedelta

_DIR = os.path.join(tempfile.gettempdir(), "wheel_test")
os.makedirs(_DIR, exist_ok=True)
_DB = os.path.join(_DIR, "db.sqlite")
os.environ["DATABASE_URL"] = "sqlite:///" + _DB.replace(chr(92), "/")
if os.path.exists(_DB):
    os.remove(_DB)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient          # noqa: E402
import main, models, roles                         # noqa: E402
import entry                                       # noqa: E402
import wheel, notify, common                       # noqa: E402
from database import SessionLocal                  # noqa: E402
from auth import hash_password                     # noqa: E402

c = TestClient(main.app)
fails = []


def ck(name, got, want):
    ok = got == want
    print(("OK  " if ok else "XATO ") + name + f": {got}"
          + ("" if ok else f"   (kutilgan {want})"))
    if not ok:
        fails.append(name)


today = roles.local_today()
PERIOD = f"{today.year:04d}-{today.month:02d}"
FIRST = today.replace(day=1)
MC = "avtomat (oylik)"

db = SessionLocal()
b = models.Branch(name="Zafar"); db.add(b); db.commit()
t = models.Teacher(full_name="Ustoz", branch_id=b.id); db.add(t); db.commit()
g = models.Group(name="Guruh", branch_id=b.id, teacher_id=t.id,
                 lesson_price=40_000, standard_lessons_per_month=12,
                 monthly_fee=480_000)
db.add(g); db.commit()
for d in range(1, 13):
    db.add(models.Lesson(group_id=g.id, teacher_id=t.id,
                         date=date(today.year, today.month, d), held=1))
BID, GID = b.id, g.id
founder = models.User(username="asos", password_hash=hash_password("x"),
                      full_name="Asoschi", role=roles.FOUNDER, is_active=1,
                      telegram_chat_id="777")
admin = models.User(username="admin1", password_hash=hash_password("x"),
                    full_name="Administrator", role=roles.ADMINISTRATOR,
                    branch_id=b.id, is_active=1)
db.add_all([founder, admin]); db.commit()
FOUNDER_ID, ADMIN_ID = founder.id, admin.id


def tok(u, p="x"):
    r = c.post("/api/auth/login", json={"username": u, "password": p})
    return {"Authorization": "Bearer " + r.json()["access_token"]}


HF = tok("asos")
HA = tok("admin1")

# Telegram ushlab olinadi — haqiqiy yuborilmaydi
SENT = []
notify.send = lambda chat_id, text: (SENT.append((chat_id, text)) or True)
wheel.notify = notify


def mk_lead(name, phone):
    ld = models.Lead(full_name=name, phone=phone, source="other",
                     stage="new", branch_id=BID)
    db.add(ld); db.commit()
    return ld


def mk_session(lead, status="done", token=None):
    PS = entry._PTS
    s = PS(token=token or ("tok-" + os.urandom(4).hex()), lead_id=lead.id,
           name=lead.full_name, phone=lead.phone, mode="link",
           status=status, branch_id=BID)
    db.add(s); db.commit()
    return s


print("=== 1. BO'LAKLAR ===")
r = c.get("/api/wheel/prizes", headers=HA)
ck("bo'laklar status", r.status_code, 200)
pz = r.json()
ck("10 ta bo'lak", len(pz["prizes"]), 10)
ck("o'rtacha chegirma ~13%", 12.0 <= pz["expected_discount_percent"] <= 14.0,
   True)
ck("tur/qiymat oralig'i",
   all(p["kind"] in ("coin", "discount") and 10 <= p["value"] <= 100
       for p in pz["prizes"]), True)

print("\n=== 2. TEST TUGAMASDAN BARABAN YO'Q ===")
L1 = mk_lead("Ali Valiyev", "998901112233")
s_run = mk_session(L1, status="running")
r = c.get(f"/api/public/placement/{s_run.token}/wheel")
ck("holat status", r.status_code, 200)
ck("tugamagan — available False", r.json()["available"], False)
r = c.post(f"/api/public/placement/{s_run.token}/wheel/spin")
ck("tugamagan — aylantirib bo'lmaydi (409)", r.status_code, 409)
s_run.status = "done"; db.commit()
r = c.get(f"/api/public/placement/{s_run.token}/wheel")
ck("tugagach — available True", r.json()["available"], True)
ck("bo'laklar ro'yxati keldi", len(r.json()["prizes"]), 10)

print("\n=== 3. SERVER TANLAYDI, IKKINCHI BOSISH O'SHA ===")
r = c.post(f"/api/public/placement/{s_run.token}/wheel/spin")
ck("spin status", r.status_code, 200)
sp1 = r.json()
ck("yangi yaratildi", sp1["created"], True)
ck("index bor", sp1["index"] >= 0, True)
ck("sovg'a bor", sp1["prize"]["kind"] in ("coin", "discount"), True)
row = db.query(models.WheelSpin).get(sp1["id"])
ck("bazada yozildi", row is not None, True)
ck("lidga bog'landi", row.lead_id, L1.id)
ck("telefon dumi saqlandi", row.phone, "901112233")
r = c.post(f"/api/public/placement/{s_run.token}/wheel/spin")
ck("ikkinchi bosish — o'sha id", r.json()["id"], sp1["id"])
ck("ikkinchi bosish — created False", r.json()["created"], False)
n_audit = (db.query(models.AuditLog)
           .filter(models.AuditLog.action == "wheel_spin").count())
ck("audit yozildi (1 ta)", n_audit, 1)

print("\n=== 4. BIR LIDGA BIR AYLANTIRISH ===")
s_re = mk_session(L1, status="done")          # qayta test
r = c.get(f"/api/public/placement/{s_re.token}/wheel")
ck("qayta test — available False", r.json()["available"], False)
ck("qayta test — spun True", r.json()["spun"], True)
ck("qayta test — o'sha sovg'a", r.json()["spin"]["id"], sp1["id"])
r = c.post(f"/api/public/placement/{s_re.token}/wheel/spin")
ck("qayta test — spin o'sha id", r.json()["id"], sp1["id"])
L1b = mk_lead("Ali Valiyev (dubl)", "+998 90 111-22-33")   # bir xil telefon
s_dup = mk_session(L1b, status="done")
r = c.get(f"/api/public/placement/{s_dup.token}/wheel")
ck("bir xil telefon — available False", r.json()["available"], False)
ck("bir xil telefon — o'sha sovg'a", r.json()["spin"]["id"], sp1["id"])
ck("jami spin 1 ta", db.query(models.WheelSpin).count(), 1)

print("\n=== 5. OG'IRLIKLAR (20 000 tanlov) ===")
prizes = wheel.active_prizes(db)
N = 20000
cnt = {}
for _ in range(N):
    p = wheel.pick_prize(prizes)
    cnt[(p.kind, p.value)] = cnt.get((p.kind, p.value), 0) + 1
p100 = cnt.get(("discount", 100), 0) * 100 / N
p10c = cnt.get(("coin", 10), 0) * 100 / N
print(f"     100% chegirma: {p100:.2f}%   10 tanga: {p10c:.2f}%")
ck("100% ≈ 1% (0.5..1.6)", 0.5 <= p100 <= 1.6, True)
ck("10 tanga ≈ 20% (17..23)", 17 <= p10c <= 23, True)
ck("hamma bo'lak tushdi", len(cnt), 10)


def force(spin, kind, value, label):
    spin.prize_kind, spin.prize_value, spin.prize_label = kind, value, label
    spin.prize_id = None
    db.commit()


print("\n=== 6. TANGA: LIDDAN O'QUVCHI OCHILGANDA DARROV ===")
L2 = mk_lead("Vali Aliyev", "998902223344")
s2 = mk_session(L2)
r = c.post(f"/api/public/placement/{s2.token}/wheel/spin")
sp2 = db.query(models.WheelSpin).get(r.json()["id"])
force(sp2, "coin", 50, "50 tanga")
r = c.post(f"/api/leads/{L2.id}/convert", headers=HA,
           json={"group_id": GID, "force": True})
ck("konvertatsiya", r.status_code, 200, )
st2_id = r.json()["id"]
ce = (db.query(models.CoinEntry)
      .filter(models.CoinEntry.student_id == st2_id,
              models.CoinEntry.source == "wheel").all())
ck("50 tanga yozildi", [x.amount for x in ce], [50])
db.refresh(sp2)
ck("spin o'quvchiga bog'landi", sp2.applied_student_id, st2_id)
ck("coin_entry_id yozildi", sp2.coin_entry_id, ce[0].id)
st2 = db.query(models.Student).get(st2_id)
wheel.apply_for_student(db, st2, on=None)
ce2 = (db.query(models.CoinEntry)
       .filter(models.CoinEntry.student_id == st2_id,
               models.CoinEntry.source == "wheel").count())
ck("qayta chaqirilganda takror emas", ce2, 1)
ck("tanga uchun chegirma yo'q",
   db.query(models.Discount).filter(
       models.Discount.student_id == st2_id).count(), 0)

print("\n=== 7. CHEGIRMA: FAOLLASHGANDA, FAQAT SHU OY ===")
L3 = mk_lead("Soli Valiyev", "998903334455")
s3 = mk_session(L3)
r = c.post(f"/api/public/placement/{s3.token}/wheel/spin")
sp3 = db.query(models.WheelSpin).get(r.json()["id"])
force(sp3, "discount", 30, "30% chegirma")
r = c.post(f"/api/leads/{L3.id}/convert", headers=HA,
           json={"group_id": GID, "force": True})
st3_id = r.json()["id"]
ck("konvertatsiyada (sinov) chegirma HALI yo'q",
   db.query(models.Discount).filter(
       models.Discount.student_id == st3_id).count(), 0)
db.refresh(sp3)
ck("lekin spin bog'landi", sp3.applied_student_id, st3_id)
# Nazorat o'quvchi — sovg'asiz, bir xil kunda faollashadi
ctrl = models.Student(full_name="Nazorat", branch_id=BID, group_id=GID,
                      status="trial", phone="998905556677")
db.add(ctrl); db.commit()
st3 = db.query(models.Student).get(st3_id)
common._activate_student(db, st3, on=FIRST, reason="test", user=None)
common._activate_student(db, ctrl, on=FIRST, reason="test", user=None)
db.commit()
dsc = (db.query(models.Discount)
       .filter(models.Discount.student_id == st3_id).all())
ck("faollashganda 1 ta chegirma", len(dsc), 1)
d3 = dsc[0]
ck("turi wheel", d3.kind, "wheel")
ck("30%", d3.percent, 30.0)
ck("faol", d3.status, "active")
ck("boshi = faollashish kuni", d3.start_date, FIRST)
ck("oxiri = shu oy oxiri", d3.end_date, wheel._month_end(FIRST, 1))
nxt = (FIRST.replace(day=28) + timedelta(days=4)).replace(day=1)
ck("keyingi oyda o'lik", common._discount_alive(d3, on=nxt), False)
ck("shu oyda tirik", common._discount_alive(d3, on=FIRST), True)


def charge(sid):
    p = (db.query(models.Payment)
         .filter(models.Payment.student_id == sid,
                 models.Payment.kind == "charge",
                 models.Payment.period == PERIOD).first())
    return int(abs(p.amount)) if p else None


ch3, chc = charge(st3_id), charge(ctrl.id)
print(f"     hisob: sovg'ali {ch3}, nazorat {chc}")
ck("nazorat hisobi bor", chc is not None and chc > 0, True)
ck("sovg'ali hisob 30% kam", ch3, int(round(chc * 0.7)))
db.refresh(sp3)
ck("discount_id yozildi", sp3.discount_id, d3.id)
wheel.apply_for_student(db, st3, on=FIRST)
ck("qayta chaqirilganda takror chegirma yo'q",
   db.query(models.Discount).filter(
       models.Discount.student_id == st3_id).count(), 1)
ck("hisob o'zgarmadi", charge(st3_id), ch3)

print("\n=== 8. ALLAQACHON FAOL O'QUVCHI (telefon mos) ===")
L4 = mk_lead("Kamol Valiyev", "998904445566")
s4 = mk_session(L4)
r = c.post(f"/api/public/placement/{s4.token}/wheel/spin")
sp4 = db.query(models.WheelSpin).get(r.json()["id"])
force(sp4, "discount", 20, "20% chegirma")
st4 = models.Student(full_name="Kamol Valiyev", branch_id=BID, group_id=GID,
                     status="active", enrolled_date=FIRST,
                     phone="+998 90 444 55 66")
db.add(st4); db.commit()
db.add(models.Payment(student_id=st4.id, amount=-480_000, kind="charge",
                      period=PERIOD, note="Guruh — 12 dars", created_by=MC))
db.commit()
out4 = wheel.apply_for_student(db, st4, on=None)
ck("qo'llandi (discount)", out4 and out4["did"], "discount")
ck("hisob 480 000 -> 384 000", charge(st4.id), 384_000)
out4b = wheel.apply_for_student(db, st4, on=None)
ck("ikkinchi urinish — did None", out4b and out4b["did"], None)
ck("hisob yana kamaymadi", charge(st4.id), 384_000)
n_dsc4 = (db.query(models.Discount)
          .filter(models.Discount.student_id == st4.id).count())
ck("bitta chegirma", n_dsc4, 1)

print("\n=== 8b. SO'M CHEGIRMA (discount_sum) ===")
L5 = mk_lead("Said Valiyev", "998905554433")
s5 = mk_session(L5)
r = c.post(f"/api/public/placement/{s5.token}/wheel/spin")
sp5 = db.query(models.WheelSpin).get(r.json()["id"])
force(sp5, "discount_sum", 60_000, "60 000 so'm chegirma")
st5 = models.Student(full_name="Said Valiyev", branch_id=BID, group_id=GID,
                     status="active", enrolled_date=FIRST,
                     phone="+998 90 555 44 33")
db.add(st5); db.commit()
db.add(models.Payment(student_id=st5.id, amount=-480_000, kind="charge",
                      period=PERIOD, note="Guruh — 12 dars", created_by=MC))
db.commit()
out5 = wheel.apply_for_student(db, st5, on=None)
ck("qo'llandi (so'm)", out5 and out5["did"], "discount")
d5 = (db.query(models.Discount)
      .filter(models.Discount.student_id == st5.id).one())
ck("summa yozildi", (d5.percent, d5.amount), (None, 60_000.0))
ck("faqat shu oy", d5.end_date, wheel._month_end(roles.local_today(), 1))
ck("hisob 480 000 -> 420 000", charge(st5.id), 420_000)
out5b = wheel.apply_for_student(db, st5, on=None)
ck("so'm: takror qo'llanmaydi", charge(st5.id), 420_000)

print("\n=== 9. TELEGRAM: 70%/100% — ha, 10% — yo'q ===")
SENT.clear()
# Faqat 100% faol qoldiriladi
for p in db.query(models.WheelPrize).all():
    p.is_active = 1 if (p.kind == "discount" and p.value == 100) else 0
db.commit()
L5 = mk_lead("Baxtiyor", "998905550001")
s5 = mk_session(L5)
r = c.post(f"/api/public/placement/{s5.token}/wheel/spin")
ck("100% tushdi", r.json()["prize"]["value"], 100)
ck("asoschiga xabar ketdi", len(SENT), 1)
ck("xabar asoschi chatiga", SENT and SENT[0][0], "777")
ck("xabarda 100% bor", SENT and ("100% chegirma" in SENT[0][1]), True)
sp5 = db.query(models.WheelSpin).get(r.json()["id"])
ck("notified_at yozildi", sp5.notified_at is not None, True)
SENT.clear()
for p in db.query(models.WheelPrize).all():
    p.is_active = 1 if (p.kind == "discount" and p.value == 10) else 0
db.commit()
L6 = mk_lead("Dilshod", "998905550002")
s6 = mk_session(L6)
r = c.post(f"/api/public/placement/{s6.token}/wheel/spin")
ck("10% tushdi", r.json()["prize"]["value"], 10)
ck("10% — xabar yo'q", len(SENT), 0)
# Hammasini qaytaramiz
for p in db.query(models.WheelPrize).all():
    p.is_active = 1
db.commit()

print("\n=== 10. SOZLAMA: FAQAT ASOSCHI, O'CHIRISH YO'Q ===")
cur = c.get("/api/wheel/prizes", headers=HF).json()["prizes"]
body = [dict(id=p["id"], kind=p["kind"], value=p["value"],
             weight=p["weight"], label=p["label"], is_active=p["is_active"],
             order_no=p["order_no"]) for p in cur]
body[-1]["is_active"] = False           # 100% ni o'chiramiz
body[0]["weight"] = 30.0
r = c.put("/api/wheel/prizes", headers=HA, json=body)
ck("admin o'zgartira olmaydi (403)", r.status_code, 403)
r = c.put("/api/wheel/prizes", headers=HF, json=body)
ck("asoschi saqladi", r.status_code, 200)
allp = db.query(models.WheelPrize).order_by(models.WheelPrize.id).all()
ck("bo'lak o'chirilmadi (10 ta qator)", len(allp), 10)
ck("100% is_active=0", allp[-1].is_active, 0)
ck("og'irlik o'zgardi", allp[0].weight, 30.0)
ck("faol bo'laklar 9 ta", len(wheel.active_prizes(db)), 9)
r = c.put("/api/wheel/prizes", headers=HF,
          json=[dict(kind="discount", value=150, weight=1)])
ck("150% rad etiladi", r.status_code, 400)
r = c.put("/api/wheel/prizes", headers=HF,
          json=[dict(kind="discount_sum", value=500, weight=1)])
ck("500 so'm rad etiladi (juda kam)", r.status_code, 400)
r = c.put("/api/wheel/prizes", headers=HF,
          json=body + [dict(kind="discount_sum", value=50_000, weight=2)])
ck("so'm bo'lak saqlandi", r.status_code, 200)
new = [p for p in r.json()["prizes"] if p["kind"] == "discount_sum"]
ck("yorliq avtomat", [p["label"] for p in new], ["50 000 so'm chegirma"])
ck("o'rtacha so'm xarajati bor", r.json()["expected_discount_sum"] > 0, True)
# Katta so'm chegirma — asoschiga xabar
SENT.clear()
L6 = mk_lead("Katta So'm", "998906667788")
s6 = mk_session(L6)
for p in db.query(models.WheelPrize).all():
    p.is_active = 0
db.add(models.WheelPrize(kind="discount_sum", value=400_000, weight=1,
                         label="400 000 so'm chegirma", is_active=1))
db.commit()
r = c.post(f"/api/public/placement/{s6.token}/wheel/spin")
ck("400 000 so'm tushdi", r.json()["prize"]["kind"], "discount_sum")
ck("asoschiga xabar ketdi", len(SENT) >= 1, True)

print("\n=== 11. LID RO'YXATIDA SOVG'A ===")
r = c.get("/api/leads", headers=HA)
ck("lidlar status", r.status_code, 200)
rows = {x["id"]: x for x in r.json()}
ck("L1 da wheel bor", (rows.get(L1.id) or {}).get("wheel") is not None, True)
ck("L1 sovg'a id to'g'ri", rows[L1.id]["wheel"]["id"], sp1["id"])
Lx = mk_lead("Sovg'asiz", "998909990000")
r = c.get("/api/leads", headers=HA)
rows = {x["id"]: x for x in r.json()}
ck("sovg'asiz lidda wheel None", rows[Lx.id].get("wheel"), None)
r = c.get(f"/api/leads/{L1.id}/wheel", headers=HA)
ck("lid wheel endpoint", r.json()["spin"]["id"], sp1["id"])

print()
if fails:
    print(f"XATO: {len(fails)} ta tekshiruv o'tmadi")
    for f in fails:
        print("   - " + f)
    sys.exit(1)
print("HAMMASI O'TDI")
sys.exit(0)
