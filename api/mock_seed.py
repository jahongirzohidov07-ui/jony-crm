# -*- coding: utf-8 -*-
"""MOCK TEST BAZASI (2026-09-26).

Jahongir: "sen shularni 1x1 kopya qilmaysan, sen xuddi shu pattern va
uslubdagi Mock testlar tuzib berasan haqiqiy IELTS CDI testlari bilan
1x1 kopya bo'lishi kerak ... va katta mock test bazasini yarat".

Shuning uchun bu yerdagi HAMMA matn — Jony Academy uchun yangidan
yozilgan: Cambridge kitoblaridan birorta gap ham ko'chirilmagan.
Ko'chirilgani faqat FORMAT: bo'limlar soni, savollar soni, savol
turlari, ko'rsatma matnlari va band jadvali.

  mock_data/<imtihon>/*.json — ielts/ va cefr/ papkalari. Har fayl
  bitta bo'lim (Listening / Reading / Writing / Speaking) va bitta
  variant. Fayl ichida:
    key      — seed kaliti (bir marta yoziladi, keyin examiner tahrirlaydi)
    section  — listening | reading | writing | speaking
    variant  — A..E
    levels   — qaysi guruh darajalariga yoziladi
    parts    — exam_online.clean_parts kutadigan ko'rinishda

  Bir daraja + "mock" ichida bir xil TUZILISHdagi variantlar avtomat
  aralashadi (exam_online.mix_parts): Listening A ning 1-qismi, C ning
  2-qismi... — ustoz qaysi savollar tushishini oldindan bilolmaydi.
  IELTS Listening (10,10,10,10), IELTS Reading (13,13,14), CEFR
  Listening (8,6,4,5,6,6), CEFR Reading (6,8,6,9,6), Writing va
  Speaking tuzilishlari boshqa-boshqa, shuning uchun ular o'zaro
  aralashmaydi.

  CEFR Multilevel: darajasi "cefr". Kitoblarda xom balldan CEFR
  darajasiga RASMIY o'tkazish jadvali yo'q (ikkala qo'llanma ham
  mytests.uz ga yo'naltiradi), shuning uchun avtomat band yozilmaydi —
  examiner xom ballni ko'rib darajani o'zi qo'yadi (exam_online.
  _write_result). IELTS Listening/Reading uchun esa rasmiy jadval bor.
"""
import json
import os
import re
from collections import defaultdict

from sqlalchemy.orm import Session

import models
from common import _seed_done, _seed_mark

DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mock_data")


def _files() -> list:
    """mock_data ichidagi har papka bitta imtihon turi: ielts, cefr, ..."""
    if not os.path.isdir(DIR):
        return []
    out = []
    for sub in sorted(os.listdir(DIR)):
        d = os.path.join(DIR, sub)
        if not os.path.isdir(d):
            continue
        for name in sorted(os.listdir(d)):
            if not name.endswith(".json"):
                continue
            with open(os.path.join(d, name), encoding="utf-8") as fh:
                tpl = json.load(fh)
            # Har bo'limga "ielts_listening" / "cefr_reading" kabi aniq
            # ko'nikma belgisi qo'yiladi: xom ballni qaysi jadval
            # bo'yicha bandga o'girishni shu hal qiladi. Bo'lim nomiga
            # tayanib bo'lmaydi — IELTS Listening bo'limlari ham
            # shunchaki "Part 1" deb nomlangan.
            skill = f"{sub}_{tpl.get('section') or ''}".strip("_")
            for part in tpl.get("parts") or []:
                part.setdefault("skill", skill)
            out.append(tpl)
    return out


_DUP_RE = re.compile(r"(\s*\(dublikat\))+\s*$")
_OLD_SUFFIX = " (eski format)"
# Mock seedining o'z qulf kaliti. Boshqa seedlar bilan umumiy bo'lmasin:
# 20260926 — seed_variants, 20260927 — seed_math, 20260925 — vocab.
MOCK_SEED_LOCK = 20260928


