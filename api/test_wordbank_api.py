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

2026-10-16 (3-qadam) qo'shimcha:
  * /api/wordbank/admin — faqat asoschi (boshqalarga 403); "all" hamma
    filialni ochadi, ro'yxat/[] bilan qaytariladi, har o'zgarish auditda;
  * words.json yuklovchisi: lemma bo'yicha upsert, ikki marta — bir xil
    son, skip=true va tarjimasiz qator yuklanmaydi, fayl yo'q — jim;
  * bir martalik "hammaga ochish" seedi: faqat bayroq qo'yilmagan bo'lsa,
    so'zlar to'liq yuklangach; /me va /session yuklangan so'zlar bilan.

2026-10-16 (review, 2-davra) qo'shimcha (12–17-bo'limlar):
  * qisman yuklangan daraja mashqqa chiqmaydi va coin to'lamaydi;
  * vaqt tugashi so'z holatiga tegmaydi, javobni ochmaydi; vaqtidan oldin
    kelgan "timeout" — oddiy "Bilmayman";
  * hajm testini erta tugatish ko'rilmagan blokni natijaga qo'shmaydi;
  * asoschining PUT [] i "hammaga ochish"dan ustun; 1-daraja to'liq
    bo'lmasa "hammaga ochish" kutadi;
  * rank surilgan 20 000 qatorli fayl chiziqli rejalanadi, qotgan so'z
    tarjimasi yangilanadi; yozib topishda misoldagi shakl ham to'g'ri.

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
# 2026-10-16: startdagi so'z seedi (main.py) haqiqiy words.json ni
# yuklamasin — test o'z kichik to'plami bilan ishlaydi (10–11-bo'limda
# seed alohida, sintetik fayl bilan tekshiriladi).
os.environ["WORDBANK_WORDS_FILE"] = "/tmp/verify_wordbank_api/yoq.json"
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


def set_band_size(n):
    """2026-10-16 (review): to'liq daraja chegarasi (wordbank.BAND_SIZE).
    Test to'plamida darajada 3–4 ta so'z — chegara 3 qilib qo'yiladi."""
    for _m in list(sys.modules.values()):
        if (getattr(_m, "__file__", "") or "").endswith("wordbank.py") \
                and hasattr(_m, "BAND_SIZE"):
            _m.BAND_SIZE = n


for _m in list(sys.modules.values()):
    if (getattr(_m, "__file__", "") or "").endswith("wordbank.py") \
            and hasattr(_m, "_now"):
        _m._now = _fake_now
set_band_size(3)


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
# 2026-10-16: startda words.json yo'q edi — "hammaga ochish" seedi
# bo'sh bo'limni ochmadi va belgisini ham qo'ymadi (keyin qayta urinadi).
ck("startda bayroq qo'yilmadi (so'zlar yo'q)",
   db.query(models.IntegrationSetting).get("wordbank_branches"), None)
ck("startda 'hammaga ochish' belgisi qo'yilmadi",
   db.query(models.SeedMark).get(WB.SEED_ENABLE_ALL), None)

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

print("\n=== 10. ADMIN: FAQAT ASOSCHI; \"all\" — BARCHA FILIALLAR ===")


def flag_raw():
    d = SessionLocal()
    row = d.query(models.IntegrationSetting).get("wordbank_branches")
    v = row.value if row is not None else None
    d.close()
    return v


def flag_audits():
    d = SessionLocal()
    rows = [(a.old_value, a.new_value, a.user_role)
            for a in d.query(models.AuditLog)
            .filter_by(entity="settings", field="wordbank_branches")
            .order_by(models.AuditLog.id)]
    d.close()
    return rows


ADM = "/api/wordbank/admin"
PILOT = json.dumps([bA.id])
ck("ustoz GET: 403", client.get(ADM, headers=HT).status_code, 403)
ck("o'quvchi GET: 403", client.get(ADM, headers=H1).status_code, 403)
ckt("tokensiz GET: 401/403",
    client.get(ADM).status_code in (401, 403))
r = client.put(ADM, json={"enabled": "all"}, headers=HT)
ck("ustoz PUT: 403", r.status_code, 403)
r = client.put(ADM, json={"enabled": "all"}, headers=H1)
ck("o'quvchi PUT: 403", r.status_code, 403)
ck("rad etilgan PUT bayroqni o'zgartirmadi", flag_raw(), PILOT)
g = client.get(ADM, headers=HF)
ck("asoschi GET: 200", g.status_code, 200)
ck("joriy holat: faqat pilot", g.json()["enabled"], [bA.id])
_br = {b["id"]: b["enabled"] for b in g.json()["branches"]}
ck("filiallar: pilot yoqilgan, boshqasi yo'q",
   (_br.get(bA.id), _br.get(bB.id)), (True, False))
