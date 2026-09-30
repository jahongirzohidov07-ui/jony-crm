"""Calendar-month exam reports shared by management and the teacher's own history."""
import re
from collections import defaultdict
from datetime import date
from fastapi import HTTPException
from sqlalchemy import func
import models, roles
from common import _branch_scope_ids, _teacher_of_user, aggregate_skip_ids


def report(db, user, period=None, branch_id=None, own=False):
    period = period or roles.local_today().strftime("%Y-%m")
    if not re.fullmatch(r"[0-9]{4}-[0-9]{2}", period):
        raise HTTPException(400, "Oy YYYY-MM ko'rinishida bo'lishi kerak")
    try:
        y, m = map(int, period.split("-"))
        start = date(y, m, 1)
        end = date(y + (m == 12), m % 12 + 1, 1)
    except ValueError:
        raise HTTPException(400, "Oy noto'g'ri")
    teacher = None
    if own or user.role == roles.TEACHER:
        teacher = _teacher_of_user(db, user)
        if not teacher:
            raise HTTPException(403, "Ustoz kartasi topilmadi")
    q = db.query(models.Exam, models.Group).join(models.Group)
    owner = func.coalesce(models.Exam.report_teacher_id, models.Group.teacher_id)
    branch = func.coalesce(models.Exam.report_branch_id, models.Group.branch_id)
    if teacher:
        q = q.filter(owner == teacher.id)
        skip = aggregate_skip_ids(db, user)
        if skip:
            q = q.filter(branch.notin_(skip))
        if branch_id:
            q = q.filter(branch == branch_id)
    else:
        q = q.filter(branch.in_(_branch_scope_ids(db, user, branch_id)))
    q = q.filter(models.Exam.date <= roles.local_today())
    exams = q.all()
    ids = [e.id for e, g in exams]
    results = defaultdict(list)
    if ids:
        for r in db.query(models.ExamResult).filter(models.ExamResult.exam_id.in_(ids)).all():
            results[r.exam_id].append(r)
    teachers = {t.id:t.full_name for t in db.query(models.Teacher).all()}
    branches = {b.id:b.name for b in db.query(models.Branch).all()}
    sids = {r.student_id for rows in results.values() for r in rows}
    names = {s.id:s.full_name for s in db.query(models.Student).filter(models.Student.id.in_(sids)).all()} if sids else {}
    tests, history = [], defaultdict(list)
    for e, g in exams:
        rr = results[e.id]
        if not rr:
            continue  # planned, ungraded tests are not completed tests
        tid = e.report_teacher_id if e.report_teacher_id is not None else g.teacher_id
        bid = e.report_branch_id if e.report_branch_id is not None else g.branch_id
        students = [{"key":r.student_id, "label":names.get(r.student_id,"O'quvchi"),
                     "percent":r.percent, "absent":bool(r.absent),
                     "counted":r.counted != 0 and not r.absent and r.percent is not None}
                    for r in rr]
        vals = [s["percent"] for s in students if s["counted"]]
        item = {"key":e.id,"label":e.title or roles.exam_title(e.kind,e.unit_no),
                "date":e.date.isoformat(),"group_id":g.id,"group":g.name,
                "teacher_id":tid,"teacher":teachers.get(tid,"Biriktirilmagan"),
                "branch_id":bid,"branch":branches.get(bid,"Biriktirilmagan"),
                "level":getattr(g,"level",None) or "—", "kind":e.kind,
                "retake":e.retake_of_id is not None, "avg":round(sum(vals)/len(vals),1) if vals else None,
                "results":len(vals),"students":len(students),"absent":sum(s["absent"] for s in students),
                "members":students,"values":vals}
        history[e.date.strftime("%Y-%m")].append(item)
        if start <= e.date < end:
            tests.append(item)
    def metrics(items):
        vals = [v for t in items for v in t["values"]]
        return {"avg":round(sum(vals)/len(vals),1) if vals else None,
                "results":len(vals),"exams":len(items),
                "students":len({s["key"] for t in items for s in t["members"]}),
                "groups":len({t["group_id"] for t in items})}
    def buckets(field, name):
        acc = defaultdict(list)
        for t in tests: acc[t[field]].append(t)
        out=[]
        for key, items in acc.items():
            out.append({"key":key,"label":items[0][name],**metrics(items),
                        "teacher":", ".join(sorted({t["teacher"] for t in items})),
                        "branch":", ".join(sorted({t["branch"] for t in items})),
                        "level":items[0]["level"],"test_ids":[t["key"] for t in items]})
        return sorted(out,key=lambda x: (-(x["avg"] if x["avg"] is not None else -1), x["label"]))
    student_rows=defaultdict(list)
    for t in tests:
        for s in t["members"]:
            student_rows[s["key"]].append((t,s))
    students=[]
    for sid, items in student_rows.items():
        vals=[s["percent"] for t,s in items if s["counted"]]
        students.append({"key":sid,"label":names.get(sid,"O'quvchi"),
                         "avg":round(sum(vals)/len(vals),1) if vals else None,
                         "exams":len(items),"results":len(vals),
                         "group":", ".join(sorted({t["group"] for t,s in items})),
                         "test_ids":[t["key"] for t,s in items]})
    students.sort(key=lambda x: (-(x["avg"] if x["avg"] is not None else -1),x["label"]))
    return {"period":period,"standard":roles.EXAM_STANDARD_PERCENT,
            "scope":branches.get(branch_id,"Barcha filiallar"),
            "teacher":teacher.full_name if teacher else None,
            **metrics(tests),"by_branch":buckets("branch_id","branch"),
            "by_teacher":buckets("teacher_id","teacher"),"by_group":buckets("group_id","group"),
            "by_student":students,"tests":[{k:v for k,v in t.items() if k!="values"} for t in sorted(tests,key=lambda t:(t["date"],t["key"]),reverse=True)],
            "history":[{"period":p,**metrics(items)} for p,items in sorted(history.items(),reverse=True)]}