def canon_title(title) -> str:
    """Sarlavhadan tizim qo'shgan "(dublikat)" qo'shimchasini olib
    tashlaydi: "IELTS Mock · Reading — Variant A (dublikat)" ->
    "IELTS Mock · Reading — Variant A"."""
    return _DUP_RE.sub("", (title or "").strip())


FIGURES_SPEC = os.path.join(DIR, "_figures.json")


def _sha(v) -> str:
    import hashlib
    return hashlib.sha1(str(v or "").encode("utf-8")).hexdigest()[:16]


def apply_figures(db: Session) -> int:
    """RASMLAR (2026-09-27, Jahongir: "listeningda map debsan qani map",
    "bar Chartingni rasmi qani").

    Listening xarita/plan savollari va Writing Task 1 grafiklari ilgari
    faqat SO'Z bilan tasvirlangan edi. mock_data fayllarida endi rasm
    (SVG) va tavsifsiz matn bor; seed esa bazadagi mavjud shablonni
    qayta yozmaydi — shuning uchun o'zgarish shu yerda ko'chiriladi.

    mock_data/_figures.json: [{"title", "part", "q", "old": {"instructions":
    sha, "passage": sha, "q": sha}}] — "old" eski (tavsifli) matnning
    xeshi. Matn faqat bazada aynan o'sha eski holida turgan bo'lsa
    almashtiriladi: examiner o'zgartirgan matnga tegilmaydi. Rasm esa
    savol matni fayldagiga mos bo'lsa qo'shiladi (buzmaydigan o'zgarish).
    Faqat faol, tizim yaratgan (JonyOS) shablonlar. Commit chaqiruvchida.
    """
    import exam_online as _eo
    if not os.path.exists(FIGURES_SPEC):
        return 0
    with open(FIGURES_SPEC, encoding="utf-8") as fh:
        spec = json.load(fh)
    by_title = {tpl["title"]: tpl for tpl in _files()}
    n = 0
    for s in spec:
        tpl = by_title.get(s.get("title"))
        if not tpl:
            continue
        src_parts = _eo.clean_parts(tpl["parts"])
        pi, qi, old = int(s["part"]), int(s["q"]), s.get("old") or {}
        if pi >= len(src_parts) or qi >= len(src_parts[pi]["questions"]):
            continue
        src_p, src_q = src_parts[pi], src_parts[pi]["questions"][qi]
        rows = (db.query(models.ExamTemplate)
                .filter(models.ExamTemplate.kind == "mock",
                        models.ExamTemplate.is_active == 1,
                        models.ExamTemplate.created_by == "JonyOS").all())
        for t in rows:
            if canon_title(t.title) != s["title"]:
                continue
            parts = _eo._load(t.parts)
            if pi >= len(parts) or qi >= len(parts[pi].get("questions") or []):
                continue
            p, q = parts[pi], parts[pi]["questions"][qi]
            changed = False
            for fld in ("instructions", "passage"):
                if (old.get(fld) and _sha(p.get(fld)) == old[fld]
                        and (p.get(fld) or "") != (src_p.get(fld) or "")):
                    p[fld] = src_p.get(fld) or ""
                    changed = True
            cur_q = _eo.strip_q_prefix(q.get("q"))
            if (old.get("q") and _sha(cur_q) == old["q"]
                    and cur_q != src_q["q"]):
                q["q"] = src_q["q"]
                changed = True
            if (src_q.get("image") and not q.get("image")
                    and _eo.strip_q_prefix(q.get("q")) == src_q["q"]):
                q["image"] = src_q["image"]
                changed = True
            if changed:
                t.parts = json.dumps(parts, ensure_ascii=False)
                n += 1
    return n