ck("mashqqa tayyor so'zlar soni (o'chirilgan va tarjimasiz sanalmaydi)",
   g.json()["words"], 9)
for bad in ({"enabled": "hammasi"}, {"enabled": [999999]},
            {"enabled": [True]}, {"enabled": [1.5]}, {"enabled": None},
            {}, [bA.id]):
    ck(f"noto'g'ri so'rov 400: {bad}",
       client.put(ADM, json=bad, headers=HF).status_code, 400)
ck("noto'g'ri so'rovlar bayroqni o'zgartirmadi", flag_raw(), PILOT)
ck("hali audit yozuvi yo'q", flag_audits(), [])

r = client.put(ADM, json={"enabled": "all"}, headers=HF)
ck("PUT all: 200", r.status_code, 200)
ck("javob: enabled = all", r.json()["enabled"], "all")
ck("javob: o'zgardi", r.json()["changed"], True)
ckt("javob: barcha filiallar yoqilgan",
    r.json()["branches"] and all(b["enabled"] for b in r.json()["branches"]))
ck("bazada 'all'", flag_raw(), "all")
ck("auditda: eski -> yangi, asoschi", flag_audits(),
   [(PILOT, "all", roles.FOUNDER)])
ck("pilot o'quvchi: /me 200",
   client.get("/api/wordbank/me", headers=H1).status_code, 200)
ck("boshqa filial o'quvchisi ham ochildi: /me 200",
   client.get("/api/wordbank/me", headers=H3).status_code, 200)
ck("boshqa filial o'quvchisi sessiya ocha oladi",
   client.post("/api/wordbank/session", json={"size": 3},
               headers=H3).status_code, 200)
ck("xodim baribir 404 (bo'lim faqat o'quvchiga)",
   client.get("/api/wordbank/me", headers=HT).status_code, 404)
dd = SessionLocal()
bC = models.Branch(name="Yangi filial (keyin ochilgan)")
dd.add(bC)
dd.commit()
ck("'all': keyin ochilgan filial ham avtomat yoqilgan",
   WB.branch_enabled(dd, bC.id), True)
ck("'all': enabled_branches — bazadagi barcha filiallar",
   WB.enabled_branches(dd),
   {b.id for b in dd.query(models.Branch)})
ck("parse_flag: '\"all\"' (JSON) ham all", WB.parse_flag('"all"'), "all")
ck("parse_flag: '[]' — hamma joyda yopiq", WB.parse_flag("[]"), set())
dd.close()
r = client.put(ADM, json={"enabled": "ALL"}, headers=HF)
ck("qayta 'all' — o'zgarmadi, audit qo'shilmadi",
   (r.json()["changed"], len(flag_audits())), (False, 1))

r = client.put(ADM, json={"enabled": [bB.id]}, headers=HF)
ck("qaytarish: faqat boshqa filial", (r.status_code, r.json()["enabled"]),
   (200, [bB.id]))
ck("pilot o'quvchiga endi 404",
   client.get("/api/wordbank/me", headers=H1).status_code, 404)
ck("boshqa filial o'quvchisi: 200",
   client.get("/api/wordbank/me", headers=H3).status_code, 200)
r = client.put(ADM, json={"enabled": []}, headers=HF)
ck("[] — hamma joyda yopiq", (r.json()["enabled"], flag_raw()), ([], "[]"))
ck("[] dan keyin hammaga 404",
   [client.get("/api/wordbank/me", headers=h).status_code
    for h in (H1, H3)], [404, 404])
ck("[] dan keyin ham asoschi admin sahifasini ko'radi",
   client.get(ADM, headers=HF).status_code, 200)
r = client.put(ADM, json={"enabled": [str(bA.id)]}, headers=HF)
ck("id matn ko'rinishida ham qabul qilinadi", r.json()["enabled"], [bA.id])
ck("har o'zgarish auditda (4 ta)", [x[1] for x in flag_audits()],
   ["all", json.dumps([bB.id]), "[]", PILOT])

