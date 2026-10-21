"""SMM BRENDLARI (2026-10-17).

Jahongir: "SMM bo'limida aynan Marhaboni profilida faqat bitta proyekt
emas u Jony School va Jahongir Zoxidovning shaxsiy brend profilini ham
yurgizadi". Asoschi tanlovi: "Brendlar ro'yxati, kontent bo'yicha".

  * smm_brands — brendlar ro'yxati: academy (Jony Academy), school
    (Jony School), personal (Jahongir Zoxidovning shaxsiy brendi) va
    asoschi keyin qo'shganlari. Brend O'CHIRILMAYDI — faqat is_active=0.
  * smm_brand_members — brendni qaysi SMM menejer yuritadi. A'zolik
    faqat profil kartasi ("Mening brendlarim") va SMM ekranidagi
    standart filtr uchun: kontent ko'rinishi O'ZGARMAYDI.
  * contents.brand_id — kontent qaysi brendniki. NULL — Jony Academy
    (eski kontentlar; seed academy brendiga bog'laydi, keyin ham
    Exceldan / Instagram'dan kelganlari NULL bo'lib qolishi mumkin —
    ular ham Jony Academy hisoblanadi).
  * Instagram ulanishi hozircha BITTA (umumiy) — brend bo'yicha token
    bu bosqichda yo'q.

Yo'llar:
  GET  /api/smm/brands               — SMM_ACCESS (ro'yxat + "mine")
  POST /api/smm/brands               — FULL_ACCESS (yangi brend)
  PUT  /api/smm/brands/{id}          — FULL_ACCESS (nomi, faolligi)
  PUT  /api/smm/brands/{id}/members  — FULL_ACCESS (a'zolar, almashtiradi)

SMM menejer ro'yxatni ko'radi va kontent brendini almashtira oladi
(content.py), lekin brend yaratish/nomini o'zgartirish/a'zolar — 403.
"""
import os
import re
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import APIRouter, Body, Depends, HTTPException  # noqa: E402
from sqlalchemy import false, func, text  # noqa: E402
from sqlalchemy.exc import IntegrityError  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

import audit  # noqa: E402
import models  # noqa: E402
import roles  # noqa: E402
from auth import has_role, require_role  # noqa: E402
from database import get_db  # noqa: E402

router = APIRouter()

ACADEMY, SCHOOL, PERSONAL = "academy", "school", "personal"
# Seed qiladigan uchta brend (kod, nom, tur). Kod o'zgarmaydi — nomni
# asoschi keyin o'zgartirishi mumkin, seed uni qayta yozmaydi.
SEED_BRANDS = (
    (ACADEMY, "Jony Academy", ACADEMY),
    (SCHOOL, "Jony School", SCHOOL),
    (PERSONAL, "Jahongir Zoxidov — shaxsiy brend", PERSONAL),
)
KINDS = ("brand", ACADEMY, SCHOOL, PERSONAL)
SEED_KEY = "smm_brands_v1"
# Marhabo ismi turlicha yozilishi mumkin (h/x, kirill) — faqat SMM
# menejerlar orasidan, ism BOSHI bo'yicha.
_MARHABO = ("marhabo", "marxabo", "мархабо")
_NAME_MIN, _NAME_MAX = 2, 80
_ID_MAX = 2 ** 31 - 1          # juda katta raqam bazaga yetib bormasin

E_ONLY_SMM = "Faqat SMM menejerlarni biriktirish mumkin"


# ------------------------------------------------------------ yordamchi ---
def academy_brand(db: Session):
    return (db.query(models.SmmBrand)
            .filter(models.SmmBrand.code == ACADEMY).first())


def brand_map(db: Session) -> tuple:
    """(id -> nom, academy id). Kontent javoblari uchun bitta so'rov."""
    names, acad = {}, None
    for bid, code, name in db.query(models.SmmBrand.id, models.SmmBrand.code,
                                    models.SmmBrand.name).all():
        names[bid] = name
        if code == ACADEMY:
            acad = bid
    return names, acad


def brand_fields(c, brands: tuple) -> dict:
    """Kontent javobidagi brend: NULL — Jony Academy. Brend topilmasa
    (seed hali ishlamagan) — ikkalasi ham None."""
    names, acad = brands
    bid = c.brand_id or acad
    name = names.get(bid) if bid else None
    return {"brand_id": bid if name else c.brand_id, "brand_name": name}


