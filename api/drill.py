"""MASHQ (admin tayyorgarligi) — 2026-09-25.

Jahongir: "admin akkauntiga shularni qilib vaqt ichida vazifa
topshiradigan funksiya qo'shsa bo'ladimi ... test filial yaratganmiz
shu filialga kirib mashq degan bo'lim ochiladi faqat adminlarga start
bossa vazifa bersin vazifalarni bajarib keyingi bosqichga o'taversin".

QANDAY ISHLAYDI
  1. Admin SINOV filialida turgan bo'lishi kerak (Branch.is_test).
     Haqiqiy filialda mashq boshlanmaydi — aks holda soxta o'quvchi,
     soxta to'lov haqiqiy bazaga tushib ketardi.
  2. "Boshlash" bosiladi: birinchi vazifa va sekundomer chiqadi.
  3. Admin vazifani TIZIMNING O'ZIDA bajaradi, keyin "Bajardim"
     bosadi. Server tekshiradi:
       - "row"   — o'sha jadvalda YANGI yozuv paydo bo'ldimi
                   (to'lov, o'quvchi, guruh, lid, vazifa...);
       - "audit" — audit jurnalida mos amal bormi (muzlatish,
                   guruhdan o'tkazish, coin, parol...);
       - "view"  — ko'rish vazifasi, tekshirib bo'lmaydi (bo'limni
                   ochib ko'rsatish) — admin o'zi tasdiqlaydi.
     Tekshiruvdan o'tmasa vazifa YOPILMAYDI.
  4. Vaqt SERVER soatidan o'lchanadi (brauzer soatini o'zgartirib
     aldab bo'lmaydi). Vaqtdan oshsa ham keyingi bosqichga o'tiladi,
     lekin o'sha band "vaqtdan oshdi" deb belgilanadi.

HR SOZLAYDI: har bandning soniyasi, nomi va tartibi HR bo'limidan
o'zgartiriladi (roles.DRILL_MANAGE).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

import audit
import models
import roles
from auth import require_role
from database import get_db
from common import _in_user_branches, _seed_done, _seed_mark  # noqa: F401

router = APIRouter()

# =====================================================================
#  RO'YXAT (boshlang'ich). HR keyin o'zgartiradi — bu faqat birinchi
#  to'ldirish uchun. Soniyalar Jahongirning ro'yxatidan olingan,
#  lekin real tezlikka moslab qayta o'lchandi: sahifa ochilishi va
#  forma to'ldirish hisobga olindi (2026-09-25).
#
#  kind: row | audit | view
# =====================================================================
SEED = [
    ("intro", "Bosh sahifa: bugungi holatni ko'rsating", 30, "view",
     None, None, None, "Dashboard — bugungi darslar, to'lovlar, qarzdorlar"),
    ("timetable", "Dars jadvalini oching va tushuntiring", 30, "view",
     None, None, None, "Dars jadvali bo'limi"),
    ("find_student", "Qidiruvdan o'quvchini toping", 25, "view",
     None, None, None, "Tepadagi qidiruv yoki Talabalar ro'yxati"),
    ("lead_add", "Lidlar bo'limiga yangi lid qo'shing", 45, "row",
     "leads", None, None, "Lidlar → Yangi lid"),
    ("student_add", "Lidni o'quvchiga aylantiring", 60, "row",
     "students", None, None,
     "JonyOS da o'quvchi FAQAT liddan ochiladi: lid kartasi → "
     "O'quvchiga aylantirish"),
    ("group_create", "Yangi guruh oching", 60, "row",
     "groups", None, None, "Guruhlar → Yangi guruh"),
    ("filter", "Guruhlar va talabalarni filtrlang", 30, "view",
     None, None, None, "Filial, holat, ustoz bo'yicha saralash"),
    ("payment_add", "O'quvchiga to'lov kiriting", 60, "row",
     "payments", None, None, "O'quvchi kartasi → To'lovlar → To'lov qo'shish"),
    ("payment_add2", "Ikkinchi to'lovni kassadan kiriting", 45, "row",
     "payments", None, None, "Moliya → Kassa (tepadagi tez to'lov)"),
    ("payment_history", "To'lovlar tarixini oching", 25, "view",
     None, None, None, "O'quvchi kartasi → To'lovlar"),
    ("refund", "To'lovni qaytaring (refund)", 60, "audit",
     None, "payment", "refund,delete,amount_edit,update", "To'lovni qaytarish"),
    ("trial_activate", "Sinov darsidagi o'quvchini faollashtiring", 45,
     "audit", None, "student", "activate", "Sinov → Faol"),
    ("freeze", "O'quvchini muzlating", 40, "audit",
     None, "student", "freeze", "O'quvchi kartasi → Muzlatish"),
    ("unfreeze", "Muzlatilgan o'quvchini qayta faollashtiring", 30,
     "audit", None, "student", "activate", "Muzlatishdan chiqarish"),
    ("attendance", "Guruh davomatini belgilang", 40, "audit",
     None, "attendance", "att_mark", "Guruh → Davomat"),
    ("comment", "O'quvchiga izoh yozing", 40, "row",
     "comments", None, None, "O'quvchi kartasi → Izoh"),
    ("group_move", "O'quvchini boshqa guruhga o'tkazing", 60, "audit",
     None, "student", "group_move,group_remove", "Guruhdan chiqarish/o'tkazish"),
    ("discount", "Chegirma o'rnating", 45, "row",
     "discounts", None, None, "O'quvchi kartasi → Narx va chegirma"),
    ("task_create", "Xodimga vazifa qo'ying", 45, "row",
     "tasks", None, None, "Vazifalar → Yangi vazifa"),
    ("coins", "O'quvchiga coin qo'shing yoki ayiring", 45, "audit",
     None, "student", "update", "Coin hisoboti → Qo'lda coin"),
    ("reward", "Coinga olingan sovg'ani o'quvchiga biriktiring", 45,
     "audit", None, "reward", "update,create", "Coin do'koni"),
    ("password", "Profil parolini o'zgartiring", 45, "audit",
     None, "user", "update,password", "Profil → Parolni o'zgartirish"),
    ("debtors", "Qarzdorlar bo'limini oching", 25, "view",
     None, None, None, "Qarzdorlar ro'yxati"),
    ("archive", "Arxiv bo'limini oching", 25, "view",
     None, None, None, "Arxiv — ketgan o'quvchilar"),
    ("group_archive", "Guruh arxivini oching", 25, "view",
     None, None, None, "Guruhlar → Arxivdagilar"),
    ("courses", "Kurslar bo'limini oching", 25, "view",
     None, None, None, "Kurslar va narxlar"),
    ("rooms", "Xona sig'imini belgilang", 30, "row",
     "rooms", None, None, "Filiallar → Xonalar"),
]

_TABLES = {
    "students": models.Student, "leads": models.Lead,
    "groups": models.Group, "payments": models.Payment,
    "discounts": models.Discount, "tasks": models.Task,
    "rooms": models.Room, "courses": models.Course,
}
try:
    _TABLES["comments"] = models.Comment
except AttributeError:      # izohlar boshqa nom bilan bo'lsa
    pass


def seed_tasks(db: Session) -> None:
    """Ro'yxat bir marta yoziladi; keyin HR tahrirlaydi."""
    if _seed_done(db, "drill_tasks_v1"):
        return
    try:
        for i, (key, title, sec, kind, table, ent, act, hint) in enumerate(
                SEED):
            if db.query(models.DrillTask).filter(
                    models.DrillTask.key == key).first():
                continue
            db.add(models.DrillTask(
                key=key, order_no=i + 1, title=title, hint=hint,
                seconds=sec, verify_kind=kind, verify_table=table,
                verify_entity=ent, verify_action=act, is_active=1))
        db.commit()
        _seed_mark(db, "drill_tasks_v1")
    except Exception:
        db.rollback()


