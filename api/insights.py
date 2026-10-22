"""BO'LIM STATISTIKASI — /api/insights/{section} (2026-10-22).

Jahongir: "dars jadvali, support jadvali, talabalar, guruhlar,
o'qituvchilar, kutubxona, xodimlar, namunali xodim, audit, ombor,
tadbirlar, shaxsiy rivojlanish" — "premium dizayn + grafiklar".

Har bo'lim sahifasi tepasida rangli ko'rsatkichlar va bar chartlar
(src/components/SectionInsights.tsx). Javob:
    {"cards": [{key, label, value, hint?, tone?, icon?}],
     "charts": [{key, title, sub?, type: hbar|bar|donut|grouped,
                 rows: [{label, value, ...}], series?, span?}]}

QOIDALAR:
  · faqat SANOQ — ism, telefon, summa tafsiloti yo'q (namunali va
    xodimlar bo'limida ism — o'sha sahifaning o'zida ham ko'rinadi);
  · filial cheklovi common.scope_to_branch bilan — filialga bog'langan
    xodim faqat o'z filiallarini, hamkor/test filial yig'indiga kirmaydi;
  · ruxsat bo'limning o'z ro'yxatiga mos; ruxsat yo'q — 403 (sahifa
    statistikasiz ishlayveradi);
  · bitta yig'uvchi xato bersa ham sahifa buzilmaydi — 500 o'rniga
    bo'sh javob.
"""
from collections import Counter
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import models
import roles
from auth import get_current_user
from database import get_db
from common import scope_to_branch

router = APIRouter()

OY = ["", "Yan", "Fev", "Mar", "Apr", "May", "Iyun", "Iyul", "Avg", "Sen",
      "Okt", "Noy", "Dek"]
HAFTA = ["Du", "Se", "Ch", "Pa", "Ju", "Sh", "Ya"]

STAFF = None  # barcha xodimlar (tashqi rollardan tashqari)
MANAGERS = [roles.FOUNDER, roles.BRANCH_MANAGER, roles.HR_MANAGER,
            roles.ACADEMIC_HEAD, roles.HEAD_SUPPORT]

ACCESS = {
    "hr": list(roles.HR_FULL),
    "timetable": STAFF,
    "support": roles.FULL_ACCESS + [roles.HEAD_SUPPORT, roles.ACADEMIC_HEAD,
                                    roles.HR_MANAGER],
    "students": STAFF,
    "groups": STAFF,
    "teachers": STAFF,
    "library": STAFF,
    "development": STAFF,
    "users": list(roles.STAFF_VIEWERS) + [roles.HEAD_SUPPORT],
    "namunali": list(roles.CONDUCT_VIEW) + [roles.FOUNDER],
    "audit": [roles.FOUNDER, roles.BRANCH_MANAGER, roles.HR_MANAGER],
    "inventory": list(roles.INVENTORY_VIEW),
    "events": list(roles.EVENTS_ACCESS),
}


# KARTA BOSILSA — SHU BO'LIMGA (2026-10-22, Jahongir: "statistika
# ustiga bossa shu bo'limga borsin"). Har bo'limning sahifasi; ba'zi
# kartalar kerakli filtr/tab bilan ochiladi.
HOME = {
    "hr": "/hr", "timetable": "/timetable", "support": "/support-schedule",
    "students": "/students", "groups": "/groups", "teachers": "/teachers",
    "library": "/library", "development": "/development", "users": "/users",
    "namunali": "/namunali", "audit": "/audit", "inventory": "/inventory",
    "events": "/events",
}
LINKS = {
    ("students", "active"): "/students?status=active",
    ("students", "trial"): "/students?status=trial",
    ("students", "frozen"): "/students?status=frozen",
    ("hr", "staff"): "/hr?tab=staff",
    ("hr", "vac"): "/hr?tab=hrvacancies",
    ("hr", "apps"): "/hr?tab=ats",
    ("hr", "turn"): "/hr?tab=exited",
    ("users", "left"): "/hr?tab=exited",
    ("users", "bday"): "/events",
}


# ------------------------------------------------------------ yordamchi
def card(key, label, value, icon=None, tone=None, hint=None):
    return {"key": key, "label": label, "value": value, "icon": icon,
            "tone": tone, "hint": hint}


def chart(key, title, rows, type="hbar", sub=None, span=1, series=None,
          unit=None):
    return {"key": key, "title": title, "sub": sub, "type": type,
            "rows": rows, "span": span, "series": series, "unit": unit}


