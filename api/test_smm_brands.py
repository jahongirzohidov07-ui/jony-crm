"""SMM BRENDLARI (2026-10-17).

Jahongir: "SMM bo'limida aynan Marhaboni profilida faqat bitta proyekt
emas u Jony School va Jahongir Zoxidovning shaxsiy brend profilini ham
yurgizadi". Asoschi tanlovi: "Brendlar ro'yxati, kontent bo'yicha".
Tekshiriladi:
  0. 0036_smm_brands migratsiyasi: eski bazada contents.brand_id va
     indeks qo'shiladi, qayta ishlasa xato bermaydi, ma'lumot qoladi;
  1. seed: uchta brend bir marta (ikkinchi yurish hech narsani
     o'zgartirmaydi), brendsiz kontent -> Jony Academy, Marhabo (SMM
     menejer, "Marhabo Mamatqulova") uchala brendga a'zo; boshqa rolli
     "Marhabo" va boshqa SMM menejer — a'zo emas; Marhabo yo'q bo'lsa
     log (faqat xabar, ism yo'q); hech narsa o'chirilmaydi;
  2. GET /api/smm/brands: SMM menejerda "mine" = uchala brend; SMM
     ruxsati yo'q — 403; tokensiz — 401; asoschida "managers";
  3. POST/PUT brendlar va PUT a'zolar: SMM menejer — 403, asoschi va
     filial rahbari — OK; noto'g'ri nom/tur — 400; noma'lum brend — 404;
     SMM bo'lmagan xodim a'zo — 400; Jony Academy nofaol bo'lmaydi;
     audit yozuvlari bor, xato so'rov audit yozmaydi;
  4. kontent: brend berilmasa (yoki null) — Jony Academy; noma'lum yoki
     nofaol brend — 400; SMM menejer brendni almashtira oladi (tarixda
     nomi bilan); hozirgi nofaol brend qayta yuborilsa — OK;
  5. GET /api/content?brand_id va /api/smm/plan?brand_id filtrlaydi
     (Jony Academy tanlansa brendsiz kontent ham chiqadi); javoblarda
     brand_id va brand_name;
  6-8. review tuzatishlari (2026-10-17): Excel import tanlangan brendga
     yoziladi, dubl tekshiruvi brend ichida, nofaol/noma'lum brend — 400;
     nofaol brenddagi post nusxasi/varianti — Jony Academy, variant
     asosiy post brendida; qo'shimcha lavozimdagi (user_roles) SMM
     menejer ham biriktiriladi va seed uni topadi; nofaol xodim
     yangidan biriktirilmaydi, hozirgi nofaol a'zo qoladi;
  9. tarmoqqa birorta ham chaqiruv yo'q.

Ishga tushirish: PYTHONIOENCODING=utf-8 python test_smm_brands.py
"""
import contextlib
import io
import os
import socket
import sys
from datetime import date as _date

os.environ["DATABASE_URL"] = "sqlite:////tmp/verify_smm_brands/db.sqlite"
os.makedirs("/tmp/verify_smm_brands", exist_ok=True)
if os.path.exists("/tmp/verify_smm_brands/db.sqlite"):
    os.remove("/tmp/verify_smm_brands/db.sqlite")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402
import main, models, roles  # noqa: E402,F401
import entry  # noqa: E402,F401 - jonli yo'llar va yamoqlar
import common  # noqa: E402
import migrations  # noqa: E402
import smm_brands as SB  # noqa: E402
from auth import hash_password  # noqa: E402
from database import SessionLocal  # noqa: E402

# TARMOQ TAQIQLANGAN: test davomida tashqariga ulanish urinishi sanaladi.
# Loopback ruxsat (Windows'da asyncio socketpair() 127.0.0.1 ga ulanadi).
_NET = []
_real_connect = socket.socket.connect
_LOOP = ("127.0.0.1", "::1", "localhost")


def _no_net(self, addr):
    if isinstance(addr, tuple) and addr and addr[0] in _LOOP:
        return _real_connect(self, addr)
    _NET.append(addr)
    raise OSError("test: tarmoq taqiqlangan")


socket.socket.connect = _no_net

client = TestClient(main.app)
fails = []


def ck(name, got, want):
    ok = got == want
    print(("OK  " if ok else "XATO ") + f"{name}: {got}"
          + ("" if ok else f"   (kutilgan {want})"))
    if not ok:
        fails.append(name)


db = SessionLocal()