print("\n=== 11. SO'ZLAR FAYLI: UPSERT (O'CHIRMASDAN), IKKI MARTA — BIR XIL ===")
import common  # noqa: E402

SEED_DIR = "/tmp/verify_wordbank_api/seed"
os.makedirs(SEED_DIR, exist_ok=True)


def write_words(name, data):
    p = os.path.join(SEED_DIR, name)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    return p


def words_count():
    d = SessionLocal()
    n = d.query(models.WordbankWord).count()
    d.close()
    return n


def word(lemma):
    d = SessionLocal()
    w = d.query(models.WordbankWord).filter_by(lemma=lemma).first()
    if w is not None:
        d.expunge(w)
    d.close()
    return w


def drop_mark(key):
    """Belgini olib tashlaydi (seedni "qayta yurgizish" uchun)."""
    d = SessionLocal()
    d.query(models.SeedMark).filter_by(key=key).delete()
    d.commit()
    d.close()
    common._SEED_KEYS = None


P1 = write_words("words.json", {"version": "test", "words": [
    {"rank": 5001, "band": 6, "lemma": "glacier", "pos": ["NOUN", "VERB"],
     "uz_primary": "muzlik", "uz_alt": ["muz qatlami"],
     "example_en": "The glacier is melting.",
     "example_uz": "Muzlik erimoqda."},
    {"rank": 5002, "band": 6, "lemma": "orchard", "pos": "NOUN",
     "uz_primary": "meva bog'i", "uz_alt": [],
     "example_en": "We walked in the orchard.",
     "example_uz": "Biz meva bog'ida sayr qildik."},
    {"rank": 5003, "band": 6, "lemma": "pebble", "pos": "NOUN",
     "uz_primary": "shag'al", "uz_alt": "mayda tosh",
     "example_en": "He threw a pebble.", "example_uz": "U shag'al otdi."},
    {"rank": 5004, "band": 6, "lemma": "zzskip", "uz_primary": "o'tkaz",
     "skip": True},
    {"rank": 5005, "band": 6, "lemma": "zzempty", "uz_primary": "  "},
    # bor so'z — yangilanadi (id o'zgarmaydi, dublikat yo'q)
    {"rank": 1001, "band": 2, "lemma": "river", "pos": "NOUN",
     "uz_primary": "daryo", "uz_alt": ["soy"],
     "example_en": "The river is long.", "example_uz": "Daryo uzun."},
    # rank 1002 bazada "market"da (faylda yo'q) — u O'CHIRILMAYDI,
    # bu qator o'tkazib yuboriladi
    {"rank": 1002, "band": 2, "lemma": "brook", "uz_primary": "jilg'a"},
]})
n0 = words_count()
ck("fayl yo'q — jim o'tadi",
   WB.load_words(SessionLocal(), os.path.join(SEED_DIR, "yoq.json")),
   {"missing": True})
ck("fayl yo'q — so'zlar soni o'zgarmadi", words_count(), n0)
dd = SessionLocal()
r1 = WB.load_words(dd, P1)
dd.close()
ck("1-yurish: 3 yangi, 1 yangilangan, 2 tashlangan, 1 to'qnashuv",
   {k: r1[k] for k in ("inserted", "updated", "skipped", "conflicts",
                       "finished")},
   {"inserted": 3, "updated": 1, "skipped": 2, "conflicts": 1,
    "finished": True})
ck("so'zlar soni +3", words_count(), n0 + 3)
ckt("belgi kaliti wordbank_words_v1 bilan boshlanadi",
    r1["key"].startswith("wordbank_words_v1:"))
dd = SessionLocal()
ckt("belgi qo'yildi", dd.query(models.SeedMark).get(r1["key"]) is not None)
dd.close()
ck("skip=true qator yuklanmadi", word("zzskip"), None)
ck("tarjimasiz qator yuklanmadi", word("zzempty"), None)
ck("band rank'i band bo'lgan qator yuklanmadi", word("brook"), None)
ck("eski so'z (market) o'chirilmadi va joyida",
   (word("market").rank, word("market").status), (1002, "active"))
g_ = word("glacier")
ck("yangi so'z maydonlari",
   (g_.rank, g_.band, g_.pos, g_.uz_primary, json.loads(g_.uz_alt),
    g_.status),
   (5001, 6, "NOUN", "muzlik", ["muz qatlami"], "active"))
ck("uz_alt matn bo'lsa ro'yxatga aylanadi",
   json.loads(word("pebble").uz_alt), ["mayda tosh"])