def top(counter: Counter, labels=None, n=10, other=True) -> list:
    """Counter -> [{label, value}] kamayish tartibida; qolgani "Boshqa"."""
    items = [(k, v) for k, v in counter.most_common() if v]
    head, tail = items[:n], items[n:]
    rows = [{"label": (labels or {}).get(k, k) if k not in (None, "")
             else "Ko'rsatilmagan", "value": v} for k, v in head]
    if other and tail:
        rows.append({"label": "Boshqa", "value": sum(v for _k, v in tail)})
    return rows


def num(x):
    """5.0 -> 5, 5.5 -> 5.5 (kartada ortiqcha ".0" ko'rinmasin)."""
    x = round(float(x or 0), 1)
    return int(x) if x == int(x) else x


def money(x) -> str:
    x = float(x or 0)
    if abs(x) >= 1e9:
        return f"{x / 1e9:.1f} mlrd"
    if abs(x) >= 1e6:
        return f"{x / 1e6:.1f} mln"
    if abs(x) >= 1e3:
        return f"{x / 1e3:.0f} ming"
    return f"{x:.0f}"


def months_back(today: date, n: int = 6) -> list:
    out, y, m = [], today.year, today.month
    for _ in range(n):
        out.append((y, m))
        y, m = (y, m - 1) if m > 1 else (y - 1, 12)
    return list(reversed(out))


def ym(d) -> tuple | None:
    if d is None:
        return None
    if isinstance(d, datetime):
        d = d.date()
    return (d.year, d.month)


def branch_names(db) -> dict:
    return {b.id: b.name for b in db.query(models.Branch).all()}


def is_staff(user) -> bool:
    return user.role not in tuple(roles.EXTERNAL_ROLES)


def scoped(db, user, model, branch_id, q=None):
    return scope_to_branch(q if q is not None else db.query(model), model,
                           user, branch_id)


def staff_users(db, user, branch_id, active_only=True):
    q = db.query(models.User).filter(
        models.User.role.notin_(tuple(roles.EXTERNAL_ROLES)))
    if active_only:
        q = q.filter(models.User.is_active == 1)
    return scoped(db, user, models.User, branch_id, q).all()


def active_groups(db, user, branch_id):
    q = db.query(models.Group).filter(models.Group.archived_at.is_(None))
    return scoped(db, user, models.Group, branch_id, q).all()


def group_counts(db, gids) -> Counter:
    """Har guruhdagi faol o'quvchilar (ko'p fanli bog'lanishlar bilan)."""
    c: Counter = Counter()
    if not gids:
        return c
    L = getattr(models, "StudentGroupLink", None)
    if L is not None:
        rows = (db.query(L.group_id, L.student_id)
                .join(models.Student, models.Student.id == L.student_id)
                .filter(L.group_id.in_(gids), L.active == 1,
                        models.Student.status == "active").all())
        seen = set()
        for gid, sid in rows:
            if (gid, sid) not in seen:
                seen.add((gid, sid))
                c[gid] += 1
    if not c:
        for gid, in (db.query(models.Student.group_id)
                     .filter(models.Student.group_id.in_(gids),
                             models.Student.status == "active").all()):
            c[gid] += 1
    return c


_TNAME: dict = {}   # o'qituvchi ismlari — har so'rov boshida tozalanadi


def teacher_name(db, tid):
    if tid not in _TNAME:
        t = db.query(models.Teacher).get(tid) if tid else None
        _TNAME[tid] = t.full_name if t else "—"
    return _TNAME[tid]


