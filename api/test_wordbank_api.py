"""LUG'AT BANKI — "So'z bilish" API testlari (2026-10-16, 2-qadam).

Tekshiriladi (vocab/DESIGN.md §2–§5, OWNER_DECISIONS D1, D4):
  * bayroq o'chiq -> hamma /api/wordbank/* 404; boshqa filial -> 404;
  * mashq sessiyasi: savollar server tomonda, javob kaliti yuborilmaydi;
  * baholash serverda, holat bazaga yoziladi, bir savolga bir marta;
  * tez yozilgan (shubhali) javob tasdiqlamaydi va (2026-10-16, review)
    na to'g'ri so'zni, na bahoni qaytaradi; 1200 ms oralig'i parallel
    sessiyalar bo'yicha ham o'lchanadi;
  * (2026-10-16, review) tanlash variantlari bir so'z uchun barqaror —
    bir necha sessiya / hajm testi kesishmasi javobni ochmaydi;
  * daraja tugasa N coin — aniq bir marta (ikki bosishda ham);
  * hajm testi — natija "taxminiy", so'z holatiga tegmaydi;
  * arxiv tarixni o'chirmaydi, asoschi o'chirishi FK xatosiz o'tadi.
So'zlar — testning o'zida yaratilgan kichik to'plam (3 daraja x 3 so'z),
haqiqiy 20 000 ro'yxat emas.

Ishga tushirish: PYTHONIOENCODING=utf-8 python test_wordbank_api.py
"""
import json
import os
import sys
from datetime import date, datetime, timedelta

os.environ["DATABASE_URL"] = "sqlite:////tmp/verify_wordbank_api/db.sqlite"
os.makedirs("/tmp/verify_wordbank_api", exist_ok=True)
if os.path.exists("/tmp/verify_wordbank_api/db.sqlite"):
    os.remove("/tmp/verify_wordbank_api/db.sqlite")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402
import main, models, roles  # noqa: E402,F401
import entry  # noqa: E402,F401 - jonli yo'llar va yamoqlar
import wordbank as WB  # noqa: E402
from database import SessionLocal  # noqa: E402
from auth import hash_password  # noqa: E402

client = TestClient(main.app)
fails = []


def ck(name, got, want):
    ok = got == want
    print(("OK  " if ok else "XATO ") + f"{name}: {got}"
          + ("" if ok else f"   (kutilgan {want})"))
    if not ok:
        fails.append(name)


def ckt(name, cond):
    ck(name, bool(cond), True)


# ---- Soxta soat: kunlar va ms oralig'ini test boshqaradi. Yamoq
# sys.modules bo'ylab qo'yiladi (entry.py modulni boshqa nom bilan
# ham yuklashi mumkin — eslatma: entry-monkeypatch-pitfall).
CLOCK = {"t": datetime(2026, 10, 1, 5, 0, 0)}       # Toshkent 10:00


def _fake_now():
    return CLOCK["t"]


for _m in list(sys.modules.values()):
    if (getattr(_m, "__file__", "") or "").endswith("wordbank.py") \
            and hasattr(_m, "_now"):
        _m._now = _fake_now


def tick(ms):
    CLOCK["t"] += timedelta(milliseconds=ms)


def next_day(n=1):
    CLOCK["t"] += timedelta(days=n)


DAY0 = date(2026, 10, 1)

# ------------------------------------------------------------ ma'lumot ---
db = SessionLocal()
bA = models.Branch(name="Pilot filial")
bB = models.Branch(name="Boshqa filial")
db.add_all([bA, bB])
db.commit()


def mk_user(uname, role, branch):
    u = models.User(username=uname, full_name=uname.title(),
                    password_hash=hash_password("Parol123!"), role=role,
                    branch_id=branch.id, is_active=1)
    db.add(u)
    db.commit()
    return u


def mk_student(name, uname, branch, tag):
    u = mk_user(uname, roles.STUDENT, branch)
    s = models.Student(full_name=name, branch_id=branch.id, status="active",
                       enrolled_date=DAY0, public_id=f"STU-WB-{tag}",
                       user_id=u.id)
    db.add(s)
    db.commit()
    return s


s1 = mk_student("Ali Vositov", "wb1", bA, "1")
s2 = mk_student("Malika Yusupova", "wb2", bA, "2")
s3 = mk_student("Boshqa Filialdagi", "wb3", bB, "3")
mk_user("wbteach", roles.TEACHER, bA)
mk_user("wbboss", roles.FOUNDER, bA)
S1, S2, S3 = s1.id, s2.id, s3.id

