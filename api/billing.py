"""Dars-asosidagi to'lov (student billing) va ustoz ish haqi (teacher
payroll) hisoblash mantig'i.

Qoida (Jahongir tavsifi bo'yicha):
- Bitta dars = group.lesson_price (masalan 40 000 so'm).
- Standart oyda group.standard_lessons_per_month (odatda 12) dars uchun
  to'lanadi. Agar oyda shundan ko'p dars o'tilgan bo'lsa (masalan 13-14),
  ortig'i talabaga bepul sovg'a - baribir standart miqdorga qarab
  hisoblanadi (ya'ni min(o'tilgan darslar, standart) bilan cheklanadi).
- Agar talaba oyning yarmida qo'shilgan bo'lsa - faqat uning qo'shilgan
  sanasidan keyin o'tilgan darslar sanaladi (standart bilan cheklangan
  holda), va shunga qarab kamroq hisoblanadi.
- USTOZ ISH HAQI - yoqlamadan hisoblanadi, avtomat:

      bitta yoqlama narxi = teacher_rate_per_student / standard_lessons

  Masalan bir o'quvchidan oyiga 120 000 so'm, oyda 12 dars bo'lsa:
  120 000 / 12 = 10 000 so'm har bir yoqlamadan.

  Ustoz bir darsda 5 o'quvchiga yoqlama qo'ysa - 50 000 so'm oladi.
  Yoqlama yo'q - oylik ham yo'q. Hech kim hech narsani bosmaydi:
  yoqlama qo'yilishi bilan oylik o'zi o'sadi.

  Bo'luvchi HAQIQATDA o'tilgan dars soni emas, STANDART dars soni.
  Aks holda kam dars o'tgan ustozning bir darsi qimmatlashib ketardi
  va oyligi baribir o'zgarmasdi.
"""

import calendar
from datetime import date
from typing import Optional

from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

import models


def month_bounds(year: int, month: int) -> tuple[date, date]:
    start = date(year, month, 1)
    end = date(year, month, calendar.monthrange(year, month)[1])
    return start, end


def held_lessons_query(db: Session, group_id: int, start: date, end: date):
    """Faqat HAQIQATDA o'tilgan darslar. Jadval bo'yicha avtomat
    yaratilgan, lekin hali yoqlama qo'yilmagan darslar (held=0) bu yerga
    kirmaydi - aks holda o'quvchidan bo'lmagan dars uchun pul olingan
    bo'lardi."""
    return db.query(models.Lesson).filter(
        models.Lesson.group_id == group_id,
        models.Lesson.date >= start,
        models.Lesson.date <= end,
        models.Lesson.held == 1,
    )


def held_lessons_count(db: Session, group_id: int, year: int, month: int) -> int:
    start, end = month_bounds(year, month)
    return held_lessons_query(db, group_id, start, end).count()


def billable_lessons_for_student(
    db: Session,
    student: models.Student,
    group: models.Group,
    year: int,
    month: int,
) -> int:
    """Necha dars uchun shu talabadan pul olinishi kerak - guruhning
    standart chegarasi bilan cheklangan, va talaba shu oyga qachon
    qo'shilganini hisobga olgan holda."""
    start, end = month_bounds(year, month)
    effective_start = start
    if student.enrolled_date and student.enrolled_date > start:
        effective_start = student.enrolled_date
    # KETGANNING DUMI (2026-08-29, Jahongir: "eng oxirgi kelgan
    # darsigacha pul hisoblanishi, undan keyin 1ta kelmaydimi 2ta
    # kelmaydimi olib tashlanishi kerak"). Chiqib ketgan o'quvchida
    # oy oxiri emas, OXIRGI KELGAN DARS chegara bo'ladi.
    stop = attendance_cutoff(db, [student.id], group.id).get(student.id)
    if stop is not None:
        if stop < effective_start:
            return 0                      # umuman kelmagan
        end = min(end, stop)
    if effective_start > end:
        return 0
    held = held_lessons_query(db, group.id, effective_start, end).count()
    cap = group.standard_lessons_per_month or 12
    return min(held, cap)


def student_lesson_price(student, group) -> float:
    """SHU O'QUVCHI uchun bitta dars narxi (2026-08-15).

    Jahongir: "bizda o'qib turganlar uchun faol bolib turganlar uchun
    sentabrdan narx eski narxda qoladi faqat yangilar uchun yoki
    avgust muzlatib keyin yana kelganlarga narx oshgan bolishi kerak".

    Shuning uchun narx endi ikki qavatli:
      1) o'quvchida QULFLANGAN narx bo'lsa - o'sha (eski narx
         himoyasi: narx oshganda faol bo'lgan o'quvchi);
      2) bo'lmasa - guruhning joriy narxi (yangi kelganlar va
         muzlatib qaytganlar shu yerga tushadi).

    Qulf bo'lmaganda javob AVVALGIDEK - guruh narxi. Ya'ni hech
    narsa qulflanmagan bo'lsa butun hisob-kitob bir zarra
    o'zgarmaydi."""
    try:
        v = getattr(student, "locked_lesson_price", None)
        if v is not None and float(v) > 0:
            return float(v)
    except Exception:
        pass
    return float((getattr(group, "lesson_price", 0) if group else 0) or 0)