# ------------------------------------------------------------ yordamchi
def _test_list(db: Session):
    return (db.query(models.Branch)
            .filter(models.Branch.is_test == 1)
            .order_by(models.Branch.name).all())


def _pick_branch(db: Session, user, branch_id=None):
    """Mashq qaysi filialda ketadi.

    Tanlagichdan filial berilgan bo'lsa (tepadagi filial tanlagichi
    GET so'rovlarga branch_id qo'shadi) va foydalanuvchi o'sha
    filialda ishlay olsa — o'sha; aks holda o'zining filiali.
    2026-09-25: ilgari faqat user.branch_id qaralardi, shuning uchun
    filiali boshqa joyda turgan admin "Mashq" ni ocholmasdi va sabab
    ham tushunarsiz edi."""
    b = None
    if branch_id:
        cand = db.query(models.Branch).get(int(branch_id))
        if cand is not None and _in_user_branches(db, user, cand.id):
            b = cand
    if b is None and user.branch_id:
        b = db.query(models.Branch).get(user.branch_id)
    return b


def _test_branch(db: Session, user, branch_id=None) -> models.Branch:
    """Mashq faqat SINOV filialida. Aks holda soxta yozuvlar haqiqiy
    hisobotlarga tushib ketardi."""
    b = _pick_branch(db, user, branch_id)
    if b is not None and b.is_test:
        return b
    tests = _test_list(db)
    if not tests:
        raise HTTPException(
            400, "Sinov filiali belgilanmagan. HR bo'limi → Admin "
                 "mashqi bo'limidan qaysi filial sinov ekanini "
                 "belgilang.")
    names = ", ".join(t.name for t in tests)
    raise HTTPException(
        400, f"Mashq faqat sinov filialida ishlaydi ({names}). "
             f"Hozir siz "
             f"\"{b.name if b else 'filialsiz'}\" da turibsiz. "
             f"Tepadagi tanlagichdan sinov filialiga o'ting; agar "
             f"tanlagich bo'lmasa, HR akkauntingizni sinov filialiga "
             f"o'tkazishi kerak.")


