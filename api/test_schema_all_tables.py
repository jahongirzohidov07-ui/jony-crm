# -*- coding: utf-8 -*-
"""SXEMA QO'RIQCHISI — HAMMA JADVAL BO'YICHA (2026-09-10).

NEGA YOZILDI. Bir xil avariya IKKI marta bo'ldi:

  28-avgust: contents.proof ustuni jonli bazada yaratilmadi ->
             butun SMM bo'limi ochilmay qoldi.
  10-sentabr: exams.pass_percent ustuni va exam_pass_rules jadvali
             yaratilmadi -> butun API yiqildi, funksiya xotirasi
             to'lib o'la boshladi, sayt ~1.5 soat ishlamadi.

Ikkalasida ham sabab bitta: sxema shtampi o'zgarmagani uchun
_schema_bootstrap() "hammasi joyida" deb erta qaytdi.

Mavjud test_schema_stamp.py bor edi, lekin u FAQAT ikkita jadvalni
(contents, content_metrics) tekshirardi — shuning uchun sentabrdagi
xatoni umuman ko'rmadi. Shu test o'sha bo'shliqni yopadi:

  1. Shtampga MODEL BARMOQ IZI kirganini — ya'ni ustun qo'shilsa
     shtamp o'zi o'zgarishini;
  2. Barmoq izi BARQARORLIGINI — bir xil modeldan har safar bir xil
     xesh chiqishini (aks holda har cold start'da to'liq migratsiya
     ishlab, Neon trafigi yeyilardi);
  3. HAR BIR modeldagi HAR BIR ustun bazada borligini — ikkita
     jadval emas, hammasi;
  4. Eski shtampli bazada bootstrap yetishmayotgan ustunni
     ROSTDAN qo'shishini (jonli holatning aynan o'zi).
"""
import os
import sys
import tempfile

_DIR = os.path.join(tempfile.gettempdir(), "schema_all_check")
os.makedirs(_DIR, exist_ok=True)
_DB = os.path.join(_DIR, "db.sqlite")
os.environ["DATABASE_URL"] = "sqlite:///" + _DB.replace("\\", "/")
if os.path.exists(_DB):
    os.remove(_DB)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import sqlalchemy as sa                              # noqa: E402
import main, models, migrations                      # noqa: F401,E402
import entry                                         # noqa: F401,E402
import common                                        # noqa: E402
from database import SessionLocal                    # noqa: E402

fails = []


def ck(n, got, want):
    ok = got == want
    print(("OK   " if ok else "XATO ") + f"{n}: {got}"
          + ("" if ok else f"   (kutilgan {want})"))
    if not ok:
        fails.append(n)


print("=== 1. SHTAMP MODELGA BOG'LANGAN ===")
stamp = common.schema_stamp()
fp = common.models_fingerprint()
ck("shtampda barmoq izi bor", fp in stamp, True)
ck("shtampda oxirgi migratsiya nomi bor",
   migrations.MIGRATIONS[-1][0] in stamp, True)

print("\n=== 2. BARMOQ IZI BARQAROR (har safar bir xil) ===")
ck("ketma-ket ikki hisob bir xil",
   common.models_fingerprint() == common.models_fingerprint(), True)
ck("uzunligi qisqa va aniq", len(fp), 10)

print("\n=== 3. USTUN QO'SHILSA BARMOQ IZI O'ZGARADI ===")
# Bugungi xatoning aynan o'zi: models.py ga ustun qo'shildi, lekin
# migratsiya yozilmadi. Shtamp shundayam o'zgarishi SHART.
_api = os.path.dirname(os.path.abspath(__file__))
_mp = os.path.join(_api, "models.py")
_orig = open(_mp, "rb").read()
try:
    open(_mp, "wb").write(
        _orig + b"\n\n_probe_col_for_test = Column(String)\n")
    fp2 = common.models_fingerprint()
finally:
    open(_mp, "wb").write(_orig)
ck("yangi ustundan keyin xesh boshqacha", fp2 != fp, True)
ck("fayl qaytarilgach xesh ham qaytadi", common.models_fingerprint(), fp)

print("\n=== 3b. IMPORT TARTIBIGA BOG'LIQ EMAS ===")
# Vercel'da main.py va entry.py alohida funksiya. Ular bir xil
# shtamp hisoblashi shart, aks holda har biri ikkinchisining
# shtampini "eski" deb bilib, HAR sovuq startda bootstrap
# yugurtiradi. 2026-09-10 da xotira aynan shunday to'lgan edi.
import subprocess                                    # noqa: E402
_env = dict(os.environ, PYTHONIOENCODING="utf-8")