rv = word("river")
ck("bor so'z yangilandi, id o'sha (o'quvchi holati saqlanadi)",
   (rv.id, json.loads(rv.uz_alt), rv.example_uz),
   (WID["river"], ["soy"], "Daryo uzun."))
ck("2-yurish: belgi bor — hech narsa qilinmaydi",
   WB.load_words(SessionLocal(), P1), None)
ck("2-yurishdan keyin soni o'sha", words_count(), n0 + 3)
drop_mark(r1["key"])
dd = SessionLocal()
r3 = WB.load_words(dd, P1)
dd.close()
ck("belgisiz qayta yurish ham idempotent (0 yangi, 0 yangilangan)",
   (r3["inserted"], r3["updated"], r3["finished"]), (0, 0, True))
ck("qayta yurishdan keyin ham soni o'sha", words_count(), n0 + 3)
# Ikki so'z rank'ini almashtirgan yangi fayl: UNIQUE(rank) yiqilmasin
# (avval vaqtincha manfiy rank'ga o'tkaziladi); faylda yo'q eski so'zlar
# (river va boshqalar) tegilmaydi.
_p1 = json.load(open(P1, encoding="utf-8"))["words"]
_sw = {"orchard": 5003, "pebble": 5002}
P3 = write_words("words3.json", [dict(e, rank=_sw.get(e["lemma"], e["rank"]))
                                 for e in _p1[:3]])
dd = SessionLocal()
r = WB.load_words(dd, P3)
dd.close()
ck("rank almashuvi: 2 yangilandi, to'qnashuvsiz",
   (r["inserted"], r["updated"], r["conflicts"], r["finished"]),
   (0, 2, 0, True))
ck("rank'lar almashdi", (word("orchard").rank, word("pebble").rank),
   (5003, 5002))
ck("faylda yo'q so'zlar o'chirilmadi", words_count(), n0 + 3)
ck("lug'at ko'rinishi ({lemma: {...}}) ham o'qiladi",
   [r["lemma"] for r in WB.parse_words(
       {"cliff": {"rank": 5006, "band": 6, "uz_primary": "qoya"}})[0]],
   ["cliff"])

print("\n=== 11b. BUDJET: QOLGANI KEYINGI STARTDA; 'HAMMAGA OCHISH' KUTADI ===")
P2 = write_words("words2.json", [
    {"rank": 6001 + i, "band": 7, "lemma": lem, "uz_primary": uz,
     "example_en": ex, "example_uz": "(misol)"}
    for i, (lem, uz, ex) in enumerate((
        ("canyon", "kanyon", "The canyon is deep."),
        ("dune", "qum tepa", "A dune of sand."),
        ("fjord", "fyord", "The fjord is cold.")))])
dd = SessionLocal()
r = WB.load_words(dd, P2, budget=2)
ck("budjet 2: 2 ta yozildi, 1 qoldi, tugamadi",
   (r["inserted"], r["left"], r["finished"]), (2, 1, False))
ckt("tugamagan — belgi yo'q, fayl 'kutilmoqda'",
    WB.words_pending(dd, P2))
ck("so'zlar to'liq emas — 'hammaga ochish' kutadi",
   WB.seed_enable_all(dd, P2), "pending")
ck("kutganda belgi qo'yilmadi",
   dd.query(models.SeedMark).get(WB.SEED_ENABLE_ALL), None)
r = WB.load_words(dd, P2, budget=2)
ck("keyingi start: qolgan 1 ta, tugadi", (r["inserted"], r["finished"]),
   (1, True))
ckt("endi kutilmayapti", not WB.words_pending(dd, P2))
dd.close()

print("\n=== 11c. BIR MARTALIK 'HAMMAGA OCHISH' (faqat bayroq qo'yilmagan bo'lsa) ===")
dd = SessionLocal()
dd.query(models.IntegrationSetting).filter_by(
    key="wordbank_branches").delete()
dd.commit()
n_aud = len(flag_audits())
ck("bayroq yo'q -> 'all'", WB.seed_enable_all(dd, P2), "enabled")
ck("bazada 'all'", flag_raw(), "all")
ck("tizim nomidan audit yozuvi", flag_audits()[n_aud:],
   [("(bo'sh)", "all", None)])
ckt("belgi qo'yildi",
    dd.query(models.SeedMark).get(WB.SEED_ENABLE_ALL) is not None)