# ------------------------------------------------------------ bo'limlar
def _students(db, user, bid, today):
    S = models.Student
    rows = scoped(db, user, S, bid).with_entities(
        S.status, S.branch_id, S.subject, S.level, S.enrolled_date,
        S.created_at, S.left_date).all()
    st = Counter(r.status for r in rows)
    month = (today.year, today.month)
    new_m = sum(1 for r in rows
                if ym(r.enrolled_date or r.created_at) == month)
    left_m = sum(1 for r in rows if ym(r.left_date) == month
                 and r.status in ("left", "archived"))
    live = [r for r in rows if r.status in ("active", "trial", "frozen")]
    bn = branch_names(db)
    flow = []
    for y, m in months_back(today):
        flow.append({"label": f"{OY[m]} {str(y)[2:]}",
                     "new": sum(1 for r in rows
                                if ym(r.enrolled_date or r.created_at) == (y, m)),
                     "left": sum(1 for r in rows if ym(r.left_date) == (y, m)
                                 and r.status in ("left", "archived"))})
    return [
        card("active", "Faol o'quvchilar", st.get("active", 0), "users", "indigo"),
        card("trial", "Sinov darsida", st.get("trial", 0), "target", "sky"),
        card("frozen", "Muzlatilgan", st.get("frozen", 0), "frozen", "amber"),
        card("new", "Shu oy qo'shilgan", new_m, "new", "emerald",
             hint=f"Shu oy ketgan: {left_m}"),
    ], [
        chart("flow", "Kelgan va ketgan o'quvchilar", flow, "grouped",
              "Oxirgi 6 oy", span=2,
              series=[{"key": "new", "label": "Kelgan", "color": "#10b981"},
                      {"key": "left", "label": "Ketgan", "color": "#f43f5e"}]),
        chart("status", "Holat bo'yicha", top(st, roles.STUDENT_STATUS_LABELS),
              "donut"),
        chart("branch", "Filial bo'yicha", top(Counter(r.branch_id for r in live),
                                               bn), sub="Faol, sinov va muzlatilgan"),
        chart("subject", "Fan bo'yicha", top(Counter(r.subject for r in live),
                                             roles.SUBJECT_LABELS)),
        chart("level", "Daraja bo'yicha", top(Counter(r.level for r in live),
                                              roles.LEVEL_LABELS)),
    ]


def _groups(db, user, bid, today):
    gs = active_groups(db, user, bid)
    cnt = group_counts(db, [g.id for g in gs])
    cap_groups = [g for g in gs if g.capacity]
    fill = [100.0 * cnt[g.id] / g.capacity for g in cap_groups]
    avg_fill = round(sum(fill) / len(fill)) if fill else 0
    full = sum(1 for f in fill if f >= 100)
    free = sum(max(0, (g.capacity or 0) - cnt[g.id]) for g in cap_groups)
    buckets = Counter()
    for f in fill:
        buckets["0–49%" if f < 50 else "50–79%" if f < 80
                else "80–99%" if f < 100 else "To'la"] += 1
    order = ["0–49%", "50–79%", "80–99%", "To'la"]
    by_teacher = Counter()
    for g in gs:
        by_teacher[teacher_name(db, g.teacher_id)] += cnt[g.id]
    return [
        card("groups", "Faol guruhlar", len(gs), "layers", "indigo"),
        card("fill", "O'rtacha to'lish", f"{avg_fill}%", "trend", "emerald"),
        card("full", "To'la guruhlar", full, "check", "violet"),
        card("free", "Bo'sh o'rinlar", free, "new", "amber",
             hint="Sig'imgacha qolgan joy"),
    ], [
        chart("fill", "Guruhlar to'lishi", [{"label": k, "value": buckets[k]}
                                            for k in order], "bar",
              "Faol o'quvchilar / sig'im"),
        chart("subject", "Fan bo'yicha guruhlar",
              top(Counter(g.subject for g in gs), roles.SUBJECT_LABELS), "donut"),
        chart("branch", "Filial bo'yicha guruhlar",
              top(Counter(g.branch_id for g in gs), branch_names(db))),
        chart("teacher", "O'qituvchilar bo'yicha o'quvchilar",
              top(by_teacher, n=10), sub="Faol guruhlardagi o'quvchilar"),
    ]


