"""Eski tizimdagi ustozlar dars-sifati statistikasini import qilish.

Jahongir: "eski dars sifati bor ustozlariniki bor shuni senga aytsam
kirigizb qoya olasanmi tashlab bersam har bir ustozniki. menga eski
statistika qoshadigan joy ochib keyin qolda kirigizib otirish keremas"
- ya'ni qo'lda kiritish oynasi EMAS, to'g'ridan-to'g'ri import.

Rasmlardagi jadvallar: 2026 yanvar-iyul (iyul jadvali rasmda adashib
"IYUN" deb yozilgan - Jahongir tasdiqladi). Tuzikova Irina iyulga
qo'shilmaydi ("Irina opani qoshmaysan").

Har bir oy = bitta LessonObservation (total=foiz, max_total=100),
shunda ustoz profilidagi "dars sifati" o'rtachasi eski oylarni ham
hisobga oladi. rubric_key="legacy_2026_MM" bo'yicha idempotent -
server qayta yonganda takror yozilmaydi. Ism yozilishi oylar orasida
farq qiladi (Sultanova/Sultonova, Zoxidova/Zohidova, Umida/Umidaxon),
shuning uchun moslashuvchan normalizatsiya bilan taqqoslanadi.
Topilmagan ismlar asoschiga bir martalik vazifa bo'lib tushadi."""

from datetime import date

import models
import roles
from sqlalchemy.orm import Session