dd.close()
r = client.put(ADM, json={"enabled": [bB.id]}, headers=HF)
dd = SessionLocal()
ck("asoschi qaytardi, seed qayta ochmaydi (bir marta)",
   (WB.seed_enable_all(dd, P2), flag_raw()), (None, json.dumps([bB.id])))
dd.close()
drop_mark(WB.SEED_ENABLE_ALL)
dd = SessionLocal()
ck("bayroq allaqachon qo'yilgan — tegilmaydi",
   (WB.seed_enable_all(dd, P2), flag_raw()),
   ("kept", json.dumps([bB.id])))
ckt("'kept' da ham belgi qo'yiladi",
    dd.query(models.SeedMark).get(WB.SEED_ENABLE_ALL) is not None)
dd.close()

print("\n=== 11d. YUKLANGAN SO'ZLAR: /me DARAJALAR, /session ISHLAYDI ===")
client.put(ADM, json={"enabled": "all"}, headers=HF)
dd = SessionLocal()
for w_ in dd.query(models.WordbankWord):
    LEMMA[w_.id] = w_.lemma
    WID[w_.lemma] = w_.id
dd.close()
d = client.get("/api/wordbank/me", headers=H1).json()
ck("/me: 6-daraja jami 3 (yuklangan), bilinganlar 0",
   (d["bands"][5]["total"], d["bands"][5]["known"], d["bands"][5]["ready"]),
   (3, 0, True))
ck("/me: 7-daraja jami 3", d["bands"][6]["total"], 3)
ck("/me: 2-daraja jami o'sha 3 (dublikat yo'q, brook qo'shilmadi)",
   d["bands"][1]["total"], 3)
ck("/me: so'z yo'q daraja — tayyor emas",
   (d["bands"][7]["total"], d["bands"][7]["ready"]), (0, False))
r = client.post("/api/wordbank/session", json={"size": 20}, headers=H1)
ck("/session: 200", r.status_code, 200)
SIDW = r.json()["session_id"]
byw = {lemma_of(it): it for it in r.json()["items"]}
ckt("yuklangan yangi so'zlar mashqqa chiqdi",
    {"glacier", "orchard", "pebble", "canyon", "dune", "fjord"}
    <= set(byw))
ck("yangi so'z — tanlash, 4 variant, to'g'risi ichida",
   (byw["glacier"]["mode"], len(byw["glacier"]["options"]),
    "muzlik" in byw["glacier"]["options"]), ("R", 4, True))
ckt("javob kaliti yuborilmaydi",
    all("expected" not in it for it in byw.values()))
r = answer(H1, SIDW, byw["glacier"], ok=True)
ck("glacier: fast track (2-pog'ona)", (r.status_code, r.json()["stage"]),
   (200, 2))
next_day(3)
r = client.post("/api/wordbank/session", json={"size": 20}, headers=H1)
SIDW2 = r.json()["session_id"]
byw = {lemma_of(it): it for it in r.json()["items"]}
ck("3 kundan keyin glacier — yozib topish", byw["glacier"]["mode"], "P")
ck("P savolida misol bo'shliq bilan", byw["glacier"]["example"],
   "The ____ is melting.")
r = answer(H1, SIDW2, byw["glacier"], ok=True, gap=4000)
ck("glacier tasdiqlandi", r.json()["known"], True)
d = client.get("/api/wordbank/me", headers=H1).json()
ck("/me: 6-daraja 1/3 bilinadi",
   (d["bands"][5]["known"], d["bands"][5]["total"]), (1, 3))
ck("asoschi sahifasi: tayyor so'zlar 9 + 6", client.get(
    ADM, headers=HF).json()["words"], 15)

print("\n=== 12. QISMAN YUKLANGAN DARAJA COIN TO'LAMAYDI (review) ===")
# 2026-10-16 (review): 9-darajada hozircha 2 ta so'z (chegara 3). O'quvchi
# ikkalasini bilsa ham daraja "tugamaydi", mashqqa ham chiqmaydi.
dd = SessionLocal()
for rank, lem, uz in ((8001, "zebra", "zebra"), (8002, "yacht", "yaxta")):
    dd.add(models.WordbankWord(rank=rank, band=9, lemma=lem, uz_primary=uz,
                               uz_alt="[]", example_en=f"A {lem}.",
                               example_uz="(misol)", status="active"))
dd.commit()
for w_ in dd.query(models.WordbankWord):
    LEMMA[w_.id] = w_.lemma
    WID[w_.lemma] = w_.id