def retire_old_speaking(db: Session) -> int:
    """ESKI 3 QISMLI CEFR SPEAKING nomini bo'shatadi (2026-09-27).

    cefr_speaking_old_off_v1 migratsiyasi eski 3 qismli Speaking'ni
    o'chirgan, lekin NOMINI o'zgartirmagan. Yangi 4 qismli fayllarning
    C va E-I variantlari aynan o'sha nomlarni saqlagan — shuning uchun
    seed "bu nom bazada bor" deb ularni hech qachon yozmagan. Jahongir
    ekranda CEFR Speaking'dan faqat D va J ni ko'rgan edi.

    Mezon migratsiyaning o'zinikidek: tizim yaratgan (JonyOS), faol
    emas, CEFR, sarlavhasida "Speaking" va qismlarida "Part 1.1" yo'q.
    Nomiga " (eski format)" qo'shiladi — yozuv o'chirilmaydi (o'tkazilgan
    imtihonlar unga FK bilan bog'langan bo'lishi mumkin). Commit
    chaqiruvchida.
    """
    import exam_online as _eo
    n = 0
    for t in (db.query(models.ExamTemplate)
              .filter(models.ExamTemplate.kind == "mock",
                      models.ExamTemplate.level == "cefr",
                      models.ExamTemplate.is_active != 1,
                      models.ExamTemplate.created_by == "JonyOS").all()):
        title = t.title or ""
        if "speaking" not in title.lower() or title.endswith(_OLD_SUFFIX):
            continue
        parts = _eo._load(t.parts)
        if "Part 1.1" in [str(p.get("title") or "") for p in parts]:
            continue
        t.title = canon_title(title) + _OLD_SUFFIX
        n += 1
    return n


def restore_hidden(db: Session, titles: set) -> int:
    """Noto'g'ri "dublikat" deb yashirilgan mock shablonlarini tiklaydi.

    2026-09-27 gacha exam_online dagi dublikat qoidasi mockni
    (daraja, tur, unit, variant) bo'yicha solishtirardi — Listening A,
    Reading A, Writing A bitta hisoblanib, Listening'dan boshqasi har
    startda yashirilardi (examinerning o'z mocklari ham, agar harfi
    tizim mockiniki bilan bir xil bo'lsa). Qoida tuzatildi; bu yerda
    o'sha zarar qaytariladi. Har (daraja, asl sarlavha, variant) uchun:

      * faol yozuv bor — tegilmaydi;
      * aynan asl nomli, lekin faol emas yozuv bor — uni examiner (yoki
        bir martalik migratsiya) ATAYLAB o'chirgan, tegilmaydi;
      * faqat "(dublikat)" nusxalar qolgan — eng yangisi asl nomi bilan
        qaytariladi, qolganlari yashirin qoladi.

    Tizim (JonyOS) yaratgan yozuv faqat sarlavhasi joriy mock_data
    faylida bo'lsa tiklanadi: fayldan olib tashlangan yoki nomi
    o'zgargan eski mazmun qayta tirilmasin. Examiner yaratganlari —
    har doim. Commit chaqiruvchida.
    """
    groups = defaultdict(list)
    # Faqat kerakli ustunlar: "parts" (~30 KB) 1800+ yashirin nusxa uchun
    # har startda Postgres'dan tortilmasin.
    from sqlalchemy.orm import load_only
    T = models.ExamTemplate
    for t in (db.query(T)
              .options(load_only(T.id, T.level, T.title, T.variant,
                                 T.is_active, T.created_by))
              .filter(T.kind == "mock")
              .order_by(T.id).all()):
        c = canon_title(t.title)
        if (t.created_by or "") == "JonyOS" and c not in titles:
            continue
        groups[(t.level, c, t.variant)].append(t)
    n = 0
    for (_lv, c, _v), rows in groups.items():
        if any(t.is_active == 1 for t in rows):
            continue
        if any((t.title or "").strip() == c for t in rows):
            continue
        keep = rows[-1]
        keep.title = c
        keep.is_active = 1
        n += 1
    return n