def _teachers(db, user, bid, today):
    T = models.Teacher
    ts = scoped(db, user, T, bid,
                db.query(T).filter(T.is_active == 1)).all()
    gs = active_groups(db, user, bid)
    cnt = group_counts(db, [g.id for g in gs])
    g_by_t, s_by_t = Counter(), Counter()
    for g in gs:
        if g.teacher_id:
            g_by_t[g.teacher_id] += 1
            s_by_t[g.teacher_id] += cnt[g.id]
    with_g = sum(1 for t in ts if g_by_t[t.id])
    avg = round(sum(g_by_t[t.id] for t in ts) / len(ts), 1) if ts else 0
    new_y = sum(1 for t in ts if t.hired_date and t.hired_date.year == today.year)
    names = {t.id: t.full_name for t in ts}
    return [
        card("teachers", "Faol o'qituvchilar", len(ts), "teacher", "indigo"),
        card("with", "Guruhi borlar", with_g, "layers", "emerald"),
        card("avg", "O'rtacha guruh", avg, "trend", "violet",
             hint="Bir o'qituvchiga"),
        card("new", "Shu yil ishga kirgan", new_y, "new", "amber"),
    ], [
        chart("students", "O'quvchilar soni bo'yicha",
              top(Counter({names[k]: v for k, v in s_by_t.items() if k in names}),
                  n=10, other=False), sub="Top 10 o'qituvchi"),
        chart("groups", "Guruhlar soni bo'yicha",
              top(Counter({names[k]: v for k, v in g_by_t.items() if k in names}),
                  n=10, other=False)),
        chart("grade", "Daraja bo'yicha", top(Counter(t.grade for t in ts),
                                              roles.GRADE_LABELS), "donut"),
        chart("subject", "Fan bo'yicha", top(Counter(t.subject for t in ts),
                                             roles.SUBJECT_LABELS)),
    ]


def _timetable(db, user, bid, today):
    gs = active_groups(db, user, bid)
    gids = [g.id for g in gs]
    since = today - timedelta(days=29)
    L = models.Lesson
    les = (db.query(L.date, L.held, L.cancelled, L.group_id)
           .filter(L.group_id.in_(gids or [-1]), L.date >= since,
                   L.date <= today).all())
    held = [x for x in les if x.held and not x.cancelled]
    cancelled = sum(1 for x in les if x.cancelled)
    week0 = today - timedelta(days=today.weekday())
    week = sum(1 for x in held if x.date >= week0)
    by_wd = Counter(x.date.weekday() for x in held)
    R = models.Room
    rooms = scoped(db, user, R, bid, db.query(R).filter(R.active == 1)).all()
    rname = {r.id: r.name for r in rooms}
    by_room = Counter(rname.get(g.room_id, g.room or "Xonasiz") for g in gs)
    by_t = Counter(teacher_name(db, g.teacher_id) for g in gs if g.teacher_id)
    days14 = []
    for i in range(13, -1, -1):
        d = today - timedelta(days=i)
        days14.append({"label": f"{d.day}.{d.month:02d}",
                       "value": sum(1 for x in held if x.date == d)})
    return [
        card("groups", "Faol guruhlar", len(gs), "layers", "indigo"),
        card("week", "Shu hafta o'tilgan darslar", week, "calendar", "emerald"),
        card("rooms", "Faol xonalar", len(rooms), "boxes", "violet"),
        card("cancel", "Bekor qilingan darslar", cancelled, "ban", "rose",
             hint="Oxirgi 30 kun"),
    ], [
        chart("days", "O'tilgan darslar kunma-kun", days14, "bar",
              "Oxirgi 14 kun", span=2),
        chart("weekday", "Hafta kunlari bo'yicha",
              [{"label": HAFTA[i], "value": by_wd[i]} for i in range(7)], "bar",
              "Oxirgi 30 kun"),
        chart("room", "Xonalar bandligi", top(by_room, n=10),
              sub="Har xonadagi faol guruhlar"),
        chart("teacher", "O'qituvchi yuklamasi", top(by_t, n=10, other=False),
              sub="Faol guruhlar soni", span=2),
    ]


def _support(db, user, bid, today):
    sups = [u for u in staff_users(db, user, bid)
            if u.role == roles.SUPPORT_TEACHER]
    sids = {u.id for u in sups}
    sname = {u.id: u.full_name for u in sups}
    A = models.SupportAssignment
    assigns = db.query(A).filter(A.user_id.in_(sids or {-1})).all()
    S = models.SupportSession
    m0 = today.replace(day=1)
    ses = scoped(db, user, S, bid,
                 db.query(S).filter(S.date >= m0, S.date <= today)).all()
    minutes = sum(s.minutes or 0 for s in ses)

    def who(tid):
        if tid in sname:
            return sname[tid]
        return teacher_name(db, tid)
    days14 = []
    since = today - timedelta(days=13)
    ses14 = scoped(db, user, S, bid,
                   db.query(S).filter(S.date >= since, S.date <= today)).all()
    for i in range(13, -1, -1):
        d = today - timedelta(days=i)
        days14.append({"label": f"{d.day}.{d.month:02d}",
                       "value": sum(1 for s in ses14 if s.date == d)})
    return [
        card("sup", "Support o'qituvchilar", len(sups), "support", "indigo"),
        card("assign", "Biriktirilgan guruh/o'quvchi", len(assigns), "layers",
             "violet"),
        card("ses", "Shu oy mashg'ulotlar", len(ses), "calendar", "emerald"),
        card("hours", "Shu oy soat", round(minutes / 60, 1), "clock", "amber"),
    ], [
        chart("days", "Mashg'ulotlar kunma-kun", days14, "bar", "Oxirgi 14 kun",
              span=2),
        chart("by_sup", "Support bo'yicha mashg'ulotlar (shu oy)",
              top(Counter(who(s.teacher_id) for s in ses), n=10, other=False)),
        chart("load", "Biriktirishlar soni",
              top(Counter(sname.get(a.user_id, "—") for a in assigns), n=10,
                  other=False), sub="Har supportga biriktirilgan"),
    ]