# (yil, oy) -> [(rasmdagi ism, foiz), ...]
LEGACY_DATA = {
    (2026, 1): [
        ("ABDURASULOV ABDULQODIR", 90.6),
        ("AKRAMOVA NODIRA", 83.8),
        ("BO'RIXO'DJAYEVA SHIRINABONU", 83.0),
        ("NABIJONOV BEKZOD", 81.2),
        ("ESHBOYEV SHAXZOD", 80.0),
        ("NABIYEV ASLIDDIN", 78.6),
        ("NASHIROVA UMIDAXON", 78.2),
        ("MIRZAMUROTOV ASADBEK", 77.8),
        ("ZOXIDOVA GO'ZAL", 77.5),
        ("TURAXODJAYEVA MASHHURA", 77.2),
        ("MUHIDDINOVA SHOHSANAM", 76.4),
        ("XAZRATQULOVA ORZIGUL", 76.1),
        ("SULTANOVA ZILOLA", 75.3),
        ("TOSHTEMIROVA SUG'DIYONA", 74.4),
        ("ABLONAZAROV ISROIL", 69.4),
    ],
    (2026, 2): [
        ("ABDURASULOV ABDULQODIR", 88.7),
        ("BO'RIXO'DJAYEVA SHIRINABONU", 83.4),
        ("SULTANOVA ZILOLA", 81.8),
        ("TURAXODJAYEVA MASHHURA", 81.6),
        ("MIRZAMUROTOV ASADBEK", 80.4),
        ("NABIJONOV BEKZOD", 79.2),
        ("ABDULATIPOV NODIR", 77.5),
        ("NABIYEV ASLIDDIN", 77.0),
        ("ABLONAZAROV ISROIL", 76.2),
        ("AKRAMOVA NODIRA", 75.8),
        ("NASHIROVA UMIDAXON", 75.6),
        ("ESHBOYEV SHAXZOD", 74.7),
        ("MUHIDDINOVA SHOHSANAM", 74.2),
        ("XAZRATQULOVA ORZIGUL", 72.5),
        ("ZOXIDOVA GO'ZAL", 69.7),
        ("TOSHTEMIROVA SUG'DIYONA", 68.0),
    ],
    (2026, 3): [
        ("ABDURASULOV ABDULQODIR", 90.0),
        ("TURAXODJAYEVA MASHHURA", 83.7),
        ("BO'RIXO'DJAYEVA SHIRINABONU", 83.0),
        ("NABIJONOV BEKZOD", 80.3),
        ("ESHBOYEV SHAXZOD", 78.2),
        ("NABIYEV ASLIDDIN", 77.6),
        ("AKRAMOVA NODIRA", 76.8),
        ("MUHIDDINOVA SHOHSANAM", 76.5),
        ("MIRZAMUROTOV ASADBEK", 75.1),
        ("SULTANOVA ZILOLA", 73.3),
        ("XAZRATQQULOVA ORZIGUL", 73.3),
        ("TOSHTEMIROVA SUG'DIYONA", 73.1),
        ("NASHIROVA UMIDAXON", 72.3),
        ("ABDULATIPOV NODIR", 72.0),
        ("ABLONAZAROV ISROIL", 72.0),
        ("ZOXIDOVA GO'ZAL", 65.3),
    ],
    (2026, 4): [
        ("ABDURASULOV ABDULQODIR", 88.5),
        ("ABDULATIPOV NODIR", 80.8),
        ("AKRAMOVA NODIRA", 79.3),
        ("BO'RIXO'DJAYEVA SHIRINABONU", 77.8),
        ("NABIJONOV BEKZOD", 77.2),
        ("NABIYEV ASLIDDIN", 76.9),
        ("ABLONAZAROV ISROIL", 76.8),
        ("ZOXIDOVA GO'ZAL", 75.6),
        ("NASHIROVA UMIDAXON", 75.5),
        ("ESHBOYEV SHAXZOD", 74.7),
        ("TURAXODJAYEVA MASHHURA", 73.2),
        ("SULTANOVA ZILOLA", 72.3),
        ("MUHIDDINOVA SHOHSANAM", 71.5),
        ("TOSHTEMIROVA SUG'DIYONA", 67.8),
        ("MIRZAMURATOV ASADBEK", 66.0),
    ],
    (2026, 5): [
        ("ALIMJANOV SARDOR", 84.6),
        ("NABIJONOV BEKZOD", 81.2),
        ("ESHBOYEV SHAXZOD", 79.5),
        ("BO'RIXO'DJAYEVA SHIRINABONU", 79.2),
        ("ABDULATIPOV NODIR", 77.4),
        ("TURAXODJAYEVA MASHHURA", 76.4),
        ("AKRAMOVA NODIRA", 75.6),
        ("NASHIROVA UMIDA", 75.2),
        ("MIRZAMUROTOV ASADBEK", 74.3),
        ("NABIYEV ASLIDDIN", 73.3),
        ("MUHIDDINOVA SHOXSANAM", 71.5),
        ("TOSHTEMIROVA SUG'DIYONA", 70.5),
        ("ZOHIDOVA GO'ZAL", 70.1),
        ("SULTONOVA ZILOLA", 63.9),
    ],
    (2026, 6): [
        ("BO'RIXO'DJAYEVA SHIRINABONU", 84.8),
        ("AKRAMOVA NODIRA", 84.4),
        ("TURAXODJAYEVA MASHHURA", 82.3),
        ("ESHBOYEV SHAXZOD", 80.4),
        ("NABIJONOV BEKZOD", 77.7),
        ("ABDULATIPOV NODIR", 75.2),
        ("ZOHIDOVA GO'ZAL", 73.8),
        ("NABIYEV ASLIDDIN", 73.7),
        ("MIRZAMUROTOV ASADBEK", 73.3),
        ("SULTONOVA ZILOLA", 72.5),
        ("NASHIROVA UMIDA", 71.2),
        ("MUHIDDINOVA SHOXSANAM", 69.9),
        ("TOSHTEMIROVA SUG'DIYONA", 69.5),
        ("TURSUNBOYEVA NAZIRA", 64.1),
    ],
    # Rasmda "IYUN" deb yozilgan, aslida IYUL (Jahongir tasdiqladi).
    # Tuzikova Irina ataylab yo'q: "Irina opani qoshmaysan".
    (2026, 7): [
        ("BO'RIXO'DJAYEVA SHIRINABONU", 84.6),
        ("TURAXODJAYEVA MASHHURA", 81.3),
        ("MIRFOZILOV SARDOR", 79.9),
        ("FAYZULLAYEVA GULNOZA", 77.6),
        ("TOSHTEMIROVA SUG'DIYONA", 75.9),
        ("AKRAMOVA NODIRA", 75.6),
        ("NABIYEV ASLIDDIN", 74.8),
        ("ESHBOYEV SHAXZOD", 74.3),
        ("NABIJONOV BEKZOD", 73.1),
        ("ABDULATIPOV NODIR", 71.8),
        ("SULTONOVA ZILOLA", 69.8),
        ("MIRZAMUROTOV ASADBEK", 69.3),
        ("NASHIROVA UMIDA", 64.8),
        ("MUHIDDINOVA SHOXSANAM", 63.1),
        ("TURSUNBOYEVA NAZIRA", 62.4),
    ],
}

_MONTH_UZ = {1: "yanvar", 2: "fevral", 3: "mart", 4: "aprel",
             5: "may", 6: "iyun", 7: "iyul", 8: "avgust",
             9: "sentyabr", 10: "oktyabr", 11: "noyabr", 12: "dekabr"}

_APOS = "ʻ‘’'`"


