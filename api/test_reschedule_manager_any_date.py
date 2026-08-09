"""Rahbariyat/HR menejer darsni ISTALGAN sanaga ko'chira olishi,
hatto o'tib ketganiga ham (2026-08).

Kontekst: avval group_reschedule() HAMMA uchun (rahbariyatni ham
qo'shib) `to_date <= today` bo'lsa 400 qaytarardi. Birinchi bosqichda
faqat BUGUNGA ko'chirishga ruxsat berildi. Jahongir keyinroq aniq
so'radi: "o'tib ketganga ham hozir kerak" — oy oxirini qayta
taqsimlash yoki orqada qolgan jadvalni tuzatish uchun, HR menejerga
har qanday (o'tmish, bugun, kelajak) TO'DATE'ga ko'chirish kerak.

2026-08-09, YANA BIR BOSQICH: yuqoridagilar faqat TO'DATE
(qayerga ko'chirilishi) ni yumshatgan edi — lekin FROM_DATE (manba
darsning o'zi) allaqachon o'tib ketgan bo'lsa, HAMMA uchun (HR ham)
400 qaytardi: "O'tib ketgan darsni ko'chirib bo'lmaydi". Bu ataylab
emas edi — izoh allaqachon "yagona chegara shift_days va held" deb
yozilgan edi, lekin kod bunga hali to'liq mos kelmagan edi. Jahongir
aniq holat keltirdi: bir kun o'z vaqtida ko'chirilmay qolsa (masalan
ustoz unutgan), HR uni endi HAM ko'chira olmas, HAM yo'qlama qo'ya
olmas edi — ikkalasi ham kerak ("boshqa kunga ko'chirib, yo'qlama
qo'ya olish"). Endi 6-8 tekshiruvlar shuni yopadi: FROM_DATE uchun
ham xuddi TO_DATE'dagi kabi bir xil qoida — `not manager and ...`.
Yagona qolgan chegara — shift_days (ikkala tomonga ham amal qiladi)
va manba darsning "held" (allaqachon o'qitilgan/ish haqiga kirgan)
bo'lmasligi. Oddiy ustoz uchun talab TO'LIQ o'zgarmadi: qat'iy
kelajak, manba ham o'tmish bo'lmasligi kerak.

9-tekshiruv: yo'qlama tomoni aslida ALLAQACHON to'g'ri ekan
(entry.py'dagi eski HR huquqlari bo'limi — roles.PAST_ATTENDANCE
allaqachon HR_MANAGER'ni o'z ichiga oladi) — lekin bu haqiqiy
so'rov/javob oqimi orqali hech qachon tasdiqlanmagan edi, shuning
uchun endi bu yerda aniq tekshiriladi (statik o'qish emas).

MUHIM: `import entry` qilinadi — /api/groups/{gid}/reschedule ni
entry.py'dagi group_reschedule_v2 ochadi (to'g'ri delegatsiya qiladi,
lekin bu farqni his qilmasdan har doim haqiqiy yo'l orqali
tekshirish kerak). Yo'qlama uchun ham xuddi shu sabab bilan
save_attendance_v2 orqali o'tadi."""
import os, sys
from datetime import date, timedelta

os.environ["DATABASE_URL"] = "sqlite:////tmp/resched_anydate_test.db"
if os.path.exists("/tmp/resched_anydate_test.db"):
    os.remove("/tmp/resched_anydate_test.db")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
import main, models, roles
import entry  # noqa: F401
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


db = SessionLocal()
b = models.Branch(name="Zafar")
db.add(b)
db.commit()
BID = b.id

t = models.Teacher(full_name="Ustoz A", branch_id=BID, is_active=1)
db.add(t)
db.commit()
db.add(models.User(username="ust3", full_name="Ustoz A", role="teacher",
                   branch_id=BID, password_hash=hash_password("x"),
                   is_active=1))
db.add(models.User(username="hrm3", full_name="HR Menejer",
                   role="hr_manager", branch_id=BID,
                   password_hash=hash_password("x"), is_active=1))
db.commit()
t.user_id = db.query(models.User).filter(
    models.User.username == "ust3").first().id
db.commit()

g = models.Group(name="G-Sep", branch_id=BID, teacher_id=t.id,
                 lesson_time="10:00-11:00")