def filter_by_brand(db: Session, q, brand_id):
    """Kontent so'rovini brend bo'yicha toraytiradi. Jony Academy
    tanlansa NULL kontentlar ham kiradi (ular ham Academy'niki)."""
    if not brand_id:
        return q
    if not (0 < brand_id <= _ID_MAX):
        return q.filter(false())
    acad = academy_brand(db)
    if acad is not None and acad.id == brand_id:
        return q.filter((models.Content.brand_id == brand_id)
                        | (models.Content.brand_id.is_(None)))
    return q.filter(models.Content.brand_id == brand_id)


def content_brand_id(db: Session, brand_id, current=None):
    """Kontentga yoziladigan brend id.

    None — Jony Academy (brend hali yo'q bo'lsa NULL, u ham Academy).
    Mavjud bo'lmagan yoki nofaol brend — 400. Kontentning HOZIRGI
    brendi (current) qayta yuborilsa tekshirilmaydi: brend keyin
    nofaol qilingan bo'lsa ham eski postni tahrirlash to'xtab qolmasin.
    """
    if brand_id is None:
        a = academy_brand(db)
        return a.id if a else None
    if isinstance(brand_id, bool) or not isinstance(brand_id, int):
        raise HTTPException(400, "Brend noto'g'ri")
    if current is not None and brand_id == current:
        return brand_id
    if not (0 < brand_id <= _ID_MAX):
        raise HTTPException(400, "Bunday brend yo'q")
    b = db.get(models.SmmBrand, brand_id)
    if b is None:
        raise HTTPException(400, "Bunday brend yo'q")
    if not b.is_active:
        raise HTTPException(400, f"\"{b.name}\" brendi nofaol — "
                                 "boshqa brendni tanlang")
    return b.id


def inherit_brand_id(db: Session, brand_id):
    """Boshqa kontentdan (nusxa, variant) o'tadigan brend (2026-10-17).

    content_brand_id'dan farqi — 400 bermaydi: manba brendi hali faol
    bo'lsa o'shani, yo'q/nofaol bo'lsa Jony Academy'ni qaytaradi.
    Aks holda nusxa orqali nofaol brendga yangi post ochilib qolardi
    (POST /api/content bunga 400 beradi)."""
    if brand_id and 0 < brand_id <= _ID_MAX:
        b = db.get(models.SmmBrand, brand_id)
        if b is not None and b.is_active:
            return b.id
    a = academy_brand(db)
    return a.id if a else None


def smm_manager_ids(db: Session, ids=None) -> set:
    """SMM menejer bo'lgan xodimlar id'lari (2026-10-17).

    Asosiy lavozimi (users.role) YOKI qo'shimcha lavozimi (user_roles,
    X-Active-Role bilan almashtiriladi) smm_manager bo'lganlar. Aks
    holda qo'shimcha lavozimdagi SMM menejer brendga biriktirilmasdi,
    asoschi ro'yxatida ko'rinmasdi va profilida doim "Brend
    biriktirilmagan" turardi. ids berilsa — faqat shular orasidan."""
    q1 = (db.query(models.User.id)
          .filter(models.User.role == roles.SMM_MANAGER))
    q2 = (db.query(models.UserRole.user_id)
          .filter(models.UserRole.role == roles.SMM_MANAGER))
    if ids is not None:
        ids = list(ids) or [-1]
        q1 = q1.filter(models.User.id.in_(ids))
        q2 = q2.filter(models.UserRole.user_id.in_(ids))
    return {i for (i,) in q1.all()} | {i for (i,) in q2.all()}


def _is_marhabo(name) -> bool:
    n = (name or "").strip().lower()
    return any(n.startswith(p) for p in _MARHABO)


def _clean_name(raw) -> str:
    if not isinstance(raw, str):
        raise HTTPException(400, "Brend nomini yozing")
    name = " ".join(raw.split())
    if not (_NAME_MIN <= len(name) <= _NAME_MAX):
        raise HTTPException(400, f"Brend nomi {_NAME_MIN} dan {_NAME_MAX} "
                                 "belgigacha bo'lsin")
    return name


