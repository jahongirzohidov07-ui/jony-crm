"""LUG'AT BANKI — "So'z bilish" SERTIFIKATLARI testlari (2026-10-17,
3-bosqich; shartnoma PHASE23_CONTRACT.md §6, OWNER D3–D4).

Tekshiriladi:
  * bayroq o'chiq -> o'quvchi va xodim yo'llari 404 (noto'g'ri tana
    bilan ham — 422 emas);
  * fayl turi faqat sehrli baytlardan: .png deb nomlangan .exe va
    matn fayli — 415; bo'sh / yo'q fayl — 400; 3 MB dan katta — 413;
  * natija qoidalari imtihon turi bo'yicha (IELTS, Multilevel, SAT,
    Duolingo, TOEFL, Cambridge, TOPIK, Goethe, TORFL, boshqa) va
    yorliqni server yasaydi;
  * test sanasi kelajakda / 5 yildan eski — 400;
  * cheklovlar: 3 ta kutilayotgan, 30 kunda 10 ta — 429;
  * bir xil fayl: o'zida kutilayotgan / tasdiqlangan bo'lsa 409, rad
    etilgandan keyin mumkin; boshqa o'quvchida — qabul, navbatda
    ogohlantirish;
  * KO'RINISH MATRITSASI: kutilayotgan ball yuklash javobida, o'z
    ro'yxatida, bildirishnomada, /me da, reytingda, ota-ona
    sahifasida va ustoz ro'yxatida YO'Q;
  * chegara: boshqa guruh ustozi / boshqa filial administratori
    ro'yxatda ko'rmaydi, begona filtr — 403, begona id (fayl,
    tasdiq) — 404 (shartnoma: borligi ham bilinmasin);
  * tasdiq: aynan bitta Certificate + bitta audit + SMM vazifasi,
    ikkinchi tasdiq 409; xodim tuzatgan qiymat (eskisi emas) belgiga
    chiqadi; rad etish — sabab majburiy; bekor qilish — Certificate
    o'chadi, belgi yo'qoladi;
  * fayl javobi sarlavhalari (nosniff, CSP sandbox, inline, no-store);
  * o'quvchi butunlay o'chirilsa ham yuklama qoladi, tasdiqlash 409.
Tarix (wordbank_hall) tarkibi bu yerda TEKSHIRILMAYDI — u "social"
qismining testida (shartnoma §7).

Ishga tushirish: PYTHONIOENCODING=utf-8 python test_wordbank_certs.py
"""
import json
import os
import sys
from datetime import date, datetime, timedelta

os.environ["DATABASE_URL"] = "sqlite:////tmp/verify_wordbank_certs/db.sqlite"
os.makedirs("/tmp/verify_wordbank_certs", exist_ok=True)
if os.path.exists("/tmp/verify_wordbank_certs/db.sqlite"):
    os.remove("/tmp/verify_wordbank_certs/db.sqlite")
os.environ["WORDBANK_WORDS_FILE"] = "/tmp/verify_wordbank_certs/yoq.json"
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import HTTPException  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
import main, models, roles  # noqa: E402,F401
import entry  # noqa: E402,F401 - jonli yo'llar (ota-ona sahifasi, push)
import wordbank as WB  # noqa: E402,F401
import wordbank_certs as WCERT  # noqa: E402
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


# ---- Soxta soat (entry-monkeypatch-pitfall: sys.modules bo'ylab) ----
CLOCK = {"t": datetime(2026, 10, 17, 5, 0, 0)}       # Toshkent 10:00


def _fake_now():
    return CLOCK["t"]


for _m in list(sys.modules.values()):
    if (getattr(_m, "__file__", "") or "").endswith("wordbank.py") \
            and hasattr(_m, "_now"):
        _m._now = _fake_now

# ---- Bildirishnomalar yozib olinadi (haqiqiy push yuborilmaydi) ----
PUSHES = []
P = sys.modules.get("push")
ckt("push moduli yuklangan (entry.py)", P is not None)


def _fake_send(db, user_ids, title, body, url="/student", tag=None):
    PUSHES.append({"users": sorted(int(u) for u in user_ids or []),
                   "title": title, "body": body, "url": url})
    return 0


if P is not None:
    P.send_to_users = _fake_send

# ------------------------------------------------------------ ma'lumot ---
db = SessionLocal()
bA = models.Branch(name="Pilot filial")
bB = models.Branch(name="Boshqa filial")
db.add_all([bA, bB])
db.commit()


def mk_user(uname, role, branch, name=None):
    u = models.User(username=uname, full_name=name or uname.title(),
                    password_hash=hash_password("Parol123!"), role=role,
                    branch_id=branch.id if branch else None, is_active=1)
    db.add(u)
    db.commit()
    return u


def mk_teacher(uname, branch, name):
    u = mk_user(uname, roles.TEACHER, branch, name)
    t = models.Teacher(full_name=name, branch_id=branch.id, is_active=1,
                       user_id=u.id)
    db.add(t)
    db.commit()
    return u, t


def mk_group(name, branch, teacher):
    g = models.Group(name=name, branch_id=branch.id, teacher_id=teacher.id,
                     lesson_price=40_000)
    db.add(g)
    db.commit()
    return g


uTA, tA = mk_teacher("certta", bA, "Ustoz Anvar")
uTB, tB = mk_teacher("certtb", bB, "Ustoz Botir")
gA = mk_group("IELTS 6.0", bA, tA)
gB = mk_group("Boshqa guruh", bB, tB)


def mk_student(name, uname, branch, group, tag):
    u = mk_user(uname, roles.STUDENT, branch, name)
    s = models.Student(full_name=name, branch_id=branch.id, status="active",
                       enrolled_date=date(2026, 9, 1),
                       public_id=f"STU-CERT-{tag}", user_id=u.id,
                       group_id=group.id,
                       parent_token=f"tok-cert-{tag}-" + "z" * 12)
    db.add(s)
    db.commit()
    db.add(models.StudentGroupLink(student_id=s.id, group_id=group.id,
                                   is_primary=1, active=1))
    db.commit()
    return s


s1 = mk_student("Ali Vositov", "cert1", bA, gA, "1")
s2 = mk_student("Malika Yusupova", "cert2", bA, gA, "2")
s3 = mk_student("Boshqa Filialdagi", "cert3", bB, gB, "3")
s4 = mk_student("Limit Sinovchi", "cert4", bA, gA, "4")
s5 = mk_student("O'chiriladigan Bola", "cert5", bA, gA, "5")
s6 = mk_student("Qo'riqchi Oxirgi", "cert6", bA, gA, "6")   # rowid qayta ishlatilmasin
S1, S2, S3, S4, S5 = s1.id, s2.id, s3.id, s4.id, s5.id
TOK1 = s1.parent_token

