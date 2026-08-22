"""
MASHQ FILIALI — TEST FILIALINI HAQIQATGA O'XSHASH MA'LUMOT BILAN TO'LDIRISH.

2026-08-23, Jahongir: "test deb filial ochganman shu filialga 100
kishilik qilib o'quvchilar va adminlar qoshib qoyginda shundan bosib
bosib o'rganvolsin adminlar nimani qanday qilishni".

NIMA QILADI. Asoschi bir tugma bosadi — test filialida to'liq "kichik
markaz" paydo bo'ladi: ustozlar, guruhlar, 100 ta o'quvchi (aktiv,
sinovda, muzlatilgan, qarzdor — hammasi aralash), o'tilgan darslar va
yo'qlamalar, to'lovlar, chegirmalar, lidlar va xodim akkauntlari.
Yangi admin shu filialda hech narsadan qo'rqmasdan bosib ko'radi.

XAVFSIZLIK — HAQIQIY FILIALGA HECH QACHON TEGMAYDI:
  1) Faqat ASOSCHI ishlata oladi;
  2) Filial nomida "test" so'zi BO'LISHI SHART (selftest bilan bir xil
     qoida) — bo'lmasa 400 qaytaradi va hech narsa yaratmaydi;
  3) Yaratilgan har bir yozuv nomida "DEMO" belgisi bo'ladi va
     xodim login'lari "demo." bilan boshlanadi — ko'rib turib
     ajratiladi;
  4) TOZALASH tugmasi shu filialdagi FAQAT demo yozuvlarni o'chiradi.

PAROL. Barcha demo xodimlar uchun bitta parol beriladi va javobda
qaytariladi — asoschi uni xodimlarga aytadi. Bu haqiqiy hisob emas,
faqat mashq filialida ishlaydi.
"""
import os
import random
import sys
from datetime import date, datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.orm import Session

import audit
import models
import roles
from auth import hash_password, require_role
from database import get_db

router = APIRouter()

# Demo yozuvlarni ajratib turadigan belgi. Ismning OXIRIDA turadi —
# ro'yxatda alifbo tartibi buzilmasin.
MARK = "(DEMO)"
LOGIN_PREFIX = "demo."
DEMO_PASSWORD = "Demo2026!"

_FAM = [
    "Abdullayev", "Aliyev", "Ergashev", "Isroilov", "Karimov", "Mahmudov",
    "Nazarov", "Olimov", "Qodirov", "Rahimov", "Sattorov", "To'xtayev",
    "Umarov", "Xolmatov", "Yusupov", "Zokirov", "Jo'rayev", "Salimov",
    "Bekmurodov", "G'aniyev",
]
_ISM_O = [
    "Abdulaziz", "Amir", "Behruz", "Diyor", "Eldor", "Firdavs", "Islom",
    "Javohir", "Komil", "Lazizbek", "Mansur", "Nodirbek", "Otabek",
    "Rustam", "Sardor", "Temur", "Ulug'bek", "Xusan", "Zafar", "Shohruh",
]
_ISM_Q = [
    "Aziza", "Barno", "Dilnoza", "Elnora", "Feruza", "Gulnoza", "Iroda",
    "Kamola", "Lola", "Madina", "Nigora", "Ozoda", "Rayhona", "Sabina",
    "Sevinch", "Umida", "Xadicha", "Yulduz", "Zilola", "Nilufar",
]

# Mashq guruhlar: (nom, fan, daraja, kun, vaqt, oylik narx)
_GROUPS = [
    ("Beginners A", "english", "step1", "mon,wed,fri", "09:00", 480000),
    ("Beginners B", "english", "step1", "tue,thu,sat", "11:00", 480000),
    ("Pre-Intermediate", "english", "step2", "mon,wed,fri", "14:00", 480000),
    ("Intermediate", "english", "step3", "tue,thu,sat", "16:00", 520000),
    ("IELTS Starter", "ielts", "ielts_1", "mon,wed,fri", "18:00", 600000),
]