def compute_student_charges(
    db: Session, group: models.Group, year: int, month: int
) -> list[dict]:
    """Guruhdagi har bir faol/sinov talaba uchun shu oyning hisob-kitobini
    qaytaradi (Payment yozmaydi - shunchaki hisoblaydi)."""
    students = (
        db.query(models.Student)
        .filter(
            models.Student.group_id == group.id,
            models.Student.status.in_(["active", "trial"]),
        )
        .order_by(models.Student.full_name)
        .all()
    )
    period = f"{year:04d}-{month:02d}"
    out = []
    for s in students:
        billable = billable_lessons_for_student(db, s, group, year, month)
        amount = billable * student_lesson_price(s, group)
        already_charged = (
            db.query(models.Payment)
            .filter(
                models.Payment.student_id == s.id,
                models.Payment.period == period,
                models.Payment.kind == "charge",
            )
            .first()
        )
        out.append(
            {
                "student_id": s.id,
                "student_name": s.full_name,
                "billable_lessons": billable,
                "amount": amount,
                "already_charged": already_charged is not None,
            }
        )
    return out


# =====================================================================
#  USTOZ DARAJASI VA STAVKA
#
#  Bir o'quvchidan qancha olishi ustozning DARAJASIDAN chiqadi:
#  Junior 80 000, Middle 100 000, Senior 120 000, Expert 140 000,
#  Head 160 000.
#
#  Eng nozik joyi shu: ustoz bugun ko'tarilsa, O'TGAN OYNING darslari
#  ESKI stavkada qolishi kerak. Aks holda tarix qayta yozilib, allaqachon
#  to'langan oyning summasi o'zgarib ketardi va kassa hisobi buzilardi.
#  Shuning uchun stavka har bir darsning SANASIGA qarab, o'sha kuni
#  kuchda bo'lgan daraja bo'yicha olinadi.
# =====================================================================
def _log_db_error(db: Session, where: str, exc: Exception) -> None:
    """DB xatosini error_logs jadvaliga yozadi - asoschi buni Audit
    bo'limida ko'radi (bundan oldin bu xatolar hech qayerda ko'rinmasdan
    yo'qolib ketardi).

    db.rollback() SHART: SQLAlchemy xato chiqqan sessiyani "buzilgan"
    holatda qoldiradi - agar shu sessiyada keyin yana so'rov yuborilsa
    (masalan grade_on()'dagi zaxira so'rovi, yoki so'rovning davomida
    keladigan boshqa so'rovlar), ular ham asossiz xato berib qoladi.
    Avval tozalab olinmasa, ErrorLog yozuvining o'zi ham muvaffaqiyatsiz
    tugaydi."""
    try:
        db.rollback()
        db.add(models.ErrorLog(
            path=f"billing.{where}", method="internal",
            detail=f"{type(exc).__name__}: {exc}"[:4000]))
        db.commit()
    except Exception:
        pass  # ErrorLog yozishning o'zi ham muvaffaqiyatsiz bo'lsa -
              # bu yerda qila oladigan boshqa ishonchli narsa qolmaydi.


# =====================================================================
#  STAVKA TARIXI (2026-09-03)
#
#  Jahongir: "men tepadagi 80-160gacha bo'lgan summani 20,000dan
#  oshirmoqchiman sentabrdan ustozlarniki".
#
#  Ilgari grade_rates() har doim BUGUNGI jadvalni qaytarardi. Daraja
#  (grade_on) tarixdan olinardi-yu, stavka SUMMASI bugungi bo'lgani
#  uchun stavka o'zgartirilsa o'tgan oylarning oyligi ham yangi
#  narxda qayta hisoblanib ko'rinardi. Ekrandagi "o'tgan oylar eski
#  stavkada qoladi" va'dasi amalda bajarilmasdi (avgust oyligi
#  saqlanmagan edi).
#
#  Endi RateTable — oddiy dict (hozirgi stavkalar, eski chaqiruvlar
#  o'zgarmaydi) + .on(daraja, sana): shu sanada amalda bo'lgan
#  stavka. Tarix teacher_grade_rates jadvalida, har yozuv "qaysi
#  oydan" bilan.
# =====================================================================
class RateTable(dict):
    """Daraja -> hozirgi stavka (dict) + .on(daraja, sana) tarix."""

    def __init__(self, current: dict, history=()):
        super().__init__(current)
        self.hist: dict = {}
        for key, eff, rate in sorted(history, key=lambda x: (x[0], x[1])):
            self.hist.setdefault(key, []).append((eff, rate))

    def on(self, grade, on_date):
        """Shu sanada amalda bo'lgan stavka. Tarix bo'lmasa — hozirgi.

        Tarix bor, lekin hamma yozuvi sanadan KEYIN bo'lsa ham
        hozirgi qaytadi — shuning uchun update_grade() yangi yozuvdan
        oldin eski stavkani 1900-01-01 bilan yozib qo'yadi (o'tmish
        aniq bo'lsin)."""
        if grade is None:
            return None
        rows = self.hist.get(grade)
        if not rows:
            return self.get(grade)
        found = None
        for eff, rate in rows:
            if eff <= on_date:
                found = rate
            else:
                break
        return found if found is not None else self.get(grade)


def _rate_on(rates, grade, on_date):
    """rates RateTable bo'lsa sanaga qarab, oddiy dict bo'lsa hozirgi."""
    if hasattr(rates, "on"):
        return rates.on(grade, on_date)
    return rates.get(grade)


def grade_rates(db: Session):
    """Daraja -> bir o'quvchidan oylik summa (RateTable, dict kabi)."""
    try:
        current = {g.key: (g.rate_per_student or 0)
                   for g in db.query(models.TeacherGrade).all()}
        hist = []
        try:
            hist = [(r.grade_key, r.effective_from, r.rate_per_student or 0)
                    for r in db.query(models.TeacherGradeRate).all()]
        except SQLAlchemyError as e:
            # Jadval hali yo'q bo'lsa — tarixsiz, eski xatti-harakat
            db.rollback()
            _log_db_error(db, "grade_rates.history", e)
        return RateTable(current, hist)
    except SQLAlchemyError as e:
        # Faqat DB-darajasidagi xatolar (aloqa uzilishi, jadval
        # muammosi va h.k.) yutiladi - avvalgi "except Exception" hatto
        # dasturchi xatosini (masalan noto'g'ri atribut nomi) ham
        # abadiy sezilmas qilib qo'yardi. Bo'sh {} qaytarish eski
        # xatti-harakat bilan bir xil qoladi (rate_per_student()
        # guruhning qo'lda kiritilgan narxiga tushadi) - farqi shuki
        # endi bu holat KO'RINADI.
        _log_db_error(db, "grade_rates", e)
        return RateTable({})