dd.close()
d = client.get("/api/wordbank/me", headers=H1).json()
ck("9-daraja: 2 so'z, tayyor emas",
   (d["bands"][8]["total"], d["bands"][8]["ready"]), (2, False))
r = client.post("/api/wordbank/session", json={"size": 20}, headers=H3)
ck("qisman daraja so'zlari mashqqa chiqmaydi",
   [lemma_of(it) for it in r.json()["items"]
    if lemma_of(it) in ("zebra", "yacht")], [])
ckt("tayyor darajalar so'zlari esa chiqadi",
    {"time", "glacier", "canyon"} <= {lemma_of(it)
                                     for it in r.json()["items"]})
dd = SessionLocal()
for lem in ("zebra", "yacht"):
    dd.add(models.WordbankStudentWord(
        student_id=S1, word_id=WID[lem], stage=3, known=1, has_prod=1,
        lapses=0, due=DAY0 + timedelta(days=60), last_move=DAY0))
dd.commit()
stu = dd.query(models.Student).get(S1)
ck("ikkala so'z bilinsa ham _award_bands -> bo'sh",
   WB._award_bands(dd, stu, {9}), [])
dd.commit()
dd.close()
d = client.get("/api/wordbank/me", headers=H1).json()
ck("/me o'z-o'zini tiklash ham to'lamaydi",
   [c for c in coin_rows(S1) if c[1] == 9], [])
ck("/me: 9-daraja tugamagan", d["bands"][8]["done"], False)
dd = SessionLocal()
dd.add(models.WordbankWord(rank=8003, band=9, lemma="quill",
                           uz_primary="pat qalam", uz_alt="[]",
                           example_en="He wrote with a quill.",
                           example_uz="(misol)", status="active"))
dd.commit()
WID["quill"] = dd.query(models.WordbankWord).filter_by(
    lemma="quill").first().id
LEMMA[WID["quill"]] = "quill"
dd.close()
d = client.get("/api/wordbank/me", headers=H1).json()
ck("3-so'z yuklandi: daraja tayyor, 2/3 — hali coin yo'q",
   (d["bands"][8]["ready"], d["bands"][8]["known"], d["bands"][8]["total"],
    [c for c in coin_rows(S1) if c[1] == 9]), (True, 2, 3, []))
dd = SessionLocal()
dd.add(models.WordbankStudentWord(
    student_id=S1, word_id=WID["quill"], stage=3, known=1, has_prod=1,
    lapses=0, due=DAY0 + timedelta(days=60), last_move=DAY0))
dd.commit()
dd.close()
d = client.get("/api/wordbank/me", headers=H1).json()
ck("to'liq daraja tugadi -> 9 coin, bir marta",
   [c for c in coin_rows(S1) if c[1] == 9], [(9, 9)])
ck("/me: 9-daraja tugagan", d["bands"][8]["done"], True)

print("\n=== 13. VAQT TUGASHI — HOLATGA TEGMAYDI (review) ===")
# 2026-10-16 (review): avval vaqt tugashi oddiy xato edi — tasdiqlangan
# so'z unutilardi. Endi: o'tkazib yuborildi, holat o'zgarmaydi, javob
# ochilmaydi; vaqtidan oldin kelgan "timeout" — oddiy "Bilmayman".
next_day(30)
r = client.post("/api/wordbank/session", json={"size": 20}, headers=H1)
SIDT = r.json()["session_id"]
itsT = r.json()["items"]
known_its = [it for it in itsT if it["mode"] == "R"
             and state(S1, lemma_of(it)) is not None
             and state(S1, lemma_of(it)).known == 1]
ckt("sessiyada tasdiqlangan so'z (R) bor", known_its)
itK = known_its[0]
lemK = lemma_of(itK)
b4 = state(S1, lemK)
tick(16000)
r = client.post("/api/wordbank/answer", headers=H1,
                json={"session_id": SIDT, "item_id": itK["item_id"],
                      "given": None, "timeout": True, "ms": 15000})
ck("timeout: 200", r.status_code, 200)
ck("timeout: belgisi, baho va javob yo'q",
   (r.json()["timeout"], r.json()["correct"], r.json()["expected"]),
   (True, None, None))
ckt("timeout javobida lemma yo'q",
    lemK not in json.dumps(list(r.json().values())).lower())