def _users(db, user, bid, today):
    allu = staff_users(db, user, bid, active_only=False)
    act = [u for u in allu if u.is_active]
    month = (today.year, today.month)
    new_m = sum(1 for u in act if ym(u.hired_date or u.created_at) == month)
    left_y = [u for u in allu if not u.is_active and u.exit_date
              and u.exit_date.year == today.year]
    bdays = sum(1 for u in act if u.birth_date
                and u.birth_date.month == today.month)
    flow = []
    for y, m in months_back(today):
        flow.append({"label": f"{OY[m]} {str(y)[2:]}",
                     "hired": sum(1 for u in allu
                                  if ym(u.hired_date or u.created_at) == (y, m)),
                     "left": sum(1 for u in allu if not u.is_active
                                 and ym(u.exit_date) == (y, m))})
    return [
        card("staff", "Faol xodimlar", len(act), "staff", "indigo"),
        card("new", "Shu oy qo'shilgan", new_m, "new", "emerald"),
        card("left", "Shu yil ketgan", len(left_y), "ban", "rose"),
        card("bday", "Shu oy tug'ilgan kuni", bdays, "party", "amber"),
    ], [
        chart("flow", "Kelgan va ketgan xodimlar", flow, "grouped",
              "Oxirgi 6 oy", span=2,
              series=[{"key": "hired", "label": "Kelgan", "color": "#10b981"},
                      {"key": "left", "label": "Ketgan", "color": "#f43f5e"}]),
        chart("role", "Lavozim bo'yicha", top(Counter(u.role for u in act),
                                              roles.UZ_LABELS, n=12)),
        chart("branch", "Filial bo'yicha", top(Counter(u.branch_id for u in act),
                                               branch_names(db))),
        chart("exit", "Ketish sabablari (shu yil)",
              top(Counter(u.exit_type for u in left_y), roles.EXIT_TYPE_LABELS),
              "donut"),
    ]


def _namunali(db, user, bid, today):
    y0 = date(today.year, 1, 1)
    V = models.ConductViolation
    staff = [u for u in staff_users(db, user, bid)
             if u.role not in tuple(roles.CONDUCT_EXCLUDED)]
    ids = {u.id for u in staff}
    names = {u.id: u.full_name for u in staff}
    vs = db.query(V).filter(V.date >= y0, V.user_id.in_(ids or {-1})).all()
    lost = Counter()
    for v in vs:
        lost[v.user_id] += abs(v.points or 0)
    start = roles.CONDUCT_START_POINTS
    avg = (round(sum(start - lost[i] for i in ids) / len(ids), 1)
           if ids else start)
    clean = sum(1 for i in ids if not lost[i])
    by_m = Counter((v.date.month) for v in vs if v.date)
    return [
        card("viol", "Qoidabuzarliklar (shu yil)", len(vs), "alert", "rose"),
        card("pts", "Ayirilgan ball", num(sum(lost.values())), "target", "amber"),
        card("clean", "Toza xodimlar", clean, "trophy", "emerald",
             hint=f"{len(ids)} tadan"),
        card("avg", "O'rtacha ball", num(avg), "star", "indigo",
             hint=f"Boshlang'ich {start}"),
    ], [
        chart("month", "Oyma-oy qoidabuzarliklar",
              [{"label": OY[m], "value": by_m[m]}
               for m in range(1, today.month + 1)], "bar", f"{today.year}-yil",
              span=2),
        chart("kind", "Turi bo'yicha", top(Counter(v.kind for v in vs),
                                           roles.CONDUCT_KIND_LABELS), "donut"),
        chart("who", "Eng ko'p ball yo'qotganlar",
              top(Counter({names[k]: v for k, v in lost.items() if k in names}),
                  n=8, other=False), sub="Shu yil, ball"),
    ]


