# -*- coding: utf-8 -*-
"""SXEMA SHTAMPI QO'RIQCHISI (2026-08-28).

NIMA BO'LGANI. Kontent-plan uchun 0010 migratsiyasi yozildi, lekin
SCHEMA_STAMP qo'lda yangilanmadi. Jonli bazada eski shtamp turgani
uchun _schema_bootstrap() "sxema tayyor" deb erta qaytdi va
migratsiya UMUMAN ishlamadi. Natijada contents jadvalida yangi
ustunlar yo'q edi va har qanday so'rov

    no such column: contents.proof

bilan yiqildi — butun SMM bo'limi ochilmay qoldi. Jahongir
ekranida "Serverda kutilmagan xato" chiqdi.

TUZATISH. Shtamp endi qo'lda yozilmaydi — oxirgi migratsiya nomidan
avtomat quriladi. Yangi migratsiya qo'shilishi bilan shtamp o'zi
o'zgaradi. Odam esdan chiqarishi mumkin edi; kod chiqarmaydi.

Bu test ikki narsani qo'riqlaydi:
  1. Shtamp oxirgi migratsiyaga BOG'LIQ ekani (bog'lanish uzilsa
     xato qaytadi);
  2. Eski shtampli bazada yangi migratsiya ROSTDAN ishlashi —
     jonli holat aynan shunday edi.
"""
import os
import sys

os.environ["DATABASE_URL"] = "sqlite:////tmp/verify_stamp/db.sqlite"
os.makedirs("/tmp/verify_stamp", exist_ok=True)
if os.path.exists("/tmp/verify_stamp/db.sqlite"):
    os.remove("/tmp/verify_stamp/db.sqlite")
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


print("=== SHTAMP OXIRGI MIGRATSIYAGA BOG'LANGAN ===")
last = migrations.MIGRATIONS[-1][0]
ck("shtampda oxirgi migratsiya nomi bor", last in common.SCHEMA_STAMP, True)
ck("shtamp qo'lda yozilgan qatorga o'xshamaydi",
   common.SCHEMA_STAMP.count("_") >= 4, True)

print("\n=== ESKI SHTAMPLI BAZADA MIGRATSIYA ISHLAYDI ===")
common._schema_bootstrap()
db = SessionLocal()


def cols(table):
    return [r[1] for r in
            db.execute(sa.text(f"PRAGMA table_info({table})")).all()]


# Jonli bazani taqlid qilamiz: eski shtamp, oxirgi migratsiya yo'q,
# ustunlar ham yo'q.
NEW_CONTENT = ["proof", "shoot_date", "kpi_target", "conclusion", "series"]
NEW_METRIC = ["source", "fetched_at", "fetch_note"]
db.execute(sa.text("DELETE FROM schema_migrations"))
db.execute(sa.text(
    "INSERT INTO schema_migrations (version) VALUES ('stamp_2026_08_24')"))
db.execute(sa.text("DROP INDEX IF EXISTS ix_contents_series"))
for cname in NEW_CONTENT:
    db.execute(sa.text(f"ALTER TABLE contents DROP COLUMN {cname}"))
for cname in NEW_METRIC:
    db.execute(sa.text(f"ALTER TABLE content_metrics DROP COLUMN {cname}"))
db.commit()

ck("taqlid: ustunlar yo'q",
   any(x in cols("contents") for x in NEW_CONTENT), False)
try:
    db.query(models.Content).first()
    broke = False
except Exception:
    broke = True
    db.rollback()
ck("taqlid: so'rov yiqiladi (jonli holat)", broke, True)

common._SCHEMA_OK = False
common._schema_bootstrap()

ck("bootstrapdan keyin contents ustunlari",
   [x for x in NEW_CONTENT if x not in cols("contents")], [])
ck("bootstrapdan keyin content_metrics ustunlari",
   [x for x in NEW_METRIC if x not in cols("content_metrics")], [])
try:
    db.query(models.Content).first()
    ok = True
except Exception as e:
    ok = str(e)[:80]
ck("Content so'rovi ishlaydi", ok, True)
try:
    db.query(models.ContentMetric).first()
    ok2 = True
except Exception as e:
    ok2 = str(e)[:80]
ck("ContentMetric so'rovi ishlaydi", ok2, True)

print("\n=== MODELDAGI HAR USTUN BAZADA BORMI ===")
# Sxema bilan model bir-biriga mos bo'lishi kerak. Mos bo'lmasa
# ekranda 500 chiqadi va sabab uzoq qidiriladi.
bad = []
for tbl in (models.Content, models.ContentMetric):
    have = set(cols(tbl.__tablename__))
    for col in tbl.__table__.columns:
        if col.name not in have:
            bad.append(f"{tbl.__tablename__}.{col.name}")
ck("yetishmayotgan ustun", bad, [])

print("\n" + ("HAMMASI O'TDI" if not fails else "XATO: " + ", ".join(fails)))
sys.exit(1 if fails else 0)
