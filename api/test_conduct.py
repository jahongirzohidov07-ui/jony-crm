"""NA'MUNALI XODIM (2026-09-16) — Excel jadvali bilan bir xil hisobmi.

Namunaviy uch xodim "Na'munali xodim.xlsx" dan olingan, Excel'dagi
"qancha ayrildi" ustuni bilan solishtiriladi:
  Mavluda Kadirova        — 81 (beyjik: fevral 3, mart 7, aprel 12 marta)
  Sug'diyona Toshtemirova — 29 (kech kelish 6, beyjik 2, xayfsan 10)
  Sardor Mirzamuratov     — 10 (kech kelish 6, beyjik 1, xayfsan -1)"""
import os, sys, tempfile
from datetime import date, timedelta

_tmp = tempfile.mkdtemp(prefix="jony_conduct_")
os.environ["DATABASE_URL"] = "sqlite:///" + os.path.join(
    _tmp, "db.sqlite").replace("\\", "/")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
import main, models, roles
import entry  # noqa
from database import SessionLocal
from auth import hash_password

c = TestClient(main.app)
db = SessionLocal()
fails = []


def ck(n, g, w):
    ok = g == w
    print(("OK  " if ok else "XATO ") + f"{n}: {g}"
          + ("" if ok else f"  (kutilgan {w})"))
    if not ok:
        fails.append(n)


b = models.Branch(name="Zafar"); db.add(b); db.commit()


def mk(username, role, name=None):
    u = models.User(username=username, full_name=name or username.title(),
                    password_hash=hash_password("Parol123!"),
                    role=role, branch_id=b.id, is_active=1)
    db.add(u); db.commit()
    return u