def _audit(db, user, bid, today):
    A = models.AuditLog
    since = datetime.combine(today - timedelta(days=13), datetime.min.time())
    rows = scoped(db, user, A, bid,
                  db.query(A.created_at, A.entity, A.action, A.user_name,
                           A.branch_id).filter(A.created_at >= since)).all()
    d7 = datetime.combine(today - timedelta(days=6), datetime.min.time())
    last7 = [r for r in rows if r.created_at >= d7]
    today_n = sum(1 for r in rows if r.created_at.date() == today)
    days = []
    for i in range(13, -1, -1):
        d = today - timedelta(days=i)
        days.append({"label": f"{d.day}.{d.month:02d}",
                     "value": sum(1 for r in rows if r.created_at.date() == d)})
    acts = {"create": "Yaratish", "update": "O'zgartirish", "delete": "O'chirish"}
    return [
        card("today", "Bugungi amallar", today_n, "activity", "indigo"),
        card("week", "7 kunda", len(last7), "history", "violet"),
        card("users", "Faol foydalanuvchilar", len({r.user_name for r in last7
                                                   if r.user_name}),
             "users", "emerald", hint="Oxirgi 7 kun"),
        card("del", "O'chirishlar", sum(1 for r in last7 if r.action == "delete"),
             "ban", "rose", hint="Oxirgi 7 kun"),
    ], [
        chart("days", "Amallar kunma-kun", days, "bar", "Oxirgi 14 kun", span=2),
        chart("entity", "Nimaga tegilgan", top(Counter(r.entity for r in last7),
                                               n=8), sub="Oxirgi 7 kun"),
        chart("who", "Eng faol foydalanuvchilar",
              top(Counter(r.user_name for r in last7 if r.user_name), n=8,
                  other=False), sub="Oxirgi 7 kun"),
        chart("action", "Amal turi", top(Counter(r.action for r in last7), acts),
              "donut", "Oxirgi 7 kun"),
    ]


def _inventory(db, user, bid, today):
    As = models.Asset
    assets = scoped(db, user, As, bid,
                    db.query(As).filter(As.written_off_on.is_(None))).all()
    C = models.Consumable
    cons = scoped(db, user, C, bid).all()
    low = [c for c in cons if (c.qty or 0) <= (c.min_qty or 0)]
    bad = sum(1 for a in assets if a.condition in ("repair", "broken"))
    return [
        card("assets", "Jihozlar", len(assets), "package", "indigo"),
        card("value", "Umumiy qiymati", money(sum(a.price or 0 for a in assets)),
             "trend", "emerald", hint="so'm"),
        card("bad", "Ta'mirda / buzilgan", bad, "alert", "rose"),
        card("low", "Kam qolgan sarf-material", len(low), "boxes", "amber",
             hint=f"{len(cons)} tadan"),
    ], [
        chart("cond", "Holati bo'yicha", top(Counter(a.condition for a in assets),
                                             roles.ASSET_CONDITION_LABELS),
              "donut"),
        chart("kind", "Turi bo'yicha", top(Counter(a.kind for a in assets),
                                           roles.ASSET_TYPE_LABELS)),
        chart("branch", "Filial bo'yicha jihozlar",
              top(Counter(a.branch_id for a in assets), branch_names(db))),
        chart("ckind", "Sarf-materiallar turi",
              top(Counter(c.kind for c in cons), roles.CONSUMABLE_TYPE_LABELS)),
    ]


