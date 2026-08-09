"""Baza sxemasi modeldan orqada qolmasligi.

2026-08-09 da modelga students.parent_token_expires_at ustuni
qo'shildi, lekin bazaga qo'shilmadi. create_all() faqat yo'q jadvalni
yaratadi — mavjud jadvalga ustun qo'shmaydi. Natijada o'quvchiga
tegadigan har bir so'rov 500 berdi: dashboard, dars jadvali,
o'quvchilar ro'yxati, ustoz kabineti. Shu holat qaytmasligi uchun
test.
"""
import os
import sys

os.environ["DATABASE_URL"] = "sqlite:////tmp/t_schema_sync.db"
for _f in ("/tmp/t_schema_sync.db", "/tmp/t_schema_sync.db-journal"):
    if os.path.exists(_f):
        os.remove(_f)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import Column, DateTime, String, inspect  # noqa: E402

import entry  # noqa: E402
import models  # noqa: E402
from database import Base, SessionLocal, engine  # noqa: E402

ok = fail = 0


def check(name, cond, extra=""):
    global ok, fail
    if cond:
        ok += 1
        print(f"  OK  {name}")
    else:
        fail += 1
        print(f"  XX  {name} {extra}")


def cols(table):
    return {c["name"] for c in inspect(engine).get_columns(table)}


print("\n--- Ishga tushganda ustunlar mos ---")
res = entry._sync_missing_columns()
check("hech narsa qo'shilmadi (baza mos)", res["added"] == [], res["added"])
check("qo'lda migratsiya kerak bo'lgani yo'q", res["manual"] == [],
      res["manual"])

print("\n--- Modelga yangi ustun qo'shildi, bazada yo'q ---")
models.Student.parent_token_expires_at = Column(
    "parent_token_expires_at", DateTime)
models.Student.probe_note = Column("probe_note", String)
check("bazada hali yo'q", "parent_token_expires_at" not in cols("students"))

res = entry._sync_missing_columns()
check("ikkalasi ham qo'shildi",
      "students.parent_token_expires_at" in res["added"]
      and "students.probe_note" in res["added"], res["added"])
check("bazada paydo bo'ldi", "parent_token_expires_at" in cols("students"))

print("\n--- O'quvchi so'rovi endi ishlaydi ---")
db = SessionLocal()
db.add(models.Student(full_name="Sxema testi"))
db.commit()
check("so'rov 500 bermaydi", db.query(models.Student).count() >= 1)
db.close()

print("\n--- Ikkinchi yurishda takrorlanmaydi ---")
res = entry._sync_missing_columns()
check("qayta qo'shmaydi", res["added"] == [], res["added"])

print("\n--- NOT NULL ustun jimgina qo'shilmaydi ---")
models.Student.must_fill = Column("must_fill", String, nullable=False)
res = entry._sync_missing_columns()
check("qo'shilmadi", "students.must_fill" not in res["added"], res["added"])
check("ro'yxatga chiqarildi", "students.must_fill" in res["manual"],
      res["manual"])
check("baza tegilmadi", "must_fill" not in cols("students"))

print("\n--- Yo'q jadval e'tiborsiz qoldiriladi ---")
Base.metadata.tables  # noqa: B018  - metadata yuklanganini bildiradi
res = entry._sync_missing_columns()
check("xato bermadi", isinstance(res, dict))

print(f"\n=== {ok} ok / {fail} fail ===")
sys.exit(1 if fail else 0)
