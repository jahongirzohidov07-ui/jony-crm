"""English Journey (diagnostik test natijasi) hisobi."""
from datetime import datetime

from api.entry import _pt_journey


def _m(j, band):
    return next(x for x in j["milestones"] if x["band"] == band)


def test_zero_start_full_path():
    j = _pt_journey("A1", 1, datetime(2026, 10, 22))
    six, seven = _m(j, "6.0"), _m(j, "7.0")
    # Intensive chizg'ichi: 192 dars, 411 mavzu, 4000 so'z
    assert six["lessons"] == 192 and six["grammar_new"] == 411
    assert six["words_new"] == 4000
    assert six["months_std"] == 16 and six["months_int"] == 8
    assert six["date_int"] == "2027-yil iyun"
    assert seven["lessons"] == 288 and seven["months_std"] == 24
    assert j["words_now"] == 0 and j["grammar_now"] == 0


def test_mid_level_marks_done_and_counts_remaining():
    j = _pt_journey("B1", 7, datetime(2026, 1, 5))  # pos = 96 + 48*6/12 = 120
    assert j["position"] == 120
    assert _m(j, "3.0")["done"] and _m(j, "4.0")["done"]
    five = _m(j, "5.0")
    assert not five["done"] and five["lessons"] == 24
    assert five["months_std"] == 2 and five["date_std"] == "2026-yil mart"
    assert 2000 < j["words_now"] < 3000
    assert _m(j, "6.0")["grammar_new"] == 411 - j["grammar_now"]


def test_unknown_level_and_bad_unit_safe():
    j = _pt_journey("ZZ", None)
    assert j["start"] == {"level": "ZZ", "unit": 1}
    assert len(j["milestones"]) == 7
