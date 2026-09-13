"""
ZAXIRA (BACKUP) — JonyOS o'zi oladi.

2026-08-15, Jahongir: "hammasini ozing qil hamma ruxsatni beraman".

NEGA SHU YO'L. Kunlik zaxira GitHub Actions'da yozilgan edi, lekin u
ishlashi uchun bazaning ULANISH SATRINI (parol bilan) qo'lda GitHub
sekretiga ko'chirish kerak edi. Parolni birov ko'chirib yurishi —
o'zi xavf. Bu modul esa zaxirani ILOVANING O'ZIDA oladi: serverda
DATABASE_URL allaqachon bor, hech kim hech qayerga parol ko'chirmaydi.

NIMA CHIQADI. Bitta .zip fayl:
    jonyos_2026-08-15.zip
      README.txt            - o'zbekcha tiklash yo'riqnomasi
      schema.sql            - barcha jadval tuzilishi (CREATE TABLE)
      restore.py            - tiklash skripti (bitta buyruq)
      manifest.json         - jadval nomlari va qator sonlari
      data/<jadval>.jsonl   - har jadval alohida, satr-satr JSON

NEGA .sql EMAS, JSONL. Chunki bu formatni MEN SINAB KO'RA OLAMAN:
sinov bazasidan zaxira olib, bo'sh bazaga qaytarib, qator sonlarini
solishtirdim (api/test_backup.py). Sinalmagan zaxira — zaxira emas.
restore.py FK (bog'liqlik) tartibini o'zi hal qiladi: qaysi qator
hozir kirmasa, keyingi aylanishda qayta uriniladi.

KIM OLADI. Faqat ASOSCHI. Har olish auditga yoziladi — zaxirada
butun bazadagi ma'lumot bor, kim yuklab olgani bilinib tursin.
"""
import gzip
import io
import json
import os
import sys
import zipfile
from datetime import date, datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.orm import Session

import audit
import models
import roles
from auth import require_role
from database import Base, engine, get_db

router = APIRouter()

# Zaxiraga TUSHMAYDIGAN jadvallar: ular vaqtinchalik jurnal, hajmi
# katta, qiymati esa yo'q. Tiklashda ular bo'sh boshlanadi.
SKIP_TABLES = {"login_attempts", "error_logs"}

# Bir jadvaldan ko'pi bilan shuncha qator (himoya chegarasi —
# kutilmaganda ulkan jadval butun jarayonni to'xtatib qo'ymasin).
MAX_ROWS_PER_TABLE = 400_000

# TELEGRAM CHEGARASI (2026-09-13). Bot 50 MB dan katta hujjatni qabul
# qilmaydi. Jonli baza bundan ancha katta (GitHub'dagi siqilgan pg_dump
# 264 MB): rasm va fayllar bazada base64 bo'lib turadi, ular deyarli
# siqilmaydi. Ilgari kunlik cron har kuni butun bazani Vercel xotirasiga
# o'qib zip yasar, keyin Telegram rad etar va send_document jimgina
# False qaytarardi — resurs bekorga ketardi, zaxira esa bo'lmasdi.
# Endi baza katta bo'lsa zip umuman yasalmaydi; to'liq zaxirani
# GitHub Actions (.github/workflows/backup.yml) oladi.
TG_MAX_BYTES = 49 * 1024 * 1024
TG_DB_LIMIT_BYTES = 200 * 1024 * 1024


def _db_size_bytes(db: Session) -> int:
    """Postgres'da bazaning diskdagi hajmi. SQLite'da 0 (cheklov yo'q)."""
    try:
        if db.get_bind().dialect.name != "postgresql":
            return 0
        from sqlalchemy import text as _t
        return int(db.execute(
            _t("SELECT pg_database_size(current_database())")).scalar() or 0)
    except Exception:
        try:
            db.rollback()
        except Exception:
            pass
        return 0


def _json_default(o):
    if isinstance(o, (datetime, date)):
        return o.isoformat()
    if isinstance(o, (bytes, bytearray)):
        return o.decode("utf-8", "replace")
    return str(o)


