"""DARS O'YINLARI — chop etiladigan o'yinlar, 2026-09-28.

Jahongir: "ielts 1.0-4.0 gacha bo'lgan dars rejalari ichiga xar xil
oyinli activitylar qoshib ber mavzuga doir. Keyin uni pdf qilib yuklab
chiqarib oynash mumkin bo'lsin"; "dars rejasiga qosh hamma pdf li
oyinlarni har bir darsga".

A. Har darsda 8 ta asosiy turning hammasi + avtomat Bingo va Memory.
B. Har darsning hamma o'yinlari bitta PDF bo'lib quriladi (xatosiz).
C. API: ro'yxat, bitta o'yin PDF, hammasi PDF, ruxsatlar.
D. Tekshiruvchi (check_game) xato kontentni ushlaydi.
"""
import copy
import os
import sys
import tempfile
import time

_DIR = os.path.join(tempfile.gettempdir(), "plan_games_test")
os.makedirs(_DIR, exist_ok=True)
_DB = os.path.join(_DIR, "db.sqlite")
os.environ["DATABASE_URL"] = "sqlite:///" + _DB.replace(chr(92), "/")
if os.path.exists(_DB):
    os.remove(_DB)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient          # noqa: E402
import main, models, roles                         # noqa: E402,F401
import entry                                       # noqa: E402,F401
import plan_games as P                             # noqa: E402
from liveplay import _load_course                  # noqa: E402
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


# ============================================================ A
print("=== A. HAR DARSDA HAMMA O'YINLAR ===")
COUNTS = {"ielts_1_0": 28, "ielts_2_0": 25, "ielts_3_0": 26, "ielts_4_0": 25}
bad_lessons, missing = [], []
for course, n in COUNTS.items():
    lessons = _load_course(course)["lessons"]
    ck(f"{course}: {n} dars", len(lessons), n)
    authored = P._load_games(course)
    for L in lessons:
        games = authored.get(str(L["no"]))
        if not games:
            missing.append(f"{course}:{L['no']}")
            continue
        errs = P.check_lesson(games)
        if errs:
            bad_lessons.append((f"{course}:{L['no']}", errs[:3]))
ck("hamma 104 darsda mualliflik o'yinlari bor", missing, [])
ck("hamma darslar tekshiruvdan o'tadi (8 tur, chegaralar)", bad_lessons, [])

L = _load_course("ielts_2_0")["lessons"][6]
G = P.lesson_games("ielts_2_0", L)
types = [g["type"] for g in G]
ck("dars o'yinlari: 8 asosiy tur + bingo + memory",
   all(t in types for t in P.CORE_TYPES) and "bingo" in types and types.count("memory") >= 1, True)
ck("avtomat o'yinlar oxirida va belgilangan",
   [g["id"] for g in G if g.get("auto")], ["bingo", "memory_vocab"])
ck("har o'yinda nomi, kerakli narsalar va qoidalar",
   all(g["type_uz"] and g["kit"] and len(g["rules"]) >= 3 for g in G), True)
bingo = next(g for g in G if g["id"] == "bingo")
ck("Bingo lug'atdan: 24 so'z (CORE 20 + STRONG 4)", len(bingo["data"]["words"]), 24)
mem = next(g for g in G if g["id"] == "memory_vocab")
ck("Memory: 12 juft, har safar bir xil (urug')",
   (len(mem["data"]["pairs"]), mem["data"]["pairs"] == P.lesson_games("ielts_2_0", L)[-1]["data"]["pairs"]),
   (12, True))
ck("lesson_games manba faylni o'zgartirmaydi (nusxa)",
   "auto" in P._load_games("ielts_2_0")["7"][0], False)

# ============================================================ B
print("\n=== B. HAR DARS PDF'I QURILADI ===")
t0 = time.time()
pdf_err, pages_min = [], 10 ** 9
for course in COUNTS:
    for L in _load_course(course)["lessons"]:
        try:
            pdf = P.build_games_pdf(course, L, P.lesson_games(course, L))
            if pdf[:4] != b"%PDF":
                pdf_err.append(f"{course}:{L['no']} PDF emas")
            pages_min = min(pages_min, pdf.count(b"/Type /Page\n") or pdf.count(b"/Type /Page"))
        except Exception as ex:                    # noqa: BLE001
            pdf_err.append(f"{course}:{L['no']} {type(ex).__name__}: {ex}")
print(f"   104 dars PDF: {time.time() - t0:.1f} s")
ck("104 darsning hammasi PDF bo'ladi", pdf_err, [])
ck("har PDF'da kamida 20 sahifa (10 o'yin: ustoz + material)", pages_min >= 20, True)

# ============================================================ C
print("\n=== C. API ===")
db = SessionLocal()
b1 = models.Branch(name="Bekobod 1")
db.add(b1)
db.commit()
for un, role in (("ustoz", roles.TEACHER), ("hr", roles.HR_MANAGER), ("asos", roles.FOUNDER)):
    db.add(models.User(username=un, password_hash=hash_password("x"), full_name=un.title(),
                       role=role, branch_id=b1.id))
db.commit()
db.close()


def tok(u):
    return {"Authorization": "Bearer " + c.post(
        "/api/auth/login", json={"username": u, "password": "x"}).json()["access_token"]}