_RATE_EPOCH = date(1900, 1, 1)


def month_start(d: date) -> date:
    return d.replace(day=1)


def ensure_rate_history(db: Session, grade_key: str, current_rate) -> bool:
    """Darajaning tarixi bo'sh bo'lsa, HOZIRGI stavkasini 1900-01-01
    bilan yozadi — o'tmish aniq bo'lsin. Yozuv bo'lsa hech nima
    qilmaydi. Qaytaradi: yozildimi."""
    has = (db.query(models.TeacherGradeRate)
           .filter(models.TeacherGradeRate.grade_key == grade_key).first())
    if has is not None:
        return False
    db.add(models.TeacherGradeRate(
        grade_key=grade_key, rate_per_student=float(current_rate or 0),
        effective_from=_RATE_EPOCH, note="Boshlang'ich stavka",
        created_by="Tizim"))
    db.flush()
    return True


def record_grade_rate(db: Session, grade_key: str, rate: float,
                      effective_from: date, by: str = None,
                      note: str = None):
    """Yangi stavkani tarixga yozadi. O'sha oy uchun yozuv bo'lsa —
    yangilanadi (xato kiritilgan bo'lsa tuzatish mumkin), o'chirilmaydi."""
    eff = month_start(effective_from)
    row = (db.query(models.TeacherGradeRate)
           .filter(models.TeacherGradeRate.grade_key == grade_key,
                   models.TeacherGradeRate.effective_from == eff).first())
    if row is None:
        row = models.TeacherGradeRate(grade_key=grade_key,
                                      effective_from=eff)
        db.add(row)
    row.rate_per_student = float(rate or 0)
    row.created_by = by
    row.note = note
    db.flush()
    return row


def backfill_grade_rate_history(db: Session) -> int:
    """Bir martalik: hamma darajaning hozirgi stavkasini tarixga
    boshlang'ich yozuv sifatida qo'yadi. Idempotent."""
    n = 0
    for g in db.query(models.TeacherGrade).all():
        if ensure_rate_history(db, g.key, g.rate_per_student):
            n += 1
    if n:
        db.commit()
    return n


def grade_on(db: Session, teacher_id: int, on_date: date) -> Optional[str]:
    """Ustoz SHU SANADA qaysi darajada edi. Tarixda yozuv bo'lmasa -
    hozirgi darajasi."""
    if not teacher_id:
        return None
    try:
        ev = (db.query(models.TeacherGradeEvent)
              .filter(models.TeacherGradeEvent.teacher_id == teacher_id,
                      models.TeacherGradeEvent.effective_from <= on_date,
                      models.TeacherGradeEvent.to_grade.isnot(None))
              .order_by(models.TeacherGradeEvent.effective_from.desc(),
                        models.TeacherGradeEvent.id.desc())
              .first())
        if ev:
            return ev.to_grade
    except SQLAlchemyError as e:
        _log_db_error(db, "grade_on", e)
    t = db.query(models.Teacher).get(teacher_id)
    return t.grade if t else None


# =====================================================================
#  TO'PLAM BO'LIB O'QISH (2026-08-15, Jahongir: "D ni ham qil")
#
#  Muammo: oylik hisoblashda HAR DARS uchun alohida so'rov ketardi —
#  grade_on() 1-2 ta, lesson_student_count() 1 ta. 360 dars = ~1000
#  so'rov. Moliya sahifasi shu sababdan 1 100 so'rov qilardi.
#
#  Yechim: kerakli hamma narsa 3 ta so'rovda oldindan o'qib olinadi,
#  keyin xotirada hisoblanadi. MANTIQ AYNAN O'ZGARMAGAN — quyidagi
#  GradeIndex.on() grade_on() bilan bir xil javob beradi (shu sana
#  yoki undan oldingi ENG OXIRGI voqea, bo'lmasa ustozning hozirgi
#  darajasi). Buni test isbotlaydi: eski va yangi yo'l bir xil
#  summani chiqarishi solishtiriladi.
# =====================================================================
class GradeIndex:
    """Ustoz darajasi tarixini bir marta o'qib, xotirada javob beradi."""

    def __init__(self, db: Session):
        self.events: dict = {}
        self.now: dict = {}
        self.rates: dict = grade_rates(db)
        try:
            rows = (db.query(models.TeacherGradeEvent)
                    .filter(models.TeacherGradeEvent.to_grade.isnot(None))
                    .order_by(models.TeacherGradeEvent.effective_from,
                              models.TeacherGradeEvent.id).all())
            for e in rows:
                self.events.setdefault(e.teacher_id, []).append(
                    (e.effective_from, e.to_grade))
        except SQLAlchemyError as exc:
            _log_db_error(db, "GradeIndex.events", exc)
        try:
            for t in db.query(models.Teacher.id, models.Teacher.grade).all():
                self.now[t[0]] = t[1]
        except SQLAlchemyError as exc:
            _log_db_error(db, "GradeIndex.now", exc)

    def on(self, teacher_id, on_date):
        """grade_on() bilan bir xil: shu sanadagi daraja."""
        if not teacher_id:
            return None
        found = None
        for eff, grade in self.events.get(teacher_id, ()):
            if eff is not None and eff <= on_date:
                found = grade      # ro'yxat o'sish tartibida - oxirgisi qoladi
            else:
                break
        if found is not None:
            return found
        return self.now.get(teacher_id)

    def per_student(self, group, teacher_id, on_date) -> float:
        """rate_per_student() bilan bir xil."""
        if getattr(group, "rate_manual", 0):
            return group.teacher_rate_per_student or 0
        v = _rate_on(self.rates, self.on(teacher_id, on_date), on_date)
        if v:
            return v
        return group.teacher_rate_per_student or 0