def _check_name_free(db: Session, name: str, skip_id=None) -> None:
    low = name.lower()
    for bid, nm in db.query(models.SmmBrand.id, models.SmmBrand.name).all():
        if bid != skip_id and (nm or "").strip().lower() == low:
            raise HTTPException(400, "Bu nomli brend allaqachon bor")


def _slug(name: str) -> str:
    s = unicodedata.normalize("NFKD", name)
    s = s.encode("ascii", "ignore").decode("ascii").lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")[:40].strip("-")
    return s or "brend"


def _unique_code(db: Session, name: str) -> str:
    base = _slug(name)
    have = {c for (c,) in db.query(models.SmmBrand.code).all()}
    code, n = base, 2
    while code in have:
        code = f"{base}-{n}"
        n += 1
    return code


def _get_or_404(db: Session, bid: int):
    b = db.get(models.SmmBrand, bid) if 0 < bid <= _ID_MAX else None
    if b is None:
        raise HTTPException(404, "Brend topilmadi")
    return b


def _payload(payload) -> dict:
    if not isinstance(payload, dict):
        raise HTTPException(400, "So'rov noto'g'ri")
    return payload


# ------------------------------------------------------------------ seed ---
def seed_smm_brands(db: Session) -> dict:
    """Bir martalik (main.py: smm_brands_v1), lekin qayta ishlasa ham
    zarari yo'q — hech narsa takrorlanmaydi va HECH NARSA O'CHIRILMAYDI.

      1) uchta brend (kodi yo'q bo'lsa qo'shiladi; bor bo'lsa nomiga
         tegilmaydi);
      2) brendsiz kontentlar Jony Academy'ga bog'lanadi (xom UPDATE —
         updated_at o'zgarmaydi);
      3) Marhabo (SMM menejer, ismi "Marhabo" bilan boshlanadi) uchala
         brendga a'zo bo'ladi; topilmasa log va davom.

    Ikki nusxa bir vaqtda ishlasa — UNIQUE cheklovi ikkinchisini
    to'xtatadi, qator qayta o'qiladi. Qaytaradi: faqat sonlar."""
    out = {"brands_created": 0, "contents_backfilled": 0,
           "members_added": 0, "marhabo": 0}
    have = {b.code: b for b in db.query(models.SmmBrand).all()}
    for code, name, kind in SEED_BRANDS:
        if code in have:
            continue
        b = models.SmmBrand(code=code, name=name, kind=kind, is_active=1)
        db.add(b)
        try:
            db.commit()
            out["brands_created"] += 1
        except IntegrityError:          # boshqa nusxa qo'shib ulgurdi
            db.rollback()
            b = (db.query(models.SmmBrand)
                 .filter(models.SmmBrand.code == code).first())
        have[code] = b

    acad = have[ACADEMY]
    res = db.execute(text("UPDATE contents SET brand_id = :b "
                          "WHERE brand_id IS NULL"), {"b": acad.id})
    db.commit()
    out["contents_backfilled"] = max(int(res.rowcount or 0), 0)

    # SMM menejer — asosiy yoki qo'shimcha lavozim (2026-10-17)
    smm_ids = smm_manager_ids(db)
    mids = [uid for uid, nm in db.query(models.User.id, models.User.full_name)
            .filter(models.User.id.in_(smm_ids or [-1])).all()
            if _is_marhabo(nm)]
    out["marhabo"] = len(mids)
    if not mids:
        print("[smm-brands] Marhabo topilmadi")
        return out
    bids = [have[code].id for code, _n, _k in SEED_BRANDS]
    for uid in mids:
        for bid in bids:
            exists = (db.query(models.SmmBrandMember.id)
                      .filter(models.SmmBrandMember.brand_id == bid,
                              models.SmmBrandMember.user_id == uid).first())
            if exists:
                continue
            db.add(models.SmmBrandMember(brand_id=bid, user_id=uid))
            try:
                db.commit()
                out["members_added"] += 1
            except IntegrityError:
                db.rollback()
    return out


def seed_startup(db: Session):
    """main.py startda chaqiradi: belgi bo'lsa hech narsa qilmaydi."""
    from common import _seed_done, _seed_mark
    if _seed_done(db, SEED_KEY):
        return None
    r = seed_smm_brands(db)
    _seed_mark(db, SEED_KEY)
    return r