def _table_names() -> list:
    """Bazada HAQIQATDA mavjud jadvallar, bog'liqlik tartibida.
    Modelda bor-u bazada yo'q jadval o'tkazib yuboriladi."""
    try:
        live = set(sa_inspect(engine).get_table_names())
    except Exception:
        live = set()
    out = []
    try:
        for t in Base.metadata.sorted_tables:
            if t.name in live and t.name not in SKIP_TABLES:
                out.append(t.name)
    except Exception:
        # sorted_tables sikl tufayli yiqilsa — oddiy tartib
        for t in Base.metadata.tables.values():
            if t.name in live and t.name not in SKIP_TABLES:
                out.append(t.name)
    # Modelda yo'q, lekin bazada bor jadvallar ham qolib ketmasin
    for name in sorted(live - set(out) - SKIP_TABLES):
        out.append(name)
    return out


def _schema_sql() -> str:
    """CREATE TABLE ko'rsatmalari — bo'sh bazani noldan tiklash uchun."""
    from sqlalchemy.schema import CreateTable
    parts = [
        "-- JonyOS sxemasi. Bo'sh bazaga birinchi bo'lib shu qo'llanadi.",
        "-- (Ilovaning o'zi ham ishga tushganda jadvallarni yaratadi —",
        "--  ya'ni bu fayl majburiy emas, ehtiyot uchun.)",
        "",
    ]
    for t in Base.metadata.sorted_tables:
        try:
            ddl = str(CreateTable(t).compile(bind=engine)).strip()
            parts.append(ddl.rstrip(";") + ";")
            parts.append("")
        except Exception:
            continue
    return "\n".join(parts)


RESTORE_PY = r'''#!/usr/bin/env python3
"""JonyOS zaxirasini tiklash.

ISHLATISH:
    pip install sqlalchemy psycopg2-binary
    python restore.py "postgresql://foydalanuvchi:parol@host/baza"

Skript shu papkadagi data/*.jsonl fayllarini bazaga qaytaradi.
Bog'liqlik (foreign key) tartibi o'zi hal qilinadi: kirmagan qatorlar
keyingi aylanishda qayta uriniladi. Mavjud qator ustidan yozilmaydi.
"""
import json
import os
import sys

from sqlalchemy import create_engine, inspect, text


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    url = sys.argv[1]
    here = os.path.dirname(os.path.abspath(__file__))
    man = json.load(open(os.path.join(here, "manifest.json"),
                         encoding="utf-8"))
    eng = create_engine(url)
    live = set(inspect(eng).get_table_names())

    pending = []
    for tbl in man["tables"]:
        name = tbl["name"]
        path = os.path.join(here, "data", name + ".jsonl")
        if not os.path.exists(path):
            continue
        if name not in live:
            print(f"  ! {name}: bazada bunday jadval yo'q, o'tkazildi")
            continue
        rows = [json.loads(x) for x in open(path, encoding="utf-8") if x.strip()]
        if rows:
            pending.append((name, rows))

    total = done = 0
    for _, rows in pending:
        total += len(rows)

    # Bir necha aylanish: FK tufayli kirmagan qator keyin urinadi.
    for attempt in range(1, 7):
        left = []
        for name, rows in pending:
            bad = []
            cols = list(rows[0].keys())
            stmt = text(
                f'INSERT INTO "{name}" (' +
                ", ".join(f'"{c}"' for c in cols) + ") VALUES (" +
                ", ".join(f":{c}" for c in cols) + ") ON CONFLICT DO NOTHING")
            for r in rows:
                try:
                    with eng.begin() as cx:
                        cx.execute(stmt, r)
                    done += 1
                except Exception:
                    bad.append(r)
            if bad:
                left.append((name, bad))
            print(f"  {name}: {len(rows) - len(bad)}/{len(rows)}")
        if not left:
            break
        if len(left) == len(pending) and \
                sum(len(r) for _, r in left) == sum(len(r) for _, r in pending):
            print("Qolgan qatorlar kiritilmadi:",
                  ", ".join(n for n, _ in left))
            break
        pending = left
        print(f"--- {attempt}-aylanish tugadi, qolgani qayta uriniladi ---")

    # Postgres'da id ketma-ketligini oxirgi qiymatga surish
    try:
        with eng.begin() as cx:
            for tbl in man["tables"]:
                n = tbl["name"]
                try:
                    cx.execute(text(
                        f"SELECT setval(pg_get_serial_sequence('\"{n}\"','id'),"
                        f" COALESCE((SELECT MAX(id) FROM \"{n}\"), 1), true)"))
                except Exception:
                    pass
    except Exception:
        pass

    print(f"\nTAYYOR: {done}/{total} qator tiklandi.")


if __name__ == "__main__":
    main()
'''


