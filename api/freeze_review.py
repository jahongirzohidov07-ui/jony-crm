"""AVTOMUZLATISHDA YO'QOLGAN YO'QLAMALAR RO'YXATI (2026-10-08).

Jahongir: "kelib turgan o'quvchi yo'qlamasi bilan ochib ketib, yana
muzlab qoldi"; qaror: "avval ro'yxatni ko'rsat" (tiklash keyin, u
ko'rib chiqqach).

Faqat O'QIYDI — hech narsa o'zgartirmaydi. Manba: audit jurnali.
Har yo'qlama o'zgarishi auditga yozilgan ("Ism · Guruh · YYYY-MM-DD",
eski -> yangi qiymat, kim, qachon). Avtomuzlatilgan/sinovdan chiqqan
har o'quvchi uchun: ustoz oxirgi marta nima belgilagan, va o'sha
yozuv hozir bazada bormi. Yo'q bo'lsa — "yo'qolgan".
Qo'shimcha: muzlatilgandan keyin o'tilgan, lekin belgisi umuman yo'q
darslar ("muzlatilgan payt belgilab bo'lmagan").
"""
from datetime import date, datetime, timedelta

from fastapi import Depends
from sqlalchemy.orm import Session

import models
import roles
from main import app, get_db, require_role

_VIEW = (roles.FOUNDER, roles.ACADEMIC_HEAD, roles.HR_MANAGER)
_LBL = {"kelmadi": 0, "keldi": 1, "kech keldi": 2}


def _parse(label: str):
    """"Ism · Guruh · 2026-09-16" -> (guruh, sana)."""
    parts = [p.strip() for p in (label or "").split(" · ")]
    if len(parts) < 3:
        return None, None
    try:
        return " · ".join(parts[1:-1]), date.fromisoformat(parts[-1])
    except ValueError:
        return None, None


def freeze_losses(db: Session, since: date, branch_id=None) -> list:
    A = models.AuditLog
    ev = (db.query(A).filter(A.entity == "student",
                             A.action.in_(("auto_freeze", "trial_dropout")),
                             A.created_at >= datetime.combine(
                                 since, datetime.min.time()))
          .order_by(A.created_at).all())
    # Eski cron tozalashi (muzlatilganlarning zanjiri) ham
    ev += (db.query(A).filter(A.entity == "student", A.action == "update",
                              A.note.like("%yo'qlamasi o'chirildi%"),
                              A.created_at >= datetime.combine(
                                  since, datetime.min.time())).all())
    by_sid: dict = {}
    for e in ev:
        if e.entity_id:
            by_sid.setdefault(e.entity_id, []).append(e)
    if not by_sid:
        return []
    sids = list(by_sid)
    studs = {s.id: s for s in db.query(models.Student).filter(
        models.Student.id.in_(sids)).all()}
    bnames = {b.id: b.name for b in db.query(models.Branch).all()}
    off = timedelta(hours=roles.TIMEZONE_OFFSET_HOURS)
    out = []
    for sid, evs in by_sid.items():
        st = studs.get(sid)
        if not st or (branch_id and st.branch_id != branch_id):
            continue
        marks = (db.query(A).filter(A.entity == "attendance",
                                    A.entity_id == sid,
                                    A.action.in_(("att_mark", "att_remove")))
                 .order_by(A.created_at, A.id).all())
        last: dict = {}
        for m in marks:
            g, d = _parse(m.entity_label)
            if d is None:
                continue
            last[(g, d)] = m
        # Hozir bazadagi yo'qlamalar: (guruh nomi, sana) -> present
        have = {}
        for a, ls, gname in (
                db.query(models.Attendance, models.Lesson, models.Group.name)
                .join(models.Lesson,
                      models.Lesson.id == models.Attendance.lesson_id)
                .join(models.Group, models.Group.id == models.Lesson.group_id)
                .filter(models.Attendance.student_id == sid).all()):
            have[(gname, ls.date)] = a.present
        lost = []
        for (g, d), m in sorted(last.items(), key=lambda kv: kv[0][1]):
            if m.action == "att_remove" or m.new_value not in _LBL:
                continue                      # ustoz o'zi olib tashlagan
            if (g, d) in have:
                continue
            lost.append({"group": g, "date": d.isoformat(),
                         "value": m.new_value, "by": m.user_name,
                         "at": (m.created_at + off).strftime(
                             "%d.%m.%Y %H:%M") if m.created_at else None})
        # Muzlatilgandan keyin belgisiz qolgan o'tilgan darslar
        first_ev = min(e.created_at for e in evs)
        blank = []
        if st.group_id:
            q = (db.query(models.Lesson)
                 .filter(models.Lesson.group_id == st.group_id,
                         models.Lesson.held == 1,
                         models.Lesson.date >= (first_ev + off).date(),
                         models.Lesson.date <= roles.local_today())
                 .order_by(models.Lesson.date).all())
            g_now = st.group.name if st.group else None
            for ls in q:
                if (g_now, ls.date) not in have and \
                        not any(x["date"] == ls.date.isoformat()
                                for x in lost):
                    blank.append(ls.date.isoformat())
        if not lost and not blank:
            continue
        out.append({
            "student_id": sid, "full_name": st.full_name,
            "status": st.status,
            "group": st.group.name if st.group else None,
            "branch": bnames.get(st.branch_id),
            "events": [{"at": (e.created_at + off).strftime("%d.%m.%Y %H:%M"),
                        "kind": e.action, "note": e.note}
                       for e in sorted(evs, key=lambda e: e.created_at)],
            "lost": lost,
            "lost_present": sum(1 for x in lost if x["value"] != "kelmadi"),
            "blank": blank,
        })
    out.sort(key=lambda r: (-r["lost_present"], -len(r["lost"]),
                            r["full_name"]))
    return out


@app.get("/api/attendance/freeze-losses")
def freeze_losses_route(since: str | None = None,
                        branch_id: int | None = None,
                        db: Session = Depends(get_db),
                        user=Depends(require_role(*_VIEW))):
    try:
        d0 = date.fromisoformat(since) if since else date(2026, 8, 1)
    except ValueError:
        d0 = date(2026, 8, 1)
    rows = freeze_losses(db, d0, branch_id)
    return {"since": d0.isoformat(), "rows": rows,
            "students": len(rows),
            "lost": sum(len(r["lost"]) for r in rows),
            "lost_present": sum(r["lost_present"] for r in rows),
            "blank": sum(len(r["blank"]) for r in rows)}