a4 = state(S1, lemK)
ck("timeout: so'z holati O'ZGARMADI (tasdiqlangan qoldi)",
   (a4.stage, a4.known, a4.lapses, a4.due, a4.last_move, a4.has_prod),
   (b4.stage, b4.known, b4.lapses, b4.due, b4.last_move, b4.has_prod))
ck("timeout: savol yopildi (o'tkazib yuborildi)",
   (item_row(itK["item_id"]).answered_at is not None,
    item_row(itK["item_id"]).given, item_row(itK["item_id"]).correct),
   (True, None, 0))
r = client.post("/api/wordbank/answer", headers=H1,
                json={"session_id": SIDT, "item_id": itK["item_id"],
                      "given": 0})
ck("timeoutdan keyin qayta javob: 409", r.status_code, 409)
itF = [it for it in itsT if it is not itK][0]
tick(2000)
r = client.post("/api/wordbank/answer", headers=H1,
                json={"session_id": SIDT, "item_id": itF["item_id"],
                      "given": None, "timeout": True, "ms": 15000})
ck("2 s da kelgan 'timeout' — oddiy 'Bilmayman' (xato)",
   (bool(r.json().get("timeout")), r.json()["correct"]), (False, False))

print("\n=== 14. HAJM TESTI: ERTA TUGATISH — KO'RILMAGAN BLOK YO'Q (review) ===")
r = client.post("/api/wordbank/size-test/start", headers=H1)
TS = r.json()
ck("yangi test 1-darajadan", TS["band"], 1)
it0 = TS["items"][0]
tick(4000)
r = client.post("/api/wordbank/size-test/finish", headers=H1,
                json={"session_id": TS["session_id"], "band": 1,
                      "answers": [{"item_id": it0["item_id"],
                                   "given": int(item_row(
                                       it0["item_id"]).expected),
                                   "ms": 3000}]})
ck("finish (javoblar bilan): 200", r.status_code, 200)
resF = r.json()["result"]
ck("natijada faqat ko'rilgan blok (2-daraja yo'q)", sorted(resF["bands"]),
   ["1"])
ck("1-blok: 1 to'g'ri, qolganlari 'Bilmayman'", resF["bands"]["1"],
   [1, 0, len(TS["items"])])
dd = SessionLocal()
ck("sessiyada yangi blok ochilmadi",
   sorted({i.band for i in dd.query(models.WordbankSessionItem)
           .filter_by(session_id=TS["session_id"])}), [1])
dd.close()
r = client.post("/api/wordbank/size-test/finish", headers=H1,
                json={"session_id": TS["session_id"], "band": 1,
                      "answers": [{"item_id": it0["item_id"], "given": 0}]})
ck("finish qayta (ikki bosish) — o'sha natija",
   (r.status_code, r.json()["result"]["test_id"]), (200, resF["test_id"]))

print("\n=== 15. ASOSCHI PUT [] — BAYROQ QO'YILMAGAN PAYTDA (review) ===")
# 2026-10-16 (review): "" va "[]" bir xil (yopiq) edi — PUT [] hech narsa
# yozmasdi va keyingi startda seed_enable_all bayroqni "all" qilardi.
dd = SessionLocal()
dd.query(models.IntegrationSetting).filter_by(
    key="wordbank_branches").delete()
dd.commit()
dd.close()
drop_mark(WB.SEED_ENABLE_ALL)
r = client.put(ADM, json={"enabled": []}, headers=HF)
ck("PUT [] (bayroq yo'q edi): o'zgardi va yozildi",
   (r.json()["changed"], flag_raw()), (True, "[]"))
dd = SessionLocal()
ck("seed_enable_all asoschi qarorini bosib ketmaydi",
   (WB.seed_enable_all(dd, P2), flag_raw()), ("kept", "[]"))
dd.close()
# 1-daraja to'liq bo'lmasa — "hammaga ochish" kutadi
dd = SessionLocal()
dd.query(models.IntegrationSetting).filter_by(
    key="wordbank_branches").delete()
dd.commit()
dd.close()
drop_mark(WB.SEED_ENABLE_ALL)
set_band_size(1000)
dd = SessionLocal()
ck("1-daraja to'liq emas -> 'not-ready', bayroq qo'yilmadi",
   (WB.seed_enable_all(dd, P2), flag_raw()), ("not-ready", None))
ck("'not-ready' da belgi qo'yilmadi",
   dd.query(models.SeedMark).get(WB.SEED_ENABLE_ALL), None)
dd.close()
set_band_size(3)