def _tasks(db: Session):
    return (db.query(models.DrillTask)
            .filter(models.DrillTask.is_active == 1)
            .order_by(models.DrillTask.order_no,
                      models.DrillTask.id).all())


def _task_out(t) -> dict:
    return {
        "id": t.id, "key": t.key, "order_no": t.order_no,
        "title": t.title, "hint": t.hint, "seconds": t.seconds,
        "verify_kind": t.verify_kind,
        "verify_label": {"row": "Yangi yozuv tekshiriladi",
                         "audit": "Amal tarixdan tekshiriladi",
                         "view": "Ko'rish — o'zingiz tasdiqlaysiz"}
        .get(t.verify_kind, t.verify_kind),
        "is_active": bool(t.is_active),
    }


def _snapshot(db: Session, task, branch_id: int) -> Optional[int]:
    """"row" turidagi vazifa uchun: jadvaldagi eng katta id."""
    m = _TABLES.get(task.verify_table or "")
    if m is None:
        return None
    q = db.query(models.func.max(m.id)) if hasattr(models, "func") else None
    from sqlalchemy import func as _f
    val = db.query(_f.max(m.id)).scalar()
    return int(val or 0)


def _verify(db: Session, step, task, user, branch_id: int) -> bool:
    if task.verify_kind == "view":
        return True
    if task.verify_kind == "row":
        m = _TABLES.get(task.verify_table or "")
        if m is None:
            return True
        q = db.query(m).filter(m.id > (step.snapshot_id or 0))
        if hasattr(m, "branch_id"):
            q = q.filter(m.branch_id == branch_id)
        return db.query(q.exists()).scalar()
    # audit
    acts = [a.strip() for a in (task.verify_action or "").split(",")
            if a.strip()]
    q = (db.query(models.AuditLog)
         .filter(models.AuditLog.user_id == user.id,
                 models.AuditLog.created_at >= step.started_at))
    if task.verify_entity:
        q = q.filter(models.AuditLog.entity == task.verify_entity)
    if acts:
        q = q.filter(models.AuditLog.action.in_(acts))
    if task.verify_field:
        q = q.filter(models.AuditLog.field == task.verify_field)
    return db.query(q.exists()).scalar()