# ------------------------------------------------------------------ yo'llar ---
def _listing(db: Session, user, only_id=None) -> dict:
    brands = db.query(models.SmmBrand).order_by(models.SmmBrand.id).all()
    mem = db.query(models.SmmBrandMember.brand_id,
                   models.SmmBrandMember.user_id).all()
    uids = {u for _b, u in mem}
    names = {i: n for i, n in db.query(models.User.id, models.User.full_name)
             .filter(models.User.id.in_(uids or [-1])).all()}
    counts = dict(db.query(models.Content.brand_id, func.count(models.Content.id))
                  .group_by(models.Content.brand_id).all())
    null_count = counts.pop(None, 0)
    by_brand: dict = {}
    for bid, uid in mem:
        by_brand.setdefault(bid, []).append(uid)
    rows, mine = [], []
    for b in brands:
        members = sorted(({"id": u, "name": names.get(u) or f"#{u}"}
                          for u in by_brand.get(b.id, [])),
                         key=lambda x: (x["name"].lower(), x["id"]))
        is_mine = user.id in by_brand.get(b.id, [])
        if is_mine:
            mine.append(b.id)
        rows.append({
            "id": b.id, "code": b.code, "name": b.name,
            "kind": b.kind or "brand",
            "is_active": bool(b.is_active),
            "note": b.note,
            "members": members,
            "mine": is_mine,
            "content_count": int(counts.get(b.id, 0)
                                 + (null_count if b.code == ACADEMY else 0)),
        })
    if only_id is not None:
        return next(r for r in rows if r["id"] == only_id)
    managers = []
    if has_role(user, roles.FULL_ACCESS):
        # A'zo tanlash uchun: faol SMM menejerlar + hozirgi a'zolar
        # (SMM — asosiy yoki qo'shimcha lavozim, 2026-10-17)
        smm_ids = smm_manager_ids(db)
        managers = [{"id": i, "name": n} for i, n in
                    db.query(models.User.id, models.User.full_name)
                    .filter(models.User.id.in_(smm_ids or [-1]))
                    .filter((models.User.is_active == 1)
                            | models.User.id.in_(uids or [-1]))
                    .order_by(models.User.full_name).all()]
    return {"brands": rows, "mine": mine, "managers": managers}


@router.get("/api/smm/brands")
def list_brands(db: Session = Depends(get_db),
                user=Depends(require_role(*roles.SMM_ACCESS))):
    """Brendlar ro'yxati. "mine" — joriy foydalanuvchi a'zo bo'lgan
    brendlar. Nofaol brendlar ham qaytadi (is_active: false)."""
    if db.query(models.SmmBrand.id).first() is None:
        # Start seedi hali ishlamagan (yoki xato bergan) — ro'yxat bo'sh
        # qolmasin. Idempotent, hech narsa o'chirmaydi.
        try:
            seed_smm_brands(db)
        except Exception:  # noqa: BLE001
            db.rollback()
    return _listing(db, user)


@router.post("/api/smm/brands")
def create_brand(payload: dict = Body(...), db: Session = Depends(get_db),
                 user=Depends(require_role(*roles.FULL_ACCESS))):
    p = _payload(payload)
    name = _clean_name(p.get("name"))
    kind = p.get("kind") or "brand"
    if kind not in KINDS:
        raise HTTPException(400, "Brend turi noto'g'ri")
    _check_name_free(db, name)
    b = models.SmmBrand(code=_unique_code(db, name), name=name, kind=kind,
                        is_active=1)
    db.add(b)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(400, "Bu brend allaqachon bor — qayta urinib "
                                 "ko'ring")
    audit.log(db, user, entity="smm_brand", action="create",
              entity_id=b.id, entity_label=name, field="name",
              new_value=name, note=f"turi: {kind}; kod: {b.code}")
    db.commit()
    return _listing(db, user, only_id=b.id)


