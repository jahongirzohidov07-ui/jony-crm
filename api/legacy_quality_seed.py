"""Eski tizimdagi ustozlar dars-sifati statistikasini import qilish.

Jahongir: "eski dars sifati bor ustozlariniki bor shuni senga aytsam
kirigizb qoya olasanmi tashlab bersam har bir ustozniki. menga eski
statistika qoshadigan joy ochib keyin qolda kirigizib otirish keremas"
- ya'ni qo'lda kiritish oynasi EMAS, to'g'ridan-to'g'ri import.

Rasmlardagi jadvallar: 2025 yanvar-dekabr ('bu 2025 yilniki bu')
va 2026 yanvar-iyul (2026 iyul jadvali rasmda adashib
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
    # ============ 2025 YIL (Jahongir: "bu 2025 yilniki bu") ============
    # Har ustozning oylik qiymatlari rasmdagi YILLIK ustuni bilan
    # solishtirib tekshirildi - o'rtachalar mos tushdi.
    (2025, 1): [
        ("BO'RIXODJAYEVA SHIRINABONU", 77.9),
        ("NABIJONOV BEKZOD", 80.3),
        ("AKRAMOVA NODIRA", 84.2),
        ("NABIJONOVA SEVINCH", 75.4),
        ("ESHBOYEV SHAXZOD", 83.7),
        ("ABLONAZAROV ISROIL", 79.8),
        ("TOSHTEMIROVA SUG'DIYONA", 73.6),
        ("AZIZOVA NODIRA", 75.7),
        ("NOSIROV SHERZOD", 73.9),
        ("JUMABOYEVA DURDONA", 70.5),
        ("ABDULATIPOV NODIR", 69.6),
        ("XAZRATQULOV MARDONBEK", 69.0),
        ("MIRZAMAHMUDOVA SARVINOZ", 62.3),
    ],
    (2025, 2): [
        ("BO'RIXODJAYEVA SHIRINABONU", 76.4),
        ("NABIJONOV BEKZOD", 80.0),
        ("AKRAMOVA NODIRA", 78.3),
        ("NABIJONOVA SEVINCH", 83.1),
        ("ESHBOYEV SHAXZOD", 75.5),
        ("ABLONAZAROV ISROIL", 76.3),
        ("MUHIDDINOVA SHOHSANAM", 74.7),
        ("TOSHTEMIROVA SUG'DIYONA", 77.4),
        ("AZIZOVA NODIRA", 74.0),
        ("NOSIROV SHERZOD", 80.9),
        ("JUMABOYEVA DURDONA", 72.7),
        ("ABDULATIPOV NODIR", 76.2),
        ("XAZRATQULOV MARDONBEK", 74.3),
        ("MIRZAMAHMUDOVA SARVINOZ", 76.5),
    ],
    (2025, 3): [
        ("BO'RIXODJAYEVA SHIRINABONU", 78.6),
        ("NABIJONOV BEKZOD", 82.6),
        ("AKRAMOVA NODIRA", 83.3),
        ("NABIJONOVA SEVINCH", 80.1),
        ("ESHBOYEV SHAXZOD", 74.9),
        ("ABLONAZAROV ISROIL", 66.1),
        ("MUHIDDINOVA SHOHSANAM", 76.3),
        ("TOSHTEMIROVA SUG'DIYONA", 66.5),
        ("NOSIROV SHERZOD", 73.3),
        ("ABDULATIPOV NODIR", 73.2),
        ("XAZRATQULOV MARDONBEK", 67.4),
        ("MIRZAMAHMUDOVA SARVINOZ", 60.0),
    ],
    (2025, 4): [
        ("BO'RIXODJAYEVA SHIRINABONU", 75.7),
        ("NABIJONOV BEKZOD", 82.0),
        ("AKRAMOVA NODIRA", 65.0),
        ("NABIJONOVA SEVINCH", 71.6),
        ("ESHBOYEV SHAXZOD", 75.9),
        ("ABLONAZAROV ISROIL", 75.7),
        ("MUHIDDINOVA SHOHSANAM", 73.5),
        ("TOSHTEMIROVA SUG'DIYONA", 66.5),
        ("NOSIROV SHERZOD", 76.9),
        ("ABDULATIPOV NODIR", 81.5),
        ("XAZRATQULOV MARDONBEK", 74.2),
        ("MIRZAMAHMUDOVA SARVINOZ", 66.7),
    ],
    (2025, 5): [
        ("BO'RIXODJAYEVA SHIRINABONU", 78.2),
        ("NABIJONOV BEKZOD", 71.7),
        ("AKRAMOVA NODIRA", 72.9),
        ("NABIJONOVA SEVINCH", 68.3),
        ("ESHBOYEV SHAXZOD", 75.9),
        ("ABLONAZAROV ISROIL", 74.7),
        ("MUHIDDINOVA SHOHSANAM", 76.4),
        ("TOSHTEMIROVA SUG'DIYONA", 72.0),
        ("SULTONOVA ZILOLA", 78.9),
        ("NOSIROV SHERZOD", 67.0),
        ("ABDULATIPOV NODIR", 75.6),
        ("XAZRATQULOV MARDONBEK", 71.5),
    ],
    (2025, 6): [
        ("ABDURASULOV ABDULQODIR", 79.7),
        ("BO'RIXODJAYEVA SHIRINABONU", 81.0),
        ("NABIJONOV BEKZOD", 76.8),
        ("AKRAMOVA NODIRA", 74.7),
        ("NABIJONOVA SEVINCH", 75.4),
        ("ESHBOYEV SHAXZOD", 75.7),
        ("ABLONAZAROV ISROIL", 80.4),
        ("MUHIDDINOVA SHOHSANAM", 72.1),
        ("TOSHTEMIROVA SUG'DIYONA", 74.6),
        ("SULTONOVA ZILOLA", 80.7),
        ("XAZRATQULOV MARDONBEK", 68.8),
    ],
    (2025, 7): [
        ("ABDURASULOV ABDULQODIR", 77.6),
        ("BO'RIXODJAYEVA SHIRINABONU", 79.9),
        ("NABIJONOV BEKZOD", 77.0),
        ("AKRAMOVA NODIRA", 76.1),
        ("NABIJONOVA SEVINCH", 75.6),
        ("TURAXODJAYEVA MASHHURA", 72.0),
        ("ESHBOYEV SHAXZOD", 80.1),
        ("ABLONAZAROV ISROIL", 79.9),
        ("MUHIDDINOVA SHOHSANAM", 78.5),
        ("TOSHTEMIROVA SUG'DIYONA", 78.1),
        ("SULTONOVA ZILOLA", 62.2),
    ],
    (2025, 8): [
        ("ABDURASULOV ABDULQODIR", 76.7),
        ("BO'RIXODJAYEVA SHIRINABONU", 79.8),
        ("NABIJONOV BEKZOD", 81.4),
        ("AKRAMOVA NODIRA", 85.4),
        ("NABIJONOVA SEVINCH", 80.8),
        ("TURAXODJAYEVA MASHHURA", 74.4),
        ("ESHBOYEV SHAXZOD", 79.1),
        ("ABLONAZAROV ISROIL", 77.4),
        ("MUHIDDINOVA SHOHSANAM", 69.8),
        ("TOSHTEMIROVA SUG'DIYONA", 76.2),
        ("SULTONOVA ZILOLA", 73.5),
    ],
    (2025, 9): [
        ("ABDURASULOV ABDULQODIR", 86.4),
        ("BO'RIXODJAYEVA SHIRINABONU", 85.4),
        ("NABIJONOV BEKZOD", 82.1),
        ("NABIJONOVA SEVINCH", 75.5),
        ("TURAXODJAYEVA MASHHURA", 77.1),
        ("XAZRATQULOVA ORZIGUL", 86.7),
        ("NABIYEV ASLIDDIN", 78.9),
        ("NASHIROVA UMIDA", 81.4),
        ("ESHBOYEV SHAXZOD", 78.6),
        ("ABLONAZAROV ISROIL", 76.7),
        ("MUHIDDINOVA SHOHSANAM", 69.8),
        ("TOSHTEMIROVA SUG'DIYONA", 73.0),
        ("SULTONOVA ZILOLA", 72.1),
    ],
    (2025, 10): [
        ("ABDURASULOV ABDULQODIR", 77.0),
        ("BO'RIXODJAYEVA SHIRINABONU", 83.0),
        ("NABIJONOV BEKZOD", 83.2),
        ("AKRAMOVA NODIRA", 79.1),
        ("NABIJONOVA SEVINCH", 85.0),
        ("TURAXODJAYEVA MASHHURA", 82.0),
        ("XAZRATQULOVA ORZIGUL", 77.3),
        ("NABIYEV ASLIDDIN", 72.3),
        ("NASHIROVA UMIDA", 74.2),
        ("ESHBOYEV SHAXZOD", 70.6),
        ("ABLONAZAROV ISROIL", 76.8),
        ("MUHIDDINOVA SHOHSANAM", 70.8),
        ("TOSHTEMIROVA SUG'DIYONA", 69.7),
        ("SULTONOVA ZILOLA", 68.5),
    ],
    (2025, 11): [
        ("ABDURASULOV ABDULQODIR", 80.1),
        ("BO'RIXODJAYEVA SHIRINABONU", 86.8),
        ("NABIJONOV BEKZOD", 81.2),
        ("AKRAMOVA NODIRA", 82.4),
        ("NABIJONOVA SEVINCH", 83.9),
        ("TURAXODJAYEVA MASHHURA", 81.1),
        ("XAZRATQULOVA ORZIGUL", 75.1),
        ("NABIYEV ASLIDDIN", 81.2),
        ("NASHIROVA UMIDA", 71.9),
        ("ESHBOYEV SHAXZOD", 69.0),
        ("ABLONAZAROV ISROIL", 78.5),
        ("MUHIDDINOVA SHOHSANAM", 73.5),
        ("TOSHTEMIROVA SUG'DIYONA", 67.8),
        ("SULTONOVA ZILOLA", 71.4),
    ],
    (2025, 12): [
        ("ABDURASULOV ABDULQODIR", 88.6),
        ("BO'RIXODJAYEVA SHIRINABONU", 83.3),
        ("NABIJONOV BEKZOD", 80.3),
        ("AKRAMOVA NODIRA", 83.6),
        ("NABIJONOVA SEVINCH", 78.0),
        ("TURAXODJAYEVA MASHHURA", 77.8),
        ("XAZRATQULOVA ORZIGUL", 69.7),
        ("NABIYEV ASLIDDIN", 74.7),
        ("NASHIROVA UMIDA", 79.0),
        ("ESHBOYEV SHAXZOD", 78.0),
        ("ABLONAZAROV ISROIL", 69.0),
        ("MUHIDDINOVA SHOHSANAM", 69.5),
        ("TOSHTEMIROVA SUG'DIYONA", 75.2),
        ("SULTONOVA ZILOLA", 67.2),
    ],
    # ============ 2026 YIL (yanvar-iyul) ============
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


def _one_edit(a: str, b: str) -> bool:
    """Ikkala so'z bitta harf farqi bilan bir xilmi.

    "Abdulqodir" (rasmda) va "Abduqodir" (bazada) bitta odam - L
    harfi tushib qolgan. Shunday mayda imlo farqlari uchun."""
    la, lb = len(a), len(b)
    if abs(la - lb) > 1:
        return False
    if la == lb:
        return sum(1 for x, y in zip(a, b) if x != y) <= 1
    if la > lb:
        a, b, la, lb = b, a, lb, la
    i = 0
    while i < la and a[i] == b[i]:
        i += 1
    return a[i:] == b[i + 1:]


def _tok_match(a: str, b: str) -> bool:
    """To'liq mosligi, biri ikkinchisining boshi (kamida 4 harf),
    yoki uzun so'zlarda bitta harf farqi.

    "Umida"/"Umidaxon" bitta odam - prefiks moslik shuni qoplaydi.
    "Abdulqodir"/"Abduqodir" ham bitta odam - bir harf farqi.
    Adashish xavfi yo'q: ism ham, familiya ham birga mos kelishi
    shart, ikki ustozga birdek to'g'ri kelsa umuman yozilmaydi."""
    if a == b:
        return True
    if len(a) >= 4 and len(b) >= 4 and (a.startswith(b) or b.startswith(a)):
        return True
    if len(a) >= 6 and len(b) >= 6 and _one_edit(a, b):
        return True
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