WORDS = [
    # (rank, band, lemma, uz, example_en, status)
    (1, 1, "time", "vaqt", "I have no time today.", "active"),
    (2, 1, "people", "odamlar", "Many people live here.", "active"),
    (3, 1, "year", "yil", "This year is good.", "active"),
    (4, 1, "thing", "narsa", "A small thing.", "disabled"),
    (1001, 2, "river", "daryo", "The river is long.", "active"),
    (1002, 2, "market", "bozor", "We go to the market.", "active"),
    (1003, 2, "winter", "qish", "Winter is cold.", "active"),
    (2001, 3, "harbor", "bandargoh", "Ships stay in the harbor.", "active"),
    (2002, 3, "lantern", "fonar", "He held a lantern.", "active"),
    (2003, 3, "meadow", "o'tloq", "Cows eat in the meadow.", "active"),
    (2004, 3, "quiver", None, "Leaves quiver.", "active"),    # tarjimasiz
]
for rank, band, lemma, uz, ex, st in WORDS:
    db.add(models.WordbankWord(rank=rank, band=band, lemma=lemma,
                               uz_primary=uz, uz_alt="[]", example_en=ex,
                               example_uz="(misol)", status=st))
db.commit()
LEMMA = {w.id: w.lemma for w in db.query(models.WordbankWord)}
WID = {v: k for k, v in LEMMA.items()}


