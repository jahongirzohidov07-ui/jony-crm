import os
from datetime import datetime, timedelta
from typing import Optional

import bcrypt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from database import get_db
import models

# In production this should come from an environment variable.
SECRET_KEY = os.environ.get("JONY_CRM_SECRET", "dev-secret-change-me-before-deploy")
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
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(
        minutes=minutes or ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(
    request: Request,
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Login ma'lumotlari noto'g'ri yoki muddati tugagan",
        headers={"WWW-Authenticate": "Bearer"},
    )
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
    if want and want != user.role:
        allowed = {r.role for r in db.query(models.UserRole)
                   .filter(models.UserRole.user_id == user.id).all()}
        if want in allowed:
            user._primary_role = user.role
            user.role = want
    return user


def require_role(*roles: str):
    """Dependency factory: restrict an endpoint to specific roles.
    Example: Depends(require_role("owner"))"""

    def checker(user: models.User = Depends(get_current_user)) -> models.User:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bu amal uchun ruxsatingiz yo'q",
            )
        return user

    return checker
