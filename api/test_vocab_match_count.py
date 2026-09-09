"""Juftlash o'yini: tanlangan so'zlarning HAMMASI chiqishi kerak.

2026-09-09, Jahongir: "Juftlar oyini lugatda app da nechta tanlasa
ham 5ta gina chiqyabdi shuni togrlab qoy tanlaganicha chiqsin."

Ilgari `_round_match(words[:min(5, len(words))])` deb kesilardi —
60 ta so'z tanlansa ham 5 tasi chiqardi. Endi so'zlar 5 taligi
TAXTALARGA bo'linadi (telefon ekraniga sig'sin), lekin jami so'z
soni tanlanganicha bo'ladi.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from student_app import _round_match, MATCH_BOARD  # noqa: E402


class W:
    """Eng oddiy soxta so'z — bazaga tegmaymiz."""

    def __init__(self, i):
        self.id = i
        self.word = f"word{i}"
        self.translation = f"tarjima{i}"


def _words(n):
    return [W(i) for i in range(1, n + 1)]


def _total(items):
    return sum(len(it["left"]) for it in items)


def test_bitta_taxta_toliq():
    items = _round_match(_words(5))
    assert len(items) == 1
    assert _total(items) == 5


def test_60_soz_hammasi_chiqadi():
    """ASOSIY XATO SHU EDI: 60 tadan 5 tasi chiqardi."""
    items = _round_match(_words(60))
    assert _total(items) == 60
    assert len(items) == 60 // MATCH_BOARD


def test_10_va_25_ham_toliq():
    for n in (10, 25):
        items = _round_match(_words(n))
        assert _total(items) == n, f"{n} ta so'zdan {_total(items)} chiqdi"


def test_har_taxtada_kopi_bilan_5():
    items = _round_match(_words(23))
    assert _total(items) == 23
    for it in items:
        assert 2 <= len(it["left"]) <= MATCH_BOARD + 1


def test_yolgiz_qolgan_soz_alohida_taxta_bolmaydi():
    """11 ta so'z: 5 + 5 + 1 emas, 5 + 6 bo'lishi kerak —
    bitta juftni "juftlash" ma'nosiz."""
    items = _round_match(_words(11))
    assert _total(items) == 11
    assert all(len(it["left"]) >= 2 for it in items)
    assert len(items) == 2


def test_chap_va_ong_bir_xil_sozlar():
    """Aralashtirilgan bo'lsa ham har taxtada juftlar to'g'ri."""
    for it in _round_match(_words(17)):
        assert sorted(x["word_id"] for x in it["left"]) == \
               sorted(x["word_id"] for x in it["right"])
        for x in it["left"]:
            assert x["text"].startswith("word")
        for x in it["right"]:
            assert x["text"].startswith("tarjima")


def test_endpointda_kesish_qolmagan():
    src = open(
        os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "student_app.py"),
        encoding="utf-8").read()
    assert "_round_match(words[:min(5" not in src
    assert "items = _round_match(words)" in src


def test_frontend_keyingi_taxtaga_otadi():
    """Ilova oxirgi taxtadan keyingina tugashi kerak."""
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "..", "src", "pages", "student",
                     "StudentGamePlay.tsx")
    src = open(p, encoding="utf-8").read()
    assert "onFinish={next}" in src
    assert "onFinish={() => setDone(true)}" not in src
    assert "key={idx}" in src
    assert "countWords" in src
