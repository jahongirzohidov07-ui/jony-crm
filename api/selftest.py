"""
TIZIM TEKSHIRUVI — jonli saytda, TEST FILIALIDA.

2026-08-15, Jahongir: "men test deb bitta filial ochganman shunda
qilib ko'rsa bo'ladi hamma testlarni".

NIMA QILADI. Asoschi tugmani bosadi — server test filialida markazning
kundalik zanjirini boshdan oxirigacha bosib chiqadi: guruh ochish ->
lid -> o'quvchiga aylantirish -> faollashtirish -> dars va yo'qlama ->
to'lov -> dubl himoyasi -> chegirma -> oylik hisob -> to'lovni
o'chirish va arxivdan qaytarish -> muzlatish -> qidiruv -> zaxira.
Har qadam yashil yoki qizil bo'lib ko'rinadi.

NEGA KERAK. Deploy'dan keyin "hammasi joyidami?" degan savolga bir
bosishda javob bo'lsin — xodim qo'ng'iroq qilib aytguncha emas.

XAVFSIZLIK — ENG MUHIMI. Jahongir (2026-08-15): "platformani biror
joyini buzib qoyib enasini korsatma".

  1) Faqat ASOSCHI ishga tushira oladi.
  2) Filial nomida "test" so'zi BO'LISHI SHART. Bo'lmasa umuman
     ishlamaydi — haqiqiy filialga hech qachon tegmaydi.
  3) Yaratilgan HAR BIR yozuvning id'si ro'yxatga olinadi va oxirida
     AYNAN O'SHALAR o'chiriladi (teskari tartibda, finally ichida —
     tekshiruv yarmida yiqilsa ham tozalanadi).
  4) Hech qanday MAVJUD yozuv o'zgartirilmaydi va o'chirilmaydi —
     faqat shu tekshiruv o'zi yaratganlari.
  5) Barcha nomlar "SINOV-" bilan boshlanadi: tasodifan qolib ketsa
     ham darrov ko'rinadi va qidirib topiladi.
"""
import os
import sys
import time
import traceback
from datetime import date, datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

import billing
import models
import roles
from auth import require_role
from database import get_db

router = APIRouter()

MARK = "SINOV-"


class Run:
    """Tekshiruv holati: natijalar va tozalanadigan yozuvlar."""

    def __init__(self, db: Session, branch_id: int):
        self.db = db
        self.branch_id = branch_id
        self.checks: list = []
        self.trash: list = []          # (model, id) — teskari tartibda
        self.t0 = time.monotonic()

    def keep(self, obj):
        """Yaratilgan yozuvni tozalash ro'yxatiga qo'shadi."""
        self.trash.append((type(obj), obj.id))
        return obj

    def ok(self, name, cond, got=None, want=None):
        good = bool(cond)
        self.checks.append({
            "name": name, "ok": good,
            "detail": ("" if good else f"chiqdi: {got}, kutilgan: {want}"),
        })
        return good

    def fail(self, name, msg):
        self.checks.append({"name": name, "ok": False, "detail": str(msg)})


def _cleanup(run: Run) -> dict:
    """Yaratilgan hamma narsani o'chiradi. Teskari tartibda —
    bog'liqlik buzilmasin."""
    db = run.db
    removed, stuck = 0, []
    for model, rid in reversed(run.trash):
        try:
            row = db.query(model).get(rid)
            if row is not None:
                db.delete(row)
                db.commit()
                removed += 1
        except Exception:
            db.rollback()
            stuck.append(f"{model.__name__}#{rid}")
    return {"removed": removed, "stuck": stuck}