def _step_out(db: Session, step) -> dict:
    t = db.query(models.DrillTask).get(step.task_id)
    return {
        "id": step.id, "task_id": step.task_id,
        "order_no": step.order_no,
        "title": t.title if t else "—",
        "hint": t.hint if t else None,
        "seconds": t.seconds if t else 0,
        "verify_kind": t.verify_kind if t else "view",
        "started_at": step.started_at.isoformat() if step.started_at else None,
        "done_at": step.done_at.isoformat() if step.done_at else None,
        "spent": step.spent,
        "ok": bool(step.ok),
        "skipped": bool(step.skipped),
        "in_time": bool(step.ok) and not step.skipped
        and t is not None and (step.spent or 0) <= t.seconds,
    }


def _attempt_out(db: Session, a) -> dict:
    steps = (db.query(models.DrillStep)
             .filter(models.DrillStep.attempt_id == a.id)
             .order_by(models.DrillStep.order_no).all())
    rows = [_step_out(db, s) for s in steps]
    u = db.query(models.User).get(a.user_id)
    return {
        "id": a.id, "user_id": a.user_id,
        "user": u.full_name if u else None,
        "status": a.status,
        "started_at": a.started_at.isoformat() if a.started_at else None,
        "finished_at": (a.finished_at.isoformat()
                        if a.finished_at else None),
        "steps": rows,
        "total": len(rows),
        "done": sum(1 for r in rows if r["ok"]),
        "in_time": sum(1 for r in rows if r["in_time"]),
        "spent": sum(r["spent"] or 0 for r in rows),
    }


def _current(db: Session, a):
    return (db.query(models.DrillStep)
            .filter(models.DrillStep.attempt_id == a.id,
                    models.DrillStep.done_at.is_(None))
            .order_by(models.DrillStep.order_no).first())


def _running(db: Session, user):
    return (db.query(models.DrillAttempt)
            .filter(models.DrillAttempt.user_id == user.id,
                    models.DrillAttempt.status == "running")
            .order_by(models.DrillAttempt.id.desc()).first())


# ------------------------------------------------------------ admin
@router.get("/api/drill/state")
def drill_state(branch_id: int | None = None,
                db: Session = Depends(get_db),
                user=Depends(require_role(*roles.DRILL_TAKE))):
    """Mashq sahifasi: hozirgi urinish, vazifa va o'tgan natijalar."""
    seed_tasks(db)
    b = _pick_branch(db, user, branch_id)
    a = _running(db, user)
    cur = _current(db, a) if a else None
    if cur is not None:
        t = db.query(models.DrillTask).get(cur.task_id)
        left = (t.seconds if t else 0) - int(
            (datetime.utcnow() - cur.started_at).total_seconds())
    else:
        left = None
    past = (db.query(models.DrillAttempt)
            .filter(models.DrillAttempt.user_id == user.id,
                    models.DrillAttempt.status != "running")
            .order_by(models.DrillAttempt.id.desc()).limit(5).all())
    tasks = _tasks(db)
    tests = _test_list(db)
    return {
        "can_start": bool(b and b.is_test) and bool(tasks),
        "test_branch": bool(b and b.is_test),
        "branch": b.name if b else None,
        "test_branches": [{"id": t.id, "name": t.name} for t in tests],
        "why": (None if (b and b.is_test) else
                ("Sinov filiali belgilanmagan — HR bo'limi → Admin "
                 "mashqi dan belgilang."
                 if not tests else
                 f"Siz \"{b.name if b else 'filialsiz'}\" da "
                 f"turibsiz. Mashq uchun sinov filialiga o'ting: "
                 + ", ".join(t.name for t in tests))),
        "tasks": [_task_out(t) for t in tasks],
        "attempt": _attempt_out(db, a) if a else None,
        "current": _step_out(db, cur) if cur is not None else None,
        "left": left,
        "now": datetime.utcnow().isoformat(),
        "history": [_attempt_out(db, x) for x in past],
        "hint": ("Vazifani tizimning o'zida bajaring, so'ng "
                 "\"Bajardim\" bosing — tizim tekshiradi. Vaqt "
                 "tugasa ham keyingi bosqichga o'tasiz, lekin o'sha "
                 "band \"vaqtdan oshdi\" bo'lib qoladi."),
    }