def _readme(stamp: str, tables: list, rows: int) -> str:
    lines = [
        "JONYOS ZAXIRA NUSXASI",
        "=" * 40,
        f"Olingan sana : {stamp}",
        f"Jadvallar    : {len(tables)} ta",
        f"Qatorlar     : {rows} ta",
        "",
        "ICHIDA NIMA BOR",
        "  data/*.jsonl   - har jadval alohida faylda, satr-satr JSON",
        "  schema.sql     - jadval tuzilishi (CREATE TABLE)",
        "  restore.py     - tiklash skripti",
        "  manifest.json  - jadval nomlari va qator sonlari",
        "",
        "QANDAY TIKLANADI",
        "  1) Yangi (bo'sh) Postgres baza oching.",
        "  2) Sxemani yarating - ikki yo'ldan biri:",
        "       a) JonyOS'ni shu bazaga ulab bir marta ishga tushiring",
        "          (ilova jadvallarni o'zi yaratadi), YOKI",
        "       b) psql \"$URL\" -f schema.sql",
        "  3) Ma'lumotni qaytaring:",
        "       pip install sqlalchemy psycopg2-binary",
        "       python restore.py \"postgresql://...\"",
        "  4) Oxirida \"TAYYOR: N/N qator tiklandi\" chiqishi kerak.",
        "",
        "DIQQAT",
        "  Bu faylda MARKAZNING BARCHA MA'LUMOTI bor: o'quvchilar,",
        "  telefon raqamlar, to'lovlar, xodimlar. Uni ochiq joyda",
        "  saqlamang va begonaga bermang.",
        "",
        "  Kirish parollari shifrlangan holda (hash) saqlangan -",
        "  ulardan hech kim asl parolni o'qiy olmaydi.",
    ]
    return "\n".join(lines)


def build_backup(db: Session, limit_tables: list | None = None) -> tuple:
    """Zaxira zip'ini xotirada yig'adi.
    Qaytaradi: (fayl nomi, baytlar, ma'lumot dict)."""
    stamp = roles.local_today().isoformat()
    names = limit_tables or _table_names()

    buf = io.BytesIO()
    manifest = {"created_at": datetime.utcnow().isoformat(),
                "date": stamp, "tables": []}
    total = 0

    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED,
                         compresslevel=6) as z:
        for name in names:
            try:
                rows = db.execute(
                    __import__("sqlalchemy").text(
                        f'SELECT * FROM "{name}" LIMIT {MAX_ROWS_PER_TABLE}')
                ).mappings().all()
            except Exception:
                continue
            out = io.StringIO()
            for r in rows:
                out.write(json.dumps(dict(r), ensure_ascii=False,
                                     default=_json_default))
                out.write("\n")
            z.writestr(f"data/{name}.jsonl", out.getvalue())
            manifest["tables"].append({"name": name, "rows": len(rows)})
            total += len(rows)

        manifest["total_rows"] = total
        z.writestr("manifest.json",
                   json.dumps(manifest, ensure_ascii=False, indent=1))
        z.writestr("restore.py", RESTORE_PY)
        try:
            z.writestr("schema.sql", _schema_sql())
        except Exception:
            pass
        z.writestr("README.txt", _readme(stamp, manifest["tables"], total))

    return f"jonyos_{stamp}.zip", buf.getvalue(), manifest


