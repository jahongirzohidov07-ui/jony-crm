"""JONY STUDENT ilovasi: daraja, ko'nikmalar, lug'at o'yinlari va
reyting (2026-08-09, Jahongir so'radi).

Eng muhim tekshiruv — XAVFSIZLIK: bir o'quvchi boshqasining
ma'lumotini KO'RA OLMASLIGI kerak. /api/student/* yo'llarida
student_id umuman qabul qilinmaydi (tokendan olinadi), shuning uchun
bu yerda ikkita o'quvchi yaratilib, har biri faqat o'zinikini
ko'rayotgani tasdiqlanadi."""
import os, sys
from datetime import date

os.environ["DATABASE_URL"] = "sqlite:////tmp/verify_student_app/db.sqlite"
os.makedirs("/tmp/verify_student_app", exist_ok=True)
if os.path.exists("/tmp/verify_student_app/db.sqlite"):
    os.remove("/tmp/verify_student_app/db.sqlite")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
import main, models, roles
import entry  # noqa: F401 - haqiqiy jonli yo'llar
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


def ckt(name, cond):
    ck(name, bool(cond), True)


db = SessionLocal()
b = models.Branch(name="Zafar")
db.add(b)
db.commit()

ut = models.User(username="ust9", full_name="Ustoz Kamola",
                 password_hash=hash_password("x"), role="teacher",
                 branch_id=b.id, is_active=1)
db.add(ut)
db.commit()
teacher = models.Teacher(full_name="Ustoz Kamola", branch_id=b.id,
                         user_id=ut.id, is_active=1)
db.add(teacher)
db.commit()

g = models.Group(name="A2-Ertalab", subject="english", level="A2",
                 branch_id=b.id, teacher_id=teacher.id, lesson_time="08:00",
                 monthly_fee=400000, lesson_days="135", capacity=12)
db.add(g)
db.commit()

today = date.today()


def mk(name, uname, tag):
    u = models.User(username=uname, full_name=name,
                    password_hash=hash_password("Parol123!"),
                    role=roles.STUDENT, branch_id=b.id, is_active=1)
    db.add(u)
    db.commit()
    s = models.Student(full_name=name, branch_id=b.id, group_id=g.id,
                       status="active", enrolled_date=today,
                       public_id=f"STU-APP-{tag}", user_id=u.id)
    db.add(s)
    db.commit()
    return u, s


u1, s1 = mk("Ali Vositov", "ali", "1")
u2, s2 = mk("Malika Yusupova", "malika", "2")