mk_user("certboss", roles.FOUNDER, bA)
mk_user("certadmA", roles.ADMINISTRATOR, bA)        # A filial administratori
mk_user("certadmB", roles.SALES_MANAGER, bB)        # B filial "Administrator"
mk_user("certbm", roles.BRANCH_MANAGER, bA)
mk_user("certhead", roles.ACADEMIC_HEAD, None)
mk_user("certacc", roles.ACCOUNTANT, bA)

# s1 ga bir nechta tasdiqlangan so'z — reytingda qatori bo'lsin
for i, lemma in enumerate(("time", "people", "year")):
    w = models.WordbankWord(rank=i + 1, band=1, lemma=lemma,
                            uz_primary=lemma + "-uz", uz_alt="[]",
                            example_en="x", example_uz="x", status="active")
    db.add(w)
    db.flush()
    db.add(models.WordbankStudentWord(
        student_id=S1, word_id=w.id, stage=5, due=date(2026, 11, 1),
        has_prod=1, known=1, lapses=0, last_move=CLOCK["t"],
        known_at=CLOCK["t"] - timedelta(days=1)))
db.commit()


def H(uname):
    r = client.post("/api/auth/login",
                    json={"username": uname, "password": "Parol123!"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


H1, H2, H3, H4, H5 = (H("cert1"), H("cert2"), H("cert3"), H("cert4"),
                      H("cert5"))
HTA, HTB, HF = H("certta"), H("certtb"), H("certboss")
HADA, HADB, HBM, HAH, HACC = (H("certadmA"), H("certadmB"), H("certbm"),
                              H("certhead"), H("certacc"))


def set_flag(value):
    d = SessionLocal()
    row = d.query(models.IntegrationSetting).get("wordbank_branches")
    if row is None:
        row = models.IntegrationSetting(key="wordbank_branches")
        d.add(row)
    row.value = value
    d.commit()
    d.close()


PNG_HEAD = b"\x89PNG\r\n\x1a\n"


def png(tag):
    return PNG_HEAD + tag.encode() + b"0" * 100


def jpg(tag):
    return b"\xff\xd8\xff\xe0" + tag.encode() + b"1" * 100


def pdf(tag):
    return b"%PDF-1.4\n" + tag.encode() + b"\n%%EOF\n"


def webp(tag):
    return b"RIFF\x24\x00\x00\x00WEBPVP8 " + tag.encode() + b"2" * 50


def up(h, content, fname="sert.png", mime="image/png", **fields):
    data = {"exam_type": "ielts", "score": "7.0", "test_date": "2026-09-20"}
    data.update({k: v for k, v in fields.items() if v is not None})
    for k in [k for k, v in fields.items() if v is None]:
        data.pop(k, None)
    files = {"file": (fname, content, mime)} if content is not None else None
    return client.post("/api/wordbank/certs/mine", headers=h, data=data,
                       files=files)


def staff_list(h, **params):
    q = "&".join(f"{k}={v}" for k, v in params.items())
    return client.get("/api/wordbank/certs" + (f"?{q}" if q else ""),
                      headers=h)


def ids_of(r):
    return [x["id"] for x in r.json().get("items", [])] \
        if r.status_code == 200 else None


SCORE = "8.5"
LABEL = "IELTS 8.5"


def _leaves(o):
    if isinstance(o, dict):
        for v in o.values():
            yield from _leaves(v)
    elif isinstance(o, list):
        for v in o:
            yield from _leaves(v)
    else:
        yield o


def _is_score(x):
    if isinstance(x, bool):
        return False
    if isinstance(x, (int, float)):
        return abs(float(x) - 8.5) < 1e-9
    return isinstance(x, str) and x.strip() in (SCORE, "8,5")


def no_score(name, obj):
    """Kutilayotgan ball (8.5) / yorliq ("IELTS 8.5") hech qayerda yo'q:
    matnda yorliq, JSON barglarida 8.5 qiymati. (Ota-ona sahifasidagi
    "~8.5-9.0" kabi doimiy jadval matni ball emas — u bargda butun
    qiymat sifatida 8.5 emas.)"""
    if isinstance(obj, str):
        try:
            obj = json.loads(obj)
        except ValueError:
            ckt(name, LABEL not in obj and SCORE not in obj)
            return
    s = json.dumps(obj, ensure_ascii=False)
    ckt(name, LABEL not in s and not any(_is_score(x)
                                         for x in _leaves(obj)))


def rows(model, **flt):
    d = SessionLocal()
    out = d.query(model).filter_by(**flt).all()
    for x in out:
        d.expunge(x)
    d.close()
    return out


print("=== 0. SXEMA ===")
ck("roles: VOCAB_CERT_CONFIRM da ustoz va SALES_MANAGER bor",
   (roles.TEACHER in roles.VOCAB_CERT_CONFIRM,
    roles.SALES_MANAGER in roles.VOCAB_CERT_CONFIRM), (True, True))
ck("roles: ustoz bekor qila olmaydi",
   roles.TEACHER in roles.VOCAB_CERT_REVOKE, False)

print("\n=== 1. BAYROQ O'CHIQ — 404 ===")
for meth, path in (("get", "/api/wordbank/certs/mine"),
                   ("post", "/api/wordbank/certs/mine"),
                   ("delete", "/api/wordbank/certs/mine/1"),
                   ("get", "/api/wordbank/certs/mine/1/file")):
    r = getattr(client, meth)(path, headers=H1)
    ck(f"o'chiq: {meth.upper()} {path}", r.status_code, 404)
r = client.post("/api/wordbank/certs/mine", headers=H1,
                data={"exam_type": "yoq"})
ck("o'chiq: noto'g'ri tana bilan ham 404 (422 emas)", r.status_code, 404)
# 2026-10-17 (review): darvoza tana tahlilidan OLDIN — buzuq multipart
# (boundary yo'q) ham 404, 400 emas
r = client.post("/api/wordbank/certs/mine",
                headers={**H1, "Content-Type": "multipart/form-data"},
                content=b"--x\r\nbuzuq")
ck("o'chiq: buzuq multipart ham 404", r.status_code, 404)
for meth, path in (("get", "/api/wordbank/certs"),
                   ("get", "/api/wordbank/certs/count"),
                   ("get", "/api/wordbank/certs/1/file"),
                   ("post", "/api/wordbank/certs/1/confirm"),
                   ("post", "/api/wordbank/certs/1/reject"),
                   ("post", "/api/wordbank/certs/1/revoke")):
    r = getattr(client, meth)(path, headers=HF)
    ck(f"o'chiq: xodim {meth.upper()} {path}", r.status_code, 404)

set_flag("all")

print("\n=== 2. FAYL TURI VA HAJMI ===")
r = up({}, png("tokensiz"))
ck("tokensiz yuklash — 401 (tana o'qilmaydi)", r.status_code, 401)
r = up(H1, b"MZ\x90\x00\x03\x00\x00\x00" + b"\x00" * 200, fname="rasm.png")
ck(".png deb nomlangan .exe — 415", r.status_code, 415)
ck("415 matni", r.json().get("detail"),
   "Faqat rasm (JPG, PNG, WEBP) yoki PDF yuklang")
r = up(H1, b"Bu oddiy matn fayli, sertifikat emas", fname="a.pdf",
       mime="application/pdf")
ck("matn fayli (.pdf nomi bilan) — 415", r.status_code, 415)
r = up(H1, b"<svg xmlns='http://www.w3.org/2000/svg'></svg>",
       fname="a.svg", mime="image/svg+xml")
ck("SVG — 415", r.status_code, 415)
r = up(H1, None)
ck("fayl yo'q — 400", r.status_code, 400)
r = up(H1, b"", fname="bo'sh.png")
ck("bo'sh fayl — 400", r.status_code, 400)
r = up(H1, PNG_HEAD + b"x" * WCERT.MAX_BYTES, fname="katta.png")
ck("3 MB dan katta — 413", r.status_code, 413)
ck("413 matni", r.json().get("detail"), "Fayl juda katta — 3 MB dan oshmasin")
r = client.post("/api/wordbank/certs/mine",
                headers={**H1, "Content-Type":
                         "multipart/form-data; boundary=xyz"},
                content=b"0" * (WCERT.MAX_BYTES + WCERT.FORM_MARGIN + 1))
ck("Content-Length juda katta — tana o'qilmasdan 413", r.status_code, 413)
r = client.post("/api/wordbank/certs/mine",
                headers={**H1, "Content-Type": "multipart/form-data"},
                content=b"--x\r\nbuzuq")
ck("buzuq multipart — o'zbekcha 400",
   (r.status_code, (r.json().get("detail") or "").startswith("Fayl yuborilmadi")),
   (400, True))
r = up(H1, png("tur-xato"), exam_type="yoq")
ck("noma'lum imtihon turi — 400", r.status_code, 400)
r = up(H1, png("sana-yoq"), test_date=None)
ck("test sanasi yo'q — 400", r.status_code, 400)
r = up(H1, png("sana-kelajak"), test_date="2026-10-18")
ck("test sanasi kelajakda — 400", r.status_code, 400)
r = up(H1, png("sana-eski"), test_date="2021-10-16")
ck("test sanasi 5 yildan eski — 400", r.status_code, 400)
ck("hali hech narsa saqlanmadi", len(rows(models.WordbankCertUpload)), 0)

print("\n=== 3. NATIJA QOIDALARI (server yorlig'i) ===")


def label(**kw):
    try:
        return WCERT.validate_result(**kw)["result_label"]
    except HTTPException as e:
        return e.status_code


ck("ielts 7", label(exam_type="ielts", score="7"), "IELTS 7.0")
ck("ielts 7,5 (vergul)", label(exam_type="ielts", score="7,5"), "IELTS 7.5")
ck("ielts 9.5 — 400", label(exam_type="ielts", score="9.5"), 400)
ck("ielts 7.25 — 400", label(exam_type="ielts", score="7.25"), 400)
ck("ielts ball yo'q — 400", label(exam_type="ielts"), 400)
ck("ielts NaN — 400", label(exam_type="ielts", score="nan"), 400)
ck("ielts bo'limlari noto'g'ri — 400",
   label(exam_type="ielts", score="7", sub_scores='{"L": 9.5}'), 400)
ck("ielts noma'lum bo'lim — 400",
   label(exam_type="ielts", score="7", sub_scores='{"X": 7}'), 400)
ck("ielts bo'limlar JSON emas — 400",
   label(exam_type="ielts", score="7", sub_scores="L=7"), 400)
ck("ielts bo'limlar saqlanadi (tartib L,R,W,S)",
   WCERT.validate_result(exam_type="ielts", score="7",
                         sub_scores='{"s": 6.5, "L": 8}')["sub_scores"],
   json.dumps({"L": 8.0, "S": 6.5}))
ck("multilevel", label(exam_type="multilevel", level="b2", score="58"),
   "Multilevel B2 (58)")
ck("multilevel 76 — 400",
   label(exam_type="multilevel", level="B2", score="76"), 400)
ck("multilevel 58.5 — 400",
   label(exam_type="multilevel", level="B2", score="58.5"), 400)
ck("multilevel D1 — 400",
   label(exam_type="multilevel", level="D1", score="50"), 400)
ck("cefr_other nomsiz", label(exam_type="cefr_other", level="C1"), "CEFR C1")
ck("cefr_other nomi bilan",
   label(exam_type="cefr_other", level="B2", exam_name="Aptis"), "Aptis B2")
ck("cefr_other nomi 41 belgi — 400",
   label(exam_type="cefr_other", level="B2", exam_name="x" * 41), 400)
ck("sat", label(exam_type="sat", score="1350"), "SAT 1350")
ck("sat 1355 — 400", label(exam_type="sat", score="1355"), 400)
ck("sat 390 — 400", label(exam_type="sat", score="390"), 400)
ck("duolingo", label(exam_type="duolingo", score="125"), "Duolingo 125")
ck("duolingo 127 — 400", label(exam_type="duolingo", score="127"), 400)
ck("toefl", label(exam_type="toefl", score="95"), "TOEFL 95")
ck("toefl 121 — 400", label(exam_type="toefl", score="121"), 400)
ck("cambridge", label(exam_type="cambridge", exam_name="b2 first",
                      score="176"), "Cambridge B2 First (176)")
ck("cambridge noma'lum imtihon — 400",
   label(exam_type="cambridge", exam_name="B3 Second", score="176"), 400)
ck("cambridge 231 — 400",
   label(exam_type="cambridge", exam_name="C1 Advanced", score="231"), 400)
ck("topik", label(exam_type="topik", level="4"), "TOPIK 4")
ck("topik 7 — 400", label(exam_type="topik", level="7"), 400)
ck("goethe", label(exam_type="goethe", level="B1"), "Goethe B1")
ck("torfl", label(exam_type="torfl", level="a2"), "TORFL A2")
ck("other", label(exam_type="other", exam_name="HSK", level="4-daraja"),
   "HSK 4-daraja")
ck("other nomsiz — 400", label(exam_type="other", level="4"), 400)
ck("other natija 21 belgi — 400",
   label(exam_type="other", exam_name="HSK", level="x" * 21), 400)
ck("sertifikat raqami 41 belgi — 400",
   label(exam_type="sat", score="1200", cert_no="9" * 41), 400)
v = WCERT.validate_result(exam_type="sat", score="1200", level="B2",
                          exam_name="zzz", sub_scores='{"L":7}')
ck("turga kerakmas maydonlar None",
   (v["level"], v["exam_name"], v["sub_scores"]), (None, None, None))

print("\n=== 4. YUKLASH (kutilayotgan) VA KO'RINISH MATRITSASI ===")
FILE1 = png("ali-ielts")
PUSHES.clear()
r = up(H1, FILE1, score=SCORE, sub_scores='{"L":8.5,"R":9,"W":7.5,"S":8}',
       cert_no="UZ-123")
ck("IELTS yuklandi — 200", r.status_code, 200)
U1 = r.json().get("id")
ck("javobda faqat id va status", sorted(r.json().keys()), ["id", "status"])
ck("javob holati pending", r.json().get("status"), "pending")
no_score("yuklash javobida ball yo'q", r.json())
u = rows(models.WordbankCertUpload, id=U1)[0]
ck("saqlangan: yorliq server yasagan", u.result_label, LABEL)
ck("saqlangan: mime sehrli baytlardan", u.mime, "image/png")
ck("saqlangan: snapshot", (u.name_snap, u.branch_id_snap),
   ("Ali Vositov", bA.id))
att = rows(models.Attachment, entity="vocab_cert", entity_id=U1)
ck("fayl Attachment da (entity=vocab_cert)", len(att), 1)
ck("attachment_id bog'langan", u.attachment_id, att[0].id if att else None)

ck("ustozga bitta bildirishnoma", len(PUSHES), 1)
if PUSHES:
    ck("bildirishnoma — faqat A guruh ustoziga", PUSHES[0]["users"], [uTA.id])
    ck("bildirishnoma matni AYNAN", PUSHES[0]["body"],
       "Yangi sertifikat tekshiruvga yuklandi: Ali Vositov")
    ck("bildirishnoma manzili", PUSHES[0]["url"], "/vocab-certs")
    no_score("bildirishnomada ball yo'q", PUSHES[0])
    ckt("bildirishnoma matnida 8.5 umuman yo'q",
        SCORE not in PUSHES[0]["title"] + PUSHES[0]["body"])

# 2026-10-17 (review): xodimlar push'ga obuna emas — qo'ng'iroqchada
# (/api/my/alerts) chegaradagi kutilayotganlar SONI chiqadi
def alert_texts(h):
    r = client.get("/api/my/alerts", headers=h)
    return [x["text"] for x in r.json().get("items", [])
            if x.get("link") == "/vocab-certs"] if r.status_code == 200 \
        else None


ck("ustoz A: qo'ng'iroqchada 1 ta kutilayotgan", alert_texts(HTA),
   ["1 ta sertifikat tekshiruvni kutmoqda"])
ck("ustoz B (boshqa guruh): yo'q", alert_texts(HTB), [])
ck("hisobchi (tasdiqlay olmaydi): yo'q", alert_texts(HACC), [])
no_score("qo'ng'iroqchada ball yo'q",
         client.get("/api/my/alerts", headers=HTA).json())

r = client.get("/api/wordbank/certs/mine", headers=H1)
ck("o'z ro'yxati — 200", r.status_code, 200)
mine = r.json()
no_score("o'z ro'yxatida ball yo'q (pending)", mine)
it = mine["items"][0]
ck("o'z ro'yxati: holat yorlig'i", it["status_label"],
   "Yuklandi — tekshirilmoqda")
ck("o'z ro'yxati: natija maydonlari null",
   [it[k] for k in ("result_label", "score", "level", "exam_name",
                    "sub_scores", "cert_no")], [None] * 6)
ck("o'z ro'yxati: kalitlar shartnomadagidek", sorted(it.keys()), sorted([
    "id", "exam_type", "exam_label", "status", "status_label", "created_at",
    "test_date", "result_label", "score", "level", "exam_name",
    "sub_scores", "cert_no", "reject_reason", "reject_note", "can_withdraw",
    "can_reupload", "mime"]))
ck("o'z ro'yxati: qaytarib olish mumkin", it["can_withdraw"], True)
ck("cheklovlar", mine["limits"], {"max_pending": 3, "pending": 1,
                                  "max_30d": 10, "used_30d": 1,
                                  "max_bytes": 3 * 1024 * 1024})

r = client.get("/api/wordbank/me", headers=H1)
ck("/me — 200", r.status_code, 200)
no_score("/me da kutilayotgan ball yo'q", r.json())
if "certs_pending" in r.json():
    ck("/me certs_pending — faqat son", r.json()["certs_pending"], 1)
    ck("/me certs — bo'sh (tasdiqlanmagan)", r.json().get("certs"), [])
for sc in ("group", "branch", "school"):
    for per in ("total", "history"):
        r = client.get(f"/api/wordbank/leaderboard?scope={sc}&period={per}",
                       headers=H1)
        no_score(f"reyting {sc}/{per}: ball yo'q (status {r.status_code})",
                 r.text)
        r = client.get(f"/api/wordbank/leaderboard?scope={sc}&period={per}",
                       headers=H2)
        no_score(f"reyting {sc}/{per} (sinfdosh): ball yo'q", r.text)
r = client.get(f"/api/parent/{TOK1}")
ck("ota-ona sahifasi — 200", r.status_code, 200)
no_score("ota-ona sahifasida ball yo'q", r.text)
r = client.get(f"/api/wordbank/teacher/students?group_id={gA.id}",
               headers=HTA)
no_score(f"ustoz ro'yxatida ball yo'q (status {r.status_code})", r.text)
ck("o'qish yordamchisi: tasdiqlanganlar yo'q",
   WCERT.confirmed_badges(SessionLocal(), [S1]), {})
ck("o'qish yordamchisi: kutilayotgan soni",
   WCERT.pending_count(SessionLocal(), S1), 1)
# umumiy /api/attachments sertifikat faylini bermaydi (skelet)
r = client.get(f"/api/attachments?entity=vocab_cert&entity_id={U1}",
               headers=HF)
ck("umumiy ro'yxat vocab_cert ni bermaydi", r.json(), [])
r = client.get(f"/api/attachments/{u.attachment_id}", headers=HF)
ck("umumiy yo'l vocab_cert faylini bermaydi", r.status_code, 404)

print("\n=== 5. BIR XIL FAYL ===")
r = up(H1, FILE1, score=SCORE)
ck("o'zida kutilayotgan fayl qayta — 409", r.status_code, 409)
ck("409 matni", r.json().get("detail"), "Bu fayl allaqachon yuklangan")
FILE2 = jpg("malika-multi")
r = up(H2, FILE1, fname="nusxa.png", score="6.0")
ck("boshqa o'quvchida xuddi shu fayl — qabul (200)", r.status_code, 200)
U2DUP = r.json().get("id")
r = up(H2, FILE2, fname="m.jpg", mime="image/jpeg", exam_type="multilevel",
       level="B2", score="58")
ck("s2 multilevel yuklandi", r.status_code, 200)
U2 = r.json().get("id")
r = up(H2, pdf("malika-pdf"), fname="m.pdf", mime="application/pdf",
       exam_type="sat", score="1350")
ck("PDF qabul qilinadi", r.status_code, 200)
U2PDF = r.json().get("id")
ck("PDF mime", rows(models.WordbankCertUpload, id=U2PDF)[0].mime,
   "application/pdf")

print("\n=== 6. XODIM NAVBATI VA CHEGARA ===")
r = staff_list(HF)
ck("asoschi: navbat — 200", r.status_code, 200)
lst = r.json()
ck("navbat: eng eskisi birinchi", [x["id"] for x in lst["items"]],
   [U1, U2DUP, U2, U2PDF])
first = lst["items"][0]
ck("navbat: xodim ballni ko'radi", (first["score"], first["result_label"]),
   (8.5, LABEL))
ck("navbat: bo'limlar", first["sub_scores"],
   {"L": 8.5, "R": 9.0, "W": 7.5, "S": 8.0})
ck("navbat: dublikat ogohlantirish (s1)", first["duplicate_warning"],
   "bu fayl boshqa o'quvchi tomonidan ham yuklangan")
dup2 = [x for x in lst["items"] if x["id"] == U2DUP][0]
ck("navbat: dublikat ogohlantirish (s2)", dup2["duplicate_warning"],
   "bu fayl boshqa o'quvchi tomonidan ham yuklangan")
ck("navbat: dublikatsiz qator", [x for x in lst["items"]
                                 if x["id"] == U2][0]["duplicate_warning"],
   None)
ck("navbat: ism, guruh, filial",
   (first["student_name"], first["groups"], first["branch_name"],
    first["student_exists"], first["student_public_id"]),
   ("Ali Vositov", ["IELTS 6.0"], "Pilot filial", True, "STU-CERT-1"))
ck("navbat: kutish kuni 0", first["days_waiting"], 0)
ck("navbat: counts", lst["counts"], {"pending": 4, "confirmed": 0,
                                     "rejected": 0})
ck("asoschi bekor qila oladi", lst["can_revoke"], True)
ck("StaffCert kalitlari", sorted(first.keys()), sorted([
    "id", "student_id", "student_name", "student_public_id",
    "student_exists", "branch_id", "branch_name", "groups", "exam_type",
    "exam_label", "exam_name", "score", "level", "sub_scores",
    "result_label", "test_date", "cert_no", "mime", "size", "status",
    "created_at", "days_waiting", "duplicate_warning", "verify_method",
    "review_note", "reviewed_by_name", "reviewed_at", "reject_reason",
    "reject_note", "revoked_by_name", "revoked_at", "revoke_note"]))

r = staff_list(HTA)
ck("A guruh ustozi o'z o'quvchilarini ko'radi", ids_of(r),
   [U1, U2DUP, U2, U2PDF])
ck("ustoz bekor qila olmaydi (can_revoke)", r.json().get("can_revoke"), False)
ck("A ustoz: o'z guruhi filtri — 200",
   staff_list(HTA, group_id=gA.id).status_code, 200)
ck("A ustoz: global branch_id e'tiborsiz (guruh chegarasi)",
   ids_of(staff_list(HTA, branch_id=bB.id)), [U1, U2DUP, U2, U2PDF])
r = staff_list(HTB)
ck("B guruh ustozi A o'quvchilarini ko'rmaydi", ids_of(r), [])
ck("B ustoz: begona guruh filtri — 403",
   staff_list(HTB, group_id=gA.id).status_code, 403)
ck("B ustoz: begona fayl — 404",
   client.get(f"/api/wordbank/certs/{U1}/file", headers=HTB).status_code,
   404)
r = client.post(f"/api/wordbank/certs/{U1}/confirm", headers=HTB,
                json={"verify_method": "fayl bo'yicha"})
ck("B ustoz: begona tasdiq — 404", r.status_code, 404)
r = client.post(f"/api/wordbank/certs/{U1}/reject", headers=HTB,
                json={"reason_code": "boshqa odamniki"})
ck("B ustoz: begona rad — 404", r.status_code, 404)
ck("B ustoz: kutilayotganlar soni 0",
   client.get("/api/wordbank/certs/count", headers=HTB).json(),
   {"pending": 0})
ck("A ustoz: kutilayotganlar soni 4",
   client.get("/api/wordbank/certs/count", headers=HTA).json(),
   {"pending": 4})

ck("A administrator ko'radi", ids_of(staff_list(HADA)),
   [U1, U2DUP, U2, U2PDF])
ck("A administrator: o'z filiali filtri",
   ids_of(staff_list(HADA, branch_id=bA.id)), [U1, U2DUP, U2, U2PDF])
ck("B administrator (sales_manager) A ni ko'rmaydi",
   ids_of(staff_list(HADB)), [])
ck("B administrator: begona filial filtri — 403",
   staff_list(HADB, branch_id=bA.id).status_code, 403)
ck("B administrator: begona fayl — 404",
   client.get(f"/api/wordbank/certs/{U1}/file", headers=HADB).status_code,
   404)
r = client.post(f"/api/wordbank/certs/{U1}/confirm", headers=HADB,
                json={"verify_method": "fayl bo'yicha"})
ck("B administrator: begona tasdiq — 404", r.status_code, 404)
ck("B administrator: soni (begona filial filtri jim)",
   client.get(f"/api/wordbank/certs/count?branch_id={bA.id}",
              headers=HADB).json(), {"pending": 0})
ck("o'quv bo'limi rahbari (butun markaz) ko'radi",
   ids_of(staff_list(HAH)), [U1, U2DUP, U2, U2PDF])
ck("buxgalter — 403", staff_list(HACC).status_code, 403)
ck("o'quvchi xodim navbatiga — 403", staff_list(H1).status_code, 403)
ck("noto'g'ri status — 400", staff_list(HF, status="yoq").status_code, 400)
ck("noto'g'ri branch_id — 400",
   staff_list(HF, branch_id="abc").status_code, 400)

print("\n=== 7. FAYL JAVOBI ===")
r = client.get(f"/api/wordbank/certs/{U1}/file", headers=HTA)
ck("ustoz: fayl — 200", r.status_code, 200)
ck("fayl: baytlar bir xil", r.content == FILE1, True)
ck("fayl: Content-Type", r.headers.get("content-type"), "image/png")
ck("fayl: nosniff", r.headers.get("x-content-type-options"), "nosniff")
ck("fayl: CSP sandbox", r.headers.get("content-security-policy"), "sandbox")
ck("fayl: inline", r.headers.get("content-disposition"),
   f'inline; filename="sertifikat-{U1}.png"')
ck("fayl: no-store", r.headers.get("cache-control"), "private, no-store")
r = client.get(f"/api/wordbank/certs/mine/{U1}/file", headers=H1)
ck("o'quvchi: o'z fayli — 200", r.status_code, 200)
ck("o'quvchi fayli: nosniff + sandbox",
   (r.headers.get("x-content-type-options"),
    r.headers.get("content-security-policy")), ("nosniff", "sandbox"))
r = client.get(f"/api/wordbank/certs/mine/{U2PDF}/file", headers=H2)
ck("PDF: Content-Type", r.headers.get("content-type"), "application/pdf")
ck("PDF: fayl nomi", r.headers.get("content-disposition"),
   f'inline; filename="sertifikat-{U2PDF}.pdf"')
ck("o'quvchi: begona fayl — 404",
   client.get(f"/api/wordbank/certs/mine/{U2}/file", headers=H1).status_code,
   404)
ck("o'quvchi: id son emas — 404",
   client.get("/api/wordbank/certs/mine/abc/file", headers=H1).status_code,
   404)

print("\n=== 8. TASDIQLASH ===")
r = client.post(f"/api/wordbank/certs/{U1}/confirm", headers=HTA, json={})
ck("tekshirish usulisiz — 400", r.status_code, 400)
r = client.post(f"/api/wordbank/certs/{U1}/confirm", headers=HTA,
                json={"verify_method": "ko'z bilan"})
ck("noma'lum tekshirish usuli — 400", r.status_code, 400)
PUSHES.clear()
r = client.post(f"/api/wordbank/certs/{U1}/confirm", headers=HTA,
                json={"verify_method": "asl nusxa ko'rildi",
                      "note": "asli ko'rildi"})
ck("A ustoz tasdiqladi — 200", r.status_code, 200)
ck("tasdiq: holat va yorliq", (r.json().get("status"),
                               r.json().get("result_label")),
   ("confirmed", LABEL))
ck("tasdiq: kim", r.json().get("reviewed_by_name"), "Ustoz Anvar")
certs = rows(models.Certificate, student_id=S1)
ck("aynan bitta Certificate", len(certs), 1)
if certs:
    c = certs[0]
    ck("Certificate maydonlari", (c.kind, c.level, c.score, c.date,
                                  c.created_by),
       ("ielts", "8.5", 8.5, date(2026, 9, 20), "Ustoz Anvar"))
    ckt("Certificate izohi", "So'z bilish: IELTS 8.5" in (c.note or ""))
    ck("yuklamada certificate_id",
       rows(models.WordbankCertUpload, id=U1)[0].certificate_id, c.id)
aud = [a for a in rows(models.AuditLog, entity="student", entity_id=S1)
       if a.field == "vocab_cert"]
ck("aynan bitta audit yozuvi", len(aud), 1)
if aud:
    ck("audit qiymati", (aud[0].new_value, aud[0].user_name),
       (LABEL, "Ustoz Anvar"))
ckt("SMM vazifasi yaratildi", any(
    "Ali Vositov" in (t.title or "") and LABEL in (t.title or "")
    for t in rows(models.Task)))
ck("o'quvchiga bildirishnoma", [(p["users"], p["body"]) for p in PUSHES],
   [([s1.user_id], "Sertifikatingiz tasdiqlandi: IELTS 8.5")])
r = client.post(f"/api/wordbank/certs/{U1}/confirm", headers=HF,
                json={"verify_method": "fayl bo'yicha"})
ck("ikkinchi tasdiq — 409", r.status_code, 409)
ck("ikkinchi tasdiqdan keyin ham bitta Certificate",
   len(rows(models.Certificate, student_id=S1)), 1)
r = client.post(f"/api/wordbank/certs/{U1}/reject", headers=HF,
                json={"reason_code": "boshqa odamniki"})
ck("tasdiqlanganni rad etib bo'lmaydi — 409", r.status_code, 409)

it = [x for x in client.get("/api/wordbank/certs/mine", headers=H1)
      .json()["items"] if x["id"] == U1][0]
ck("o'z ro'yxati: tasdiqlangan natija",
   (it["status_label"], it["result_label"], it["score"], it["cert_no"]),
   ("Tasdiqlangan", LABEL, 8.5, "UZ-123"))
ck("o'qish yordamchisi: belgi", WCERT.latest_badges(SessionLocal(), [S1]),
   {S1: LABEL})
r = client.get("/api/wordbank/me", headers=H1)
if "certs" in r.json():
    ck("/me certs — tasdiqlangan belgi",
       [b["label"] for b in r.json()["certs"]], [LABEL])
r = client.get("/api/wordbank/leaderboard?scope=group&period=total",
               headers=H2)
if r.status_code == 200:
    mine_row = [x for x in r.json().get("rows", [])
                if x.get("initials") == "AV"]
    if mine_row:
        ck("reyting: tasdiqlangan belgi chiqdi", mine_row[0]["cert_badge"],
           LABEL)
r = client.get(f"/api/parent/{TOK1}")
wbp = r.json().get("wordbank")
if wbp:
    ck("ota-ona: tasdiqlangan belgi", [b["label"] for b in wbp["certs"]],
       [LABEL])

# xodim tuzatgan qiymat — belgiga aynan shu chiqadi (eskisi emas)
r = client.post(f"/api/wordbank/certs/{U2}/confirm", headers=HADA,
                json={"verify_method": "onlayn tekshirildi", "level": "C1",
                      "score": 80})
ck("tuzatishda qoida buzilsa — 400", r.status_code, 400)
ck("400 dan keyin holat o'zgarmadi",
   rows(models.WordbankCertUpload, id=U2)[0].status, "pending")
r = client.post(f"/api/wordbank/certs/{U2}/confirm", headers=HADA,
                json={"verify_method": "onlayn tekshirildi", "level": "C1",
                      "score": 66})
ck("A administrator tuzatib tasdiqladi", (r.status_code,
                                         r.json().get("result_label")),
   (200, "Multilevel C1 (66)"))
ck("tuzatilgan belgi (eskisi emas)",
   WCERT.latest_badges(SessionLocal(), [S2]), {S2: "Multilevel C1 (66)"})
c2 = rows(models.Certificate, student_id=S2)
ck("multilevel Certificate", [(c.kind, c.level, c.score) for c in c2],
   [("cefr", "C1", 66.0)])

print("\n=== 9. RAD ETISH ===")
r = client.post(f"/api/wordbank/certs/{U2DUP}/reject", headers=HTA, json={})
ck("sababsiz — 400", r.status_code, 400)
r = client.post(f"/api/wordbank/certs/{U2DUP}/reject", headers=HTA,
                json={"reason_code": "boshqa"})
ck("'boshqa' izohsiz — 400", r.status_code, 400)
PUSHES.clear()
r = client.post(f"/api/wordbank/certs/{U2DUP}/reject", headers=HTA,
                json={"reason_code": "boshqa odamniki",
                      "note": "bu Alining fayli"})
ck("rad etildi — 200", (r.status_code, r.json().get("status")),
   (200, "rejected"))
ck("o'quvchiga rad bildirishnomasi", [(p["users"], p["body"])
                                      for p in PUSHES],
   [([s2.user_id], "Sertifikatingiz rad etildi: boshqa odamniki. Profil "
     "bo'limidan qayta yuklashingiz mumkin.")])
no_score("rad bildirishnomasida ball yo'q", PUSHES)
r = client.post(f"/api/wordbank/certs/{U2DUP}/reject", headers=HTA,
                json={"reason_code": "boshqa odamniki"})
ck("ikkinchi rad — 409", r.status_code, 409)
r = client.post(f"/api/wordbank/certs/{U2DUP}/confirm", headers=HTA,
                json={"verify_method": "fayl bo'yicha"})
ck("rad etilganni tasdiqlab bo'lmaydi — 409", r.status_code, 409)
it = [x for x in client.get("/api/wordbank/certs/mine", headers=H2)
      .json()["items"] if x["id"] == U2DUP][0]
ck("o'z ro'yxati: rad sababi, qayta yuklash, ball yo'q",
   (it["status_label"], it["reject_reason"], it["reject_note"],
    it["can_reupload"], it["score"], it["result_label"]),
   ("Rad etildi", "boshqa odamniki", "bu Alining fayli", True, None, None))
r = up(H2, FILE1, fname="nusxa.png", score="6.0")
ck("rad etilgandan keyin xuddi shu fayl qayta — 200", r.status_code, 200)
U2RE = r.json().get("id")
r = up(H1, FILE1, score=SCORE)
ck("o'zida tasdiqlangan fayl qayta — 409", r.status_code, 409)

print("\n=== 10. QAYTARIB OLISH ===")
r = client.delete(f"/api/wordbank/certs/mine/{U2}", headers=H1)
ck("begona yuklamani qaytarib olish — 404", r.status_code, 404)
r = client.delete(f"/api/wordbank/certs/mine/{U2}", headers=H2)
ck("tasdiqlanganni qaytarib olib bo'lmaydi — 409", r.status_code, 409)
r = client.delete(f"/api/wordbank/certs/mine/{U2RE}", headers=H2)
ck("kutilayotganni qaytarib olish — 200", r.json(),
   {"id": U2RE, "status": "withdrawn"})
r = client.delete(f"/api/wordbank/certs/mine/{U2RE}", headers=H2)
ck("ikkinchi marta — 409", r.status_code, 409)
ckt("qaytarib olingan o'z ro'yxatida yo'q", U2RE not in [
    x["id"] for x in client.get("/api/wordbank/certs/mine",
                                headers=H2).json()["items"]])
ck("qaytarib olingan qator bazada qoladi",
   rows(models.WordbankCertUpload, id=U2RE)[0].status, "withdrawn")
# 2026-10-17 (review): qaytarib olingan yuklama xodimga ko'rinmaydi
ck("xodim: status=withdrawn — 400",
   staff_list(HF, status="withdrawn").status_code, 400)
ck("xodim: qaytarib olinganning fayli — 404",
   client.get(f"/api/wordbank/certs/{U2RE}/file", headers=HF).status_code,
   404)
ck("o'quvchi o'z faylini ko'ra oladi",
   client.get(f"/api/wordbank/certs/mine/{U2RE}/file",
              headers=H2).status_code, 200)

print("\n=== 11. BEKOR QILISH ===")
r = client.post(f"/api/wordbank/certs/{U1}/revoke", headers=HTA,
                json={"note": "xato"})
ck("ustoz bekor qila olmaydi — 403", r.status_code, 403)
r = client.post(f"/api/wordbank/certs/{U1}/revoke", headers=HADA,
                json={"note": "xato"})
ck("administrator bekor qila olmaydi — 403", r.status_code, 403)
r = client.post(f"/api/wordbank/certs/{U1}/revoke", headers=HF, json={})
ck("izohsiz — 400", r.status_code, 400)
r = client.post(f"/api/wordbank/certs/{U2PDF}/revoke", headers=HF,
                json={"note": "x"})
ck("kutilayotganni bekor qilib bo'lmaydi — 409", r.status_code, 409)
r = client.post(f"/api/wordbank/certs/{U1}/revoke", headers=HBM,
                json={"note": "Sertifikat soxta chiqdi"})
ck("filial rahbari bekor qildi — 200", (r.status_code, r.json().get("status")),
   (200, "revoked"))
ck("bekor: kim va izoh", (r.json().get("revoked_by_name"),
                          r.json().get("revoke_note")),
   ("Certbm", "Sertifikat soxta chiqdi"))
ck("Certificate o'chirildi", len(rows(models.Certificate, student_id=S1)), 0)
ck("yuklamada certificate_id iz uchun qoldi",
   rows(models.WordbankCertUpload, id=U1)[0].certificate_id is not None, True)
ck("fayl qoldi (D4)",
   len(rows(models.Attachment, entity="vocab_cert", entity_id=U1)), 1)
aud = [a for a in rows(models.AuditLog, entity="student", entity_id=S1)
       if a.field == "vocab_cert"]
ck("bekor audit yozuvi", [(a.old_value, a.new_value) for a in aud][-1:],
   [(LABEL, "bekor qilindi")])
ck("belgi yo'qoldi (o'qish yordamchisi)",
   WCERT.latest_badges(SessionLocal(), [S1]), {})
it = [x for x in client.get("/api/wordbank/certs/mine", headers=H1)
      .json()["items"] if x["id"] == U1][0]
ck("o'z ro'yxati: bekor qilindi, natija yo'q",
   (it["status_label"], it["result_label"], it["score"]),
   ("Bekor qilindi", None, None))
r = client.get("/api/wordbank/me", headers=H1)
if "certs" in r.json():
    ck("/me certs — bekor qilingandan keyin bo'sh", r.json()["certs"], [])
r = client.get("/api/wordbank/leaderboard?scope=group&period=total",
               headers=H2)
if r.status_code == 200:
    no_score("reyting: bekor qilingan belgi yo'q", r.text)
no_score("ota-ona: bekor qilingan belgi yo'q",
         client.get(f"/api/parent/{TOK1}").text)
r = client.post(f"/api/wordbank/certs/{U1}/revoke", headers=HF,
                json={"note": "yana"})
ck("ikkinchi bekor — 409", r.status_code, 409)
r = staff_list(HF, status="rejected,revoked")
ck("Rad etilgan yorlig'i: rejected + revoked",
   sorted(ids_of(r)), sorted([U2DUP, U1]))
ck("counts", r.json()["counts"], {"pending": 1, "confirmed": 1,
                                  "rejected": 2})
ck("tasdiqlanganlar yorlig'i", ids_of(staff_list(HF, status="confirmed")),
   [U2])

print("\n=== 12. CHEKLOVLAR (3 kutilayotgan, 30 kunda 10) ===")
got = [up(H4, png(f"lim-{i}")).status_code for i in range(3)]
ck("3 ta kutilayotgan — 200", got, [200, 200, 200])
r = up(H4, png("lim-3"))
ck("4-kutilayotgan — 429", r.status_code, 429)
ck("429 matni", r.json().get("detail"),
   "Tekshirilayotgan sertifikatlar 3 tadan oshmasin")
for x in client.get("/api/wordbank/certs/mine", headers=H4).json()["items"]:
    client.delete(f"/api/wordbank/certs/mine/{x['id']}", headers=H4)
got = []
for i in range(7):
    r = up(H4, png(f"lim-b{i}"))
    got.append(r.status_code)
    if r.status_code == 200:
        client.delete(f"/api/wordbank/certs/mine/{r.json()['id']}",
                      headers=H4)
ck("yana 7 ta (jami 10) — 200", got, [200] * 7)
r = up(H4, png("lim-11"))
ck("11-yuklama 30 kun ichida — 429", r.status_code, 429)
ck("429 matni (30 kun)", r.json().get("detail"),
   "30 kunda 10 tadan ko'p yuklab bo'lmaydi")
ck("cheklovlar: used_30d",
   client.get("/api/wordbank/certs/mine", headers=H4).json()["limits"]
   ["used_30d"], 10)

print("\n=== 13. KUTISH KUNLARI ===")
CLOCK["t"] += timedelta(days=4)
r = staff_list(HF)
ck("kutilayotganlar: kutish kuni 4", sorted({x["days_waiting"]
                                             for x in r.json()["items"]}),
   [4])
r = up(H4, png("lim-later"))
ck("31 kundan keyin emas, 4 kunda hali 429", r.status_code, 429)
CLOCK["t"] += timedelta(days=27)
r = up(H4, png("lim-later"))
ck("31 kundan keyin yana mumkin", r.status_code, 200)

print("\n=== 14. O'QUVCHI BUTUNLAY O'CHIRILSA ===")
r = up(H5, webp("bola-webp"), fname="b.webp", mime="image/webp",
       exam_type="toefl", score="95", test_date="2026-10-01")
ck("WEBP qabul", r.status_code, 200)
U5 = r.json().get("id")
r = client.delete(f"/api/students/{S5}", headers=HF)
ck("asoschi o'quvchini o'chirdi", r.status_code, 200)
ck("yuklama qoldi (D4)", len(rows(models.WordbankCertUpload, id=U5)), 1)
ck("fayl qoldi (D4)",
   len(rows(models.Attachment, entity="vocab_cert", entity_id=U5)), 1)
lst = staff_list(HF).json()["items"]
row5 = [x for x in lst if x["id"] == U5]
ck("navbatda ko'rinadi (snapshot bilan)",
   [(x["student_exists"], x["student_name"], x["branch_name"], x["groups"])
    for x in row5], [(False, "O'chiriladigan Bola", "Pilot filial", [])])
ck("A administrator snapshot filiali bo'yicha ko'radi",
   U5 in ids_of(staff_list(HADA)), True)
ck("B administrator ko'rmaydi", U5 in ids_of(staff_list(HADB)), False)
ck("ustoz (o'quvchi guruhda yo'q) ko'rmaydi", U5 in ids_of(staff_list(HTA)),
   False)
r = client.post(f"/api/wordbank/certs/{U5}/confirm", headers=HF,
                json={"verify_method": "fayl bo'yicha"})
ck("o'chirilgan o'quvchini tasdiqlab bo'lmaydi — 409", r.status_code, 409)
r = client.get(f"/api/wordbank/certs/{U5}/file", headers=HF)
ck("o'chirilgan o'quvchi fayli asoschiga — 200", r.status_code, 200)
r = client.post(f"/api/wordbank/certs/{U5}/reject", headers=HF,
                json={"reason_code": "sertifikat emas"})
ck("o'chirilgan o'quvchinikini rad etish mumkin", r.status_code, 200)

print("\n=== NATIJA ===")
if fails:
    print(f"XATOLAR ({len(fails)}):")
    for f in fails:
        print("  -", f)
    sys.exit(1)
print("Hammasi OK")
