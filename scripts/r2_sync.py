"""api/plans_data/media dagi fayllarni Cloudflare R2 ga yuklaydi (2026-09-27).

Ishlatish (repo ildizidan):  python scripts/r2_sync.py [--check]
Kalitlar muhitdan yoki %USERPROFILE%\\.jony-r2.env faylidan (KEY=qiymat
qatorlari, repodan tashqarida — hech qachon commit qilinmaydi) olinadi:
R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_BUCKET.
R2 da o'sha hajmdagi fayl bo'lsa qayta yuklanmaydi. --check faqat
yetishmayotganlarni sanaydi. Kalit qiymatlari hech qayerga chiqarilmaydi.
"""
import os
import sys

import httpx

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "api"))
import r2  # noqa: E402

MEDIA = os.path.join(ROOT, "api", "plans_data", "media")
TYPES = {"jpg": "image/jpeg", "png": "image/png", "pdf": "application/pdf", "mp3": "audio/mpeg"}


def load_env():
    f = os.path.join(os.path.expanduser("~"), ".jony-r2.env")
    if os.path.exists(f):
        for line in open(f, encoding="utf-8"):
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"'))


def main():
    load_env()
    if not r2.enabled():
        sys.exit("R2 kalitlari topilmadi (muhit yoki ~/.jony-r2.env)")
    check = "--check" in sys.argv
    names = sorted(n for n in os.listdir(MEDIA) if n.rsplit(".", 1)[-1] in TYPES)
    up = skip = bad = 0
    with httpx.Client(timeout=120) as c:
        for n in names:
            size = os.path.getsize(os.path.join(MEDIA, n))
            h = c.head(r2.presign("HEAD", n, 600))
            if h.status_code == 200 and int(h.headers.get("content-length", -1)) == size:
                skip += 1
                continue
            if check:
                print("yo'q:", n); bad += 1
                continue
            with open(os.path.join(MEDIA, n), "rb") as fh:
                r = c.put(r2.presign("PUT", n, 600), content=fh.read(),
                          headers={"Content-Type": TYPES[n.rsplit(".", 1)[1]]})
            if r.status_code == 200:
                up += 1
            else:
                bad += 1
                print("XATO", n, r.status_code, r.text[:200])
    print(f"jami {len(names)}: yuklandi {up}, bor edi {skip}, xato/yo'q {bad}")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
