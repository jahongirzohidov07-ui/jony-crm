"""Eski yillardagi to'lov yig'ilish statistikasi (reja/fakt) importi.

Jahongir: "endi eski yillarda tolov foizilari ularniyam tashlaymi
qancha tushishi kerak edi qancha tushdi" va "Bekbod deganda Bekobod 1
filial shuni yozganmiz" - Google Sheets'dagi "To'lovlar foizi"
varag'idan olingan.

2023-2024 markaz bo'yicha umumiy, 2025-2026 esa Bekobod 1 va Zafar
filiallari kesimida. Foiz saqlanmaydi - reja va faktdan hisoblanadi
(jadvaldagi foizlar bilan solishtirib tekshirilgan). (yil, oy, filial)
bo'yicha idempotent."""

import models
from sqlalchemy.orm import Session

# label -> yil -> [(oy, reja, fakt), ...]
LEGACY_COLLECTION = {
    "Markaz umumiy": {
        2023: [
            (3, 111_461_556, 81_183_000),
            (4, 94_833_049, 92_210_715),
            (5, 94_776_729, 100_876_001),
            (6, 101_776_402, 75_531_004),
            (7, 102_605_748, 108_208_926),
            (8, 90_522_239, 106_033_000),
            (9, 127_522_539, 104_857_000),
            (10, 147_368_543, 132_933_000),
            (11, 145_212_039, 148_246_000),
            (12, 144_833_000, 138_718_500),
        ],
        2024: [
            (1, 141_318_001, 139_862_000),
            (2, 154_839_001, 152_571_500),
            (3, 157_631_000, 156_749_000),
            (4, 153_005_250, 151_815_950),
            (5, 138_219_000, 137_494_500),
            (6, 153_338_000, 154_046_000),
            (7, 170_984_500, 167_732_500),
            (8, 164_936_500, 170_812_000),
            (9, 172_274_230, 186_928_500),
            (10, 200_707_423, 197_608_000),
            (11, 165_704_000, 161_156_504),
            (12, 158_660_000, 155_555_000),
        ],
    },
    "Bekobod 1": {
        2025: [
            (1, 51_691_004, 50_536_004),
            (2, 44_175_500, 42_810_500),
            (3, 45_198_000, 41_418_000),
            (4, 49_955_537, 46_682_615),
            (5, 50_392_125, 45_335_611),
            (6, 49_112_070, 47_381_818),
            (7, 55_736_291, 51_736_000),
            (8, 45_566_000, 45_011_000),
            (9, 54_619_078, 53_659_078),
            (10, 53_767_000, 53_767_000),
            (11, 68_700_604, 61_595_109),
            (12, 77_455_430, 76_775_430),
        ],
        2026: [
            (1, 80_538_000, 77_110_000),
            (2, 83_242_000, 81_882_000),
            (3, 76_732_000, 73_862_000),
            (4, 72_726_000, 67_838_000),
            (5, 61_907_846, 54_133_846),
            (6, 83_641_384, 82_481_384),
            (7, 79_471_428, 76_375_428),
        ],
    },
    "Zafar": {
        2025: [
            (1, 155_465_298, 150_738_004),
            (2, 159_319_011, 151_319_011),
            (3, 163_365_509, 160_134_508),
            (4, 165_583_235, 164_985_004),
            (5, 162_308_001, 159_808_001),
            (6, 167_533_579, 157_470_004),
            (7, 197_387_000, 187_887_000),
            (8, 179_086_509, 172_357_509),
            (9, 196_290_120, 183_049_009),
            (10, 184_000_000, 180_545_524),
            (11, 185_226_981, 182_180_481),
            (12, 185_490_506, 182_400_007),
        ],
        2026: [
            (1, 194_740_012, 192_168_012),
            (2, 193_756_007, 192_156_007),
            (3, 189_857_000, 186_806_000),
            (4, 172_625_308, 169_386_008),
            (5, 172_098_004, 167_587_004),
            (6, 196_892_500, 194_437_504),
            (7, 214_243_000, 210_771_006),
        ],
    },
}


def seed_legacy_collection(db: Session) -> int:
    """Import. Qaytaradi: nechta yangi yozuv."""
    existing = {(r.year, r.month, r.branch_label)
                for r in db.query(models.LegacyCollectionMonth).all()}
    made = 0
    for label, years in LEGACY_COLLECTION.items():
        for year, rows in years.items():
            for month, plan, fact in rows:
                if (year, month, label) in existing:
                    continue
                db.add(models.LegacyCollectionMonth(
                    year=year, month=month, branch_label=label,
                    plan=float(plan), fact=float(fact)))
                made += 1
    if made:
        db.commit()
    return made