# Mashq xodimlari: (login qo'shimchasi, ism, rol)
_STAFF = [
    ("admin1", "Demo Administrator 1", roles.ADMINISTRATOR),
    ("admin2", "Demo Administrator 2", roles.ADMINISTRATOR),
    ("sotuv", "Demo Sotuv menejeri", roles.SALES_MANAGER),
    ("kassa", "Demo Buxgalter", roles.ACCOUNTANT),
    ("ustoz", "Demo O'qituvchi", roles.TEACHER),
    ("support", "Demo Support teacher", roles.SUPPORT_TEACHER),
]


def _branch_or_400(db: Session, branch_id: int) -> models.Branch:
    b = db.query(models.Branch).get(branch_id)
    if not b:
        raise HTTPException(404, "Filial topilmadi")
    if "test" not in (b.name or "").lower():
        raise HTTPException(
            400, "Faqat nomida \"test\" so'zi bor filial bilan ishlaydi — "
                 "haqiqiy filialga tegilmaydi")
    return b


def _phone(rnd: random.Random) -> str:
    return f"+99890{rnd.randint(1000000, 9999999)}"


@router.get("/api/demo/status")
def demo_status(branch_id: int, db: Session = Depends(get_db),
                user=Depends(require_role(roles.FOUNDER))):
    """Shu test filialida hozir nechta demo yozuv bor."""
    _branch_or_400(db, branch_id)
    like = f"%{MARK}"
    return {
        "students": db.query(models.Student).filter(
            models.Student.branch_id == branch_id,
            models.Student.full_name.like(like)).count(),
        "groups": db.query(models.Group).filter(
            models.Group.branch_id == branch_id,
            models.Group.name.like(like)).count(),
        "teachers": db.query(models.Teacher).filter(
            models.Teacher.branch_id == branch_id,
            models.Teacher.full_name.like(like)).count(),
        "users": db.query(models.User).filter(
            models.User.branch_id == branch_id,
            models.User.username.like(f"{LOGIN_PREFIX}%")).count(),
        "password": DEMO_PASSWORD,
    }


