"""KOREYS TILI ISHLAMAYAPTI (2026-09-25).

Jahongir: "programmada JonyStudentappda muammo koreys tiliga
o'tmayabdi ekan".

Bayroqni koreys tiliga o'zgartirganda o'quvchi nimani ko'rishi kerak:
unitlar ro'yxati, lug'at o'yinlari, grammatika, diktant. Shu test
HAR BIRINI koreys tilida chaqirib ko'radi — qaysi biri sinishini
aniq ko'rsatadi. Inglizchasi bilan solishtiriladi, shunda "umuman
ishlamaydi" va "faqat koreyscha ishlamaydi" farqlanadi.
"""
import os, sys

os.environ["DATABASE_URL"] = "sqlite:////tmp/verify_ko/db.sqlite"
os.makedirs("/tmp/verify_ko", exist_ok=True)
if os.path.exists("/tmp/verify_ko/db.sqlite"):
    os.remove("/tmp/verify_ko/db.sqlite")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
import main, models, roles
import entry  # noqa: F401
from database import SessionLocal
from auth import hash_password

c = TestClient(main.app)
db = SessionLocal()
fails = []


def ck(n, g, w):
    ok = g == w
    print(("OK  " if ok else "XATO ") + f"{n}: {g}"
          + ("" if ok else f"   (kutilgan {w})"))
    if not ok:
        fails.append(n)


b = models.Branch(name="Zafar"); db.add(b); db.commit()
s = models.Student(full_name="Ali Valiyev", branch_id=b.id,
                   status="active", phone="998901112255",
                   public_id="STU-KO-1")
db.add(s); db.commit()
u = models.User(username="998901112255",
                password_hash=hash_password("jonyjony"),
                full_name="Ali Valiyev", role=roles.STUDENT,
                branch_id=b.id, is_active=1)
db.add(u); db.commit()
s.user_id = u.id; db.commit()
H = {"Authorization": "Bearer " + c.post(
    "/api/auth/login",
    json={"username": "998901112255", "password": "jonyjony"},
).json()["access_token"]}

print("=== 1. BAZADA KOREYS SO'ZLARI BORMI ===")
n_en = (db.query(models.VocabWord)
        .filter(models.VocabWord.language == "en").count())
n_ko = (db.query(models.VocabWord)
        .filter(models.VocabWord.language == "ko").count())
print(f"     en: {n_en} so'z,  ko: {n_ko} so'z")
ck("koreys so'zlari yuklangan", n_ko >= 1000, True)

# Darajasi bor koreys so'zlari (level filtri ishlashi uchun kerak)
ko_lvl = (db.query(models.VocabWord)
          .filter(models.VocabWord.language == "ko",
                  models.VocabWord.level.isnot(None)).count())
print(f"     ko so'zlardan darajasi bor: {ko_lvl}")

print("\n=== 2. UNITLAR RO'YXATI ===")
r = c.get("/api/student/vocab/units?language=en", headers=H)
ck("en unitlar status", r.status_code, 200)
en_units = r.json().get("units") or []
r = c.get("/api/student/vocab/units?language=ko", headers=H)
ck("ko unitlar status", r.status_code, 200)
ko_units = r.json().get("units") or []
print(f"     en unit: {len(en_units)},  ko unit: {len(ko_units)}")
ck("ko unitlar bo'sh emas", len(ko_units) > 0, True)

print("\n=== 3. LUG'AT O'YINLARI (har o'yin koreyschada) ===")
for game in roles.VOCAB_GAME_KEYS:
    r = c.get(f"/api/student/vocab/round?game={game}&language=ko",
              headers=H)
    ok = r.status_code == 200
    detail = "" if ok else f"  -> {r.status_code} {r.text[:90]}"
    ck(f"ko o'yin '{game}'", ok, True)
    if not ok:
        print("      " + detail)
    else:
        items = r.json().get("items") or []
        ck(f"ko o'yin '{game}' savol keldi", len(items) > 0, True)

print("\n=== 4. UNIT TANLANGANDA ===")
if ko_units:
    unit = ko_units[0]["key"]
    r = c.get(f"/api/student/vocab/round?game=en_uz&language=ko"
              f"&unit={unit}", headers=H)
    ck(f"ko unit '{unit}' bilan round", r.status_code, 200)
    if r.status_code != 200:
        print("      -> " + r.text[:200])

print("\n=== 5. GRAMMATIKA ===")
# Javob tuzilishi: {"language", "available", "a1": {"topics": [...]}, ...}
r = c.get("/api/student/grammar/topics?language=ko", headers=H)
ck("ko grammatika mavzulari status", r.status_code, 200)
ko_topics = []
if r.status_code == 200:
    body = r.json()
    ko_topics = (body.get("a1") or {}).get("topics") or []
    print(f"     ko: available={body.get('available')}, "
          f"A1 mavzu={len(ko_topics)}")
    ck("ko grammatika A1 mavzulari bor", len(ko_topics) > 0, True)
    ck("ko 'available' ro'yxatida A1 bor",
       "A1" in (body.get("available") or []), True)
    # Inglizchaning mavzulari koreyschaga aralashmasin
    ck("ko mavzu nomlari koreyscha (KO bilan boshlanadi)",
       all(str(t["topic"]).startswith("KO ") for t in ko_topics), True)

r = c.get("/api/student/grammar/topics?language=en", headers=H)
en_topics = ((r.json().get("a1") or {}).get("topics") or []
             if r.status_code == 200 else [])
print(f"     en: A1 mavzu={len(en_topics)}")
ck("en grammatika mavzulari bor", len(en_topics) > 0, True)

if ko_topics:
    t0 = ko_topics[0]["topic"]
    r = c.get("/api/student/grammar/round?language=ko"
              f"&topic={t0}", headers=H)
    ck(f"ko grammatika round ('{t0}')", r.status_code, 200)
    if r.status_code == 200:
        items = r.json().get("items") or []
        ck("ko grammatika savollari keldi", len(items) > 0, True)
    else:
        print("      -> " + r.text[:200])

print("\n=== 6. DIKTANT (listening) ===")
r = c.get("/api/student/practice/listening/round?language=ko",
          headers=H)
ck("ko diktant status", r.status_code, 200)
if r.status_code == 200:
    ck("ko diktant savol keldi",
       len(r.json().get("items") or []) > 0, True)
else:
    print("      -> " + r.text[:200])

print("\n=== 7. INGLIZCHA HALI HAM ISHLAYDI (regressiya) ===")
r = c.get("/api/student/vocab/round?game=en_uz&language=en", headers=H)
ck("en o'yin ishlaydi", r.status_code, 200)

print()
if fails:
    print(f"XATO: {len(fails)} ta tekshiruv o'tmadi")
    for f in fails:
        print("   - " + f)
    sys.exit(1)
print("HAMMASI O'TDI")
sys.exit(0)