def _fp_in(mods):
    code = ("import sys; sys.path.insert(0, r'%s');\n" % _api
            + "".join("import %s\n" % m for m in mods)
            + "import common; print('FP=' + common.models_fingerprint())")
    out = subprocess.run([sys.executable, "-c", code], env=_env,
                         capture_output=True, text=True).stdout
    for ln in out.splitlines():
        if ln.startswith("FP="):
            return ln[3:]
    return "?"


_fp_bare = _fp_in([])
_fp_main = _fp_in(["main"])
ck("faqat common import qilinganda", _fp_bare, fp)
ck("main import qilinganda ham bir xil", _fp_main, fp)

print("\n=== 4. BOOTSTRAP: HAMMA JADVAL VA USTUN BAZADA ===")
common._schema_bootstrap()
db = SessionLocal()
insp = sa.inspect(db.get_bind())
db_tables = set(insp.get_table_names())

missing_tables = []
missing_cols = []
for tname in sorted(common.Base.metadata.tables):
    if tname not in db_tables:
        missing_tables.append(tname)
        continue
    have = {c["name"] for c in insp.get_columns(tname)}
    for col in common.Base.metadata.tables[tname].columns:
        if col.name not in have:
            missing_cols.append(f"{tname}.{col.name}")

ck("yetishmayotgan JADVAL", missing_tables, [])
ck("yetishmayotgan USTUN", missing_cols, [])
print(f"     (tekshirildi: {len(common.Base.metadata.tables)} jadval)")

print("\n=== 5. ESKI SHTAMPLI BAZA TUZALADI (jonli holat) ===")
# 10-sentabrdagi avariyani aynan takrorlaymiz: ustunni olib
# tashlaymiz va bazaga ESKI shtampni yozamiz.
db.execute(sa.text("DELETE FROM schema_migrations"))
db.execute(sa.text(
    "INSERT INTO schema_migrations (version) VALUES ('stamp_2026_08_28_x')"))
db.execute(sa.text("ALTER TABLE exams DROP COLUMN pass_percent"))
db.commit()


def exam_cols():
    return [r[1] for r in
            db.execute(sa.text("PRAGMA table_info(exams)")).all()]


ck("taqlid: pass_percent yo'q", "pass_percent" in exam_cols(), False)
broke = False
try:
    db.query(models.Exam).first()
except Exception:
    broke = True
    db.rollback()
ck("taqlid: so'rov yiqiladi", broke, True)

common._SCHEMA_OK = None
common._STAMP_CACHE["v"] = None
common._schema_bootstrap()

ck("bootstrapdan keyin ustun bor", "pass_percent" in exam_cols(), True)
try:
    db.query(models.Exam).first()
    ok = True
except Exception as e:
    ok = str(e)[:80]
ck("Exam so'rovi ishlaydi", ok, True)

print("\n=== 6. YANGI JADVAL HAM YARATILADI ===")
ck("exam_pass_rules bazada",
   "exam_pass_rules" in set(sa.inspect(db.get_bind()).get_table_names()),
   True)

print("\n=== 7. QO'LDA ALTER YOZILMAGAN USTUN HAM TIKLANADI ===")
# 5-bo'limdagi pass_percent uchun _ensure_new_columns() da QO'LDA
# ALTER qatori bor. Bu yerda ataylab QO'LDA YOZILMAGAN ustunni
# olib tashlaymiz — uni faqat avtomat solishtiruv qaytara oladi.
# Ya'ni endi ALTER ro'yxatiga qator qo'shishni unutish xavfli emas.
_manual = open(os.path.join(_api, "common.py"), "rb").read()
ck("updated_by qo'lda ro'yxatda YO'Q",
   b"exam_pass_rules ADD COLUMN updated_by" in _manual, False)

db.execute(sa.text("ALTER TABLE exam_pass_rules DROP COLUMN updated_by"))
db.execute(sa.text("DELETE FROM schema_migrations"))
db.commit()


def _epr_cols():
    return [r[1] for r in db.execute(
        sa.text("PRAGMA table_info(exam_pass_rules)")).all()]


ck("taqlid: updated_by yo'q", "updated_by" in _epr_cols(), False)
common._SCHEMA_OK = None
common._schema_bootstrap()
ck("avtomat qaytarildi", "updated_by" in _epr_cols(), True)

db.close()

print("\n" + ("HAMMASI O'TDI" if not fails else "XATO: " + ", ".join(fails)))
sys.exit(1 if fails else 0)
