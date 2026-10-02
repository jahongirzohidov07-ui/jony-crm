"""EXAMINER OYLIGI — JADVAL KO'RINISHIDA (2026-10-02).

Jahongir (skrinshot: "MUHAMMADHAYOT / SENTABR / STRETINKO" jadvali):
"har bir examinerning oyligini shunaqa nechta imtihon oldi va qancha
oylik qayerdan chiqdi ko'rinishi kerak hisobotlarda, examinerlarniki
o'ziga ham ko'rinishi kerak".

Tekshiriladi:
  1. Har imtihon satrida qisqa nom (S2 U9, S1 U7, MID-COURSE, RETAKE ..),
     ustoz, guruh, filial, o'quvchi soni (kelmaganlar sanalmaydi), ball.
  2. Jami: imtihonlar soni, o'quvchilar, ball; filiallar ro'yxati.
"""
import os
import sys
import tempfile
from datetime import date

_DB = os.path.join(tempfile.gettempdir(), "examiner_sheet_test.db")
os.environ["DATABASE_URL"] = "sqlite:///" + _DB.replace("\\", "/")
if os.path.exists(_DB):
    os.remove(_DB)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import main, models, roles                         # noqa: E402,F401
import entry  # noqa: F401,E402
import common                                      # noqa: E402
from database import SessionLocal                  # noqa: E402

fails = []


def ck(name, got, want):
    ok = got == want
    print(("OK  " if ok else "XATO ") + f"{name}: {got}"
          + ("" if ok else f"   (kutilgan {want})"))
    if not ok:
        fails.append(name)


Y, M = 2026, 9
db = SessionLocal()
b = models.Branch(name="STRETINKO"); db.add(b); db.commit()
ex = models.User(username="mh", full_name="Muhammadhayot", role=roles.EXAMINER,
                 branch_id=b.id, is_active=1, password_hash="x")
db.add(ex); db.commit()
EX = ex.id
nodir = models.Teacher(full_name="Abdulatipov Nodir", branch_id=b.id,
                       is_active=1)
nazira = models.Teacher(full_name="Turusnboyeva Nazira", branch_id=b.id,
                        is_active=1)
db.add_all([nodir, nazira]); db.commit()


def group(name, level, teacher):
    g = models.Group(name=name, level=level, branch_id=b.id,
                     teacher_id=teacher.id, subject="english")
    db.add(g); db.commit()
    return g


nevada = group("NEVADA", "step2", nodir)
texas = group("TEXAS", "step1", nodir)
valoria = group("VALORIA", "step1", nazira)


def exam(g, day, kind, unit, present, absent=0, retake_of=None,
         report_teacher=None):
    e = models.Exam(group_id=g.id, kind=kind, unit_no=unit,
                    date=date(Y, M, day), status="done", examiner_id=EX,
                    title="t", max_score=50, retake_of_id=retake_of,
                    report_teacher_id=report_teacher)
    db.add(e); db.commit()
    for i in range(present + absent):
        s = models.Student(full_name=f"{g.name}-{day}-{i}", branch_id=b.id,
                           group_id=g.id, status="active")
        db.add(s); db.commit()
        db.add(models.ExamResult(exam_id=e.id, student_id=s.id,
                                 score=None if i >= present else 30,
                                 absent=1 if i >= present else 0))
    db.commit()
    return e


e1 = exam(nevada, 8, "unit", 9, 7)
exam(texas, 11, "unit", 7, 13, absent=2)
exam(valoria, 19, "mid", None, 4)
exam(texas, 26, "unit", 7, 4, retake_of=e1.id)
db.close()

s = SessionLocal()
d = common._examiner_month(s, EX, Y, M)
s.close()
rows = d["exams"]

print("=== 1. Satrlar ===")
ck("qisqa nomlar", [r["code"] for r in rows],
   ["S2 U9", "S1 U7", "MID-COURSE", "RETAKE S1 U7"])
ck("ustozlar", [r["teacher"] for r in rows],
   ["Abdulatipov Nodir", "Abdulatipov Nodir", "Turusnboyeva Nazira",
    "Abdulatipov Nodir"])
ck("guruh va filial", (rows[0]["group"], rows[0]["branch"]),
   ("NEVADA", "STRETINKO"))
ck("kelmaganlar sanalmaydi", [r["students"] for r in rows], [7, 13, 4, 4])
ck("ball: S2 U9 = 13 + 7x2.5", rows[0]["points"], 30.5)
ck("ball: MID = 20 + 4x3.5", rows[2]["points"], 34.0)

print("\n=== 2. Jami ===")
ck("imtihonlar va o'quvchilar", (d["exam_count"], d["students_total"]),
   (4, 28))
ck("ball jami", d["base_points"], round(sum(r["points"] for r in rows), 2))
ck("filiallar", d["branches"], ["STRETINKO"])

print()
if fails:
    print(f"{len(fails)} ta XATO: {fails}")
    sys.exit(1)
print("HAMMASI OK")