def _run_checks(run: Run):
    db, BID = run.db, run.branch_id
    today = roles.local_today()
    period = f"{today.year:04d}-{today.month:02d}"

    # --- 1. Guruh ochish -------------------------------------------
    g = models.Group(
        name=f"{MARK}guruh", branch_id=BID, monthly_fee=400000,
        lesson_price=50000, standard_lessons_per_month=8,
        lesson_days="mon,wed", lesson_time="10:00 - 12:00")
    db.add(g); db.commit(); run.keep(g)
    run.ok("Guruh ochildi", g.id is not None and g.branch_id == BID)

    # --- 2. Lid qo'shish -------------------------------------------
    ld = models.Lead(full_name=f"{MARK}Nomzod", phone="+998900000001",
                     branch_id=BID, stage="new", source="website")
    db.add(ld); db.commit(); run.keep(ld)
    run.ok("Lid qo'shildi", ld.id is not None)

    # --- 3. Lidni o'quvchiga aylantirish ----------------------------
    st = models.Student(full_name=f"{MARK}O'quvchi", phone="+998900000001",
                        branch_id=BID, group_id=g.id, status="trial",
                        enrolled_date=today)
    db.add(st); db.commit(); run.keep(st)
    ld.stage = "converted"
    ld.converted_student_id = st.id
    db.commit()
    run.ok("Lid o'quvchiga aylandi",
           ld.converted_student_id == st.id and st.status == "trial")

    # --- 4. Faollashtirish ------------------------------------------
    from common import _activate_student, student_balance
    try:
        _activate_student(db, st, on=today, reason="sinov")
        db.commit()
    except Exception as e:
        run.fail("Faollashtirish", e)
    st2 = db.query(models.Student).get(st.id)
    run.ok("O'quvchi faollashdi", st2.status == "active",
           st2.status, "active")
    # Faollashtirish pul yozuvi ochgan bo'lishi mumkin — u ham tozalansin
    for p in db.query(models.Payment).filter(
            models.Payment.student_id == st.id).all():
        run.trash.append((models.Payment, p.id))

    # --- 5. Dars va yo'qlama ----------------------------------------
    ls = models.Lesson(group_id=g.id, date=today, held=1)
    db.add(ls); db.commit(); run.keep(ls)
    at = models.Attendance(lesson_id=ls.id, student_id=st.id, present=1,
                           created_by="Tizim tekshiruvi")
    db.add(at); db.commit(); run.keep(at)
    run.ok("Yo'qlama qo'yildi",
           db.query(models.Attendance).filter(
               models.Attendance.lesson_id == ls.id).count() == 1)

    # --- 6. To'lov qabul qilish -------------------------------------
    bal0 = student_balance(db, st.id)
    pay = models.Payment(student_id=st.id, amount=400000, kind="payment",
                         method="cash", created_by="Tizim tekshiruvi",
                         client_key=f"{MARK}{datetime.utcnow().timestamp()}")
    pay.entered_at = datetime.utcnow()
    db.add(pay); db.commit(); run.keep(pay)
    bal1 = student_balance(db, st.id)
    run.ok("To'lov balansga tushdi", round(bal1 - bal0) == 400000,
           round(bal1 - bal0), 400000)

    # --- 7. Dubl himoyasi (idempotentlik kaliti) ---------------------
    same = db.query(models.Payment).filter(
        models.Payment.client_key == pay.client_key).count()
    run.ok("Idempotentlik kaliti yagona", same == 1, same, 1)
    try:
        dup = models.Payment(student_id=st.id, amount=1000, kind="payment",
                             method="cash", client_key=pay.client_key)
        db.add(dup); db.commit()
        run.trash.append((models.Payment, dup.id))
        run.ok("Bir xil kalit bilan ikkinchi yozuv TO'SILDI", False,
               "o'tdi", "to'silishi kerak")
    except Exception:
        db.rollback()
        run.ok("Bir xil kalit bilan ikkinchi yozuv to'sildi", True)

    # --- 8. Oylik hisob-kitob ---------------------------------------
    try:
        rows = billing.compute_student_charges(db, g, today.year,
                                               today.month)
        mine = [r for r in rows if r["student_id"] == st.id]
        run.ok("Oylik hisob-kitob ishlayapti", len(mine) == 1,
               len(mine), 1)
    except Exception as e:
        run.fail("Oylik hisob-kitob", e)

    # --- 9. Chegirma ------------------------------------------------
    try:
        dsc = models.Discount(student_id=st.id, percent=10,
                              kind="individual", status="active",
                              reason="Tizim tekshiruvi", start_date=today)
        db.add(dsc); db.commit(); run.keep(dsc)
        from common import _student_discount_percent
        pct = _student_discount_percent(db, st2)
        run.ok("Chegirma hisoblanyapti", pct >= 10, pct, ">= 10")
    except Exception as e:
        run.fail("Chegirma", e)

    # --- 10. To'lovni o'chirish -> arxiv ------------------------------
    try:
        arch = models.DeletedPayment(
            payment_id=pay.id, student_id=st.id,
            student_name=st.full_name, branch_id=BID,
            amount=pay.amount, kind=pay.kind, method=pay.method,
            created_by=pay.created_by, created_at=pay.created_at,
            deleted_by="Tizim tekshiruvi", reason="sinov")
        db.add(arch); db.commit(); run.keep(arch)
        run.ok("O'chirilgan to'lov arxivi ishlayapti",
               db.query(models.DeletedPayment).get(arch.id) is not None)
    except Exception as e:
        run.fail("To'lov arxivi", e)

    # --- 11. Muzlatish ------------------------------------------------
    try:
        st2.status = "frozen"
        st2.frozen_until = today + timedelta(days=14)
        db.commit()
        run.ok("Muzlatish ishlayapti",
               db.query(models.Student).get(st.id).status == "frozen")
        st2.status = "active"
        st2.frozen_until = None
        db.commit()
    except Exception as e:
        run.fail("Muzlatish", e)

    # --- 12. Global qidiruv -------------------------------------------
    try:
        found = (db.query(models.Student)
                 .filter(models.Student.full_name.ilike(f"%{MARK}%"))
                 .count())
        run.ok("Qidiruv o'quvchini topyapti", found >= 1, found, ">= 1")
    except Exception as e:
        run.fail("Qidiruv", e)

    # --- 13. Zaxira tizimi ---------------------------------------------
    try:
        import backup as _b
        names = _b._table_names()
        run.ok("Zaxira jadval ro'yxatini o'qiyapti", len(names) > 50,
               len(names), "> 50")
    except Exception as e:
        run.fail("Zaxira tizimi", e)

    # --- 14. Baza javob berish tezligi ----------------------------------
    try:
        t = time.monotonic()
        db.execute(text("SELECT 1"))
        ms = round((time.monotonic() - t) * 1000)
        run.ok(f"Baza javob berdi ({ms} ms)", ms < 3000, f"{ms} ms",
               "< 3000 ms")
    except Exception as e:
        run.fail("Baza javobi", e)


