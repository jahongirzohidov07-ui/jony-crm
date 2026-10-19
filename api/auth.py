import os
from datetime import datetime, timedelta
from typing import Optional

import bcrypt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import set_committed_value

from database import get_db
import models
import roles

# In production this should come from an environment variable.
_DEFAULT_SECRET = "dev-secret-change-me-before-deploy"
SECRET_KEY = os.environ.get("JONY_CRM_SECRET") or _DEFAULT_SECRET
# 2026-09-10 audit: ilgari default kalit JIMGINA ishlatilaverardi. Kalit
# kodda ochiq turgani uchun uni bilgan odam o'ziga asoschi tokeni yasab
# olardi. Endi holat aniq ko'rinadi:
#   SECRET_STRICT  — jonli muhitda (Vercel yoki Postgres) default kalit
#                    ishlatilyapti: /api/health secret_ok=false beradi.
#   SECRET_ENFORCE — JONY_SECRET_ENFORCE=1 qo'yilsa, token BERILMAYDI
#                    ham, QABUL QILINMAYDI ham (ikkala tomon yopiladi).
SECRET_IS_DEFAULT = SECRET_KEY == _DEFAULT_SECRET
SECRET_STRICT = SECRET_IS_DEFAULT and (
    bool(os.environ.get("VERCEL"))
    or not os.environ.get("DATABASE_URL", "sqlite").startswith("sqlite"))
SECRET_ENFORCE = SECRET_STRICT and os.environ.get("JONY_SECRET_ENFORCE") == "1"
SECRET_ERROR = ("Xavfsizlik kaliti (JONY_CRM_SECRET) o'rnatilmagan — "
                "Vercel Environment Variables'ga qo'shib, qayta deploy qiling")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 12  # 12 soat

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# 2026-08: passlib'dan voz kechildi (2020-yildan beri yangilanmagan,
# shuning uchun bcrypt==3.2.0'ga "michoqlanib" qolgan edi - xavfsizlik
# yamoqlari kelmasdi). Endi bcrypt kutubxonasidan TO'G'RIDAN-TO'G'RI
# foydalanamiz. Bazadagi eski (passlib orqali yozilgan) parol
# hash'lari O'ZGARMAYDI - ular oddiy $2b$... formatidagi standart
# bcrypt hash, passlib buni faqat o'rab turgan edi. Shu sababli hech
# bir foydalanuvchi parolini qayta kiritishi shart emas.
#
# bcrypt 72 BAYTdan uzun parolni qabul qilmaydi (ValueError) - passlib
# bunday holatda jimgina kesib tashlagan, xatti-harakat bir xil
# qolishi uchun shu yerda ham xuddi shunday kesamiz.
_BCRYPT_MAX_BYTES = 72


def _prep(password: str) -> bytes:
    return (password or "").encode("utf-8")[:_BCRYPT_MAX_BYTES]


