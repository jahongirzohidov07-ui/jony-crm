"""KAHOOT SUB JAVOBNI AYTMASIN (2026-10-05, dars rejalari auditi).

Savol ostidagi sub ("wish + were", "Used to", "since") proyektorga va
o'quvchi testiga savol bilan birga chiqadi. 161 ta savolda u javobning
o'zi edi — endi bunday sub izohga (javobdan keyin) ko'chiriladi."""
import os, sys, json, random

os.environ["DATABASE_URL"] = "sqlite:////tmp/ksl/db.sqlite"
os.makedirs("/tmp/ksl", exist_ok=True)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import liveplay

fails = []


def ck(n, g, w):
    ok = g == w
    print(("OK  " if ok else "XATO ") + f"{n}: {g}" + ("" if ok else f"  (kutilgan {w})"))
    if not ok:
        fails.append(n)


print("=== QOIDA ===")
ck("'wish + were' -> were", liveplay._sub_leaks("wish + were", "were"), True)
ck("'Used to' -> used to", liveplay._sub_leaks("Used to", "used to"), True)
ck("'It's … since' -> since", liveplay._sub_leaks("It's … since", "since"), True)
ck("toifa nomi javob emas", liveplay._sub_leaks("Bo'shliq grammatikasi", "invention"), False)
ck("so'z ichida emas: 'was' ~ 'wasp'", liveplay._sub_leaks("wasp nest", "was"), False)
ck("bo'sh sub", liveplay._sub_leaks(None, "were"), False)

q = liveplay._mk(random.Random(1), "grammar", "I wish I ___ taller.", "were",
                 ["was", "am", "be"], explain="Hozirgi istak.", sub="wish + were")
ck("sub olib tashlandi", q["sub"], None)
ck("qoida izohga ko'chdi", q["explain"], "wish + were. Hozirgi istak.")
ck("to'g'ri javob o'zgarmadi", q["options"][q["correct"]], "were")
q = liveplay._mk(random.Random(1), "grammar", "Q?", "invention",
                 ["pantograph", "x", "y"], sub="Bo'shliq grammatikasi")
ck("begunoh sub qoladi", q["sub"], "Bo'shliq grammatikasi")

print("\n=== HAMMA KURSLAR ===")
base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "plans_data")
total = leaks = 0
for c in ["ielts_1_0", "ielts_2_0", "ielts_3_0", "ielts_4_0",
          "ielts_5_0", "ielts_6_0", "ielts_7_0"]:
    p = os.path.join(base, f"{c}.json")
    if not os.path.exists(p):
        continue
    for L in json.load(open(p, encoding="utf-8"))["lessons"]:
        for qq in liveplay._kahoot_questions(random.Random(L["no"]), L):
            total += 1
            if qq["sub"] and liveplay._sub_leaks(qq["sub"], qq["options"][qq["correct"]]):
                leaks += 1
print(f"Kahoot savollari: {total}")
ck("javobni aytadigan sub qolmadi", leaks, 0)
ck("savollar bor", total > 1000, True)

print("\n" + ("BARCHASI OK" if not fails else f"XATOLAR: {fails}"))
sys.exit(1 if fails else 0)