def audit(db: Session) -> str:
    """Startdagi bir qatorlik hisobot: qaysi bo'limda nechta faol shablon
    va qaysi variantlar. Production natijasini loglardan tekshirish
    uchun — ekranni ochmasdan."""
    cnt, letters, hidden = defaultdict(int), defaultdict(set), 0
    for lv, ti, act, var in (db.query(models.ExamTemplate.level,
                                      models.ExamTemplate.title,
                                      models.ExamTemplate.is_active,
                                      models.ExamTemplate.variant)
                             .filter(models.ExamTemplate.kind == "mock")
                             .all()):
        if act != 1:
            hidden += 1
            continue
        sk = skill_from_template(lv, canon_title(ti)) or "?"
        cnt[sk] += 1
        letters[sk].add(var or "A")
    body = " ".join(f"{k}={cnt[k]}({''.join(sorted(letters[k]))})"
                    for k in sorted(cnt))
    return f"faol: {body} | yashirin: {hidden}"


def _strict_col(db: Session) -> str:
    """Qat'iy rejim ustuni jonli bazada bormi (2026-09-27). Vercel
    loglarida sxema/migratsiya qatorlari ba'zan yo'qoladi, [mock-audit]
    esa har sovuq startda ko'rinadi — tekshiruv shu qatorda turadi."""
    try:
        db.query(models.ExamSubmission.away_eids).limit(1).all()
        return "bor"
    except Exception as e:      # noqa: BLE001
        db.rollback()
        return f"YO'Q ({type(e).__name__})"


def audit_off(db: Session, titles: set, limit: int = 40) -> str:
    """Seed nomi bilan, lekin FAOL EMAS yozuvlar (dublikat emas): ularni
    kimdir ataylab o'chirgan — examiner yoki bir martalik migratsiya.
    restore_hidden bularga tegmaydi; ro'yxat faqat ko'rish uchun."""
    import exam_online as _eo
    out = []
    for t in (db.query(models.ExamTemplate)
              .filter(models.ExamTemplate.kind == "mock",
                      models.ExamTemplate.is_active != 1)
              .order_by(models.ExamTemplate.id).all()):
        ti = (t.title or "").strip()
        if ti not in titles:
            continue
        sk = skill_from_template(t.level, ti) or "?"
        out.append(f"{sk}:{t.variant or 'A'}@{t.level}"
                   f"(qism={len(_eo._load(t.parts))},{t.created_by or '-'})")
    more = f" +{len(out) - limit}" if len(out) > limit else ""
    return f"ataylab o'chirilgan: {len(out)} {' '.join(out[:limit])}{more}"


def _xact_lock(db: Session, key: int) -> bool:
    """Parallel sovuq startlar (Vercel 2-4 instansiya) bir vaqtda yozib
    dublikat qilmasin. TRANZAKSIYA qulfi: commit/rollback bilan o'zi
    bo'shaydi — sessiya qulfidek pooldagi ulanishda osilib qolmaydi.
    Postgres bo'lmasa (SQLite testlar) — qulf shart emas."""
    try:
        from sqlalchemy import text as _sql
        if db.bind.dialect.name != "postgresql":
            return True
        return bool(db.execute(_sql("SELECT pg_try_advisory_xact_lock(:k)"),
                               {"k": key}).scalar())
    except Exception:           # noqa: BLE001
        db.rollback()
        return True


def skill_from_template(level, title) -> str:
    """Shablon sarlavhasi va darajasidan ko'nikma belgisi.

    Eski yozuvlarda bo'limlarda "skill" maydoni yo'q edi (u 2026-09-26
    da qo'shildi), shuning uchun ular guruhlashda bir-biriga qo'shilib
    ketardi: CEFR bo'limlari yo'qolib, IELTS "?" bo'lib chiqardi.
    """
    t = (title or "").lower()
    if "challenge" in t:
        bank = "challenge25"
    elif (level or "") == "cefr":
        bank = "cefr"
    else:
        bank = "ielts"
    for sec in ("listening", "reading", "writing", "speaking"):
        if sec in t:
            return f"{bank}_{sec}"
    return ""