@router.get("/api/backup/download")
def backup_download(db: Session = Depends(get_db),
                    user=Depends(require_role(roles.FOUNDER))):
    """Butun bazani bitta zip qilib yuklab beradi. Faqat asoschi."""
    fname, blob, manifest = build_backup(db)
    try:
        audit.log(db, user, entity="system", action="backup",
                  note=(f"Zaxira yuklab olindi: {len(manifest['tables'])} "
                        f"jadval, {manifest['total_rows']} qator, "
                        f"{len(blob) // 1024} KB"), commit=True)
    except Exception:
        db.rollback()
    return Response(
        content=blob, media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{fname}"',
                 "Content-Length": str(len(blob))})


@router.get("/api/backup/status")
def backup_status(db: Session = Depends(get_db),
                  user=Depends(require_role(roles.FOUNDER))):
    """Zaxira holati: oxirgi marta qachon olingan, baza qanchalik katta."""
    last = None
    try:
        row = (db.query(models.AuditLog)
               .filter(models.AuditLog.entity == "system",
                       models.AuditLog.action == "backup")
               .order_by(models.AuditLog.id.desc()).first())
        if row:
            last = {"at": row.created_at.isoformat() if row.created_at
                    else None,
                    "by": row.user_name, "note": row.note}
    except Exception:
        last = None
    tables = _table_names()
    return {
        "tables": len(tables),
        "last": last,
        "telegram_ready": bool(os.environ.get("TELEGRAM_BOT_TOKEN")),
        "hint": ("Zaxirada markazning barcha ma'lumoti bor. Uni "
                 "ishonchli joyda saqlang."),
    }


def daily_backup_to_telegram(db: Session) -> dict:
    """Kunlik cron chaqiradi: zaxirani asoschining Telegramiga yuboradi.

    Chat bog'lanmagan bo'lsa yoki bot sozlanmagan bo'lsa — jimgina
    o'tadi (zaxira baribir /api/backup/download orqali olinadi)."""
    import notify
    from common import _seed_done, _seed_mark

    today = roles.local_today()
    key = f"bkp_{today.isoformat()}"
    if _seed_done(db, key):
        return {"skipped": "bugun yuborilgan"}
    size = _db_size_bytes(db)
    if size > TG_DB_LIMIT_BYTES:
        return {"skipped": (f"baza {size // 1048576} MB — Telegram 50 MB dan "
                            "kattasini qabul qilmaydi; to'liq zaxira GitHub "
                            "Actions'da olinadi"),
                "db_mb": size // 1048576}
    if not notify.enabled():
        return {"skipped": "TELEGRAM_BOT_TOKEN yo'q"}

    chats = [u.telegram_chat_id for u in db.query(models.User).filter(
        models.User.role == roles.FOUNDER,
        models.User.is_active == 1,
        models.User.telegram_chat_id.isnot(None)).all()]
    chats = [c for c in chats if c]
    if not chats:
        return {"skipped": "asoschining Telegram chati bog'lanmagan"}

    fname, blob, manifest = build_backup(db)
    if len(blob) > TG_MAX_BYTES:
        return {"skipped": (f"zaxira {len(blob) // 1048576} MB — Telegram "
                            "50 MB dan kattasini qabul qilmaydi"),
                "kb": len(blob) // 1024}
    caption = (f"JonyOS zaxira — {manifest['date']}\n"
               f"{len(manifest['tables'])} jadval, "
               f"{manifest['total_rows']} qator, "
               f"{len(blob) // 1024} KB\n"
               "Ichida tiklash yo'riqnomasi (README.txt) bor.")
    sent = 0
    for chat in chats:
        if notify.send_document(chat, fname, blob, caption):
            sent += 1
    if sent:
        _seed_mark(db, key)
        try:
            audit.log(db, None, entity="system", action="backup",
                      note=(f"Avtomat zaxira Telegramga yuborildi "
                            f"({manifest['total_rows']} qator, "
                            f"{len(blob) // 1024} KB)"), commit=True)
        except Exception:
            db.rollback()
    return {"sent": sent, "rows": manifest["total_rows"],
            "kb": len(blob) // 1024}