@router.post("/api/drill/start")
def drill_start(branch_id: int | None = None,
                db: Session = Depends(get_db),
                user=Depends(require_role(*roles.DRILL_TAKE))):
    seed_tasks(db)
    b = _test_branch(db, user, branch_id)
    old = _running(db, user)
    if old is not None:
        old.status = "stopped"
        old.finished_at = datetime.utcnow()
    tasks = _tasks(db)
    if not tasks:
        raise HTTPException(400, "Mashq ro'yxati bo'sh")
    a = models.DrillAttempt(user_id=user.id, branch_id=b.id,
                            status="running", started_at=datetime.utcnow())
    db.add(a)
    db.commit()
    db.refresh(a)
    first = tasks[0]
    st = models.DrillStep(
        attempt_id=a.id, task_id=first.id, order_no=1,
        started_at=datetime.utcnow(),
        snapshot_id=_snapshot(db, first, b.id))
    db.add(st)
    db.commit()
    audit.log(db, user, entity="drill", action="start", entity_id=a.id,
              entity_label=b.name, branch_id=b.id, commit=True)
    return drill_state(branch_id=b.id, db=db, user=user)


class DoneIn(BaseModel):
    skip: bool = False


@router.post("/api/drill/done")
def drill_done(payload: DoneIn = Body(default=DoneIn()),
               db: Session = Depends(get_db),
               user=Depends(require_role(*roles.DRILL_TAKE))):
    """Vazifani yopish: tekshiriladi, so'ng keyingisi beriladi."""
    a = _running(db, user)
    if a is None:
        raise HTTPException(400, "Mashq boshlanmagan")
    cur = _current(db, a)
    if cur is None:
        raise HTTPException(400, "Bajarilmagan vazifa yo'q")
    t = db.query(models.DrillTask).get(cur.task_id)
    ok = True if payload.skip else _verify(db, cur, t, user, a.branch_id)
    if not ok:
        return {
            "ok": False,
            "message": ("Bu vazifa bajarilgani ko'rinmadi. Tizimda "
                        "amalni bajaring, so'ng qaytadan \"Bajardim\" "
                        "bosing."),
            **drill_state(branch_id=a.branch_id, db=db, user=user),
        }
    now = datetime.utcnow()
    cur.done_at = now
    cur.spent = int((now - cur.started_at).total_seconds())
    cur.ok = 0 if payload.skip else 1
    cur.skipped = 1 if payload.skip else 0
    db.commit()

    tasks = _tasks(db)
    nxt = None
    for i, x in enumerate(tasks):
        if x.id == t.id and i + 1 < len(tasks):
            nxt = tasks[i + 1]
            break
    if nxt is None:
        a.status = "done"
        a.finished_at = now
        db.commit()
        audit.log(db, user, entity="drill", action="finish", entity_id=a.id,
                  new_value=f"{sum(1 for s in db.query(models.DrillStep).filter(models.DrillStep.attempt_id == a.id).all() if s.ok)} ta",
                  branch_id=a.branch_id, commit=True)
    else:
        db.add(models.DrillStep(
            attempt_id=a.id, task_id=nxt.id, order_no=cur.order_no + 1,
            started_at=datetime.utcnow(),
            snapshot_id=_snapshot(db, nxt, a.branch_id)))
        db.commit()
    return {"ok": True,
            **drill_state(branch_id=a.branch_id, db=db, user=user)}