def _events(db, user, bid, today):
    E = models.Event
    evs = scoped(db, user, E, bid).all()
    year = [e for e in evs if e.event_date and e.event_date.year == today.year]
    upcoming = sum(1 for e in evs if e.event_date and e.event_date >= today
                   and e.status in ("planned", "preparing"))
    month = sum(1 for e in evs if ym(e.event_date) == (today.year, today.month))
    done = sum(1 for e in year if e.status == "done")
    rng = months_back(today, 6)
    y, m = today.year, today.month
    for _ in range(3):
        y, m = (y, m + 1) if m < 12 else (y + 1, 1)
        rng.append((y, m))
    return [
        card("up", "Rejadagi tadbirlar", upcoming, "calendar", "indigo"),
        card("month", "Shu oy", month, "party", "violet"),
        card("done", "Shu yil o'tkazilgan", done, "check", "emerald"),
        card("budget", "Shu yil byudjet",
             money(sum(e.budget or 0 for e in year if e.status != "cancelled")),
             "trend", "amber", hint="so'm"),
    ], [
        chart("month", "Oyma-oy tadbirlar",
              [{"label": f"{OY[mm]} {str(yy)[2:]}",
                "value": sum(1 for e in evs if ym(e.event_date) == (yy, mm))}
               for yy, mm in rng], "bar", "6 oy oldin — 3 oy keyin", span=2),
        chart("kind", "Turi bo'yicha", top(Counter(e.kind for e in year),
                                           roles.EVENT_KIND_LABELS), "donut",
              "Shu yil"),
        chart("status", "Holati bo'yicha", top(Counter(e.status for e in year),
                                               roles.EVENT_STATUS_LABELS),
              sub="Shu yil"),
    ]


def _targets(item, role) -> bool:
    t = (getattr(item, "target_roles", None) or "").strip()
    return not t or role in [x.strip() for x in t.split(",")]


def _learning(db, user, bid, today, Item, Prog, done_attr, kind_attr, kind_labels,
              title_attr, noun):
    items = db.query(Item).filter(Item.active == 1).all()
    key = "item_id" if hasattr(Prog, "item_id") else "video_id"
    manager = user.role in tuple(MANAGERS)
    if not manager:
        mine = [i for i in items if _targets(i, user.role)]
        req = [i for i in mine if i.required]
        prog = {getattr(p, key): p
                for p in db.query(Prog).filter(Prog.user_id == user.id).all()}
        done = [i for i in mine if (p := prog.get(i.id)) and getattr(p, done_attr)]
        req_left = [i for i in req if i not in done]
        pct = round(100 * len(done) / len(mine)) if mine else 0
        return [
            card("mine", f"Menga tegishli {noun}", len(mine), "book", "indigo"),
            card("done", "Topshirganim", len(done), "check", "emerald"),
            card("req", "Majburiy qolgan", len(req_left), "alert", "rose"),
            card("pct", "Bajarilish", f"{pct}%", "trend", "violet"),
        ], [
            chart("kind", f"{noun.capitalize()} turi bo'yicha",
                  top(Counter(getattr(i, kind_attr) for i in mine), kind_labels),
                  "donut"),
        ]
    staff = staff_users(db, user, bid)
    sids = {u.id for u in staff}
    progs = db.query(Prog).filter(Prog.user_id.in_(sids or {-1})).all()
    done = [p for p in progs if getattr(p, done_attr)]
    by_item = Counter(getattr(p, key) for p in done)
    title = {i.id: getattr(i, title_attr) for i in items}
    active30 = {p.user_id for p in progs
                if (ts := getattr(p, "updated_at", None) or getattr(p, "last_at", None))
                and ts >= datetime.combine(today - timedelta(days=29),
                                           datetime.min.time())}
    req = [i for i in items if i.required]
    # Majburiy materiallarni to'liq topshirgan xodimlar
    done_set = {(p.user_id, getattr(p, key)) for p in done}
    full = sum(1 for u in staff
               if all((u.id, i.id) in done_set for i in req
                      if _targets(i, u.role)))
    return [
        card("items", f"{noun.capitalize()}", len(items), "book", "indigo",
             hint=f"Majburiy: {len(req)}"),
        card("done", "Topshirilgan", len(done), "check", "emerald"),
        card("active", "Faol o'rganuvchilar", len(active30), "users", "violet",
             hint="Oxirgi 30 kun"),
        card("full", "Majburiyni to'liq bajargan", full, "trophy", "amber",
             hint=f"{len(staff)} xodimdan"),
    ], [
        chart("top", f"Eng ko'p topshirilgan {noun}",
              top(Counter({title.get(k, "—"): v for k, v in by_item.items()}),
                  n=8, other=False), span=2),
        chart("kind", "Turi bo'yicha", top(Counter(getattr(i, kind_attr)
                                                   for i in items), kind_labels),
              "donut"),
        chart("role", "Lavozim bo'yicha topshirishlar",
              top(Counter(next((u.role for u in staff if u.id == p.user_id), None)
                          for p in done), roles.UZ_LABELS, n=8)),
    ]