def H(uname):
    r = client.post("/api/auth/login",
                    json={"username": uname, "password": "Parol123!"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


H1, H2, H3, HT, HF = H("wb1"), H("wb2"), H("wb3"), H("wbteach"), H("wbboss")


def set_flag(value):
    d = SessionLocal()
    row = d.query(models.IntegrationSetting).get("wordbank_branches")
    if row is None:
        row = models.IntegrationSetting(key="wordbank_branches")
        d.add(row)
    row.value = value
    d.commit()
    d.close()


def item_row(item_id):
    d = SessionLocal()
    it = d.query(models.WordbankSessionItem).get(item_id)
    d.expunge(it)
    d.close()
    return it


def state(sid, lemma):
    d = SessionLocal()
    sw = (d.query(models.WordbankStudentWord)
          .filter_by(student_id=sid, word_id=WID[lemma]).first())
    if sw is not None:
        d.expunge(sw)
    d.close()
    return sw


def coin_rows(sid):
    d = SessionLocal()
    n = (d.query(models.CoinEntry)
         .filter_by(student_id=sid, source="vocab_band").all())
    out = [(c.amount, c.ref_id) for c in n]
    d.close()
    return out


def answer(h, sid, it, ok=True, gap=3000, ms=None, text_=None):
    """it — sessiyadan kelgan savol. To'g'ri javob bazadan olinadi."""
    tick(gap)
    row = item_row(it["item_id"])
    if it["mode"] == "R":
        n = len(it["options"])
        idx = int(row.expected)
        given = idx if ok else (idx + 1) % n
    else:
        given = text_ if text_ is not None else (
            row.expected if ok else "zzzz")
    body = {"session_id": sid, "item_id": it["item_id"], "given": given}
    if ms is not None:
        body["ms"] = ms
    return client.post("/api/wordbank/answer", json=body, headers=h)


def lemma_of(it):
    return LEMMA[item_row(it["item_id"]).word_id]


print("=== 0. SXEMA: jadvallar va 0032 migratsiyasi ===")
names = {r[0] for r in db.execute(text(
    "SELECT name FROM sqlite_master WHERE type IN ('table','index')"))}
for t in ("wordbank_words", "wordbank_student_words", "wordbank_sessions",
          "wordbank_session_items", "wordbank_band_awards",
          "wordbank_size_tests"):
    ckt(f"jadval bor: {t}", t in names)
ckt("pul himoyasi: UNIQUE ux_wordbank_band_awards", "ux_wordbank_band_awards"
    in names)
ck("0032_wordbank qo'llangan",
   db.execute(text("SELECT COUNT(*) FROM schema_migrations "
                   "WHERE version = '0032_wordbank'")).scalar(), 1)

print("\n=== 1. BAYROQ O'CHIQ — HAMMAGA 404 ===")
for path, meth in (("/api/wordbank/me", "get"),
                   ("/api/wordbank/session", "post"),
                   ("/api/wordbank/answer", "post"),
                   ("/api/wordbank/size-test/start", "post"),
                   ("/api/wordbank/size-test/next", "post"),
                   ("/api/wordbank/size-test/finish", "post")):
    kw = {"headers": H1}
    if meth == "post":
        kw["json"] = {"session_id": 1, "item_id": 1}
    r = getattr(client, meth)(path, **kw)
    ck(f"sozlama yo'q: {path}", r.status_code, 404)
ck("tanasiz so'rov ham 404 (422 emas — yo'l oshkor bo'lmaydi)",
   client.post("/api/wordbank/answer", headers=H1).status_code, 404)
set_flag("")
ck("bo'sh qiymat ham o'chiq", client.get("/api/wordbank/me",
                                          headers=H1).status_code, 404)
set_flag(json.dumps([bB.id]))
ck("faqat boshqa filial yoqilgan — pilot o'quvchiga 404",
   client.get("/api/wordbank/me", headers=H1).status_code, 404)
ck("o'sha filial o'quvchisi ochiladi",
   client.get("/api/wordbank/me", headers=H3).status_code, 200)

print("\n=== 2. PILOT FILIAL YOQILDI ===")
set_flag(json.dumps([bA.id]))
ck("pilot o'quvchi: /me 200",
   client.get("/api/wordbank/me", headers=H1).status_code, 200)
ck("boshqa filial o'quvchisi: 404",
   client.get("/api/wordbank/me", headers=H3).status_code, 404)
ck("boshqa filial o'quvchisi sessiya ocholmaydi",
   client.post("/api/wordbank/session", json={}, headers=H3).status_code, 404)
ck("xodim (ustoz) — bo'lim yo'qdek: 404",
   client.get("/api/wordbank/me", headers=HT).status_code, 404)
set_flag("3, 5")
_d = SessionLocal()
ck("'3, 5' ko'rinishidagi qiymat ham o'qiladi", WB.enabled_branches(_d),
   {3, 5})
_d.close()
set_flag(json.dumps([bA.id]))
d0 =client.get("/api/wordbank/me", headers=H1).json()
ck("boshida tasdiqlangan 0", d0["known"], 0)
ck("20 ta daraja qatori", len(d0["bands"]), 20)
ck("1-daraja jami: faol so'zlar (o'chirilgan sanalmaydi)",
   d0["bands"][0]["total"], 3)
ck("3-daraja jami: tarjimasiz so'z ham daraja tarkibida",
   d0["bands"][2]["total"], 4)
ck("hajm testi hali yo'q", d0["size_test"], None)

print("\n=== 3. MASHQ SESSIYASI (0-kun) ===")
ck("size > 20 rad etiladi",
   client.post("/api/wordbank/session", json={"size": 21},
               headers=H1).status_code, 400)
ck("size = 0 rad etiladi",
   client.post("/api/wordbank/session", json={"size": 0},
               headers=H1).status_code, 400)
ck("tana obyekt emas — 400",
   client.post("/api/wordbank/answer", json=[1, 2],
               headers=H1).status_code, 400)
r = client.post("/api/wordbank/session", json={"size": 20}, headers=H1)
ck("status 200", r.status_code, 200)
sess = r.json()
items = sess["items"]
ck("9 ta yangi so'z (o'chirilgan va tarjimasiz chiqmaydi)", len(items), 9)
lem0 = [lemma_of(it) for it in items]
ck("rank tartibida", lem0, ["time", "people", "year", "river", "market",
                            "winter", "harbor", "lantern", "meadow"])
ckt("hammasi tanlash (R)", all(it["mode"] == "R" for it in items))
ckt("javob kaliti yuborilmaydi",
    all("expected" not in it and "answer" not in it
        and "correct" not in it for it in items))
ckt("4 tadan variant", all(len(it["options"]) == 4 for it in items))
ckt("variantlar ichida to'g'ri tarjima bor",
    all(dict((w[2], w[3]) for w in WORDS)[lemma_of(it)] in it["options"]
        for it in items))
SID0 = sess["session_id"]
by = {lemma_of(it): it for it in items}

# 2026-10-16 (review): javob bermasdan bir necha sessiya ochib,
# variantlar kesishmasidan to'g'ri tarjimani topib bo'lmasin — bir
# o'quvchi + so'z + holat uchun variantlar TO'PLAMI har safar bir xil.
_dups = [client.post("/api/wordbank/session", json={"size": 20},
                     headers=H1).json() for _ in range(2)]
_same = True
for _d_ in _dups:
    for it in _d_["items"]:
        if set(it["options"]) != set(by[lemma_of(it)]["options"]):
            _same = False
ck("3 sessiya: har so'zning variantlar to'plami bir xil", _same, True)
_inter = {lem: set(by[lem]["options"]) for lem in by}
for _d_ in _dups:
    for it in _d_["items"]:
        _inter[lemma_of(it)] &= set(it["options"])
ck("kesishma to'g'ri javobni ochmaydi (4 tadan qoladi)",
   sorted(len(v) for v in _inter.values()), [4] * 9)

# s2 s1 ning savoliga javob bera olmaydi (egasi emas)
r = client.post("/api/wordbank/answer", headers=H2,
                json={"session_id": SID0, "item_id": by["time"]["item_id"],
                      "given": 0})
ck("begona o'quvchi javobi: 404", r.status_code, 404)

res = {}
for lem in ("time", "people", "year", "river", "market", "harbor",
            "lantern", "meadow"):
    res[lem] = answer(H1, SID0, by[lem], ok=True)
res["winter"] = answer(H1, SID0, by["winter"], ok=False)
ckt("hammasi 200", all(x.status_code == 200 for x in res.values()))
ck("to'g'ri javob — correct", res["time"].json()["correct"], True)
ck("xato javob — correct=False", res["winter"].json()["correct"], False)
ck("xatodan keyin to'g'ri tarjima ko'rsatiladi",
   res["winter"].json()["expected"], "qish")
ck("birinchi to'g'ri javob — fast track: 2-pog'ona",
   res["time"].json()["stage"], 2)
ck("fast track hali tasdiqlanmagan", res["time"].json()["known"], False)
r = answer(H1, SID0, by["time"], ok=True)
ck("ikkinchi marta javob (ikki bosish): 409", r.status_code, 409)
st = state(S1, "time")
ck("holat bazada: 2-pog'ona", st.stage, 2)
ck("holat bazada: due +3 kun", st.due, DAY0 + timedelta(days=3))
ck("holat bazada: known=0", st.known, 0)
st = state(S1, "winter")
ck("xato yangi so'z: new_word, 0-pog'ona", st.stage, 0)
ck("xato yangi so'z: bugun qayta keladi", st.due, DAY0)
ck("hali coin yo'q", coin_rows(S1), [])
d = client.get("/api/wordbank/me", headers=H1).json()
ck("/me: tasdiqlangan 0", d["known"], 0)
ck("/me: 1-darajada o'rganilmoqda 3", d["bands"][0]["learning"], 3)
r = client.post("/api/wordbank/session", json={"size": 20}, headers=H1)
ck("bugun yana: faqat 'winter' (0-pog'ona, due bugun)",
   [lemma_of(it) for it in r.json()["items"]], ["winter"])

print("\n=== 4. 3-KUN: YOZIB TOPISH (P), SHUBHALI TEZ JAVOB ===")
next_day(3)
r = client.post("/api/wordbank/session", json={"size": 20}, headers=H1)
items = r.json()["items"]
SID1 = r.json()["session_id"]
by = {lemma_of(it): it for it in items}
ck("vaqti kelgan 9 so'z", sorted(by), sorted(
    ["time", "people", "year", "river", "market", "harbor", "lantern",
     "meadow", "winter"]))
ck("2-pog'ona (P yo'q) -> yozib topish", by["time"]["mode"], "P")
ck("0-pog'ona -> tanlash", by["winter"]["mode"], "R")
ckt("P savolida so'zning o'zi yo'q (faqat bosh harf)",
    "time" not in json.dumps(by["time"]).lower()
    and by["time"]["hint"] == "t")
ck("P savolida misol bo'shliq bilan", by["time"]["example"],
   "I have no ____ today.")
r = answer(H1, SID1, by["time"], ok=True, gap=300, ms=5000)
ck("server oralig'i 300 ms (mijoz 5000 desa ham) — shubhali",
   r.json()["suspect"], True)
ck("shubhali javob tasdiqlamaydi", r.json()["known"], False)
ck("shubhali javob pog'onani o'zgartirmaydi", state(S1, "time").stage, 2)
# 2026-10-16 (review): shubhali javob lemmani oshkor qilmasin — aks
# holda o'sha kuni qayta berilgan savolga uni yozib tasdiqlatish mumkin.
ck("shubhali javob: to'g'ri so'z qaytarilmaydi", r.json()["expected"], None)
ck("shubhali javob: baho ham qaytarilmaydi", r.json()["correct"], None)
ckt("shubhali javob matnida lemma yo'q",
    "time" not in json.dumps(r.json()).lower())
r_ok = r.json()
r = answer(H1, SID1, by["people"], ok=True, gap=5000, ms=800)
ck("mijoz 800 ms — kichigi olinadi, shubhali", r.json()["suspect"], True)
ck("people hali tasdiqlanmagan", state(S1, "people").known, 0)
r = answer(H1, SID1, by["meadow"], gap=5000, ms=0, text_="x")
ck("ms=0 + xato matn (PoC) — shubhali", r.json()["suspect"], True)
ck("ms=0 + xato matn: lemma qaytarilmaydi", r.json()["expected"], None)
ckt("ms=0 + xato matn: javobda 'meadow' yo'q",
    "meadow" not in json.dumps(r.json()).lower())
ck("shubhali to'g'ri va shubhali xato javob bir xil ko'rinadi (bepul "
   "tekshiruv yo'q)",
   {k: v for k, v in r.json().items() if k != "due"},
   {k: v for k, v in r_ok.items() if k != "due"})
ck("meadow holati o'zgarmadi (2-pog'ona, bugun due)",
   (state(S1, "meadow").stage, state(S1, "meadow").due),
   (2, DAY0 + timedelta(days=3)))
ck("bazada haqiqiy baho saqlanadi (keyingi anti-cheat uchun)",
   (item_row(by["meadow"]["item_id"]).correct,
    item_row(by["meadow"]["item_id"]).suspect), (0, 1))
# 2026-10-16 (review): parallel sessiya 1200 ms tekshiruvini chetlab
# o'tmasin — oraliq o'quvchining barcha ochiq sessiyalari bo'yicha.
r = client.post("/api/wordbank/session", json={"size": 20}, headers=H1)
SIDX = r.json()["session_id"]
byx = {lemma_of(it): it for it in r.json()["items"]}
ck("parallel sessiyada ham winter variantlari o'sha to'plam",
   set(byx["winter"]["options"]), set(by["winter"]["options"]))
r = answer(H1, SID1, by["year"], ok=True, gap=4000, text_="  YEAR. ")
ck("katta harf/bo'shliq farq qilmaydi — to'g'ri", r.json()["correct"], True)
ck("P to'g'ri -> tasdiqlangan", r.json()["known"], True)
ck("3-pog'ona", r.json()["stage"], 3)
ck("1-daraja hali to'liq emas — coin yo'q", r.json()["awards"], [])
r = answer(H1, SIDX, byx["river"], ok=True, gap=300)
ck("boshqa sessiyadagi javobdan 300 ms keyin — shubhali",
   r.json()["suspect"], True)
ck("river o'zgarmadi (2-pog'ona)", state(S1, "river").stage, 2)
for lem in ("river", "market", "harbor"):
    answer(H1, SID1, by[lem], ok=True, gap=4000)
answer(H1, SID1, by["winter"], ok=True, gap=4000)
r = answer(H1, SID1, by["lantern"], ok=False, gap=4000)
ck("P xato -> 1-pog'ona", r.json()["stage"], 1)
ck("2-daraja: winter hali o'rganilmoqda", state(S1, "winter").stage, 1)

print("\n=== 5. DARAJA TUGADI -> N COIN, BIR MARTA ===")
r = client.post("/api/wordbank/session", json={"size": 20}, headers=H1)
SID2 = r.json()["session_id"]
by = {lemma_of(it): it for it in r.json()["items"]}
ck("qayta keldi: shubhalilar va javobsiz qolgan", sorted(by),
   ["meadow", "people", "time"])
ckt("qayta berilgan P savolida ham lemma yo'q",
    "meadow" not in json.dumps(by["meadow"]).lower())
r = answer(H1, SID2, by["time"], ok=True, gap=4000)
ck("time tasdiqlandi", r.json()["known"], True)
ck("hali coin yo'q (people qoldi)", r.json()["awards"], [])
r = answer(H1, SID2, by["people"], ok=True, gap=4000)
ck("oxirgi so'z: 1-daraja tugadi -> 1 coin", r.json()["awards"],
   [{"band": 1, "coins": 1}])
r2 = answer(H1, SID2, by["people"], ok=True, gap=50)
ck("ikki bosish: 409", r2.status_code, 409)
ck("coin yozuvi aniq bitta (1 coin, ref=1)", coin_rows(S1), [(1, 1)])
for _ in range(2):
    client.get("/api/wordbank/me", headers=H1)
ck("/me ikki marta — coin baribir bitta", coin_rows(S1), [(1, 1)])
# Bir vaqtdagi ikki so'rov: ikkalasi ham "hali berilmagan" deb o'tdi deb
# faraz qilamiz — UNIQUE qator ikkinchisini to'xtatadi.
dd = SessionLocal()
stu = dd.query(models.Student).get(S1)
ck("poyga: to'g'ridan-to'g'ri ikkinchi to'lov -> None",
   WB._pay_band(dd, stu, 1, 1), None)
dd.commit()
ck("poyga: _award_bands qayta -> bo'sh", WB._award_bands(dd, stu, {1}), [])
dd.commit()
aw = dd.query(models.WordbankBandAward).filter_by(student_id=S1).all()
ck("daraja yozuvi bitta", [(a.band, a.coins) for a in aw], [(1, 1)])
ce = (dd.query(models.CoinEntry)
      .filter_by(student_id=S1, source="vocab_band").first())
ck("daraja yozuvi coin yozuviga bog'langan", aw[0].coin_entry_id, ce.id)
ck("coin izohi", ce.note, "So'z bilish: Common 1000 tugatildi (+1 coin)")
ck("coin manba nomi", roles.COIN_SOURCE_LABELS.get("vocab_band"),
   "So'z bilish: daraja tugatildi")
au = (dd.query(models.AuditLog)
      .filter_by(entity="student", entity_id=S1, action="vocab_band").all())
ck("auditda bitta yozuv", [a.new_value for a in au],
   ["Common 1000: +1 coin"])
dd.close()
d = client.get("/api/wordbank/me", headers=H1).json()
ck("/me: tasdiqlangan 6 (wordbank_core.known_count)", d["known"], 6)
ck("/me: 1-daraja tugagan", d["bands"][0]["done"], True)
ck("/me: 2-daraja tugamagan", d["bands"][1]["done"], False)
ck("/me: 1-daraja 3/3", (d["bands"][0]["known"], d["bands"][0]["total"]),
   (3, 3))
ck("/me: jami coin 1", d["coins_earned"], 1)

print("\n=== 6. UNUTISH -> COIN QAYTARILMAYDI, QAYTA TUGATISH -> COIN YO'Q ===")
next_day(7)                       # 10-kun: tasdiqlanganlar takrori
r = client.post("/api/wordbank/session", json={"size": 20}, headers=H1)
SID3 = r.json()["session_id"]
by = {lemma_of(it): it for it in r.json()["items"]}
ckt("time takrorga chiqdi", "time" in by)
r = answer(H1, SID3, by["time"], ok=False, gap=4000)
ck("xato -> unutildi (known=False)", r.json()["known"], False)
ck("xato -> 2-pog'ona", r.json()["stage"], 2)
ck("lapses=1", state(S1, "time").lapses, 1)
ck("coin qaytarib olinmaydi", coin_rows(S1), [(1, 1)])
ck("/me: tasdiqlangan 5", client.get("/api/wordbank/me",
                                     headers=H1).json()["known"], 5)
next_day(1)
r = client.post("/api/wordbank/session", json={"size": 20}, headers=H1)
SID4 = r.json()["session_id"]
by = {lemma_of(it): it for it in r.json()["items"]}
ck("unutilgan so'z P bilan qayta tekshiriladi", by["time"]["mode"], "P")
r = answer(H1, SID4, by["time"], ok=True, gap=4000)
ck("qayta tasdiqlandi", r.json()["known"], True)
ck("daraja qayta to'ldi — yangi coin YO'Q", r.json()["awards"], [])
ck("coin baribir bitta", coin_rows(S1), [(1, 1)])

print("\n=== 7. SESSIYA MUDDATI VA BEGONA SESSIYA ===")
r = client.post("/api/wordbank/session", json={"size": 5}, headers=H1)
SID5 = r.json()["session_id"]
it5 = r.json()["items"][0]
ck("size=5 -> 5 tadan ko'p emas", len(r.json()["items"]) <= 5, True)
tick(46 * 60 * 1000)
r = answer(H1, SID5, it5, ok=True, gap=0)
ck("45 daqiqadan keyin javob: 410", r.status_code, 410)
r = client.post("/api/wordbank/answer", headers=H1,
                json={"session_id": SID4, "item_id": it5["item_id"],
                      "given": 0})
ck("savol boshqa sessiyaniki: 404", r.status_code, 404)

print("\n=== 7b. O'Z-O'ZINI TIKLASH (ikki parallel javob darajani yopsa) ===")
# Ikki qurilmada bir vaqtda oxirgi ikki so'z tasdiqlansa, har tranzaksiya
# boshqasining so'zini hali ko'rmaydi va daraja "to'liq emas" deb o'tadi.
# Shu holatni bazada yasaymiz: /me uni topib, BIR marta to'lashi kerak.
dd = SessionLocal()
w_ = (dd.query(models.WordbankStudentWord)
      .filter_by(student_id=S1, word_id=WID["winter"]).first())
w_.stage, w_.known, w_.has_prod = 3, 1, 1
dd.commit()
dd.close()
ck("hali 2-daraja coini yo'q", coin_rows(S1), [(1, 1)])
d = client.get("/api/wordbank/me", headers=H1).json()
ck("/me 2-darajani to'laydi (2 coin)", sorted(coin_rows(S1)),
   [(1, 1), (2, 2)])
ck("/me: 2-daraja tugagan", d["bands"][1]["done"], True)
ck("/me: jami coin 3", d["coins_earned"], 3)
client.get("/api/wordbank/me", headers=H1)
ck("/me qayta — ortiqcha to'lov yo'q", sorted(coin_rows(S1)),
   [(1, 1), (2, 2)])

print("\n=== 8. HAJM TESTI — TAXMINIY, SO'Z HOLATIGA TEGMAYDI ===")


def snapshot(sid):
    d = SessionLocal()
    rows = sorted((r.word_id, r.stage, r.due, r.has_prod, r.known,
                   r.lapses, r.last_move)
                  for r in d.query(models.WordbankStudentWord)
                  .filter_by(student_id=sid))
    d.close()
    return rows


before = snapshot(S1)
coins_before = coin_rows(S1)
r = client.post("/api/wordbank/size-test/start", headers=H1)
ck("start 200", r.status_code, 200)
t = r.json()
TID = t["session_id"]
ck("1-daraja bilan boshlanadi", t["band"], 1)
ck("1-darajadan 3 so'z (o'chirilgan chiqmaydi)",
   sorted(lemma_of(it) for it in t["items"]), ["people", "time", "year"])
ckt("javob kaliti yo'q", all("expected" not in it and "answer" not in it
                             for it in t["items"]))
# 2026-10-16 (review): testni qayta boshlab ham variantlar kesishmasidan
# javobni topib bo'lmaydi — o'sha so'zlar o'sha to'plam bilan chiqadi.
_t2 = client.post("/api/wordbank/size-test/start", headers=H1).json()
ck("qayta boshlangan test: variantlar to'plami bir xil",
   {lemma_of(it): sorted(it["options"]) for it in _t2["items"]},
   {lemma_of(it): sorted(it["options"]) for it in t["items"]})
r = client.post("/api/wordbank/answer", headers=H1,
                json={"session_id": TID, "item_id": t["items"][0]["item_id"],
                      "given": 0})
ck("test savoli mashq yo'lidan qabul qilinmaydi", r.status_code, 404)
ans1 = [{"item_id": it["item_id"],
         "given": int(item_row(it["item_id"]).expected)}
        for it in t["items"]]
tick(5000)
r = client.post("/api/wordbank/size-test/next", headers=H1,
                json={"session_id": TID, "band": 1, "answers": ans1})
ck("1-blok yuborildi", r.status_code, 200)
b2 = r.json()
ck("keyingi daraja 2", b2.get("band"), 2)
r = client.post("/api/wordbank/size-test/next", headers=H1,
                json={"session_id": TID, "band": 1, "answers": ans1})
ck("1-blok qayta (ikki bosish): 409", r.status_code, 409)
r = client.post("/api/wordbank/size-test/next", headers=H2,
                json={"session_id": TID, "band": 2, "answers": []})
ck("begona o'quvchi testni davom ettira olmaydi: 404", r.status_code, 404)
its = b2["items"]
ans2 = []
for k, it in enumerate(its):
    exp = int(item_row(it["item_id"]).expected)
    if k == 0:
        ans2.append({"item_id": it["item_id"], "given": exp})          # R
    elif k == 1:
        ans2.append({"item_id": it["item_id"],
                     "given": (exp + 1) % len(it["options"])})          # W
    else:
        ans2.append({"item_id": it["item_id"], "given": None})  # Bilmayman
tick(5000)
r = client.post("/api/wordbank/size-test/next", headers=H1,
                json={"session_id": TID, "band": 2, "answers": ans2})
b3 = r.json()
ck("keyingi daraja 3", b3.get("band"), 3)
ck("3-darajadan faqat tarjimali 3 so'z", len(b3["items"]), 3)
tick(5000)
r = client.post("/api/wordbank/size-test/next", headers=H1,
                json={"session_id": TID, "band": 3, "answers": []})
fin = r.json()
ck("3-blok javobsiz ('Bilmayman') -> test tugadi", fin.get("done"), True)
res_ = fin["result"]
ck("natija 'taxminiy' deb belgilangan", res_["taxminiy"], True)
# p1=1, p2=(3.33-1.11)/10=0.222, p3=0 -> E=1222 -> 1200
ck("taxmin (wordbank_core.size_estimate)", res_["estimate"], 1200)
ck("darajalar natijasi saqlandi", res_["bands"],
   {"1": [3, 0, 3], "2": [1, 1, 3], "3": [0, 0, 3]})
r = client.post("/api/wordbank/size-test/finish", headers=H1,
                json={"session_id": TID})
ck("finish qayta — o'sha natija", r.json()["result"]["test_id"],
   res_["test_id"])
dd = SessionLocal()
ck("natija bitta qator",
   dd.query(models.WordbankSizeTest).filter_by(student_id=S1).count(), 1)
dd.close()
ck("so'z holatlari O'ZGARMADI", snapshot(S1), before)
ck("coin o'zgarmadi", coin_rows(S1), coins_before)
d = client.get("/api/wordbank/me", headers=H1).json()
ck("/me: tasdiqlangan son testdan o'zgarmaydi", d["known"], 7)
ck("/me: test natijasi alohida, taxminiy",
   (d["size_test"]["taxminiy"], d["size_test"]["estimate"]), (True, 1200))
r = client.post("/api/wordbank/size-test/finish", headers=H2,
                json={"session_id": TID})
ck("begona o'quvchi natijani ocholmaydi: 404", r.status_code, 404)

print("\n=== 9. D4: ARXIV TARIXNI O'CHIRMAYDI; O'CHIRISH FK XATOSIZ ===")
r = client.post("/api/wordbank/session", json={"size": 3}, headers=H2)
SIDB = r.json()["session_id"]
# 2026-10-16 (review): mashq va hajm testi bir so'z uchun bir xil
# variantlar beradi — ikkalasini kesishtirib ham javob topilmaydi.
_tb = client.post("/api/wordbank/size-test/start", headers=H2).json()
ck("mashq va hajm testi: kuzatilmagan so'z variantlari bir xil",
   {lemma_of(it): sorted(it["options"]) for it in _tb["items"]},
   {lemma_of(it): sorted(it["options"]) for it in r.json()["items"]})
answer(H2, SIDB, r.json()["items"][0], ok=True)
dd = SessionLocal()
st2 = dd.query(models.Student).get(S2)
st2.status = "archived"
dd.commit()
ck("arxivlangan o'quvchi ilovaga kira olmaydi: 403",
   client.get("/api/wordbank/me", headers=H2).status_code, 403)
ck("arxivdan keyin ham so'z holati turibdi",
   dd.query(models.WordbankStudentWord).filter_by(student_id=S2).count(), 1)
ck("arxivdan keyin ham sessiyalar turibdi (mashq + hajm testi)",
   dd.query(models.WordbankSession).filter_by(student_id=S2).count(), 2)
dd.close()
r = client.delete(f"/api/students/{S2}", headers=HF)
ck("asoschi o'chirishi o'tdi", r.status_code, 200)
dd = SessionLocal()
bad = []
for t_ in ("wordbank_student_words", "wordbank_sessions",
           "wordbank_session_items", "wordbank_size_tests"):
    bad += list(dd.execute(text(f"PRAGMA foreign_key_check({t_})")))
ck("FK buzilishi yo'q (sessiya savollari ham tozalandi)", bad, [])
ck("s2 savollari qolmadi",
   dd.query(models.WordbankSessionItem).filter_by(student_id=S2).count(), 0)
ck("s1 ma'lumoti tegilmagan",
   dd.query(models.WordbankStudentWord).filter_by(student_id=S1).count(), 9)
dd.close()

print("\n" + ("BARCHASI OK" if not fails else f"XATOLAR: {fails}"))
sys.exit(1 if fails else 0)