# =====================================================================
#  KETGANNING DUMI  (2026-08-29)
# =====================================================================
#
#  Jahongir: "chiqib ketgan kunida oxirida masalan Mahbubahon turibdi
#  oxirgi 2ta dars kelmagan va chiqib ketgan, shu kelmagan darsini
#  ayirib tashlash kerak, yo'qlamasi yo'qolishi kerak, chunki u chiqib
#  ketgan ustozga oylik yozilishi kerak emas, AVTOMAT yo'q bo'lishi
#  kerak. Admin noto'g'ri kundan chiqarvorgan bo'lsa ham ENG OXIRGI
#  KELGAN DARSIGACHA pul hisoblanishi, undan keyin 1ta kelmaydimi 2ta
#  kelmaydimi olib tashlanishi kerak"
#
#  QOIDA. O'quvchi guruhdan CHIQQAN bo'lsa (arxiv, muzlatilgan yoki
#  shu guruhdan chiqarilgan), uning OXIRGI KELGAN darsidan KEYINGI
#  yo'qlama yozuvlari hech qayerda sanalmaydi:
#     · ustoz oyligiga qo'shilmaydi,
#     · o'quvchining hisobiga (pul) qo'shilmaydi,
#     · yo'qlama jadvalida ko'rinmaydi.
#
#  NEGA SANA EMAS, OXIRGI KELGAN DARS. Admin chiqarish sanasini
#  noto'g'ri qo'yishi mumkin (kech qo'ygan, esdan chiqargan). Oxirgi
#  kelgan dars esa YOLG'ON GAPIRMAYDI: bola kelgan bo'lsa — kelgan.
#  Shuning uchun chegara sanadan emas, faktdan olinadi.
#
#  HECH NARSA O'CHIRILMAYDI. Yo'qlama yozuvlari bazada joyida qoladi
#  (tarix uchun), faqat HISOBGA OLINMAYDI.
#
#  DIQQAT — FAOL O'QUVCHIGA TEGMAYDI. Hozir o'qiyotgan bola oxirgi 2
#  darsga kelmagan bo'lsa, u baribir to'laydi va ustoz haqini oladi.
#  Kesish FAQAT guruhdan chiqqanlarga qo'llanadi.
_OPEN_STATUSES = ("active", "trial")
_NEVER = date(1900, 1, 1)      # umuman kelmagan — hech narsa sanalmaydi


def attendance_cutoff(db: Session, student_ids, group_id=None) -> dict:
    """{student_id: shu sanagacha sanaladi}. Faqat CHIQQANLAR uchun.

    Ro'yxatda bo'lmagan o'quvchiga chegara yo'q — u to'liq sanaladi."""
    ids = [int(i) for i in set(student_ids or []) if i]
    if not ids:
        return {}

    rows = (db.query(models.Student.id, models.Student.status)
            .filter(models.Student.id.in_(ids)).all())
    closed = {sid for sid, st in rows if st not in _OPEN_STATUSES}

    # SHU GURUHDAN chiqarilganlar ham (statusi "active" bo'lsa ham —
    # ular boshqa guruhga o'tgan bo'lishi mumkin).
    if group_id:
        left_links = (db.query(models.StudentGroupLink.student_id)
                      .filter(models.StudentGroupLink.student_id.in_(ids),
                              models.StudentGroupLink.group_id == group_id,
                              models.StudentGroupLink.active == 0).all())
        closed |= {r[0] for r in left_links}
        # Bog'lanish jadvali to'ldirilmagan bo'lsa: asosiy guruhi
        # boshqa bo'lgan va shu guruhda faol bog'lanishi yo'q o'quvchi.
        alive = {r[0] for r in
                 db.query(models.StudentGroupLink.student_id)
                 .filter(models.StudentGroupLink.student_id.in_(ids),
                         models.StudentGroupLink.group_id == group_id,
                         models.StudentGroupLink.active == 1).all()}
        prim = {sid for sid, in
                db.query(models.Student.id)
                .filter(models.Student.id.in_(ids),
                        models.Student.group_id == group_id).all()}
        closed |= (set(ids) - alive - prim)

    if not closed:
        return {}

    last = dict(
        db.query(models.Attendance.student_id, func.max(models.Lesson.date))
        .join(models.Lesson, models.Lesson.id == models.Attendance.lesson_id)
        .filter(models.Attendance.student_id.in_(list(closed)),
                models.Attendance.present.in_([1, 2]))
        .group_by(models.Attendance.student_id).all())
    return {sid: (last.get(sid) or _NEVER) for sid in closed}


def countable_attendance(db: Session, lessons, group_id=None) -> dict:
    """{lesson_id: sanaladigan yo'qlama soni}.

    lesson_student_count() ning to'plam varianti, ketganlarning dumi
    kesilgan holda. Bitta so'rovda oladi — N+1 bo'lmasin."""
    lessons = list(lessons)
    if not lessons:
        return {}
    by_id = {l.id: l for l in lessons}
    rows = []
    ids = list(by_id)
    CHUNK = 900
    for i in range(0, len(ids), CHUNK):
        rows += (db.query(models.Attendance.lesson_id,
                          models.Attendance.student_id)
                 .filter(models.Attendance.lesson_id.in_(ids[i:i + CHUNK]))
                 .all())
    cut = attendance_cutoff(db, {sid for _, sid in rows}, group_id)
    out = {lid: 0 for lid in by_id}
    for lid, sid in rows:
        stop = cut.get(sid)
        les = by_id.get(lid)
        if stop is not None and les is not None and les.date \
                and les.date > stop:
            continue                      # ketganning dumi — sanalmaydi
        out[lid] = out.get(lid, 0) + 1
    return out