def cols(table):
    return [r[1] for r in db.execute(text(f"PRAGMA table_info({table})"))]


def idx(table):
    return [r[1] for r in db.execute(text(f"PRAGMA index_list({table})"))]


def counts():
    db.expire_all()
    return (db.query(models.SmmBrand).count(),
            db.query(models.SmmBrandMember).count(),
            db.query(models.Content).count())


print("=== 0. MIGRATSIYA 0036_smm_brands ===")
ck("oxirgi migratsiya", migrations.MIGRATIONS[-1][0], "0036_smm_brands")
ck("shtampda 0036", "0036_smm_brands" in common.SCHEMA_STAMP, True)
ck("yangi baza: contents.brand_id bor", "brand_id" in cols("contents"), True)
ck("yangi baza: jadvallar bor",
   [t for t in ("smm_brands", "smm_brand_members")
    if not db.execute(text("SELECT name FROM sqlite_master WHERE "
                           "type='table' AND name=:n"), {"n": t}).first()],
   [])
# Eski (jonli) bazani taqlid qilamiz: alohida faylda brand_id'siz
# contents jadvali, 0034 gacha hammasi qo'llangan. SQLite FK ustunini
# DROP qila olmaydi — shuning uchun asosiy bazada emas.
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import Session as _S  # noqa: E402
_OLD = "/tmp/verify_smm_brands/old.sqlite"
if os.path.exists(_OLD):
    os.remove(_OLD)
eng_old = create_engine("sqlite:///" + _OLD)
models.SchemaMigration.__table__.create(eng_old)
models.ErrorLog.__table__.create(eng_old)
with eng_old.begin() as cx:
    cx.execute(text("CREATE TABLE contents (id INTEGER PRIMARY KEY, "
                    "title VARCHAR NOT NULL, status VARCHAR)"))
    cx.execute(text("INSERT INTO contents (title, status) "
                    "VALUES ('Eski post 0', 'idea')"))
with _S(eng_old) as dbo:
    for v, _st in migrations.MIGRATIONS[:-1]:
        dbo.add(models.SchemaMigration(version=v))
    dbo.commit()

    def ocols():
        return [r[1] for r in dbo.execute(
            text("PRAGMA table_info(contents)"))]
    ck("taqlid: ustun yo'q", "brand_id" in ocols(), False)
    ck("0036 xatosiz qo'llandi", migrations.run(dbo),
       [("0036_smm_brands", None)])
    ck("ustun qo'shildi", "brand_id" in ocols(), True)
    ck("indeks bor", "ix_contents_brand_id" in [
        r[1] for r in dbo.execute(text("PRAGMA index_list(contents)"))],
       True)
    ck("eski kontent saqlandi, brendsiz (NULL)",
       [tuple(r) for r in dbo.execute(
           text("SELECT title, brand_id FROM contents"))],
       [("Eski post 0", None)])
    dbo.execute(text("DELETE FROM schema_migrations "
                     "WHERE version = '0036_smm_brands'"))
    dbo.commit()
    ck("qayta ishlasa ham xatosiz (duplicate column o'tadi)",
       migrations.run(dbo), [("0036_smm_brands", None)])
    ck("xato jurnali bo'sh", dbo.query(models.ErrorLog).count(), 0)
eng_old.dispose()

print("\n=== 1. SEED ===")
ck("start seedi belgilangan", common._seed_done(db, SB.SEED_KEY), True)
ck("startda uchta brend",
   sorted(c for (c,) in db.query(models.SmmBrand.code).all()),
   ["academy", "personal", "school"])
ck("belgi bor — start seedi qayta yurmaydi", SB.seed_startup(db), None)
# Toza holatdan: brendlar yo'q, Marhabo yo'q
db.execute(text("DELETE FROM smm_brands"))
db.commit()
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    r0 = SB.seed_smm_brands(db)
ck("Marhabo yo'q: brendlar qo'shildi, a'zo yo'q", r0,
   {"brands_created": 3, "contents_backfilled": 0, "members_added": 0,
    "marhabo": 0})
ck("log — faqat xabar", buf.getvalue().strip(),
   "[smm-brands] Marhabo topilmadi")
B = {b.code: b for b in db.query(models.SmmBrand).all()}
ck("nomlar", [(B[c].name, B[c].kind, B[c].is_active)
              for c in ("academy", "school", "personal")],
   [("Jony Academy", "academy", 1), ("Jony School", "school", 1),
    ("Jahongir Zoxidov — shaxsiy brend", "personal", 1)])
