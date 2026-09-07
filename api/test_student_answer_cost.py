# -*- coding: utf-8 -*-
"""JAVOB SO'ROVINING NARXI (2026-09-07).

Jahongir: Neon hisobining 95% i bazaning uyg'oq turgan vaqtiga
ketadi ($21.97 / oy). Eng ko'p so'rov — o'quvchi ilovasidan:
kuniga ~4200 ta javob (vocab 2397, grammar 1057, practice 735).

Bu test HAR BIR javob nechta baza so'rovi qilishini o'lchaydi va
javob MAZMUNI o'zgarmaganini tekshiradi.
"""
import os
import sys

os.environ["DATABASE_URL"] = "sqlite:////tmp/ans_cost.db"
if os.path.exists("/tmp/ans_cost.db"):
    os.remove("/tmp/ans_cost.db")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import date                             # noqa: E402
from fastapi.testclient import TestClient             # noqa: E402
from sqlalchemy import event                          # noqa: E402
import main, models, roles                            # noqa: E402
import entry                                          # noqa: E402,F401
from database import SessionLocal, engine             # noqa: E402
from auth import hash_password                        # noqa: E402

client = TestClient(main.app)
fails = []
QN = {"n": 0}


@event.listens_for(engine, "before_cursor_execute")
def _count(conn, cursor, statement, parameters, context, executemany):
    QN["n"] += 1


def ck(name, got, want):
    ok = got == want
    print(("OK  " if ok else "XATO ") + name + f": {got}"
          + ("" if ok else f"   (kutilgan {want})"))
    if not ok:
        fails.append(name)


def tok(u, p="x"):
    return {"Authorization": "Bearer " + client.post(
        "/api/auth/login", json={"username": u, "password": p}
    ).json()["access_token"]}


db = SessionLocal()
b = models.Branch(name="Zafar"); db.add(b); db.commit()
g = models.Group(name="Step 1", branch_id=b.id, lesson_price=45_000,
                 standard_lessons_per_month=12, monthly_fee=540_000)
db.add(g); db.commit()
st = models.Student(full_name="O'quvchi", branch_id=b.id, status="active",
                    group_id=g.id, enrolled_date=date(2026, 6, 1))
db.add(st); db.commit()
u = models.User(username="901234567", password_hash=hash_password("x"),
                full_name="O'quvchi", role=roles.STUDENT, branch_id=b.id)
db.add(u); db.commit()
st.user_id = u.id
db.commit()

# Lug'at so'zlari
words = []
for i in range(12):
    w = models.VocabWord(word=f"word{i}", translation=f"soz{i}",
                         language="en", level="A1", is_active=1)
    db.add(w); words.append(w)
db.commit()
# Grammatika savollari
qs = []
for i in range(6):
    q = models.GrammarQuestion(topic="present simple", level="A1",
                               kind="fill", prompt=f"savol {i}",
                               options='["a","b"]', answer="a",
                               language="en", is_active=1)
    db.add(q); qs.append(q)
db.commit()

S = tok("901234567")


def cost(fn):
    QN["n"] = 0
    r = fn()
    return r, QN["n"]


print("=== 1. Lug'at javobi ===")
r, n1 = cost(lambda: client.post(
    "/api/student/vocab/answer",
    json={"word_id": words[0].id, "game": "uz_en", "answer": "word0"},
    headers=S))
ck("javob 200", r.status_code, 200)
d = r.json()
ck("to'g'ri deb topdi", d.get("correct"), True)
ck("kutilgan javob qaytdi", d.get("expected"), "word0")
ck("XP berildi", d.get("xp") > 0, True)
print(f"   baza so'rovlari: {n1}")

r, n2 = cost(lambda: client.post(
    "/api/student/vocab/answer",
    json={"word_id": words[1].id, "game": "uz_en", "answer": "xato"},
    headers=S))
ck("noto'g'ri javob", r.json().get("correct"), False)
print(f"   noto'g'ri javob so'rovlari: {n2}")

r, n3 = cost(lambda: client.post(
    "/api/student/vocab/answer?want_skills=1",
    json={"word_id": words[2].id, "game": "uz_en", "answer": "word2"},
    headers=S))
ck("so'ralganda daraja kartasi keladi",
   bool(r.json().get("skills")), True)
print(f"   daraja kartasi bilan: {n3}")
ck("daraja kartasi qo'shimcha so'rov talab qiladi", n3 > n1, True)
ck("oddiy javobda daraja kartasi YO'Q",
   d.get("skills") in (None, {}), True)

print("\n=== 2. Grammatika javobi ===")
r, g1 = cost(lambda: client.post(
    "/api/student/grammar/answer",
    json={"question_id": qs[0].id, "answer": "a"}, headers=S))
ck("javob 200", r.status_code, 200)
gd = r.json()
ck("to'g'ri", gd.get("correct"), True)
ck("birinchi marta", gd.get("first_time"), True)
ck("XP", gd.get("xp") > 0, True)
print(f"   baza so'rovlari: {g1}")
r, g2 = cost(lambda: client.post(
    "/api/student/grammar/answer",
    json={"question_id": qs[0].id, "answer": "a"}, headers=S))
ck("ikkinchi marta XP yo'q", r.json().get("xp"), 0)
ck("first_time endi False", r.json().get("first_time"), False)

print("\n=== 3. Yozuvlar bazaga tushdi ===")
db.expire_all()
ck("lug'at urinishlari yozildi",
   db.query(models.VocabAttempt).count(), 3)
ck("grammatika urinishlari yozildi",
   db.query(models.GrammarAttempt).count(), 2)
ck("XP yozuvlari bor",
   db.query(models.XpTransaction).count() >= 2, True)

print(f"\nXULOSA: bitta lug'at javobi = {n1} so'rov, "
      f"grammatika = {g1} so'rov")
print()
print("XATOLAR:", fails if fails else "yo'q")
sys.exit(1 if fails else 0)