db.add(g)
db.commit()
GID = g.id

TODAY = date.today()
HR = tok("hrm3")
TEA = tok("ust3")

print("=== 1. GET attendance: box.manager to'g'ri keladi ===")
r0 = client.get(f"/api/groups/{GID}/attendance",
                params={"year": TODAY.year, "month": TODAY.month},
                headers=HR)
ck("status 200", r0.status_code, 200)
ck("HR uchun box.manager=True", r0.json()["reschedule"]["manager"], True)

r0b = client.get(f"/api/groups/{GID}/attendance",
                 params={"year": TODAY.year, "month": TODAY.month},
                 headers=TEA)
ck("ustoz uchun box.manager=False", r0b.json()["reschedule"]["manager"],
   False)

print("\n=== 2. HR menejer darsni BUGUNGA ko'chiradi ===")
from_date = TODAY + timedelta(days=15)
r1 = client.post(f"/api/groups/{GID}/reschedule", headers=HR, json={
    "from_date": from_date.isoformat(), "to_date": TODAY.isoformat(),
    "reason": "tezroq tugatish",
})
ck("so'rov muvaffaqiyatli", r1.status_code, 200)
ck("darrov qo'llandi", r1.json().get("applied"), True)
ls = db.query(models.Lesson).filter(
    models.Lesson.group_id == GID, models.Lesson.date == TODAY).first()
ck("dars bazada bugungi sanaga ko'chgan", bool(ls), True)

print("\n=== 2b. YANGI (to_date) ustunida 'boshqa kundan "
      "ko'chirilgan' belgisi chiqadi (YANGILIK, 2026-08-09) ===")
rbox = client.get(f"/api/groups/{GID}/attendance",
                  params={"year": TODAY.year, "month": TODAY.month},
                  headers=HR)
mi = rbox.json()["reschedule"].get("moved_in", {})
ck("bugungi sana moved_in'da bor", TODAY.isoformat() in mi, True)
ck("asl sana to'g'ri ko'rsatilgan",
   mi.get(TODAY.isoformat(), {}).get("from_date"), from_date.isoformat())

print("\n=== 3. HR menejer O'TIB KETGAN sanaga ham ko'chiradi (YANGILIK) ===")
from_date2 = TODAY + timedelta(days=16)
past_ok = TODAY - timedelta(days=5)   # shift_days (30) doirasida
r2 = client.post(f"/api/groups/{GID}/reschedule", headers=HR, json={
    "from_date": from_date2.isoformat(), "to_date": past_ok.isoformat(),
    "reason": "jadvalni qayta taqsimlash",
})
ck("so'rov muvaffaqiyatli (ilgari 400 edi)", r2.status_code, 200)
ck("darrov qo'llandi", r2.json().get("applied"), True)
ls2 = db.query(models.Lesson).filter(
    models.Lesson.group_id == GID, models.Lesson.date == past_ok).first()
ck("dars bazada o'tgan sanaga ko'chgan", bool(ls2), True)
ck("held=0 (hali o'qitilmagan, keyin belgilanishi mumkin)",
   ls2.held or 0, 0)

print("\n=== 4. shift_days chegarasi HALI HAM amal qiladi (ikkala "
      "tomonga ham) ===")
from_date3 = TODAY + timedelta(days=17)
too_far_past = TODAY - timedelta(
    days=roles.RESCHEDULE_MAX_SHIFT_DAYS + 10)
r3 = client.post(f"/api/groups/{GID}/reschedule", headers=HR, json={
    "from_date": from_date3.isoformat(),
    "to_date": too_far_past.isoformat(),
    "reason": "test",
})
ck("status 400 (shift chegarasi buzilmaydi)", r3.status_code, 400)
ck("sababi shift haqida",
   "ko'pi bilan" in r3.json().get("detail", ""), True)

print("\n=== 5. Oddiy ustoz hali ham bugun/o'tmishga ko'chira OLMAYDI "
      "(o'zgarmadi) ===")