def _library(db, user, bid, today):
    kinds = {"video": "Video", "book": "Kitob", "file": "Fayl",
             "link": "Havola", "audio": "Audio"}
    return _learning(db, user, bid, today, models.LibraryItem,
                     models.LibraryProgress, "passed", "kind", kinds, "title",
                     "materiallar")


def _development(db, user, bid, today):
    return _learning(db, user, bid, today, models.PdVideo, models.PdWatch,
                     "done", "topic", None, "title", "videolar")


def _hr(db, user, bid, today):
    """HR sahifasi tepasidagi statistika (2026-10-22, Jahongir: "barchart
    HR dashboardida ham bo'lsin"). Raqamlar /hr/overview bilan bir xil
    manbadan — hr._hr_overview_charts (butun tashkilot)."""
    import hr as _hr_mod
    ch = _hr_mod._hr_overview_charts(db, today)
    open_vac = 0
    if hasattr(roles, "VACANCY_OPEN_STATES"):
        open_vac = db.query(models.Vacancy).filter(
            models.Vacancy.status.in_(tuple(roles.VACANCY_OPEN_STATES))).count()
    open_apps = db.query(models.CandidateApplication).filter(
        models.CandidateApplication.stage.notin_(
            tuple(roles.APPLICATION_CLOSED))).count()
    staff = sum(r["value"] for r in ch["by_role"])
    reasons = Counter(a.reject_reason for a in db.query(
        models.CandidateApplication).filter(
            models.CandidateApplication.stage == "rejected",
            models.CandidateApplication.reject_reason.isnot(None)).all())
    return [
        card("staff", "Faol xodimlar", staff, "staff", "indigo"),
        card("vac", "Ochiq vakansiyalar", open_vac, "briefcase", "violet"),
        card("apps", "Ochiq arizalar", open_apps, "new", "sky"),
        card("turn", "Kadrlar almashinuvi",
             f"{num(ch['turnover_6m'])}%" if ch["turnover_6m"] is not None
             else "—",
             "trend", "rose",
             hint=f"6 oy: kelgan {ch['hired_6m']}, ketgan {ch['left_6m']}"),
    ], [
        chart("flow", "Kelgan va ketgan xodimlar",
              [{"label": f["month"], "hired": f["hired"], "left": f["left"]}
               for f in ch["flow"]], "grouped", "Oxirgi 6 oy", span=2,
              series=[{"key": "hired", "label": "Kelgan", "color": "#10b981"},
                      {"key": "left", "label": "Ketgan", "color": "#f43f5e"}]),
        chart("role", "Xodimlar lavozim bo'yicha", ch["by_role"]),
        chart("branch", "Xodimlar filial bo'yicha", ch["by_branch"]),
        chart("funnel", "Ishga olish voronkasi",
              [{"label": f["label"], "value": f["value"]} for f in ch["funnel"]],
              sub="Nomzodlar qaysi bosqichda"),
        chart("sources", "Nomzodlar qayerdan keladi", ch["sources"], "donut"),
        chart("reject", "Rad etish sabablari",
              top(reasons, roles.REJECT_LABELS), sub="Nega odam topilmayapti",
              span=2),
    ]


BUILDERS = {
    "hr": _hr,
    "students": _students, "groups": _groups, "teachers": _teachers,
    "timetable": _timetable, "support": _support, "users": _users,
    "namunali": _namunali, "audit": _audit, "inventory": _inventory,
    "events": _events, "library": _library, "development": _development,
}


@router.get("/api/insights/{section}")
def section_insights(section: str, branch_id: int | None = None,
                     db: Session = Depends(get_db),
                     user=Depends(get_current_user)):
    fn = BUILDERS.get(section)
    if not fn:
        raise HTTPException(404, "Bunday bo'lim yo'q")
    allowed = ACCESS.get(section)
    if not is_staff(user) or (allowed is not None
                              and user.role not in tuple(allowed)):
        raise HTTPException(403, "Ruxsat yo'q")
    today = roles.local_today()
    _TNAME.clear()
    try:
        cards, charts = fn(db, user, branch_id, today)
    except Exception:
        # Statistika sahifani hech qachon buzmasin
        db.rollback()
        import traceback
        traceback.print_exc()
        return {"cards": [], "charts": []}
    for c in cards:
        c.setdefault("to", LINKS.get((section, c["key"]), HOME.get(section)))
    return {"cards": cards, "charts": charts, "home": HOME.get(section)}
