"""Atomic, repeat-safe import of optional paper books."""
import unicodedata
from fastapi import HTTPException


def title_key(value):
    value = unicodedata.normalize("NFKC", value).casefold()
    value = value.translate(str.maketrans({"’": "'", "‘": "'", "ʻ": "'", "ʼ": "'", "`": "'"}))
    return " ".join(value.split())


def import_books(db, model, items, created_by):
    if not isinstance(items, list) or not 1 <= len(items) <= 500:
        raise HTTPException(400, "1 tadan 500 tagacha kitob yuboring")
    clean = []
    for i, item in enumerate(items, 1):
        if not isinstance(item, dict):
            raise HTTPException(400, f"{i}-qator noto'g'ri")
        title, description = item.get("title"), item.get("description", "")
        if not isinstance(title, str) or not title.strip() or len(title) > 300:
            raise HTTPException(400, f"{i}-qatorda kitob nomini tekshiring")
        if not isinstance(description, str) or len(description) > 6000:
            raise HTTPException(400, f"{i}-qatorda izohni tekshiring")
        clean.append((" ".join(title.split()), description.strip() or None))
    # Serialize simultaneous imports in production; SQLite tests use a single writer.
    if db.bind.dialect.name == "postgresql":
        from sqlalchemy import text
        db.execute(text("SELECT pg_advisory_xact_lock(190930, 1)"))
    known = {title_key(x.title) for x in db.query(model).filter(model.kind == "book").all()}
    added, skipped = [], []
    for title, description in clean:
        key = title_key(title)
        if key in known:
            skipped.append(title)
            continue
        row = model(title=title, kind="book", description=description,
                    required=0, active=1, minutes=0, order_no=0,
                    created_by=created_by)
        db.add(row)
        known.add(key)
        added.append(title)
    db.flush()
    return {"added": len(added), "skipped": len(skipped),
            "added_titles": added, "skipped_titles": skipped}