def H(uname):
    r = client.post("/api/auth/login",
                    json={"username": uname, "password": "Parol123!"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


H1, H2 = H("ali"), H("malika")

print("=== LUG'AT BAZASI URUG'LANDI ===")
n_words = db.query(models.VocabWord).count()
ckt(f"boshlang'ich so'zlar bazaga tushdi ({n_words} ta)", n_words >= 100)

print("\n=== BOSH SAHIFA ===")
r = client.get("/api/student/home", headers=H1)
ck("status 200", r.status_code, 200)
d = r.json()
ck("o'z ismini ko'radi", d["name"], "Ali Vositov")
ck("guruhi ko'rinadi", d["group"], "A2-Ertalab")
ck("boshlang'ich daraja Beginner", d["overall"]["level"]["label"], "Beginner")
ck("6 ta ko'nikma qaytadi", len(d["skills"]), 6)
ck("o'yinlar ro'yxati to'liq", len(d["games"]), len(roles.VOCAB_GAMES))
ck("boshida streak 0", d["streak"], 0)

print("\n=== KO'NIKMALAR (har biri alohida daraja) ===")
r = client.get("/api/student/skills", headers=H1)
ck("status 200", r.status_code, 200)
sk = r.json()
keys = [x["key"] for x in sk["skills"]]
ck("ko'nikmalar to'g'ri", keys, roles.SKILL_KEYS)
voc = next(x for x in sk["skills"] if x["key"] == "vocabulary")
ck("lug'at boshida 0 ball", voc["points"], 0)
ck("keyingi darajagacha 500 ball", voc["next"]["points_left"], 500)

print("\n=== O'YIN BOSQICHI (round) ===")
r = client.get("/api/student/vocab/round?game=en_uz", headers=H1)
ck("status 200", r.status_code, 200)
rd = r.json()
ck("10 ta savol", len(rd["items"]), 10)
first = rd["items"][0]
ck("har savolda 4 variant", len(first["options"]), 4)
ckt("to'g'ri javob variantlar ichida", first["answer"] in first["options"])
ckt("variantlar takrorlanmaydi", len(set(first["options"])) == 4)

# Mashq sonini tanlash (2026-08-21, Jahongir: "10 yoki 25 va 60 va
# hammasi tanlaydigan bolishi kerak")
r = client.get("/api/student/vocab/round?game=en_uz&count=500", headers=H1)
ck("Hammasi (count=500) ishlaydi", r.status_code, 200)
pool_n = len(r.json()["items"])
ckt("Hammasi standart 10 tadan kam emas", pool_n >= 10)
r = client.get("/api/student/vocab/round?game=en_uz&count=25", headers=H1)
ck("count=25 status 200", r.status_code, 200)
ck("25 tagacha savol (baza yetsa 25)", len(r.json()["items"]),
   min(25, pool_n))

r = client.get("/api/student/vocab/round?game=match", headers=H1)
ck("juftlash o'yini ham ishlaydi", r.status_code, 200)

# JonyLugatBot'dagi qolgan ikki o'yin turi (2026-08-10)
r = client.get("/api/student/vocab/round?game=truefalse", headers=H1)
ck("To'g'ri/Xato o'yini ishlaydi", r.status_code, 200)
tf = r.json()["items"]
ck("10 ta savol", len(tf), 10)
ckt("har savolda ko'rsatilgan tarjima bor", all(i.get("shown") for i in tf))
n_true = sum(1 for i in tf if i["answer"] == "togri")
ckt("javoblar yarma-yarim (hamma vaqt 'ha' ishlamaydi)",
    2 <= n_true <= 8)

r = client.get("/api/student/vocab/round?game=scramble", headers=H1)
ck("Harflarni tartiblash ishlaydi", r.status_code, 200)
sc = r.json()["items"][0]
ckt("harflar berilgan", len(sc["letters"]) > 0)
ck("harflar so'zning o'zi", sorted(sc["letters"]), sorted(sc["answer"]))
r = client.get("/api/student/vocab/round?game=yoq", headers=H1)
ck("noma'lum o'yin rad etiladi", r.status_code, 400)

print("\n=== JAVOB BERISH (ball SERVERDA hisoblanadi) ===")
# Bazadagi birinchi so'z (JonyLugatBot bazasi katta-kichik harf
# aralash, shuning uchun aniq nom bo'yicha qidirilmaydi).
w = db.query(models.VocabWord).order_by(models.VocabWord.id).first()
# 2026-09-07: daraja kartasi endi har javobda YUBORILMAYDI (Neon
# compute tejash) — kerak bo'lsa ?want_skills=1 bilan so'raladi.
r = client.post("/api/student/vocab/answer?want_skills=1", headers=H1,
                json={"word_id": w.id, "game": "en_uz",
                      "answer": w.translation})
ck("status 200", r.status_code, 200)
a = r.json()
ck("to'g'ri deb qabul qilindi", a["correct"], True)
ck("lug'at bali 1 ga oshdi",
   next(x for x in a["skills"]["skills"]
        if x["key"] == "vocabulary")["points"], 1)

r = client.post("/api/student/vocab/answer", headers=H1,
                json={"word_id": w.id, "game": "en_uz",
                      "answer": "butunlay boshqa javob"})
ck("noto'g'ri javob rad etiladi", r.json()["correct"], False)
ck("noto'g'ri javobda to'g'risi ko'rsatiladi",
   r.json()["expected"], w.translation)

# Mijoz "men to'g'ri javob berdim" deb yolg'on aytolmaydi:
# server so'zni bazadan tekshiradi.
r = client.post("/api/student/vocab/answer", headers=H1,
                json={"word_id": w.id, "game": "uz_en",
                      "answer": w.translation})  # uz_en'da inglizcha kutiladi
ck("mijoz javobi serverda qayta tekshiriladi", r.json()["correct"], False)

# To'g'ri/Xato: server ko'rsatilgan tarjimani BAZA bilan solishtiradi
r = client.post("/api/student/vocab/answer", headers=H1,
                json={"word_id": w.id, "game": "truefalse",
                      "shown": w.translation, "answer": "togri"})
ck("to'g'ri tarjimaga 'to'g'ri' — qabul qilinadi",
   r.json()["correct"], True)
r = client.post("/api/student/vocab/answer", headers=H1,
                json={"word_id": w.id, "game": "truefalse",
                      "shown": "butunlay boshqa tarjima",
                      "answer": "togri"})
ck("noto'g'ri tarjimaga 'to'g'ri' — rad etiladi",
   r.json()["correct"], False)

# Harflarni tartiblash: to'g'ri yig'ilgan so'z qabul qilinadi
r = client.post("/api/student/vocab/answer", headers=H1,
                json={"word_id": w.id, "game": "scramble",
                      "answer": w.word})
ck("tartiblangan so'z to'g'ri", r.json()["correct"], True)

print("\n=== STATISTIKA ===")
r = client.get("/api/student/vocab/stats", headers=H1)
ck("status 200", r.status_code, 200)
st = r.json()
ckt("javoblar soni yozilgan", st["total"] >= 3)
ckt("to'g'ri javoblar sanaladi", st["correct"] >= 1)
ck("7 kunlik grafik", len(st["week"]), 7)
ck("bugundan streak 1", st["streak"], 1)

print("\n=== REYTING (boshqa o'quvchi ismi QISQARTIRILADI) ===")
# Malika 3 ta to'g'ri javob beradi -> u birinchi bo'lishi kerak
# Malika ATAYLAB ko'proq (6 ta) to'g'ri javob beradi — Ali yuqorida
# 3 ta to'g'ri javob berdi (en_uz + truefalse + scramble), shuning
# uchun reyting tartibi aniq bo'lishi kerak.
others = (db.query(models.VocabWord)
          .order_by(models.VocabWord.id).offset(1).limit(6).all())
for ww in others:
    client.post("/api/student/vocab/answer", headers=H2,
                json={"word_id": ww.id, "game": "en_uz",
                      "answer": ww.translation})

# 2026-08-16: reyting endi XP jurnalidan hisoblanadi (ilgari faqat
# lug'at javoblari sanalardi — Jahongir: "grammatikasi yoki
# speaking'i kuchli bolaga adolatsiz tuyuladi"). Javob berilganda
# har to'g'ri javob uchun 1 XP beriladi, shuning uchun sonlar
# o'zgarmadi. Javob shakli ham o'zgardi: birinchi uchtasi "podium",
# qolgani "rows".
r = client.get("/api/student/leaderboard?scope=group&period=all", headers=H1)
ck("status 200", r.status_code, 200)
lb = r.json()
ck("2 ta o'quvchi bor", len(lb["podium"]), 2)
ck("Malika birinchi (6 XP)", lb["podium"][0]["points"], 6)
ck("boshqa o'quvchi familiyasi qisqartirilgan",
   lb["podium"][0]["name"], "Malika Y.")
ck("o'zi 'Siz' deb ko'rsatiladi", lb["podium"][1]["name"], "Siz")
ck("o'z o'rni alohida qaytadi", lb["me"]["rank"], 2)
ck("sovrin ko'rsatilgan", lb["prize_coin"], 10)
# Guruh/filial/umumiy — uchalasi ham ochilishi kerak
for sc in ("group", "branch", "all"):
    rr = client.get(f"/api/student/leaderboard?scope={sc}&period=week",
                    headers=H1)
    ck(f"scope={sc} ishlaydi", rr.status_code, 200)
rr = client.get("/api/student/leaderboard?scope=xato", headers=H1)
ck("noto'g'ri scope rad etiladi", rr.status_code, 400)

print("\n=== O'RGANISH SAHIFASI (bitta so'rov) ===")
r = client.get("/api/student/learn", headers=H1)
ck("status 200", r.status_code, 200)
lr = r.json()
ck("6 ta bo'lim", len(lr["sections"]), 6)
ck("kunlik 3 vazifa", lr["daily"]["total"], 3)
ckt("XP qaytadi", isinstance(lr["lifetime_xp"], (int, float)))
ckt("har bo'limda foiz bor",
    all(isinstance(x["percent"], (int, float)) for x in lr["sections"]))

print("\n=== BOSH EKRAN: kunlik maqsad va davom ettirish ===")
hm = client.get("/api/student/home", headers=H1).json()
ckt("daily qo'shildi", "daily" in hm)
ck("uchta vazifa", hm["daily"]["total"], 3)
ckt("lug'at vazifasi hisoblanmoqda",
    hm["daily"]["tasks"][0]["done_count"] >= 1)
ckt("week_xp qaytadi", "week_xp" in hm)

print("\n=== XAVFSIZLIK ===")
# Ali'ning bosh sahifasi Malika'nikidan boshqa bo'lishi shart
r1 = client.get("/api/student/home", headers=H1).json()
r2 = client.get("/api/student/home", headers=H2).json()
ck("har kim o'z ismini ko'radi (Ali)", r1["name"], "Ali Vositov")
ck("har kim o'z ismini ko'radi (Malika)", r2["name"], "Malika Yusupova")
ckt("ballari ham alohida",
    r1["skills"][0]["points"] != r2["skills"][0]["points"])

# Ustoz (o'quvchi emas) bu yo'llarga kira olmaydi
Ht = H("ust9") if False else None
rt = client.post("/api/auth/login",
                 json={"username": "ust9", "password": "x"})
Ht = {"Authorization": f"Bearer {rt.json()['access_token']}"}
r = client.get("/api/student/home", headers=Ht)
ck("ustoz o'quvchi ilovasiga kira olmaydi", r.status_code, 403)

# Loginsiz umuman kirib bo'lmaydi
r = client.get("/api/student/home")
ckt("loginsiz kirish yopiq", r.status_code in (401, 403))

print("\n=== ADMIN: SO'Z IMPORTI ===")
ra = client.post("/api/auth/login", json={"username": "ust9", "password": "x"})
# Ustozda ACADEMIC_ACCESS yo'q — asoschi kerak
founder = models.User(username="dir9", full_name="Asoschi",
                      password_hash=hash_password("x"), role="founder",
                      branch_id=b.id, is_active=1)
db.add(founder)
db.commit()
Hf = {"Authorization": f"Bearer {client.post('/api/auth/login', json={'username': 'dir9', 'password': 'x'}).json()['access_token']}"}
before = db.query(models.VocabWord).count()
r = client.post("/api/vocab/import", headers=Hf, json={"words": [
    {"word": "resilience", "translation": "bardoshlilik", "level": "C1"},
    {"word": w.word, "translation": w.translation, "level": "A1"},  # dublikat
]})
ck("import 200", r.status_code, 200)
ck("1 ta yangi so'z qo'shildi", r.json()["added"], 1)
ck("dublikat o'tkazib yuborildi", r.json()["skipped"], 1)
ck("baza soni 1 ga oshdi",
   db.query(models.VocabWord).count(), before + 1)

r = client.post("/api/vocab/import", headers=H1, json={"words": []})
ck("o'quvchi so'z import qila olmaydi", r.status_code, 403)

print("\n=== YUTUQLAR VA SERTIFIKATLAR (2026-08-16) ===")
r = client.get("/api/student/achievements", headers=H1)
ck("status 200", r.status_code, 200)
ac = r.json()
ckt("yutuqlar ro'yxati bo'sh emas", len(ac["badges"]) > 0)
ck("streak sovrinlari 7 bosqich", len(ac["streak_rewards"]), 7)
ck("7 kunlik sovrin 1 coin", ac["streak_rewards"][0]["coin"], 1)
ck("365 kunlik sovrin 100 coin", ac["streak_rewards"][-1]["coin"], 100)

# STREAK AVTOMAT COIN (2026-08-21, Jahongir: "avtomat bersin"):
# 7 kun ketma-ket mashq yozamiz -> achievements ochilганda 1 coin
# o'zi tushishi kerak, ikkinchi ochishda TAKROR tushmasligi kerak.
from datetime import date as _d, timedelta as _td
for i in range(7):
    db.add(models.VocabAttempt(student_id=s1.id, game="en_uz",
                               correct=1,
                               date=_d.today() - _td(days=i)))
db.commit()
bal0 = (client.get(f"/api/students/{s1.id}", headers=Hf).json()
        if False else None)  # balansni to'g'ridan bazadan olamiz
from sqlalchemy import func as _f
def _coins():
    return int(db.query(_f.coalesce(_f.sum(models.CoinEntry.amount), 0))
               .filter(models.CoinEntry.student_id == s1.id,
                       models.CoinEntry.source == "streak").scalar() or 0)
r = client.get("/api/student/achievements", headers=H1)
ck("7 kun streak ko'rinadi", r.json()["streak"] >= 7, True)
db.expire_all()
ck("7 kunlik 1 coin avtomat tushdi", _coins(), 1)
r = client.get("/api/student/achievements", headers=H1)
db.expire_all()
ck("takror tushmadi", _coins(), 1)

# HAFTALIK REYTING G'OLIBI (2026-08-21): o'tgan haftaga XP yozamiz,
# boshlanish sanasini testda orqaga suramiz -> leaderboard ochilганda
# g'olibga 10 coin avtomat.
import student_app as _sa
_sa._RANK_PRIZE_FROM = _d.today() - _td(days=21)
from datetime import datetime as _dt2
_wk = _d.today() - _td(days=_d.today().weekday())  # shu hafta boshi
_prev = _wk - _td(days=7)
db.add(models.XpTransaction(student_id=s1.id, amount=40, is_reversal=0,
                            created_at=_dt2(_prev.year, _prev.month,
                                            _prev.day, 12, 0)))
db.commit()
r = client.get("/api/student/leaderboard?scope=all&period=week",
               headers=H1)
ck("leaderboard 200", r.status_code, 200)
ck("sovrin endi 10 coin", r.json()["prize_coin"], 10)
db.expire_all()
rank_coins = (db.query(models.CoinEntry)
              .filter(models.CoinEntry.source == "rank").all())
ck("o'tgan hafta g'olibiga yozildi", len(rank_coins) >= 1, True)
ck("g'olib to'g'ri va 10 coin",
   (rank_coins[-1].student_id, rank_coins[-1].amount), (s1.id, 10))
n_rank = len(rank_coins)
client.get("/api/student/leaderboard?scope=all&period=week", headers=H1)
db.expire_all()
ck("qayta ochishda takror berilmadi",
   db.query(models.CoinEntry)
   .filter(models.CoinEntry.source == "rank").count(), n_rank)
ckt("hech biri hali ochilmagan (yangi o'quvchi)", ac["done"] == 0)
ckt("keyingi maqsad ko'rsatilgan", ac["next"] is not None)
ckt("har yutuqda foiz bor",
    all(0 <= b["percent"] <= 100 for b in ac["badges"]))

r = client.get("/api/student/certificates", headers=H1)
ck("sertifikatlar 200", r.status_code, 200)
ck("hozircha yo'q", r.json()["count"], 0)

print("\n=== PROFIL: radar va sanoqlar ===")
r = client.get("/api/student/profile", headers=H1)
ck("status 200", r.status_code, 200)
pf = r.json()
ck("radar 6 ta ko'nikma", len(pf["radar"]), 6)
ckt("radar 0-100 oralig'ida",
    all(0 <= x["score"] <= 100 for x in pf["radar"]))
ckt("eng kuchli ko'rsatilgan", pf["strongest"] is not None)
ckt("eng zaif ko'rsatilgan", pf["weakest"] is not None)
ckt("yutuq sanog'i bor", pf["badges_total"] > 0)
ckt("eski maydonlar joyida", "full_name" in pf and "phone" in pf)

# Ustoz bu yo'llarga kira olmaydi
for path in ("/api/student/achievements", "/api/student/certificates",
             "/api/student/learn"):
    ck(f"ustozga yopiq: {path}",
       client.get(path, headers=Ht).status_code, 403)

print("\n" + ("BARCHASI OK" if not fails else f"XATOLAR: {fails}"))
sys.exit(1 if fails else 0)