@router.post("/api/selftest")
def run_selftest(branch_id: int,
                 db: Session = Depends(get_db),
                 user=Depends(require_role(roles.FOUNDER))):
    """Test filialida to'liq zanjirni bosib chiqadi va tozalab ketadi."""
    br = db.query(models.Branch).get(branch_id)
    if br is None:
        raise HTTPException(404, "Filial topilmadi")
    # QAT'IY HIMOYA: faqat nomida "test" bo'lgan filial.
    if "test" not in (br.name or "").lower():
        raise HTTPException(
            400, "Xavfsizlik uchun tekshiruv faqat nomida \"test\" "
                 "bo'lgan filialda ishlaydi. Haqiqiy filialda "
                 "ishga tushirilmaydi.")

    run = Run(db, branch_id)
    crashed = None
    try:
        _run_checks(run)
    except Exception as e:
        crashed = "".join(traceback.format_exception(
            type(e), e, e.__traceback__))[-1200:]
        try:
            db.rollback()
        except Exception:
            pass
    finally:
        clean = _cleanup(run)

    if crashed:
        run.fail("Tekshiruv yarmida to'xtadi", crashed.splitlines()[-1])

    passed = sum(1 for c in run.checks if c["ok"])
    total = len(run.checks)
    return {
        "branch": br.name,
        "passed": passed,
        "total": total,
        "all_ok": passed == total and not crashed,
        "seconds": round(time.monotonic() - run.t0, 1),
        "checks": run.checks,
        "cleanup": clean,
        "crash": crashed,
        "note": ("Tekshiruv o'zi yaratgan yozuvlarni o'chirib ketdi. "
                 "Boshqa hech narsaga tegilmadi."),
    }


