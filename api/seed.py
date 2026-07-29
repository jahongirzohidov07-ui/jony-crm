"""Local test data only. Names below are placeholders, NOT real students.
Run once: python seed.py
Before any real deployment, delete this data and create real accounts with
strong, unique passwords (and change JONY_CRM_SECRET env var)."""

from datetime import date

from database import Base, SessionLocal, engine
import models
import roles
from auth import hash_password

Base.metadata.create_all(bind=engine)
db = SessionLocal()

if db.query(models.Branch).count() == 0:
    b1 = models.Branch(name="Filial 1 (namuna)", address="Bekobod")
    b2 = models.Branch(name="Filial 2 (namuna)", address="Bekobod")
    db.add_all([b1, b2])
    db.commit()
else:
    b1, b2 = db.query(models.Branch).order_by(models.Branch.id).all()[:2]

if db.query(models.User).count() == 0:
    test_pw = hash_password("ChangeMe123!")
    db.add_all([
        models.User(username="admin", password_hash=test_pw, full_name="Administrator (test)",
                    role=roles.ADMINISTRATOR, branch_id=None),
        models.User(username="filial1", password_hash=test_pw, full_name="Filial Menejeri (test)",
                    role=roles.BRANCH_MANAGER, branch_id=b1.id),
        models.User(username="teacher1", password_hash=test_pw, full_name="O'qituvchi (test)",
                    role=roles.TEACHER, branch_id=b1.id),
        models.User(username="hr1", password_hash=test_pw, full_name="HR Manager (test)",
                    role=roles.HR_MANAGER, branch_id=None),
        models.User(username="smm1", password_hash=test_pw, full_name="SMM Manager (test)",
                    role=roles.SMM_MANAGER, branch_id=None),
    ])
    db.commit()
    print("Test foydalanuvchilar yaratildi (barchasi parol: ChangeMe123!):")
    print("  admin / filial1 / teacher1 / hr1 / smm1")

if db.query(models.Teacher).count() == 0:
    t1 = models.Teacher(full_name="Test Ustoz Bir", phone="+998901234567", subject="Matematika", branch_id=b1.id)
    t2 = models.Teacher(full_name="Test Ustoz Ikki", phone="+998901234568", subject="Ingliz tili", branch_id=b2.id)
    db.add_all([t1, t2])
    db.commit()

    # lesson_price=40 000, standard_lessons_per_month=12 -> standart oy = 480 000.
    # teacher_rate_per_student=100 000 - ustoz bitta o'quvchidan to'liq yoqlama
    # qo'ysa shuncha oladi (Jahongirning aytgan namunasi).
    g1 = models.Group(
        name="IELTS 1.0 (namuna)", room="1-xona", teacher_id=t1.id, branch_id=b1.id,
        monthly_fee=480000, lesson_price=40000, standard_lessons_per_month=12,
        teacher_rate_per_student=100000,
    )
    g2 = models.Group(
        name="IELTS 2.0 (namuna)", room="2-xona", teacher_id=t2.id, branch_id=b2.id,
        monthly_fee=480000, lesson_price=40000, standard_lessons_per_month=12,
        teacher_rate_per_student=100000,
    )
    db.add_all([g1, g2])
    db.commit()

    st1 = models.Student(
        full_name="Namuna O'quvchi 1", phone="+998900000001", parent_phone="+998900000011",
        enrolled_date=date.today(), group_id=g1.id, branch_id=b1.id, status="active",
    )
    st2 = models.Student(
        full_name="Namuna O'quvchi 2", phone="+998900000002", parent_phone="+998900000012",
        enrolled_date=date.today(), group_id=g2.id, branch_id=b2.id, status="active",
    )
    db.add_all([st1, st2])
    db.commit()

    db.add_all([
        models.Payment(student_id=st1.id, amount=-480000, kind="charge", note="Iyul oyi to'lovi", created_by="Tizim"),
        models.Payment(student_id=st1.id, amount=480000, kind="payment", note="Naqd to'lov", created_by="admin"),
        models.Payment(student_id=st2.id, amount=-480000, kind="charge", note="Iyul oyi to'lovi", created_by="Tizim"),
    ])
    db.commit()
    print("Namuna filial/guruh/o'quvchi/to'lov yozuvlari yaratildi.")

db.close()
print("Seed tugadi.")