def backfill_skills(db: Session) -> int:
    """Eski mock shablonlariga ko'nikma belgisini yozadi.

    Faqat FAOL shablonlar (2026-09-27): bazada 1800 dan ortiq yashirin
    "(dublikat)" nusxa bor (seed va dublikat qoidasi loopining qoldig'i)
    — har sovuq startda ularning har birini (~30 KB) o'qish o'nlab MB
    bo'lardi. Yashirin nusxa tiklansa, keyingi startda shu yerda
    to'ldiriladi."""
    import exam_online as _eo
    n = 0
    for t in (db.query(models.ExamTemplate)
              .filter(models.ExamTemplate.kind == "mock",
                      models.ExamTemplate.is_active == 1).all()):
        parts = _eo._load(t.parts)
        if not parts or all((p.get("skill") or "").strip() for p in parts):
            continue
        sk = skill_from_template(t.level, t.title)
        if not sk:
            continue
        for part in parts:
            if not (part.get("skill") or "").strip():
                part["skill"] = sk
        t.parts = json.dumps(parts, ensure_ascii=False)
        n += 1
    if n:
        db.commit()
    return n


def seed_mocks(db: Session) -> None:
    """Mock shablonlarini bazaga bir marta yozadi. Kalit belgilangach
    qayta yozilmaydi — examinerlar boshlig'i CRM'da o'zi tahrirlaydi."""
    import exam_online as _eo

    # ESKI CEFR SPEAKING (bir martalik, 2026-09-26). Avvalgi Speaking
    # shablonlari IELTS uslubida 3 qismli edi; rasmiy Multilevel
    # formati 4 qismli (Part 1.1 / 1.2 / 2 / 3). Eskilari bazada
    # qolib ketmasin — yashiriladi, o'chirilmaydi (examiner kerak
    # bo'lsa Test bazasidan qaytarib yoqa oladi).
    if not _seed_done(db, "cefr_speaking_old_off_v1"):
        try:
            import exam_online as _eo
            n = 0
            for t in (db.query(models.ExamTemplate)
                      .filter(models.ExamTemplate.kind == "mock",
                              models.ExamTemplate.level == "cefr",
                              models.ExamTemplate.is_active == 1).all()):
                parts = _eo._load(t.parts)
                titles = [str(p.get("title") or "") for p in parts]
                if "Speaking" in (t.title or "") and "Part 1.1" not in titles:
                    t.is_active = 0
                    n += 1
            db.commit()
            if n:
                print(f"[seed] eski CEFR Speaking shablonlari yashirildi: {n}")
            _seed_mark(db, "cefr_speaking_old_off_v1")
        except Exception as e:          # noqa: BLE001
            db.rollback()
            print(f"[seed] eski CEFR Speaking: {e}")

    # TAKRORLANGAN RAQAM VA HARF (bir martalik, 2026-09-27, Jahongir
    # skrinshoti: "11. 11 The land ..." va "A A a reservoir."). Bazadagi
    # faol mock shablonlaridan savol raqami va variant harfi prefiksi
    # olib tashlanadi (exam_online.strip_prefixes). Idempotent: ikki
    # instansiya bir vaqtda ishlatsa ham natija bir xil.
    if not _seed_done(db, "mock_prefix_strip_v1"):
        try:
            n = 0
            for t in (db.query(models.ExamTemplate)
                      .filter(models.ExamTemplate.kind == "mock",
                              models.ExamTemplate.is_active == 1).all()):
                parts = _eo._load(t.parts)
                new = _eo.strip_prefixes(parts)
                if new != parts:
                    t.parts = json.dumps(new, ensure_ascii=False)
                    n += 1
            db.commit()
            _seed_mark(db, "mock_prefix_strip_v1")
            print(f"[seed] mock savol/variant prefikslari tozalandi: {n}")
        except Exception as e:          # noqa: BLE001
            db.rollback()
            print(f"[seed] mock prefikslari: {e}")

    # RASMLAR (bir martalik, 2026-09-27): listening xarita/plan va
    # Writing Task 1 grafiklari bazadagi shablonlarga ko'chiriladi.
    # Prefiks tozalashdan KEYIN — savol matni tozalangan holda
    # solishtiriladi.
    if not _seed_done(db, "mock_figures_v1"):
        try:
            n = apply_figures(db)
            db.commit()
            _seed_mark(db, "mock_figures_v1")
            print(f"[seed] mock rasmlari (xarita, grafik) qo'shildi: {n}")
        except Exception as e:          # noqa: BLE001
            db.rollback()
            print(f"[seed] mock rasmlari: {e}")

    # KO'NIKMA BELGISINI TO'LDIRISH (2026-09-27). Bazadagi eski
    # shablonlarda bu maydon yo'q — ularsiz "Mock testlar" jadvali
    # noto'g'ri guruhlanardi. Har startda tekshiriladi (arzon:
    # belgisi bor yozuvlar chetlab o'tiladi).
    try:
        n = backfill_skills(db)
        if n:
            print(f"[seed] mock shablonlariga ko'nikma belgisi: {n}")
    except Exception as e:          # noqa: BLE001
        db.rollback()
        print(f"[seed] ko'nikma belgisi: {e}")

    # SHABLONLARNI BAZAGA MOSLASH (2026-09-27).
    #
    # Har startda bazadagi (daraja, sarlavha) juftliklari BITTA so'rov
    # bilan o'qiladi va yetishmagani yoziladi. Sarlavhalar
    # canon_title() dan o'tadi: tizim "(dublikat)" deb yashirgan nusxa
    # ham "bor" hisoblanadi — aks holda seed va dublikat qoidasi bir-
    # birini aylantirib, har startda 69 tadan yashirin nusxa qoldirardi
    # (2026-09-27 production loglarida ko'rindi).
    #
    # Tiklash + yozish bitta tranzaksiyada, tranzaksiya qulfi ostida.
    files = _files()
    titles = {tpl["title"] for tpl in files}
    if not _xact_lock(db, MOCK_SEED_LOCK):
        print("[seed] mock: boshqa instansiya yozyapti — o'tkazildi")
        return
    try:
        retired = retire_old_speaking(db)
        db.flush()
        restored = restore_hidden(db, titles)
        db.flush()
        have = {(lv, canon_title(ti)) for lv, ti in
                db.query(models.ExamTemplate.level,
                         models.ExamTemplate.title)
                .filter(models.ExamTemplate.kind == "mock").all()}
        added = 0
        for tpl in files:
            levels = [lv for lv in (tpl.get("levels") or [None])
                      if (lv, tpl["title"]) not in have]
            if not levels:
                continue
            try:
                parts = _eo.clean_parts(tpl["parts"])
            except Exception as e:      # noqa: BLE001
                # Bitta buzuq fayl qolganlarini to'xtatmasin
                print(f"[seed] mock {tpl.get('key')}: {getattr(e, 'detail', e)}")
                continue
            for level in levels:
                db.add(models.ExamTemplate(
                    level=level,
                    kind="mock",
                    unit_no=None,
                    title=tpl["title"],
                    parts=json.dumps(parts, ensure_ascii=False),
                    paper_max=float(tpl.get("paper_max") or 0),
                    variant=tpl.get("variant") or "A",
                    subject="english",
                    is_active=1,
                    created_by="JonyOS"))
                have.add((level, tpl["title"]))
                added += 1
        db.commit()
    except Exception:
        db.rollback()
        raise
    if retired:
        print(f"[seed] eski 3 qismli CEFR Speaking nomi bo'shatildi: {retired}")
    if restored:
        print(f"[seed] noto'g'ri yashirilgan mock shablonlari tiklandi: {restored}")
    if added:
        print(f"[seed] yetishmagan mock shablonlari yozildi: {added}")
    try:
        print(f"[mock-audit] {audit(db)}")
        print(f"[mock-audit] {audit_off(db, titles)} | away_eids: {_strict_col(db)}")
    except Exception as e:      # noqa: BLE001
        print(f"[mock-audit] xato: {e}")