T = tok("ustoz")
r = c.get("/api/plans/ielts_1_0/5/games", headers=T)
ck("ro'yxat 200", r.status_code, 200)
g = r.json()["games"]
ck("1.0 5-dars: 10 ta o'yin (8 + bingo + memory)", len(g) >= 10, True)
ck("ro'yxatda turi o'zbekcha va data bor", all(x["type_uz"] and x["data"] for x in g), True)
one = g[0]["id"]
rp = c.get(f"/api/plans/ielts_1_0/5/games.pdf?id={one}", headers=T)
ck("bitta o'yin PDF", (rp.status_code, rp.headers.get("content-type"), rp.content[:4] == b"%PDF"),
   (200, "application/pdf", True))
ck("fayl nomi o'yin id si bilan", one in rp.headers.get("content-disposition", ""), True)
ra = c.get("/api/plans/ielts_1_0/5/games.pdf", headers=T)
ck("hammasi bitta PDF, bittasidan katta",
   (ra.status_code, ra.content[:4] == b"%PDF", len(ra.content) > len(rp.content)), (200, True, True))
ck("bo'lmagan o'yin — 404", c.get("/api/plans/ielts_1_0/5/games.pdf?id=yoq", headers=T).status_code, 404)
ck("bo'lmagan dars — 404", c.get("/api/plans/ielts_1_0/99/games", headers=T).status_code, 404)
ck("IELTS 5.0 da o'yin yo'q — 404", c.get("/api/plans/ielts_5_0/1/games", headers=T).status_code, 404)
ck("HR ga yopiq", c.get("/api/plans/ielts_1_0/5/games", headers=tok("hr")).status_code, 403)
ck("PDF HR ga yopiq", c.get("/api/plans/ielts_1_0/5/games.pdf", headers=tok("hr")).status_code, 403)
ck("tokensiz yopiq", c.get("/api/plans/ielts_1_0/5/games").status_code in (401, 403), True)
ck("asoschiga ochiq", c.get("/api/plans/ielts_4_0/25/games", headers=tok("asos")).status_code, 200)
# Darslar ro'yxatida "N o'yin" belgisi (2026-09-28, "qani oyinlar chiqmadiku")
lv = {x["course"]: x for x in c.get("/api/plans", headers=T).json()}
ck("ro'yxatda har 1.0-4.0 darsida kamida 10 o'yin (ba'zida +memory = 11)",
   min(l.get("games") or 0 for c_ in P.COURSES for l in lv[c_]["lessons"]) >= 10, True)
ck("o'yin soni /games bilan bir xil",
   lv["ielts_1_0"]["lessons"][4]["games"], len(c.get("/api/plans/ielts_1_0/5/games", headers=T).json()["games"]))

# ============================================================ D
print("\n=== D. TEKSHIRUVCHI XATONI USHLAYDI ===")
base = copy.deepcopy(P._load_games("ielts_2_0")["7"])
by = {x["type"]: x for x in base}


def errs_of(mut):
    x = copy.deepcopy(by[mut[0]])
    mut[1](x)
    return P.check_game(x)


ck("to'g'ri o'yin — xatosiz", [P.check_game(x) for x in base], [[] for _ in base])
ck("auction: xato ulushi 40-60% dan tashqari",
   any("ulushi" in e for e in errs_of(("auction", lambda x: [it.update(ok=True) for it in x["data"]["items"]]))), True)
ck("auction: xato gapning fix'i yo'q",
   any("fix" in e for e in errs_of(("auction", lambda x: next(
       it for it in x["data"]["items"] if not it["ok"]).pop("fix")))), True)
ck("board: 24 katak shart",
   any("24" in e for e in errs_of(("board", lambda x: x["data"]["squares"].pop()))), True)
ck("dominoes: takroriy qism",
   any("takrorlanmasin" in e for e in errs_of(("dominoes", lambda x: x["data"]["pairs"].append(
       list(x["data"]["pairs"][0]))))), True)
ck("taboo: 3 ta taqiqlangan so'z shart",
   any("aynan 3" in e for e in errs_of(("taboo", lambda x: x["data"]["cards"][0]["taboo"].pop()))), True)
ck("scramble: juda uzun gap",
   any("so'z" in e for e in errs_of(("scramble", lambda x: x["data"]["sentences"].__setitem__(
       0, " ".join(["word"] * 16) + ".")))), True)
ck("quiz: 4 bo'lim shart",
   any("4 ta" in e for e in errs_of(("quiz_board", lambda x: x["data"]["categories"].pop()))), True)
ck("matn chegarasi (karta sig'masin)",
   any("juda uzun" in e for e in errs_of(("speaking_cards", lambda x: x["data"]["cards"].__setitem__(
       0, "x" * 200)))), True)
ck("noma'lum tur", "noma'lum" in " ".join(P.check_game(dict(by["taboo"], type="kahoot"))), True)
ck("daqiqa 5..30", any("minutes" in e for e in P.check_game(dict(by["taboo"], minutes=45))), True)
ck("darsda tur yetishmasa — xato",
   any("yetishmaydi" in e for e in P.check_lesson([x for x in base if x["type"] != "taboo"])), True)
ck("band id (bingo) ishlatilsa — xato",
   any("band" in e for e in P.check_lesson(base + [dict(by["taboo"], id="bingo", type="memory",
                                                       data={"pairs": [["a", "b"]] * 12})])), True)
from reportlab.pdfbase.pdfmetrics import stringWidth   # noqa: E402
p = P._fit("<b>rosy-cheeked</b>", 50, 60, size=10, bold=True)
ck("uzun so'z katakka sig'adi (defisda bo'linadi, harflab emas)",
   all(stringWidth(w, "DV-B", p.style.fontSize) <= 50 for w in ("rosy-", "cheeked")), True)

print(f"\nJAMI XATO: {len(fails)} {fails[:8]}")
sys.exit(1 if fails else 0)