def attendance_counts(db: Session, lesson_ids) -> dict:
    """Har darsda nechta yo'qlama bor — BITTA so'rovda.
    lesson_student_count() ning to'plam varianti."""
    ids = list(lesson_ids)
    out = {}
    CHUNK = 900
    for i in range(0, len(ids), CHUNK):
        part = ids[i:i + CHUNK]
        rows = (db.query(models.Attendance.lesson_id,
                         func.count(models.Attendance.id))
                .filter(models.Attendance.lesson_id.in_(part))
                .group_by(models.Attendance.lesson_id).all())
        for lid, n in rows:
            out[lid] = n
    return out



# =====================================================================
#  OYLIK SAHIFASI TEZLIGI (2026-09-05, Jahongir: "shunaqa yuklashlar
#  juda sekin bolyabdi")
#
#  Muammo: Hisobotlar → Oyliklar → Ustozlar oyligi 72 ta ustoz uchun
#  _teacher_earned() ni 2 martadan chaqiradi, u esa HAR DARS uchun
#  grade_on() (1 so'rov) + lesson_student_count() (5-6 so'rov) +
#  month_divisor() (oyiga 1 so'rov) qilardi. Butun tarix bo'yicha bu
#  o'n minglab so'rov — Vercel 504 (FUNCTION_INVOCATION_TIMEOUT).
#
#  Yechim: hamma narsa BIR MARTA, to'plam bo'lib o'qiladi (PayrollContext),
#  hisob-kitob xotirada. MANTIQ AYNAN O'ZGARMAGAN:
#    - countable_attendance_many() har dars uchun
#      countable_attendance(db, [dars], dars.group_id) bilan bir xil son;
#    - GradeIndex.per_student() rate_per_student() bilan bir xil;
#    - month_divisor() keshi oldindan xuddi o'sha so'rov natijasi bilan
#      to'ldiriladi.
#  test_payroll_speed.py eski va yangi yo'lni sintetik ma'lumotda
#  solishtiradi (bir xil natija, so'rovlar soni bir necha barobar kam).
# =====================================================================
_CHUNK = 900


def _chunks(seq, n: int = _CHUNK):
    seq = list(seq)
    for i in range(0, len(seq), n):
        yield seq[i:i + n]


def attendance_cutoff_many(db: Session, per_group: dict) -> dict:
    """{group_id: {student_id: shu sanagacha sanaladi}}.

    attendance_cutoff() ning ko'p guruhli varianti: har guruh uchun
    javob attendance_cutoff(db, ids, group_id) bilan AYNAN bir xil,
    faqat so'rovlar guruhlar bo'ylab birlashtirilgan (5 ta so'rov
    o'rniga guruh soniga bog'liq bo'lmagan ~5 ta)."""
    per_group = {gid: {int(i) for i in (ids or []) if i}
                 for gid, ids in per_group.items()}
    all_ids = sorted({i for ids in per_group.values() for i in ids})
    if not all_ids:
        return {gid: {} for gid in per_group}

    status_closed: set = set()
    prim_of: dict = {}
    for chunk in _chunks(all_ids):
        rows = (db.query(models.Student.id, models.Student.status,
                         models.Student.group_id)
                .filter(models.Student.id.in_(chunk)).all())
        for sid, st, gid in rows:
            if st not in _OPEN_STATUSES:
                status_closed.add(sid)
            prim_of[sid] = gid

    gids = [g for g in per_group if g]
    left: set = set()
    alive: set = set()
    if gids:
        for chunk in _chunks(all_ids):
            rows = (db.query(models.StudentGroupLink.student_id,
                             models.StudentGroupLink.group_id,
                             models.StudentGroupLink.active)
                    .filter(models.StudentGroupLink.student_id.in_(chunk),
                            models.StudentGroupLink.group_id.in_(gids))
                    .all())
            for sid, gid, act in rows:
                if act == 0:
                    left.add((sid, gid))
                elif act == 1:
                    alive.add((sid, gid))

    closed_by_group: dict = {}
    closed_all: set = set()
    for gid, ids in per_group.items():
        closed = ids & status_closed
        if gid:
            closed |= {s for s in ids if (s, gid) in left}
            # Bog'lanish jadvali to'ldirilmagan bo'lsa: asosiy guruhi
            # boshqa bo'lgan va shu guruhda faol bog'lanishi yo'q o'quvchi.
            closed |= {s for s in ids
                       if (s, gid) not in alive and prim_of.get(s) != gid}
        closed_by_group[gid] = closed
        closed_all |= closed

    last: dict = {}
    for chunk in _chunks(sorted(closed_all)):
        rows = (db.query(models.Attendance.student_id,
                         func.max(models.Lesson.date))
                .join(models.Lesson,
                      models.Lesson.id == models.Attendance.lesson_id)
                .filter(models.Attendance.student_id.in_(chunk),
                        models.Attendance.present.in_([1, 2]))
                .group_by(models.Attendance.student_id).all())
        for sid, d in rows:
            last[sid] = d
    return {gid: {sid: (last.get(sid) or _NEVER) for sid in closed}
            for gid, closed in closed_by_group.items()}


