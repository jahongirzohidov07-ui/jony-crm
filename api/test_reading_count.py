# -*- coding: utf-8 -*-
"""Reading daraja mashqi: NECHTA so'ralsa, shuncha chiqadimi.

Jahongir: "10, 20, 30ta qilib tanlashni ezsa qaysini tanlasa ham
faqat 4tadan chiqaryabdi, 10ta tanlasa 10ta bo'lsinda."

Xato IKKI QATLAMLI edi:
  1) practice_round reading uchun FAQAT bitta matn tanlab, uning
     to'rtta savolini qaytarardi — count parametri umuman o'qilmasdi;
  2) kontentning o'zi yetmasdi: B2, C1 va C2 darajalarda atigi 2
     tadan matn (8 tadan savol) bor edi.
Test ikkalasini ham qo'riqlaydi.
"""
import collections
import reading_seed as R

ALL = R.SEED + R.SEED2 + R.SEED3


def _per_level():
    c = collections.Counter()
    for _t, level, _b, qs in ALL:
        c[level] += len(qs)
    return c


def test_har_darajada_kamida_30_savol():
    """30 tanlansa ham yetsin."""
    c = _per_level()
    for lv in ("A1", "A2", "B1", "B2", "C1", "C2"):
        assert c[lv] >= 30, (lv, c[lv])


def test_sarlavhalar_takrorlanmaydi():
    """Seed sarlavha bo'yicha o'tkazib yuboradi — dublikat bo'lsa
    matn umuman tushmay qolardi."""
    titles = [t for t, *_ in ALL]
    dup = [t for t, n in collections.Counter(titles).items() if n > 1]
    assert not dup, dup


def test_har_matnda_4_savol():
    bad = [(t, len(qs)) for t, _l, _b, qs in ALL if len(qs) != 4]
    assert not bad, bad


def test_javob_variantlar_ichida():
    bad = []
    for t, _l, _b, qs in ALL:
        for prompt, options, answer, explain in qs:
            if answer not in options:
                bad.append((t, answer))
            if len(set(options)) != len(options):
                bad.append((t, "dubl variant"))
    assert not bad, bad


def test_izoh_matndan_iqtibos():
    """Izohdagi tirnoq ichidagi bo'lak matnda bo'lsin (SEED3)."""
    import re
    bad = []
    for t, _l, body, qs in R.SEED3:
        flat = re.sub(r"\s+", " ", body)
        for prompt, options, answer, explain in qs:
            m = re.search(r'"(.+?)"', explain or "")
            if not m:
                continue
            for chunk in m.group(1).split("..."):
                chunk = re.sub(r"\s+", " ", chunk).strip()
                if chunk and chunk not in flat:
                    bad.append((t, chunk[:50]))
    assert not bad, bad


def test_count_backend_ishlatilyapti():
    """practice_round endi count'ni o'qib, bir nechta matndan
    to'ldirishi kerak."""
    src = open("student_app.py", encoding="utf-8").read()
    # practice_round ICHIDAGI blok kerak (fayl boshida darajalar
    # endpointida ham shu satr bor).
    i = src.index("def practice_round(")
    j = src.index('if skill == "reading":', i)
    blok = src[j:j + 3000]
    assert "n = int(count or 0) or PRACTICE_ROUND" in blok
    assert "items = items[:n]" in blok
    # eski xato: faqat bitta matn olinardi
    assert "tx = texts[0] if texts else None" not in blok
    # har savol o'z matni bilan kelsin
    assert '"text": body,' in blok


def test_ekran_har_savolning_matnini_korsatadi():
    fe = open("../src/pages/student/StudentPractice.tsx",
              encoding="utf-8").read()
    assert "(q?.text || d.text)" in fe


def test_yangi_marker():
    """reading_v2 qo'yilgan bazalarda SEED3 tushishi uchun yangi
    marker shart."""
    src = open("reading_seed.py", encoding="utf-8").read()
    assert '"reading_v3"' in src
    assert '("reading_v2", SEED + SEED2)' in src