def _norm(token: str) -> str:
    """Ism yozilish farqlarini tekislaydi.

    Oylar orasida bir odam har xil yozilgan: Sultanova/Sultonova,
    Zoxidova/Zohidova, Mirzamurotov/Mirzamuratov, Shohsanam/Shoxsanam,
    Xazratqulova/Xazratqqulova, Turaxodjayeva/Turaxo'jayeva. Shuning
    uchun: apostroflar olib tashlanadi, x->h, dj->j, o->a, ketma-ket
    takror harflar bittaga tushiriladi. Ikkala tomon ham shu qoida
    bilan normalizatsiya qilinadi - taqqoslash adolatli."""
    t = token.lower()
    for ch in _APOS:
        t = t.replace(ch, "")
    t = t.replace("x", "h").replace("dj", "j").replace("o", "a")
    out = []
    for ch in t:
        if not out or out[-1] != ch:
            out.append(ch)
    return "".join(c for c in out if c.isalpha())


def _tok_match(a: str, b: str) -> bool:
    """To'liq mosligi yoki biri ikkinchisining boshi (kamida 4 harf).

    "Umida" va "Umidaxon" bitta odam - prefiks moslik shuni qoplaydi."""
    if a == b:
        return True
    if len(a) >= 4 and len(b) >= 4:
        return a.startswith(b) or b.startswith(a)
    return False


def _find_teacher(teachers, name: str):
    """Rasmdagi "FAMILIYA ISM" ni bazadagi ustozga bog'laydi.

    Bazada ism-familiya tartibi boshqacha bo'lishi mumkin, shuning
    uchun tartibga qaramay: har bir token bazadagi ismning biror
    tokeniga mos kelishi shart. Bitta aniq nomzod bo'lsa - shu.
    Ikki xil ustozga mos kelsa - xato yozmaslik uchun o'tkazib
    yuboriladi va asoschiga xabar qilinadi."""
    want = [_norm(x) for x in name.split() if _norm(x)]
    hits = []
    for t, toks in teachers:
        used = set()
        ok = True
        for w in want:
            found = None
            for i, tt in enumerate(toks):
                if i in used:
                    continue
                if _tok_match(w, tt):
                    found = i
                    break
            if found is None:
                ok = False
                break
            used.add(found)
        if ok:
            hits.append(t)
    return hits[0] if len(hits) == 1 else None


def seed_legacy_quality(db: Session) -> int:
    """Import. Qaytaradi: nechta yangi yozuv kiritildi."""
    all_teachers = db.query(models.Teacher).all()
    if not all_teachers:
        return 0
    prepared = [(t, [_norm(x) for x in (t.full_name or "").split()
                     if _norm(x)]) for t in all_teachers]

    inserted, unmatched = 0, []
    for (year, month), rows in sorted(LEGACY_DATA.items()):
        rk = f"legacy_{year}_{month:02d}"
        # Shu oy uchun allaqachon yozilgan ustozlar - takrorlamaymiz
        done = {tid for (tid,) in db.query(
            models.LessonObservation.teacher_id).filter(
            models.LessonObservation.rubric_key == rk).all()}
        for name, score in rows:
            t = _find_teacher(prepared, name)
            if t is None:
                unmatched.append(f"{name} ({_MONTH_UZ[month]}, {score})")
                continue
            if t.id in done:
                continue
            db.add(models.LessonObservation(
                rubric_key=rk,
                target_type="teacher",
                stage="legacy",
                attempt=1,
                teacher_id=t.id,
                date=date(year, month, 15),
                total=float(score),
                max_total=100.0,
                percent=float(score),
                note=(f"Eski tizimdan import - {year}-yil "
                      f"{_MONTH_UZ[month]} oyi natijasi"),
                observer="Import (eski tizim)",
            ))
            done.add(t.id)
            inserted += 1
    if inserted:
        db.commit()

    # Topilmaganlar haqida asoschiga BIR martalik vazifa - jim
    # yo'qolib ketmasin. Ustoz bazaga qo'shilgach server qayta
    # yonganda import o'zi topib yozadi.
    if unmatched and inserted:
        try:
            from common import _hr_task_for
            who = (db.query(models.User)
                   .filter(models.User.role == roles.FOUNDER,
                           models.User.is_active == 1).first())
            if who:
                _hr_task_for(
                    db, who.id,
                    title="Eski dars sifati - ba'zi ustozlar topilmadi",
                    body=("Eski statistikadagi quyidagi ismlar bazadagi "
                          "ustozlarga mos kelmadi (yozuv kiritilmadi). "
                          "Ustoz kartasi ochilsa yoki ismi to'g'rilansa "
                          "keyingi qayta ishga tushishda avtomat "
                          "qo'shiladi:\n\n- " + "\n- ".join(unmatched)),
                    days=7)
                db.commit()
        except Exception:
            db.rollback()
    return inserted