from_date4 = TODAY + timedelta(days=18)
r4 = client.post(f"/api/groups/{GID}/reschedule", headers=TEA, json={
    "from_date": from_date4.isoformat(), "to_date": TODAY.isoformat(),
    "reason": "test",
})
ck("status 400 (ustoz uchun eski qoida saqlanadi)", r4.status_code, 400)
ck("sababi eski xabar bilan mos",
   "kelajakda bo'lishi kerak" in r4.json().get("detail", ""), True)

print("\n=== 6. HR menejer MANBA DARSNING O'ZI o'tib ketgan bo'lsa ham "
      "boshqa kunga suradi (YANGILIK, 2026-08-09) ===")
# Bir kun o'z vaqtida ko'chirilmay qolgan holatni simulyatsiya
# qiladi: from_date allaqachon o'tib ketgan, bazada mos Lesson
# yozuvi yo'q (hali "reja" holatida).
from_date6 = TODAY - timedelta(days=10)
to_date6 = TODAY - timedelta(days=6)
r5 = client.post(f"/api/groups/{GID}/reschedule", headers=HR, json={
    "from_date": from_date6.isoformat(), "to_date": to_date6.isoformat(),
    "reason": "vaqtida ko'chirilmay qolgan edi",
})
ck("so'rov muvaffaqiyatli (ilgari 400 edi)", r5.status_code, 200)
ck("darrov qo'llandi", r5.json().get("applied"), True)
ls5 = db.query(models.Lesson).filter(
    models.Lesson.group_id == GID, models.Lesson.date == to_date6).first()
ck("dars bazada yangi (o'tgan) sanaga ko'chgan", bool(ls5), True)
ck("held=0 (endi yo'qlama qo'yish mumkin)", ls5.held or 0, 0)

print("\n=== 7. O'TILGAN (held=1) darsni HR ham ko'chira OLMAYDI "
      "(ish haqi himoyasi o'zgarmadi) ===")
from_date7 = TODAY - timedelta(days=8)
held_ls = models.Lesson(group_id=GID, teacher_id=t.id, date=from_date7,
                        held=1, note="allaqachon o'qitilgan")
db.add(held_ls); db.commit()
r6 = client.post(f"/api/groups/{GID}/reschedule", headers=HR, json={
    "from_date": from_date7.isoformat(),
    "to_date": (TODAY - timedelta(days=3)).isoformat(),
    "reason": "test",
})
ck("status 400 (held dars himoyalangan)", r6.status_code, 400)
ck("sababi ish haqi haqida",
   "ish haqi asosi" in r6.json().get("detail", ""), True)

print("\n=== 8. Oddiy ustoz manba o'tmishda bo'lsa hali ham "
      "ko'chira OLMAYDI (to'liq yangi tekshiruv, o'zgarmadi) ===")
from_date8 = TODAY - timedelta(days=2)
r7 = client.post(f"/api/groups/{GID}/reschedule", headers=TEA, json={
    "from_date": from_date8.isoformat(),
    "to_date": (TODAY + timedelta(days=5)).isoformat(),
    "reason": "test",
})
ck("status 400 (ustoz uchun manba o'tmish bo'lsa ham taqiqlanadi)",
   r7.status_code, 400)
ck("sababi eski xabar bilan mos",
   "O'tib ketgan darsni" in r7.json().get("detail", ""), True)

print("\n=== 9. Ko'chirilgan o'tgan darsga YO'QLAMA: HR qo'ya oladi, "
      "ustoz qo'ya olmaydi (PAST_ATTENDANCE — allaqachon ochiq, "
      "endi haqiqiy oqim orqali tasdiqlanadi) ===")
r8 = client.put(f"/api/lessons/{ls5.id}/attendance", headers=HR,
                json={"marks": []})
ck("HR o'tgan kunga yo'qlama qo'ya oladi", r8.status_code, 200)
ck("javob ok", r8.json().get("ok"), True)

r9 = client.put(f"/api/lessons/{ls5.id}/attendance", headers=TEA,
                json={"marks": []})
ck("oddiy ustoz o'tgan kunga yo'qlama qo'ya OLMAYDI", r9.status_code, 403)
ck("sababi PAST_ATTENDANCE haqida",
   "o'quv bo'limi rahbari" in r9.json().get("detail", ""), True)

db.close()

print()
if fails:
    print(f"XATOLAR ({len(fails)}): " + ", ".join(fails))
    sys.exit(1)
print("HAMMASI O'TDI")