@router.post("/api/demo/seed")
def demo_seed(payload: dict = Body(default={}),
              db: Session = Depends(get_db),
              user=Depends(require_role(roles.FOUNDER))):
    """TEST FILIALINI MASHQ MA'LUMOTI BILAN TO'LDIRISH.

    payload: {"branch_id": 5, "students": 100}
    """
    branch_id = int(payload.get("branch_id") or 0)
    want = max(1, min(300, int(payload.get("students") or 100)))
    b = _branch_or_400(db, branch_id)

    # Ikki marta bosilsa ikkilanmasin — avval borini sanaymiz
    have = db.query(models.Student).filter(
        models.Student.branch_id == branch_id,
        models.Student.full_name.like(f"%{MARK}")).count()
    if have >= want:
        return {"ok": True, "created": 0, "students_total": have,
                "password": DEMO_PASSWORD,
                "note": f"Filialda allaqachon {have} ta demo o'quvchi bor — "
                        "yangisi qo'shilmadi. Avval tozalang."}

    rnd = random.Random(20260823 + branch_id)
    today = roles.local_today()
    made = {"teachers": 0, "groups": 0, "students": 0, "lessons": 0,
            "attendances": 0, "payments": 0, "leads": 0, "users": 0}

    # ---- 1. Ustozlar
    teachers = []
    for i, (gname, subj, *_rest) in enumerate(_GROUPS):
        t = models.Teacher(
            full_name=f"{_FAM[i]} {_ISM_O[i]} {MARK}",
            phone=_phone(rnd), subject=subj, branch_id=branch_id,
            hired_date=today - timedelta(days=200), is_active=1)
        db.add(t); teachers.append(t); made["teachers"] += 1
    db.commit()

    # ---- 2. Guruhlar
    groups = []
    for i, (gname, subj, level, days, tm, fee) in enumerate(_GROUPS):
        g = models.Group(
            name=f"{gname} {MARK}", branch_id=branch_id,
            teacher_id=teachers[i].id, subject=subj, level=level,
            lesson_days=days, lesson_time=tm, monthly_fee=float(fee),
            capacity=25, start_date=today - timedelta(days=120),
            room=f"{i + 1}-xona")
        db.add(g); groups.append(g); made["groups"] += 1
    db.commit()

    # ---- 3. O'quvchilar (holatlari aralash — hayotdagidek)
    need = want - have
    students = []
    for i in range(need):
        fam = rnd.choice(_FAM)
        qiz = rnd.random() < 0.5
        ism = rnd.choice(_ISM_Q if qiz else _ISM_O)
        name = f"{fam}{'a' if qiz else ''} {ism} {MARK}"
        r = rnd.random()
        if r < 0.72:
            status, grp = "active", rnd.choice(groups)
        elif r < 0.82:
            status, grp = "trial", rnd.choice(groups)
        elif r < 0.92:
            status, grp = "frozen", rnd.choice(groups)
        else:
            status, grp = "archived", None
        s = models.Student(
            full_name=name, branch_id=branch_id,
            group_id=grp.id if grp else None, status=status,
            phone=_phone(rnd), parent_phone=_phone(rnd),
            enrolled_date=today - timedelta(days=rnd.randint(20, 300)),
            school=f"{rnd.randint(1, 60)}-maktab",
            school_grade=str(rnd.randint(1, 11)))
        if status == "archived":
            s.left_date = today - timedelta(days=rnd.randint(1, 60))
        db.add(s); students.append((s, grp)); made["students"] += 1
    db.commit()

    # ---- 4. Darslar va yo'qlama (oxirgi 3 hafta)
    for g in groups:
        for d in range(21, 0, -2):
            day = today - timedelta(days=d)
            les = models.Lesson(group_id=g.id, teacher_id=g.teacher_id,
                                date=day, held=1)
            db.add(les); made["lessons"] += 1
    db.commit()

    lessons_by_group = {}
    for les in db.query(models.Lesson).filter(
            models.Lesson.group_id.in_([g.id for g in groups])).all():
        lessons_by_group.setdefault(les.group_id, []).append(les)

    for s, grp in students:
        if not grp or s.status not in ("active", "trial"):
            continue
        for les in lessons_by_group.get(grp.id, [])[:8]:
            db.add(models.Attendance(lesson_id=les.id, student_id=s.id,
                                     present=1 if rnd.random() < 0.85 else 0))
            made["attendances"] += 1
    db.commit()

    # ---- 5. To'lovlar va hisoblar (kimdir to'lagan, kimdir qarzdor)
    methods = ["cash", "card", "terminal"]
    for s, grp in students:
        if not grp or s.status == "archived":
            continue
        fee = float(grp.monthly_fee or 480000)
        for m in (2, 1, 0):
            when = datetime.combine(
                (today.replace(day=1) - timedelta(days=31 * m)), datetime.min.time())
            db.add(models.Payment(
                student_id=s.id, amount=-fee, kind="charge",
                period=f"{when.year:04d}-{when.month:02d}",
                note=f"{when.year:04d}-{when.month:02d} oylik (demo)",
                created_at=when))
            made["payments"] += 1
            paid = rnd.random()
            if paid < 0.75:                       # to'liq to'lagan
                amount = fee
            elif paid < 0.9:                      # yarim to'lagan
                amount = round(fee / 2)
            else:                                 # to'lamagan — qarzdor
                continue
            db.add(models.Payment(
                student_id=s.id, amount=amount, kind="payment",
                method=rnd.choice(methods), note="Demo to'lov",
                created_at=when + timedelta(days=rnd.randint(1, 20))))
            made["payments"] += 1
    db.commit()

    # ---- 6. Lidlar (sotuv menejeri mashq qilsin)
    for i in range(12):
        fam = rnd.choice(_FAM); ism = rnd.choice(_ISM_O + _ISM_Q)
        db.add(models.Lead(
            full_name=f"{fam} {ism} {MARK}", phone=_phone(rnd),
            source=rnd.choice(["instagram", "telegram", "friend", "website"]),
            stage=rnd.choice(["new", "contacted", "trial", "won"]),
            branch_id=branch_id,
            note="Mashq uchun demo lid"))
        made["leads"] += 1
    db.commit()

    # ---- 7. Xodim akkauntlari
    logins = []
    for suffix, full_name, role in _STAFF:
        uname = f"{LOGIN_PREFIX}{suffix}"
        u = db.query(models.User).filter(models.User.username == uname).first()
        if not u:
            u = models.User(username=uname,
                            password_hash=hash_password(DEMO_PASSWORD),
                            full_name=f"{full_name} {MARK}", role=role,
                            branch_id=branch_id, is_active=1)
            db.add(u); made["users"] += 1
        else:
            # parolni tiklab qo'yamiz — kimdir o'zgartirgan bo'lsa
            u.password_hash = hash_password(DEMO_PASSWORD)
            u.branch_id = branch_id
            u.is_active = 1
        logins.append({"login": uname,
                       "role": roles.UZ_LABELS.get(role, role)})
    db.commit()

    total = db.query(models.Student).filter(
        models.Student.branch_id == branch_id,
        models.Student.full_name.like(f"%{MARK}")).count()

    audit.log(db, user, entity="branch", action="demo_seed",
              entity_id=branch_id, entity_label=b.name,
              note=f"Mashq ma'lumoti yaratildi: {made}", branch_id=branch_id,
              commit=True)

    return {"ok": True, "branch": b.name, "created": made,
            "students_total": total, "password": DEMO_PASSWORD,
            "logins": logins,
            "note": "Barcha demo yozuvlar nomida (DEMO) belgisi bor. "
                    "Xodim login'lari demo. bilan boshlanadi."}