@router.put("/api/smm/brands/{bid}")
def update_brand(bid: int, payload: dict = Body(...),
                 db: Session = Depends(get_db),
                 user=Depends(require_role(*roles.FULL_ACCESS))):
    b = _get_or_404(db, bid)
    p = _payload(payload)
    changes = {}
    if "name" in p:
        name = _clean_name(p.get("name"))
        if name != b.name:
            _check_name_free(db, name, skip_id=b.id)
            changes["name"] = name
    if "is_active" in p:
        v = p.get("is_active")
        if not isinstance(v, bool) and v not in (0, 1):
            raise HTTPException(400, "is_active — ha yoki yo'q bo'lsin")
        if b.code == ACADEMY and not v:
            # NULL kontent va yangi kontent standarti — Jony Academy
            raise HTTPException(400, "Jony Academy asosiy brend — uni "
                                     "nofaol qilib bo'lmaydi")
        changes["is_active"] = 1 if v else 0
    old_label = b.name
    for k, v in changes.items():
        old = getattr(b, k)
        if audit._fmt(old) == audit._fmt(v):
            continue
        audit.log(db, user, entity="smm_brand", action="update",
                  entity_id=b.id, entity_label=old_label, field=k,
                  old_value=bool(old) if k == "is_active" else old,
                  new_value=bool(v) if k == "is_active" else v)
        setattr(b, k, v)
    db.commit()
    return _listing(db, user, only_id=b.id)


@router.put("/api/smm/brands/{bid}/members")
def set_brand_members(bid: int, payload: dict = Body(...),
                      db: Session = Depends(get_db),
                      user=Depends(require_role(*roles.FULL_ACCESS))):
    """A'zolar ro'yxatini ALMASHTIRADI (yuborilmaganlari chiqadi).
    Faqat SMM menejerlar (asosiy yoki qo'shimcha lavozim, 2026-10-17);
    nofaol xodim yangidan qo'shilmaydi."""
    b = _get_or_404(db, bid)
    raw = _payload(payload).get("user_ids")
    if not isinstance(raw, list) or any(
            isinstance(x, bool) or not isinstance(x, int) for x in raw):
        raise HTTPException(400, "user_ids — xodim raqamlari ro'yxati "
                                 "bo'lsin")
    ids = sorted(set(raw))
    if any(not (0 < x <= _ID_MAX) for x in ids):
        raise HTTPException(400, E_ONLY_SMM)
    found = {}
    if ids:
        found = {i: (n, a) for i, n, a in db.query(
            models.User.id, models.User.full_name, models.User.is_active)
            .filter(models.User.id.in_(ids)).all()}
    # SMM menejer — asosiy yoki qo'shimcha lavozim (2026-10-17)
    if len(found) != len(ids) or (
            ids and smm_manager_ids(db, ids) != set(ids)):
        raise HTTPException(400, E_ONLY_SMM)

    cur = (db.query(models.SmmBrandMember)
           .filter(models.SmmBrandMember.brand_id == b.id).all())
    cur_ids = {m.user_id for m in cur}
    # Ishdan ketgan (nofaol) xodim YANGIDAN biriktirilmaydi (2026-10-17).
    # Hozirgi a'zo nofaol bo'lsa qolishi mumkin — tahrir to'xtamasin.
    if any(a == 0 and i not in cur_ids for i, (_n, a) in found.items()):
        raise HTTPException(400, "Nofaol (ishdan ketgan) xodimni "
                                 "biriktirib bo'lmaydi")
    if cur_ids != set(ids):
        old_names = {i: n for i, n in db.query(models.User.id,
                                               models.User.full_name)
                     .filter(models.User.id.in_(cur_ids or [-1])).all()}

        def _names(xs, src):
            return ", ".join(sorted((src.get(x) or f"#{x}") for x in xs)) \
                or None
        audit.log(db, user, entity="smm_brand", action="update",
                  entity_id=b.id, entity_label=b.name, field="members",
                  old_value=_names(cur_ids, old_names),
                  new_value=_names(ids, {i: v[0] for i, v in found.items()}))
        for m in cur:
            if m.user_id not in found:
                db.delete(m)
        for uid in ids:
            if uid not in cur_ids:
                db.add(models.SmmBrandMember(brand_id=b.id, user_id=uid))
        try:
            db.commit()
        except IntegrityError:          # parallel so'rov qo'shib ulgurdi
            db.rollback()
            raise HTTPException(409, "A'zolar hozirgina o'zgardi — "
                                     "sahifani yangilang")
    return _listing(db, user, only_id=b.id)