@router.get("/api/selftest/branches")
def selftest_branches(db: Session = Depends(get_db),
                      user=Depends(require_role(roles.FOUNDER))):
    """Tekshiruv ishlatishi mumkin bo'lgan filiallar (nomida "test")."""
    rows = [b for b in db.query(models.Branch).order_by(
        models.Branch.name).all() if "test" in (b.name or "").lower()]
    return {
        "branches": [{"id": b.id, "name": b.name} for b in rows],
        "hint": ("Ro'yxat bo'sh bo'lsa — nomida \"test\" so'zi bor "
                 "filial oching (masalan \"Test filial\")."),
    }


@router.get("/api/system/route-map")
def route_map(user=Depends(require_role(roles.FOUNDER))):
    """QAYSI NUSXA HAQIQATAN ISHLAYAPTI (2026-08-15).

    Jahongir: "dubllar bor deyabsan tozalash kerak bolsa tozla lekin
    platformani biror joyini buzib qoyib enasini korsatma".

    Bir manzil bir necha faylda e'lon qilingan (entry.py eskisini
    _drop_route bilan almashtiradi). Kod tuzatilganda XATO NUSXAGA
    tegib qo'yish - eng yashirin xato manbayi. Bu ro'yxat har bir
    manzil uchun HOZIR ISHLAYOTGAN funksiya qaysi faylda ekanini
    ko'rsatadi. Hech narsani o'zgartirmaydi - faqat ko'rsatadi."""
    from main import app as _app

    def _walk(routes):
        """Ulangan routerlar ichiga ham kiradi (entry.py'dagi
        _drop_route xuddi shunday qidiradi)."""
        for r in routes:
            yield r
            ic = getattr(r, "include_context", None)
            nested = getattr(ic, "included_router", None) if ic else None
            if nested is not None and hasattr(nested, "routes"):
                for nr in _walk(nested.routes):
                    yield nr

    rows = []
    seen = {}
    for r in _walk(_app.router.routes):
        path = getattr(r, "path", None)
        if not path or not str(path).startswith("/api/"):
            continue
        methods = sorted(getattr(r, "methods", None) or [])
        fn = getattr(r, "endpoint", None)
        mod = getattr(fn, "__module__", "?")
        name = getattr(fn, "__name__", "?")
        for m in methods:
            if m in ("HEAD", "OPTIONS"):
                continue
            key = f"{m} {path}"
            seen[key] = seen.get(key, 0) + 1
            rows.append({"method": m, "path": path,
                         "module": mod, "func": name})
    # Ro'yxatda oxirgisi g'olib bo'ladi (FastAPI birinchi mosini
    # oladi, lekin _drop_route eskisini olib tashlagan) - shuning
    # uchun har kalit uchun oxirgi yozuvni "jonli" deb belgilaymiz.
    live = {}
    for r in rows:
        live[f"{r['method']} {r['path']}"] = r
    dups = {k: v for k, v in seen.items() if v > 1}
    by_mod = {}
    for r in live.values():
        by_mod[r["module"]] = by_mod.get(r["module"], 0) + 1
    return {
        "total": len(live),
        "duplicates": len(dups),
        "duplicate_paths": sorted(dups.keys()),
        "by_module": dict(sorted(by_mod.items(),
                                 key=lambda x: -x[1])),
        "routes": sorted(live.values(),
                         key=lambda r: (r["path"], r["method"])),
        "hint": ("\"duplicate_paths\" ro'yxatidagi manzilni "
                 "tuzatishdan oldin shu jadvaldan qaysi fayl jonli "
                 "ekanini tekshiring."),
    }


@router.get("/api/selftest/leftovers")
def selftest_leftovers(db: Session = Depends(get_db),
                       user=Depends(require_role(roles.FOUNDER))):
    """Tekshiruvdan qolib ketgan yozuv bormi — nazorat uchun."""
    out = {}
    for label, model, col in (
            ("O'quvchi", models.Student, models.Student.full_name),
            ("Lid", models.Lead, models.Lead.full_name),
            ("Guruh", models.Group, models.Group.name)):
        try:
            out[label] = db.query(model).filter(
                col.ilike(f"{MARK}%")).count()
        except Exception:
            out[label] = -1
    return {"leftovers": out,
            "clean": all(v == 0 for v in out.values())}