def countable_attendance_many(db: Session, lessons) -> dict:
    """{lesson_id: sanaladigan yo'qlama soni} — ko'p guruh uchun birdan.

    Har dars uchun javob countable_attendance(db, [dars], dars.group_id)
    bilan aynan bir xil. Farqi: so'rovlar soni darslar/guruhlar soniga
    emas, faqat ma'lumot hajmiga bog'liq."""
    lessons = list(lessons)
    if not lessons:
        return {}
    by_id = {l.id: l for l in lessons}
    ids = list(by_id)
    out = {lid: 0 for lid in by_id}

    # 1) xom sonlar — har darsda nechta yo'qlama yozuvi bor
    for lid, n in attendance_counts(db, ids).items():
        if lid in out:
            out[lid] = int(n or 0)

    # 2) qaysi guruh darslarida qaysi o'quvchi uchraydi
    per_group: dict = {}
    for chunk in _chunks(ids):
        rows = (db.query(models.Lesson.group_id, models.Attendance.student_id)
                .join(models.Lesson,
                      models.Lesson.id == models.Attendance.lesson_id)
                .filter(models.Attendance.lesson_id.in_(chunk))
                .distinct().all())
        for gid, sid in rows:
            per_group.setdefault(gid, set()).add(sid)
    if not per_group:
        return out

    # 3) chiqqanlarning chegaralari (guruh bo'yicha)
    cut = attendance_cutoff_many(db, per_group)
    closed_all = sorted({sid for c in cut.values() for sid in c})
    if not closed_all:
        return out

    # 4) faqat chiqqanlarning yozuvlari — dumini kesish.
    #    Chegarasi eng erta bo'lganlardan boshlab bo'laklanadi, har
    #    bo'lakda "sana > shu bo'lakning eng erta chegarasi" sharti
    #    ortiqcha qatorlarni o'qimaslik uchun.
    stop_min: dict = {}
    for c in cut.values():
        for sid, stop in c.items():
            if sid not in stop_min or stop < stop_min[sid]:
                stop_min[sid] = stop
    closed_all.sort(key=lambda s: stop_min.get(s) or _NEVER)
    gids = [g for g in per_group if g]
    gcond = models.Lesson.group_id.in_(gids) if gids else None
    if None in per_group or 0 in per_group:
        nul = models.Lesson.group_id.is_(None) | (models.Lesson.group_id == 0)
        gcond = nul if gcond is None else (gcond | nul)
    for chunk in _chunks(closed_all):
        q = (db.query(models.Attendance.lesson_id, models.Attendance.student_id)
             .join(models.Lesson,
                   models.Lesson.id == models.Attendance.lesson_id)
             .filter(models.Attendance.student_id.in_(chunk)))
        if gcond is not None:
            q = q.filter(gcond)
        floor = stop_min.get(chunk[0]) or _NEVER
        if floor > _NEVER:
            q = q.filter(models.Lesson.date > floor)
        for lid, sid in q.all():
            les = by_id.get(lid)
            if les is None:
                continue
            stop = cut.get(les.group_id, {}).get(sid)
            if stop is not None and les.date and les.date > stop:
                out[lid] -= 1              # ketganning dumi — sanalmaydi
    return out


class PayrollContext:
    """Oylik hisoblash uchun bir marta o'qiladigan ma'lumotlar.

    _teacher_earned() shu orqali ishlaydi: guruhlar, daraja tarixi,
    oy bo'luvchisi keshi va har dars uchun sanaladigan yo'qlama soni.
    Bir nechta ustoz uchun (oyliklar sahifasi) prefetch() bilan hamma
    darslar va to'lovlar ham bir yo'la o'qiladi."""

    def __init__(self, db: Session):
        self.db = db
        self.groups = {g.id: g for g in db.query(models.Group).all()}
        self.grades = GradeIndex(db)
        self.mcache: dict = {}
        self.counts: dict = {}
        self._lessons: Optional[dict] = None
        self._payments: Optional[dict] = None

    # --- darslar ---------------------------------------------------
    @staticmethod
    def _lesson_q(db: Session):
        return db.query(models.Lesson.id, models.Lesson.group_id,
                        models.Lesson.teacher_id, models.Lesson.date)

    def prefetch(self, teacher_ids) -> None:
        ids = sorted({int(t) for t in teacher_ids if t})
        self._lessons = {t: [] for t in ids}
        self._payments = {t: [] for t in ids}
        for chunk in _chunks(ids):
            rows = (self._lesson_q(self.db)
                    .filter(models.Lesson.teacher_id.in_(chunk),
                            models.Lesson.held == 1)
                    .order_by(models.Lesson.date, models.Lesson.id).all())
            for r in rows:
                self._lessons.setdefault(r.teacher_id, []).append(r)
            pays = (self.db.query(models.TeacherPayment.teacher_id,
                                  models.TeacherPayment.paid_on,
                                  models.TeacherPayment.amount)
                    .filter(models.TeacherPayment.teacher_id.in_(chunk))
                    .order_by(models.TeacherPayment.id).all())
            for p in pays:
                self._payments.setdefault(p.teacher_id, []).append(p)
        all_rows = [r for rows in self._lessons.values() for r in rows]
        self.count_for(all_rows)
        self.prefill_divisors(all_rows)

    def lessons(self, teacher_id: int, since: Optional[date],
                until: date) -> list:
        """_teacher_earned() dagi so'rov bilan bir xil to'plam:
        held=1, sana <= until, (since bo'lsa) sana >= since."""
        if self._lessons is not None and teacher_id in self._lessons:
            return [l for l in self._lessons[teacher_id]
                    if l.date is not None and l.date <= until
                    and (since is None or l.date >= since)]
        q = (self._lesson_q(self.db)
             .filter(models.Lesson.teacher_id == teacher_id,
                     models.Lesson.held == 1,
                     models.Lesson.date <= until))
        if since:
            q = q.filter(models.Lesson.date >= since)
        return q.order_by(models.Lesson.date, models.Lesson.id).all()

    # --- to'lovlar -------------------------------------------------
    def payments(self, teacher_id: int):
        """None — oldindan o'qilmagan (chaqiruvchi o'zi so'raydi)."""
        if self._payments is None:
            return None
        return self._payments.get(teacher_id, [])

    # --- yo'qlama sonlari -----------------------------------------
    def count_for(self, lessons) -> dict:
        missing = [l for l in lessons if l.id not in self.counts]
        if missing:
            self.counts.update(countable_attendance_many(self.db, missing))
        return self.counts

    # --- oy bo'luvchisi -------------------------------------------
    def prefill_divisors(self, lessons) -> None:
        """month_divisor() keshini xuddi o'sha so'rov natijasi bilan
        oldindan to'ldiradi — oy/guruh boshiga 1 so'rov o'rniga 1 ta."""
        keys = {(l.group_id, l.date.year, l.date.month) for l in lessons
                if l.group_id and l.date and l.date >= SALARY_DIVISOR_SINCE
                and l.group_id in self.groups}
        keys -= set(self.mcache)
        if not keys:
            return
        agg: dict = {}
        for chunk in _chunks(sorted({k[0] for k in keys})):
            rows = (self.db.query(models.Lesson.group_id, models.Lesson.date)
                    .filter(models.Lesson.group_id.in_(chunk),
                            (models.Lesson.cancelled.is_(None))
                            | (models.Lesson.cancelled == 0)).all())
            for gid, d in rows:
                if d:
                    k = (gid, d.year, d.month)
                    agg[k] = agg.get(k, 0) + 1
        for k in keys:
            g = self.groups.get(k[0])
            std = int(g.standard_lessons_per_month or 12)
            if std <= 0:
                std = 12
            self.mcache[k] = max(std, int(agg.get(k, 0)))