def login(username):
    r = c.post("/api/auth/login",
               json={"username": username, "password": "Parol123!"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


founder = mk("asoschi", roles.FOUNDER)
hr = mk("hr", roles.HR_MANAGER)
hx = mk("boshliq", roles.HEAD_EXAMINER)
bm = mk("rahbar", roles.BRANCH_MANAGER)
mav = mk("mavluda", roles.ADMINISTRATOR, "Mavluda Kadirova")
sug = mk("sugdiyona", roles.TEACHER, "Sug'diyona Toshtemirova")
sar = mk("sardor", roles.SALES_MANAGER, "Sardor Mirzamuratov")
exm = mk("exam", roles.EXAMINER, "Sardor Examiner")
sup = mk("sup", roles.SUPPORT_TEACHER, "Sevinch Support")
hs = mk("supboshliq", roles.HEAD_SUPPORT)

H = login("hr")
Y = 2026


def add(u, kind, d, points=None, note=None, h=H):
    body = {"user_id": u.id, "kind": kind, "date": d}
    if points is not None:
        body["points"] = points
    if note is not None:
        body["note"] = note
    return c.post("/api/conduct", headers=h, json=body)


# --- Excel "setup" varag'idagi yozuvlar ---
for d in ["2026-02-09", "2026-02-17", "2026-02-25",
          "2026-03-06", "2026-03-23", "2026-03-24", "2026-03-26",
          "2026-03-27", "2026-03-30", "2026-03-31",
          "2026-04-09", "2026-04-13", "2026-04-14", "2026-04-15",
          "2026-04-16", "2026-04-17", "2026-04-18", "2026-04-22",
          "2026-04-25", "2026-04-27", "2026-04-29", "2026-04-30"]:
    ck(f"Mavluda {d}", add(mav, "badge", d).status_code, 200)

for d in ["2026-02-17", "2026-05-12", "2026-05-13", "2026-05-16",
          "2026-05-19", "2026-05-23"]:
    add(sug, "late", d)
add(sug, "badge", "2026-05-27")
add(sug, "badge", "2026-05-29")
r = add(sug, "reprimand", "2026-05-30", points=10, note="Xayfsan")
ck("xayfsan yozildi", r.status_code, 200)

for d in ["2026-01-09", "2026-01-17", "2026-02-13", "2026-03-11",
          "2026-03-12", "2026-03-31"]:
    add(sar, "late", d)
add(sar, "badge", "2026-03-30")
add(sar, "reprimand", "2026-01-05", points=-1, note="Rag'bat")


def board(section="staff", month=0, h=H):
    return c.get(f"/api/conduct?section={section}&year={Y}&month={month}",
                 headers=h)


print("\n=== EXCEL BILAN SOLISHTIRISH ===")
r = board()
ck("jadval 200", r.status_code, 200)
rows = {x["name"]: x for x in r.json()["rows"]}
ck("Mavluda ayrildi", rows["Mavluda Kadirova"]["year_minus"], 81)
ck("Mavluda qoldi", rows["Mavluda Kadirova"]["remaining"], 19)
ck("Sug'diyona ayrildi", rows["Sug'diyona Toshtemirova"]["year_minus"], 29)
ck("Sardor ayrildi", rows["Sardor Mirzamuratov"]["year_minus"], 10)

print("\n=== JAZO ===")
ck("Mavluda (xodim, 19) — xayfsan",
   rows["Mavluda Kadirova"]["sanction"]["text"], "Xayfsan beriladi")
ck("Sug'diyona (ustoz, 71) — jazo yo'q",
   rows["Sug'diyona Toshtemirova"]["sanction"], None)
ck("Sardor (90) — jazo yo'q", rows["Sardor Mirzamuratov"]["sanction"], None)
ck("eng past ball tepada", r.json()["rows"][0]["name"], "Mavluda Kadirova")

print("\n=== BO'LIMLAR ===")
names = {x["name"] for x in r.json()["rows"]}
ck("asoschi ro'yxatda yo'q", "Asoschi" in names, False)
ck("examiner xodimlarda yo'q", "Sardor Examiner" in names, False)
ck("support xodimlarda yo'q", "Sevinch Support" in names, False)
ck("HR xodimlarda bor", "Hr" in names, True)
ck("examiner o'z bo'limida",
   [x["name"] for x in board("examiner").json()["rows"]],
   ["Boshliq", "Sardor Examiner"])
ck("support o'z bo'limida",
   [x["name"] for x in board("support").json()["rows"]],
   ["Sevinch Support", "Supboshliq"])
ck("HR uchala bo'limni ko'radi",
   [s["key"] for s in r.json()["sections"]],
   ["staff", "support", "examiner"])

print("\n=== OY BO'YICHA JURNAL (kimga, qachon, qanday) ===")
r = board(month=4)
log = [e for e in r.json()["log"] if e["name"] == "Mavluda Kadirova"]
ck("aprelda 12 yozuv", len(log), 12)
last = log[0]
ck("oxirgisi 30-aprel", last["date"], "2026-04-30")
ck("12-marta", last["nth"], 12)
ck("5 ball (5-martadan keyin o'zgarmaydi)", last["points"], 5)
ck("turi", last["kind_label"], "Beyjik taqmaslik")
ck("kim yozdi", last["created_by"], "Hr")
ck("aprel minusi", {x["name"]: x for x in r.json()["rows"]}[
    "Mavluda Kadirova"]["period_minus"], 50)

print("\n=== YANGI YOZUV JAVOBI ===")
r = add(sar, "conflict_cause", "2026-06-01")
ck("ziddiyat sababchi 1-marta = 4", (r.json()["nth"], r.json()["points"]),
   (1, 4.0))
r = add(sar, "conflict_cause", "2026-06-02")
ck("2-marta = 6", r.json()["points"], 6.0)
cid = r.json()["id"]
r = add(sar, "conflict_part", "2026-06-02")
ck("qatnashchi alohida hisob: 1-marta = 2", r.json()["points"], 2.0)

print("\n=== O'CHIRSA QAYTA HISOBLANADI ===")
first_feb = [e for e in board(month=2).json()["log"]
             if e["name"] == "Mavluda Kadirova" and e["date"] == "2026-02-09"]
ck("delete 200", c.delete(f"/api/conduct/{first_feb[0]['id']}",
                          headers=H).status_code, 200)
rows = {x["name"]: x for x in board().json()["rows"]}
ck("fevral 1+2 bo'ldi: 81-6+3 = 78",
   rows["Mavluda Kadirova"]["year_minus"], 78)

print("\n=== XODIM TARIXI ===")
r = c.get(f"/api/conduct/user/{sar.id}?year={Y}", headers=H)
ck("tarix 200", r.status_code, 200)
ck("jami: 10 + 4 + 6 + 2", r.json()["year_minus"], 22)
ck("eng yangisi tepada", r.json()["items"][0]["date"], "2026-06-02")

print("\n=== TEKSHIRUVLAR ===")
ck("noma'lum tur", add(sar, "xyz", "2026-06-03").status_code, 400)
ck("kelajak sana",
   add(sar, "late", (date.today() + timedelta(days=2)).isoformat())
   .status_code, 400)
ck("xayfsan sababsiz", add(sar, "reprimand", "2026-06-03", points=3)
   .status_code, 400)
ck("xayfsan 0 ball", add(sar, "reprimand", "2026-06-03", points=0,
                         note="x").status_code, 400)
ck("asoschiga yozib bo'lmaydi", add(founder, "late", "2026-06-03")
   .status_code, 404)

print("\n=== RUXSATLAR ===")
# 2026-09-16, Jahongir: "examiner boshlig'i examinerlarni, support manager
# esa supportlarni jarima ball qo'shsin, o'zlarini esa HR baholasin"
ck("HR examinerga yozadi", add(exm, "late", "2026-06-03").status_code, 200)
ck("HR examinerlar boshlig'iga yozadi",
   add(hx, "late", "2026-06-03").status_code, 200)
ck("HR support rahbariga yozadi",
   add(hs, "late", "2026-06-03").status_code, 200)
for who in ("asoschi", "rahbar"):
    h = login(who)
    for sec in ("staff", "support", "examiner"):
        ck(f"{who} {sec} ko'rolmaydi", board(sec, h=h).status_code, 403)
    ck(f"{who} yozolmaydi", add(exm, "late", "2026-06-03", h=h)
       .status_code, 403)
    ck(f"{who} o'chirolmaydi",
       c.delete(f"/api/conduct/{cid}", headers=h).status_code, 403)
    ck(f"{who} tarixni ko'rolmaydi",
       c.get(f"/api/conduct/user/{sar.id}", headers=h).status_code, 403)

HX, HS = login("boshliq"), login("supboshliq")
r = board("examiner", h=HX)
ck("boshliq examinerlarni ko'radi", r.status_code, 200)
ck("boshliqqa faqat oddiy examinerlar (o'zi yo'q)",
   [x["name"] for x in r.json()["rows"]], ["Sardor Examiner"])
ck("boshliqqa faqat examiner bo'limi",
   [s["key"] for s in r.json()["sections"]], ["examiner"])
ck("boshliq import qilolmaydi (bayroq)", r.json()["can_import"], False)
ck("boshliq xodimlarni ko'rolmaydi", board("staff", h=HX).status_code, 403)
ck("boshliq supportlarni ko'rolmaydi",
   board("support", h=HX).status_code, 403)
r = add(exm, "badge", "2026-06-04", h=HX)
ck("boshliq examinerga yozadi", r.status_code, 200)
ck("boshliq o'z yozuvini o'chiradi",
   c.delete(f"/api/conduct/{r.json()['id']}", headers=HX).status_code, 200)
ck("boshliq o'ziga yozolmaydi", add(hx, "late", "2026-06-04", h=HX)
   .status_code, 403)
ck("boshliq xodimga yozolmaydi", add(sar, "late", "2026-06-04", h=HX)
   .status_code, 403)
ck("boshliq supportga yozolmaydi", add(sup, "late", "2026-06-04", h=HX)
   .status_code, 403)
ck("boshliq o'z tarixini ko'rolmaydi",
   c.get(f"/api/conduct/user/{hx.id}", headers=HX).status_code, 403)
ck("boshliq examiner tarixini ko'radi",
   c.get(f"/api/conduct/user/{exm.id}", headers=HX).status_code, 200)
ck("boshliq HR yozgan xodim yozuvini o'chirolmaydi",
   c.delete(f"/api/conduct/{cid}", headers=HX).status_code, 403)

hr_exm = add(exm, "manual", "2026-06-05").json()["id"]
ck("boshliq HR yozgan examiner yozuvini o'chirolmaydi",
   c.delete(f"/api/conduct/{hr_exm}", headers=HX).status_code, 403)
lg = {e["id"]: e for e in board("examiner", month=6, h=HX).json()["log"]}
ck("boshliqqa HR yozuvida o'chirish tugmasi yo'q",
   lg[hr_exm]["can_delete"], False)
ck("HR o'chiradi", c.delete(f"/api/conduct/{hr_exm}", headers=H)
   .status_code, 200)

r = board("support", h=HS)
ck("support rahbari supportlarni ko'radi",
   [x["name"] for x in r.json()["rows"]], ["Sevinch Support"])
ck("support rahbari supportga yozadi",
   add(sup, "manual", "2026-06-04", h=HS).status_code, 200)
ck("support rahbari o'ziga yozolmaydi",
   add(hs, "manual", "2026-06-04", h=HS).status_code, 403)
ck("support rahbari examinerga yozolmaydi",
   add(exm, "manual", "2026-06-04", h=HS).status_code, 403)
ck("support rahbari examinerlarni ko'rolmaydi",
   board("examiner", h=HS).status_code, 403)
r = c.post("/api/conduct/import", headers=HS, json={"items": []})
ck("support rahbari import qilolmaydi", r.status_code, 403)
ck("HR bo'limida rahbarlar ko'rinadi",
   sorted(x["name"] for x in board("support").json()["rows"]),
   ["Sevinch Support", "Supboshliq"])

print("\n=== EXCEL IMPORT ===")
items = [
    {"name": "Irina  Tuzikova ", "kind": "late", "date": "2026-02-02"},
    {"name": "Irina Tuzikova", "kind": "late", "date": "2026-02-03"},
    {"name": "Irina Tuzikova", "kind": "reprimand", "date": "2026-01-01",
     "points": 5},
    {"name": "Sarvar mob", "kind": "badge", "date": "2026-02-02"},
    {"name": "Noma'lum Odam", "kind": "badge", "date": "2026-02-02"},
]
irina = mk("irina", roles.ADMINISTRATOR, "Irina Tuzikova")
sarvar = mk("sarvar", roles.ADMINISTRATOR, "Sarvar mobilograf")
r = c.post("/api/conduct/import", headers=H, json={"items": items})
ck("oldindan ko'rish 200", r.status_code, 200)
st = {n["name"]: n["status"] for n in r.json()["names"]}
ck("bo'shliqlar farq qilmaydi", st["Irina Tuzikova"], "matched")
ck("qisqa ism topilmaydi", st["Sarvar mob"], "unmatched")
ck("qo'shiladi (hali saqlanmagan)", (r.json()["to_add"], r.json()["added"]),
   (3, 0))
ck("saqlanmadi", c.get(f"/api/conduct/user/{irina.id}?year={Y}",
                       headers=H).json()["items"], [])
mp = {"Sarvar mob": sarvar.id, "Noma'lum Odam": 0}
r = c.post("/api/conduct/import", headers=H,
           json={"items": items, "mapping": mp, "apply": True})
ck("import 200", r.status_code, 200)
ck("4 ta qo'shildi", r.json()["added"], 4)
st = {n["name"]: n["status"] for n in r.json()["names"]}
ck("qo'lda moslandi", st["Sarvar mob"], "mapped")
ck("o'tkazib yuborildi", st["Noma'lum Odam"], "skipped")
h = c.get(f"/api/conduct/user/{irina.id}?year={Y}", headers=H).json()
ck("Irina: 1 + 2 + xayfsan 5", h["year_minus"], 8)
ck("import belgisi", h["items"][0]["note"], "Excel'dan import")
r = c.post("/api/conduct/import", headers=H,
           json={"items": items, "mapping": mp, "apply": True})
ck("qayta import takrorlamaydi", (r.json()["added"], r.json()["already"]),
   (0, 4))
r = c.post("/api/conduct/import", headers=H, json={"items": [
    {"name": "Irina Tuzikova", "kind": "late",
     "date": (date.today() + timedelta(days=3)).isoformat()}]})
ck("kelajak sana rad", r.status_code, 400)

print()
if fails:
    print("XATOLAR:", fails)
    sys.exit(1)
print("HAMMASI O'TDI")