@router.post("/api/drill/stop")
def drill_stop(db: Session = Depends(get_db),
               user=Depends(require_role(*roles.DRILL_TAKE))):
    a = _running(db, user)
    if a is None:
        raise HTTPException(400, "Mashq boshlanmagan")
    a.status = "stopped"
    a.finished_at = datetime.utcnow()
    db.commit()
    return drill_state(branch_id=a.branch_id, db=db, user=user)


# --------------------------------------------------------------- HR
@router.get("/api/drill/admin")
def drill_admin(db: Session = Depends(get_db),
                user=Depends(require_role(*roles.DRILL_MANAGE))):
    """HR: vazifalar ro'yxati, soniyalari va kim qanday topshirgani."""
    seed_tasks(db)
    tasks = (db.query(models.DrillTask)
             .order_by(models.DrillTask.order_no,
                       models.DrillTask.id).all())
    att = (db.query(models.DrillAttempt)
           .order_by(models.DrillAttempt.id.desc()).limit(50).all())
    return {
        "tasks": [_task_out(t) for t in tasks],
        "total_seconds": sum(t.seconds for t in tasks if t.is_active),
        "attempts": [_attempt_out(db, a) for a in att],
        "branches": [{"id": b.id, "name": b.name, "is_test": bool(b.is_test)}
                     for b in db.query(models.Branch)
                     .order_by(models.Branch.name).all()],
        "hint": ("Soniyani real tezlikka qarab qo'ying: sahifa "
                 "ochilishi ham vaqt oladi. Mashq faqat SINOV deb "
                 "belgilangan filialda ishlaydi."),
    }


class TaskIn(BaseModel):
    title: Optional[str] = None
    hint: Optional[str] = None
    seconds: Optional[int] = None
    order_no: Optional[int] = None
    is_active: Optional[bool] = None


@router.put("/api/drill/tasks/{tid}")
def drill_task_edit(tid: int, payload: TaskIn,
                    db: Session = Depends(get_db),
                    user=Depends(require_role(*roles.DRILL_MANAGE))):
    t = db.query(models.DrillTask).get(tid)
    if not t:
        raise HTTPException(404, "Vazifa topilmadi")
    old = t.seconds
    if payload.title is not None:
        t.title = payload.title.strip() or t.title
    if payload.hint is not None:
        t.hint = payload.hint
    if payload.seconds is not None:
        if not (5 <= payload.seconds <= 600):
            raise HTTPException(400, "Soniya 5 dan 600 gacha bo'lsin")
        t.seconds = payload.seconds
    if payload.order_no is not None:
        t.order_no = payload.order_no
    if payload.is_active is not None:
        t.is_active = 1 if payload.is_active else 0
    t.updated_by = user.full_name
    t.updated_at = datetime.utcnow()
    db.commit()
    audit.log(db, user, entity="drill_task", action="update", entity_id=t.id,
              entity_label=t.title, field="soniya",
              old_value=old, new_value=t.seconds, commit=True)
    return _task_out(t)


class BranchTestIn(BaseModel):
    is_test: bool


@router.put("/api/drill/branches/{bid}")
def drill_branch_flag(bid: int, payload: BranchTestIn,
                      db: Session = Depends(get_db),
                      user=Depends(require_role(*roles.DRILL_MANAGE))):
    """Filialni SINOV deb belgilash. Mashq faqat shunday filialda
    ishlaydi — haqiqiy filialda soxta yozuv paydo bo'lmaydi."""
    b = db.query(models.Branch).get(bid)
    if not b:
        raise HTTPException(404, "Filial topilmadi")
    b.is_test = 1 if payload.is_test else 0
    db.commit()
    audit.log(db, user, entity="branch", action="update", entity_id=b.id,
              entity_label=b.name, field="sinov filiali",
              new_value=("ha" if b.is_test else "yo'q"), commit=True)
    return {"ok": True, "id": b.id, "is_test": bool(b.is_test)}