def rate_per_student(db: Session, group: models.Group,
                     teacher_id: Optional[int], on_date: date,
                     rates: Optional[dict] = None) -> float:
    """Ustozga shu guruhning bir o'quvchisidan bir oyga qancha
    to'lanadi — shu sanadagi holat bo'yicha.

    Guruhga ataylab qo'lda narx qo'yilgan bo'lsa (rate_manual), daraja
    unga tegmaydi: istisno holatlar uchun yo'l ochiq qoladi."""
    if getattr(group, "rate_manual", 0):
        return group.teacher_rate_per_student or 0
    if rates is None:
        rates = grade_rates(db)
    v = _rate_on(rates, grade_on(db, teacher_id, on_date), on_date)
    if v:
        return v
    # Daraja jadvali hali to'lmagan bo'lsa - eski xatti-harakat
    return group.teacher_rate_per_student or 0


def per_attendance_rate(group: models.Group,
                        per_student: Optional[float] = None) -> float:
    """Bitta yoqlama qancha turadi.

    Formula: ustozga bir o'quvchidan bir OY uchun beriladigan summa,
    o'shanday oydagi STANDART dars soniga bo'linadi.

        120 000 / 12 = 10 000

    Muhim: bo'luvchi haqiqatda o'tilgan dars soni EMAS, standart dars
    soni. Aks holda ustoz kam dars o'tsa bir darsning narxi ko'tarilib
    ketardi va oyligi baribir o'zgarmasdi — ya'ni dars o'tmaslikning
    jazosi bo'lmasdi."""
    std = group.standard_lessons_per_month or 12
    if std <= 0:
        return 0.0
    if per_student is None:
        per_student = group.teacher_rate_per_student or 0
    return (per_student or 0) / std


# =====================================================================
#  OYLIK BO'LUVCHISI: REJADAGI DARS SONI (2026-08-19)
#
#  Jahongir: "biz minimum 12ta dars o'tishimiz kerak va bu oy hisoblashi
#  boyicha 13ta dars bor lekin sen 11ta bilan bir o'quvchiga to'liq
#  o'tmasidan 140,000 hisoblab qoygansan" va tasdiqladi: "yangi hisobni
#  tasdiqlayman 13 ta darsni toliq o'tsa 160,000 oladi".
#
#  Avval bo'luvchi DOIM standart (12) edi. 13 darslik oyda ustoz
#  hammasini o'tsa 13/12 barobar — oylik stavkadan OSHIB ketardi.
#  Endi bo'luvchi = o'sha oyda guruhning REJADAGI dars soni, lekin
#  12 dan (standartdan) kam bo'lmaydi:
#    13 darslik oy: to'liq o'tsa — aynan oylik stavka;
#    12 darslik oy: hech narsa o'zgarmaydi;
#    11 rejali oy: baribir 12 ga bo'linadi — "kamida 12 dars" qoidasi.
#
#  FAQAT 2026-AVGUSTDAN. O'tgan oylarning hisob-kitobi to'langan va
#  yopilgan — ular eski qoidada qoladi, orqaga qayta ochilmaydi.
# =====================================================================
SALARY_DIVISOR_SINCE = date(2026, 8, 1)


def month_divisor(db: Session, group: models.Group, on_date: date,
                  cache: Optional[dict] = None) -> int:
    """Shu oy uchun oylik stavka bo'linadigan dars soni."""
    std = int(group.standard_lessons_per_month or 12)
    if std <= 0:
        std = 12
    if on_date < SALARY_DIVISOR_SINCE:
        return std
    key = (group.id, on_date.year, on_date.month)
    if cache is not None and key in cache:
        return cache[key]
    start, end = month_bounds(on_date.year, on_date.month)
    try:
        n = (db.query(func.count(models.Lesson.id))
             .filter(models.Lesson.group_id == group.id,
                     models.Lesson.date >= start,
                     models.Lesson.date <= end,
                     # Bekor qilingan (dam kuni) dars REJAGA kirmaydi
                     (models.Lesson.cancelled.is_(None))
                     | (models.Lesson.cancelled == 0)).scalar() or 0)
    except SQLAlchemyError as e:
        _log_db_error(db, "month_divisor", e)
        n = 0
    d = max(std, int(n))
    if cache is not None:
        cache[key] = d
    return d