print("\n=== 16. RANK SURILISHI: CHIZIQLI, TARJIMA TUZATISHI TUSHADI (review) ===")
import time as _time  # noqa: E402

N = 20000
_have = {f"w{i}": {"id": i, "rank": i} for i in range(1, N + 1)}
_rows = [{"lemma": f"w{i}", "rank": i - 1} for i in range(2, N + 1)]
_t0 = _time.perf_counter()
_acc, _conf = WB._plan(_have, _rows)
_dt = _time.perf_counter() - _t0
ck("20 000 qator, rank bittaga surilgan: hammasi qotdi",
   (len(_acc), len(_conf)), (0, N - 1))
ckt(f"chiziqli: {_dt:.3f} s < 2 s", _dt < 2)
_acc, _conf = WB._plan(_have, [{"lemma": f"w{i}", "rank": i}
                               for i in range(1, N + 1)])
ck("surilmagan fayl: hammasi qabul", (len(_acc), len(_conf)), (N, 0))
_acc, _conf = WB._plan({"a": {"rank": 1}, "b": {"rank": 2}},
                       [{"lemma": "a", "rank": 2}, {"lemma": "b", "rank": 1}])
ck("almashuv to'qnashuv emas", (len(_acc), _conf), (2, []))
# Bazada canyon 6001, dune 6002, fjord 6003. Faylda canyon yo'q, dune va
# fjord bittaga yuqoriga surilgan va tarjimasi tuzatilgan.
P4 = write_words("words4.json", [
    {"rank": 6001, "band": 7, "lemma": "dune", "uz_primary": "qum tepaligi",
     "example_en": "A dune of sand.", "example_uz": "(misol)"},
    {"rank": 6002, "band": 7, "lemma": "fjord", "uz_primary": "fyord",
     "uz_alt": ["tor ko'rfaz"], "example_en": "The fjord is cold.",
     "example_uz": "(misol)"}])
dd = SessionLocal()
r = WB.load_words(dd, P4)
dd.close()
ck("surilgan fayl: yangi yo'q, 2 to'qnashuv, 2 tarjima yangilandi",
   (r["inserted"], r["conflicts"], r["updated"], r["finished"]),
   (0, 2, 2, True))
ck("rank'lar bazadagidek (hech narsa o'chirilmadi/ko'chmadi)",
   (word("canyon").rank, word("dune").rank, word("fjord").rank),
   (6001, 6002, 6003))
ck("qotgan so'zning tarjimasi fayldan tushdi",
   (word("dune").uz_primary, json.loads(word("fjord").uz_alt)),
   ("qum tepaligi", ["tor ko'rfaz"]))

print("\n=== 17. YOZIB TOPISH: MISOLDAGI SHAKL HAM TO'G'RI (review) ===")
# 2026-10-16 (review): DESIGN §2 — lemma va misoldagi bo'shliq shakli
# qabul qilinadi ("She ____ in the park." -> "wandered" ham to'g'ri).
set_flag("all")
_today = roles.to_local(CLOCK["t"]).date()
dd = SessionLocal()
dd.add(models.WordbankWord(rank=8004, band=9, lemma="wander",
                           uz_primary="kezmoq", uz_alt="[]",
                           example_en="She wandered in the park.",
                           example_uz="(misol)", status="active"))
dd.commit()
WID["wander"] = dd.query(models.WordbankWord).filter_by(
    lemma="wander").first().id
LEMMA[WID["wander"]] = "wander"
dd.add(models.WordbankStudentWord(
    student_id=S1, word_id=WID["wander"], stage=2, known=0, has_prod=0,
    lapses=0, due=_today, last_move=_today - timedelta(days=3)))
dd.commit()
dd.close()
r = client.post("/api/wordbank/session", json={"size": 20}, headers=H1)
itW = [it for it in r.json()["items"] if lemma_of(it) == "wander"]
ckt("wander mashqda", itW)
itW = itW[0]
ck("P savoli, misoldagi shakl bo'shliq", (itW["mode"], itW["example"]),
   ("P", "She ____ in the park."))
r = answer(H1, r.json()["session_id"], itW, gap=5000, text_=" Wandered ")
ck("misoldagi shakl (wandered) — to'g'ri, tasdiqlandi",
   (r.json()["correct"], r.json()["known"]), (True, True))

print("\n" + ("BARCHASI OK" if not fails else f"XATOLAR: {fails}"))
sys.exit(1 if fails else 0)