ACAD, SCH, PERS = B["academy"].id, B["school"].id, B["personal"].id


def mk_user(uname, role, name, active=1):
    u = models.User(username=uname, full_name=name,
                    password_hash=hash_password("Parol123!"), role=role,
                    branch_id=None, is_active=active)
    db.add(u)
    db.commit()
    return u.id


U_MAR = mk_user("marhabo", roles.SMM_MANAGER, "Marhabo Mamatqulova")
U_DIL = mk_user("dilnoza", roles.SMM_MANAGER, "Dilnoza SMM")
U_TCH = mk_user("mteach", roles.TEACHER, "Marhabo Ustoz")
U_FND = mk_user("boss", roles.FOUNDER, "Asoschi")
U_BM = mk_user("bm", roles.BRANCH_MANAGER, "Filial Rahbari")
U_SH = mk_user("sh", roles.SALES_HEAD, "Sotuv Rahbari")
for i in range(3):
    db.add(models.Content(title=f"Eski post {i + 1}", status="idea"))
db.commit()

before = counts()
r1 = SB.seed_smm_brands(db)
ck("1-yurish: kontentlar Academy'ga, Marhabo uchala brendga", r1,
   {"brands_created": 0, "contents_backfilled": 3, "members_added": 3,
    "marhabo": 1})
ck("brendsiz kontent qolmadi",
   db.query(models.Content).filter(models.Content.brand_id.is_(None))
   .count(), 0)
ck("hammasi Jony Academy",
   {c.brand_id for c in db.query(models.Content).all()}, {ACAD})
mem = sorted((b, u) for b, u in db.query(models.SmmBrandMember.brand_id,
                                         models.SmmBrandMember.user_id))
ck("a'zolar — faqat Marhabo (SMM), ustoz Marhabo va Dilnoza emas", mem,
   sorted([(ACAD, U_MAR), (SCH, U_MAR), (PERS, U_MAR)]))
mid = counts()
r2 = SB.seed_smm_brands(db)
ck("2-yurish hech narsa o'zgartirmaydi", r2,
   {"brands_created": 0, "contents_backfilled": 0, "members_added": 0,
    "marhabo": 1})
ck("sonlar o'zgarmadi (brend, a'zo, kontent)", counts(), mid)
ck("hech narsa o'chmadi", (mid[0] >= before[0], mid[2] == before[2]),
   (True, True))