def per_attendance_rate_m(db: Session, group: models.Group, on_date: date,
                          per_student: float,
                          cache: Optional[dict] = None) -> float:
    """Bitta yoqlama narxi — oyning rejadagi dars soniga qarab."""
    d = month_divisor(db, group, on_date, cache)
    if d <= 0:
        return 0.0
    return (per_student or 0) / d


def lesson_rate(db: Session, group: models.Group, lesson: models.Lesson,
                rates: Optional[dict] = None,
                mcache: Optional[dict] = None) -> tuple[float, float]:
    """Shu dars uchun (bir yoqlama narxi, bir o'quvchidan oylik summa)."""
    per_student = rate_per_student(db, group, lesson.teacher_id,
                                   lesson.date, rates)
    return (per_attendance_rate_m(db, group, lesson.date, per_student,
                                  mcache), per_student)


def lesson_student_count(db: Session, lesson: models.Lesson) -> int:
    """Shu darsda ustoz nechta o'quvchi uchun javobgar edi.

    Yoqlamada belgilangan o'quvchilar soni olinadi. O'quvchi kelmagan
    bo'lsa ham sanaladi — chunki u shu dars uchun baribir to'laydi,
    demak ustoz ham haqini oladi.

    Yoqlama qo'yilmagan bo'lsa — NOL. Bu ataylab: ustoz
    dashboardidagi ogohlantirish "Davomat belgilanmasa ish haqi ham
    hisoblanmaydi" deb va'da beradi, hisob shu va'daga mos bo'lishi
    shart. Keldi (1), kech keldi (2) va kelmadi (0) — hammasi
    BELGILANGAN yoqlama, hammasi sanaladi: o'quvchi kelmasa ham shu
    dars uchun to'laydi, demak ustoz ham haqini oladi.

    BITTA ISTISNO (2026-08-29): guruhdan CHIQIB KETGAN o'quvchining
    oxirgi kelgan darsidan keyingi yozuvlari sanalmaydi — u endi
    o'qimayapti, to'lamaydi ham (yuqoridagi "ketganning dumi"
    izohiga qarang)."""
    return countable_attendance(db, [lesson],
                                getattr(lesson, "group_id", None)
                                ).get(lesson.id, 0)


def compute_teacher_payroll(
    db: Session, group: models.Group, year: int, month: int,
    rates: Optional[dict] = None,
) -> list[dict]:
    """Guruh bo'yicha shu oyda kim qancha ish haqi olishini hisoblaydi.

    Ustoz YOQLAMA qo'ygani uchun pul oladi: har bir o'tilgan darsda
    nechta o'quvchi bo'lsa, shuncha marta per_attendance_rate.
    Yoqlama yo'q — oylik ham yo'q.

    Stavka har bir darsning sanasiga qarab olinadi: oy o'rtasida
    ko'tarilgan ustoz eski darslari uchun eski, yangilari uchun yangi
    stavkada oladi."""
    start, end = month_bounds(year, month)
    lessons = held_lessons_query(db, group.id, start, end).all()
    held = len(lessons)
    std = group.standard_lessons_per_month or 12
    if rates is None:
        rates = grade_rates(db)

    student_count = (
        db.query(models.Student)
        .filter(
            models.Student.group_id == group.id,
            models.Student.status.in_(["active", "trial"]),
        )
        .count()
    )

    # Ustoz kesimida: nechta dars o'tdi, nechta yoqlama qo'ydi, qancha
    # ishlab topdi. Stavka dars sanasi bo'yicha olinadi.
    cache: dict = {}
    mcache: dict = {}
    # KETGANNING DUMI KESILADI (2026-08-29). Bitta so'rovda — avval
    # har dars uchun alohida COUNT ketardi (N+1).
    n_by_lesson = countable_attendance(db, lessons, group.id)
    by_teacher: dict[Optional[int], dict] = {}
    for lesson in lessons:
        if lesson.teacher_id is None:
            continue
        key = (lesson.teacher_id, lesson.date)
        if key not in cache:
            cache[key] = rate_per_student(db, group, lesson.teacher_id,
                                          lesson.date, rates)
        per_student = cache[key]
        rate = per_attendance_rate_m(db, group, lesson.date, per_student,
                                     mcache)
        n = n_by_lesson.get(lesson.id, 0)

        row = by_teacher.setdefault(lesson.teacher_id, {
            "taught_lessons": 0, "attendances": 0, "amount": 0.0,
            "per_student": per_student, "rate": rate,
        })
        row["taught_lessons"] += 1
        row["attendances"] += n
        row["amount"] += n * rate
        # Oy oxiridagi (eng so'nggi) stavka ko'rsatiladi
        row["per_student"] = per_student
        row["rate"] = rate

    out = []
    for teacher_id, row in by_teacher.items():
        amount = row["amount"]
        out.append(
            {
                "teacher_id": teacher_id,
                "held_lessons": held,
                "taught_lessons": row["taught_lessons"],
                "attendances": row["attendances"],
                "student_count": student_count,
                "rate": row["rate"],
                "rate_per_student_month": row["per_student"],
                "standard_lessons": std,
                # Standartdan ko'p dars o'tilgan bo'lsa - ko'rinib tursin.
                # O'quvchi ortiqcha darsga to'lamaydi, ustoz esa oladi.
                "extra_lessons": max(0, row["taught_lessons"] - std),
                "amount": amount,
                "amount_per_student": (amount / student_count
                                       if student_count else 0.0),
            }
        )
    return out