def hash_password(password: str) -> str:
    return bcrypt.hashpw(_prep(password), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    if not hashed:
        return False
    try:
        return bcrypt.checkpw(_prep(plain), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        # Buzilgan/notanish formatdagi hash - kirishga ruxsat yo'q,
        # lekin 500 bilan yiqilib tushmaydi.
        return False


def create_access_token(data: dict, minutes: int | None = None) -> str:
    """minutes berilmasa odatiy 12 soat. "Eslab qolish" bilan
    kirilganda login yo'li uzoqroq muddat beradi (60 kun) -
    o'quvchi ilovani har ochganda qayta kirib o'tirmasin."""
    if SECRET_ENFORCE:
        raise HTTPException(status_code=503, detail=SECRET_ERROR)
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(
        minutes=minutes or ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


_READ_METHODS = ("GET", "HEAD", "OPTIONS")


def observer_gate(request) -> None:
    """Kuzatuvchi so'rovini tekshiradi: yozish va yopiq yo'llar — 403."""
    method = (getattr(request, "method", "") or "").upper()
    try:
        path = request.url.path
    except Exception:
        path = ""
    if method not in _READ_METHODS:
        if path in roles.OBSERVER_WRITE_ALLOW:
            return
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Kuzatuvchi faqat ko'ra oladi — o'zgartirish mumkin emas")
    if any(path == p or path.startswith(p + "/")
           for p in roles.OBSERVER_DENY_PREFIXES):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu bo'lim kuzatuvchi uchun yopiq")


def is_observer(user) -> bool:
    return bool(getattr(user, "_observer", False))


def get_current_user(
    request: Request,
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Login ma'lumotlari noto'g'ri yoki muddati tugagan",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if SECRET_ENFORCE:
        raise HTTPException(status_code=503, detail=SECRET_ERROR)
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: Optional[str] = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(models.User).filter(models.User.username == username).first()
    if user is None or not user.is_active:
        raise credentials_exception

    # KUZATUVCHI (2026-10-19): faqat ko'radi, hech narsani o'zgartirmaydi.
    # Tekshiruv shu YAGONA joyda — har bir endpointni alohida
    # tahrirlash shart emas va yangi endpoint qo'shilsa ham himoya
    # o'z-o'zidan ishlaydi. Batafsil: roles.OBSERVER izohi.
    if user.role == roles.OBSERVER:
        observer_gate(request)
        user._observer = True
        user._all_roles = [roles.OBSERVER_VIEW_AS]
        user._primary_role = roles.OBSERVER_VIEW_AS
        # Bazaga yozilmaydi (pastdagi lavozim almashtirish izohiga q.)
        set_committed_value(user, "role", roles.OBSERVER_VIEW_AS)
        return user

    # KO'P LAVOZIMLI XODIM (2026-08-10): agar xodimda qo'shimcha
    # lavozim bo'lsa va u tepadagi tanlagichdan boshqasini tanlagan
    # bo'lsa, so'rov sarlavhasida X-Active-Role keladi. Shu so'rov
    # davomida user.role AYNAN o'sha lavozimga almashtiriladi —
    # natijada tizimdagi barcha tekshiruvlar (require_role,
    # scope_to_branch, menyular) hech qanday o'zgarishsiz to'g'ri
    # ishlaydi.
    #
    # XAVFSIZLIK: sarlavhaga KO'R-KO'RONA ishonilmaydi — so'ralgan
    # lavozim xodimning HAQIQIY lavozimlari ro'yxatida bo'lsagina
    # qabul qilinadi. Aks holda asosiy lavozimda qoladi. Ya'ni
    # sarlavhani qo'lda o'zgartirib huquq oshirib bo'lmaydi.
    try:
        want = (request.headers.get("x-active-role") or "").strip()
    except Exception:
        want = ""
    # Kuzatuvchi qo'shimcha lavozim sifatida ishlamaydi: boshqa xodim
    # unga o'tib asoschi ko'zi bilan ko'rib qolmasin.
    if want and want != user.role and want != roles.OBSERVER:
        allowed = {r.role for r in db.query(models.UserRole)
                   .filter(models.UserRole.user_id == user.id).all()}
        if want in allowed:
            # 2026-08-25: almashtirishdan OLDIN to'liq ro'yxatni
            # yozib qo'yamiz — keyin u hech qayerda qisqarmaydi.
            user._all_roles = [user.role] + [
                r for r in sorted(allowed) if r != user.role]
            user._primary_role = user.role
            # 2026-09-10 audit: user.role = want DEB YOZIB BO'LMAYDI —
            # bu bazaga bog'langan ustun, obyekt "iflos" bo'lib qoladi va
            # endpoint db.commit() qilganda ASOSIY lavozim bazada butunlay
            # almashib ketardi. set_committed_value qiymatni xuddi bazadan
            # o'qilgandek qo'yadi: so'rov davomida hamma tekshiruv to'g'ri
            # ishlaydi, lekin hech qachon saqlanmaydi.
            set_committed_value(user, "role", want)
    return user


_PARTNER_HEAD = "partner_head"   # roles.PARTNER_HEAD (virtual belgi)


def is_partner_head(user) -> bool:
    """Hamkor markaz (Stech) rahbarimi — asosiy filiali hamkor bo'lgan
    filial rahbari (2026-09-17). Faqat O'Z filialida asoschi kabi
    ishlaydi; boshqa filial ma'lumoti unga baribir yopiq."""
    if getattr(user, "role", None) != "branch_manager":
        return False
    b = getattr(user, "branch", None)
    return bool(b is not None and getattr(b, "is_partner", 0))


def has_role(user, allowed) -> bool:
    """user.role ro'yxatdami. Ro'yxatda roles.PARTNER_HEAD bo'lsa,
    hamkor markaz rahbari ham o'tadi."""
    allowed = tuple(allowed)
    r = getattr(user, "role", None)
    return r in allowed or (_PARTNER_HEAD in allowed
                            and is_partner_head(user))


def founder_like(user) -> bool:
    """Asoschi yoki hamkor markaz rahbari. FAQAT allaqachon filial
    bo'yicha tekshirilgan (o'z filialidagi) yozuvlar uchun ishlatiladi."""
    return getattr(user, "role", None) == "founder" or is_partner_head(user)


def require_role(*roles: str):
    """Dependency factory: restrict an endpoint to specific roles.
    Example: Depends(require_role("owner"))"""

    def checker(user: models.User = Depends(get_current_user)) -> models.User:
        if not has_role(user, roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bu amal uchun ruxsatingiz yo'q",
            )
        return user

    return checker


def client_ip(request) -> str:
    """Mijozning HAQIQIY IP'si.

    2026-09-10 audit: ilgari x-forwarded-for XOM holda (yoki uning
    BIRINCHI qiymati) olinardi. Bu sarlavhani mijozning o'zi yozib
    yuborishi mumkin — ya'ni har safar soxta IP qo'yib, IP bo'yicha
    qo'yilgan istalgan cheklovni cheksiz aylanib o'tsa bo'lardi.

    Endi tartib shunday:
      1) Vercel o'zi qo'yadigan sarlavhalar — mijoz ularni almashtira
         olmaydi (Vercel kiruvchi x-vercel-* ni o'chirib tashlaydi);
      2) bo'lmasa XFF'ning ENG OXIRGI qiymati — uni bizga eng yaqin
         proksi qo'shadi, mijoz emas. (Birinchi qiymat — aynan mijoz
         yozib yuborgani, shuning uchun unga ishonib bo'lmaydi.)
    """
    h = request.headers
    for name in ("x-vercel-forwarded-for", "x-real-ip"):
        v = (h.get(name) or "").strip()
        if v:
            return v[:64]
    xff = (h.get("x-forwarded-for") or "").strip()
    if xff:
        return xff.split(",")[-1].strip()[:64]
    return ((request.client.host if request.client else "") or "")[:64]