def H(uname):
    r = client.post("/api/auth/login",
                    json={"username": uname, "password": "Parol123!"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


HM, HD, HT, HF, HB, HS = (H("marhabo"), H("dilnoza"), H("mteach"),
                          H("boss"), H("bm"), H("sh"))

print("\n=== 2. GET /api/smm/brands ===")
r = client.get("/api/smm/brands", headers=HM)
ck("SMM menejer — 200", r.status_code, 200)
d = r.json()
ck("mine — uchala brend", sorted(d["mine"]), sorted([ACAD, SCH, PERS]))
ck("javob kalitlari", sorted(d["brands"][0].keys()),
   sorted(["id", "code", "name", "kind", "is_active", "note", "members",
           "mine", "content_count"]))
ck("brendlar tartibi va mine",
   [(b["code"], b["mine"], b["is_active"]) for b in d["brands"]],
   [("academy", True, True), ("school", True, True),
    ("personal", True, True)])
ck("a'zo — Marhabo", d["brands"][1]["members"],
   [{"id": U_MAR, "name": "Marhabo Mamatqulova"}])
ck("kontent soni", [b["content_count"] for b in d["brands"]], [3, 0, 0])
ck("SMM menejerga xodimlar ro'yxati berilmaydi", d.get("managers"), [])
ck("Dilnoza — mine bo'sh",
   client.get("/api/smm/brands", headers=HD).json()["mine"], [])
ck("sotuv rahbari (SMM ruxsati bor) — 200",
   client.get("/api/smm/brands", headers=HS).status_code, 200)
ck("ustoz — 403", client.get("/api/smm/brands", headers=HT).status_code, 403)
ck("tokensiz — 401", client.get("/api/smm/brands").status_code, 401)
df = client.get("/api/smm/brands", headers=HF).json()
ck("asoschi — mine bo'sh", df["mine"], [])
ck("asoschiga SMM menejerlar (ustoz yo'q)",
   sorted(x["id"] for x in df["managers"]), sorted([U_MAR, U_DIL]))

print("\n=== 3. BREND YARATISH / O'ZGARTIRISH / A'ZOLAR ===")
n_audit = db.query(models.AuditLog).filter(
    models.AuditLog.entity == "smm_brand").count()
ck("SMM menejer brend yarata olmaydi — 403",
   client.post("/api/smm/brands", json={"name": "Jony Kids"},
               headers=HM).status_code, 403)
ck("ustoz — 403",
   client.post("/api/smm/brands", json={"name": "Jony Kids"},
               headers=HT).status_code, 403)
for bad, why in (({"name": "x"}, "qisqa nom"), ({"name": "a" * 81}, "uzun"),
                 ({"name": 12}, "son"), ({}, "nomsiz"),
                 ({"name": "Jony Kids", "kind": "shop"}, "tur"),
                 ({"name": "  jony academy "}, "takror nom")):
    ck(f"400 — {why}", client.post("/api/smm/brands", json=bad,
                                   headers=HF).status_code, 400)
ck("xato so'rovlar audit yozmadi",
   db.query(models.AuditLog).filter(
       models.AuditLog.entity == "smm_brand").count(), n_audit)
r = client.post("/api/smm/brands", json={"name": "  Jony   Kids "},
                headers=HF)
ck("asoschi yaratdi — 200", r.status_code, 200)
KIDS = r.json()
ck("yangi brend", (KIDS["name"], KIDS["code"], KIDS["kind"],
                   KIDS["is_active"], KIDS["members"], KIDS["mine"]),
   ("Jony Kids", "jony-kids", "brand", True, [], False))
r = client.post("/api/smm/brands", json={"name": "Мактаб", "kind": "school"},
                headers=HB)
ck("filial rahbari ham yaratadi; kirill nom — kod 'brend'",
   (r.status_code, r.json().get("code"), r.json().get("kind")),
   (200, "brend", "school"))
r = client.post("/api/smm/brands", json={"name": "Jony-Kids"}, headers=HF)
ck("slug takrorlanmaydi", r.json().get("code"), "jony-kids-2")
KIDS2 = r.json()["id"]

ck("SMM menejer nomni o'zgartira olmaydi — 403",
   client.put(f"/api/smm/brands/{KIDS['id']}", json={"name": "X brend"},
              headers=HM).status_code, 403)
ck("noma'lum brend — 404",
   client.put("/api/smm/brands/99999", json={"name": "Yangi nom"},
              headers=HF).status_code, 404)
ck("juda katta id — 404",
   client.put(f"/api/smm/brands/{10 ** 15}", json={"name": "Yangi nom"},
              headers=HF).status_code, 404)
ck("boshqa brend nomi — 400",
   client.put(f"/api/smm/brands/{KIDS['id']}", json={"name": "Jony School"},
              headers=HF).status_code, 400)
r = client.put(f"/api/smm/brands/{KIDS['id']}", json={"name": "Jony Kids Club"},
               headers=HF)
ck("nom o'zgardi, kod o'zgarmadi",
   (r.status_code, r.json()["name"], r.json()["code"]),
   (200, "Jony Kids Club", "jony-kids"))
ck("is_active noto'g'ri — 400",
   client.put(f"/api/smm/brands/{SCH}", json={"is_active": "ha"},
              headers=HF).status_code, 400)
ck("Jony Academy nofaol bo'lmaydi — 400",
   client.put(f"/api/smm/brands/{ACAD}", json={"is_active": False},
              headers=HF).status_code, 400)
r = client.put(f"/api/smm/brands/{KIDS2}", json={"is_active": False},
               headers=HF)
ck("nofaol qilindi", (r.status_code, r.json()["is_active"]), (200, False))
lst = client.get("/api/smm/brands", headers=HM).json()["brands"]
ck("nofaol brend ro'yxatda is_active=false",
   [b["is_active"] for b in lst if b["id"] == KIDS2], [False])

MU = f"/api/smm/brands/{PERS}/members"
ck("SMM menejer a'zolarni o'zgartira olmaydi — 403",
   client.put(MU, json={"user_ids": [U_MAR]}, headers=HM).status_code, 403)
r = client.put(MU, json={"user_ids": [U_MAR, U_TCH]}, headers=HF)
ck("ustoz a'zo bo'lmaydi — 400", (r.status_code, r.json().get("detail")),
   (400, "Faqat SMM menejerlarni biriktirish mumkin"))
r = client.put(MU, json={"user_ids": [U_FND]}, headers=HF)
ck("asoschi ham — 400", r.status_code, 400)
ck("yo'q xodim — 400",
   client.put(MU, json={"user_ids": [987654]}, headers=HF).status_code, 400)
ck("ro'yxat emas — 400",
   client.put(MU, json={"user_ids": U_MAR}, headers=HF).status_code, 400)
ck("son emas — 400",
   client.put(MU, json={"user_ids": ["1"]}, headers=HF).status_code, 400)
ck("noma'lum brend — 404",
   client.put("/api/smm/brands/99999/members", json={"user_ids": [U_MAR]},
              headers=HF).status_code, 404)
ck("xato so'rov a'zolarni o'zgartirmadi",
   [u for (u,) in db.query(models.SmmBrandMember.user_id)
    .filter(models.SmmBrandMember.brand_id == PERS)], [U_MAR])
r = client.put(MU, json={"user_ids": [U_DIL, U_DIL]}, headers=HB)
ck("almashtirish: Dilnoza kirdi, Marhabo chiqdi",
   (r.status_code, [m["id"] for m in r.json()["members"]]), (200, [U_DIL]))
dm = client.get("/api/smm/brands", headers=HM).json()
ck("Marhaboda shaxsiy brend endi yo'q", sorted(dm["mine"]),
   sorted([ACAD, SCH]))
r = client.put(MU, json={"user_ids": [U_MAR, U_DIL]}, headers=HF)
ck("ikkalasi", sorted(m["id"] for m in r.json()["members"]),
   sorted([U_MAR, U_DIL]))
r = client.put(f"/api/smm/brands/{KIDS['id']}/members",
               json={"user_ids": []}, headers=HF)
ck("bo'sh ro'yxat — 200", (r.status_code, r.json()["members"]), (200, []))
aud = {(a.action, a.field) for a in db.query(models.AuditLog)
       .filter(models.AuditLog.entity == "smm_brand").all()}
ck("audit: yaratish, nom, faollik, a'zolar",
   sorted(aud), sorted({("create", "name"), ("update", "name"),
                        ("update", "is_active"), ("update", "members")}))
am = (db.query(models.AuditLog)
      .filter(models.AuditLog.entity == "smm_brand",
              models.AuditLog.field == "members",
              models.AuditLog.entity_id == PERS)
      .order_by(models.AuditLog.id).all())
ck("a'zolar auditi (eski -> yangi)",
   [(a.old_value, a.new_value, a.user_name) for a in am],
   [("Marhabo Mamatqulova", "Dilnoza SMM", "Filial Rahbari"),
    ("Dilnoza SMM", "Dilnoza SMM, Marhabo Mamatqulova", "Asoschi")])
ck("o'zgarmagan a'zolar audit yozmaydi",
   (client.put(MU, json={"user_ids": [U_DIL, U_MAR]},
               headers=HF).status_code,
    db.query(models.AuditLog).filter(
        models.AuditLog.entity == "smm_brand",
        models.AuditLog.field == "members").count()),
   (200, 2))

print("\n=== 4. KONTENT BRENDI ===")
r = client.post("/api/content", json={"title": "Yangi post"}, headers=HM)
ck("brend berilmasa — Jony Academy",
   (r.status_code, r.json().get("brand_id"), r.json().get("brand_name")),
   (200, ACAD, "Jony Academy"))
C1 = r.json()["id"]
ck("bazada ham Academy", db.get(models.Content, C1).brand_id, ACAD)
r = client.post("/api/content", json={"title": "Null", "brand_id": None},
                headers=HM)
ck("null — Jony Academy", r.json().get("brand_id"), ACAD)
r = client.post("/api/content", json={"title": "Shaxsiy",
                                      "brand_id": PERS}, headers=HM)
ck("shaxsiy brend",
   (r.status_code, r.json().get("brand_id"), r.json().get("brand_name")),
   (200, PERS, "Jahongir Zoxidov — shaxsiy brend"))
C_P = r.json()["id"]
r = client.post("/api/content", json={"title": "Maktab",
                                      "brand_id": SCH}, headers=HM)
C_S = r.json()["id"]
nc = db.query(models.Content).count()
for bid, why in ((99999, "noma'lum"), (KIDS2, "nofaol"), (10 ** 15, "katta"),
                 (0, "nol")):
    ck(f"yaratish: {why} brend — 400",
       client.post("/api/content", json={"title": "Xato",
                                         "brand_id": bid},
                   headers=HM).status_code, 400)
ck("xato so'rovlar kontent yaratmadi", db.query(models.Content).count(), nc)
ck("ustoz kontent yarata olmaydi — 403",
   client.post("/api/content", json={"title": "U"}, headers=HT).status_code,
   403)

r = client.put(f"/api/content/{C1}", json={"brand_id": SCH}, headers=HM)
ck("SMM menejer brendni almashtirdi",
   (r.status_code, r.json().get("brand_id"), r.json().get("brand_name")),
   (200, SCH, "Jony School"))
v = (db.query(models.ContentVersion)
     .filter(models.ContentVersion.content_id == C1,
             models.ContentVersion.field == "brand").all())
ck("tarixda nomi bilan", [(x.old_value, x.new_value, x.changed_by)
                          for x in v],
   [("Jony Academy", "Jony School", "Marhabo Mamatqulova")])
ck("noma'lum brend — 400",
   client.put(f"/api/content/{C1}", json={"brand_id": 99999},
              headers=HM).status_code, 400)
ck("nofaol brend — 400",
   client.put(f"/api/content/{C1}", json={"brand_id": KIDS2},
              headers=HM).status_code, 400)
ck("xatodan keyin brend o'zgarmadi", db.get(models.Content, C1).brand_id,
   SCH)
# Brend keyin nofaol qilinsa — eski postni tahrirlash to'xtamasin
client.put(f"/api/smm/brands/{SCH}", json={"is_active": False}, headers=HF)
r = client.put(f"/api/content/{C1}", json={"brand_id": SCH,
                                           "title": "Yangi post 2"},
               headers=HM)
ck("hozirgi nofaol brend qayta yuborildi — 200",
   (r.status_code, r.json().get("brand_id"), r.json().get("title")),
   (200, SCH, "Yangi post 2"))
ck("nofaol brendga yangi kontent — 400",
   client.post("/api/content", json={"title": "Y", "brand_id": SCH},
               headers=HM).status_code, 400)
client.put(f"/api/smm/brands/{SCH}", json={"is_active": True}, headers=HF)
r = client.put(f"/api/content/{C1}", json={"brand_id": None}, headers=HM)
ck("null — Jony Academy'ga qaytdi", r.json().get("brand_id"), ACAD)
r = client.put(f"/api/content/{C1}", json={"title": "Faqat nom"}, headers=HM)
ck("brend yuborilmasa o'zgarmaydi", r.json().get("brand_id"), ACAD)
ck("brend o'zgarmasa tarix yozilmaydi",
   db.query(models.ContentVersion).filter(
       models.ContentVersion.content_id == C1,
       models.ContentVersion.field == "brand").count(), 2)
r = client.post(f"/api/content/{C_P}/copy", json={}, headers=HM)
ck("nusxa o'sha brendda", (r.status_code, r.json().get("brand_id")),
   (200, PERS))
C_COPY = r.json()["id"]

print("\n=== 5. FILTR ===")
# Exceldan/Instagram'dan kelgan brendsiz kontent — Jony Academy
db.add(models.Content(title="Brendsiz (import)", status="idea"))
db.commit()
C_NULL = db.query(models.Content).filter(
    models.Content.title == "Brendsiz (import)").first().id


def titles(path, h=HM):
    r = client.get(path, headers=h)
    return r.status_code, sorted(x["title"] for x in r.json()["rows"])


ALL = sorted(c.title for c in db.query(models.Content).all())
ck("filtrsiz — hammasi", titles("/api/content"), (200, ALL))
ck("Academy — brendsiz ham",
   titles(f"/api/content?brand_id={ACAD}"),
   (200, sorted(["Eski post 1", "Eski post 2", "Eski post 3", "Faqat nom",
                 "Null", "Brendsiz (import)"])))
ck("shaxsiy", titles(f"/api/content?brand_id={PERS}"),
   (200, ["Shaxsiy", "Shaxsiy (nusxa)"]))
ck("maktab", titles(f"/api/content?brand_id={SCH}"), (200, ["Maktab"]))
ck("noma'lum brend — bo'sh", titles("/api/content?brand_id=99999"),
   (200, []))
ck("juda katta — bo'sh", titles(f"/api/content?brand_id={10 ** 15}"),
   (200, []))
rows = client.get(f"/api/content?brand_id={ACAD}", headers=HM).json()["rows"]
ck("brendsiz qator javobda Jony Academy",
   [(x["brand_id"], x["brand_name"]) for x in rows if x["id"] == C_NULL],
   [(ACAD, "Jony Academy")])
g = client.get(f"/api/content/{C_P}", headers=HM).json()
ck("bitta kontent javobida brend", (g["brand_id"], g["brand_name"]),
   (PERS, "Jahongir Zoxidov — shaxsiy brend"))
ck("kontent-plan: shaxsiy",
   titles(f"/api/smm/plan?brand_id={PERS}", HF),
   (200, ["Shaxsiy", "Shaxsiy (nusxa)"]))
pr = client.get(f"/api/smm/plan?brand_id={ACAD}", headers=HM).json()["rows"]
ck("kontent-plan qatorida brend",
   sorted({(x["brand_id"], x["brand_name"]) for x in pr}),
   [(ACAD, "Jony Academy")])
ck("kontent-plan: filtrsiz hammasi",
   titles("/api/smm/plan", HM), (200, ALL))
dash = client.get("/api/smm/dashboard", headers=HM)
ck("SMM dashboard ishlaydi", dash.status_code, 200)
d2 = client.get("/api/smm/brands", headers=HM).json()
ck("kontent soni (Academy'da brendsiz ham)",
   {b["code"]: b["content_count"] for b in d2["brands"]
    if b["code"] in ("academy", "school", "personal")},
   {"academy": 6, "school": 1, "personal": 2})
ck("a'zolik kontent ko'rinishini o'zgartirmaydi (Dilnoza hammasini ko'radi)",
   titles("/api/content", HD), (200, ALL))

print("\n=== 6. EXCEL IMPORT BREND BILAN (review, 2026-10-17) ===")
IMP = "/api/smm/plan/import"
ROWS_IMP = [{"Sana": "2026-11-05", "Mavzu": "Maktab reja A"},
            {"Sana": "2026-11-06", "Mavzu": "Umumiy mavzu"}]
# Academy'da xuddi shu sana+mavzuli post bor — boshqa brend rejasini
# "allaqachon bor" qilib o'tkazib yubormasligi kerak
db.add(models.Content(title="Umumiy mavzu", planned_date=_date(2026, 11, 6),
                      status="idea", brand_id=ACAD))
db.commit()


def imp(brand=..., dry=True, h=HM):
    body = {"year": 2026, "month": 11, "rows": ROWS_IMP, "dry_run": dry}
    if brand is not ...:
        body["brand_id"] = brand
    return client.post(IMP, json=body, headers=h)


r = imp(SCH)
ck("ko'rib chiqish: maktab — ikkalasi qo'shiladi (dubl brend ichida)",
   (r.status_code, r.json().get("will_add"), r.json().get("skipped"),
    r.json().get("brand_id")), (200, 2, 0, SCH))
r = imp()
ck("brend berilmasa — Academy, umumiy mavzu dubl",
   (r.status_code, r.json().get("will_add"), r.json().get("skipped"),
    r.json().get("brand_id")), (200, 1, 1, ACAD))
nc = db.query(models.Content).count()
for bid, why in ((99999, "noma'lum"), (KIDS2, "nofaol"), ("2", "matn")):
    ck(f"import: {why} brend — 400", imp(bid, dry=False).status_code, 400)
ck("xato import kontent yaratmadi", db.query(models.Content).count(), nc)
r = imp(SCH, dry=False)
ck("import: maktabga qo'shildi", (r.status_code, r.json().get("added")),
   (200, 2))
db.expire_all()
ck("import qatorlari maktab brendida",
   sorted((c.title, c.brand_id) for c in db.query(models.Content)
          .filter(models.Content.planned_date >= _date(2026, 11, 1)).all()),
   sorted([("Maktab reja A", SCH), ("Umumiy mavzu", SCH),
           ("Umumiy mavzu", ACAD)]))
ck("filtr: maktab tanlansa import ko'rinadi",
   titles(f"/api/content?brand_id={SCH}&date_from=2026-11-01"
          "&date_to=2026-11-30"),
   (200, ["Maktab reja A", "Umumiy mavzu"]))
ck("filtr: Academy'da maktab rejasi yo'q",
   titles(f"/api/content?brand_id={ACAD}&date_from=2026-11-01"
          "&date_to=2026-11-30"),
   (200, ["Umumiy mavzu"]))
r = imp(SCH, dry=False)
ck("qayta import — hammasi dubl", (r.json().get("added"),
                                    r.json().get("skipped")), (0, 2))

print("\n=== 7. NUSXA VA VARIANT BRENDI (review, 2026-10-17) ===")
r = client.post("/api/content", json={"title": "Kids post",
                                      "brand_id": KIDS["id"]}, headers=HM)
C_K = r.json()["id"]
client.put(f"/api/smm/brands/{KIDS['id']}", json={"is_active": False},
           headers=HF)
r = client.post(f"/api/content/{C_K}/copy", json={}, headers=HM)
ck("nofaol brenddagi post nusxasi — Jony Academy",
   (r.status_code, r.json().get("brand_id")), (200, ACAD))
r = client.post(f"/api/content/{C_P}/copy", json={}, headers=HM)
ck("faol brenddagi nusxa — o'sha brend", r.json().get("brand_id"), PERS)
r = client.post("/api/content", json={"title": "Variant",
                                      "parent_id": C_P}, headers=HM)
ck("variant asosiy post brendida", (r.status_code, r.json().get("brand_id")),
   (200, PERS))
r = client.post("/api/content", json={"title": "Variant 2", "parent_id": C_P,
                                      "brand_id": None}, headers=HM)
ck("variant: brend aniq null — Academy", r.json().get("brand_id"), ACAD)
r = client.post("/api/content", json={"title": "Variant 3", "parent_id": C_P,
                                      "brand_id": SCH}, headers=HM)
ck("variant: brend aniq berilsa — o'shasi", r.json().get("brand_id"), SCH)
r = client.post("/api/content", json={"title": "Variant 4",
                                      "parent_id": C_K}, headers=HM)
ck("nofaol brenddagi postning varianti — Academy",
   r.json().get("brand_id"), ACAD)

print("\n=== 8. QO'SHIMCHA LAVOZIMDAGI VA NOFAOL SMM (review) ===")
U_EX = mk_user("marx", roles.TEACHER, "Marxabo Qo'shimcha")
db.add(models.UserRole(user_id=U_EX, role=roles.SMM_MANAGER))
db.commit()
df = client.get("/api/smm/brands", headers=HF).json()
ck("qo'shimcha lavozimdagi SMM — asoschi ro'yxatida",
   U_EX in [x["id"] for x in df["managers"]], True)
ck("ustoz (SMM emas) ro'yxatda yo'q",
   U_TCH in [x["id"] for x in df["managers"]], False)
MS = f"/api/smm/brands/{SCH}/members"
r = client.put(MS, json={"user_ids": [U_MAR, U_EX]}, headers=HF)
ck("qo'shimcha lavozimdagi SMM biriktiriladi",
   (r.status_code, sorted(m["id"] for m in r.json()["members"])),
   (200, sorted([U_MAR, U_EX])))
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    r3 = SB.seed_smm_brands(db)
ck("seed qo'shimcha lavozimdagi Marhabo'ni ham topadi (2 ta, 2 a'zolik)",
   (r3["marhabo"], r3["members_added"]), (2, 2))
HX = H("marx")
r = client.get("/api/smm/brands",
               headers={**HX, "X-Active-Role": roles.SMM_MANAGER})
ck("X-Active-Role bilan — mine uchala brend",
   (r.status_code, sorted(r.json().get("mine", []))),
   (200, sorted([ACAD, SCH, PERS])))
U_OLD = mk_user("oldsmm", roles.SMM_MANAGER, "Ketgan SMM", active=0)
r = client.put(MS, json={"user_ids": [U_MAR, U_EX, U_OLD]}, headers=HF)
ck("nofaol xodim yangidan biriktirilmaydi — 400", r.status_code, 400)
ck("a'zolar o'zgarmadi",
   sorted(u for (u,) in db.query(models.SmmBrandMember.user_id)
          .filter(models.SmmBrandMember.brand_id == SCH)),
   sorted([U_MAR, U_EX]))
db.get(models.User, U_EX).is_active = 0
db.commit()
r = client.put(MS, json={"user_ids": [U_EX]}, headers=HF)
ck("hozirgi a'zo nofaol bo'lsa ham qoladi (tahrir to'xtamaydi)",
   (r.status_code, [m["id"] for m in r.json()["members"]]), (200, [U_EX]))
db.get(models.User, U_EX).is_active = 1
db.commit()

print("\n=== 9. TARMOQ ===")
ck("tarmoqqa ulanish urinishi yo'q", _NET, [])

socket.socket.connect = _real_connect
db.close()
print("\n" + ("BARCHASI OK" if not fails else f"XATOLAR: {len(fails)}"))
for f_ in fails:
    print("  -", f_)
sys.exit(1 if fails else 0)