@router.delete("/api/demo/seed")
def demo_clear(branch_id: int, db: Session = Depends(get_db),
               user=Depends(require_role(roles.FOUNDER))):
    """MASHQ MA'LUMOTINI TOZALASH — faqat (DEMO) belgili yozuvlar."""
    b = _branch_or_400(db, branch_id)
    like = f"%{MARK}"
    removed = {}

    sids = [r[0] for r in db.query(models.Student.id).filter(
        models.Student.branch_id == branch_id,
        models.Student.full_name.like(like)).all()]
    gids = [r[0] for r in db.query(models.Group.id).filter(
        models.Group.branch_id == branch_id,
        models.Group.name.like(like)).all()]
    lids = [r[0] for r in db.query(models.Lesson.id).filter(
        models.Lesson.group_id.in_(gids or [-1])).all()]

    if sids:
        # O'quvchiga bog'langan hamma narsa (students.py dagi qoida bilan bir xil)
        for table in reversed(models.Base.metadata.sorted_tables):
            if table.name in ("students", "payments_deleted", "audit_logs"):
                continue
            for col in table.columns:
                if col.name != "student_id":
                    continue
                n = db.execute(table.delete().where(col.in_(sids))).rowcount
                if n:
                    removed[table.name] = removed.get(table.name, 0) + n
    if lids:
        n = db.query(models.Lesson).filter(
            models.Lesson.id.in_(lids)).delete(synchronize_session=False)
        removed["lessons"] = n
    if sids:
        n = db.query(models.Student).filter(
            models.Student.id.in_(sids)).delete(synchronize_session=False)
        removed["students"] = n
    if gids:
        n = db.query(models.Group).filter(
            models.Group.id.in_(gids)).delete(synchronize_session=False)
        removed["groups"] = n
    n = db.query(models.Teacher).filter(
        models.Teacher.branch_id == branch_id,
        models.Teacher.full_name.like(like)).delete(synchronize_session=False)
    if n:
        removed["teachers"] = n
    n = db.query(models.Lead).filter(
        models.Lead.branch_id == branch_id,
        models.Lead.full_name.like(like)).delete(synchronize_session=False)
    if n:
        removed["leads"] = n
    n = db.query(models.User).filter(
        models.User.branch_id == branch_id,
        models.User.username.like(f"{LOGIN_PREFIX}%")).delete(
            synchronize_session=False)
    if n:
        removed["users"] = n
    db.commit()

    audit.log(db, user, entity="branch", action="demo_clear",
              entity_id=branch_id, entity_label=b.name,
              note=f"Mashq ma'lumoti tozalandi: {removed}",
              branch_id=branch_id, commit=True)
    return {"ok": True, "removed": removed}
