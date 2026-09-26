"""MATEMATIKA TEST BAZASI (2026-09-26, Jahongir: "endi matematikanini
ozing tuzib qoy baza qildib bo'l tez").

Ingliz tilidagi kabi: 3 daraja (Boshlang'ich 5–6-sinf, O'rta 7–9-sinf,
Yuqori 10–11-sinf/DTM) × (12 unit + Mid-course + End of course), har
biri A/B/C/D/E variantda. Savollar PROTSEDURA bilan tuziladi
(parametrlar tasodifiy, javob aniq hisoblanadi) — javob kaliti xato
bo'lmaydi, variantlar cheksiz. Har (daraja, tur, unit, variant) uchun
urug' (seed) o'zgarmas — qayta seed qilinsa ham o'sha savollar.

Tuzilishi ingliz testlari bilan bir xil: unit = 5 bo'lim × 6 savol = 30,
mid/end = 9 bo'lim × 5 savol = 45. Har savol 4 variantli (A–D),
noto'g'ri variantlar odatiy xatolardan (ishora, ±1, o'nlik xatosi).
Mavzu: "Matematika · <mavzu>" — mavzu kesimida tahlil uchun.
"""
import math
import random
from fractions import Fraction

SUBJECT = "math"
LEVELS = ["basic", "intermediate", "advanced"]
LEVEL_TITLES = {"basic": "Boshlang'ich", "intermediate": "O'rta",
                "advanced": "Yuqori"}
VARIANTS = "ABCDE"
SUP = str.maketrans("0123456789-", "⁰¹²³⁴⁵⁶⁷⁸⁹⁻")


def _sup(n) -> str:
    return str(n).translate(SUP)


def fmt(x) -> str:
    """Son matni: 3,5 (o'nli vergul), 2/3, -4."""
    if isinstance(x, Fraction):
        if x.denominator == 1:
            return str(x.numerator)
        return f"{x.numerator}/{x.denominator}"
    if isinstance(x, float):
        if abs(x - round(x)) < 1e-9:
            return str(int(round(x)))
        s = f"{x:.4f}".rstrip("0").rstrip(".")
        return s.replace(".", ",")
    return str(x)


_DIG = "0123456789⁰¹²³⁴⁵⁶⁷⁸⁹"


def _mutate(s: str, k: int) -> str:
    """Matnli javob uchun noto'g'ri variant: oxirgi raqamni o'zgartirish."""
    chars = list(s)
    for i in range(len(chars) - 1, -1, -1):
        if chars[i] in _DIG:
            j = _DIG.index(chars[i])
            base = 0 if j < 10 else 10
            chars[i] = _DIG[base + (j % 10 + k) % 10]
            return "".join(chars)
    return s + " + " + str(k)


def _q(text, correct, wrongs, rng, topic):
    """4 variantli savol. wrongs — noto'g'ri variantlar (kamida 3 xil,
    to'g'risiga teng bo'lmagan); yetmasa tasodifiy siljitish."""
    cs = fmt(correct)
    opts = []
    for w in wrongs:
        ws = fmt(w)
        if ws != cs and ws not in opts:
            opts.append(ws)
        if len(opts) == 3:
            break
    k = 1
    while len(opts) < 3:
        try:
            base = float(str(correct).replace(",", ".")) if not isinstance(correct, Fraction) else float(correct)
            cand = base + k * (1 if k % 2 else -1) * (1 if abs(base) < 20 else round(abs(base) * 0.1))
            ws = fmt(int(cand) if float(cand).is_integer() and not isinstance(correct, Fraction) else cand)
        except (ValueError, TypeError):
            ws = _mutate(cs, k)
        if ws != cs and ws not in opts:
            opts.append(ws)
        k += 1
    pos = rng.randrange(4)
    opts.insert(pos, cs)
    return {"type": "choice", "q": text, "options": opts, "answer": pos,
            "topic": "Matematika · " + topic}


# ----------------------------------------------------------- generatorlar
# Har generator: (rng) -> savol dict. Nomi bo'lim sarlavhasi bilan.

def g_add_sub(r):
    a, b = r.randint(120, 9800), r.randint(45, 4900)
    if r.random() < 0.5:
        return _q(f"Hisoblang: {a} + {b}", a + b, [a + b + 10, a + b - 100, a + b + 1], r,
                  "Natural sonlar")
    a, b = max(a, b), min(a, b)
    return _q(f"Hisoblang: {a} − {b}", a - b, [a - b + 10, a - b - 100, a - b + 1], r,
              "Natural sonlar")


def g_mul_div(r):
    if r.random() < 0.5:
        a, b = r.randint(12, 99), r.randint(3, 49)
        return _q(f"Hisoblang: {a} × {b}", a * b, [a * b + b, a * b - a, a * b + 10], r,
                  "Natural sonlar")
    b, c = r.randint(3, 24), r.randint(12, 150)
    a = b * c
    return _q(f"Hisoblang: {a} : {b}", c, [c + 1, c - 1, c + b], r, "Natural sonlar")


def g_order_ops(r):
    a, b, c = r.randint(2, 12), r.randint(2, 12), r.randint(2, 9)
    d = r.randint(1, 30)
    if r.random() < 0.5:
        return _q(f"Hisoblang: {a} + {b} × {c}", a + b * c, [(a + b) * c, a * b + c, a + b + c], r,
                  "Amallar tartibi")
    return _q(f"Hisoblang: ({a} + {b}) × {c} − {d}", (a + b) * c - d,
              [a + b * c - d, (a + b) * (c - d), (a + b) * c + d], r, "Amallar tartibi")


def g_divisibility(r):
    kind = r.choice(["div", "prime", "gcd", "lcm"])
    if kind == "div":
        d = r.choice([2, 3, 4, 5, 6, 9, 10])
        good = d * r.randint(11, 99)
        bads = []
        while len(bads) < 3:
            x = r.randint(100, 999)
            if x % d and x not in bads:
                bads.append(x)
        return _q(f"Qaysi son {d} ga bo'linadi?", good, bads, r, "Bo'linish belgilari")
    if kind == "prime":
        primes = [11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97]
        p = r.choice(primes)
        comps = r.sample([15, 21, 25, 27, 33, 35, 39, 45, 49, 51, 55, 57, 63, 65, 69, 75, 77, 81, 85, 87, 91, 93, 95], 3)
        return _q("Qaysi son tub son?", p, comps, r, "Tub va murakkab sonlar")
    a, b = r.randint(2, 12) * r.randint(2, 6), r.randint(2, 12) * r.randint(2, 6)
    if kind == "gcd":
        g = math.gcd(a, b)
        return _q(f"EKUB({a}; {b}) = ?", g, [g * 2, max(1, g - 1), a * b // g], r, "EKUB va EKUK")
    l = a * b // math.gcd(a, b)
    return _q(f"EKUK({a}; {b}) = ?", l, [a * b, l // 2 if l % 2 == 0 else l + 6, math.gcd(a, b)], r,
              "EKUB va EKUK")


def _frac(r, maxd=12):
    d = r.randint(2, maxd)
    n = r.randint(1, d - 1)
    return Fraction(n, d)


def g_frac_add(r):
    a, b = _frac(r), _frac(r)
    op = r.choice(["+", "−"])
    if op == "−" and a < b:
        a, b = b, a
    res = a + b if op == "+" else a - b
    wrong = [Fraction(a.numerator + b.numerator, a.denominator + b.denominator) if op == "+"
             else Fraction(abs(a.numerator - b.numerator), a.denominator + b.denominator),
             res + Fraction(1, res.denominator), res * 2]
    return _q(f"Hisoblang: {fmt(a)} {op} {fmt(b)}", res, wrong, r, "Oddiy kasrlar")


def g_frac_mul(r):
    a, b = _frac(r), _frac(r)
    if r.random() < 0.5:
        res = a * b
        return _q(f"Hisoblang: {fmt(a)} × {fmt(b)}", res, [a / b, a + b, res * 2], r, "Oddiy kasrlar")
    res = a / b
    return _q(f"Hisoblang: {fmt(a)} : {fmt(b)}", res, [a * b, b / a, res / 2], r, "Oddiy kasrlar")


def g_frac_compare(r):
    fr = [_frac(r) for _ in range(4)]
    while len({f for f in fr}) < 4:
        fr = [_frac(r) for _ in range(4)]
    big = max(fr)
    return _q("Qaysi kasr eng katta?", big, [f for f in fr if f != big], r, "Kasrlarni taqqoslash")


def g_mixed(r):
    w, f = r.randint(1, 5), _frac(r, 8)
    v = w + f
    kind = r.choice(["to_improper", "of_number"])
    if kind == "to_improper":
        return _q(f"{w} {fmt(f)} aralash sonni noto'g'ri kasr ko'rinishida yozing", v,
                  [Fraction(w * f.numerator + f.denominator, f.denominator),
                   Fraction(w + f.numerator, f.denominator), v + 1], r, "Aralash sonlar")
    n = f.denominator * r.randint(2, 9)
    return _q(f"{n} sonining {fmt(f)} qismini toping", n * f, [n * f + f.denominator, n / f, n * f - 1], r,
              "Sonning qismi")


def g_decimal(r):
    a = round(r.uniform(1, 99), r.choice([1, 2]))
    b = round(r.uniform(0.1, 20), r.choice([1, 2]))
    op = r.choice(["+", "−", "×"])
    if op == "+":
        res = round(a + b, 2); wrong = [round(a + b + 1, 2), round(a + b - 0.1, 2), round(a + b * 10, 2)]
    elif op == "−":
        if a < b:
            a, b = b, a
        res = round(a - b, 2); wrong = [round(a - b + 1, 2), round(a - b - 0.1, 2), round(a + b, 2)]
    else:
        b = r.choice([0.5, 0.2, 0.25, 1.5, 2.5, 0.1, 4]); res = round(a * b, 3)
        wrong = [round(a * b * 10, 3), round(a * b / 10, 3), round(a + b, 3)]
    return _q(f"Hisoblang: {fmt(a)} {op} {fmt(b)}", res, wrong, r, "O'nli kasrlar")


def g_rounding(r):
    x = round(r.uniform(10, 999), 3)
    place = r.choice([("birlar", 0), ("o'ndan birlar", 1), ("yuzdan birlar", 2)])
    res = round(x, place[1]) if place[1] else int(round(x))
    return _q(f"{fmt(x)} sonini {place[0]} xonasigacha yaxlitlang", res,
              [round(x, place[1] + 1), math.floor(x), math.ceil(x)], r, "Yaxlitlash")


def g_percent(r):
    kind = r.choice(["of", "inc", "dec", "what"])
    n = r.choice([40, 60, 80, 120, 150, 200, 240, 300, 400, 500, 640, 800, 1200, 2500])
    p = r.choice([p for p in [5, 10, 12, 15, 20, 25, 30, 40, 50, 60, 75, 80] if (n * p) % 100 == 0])
    v = n * p // 100
    if kind == "of":
        return _q(f"{n} ning {p}% ini toping", v, [v * 10, n - v, v // 2 or 1], r, "Foizlar")
    if kind == "inc":
        return _q(f"{n} ni {p}% ga oshiring", n + v, [n - v, v, n + p], r, "Foizlar")
    if kind == "dec":
        return _q(f"{n} ni {p}% ga kamaytiring", n - v, [n + v, v, n - p], r, "Foizlar")
    return _q(f"{v} soni {n} ning necha foizi?", p, [p + 5, 100 - p, p * 2], r, "Foizlar")


def g_units(r):
    kind = r.choice(["km_m", "m_cm", "kg_g", "h_min", "t_kg", "l_ml"])
    tbl = {"km_m": ("km", "m", 1000), "m_cm": ("m", "sm", 100), "kg_g": ("kg", "g", 1000),
           "h_min": ("soat", "minut", 60), "t_kg": ("t", "kg", 1000), "l_ml": ("l", "ml", 1000)}
    a, b, k = tbl[kind]
    x = r.choice([2, 3, 4, 5, 7, 12, 0.5, 1.5, 2.5, 3.5])
    res = x * k
    return _q(f"{fmt(x)} {a} = ? {b}", int(res) if float(res).is_integer() else res,
              [res * 10, res / 10, res + k], r, "O'lchov birliklari")


def g_linear_eq(r):
    x = r.randint(-12, 25)
    a = r.choice([2, 3, 4, 5, 6, 7, 8, 9, 11, 12])
    b = r.randint(-30, 30)
    kind = r.choice(["ax_b", "ax_b_cx"])
    if kind == "ax_b":
        c = a * x + b
        bs = f"+ {b}" if b >= 0 else f"− {-b}"
        return _q(f"Tenglamani yeching: {a}x {bs} = {c}", x, [-x if x else 1, x + 1, (c + b) // a if a else 0], r,
                  "Chiziqli tenglamalar")
    c = r.choice([1, 2, 3])
    while c == a:
        c = r.choice([1, 2, 3, 4])
    d = (a - c) * x + b       # ax + b = cx + d
    bs = f"+ {b}" if b >= 0 else f"− {-b}"
    ds = f"+ {d}" if d >= 0 else f"− {-d}"
    return _q(f"Tenglamani yeching: {a}x {bs} = {c}x {ds}", x, [-x if x else 2, x + 2, x - 1], r,
              "Chiziqli tenglamalar")


def g_rect(r):
    a, b = r.randint(3, 40), r.randint(3, 40)
    kind = r.choice(["P", "S", "sq"])
    if kind == "P":
        return _q(f"Tomonlari {a} sm va {b} sm bo'lgan to'rtburchak perimetrini toping (sm)", 2 * (a + b),
                  [a + b, a * b, 2 * a + b], r, "Perimetr va yuza")
    if kind == "S":
        return _q(f"Tomonlari {a} sm va {b} sm bo'lgan to'rtburchak yuzini toping (sm²)", a * b,
                  [2 * (a + b), a + b, a * b * 2], r, "Perimetr va yuza")
    return _q(f"Perimetri {4 * a} sm bo'lgan kvadratning yuzini toping (sm²)", a * a,
              [4 * a, 2 * a, a * a * 2], r, "Perimetr va yuza")


def g_triangle_angles(r):
    a, b = r.randint(20, 80), r.randint(20, 80)
    c = 180 - a - b
    return _q(f"Uchburchakning ikki burchagi {a}° va {b}°. Uchinchi burchagi?", c,
              [360 - a - b, 90 - min(a, b), c + 10], r, "Uchburchak burchaklari")


def g_mean(r):
    n = r.choice([3, 4, 5])
    m = r.randint(5, 60)
    nums = [m + r.randint(-4, 4) for _ in range(n - 1)]
    nums.append(m * n - sum(nums))
    r.shuffle(nums)
    return _q("Sonlarning o'rta arifmetigini toping: " + ", ".join(map(str, nums)), m,
              [m + 1, m - 1, sum(nums)], r, "O'rta arifmetik")


def g_speed(r):
    v, t = r.choice([40, 45, 50, 60, 70, 80, 90]), r.choice([2, 3, 4, 5, 6])
    kind = r.choice(["s", "v", "t"])
    s = v * t
    if kind == "s":
        return _q(f"Avtomobil {v} km/soat tezlik bilan {t} soat yurdi. U qancha yo'l bosdi (km)?", s,
                  [v + t, s // 2, s + v], r, "Harakat masalalari")
    if kind == "v":
        return _q(f"Avtomobil {s} km yo'lni {t} soatda bosib o'tdi. Tezligi (km/soat)?", v,
                  [s * t, v + 10, v - 5], r, "Harakat masalalari")
    return _q(f"Avtomobil {s} km yo'lni {v} km/soat tezlik bilan necha soatda bosib o'tadi?", t,
              [t + 1, t - 1 or 1, s // v + 2], r, "Harakat masalalari")


def g_ratio(r):
    a, b = r.randint(2, 9), r.randint(2, 9)
    while a == b:
        b = r.randint(2, 9)
    k = r.randint(3, 15)
    tot = (a + b) * k
    kind = r.choice(["split", "prop"])
    if kind == "split":
        return _q(f"{tot} sonini {a}:{b} nisbatda bo'ling. Katta qismi?", max(a, b) * k,
                  [min(a, b) * k, tot // 2, max(a, b) * k + k], r, "Nisbat va proporsiya")
    x = r.randint(2, 12); y = r.randint(2, 12)
    return _q(f"Proporsiyadan x ni toping: {x} : {y} = {x * k} : x", y * k, [x * k, y * k + k, x * y], r,
              "Nisbat va proporsiya")


def g_integers(r):
    a, b = r.randint(-30, 30), r.randint(-30, 30)
    op = r.choice(["+", "−", "×"])
    bs = f"({b})" if b < 0 else str(b)
    if op == "+":
        res = a + b; wrong = [a - b, -(a + b), abs(a) + abs(b)]
    elif op == "−":
        res = a - b; wrong = [a + b, b - a, -(a - b) + 1]
    else:
        a, b = r.randint(-12, 12), r.randint(-12, 12)
        bs = f"({b})" if b < 0 else str(b)
        res = a * b; wrong = [-(a * b), a * b + a, abs(a * b) + 1]
    return _q(f"Hisoblang: {a} {op} {bs}", res, wrong, r, "Butun sonlar")


def g_powers(r):
    kind = r.choice(["pow", "mulpow", "root", "divpow"])
    if kind == "pow":
        a, n = r.randint(2, 9), r.randint(2, 4)
        return _q(f"Hisoblang: {a}{_sup(n)}", a ** n, [a * n, a ** (n - 1), a ** n + a], r, "Darajalar")
    if kind == "mulpow":
        a, m, n = r.randint(2, 7), r.randint(2, 6), r.randint(2, 6)
        return _q(f"Soddalashtiring: {a}{_sup(m)} · {a}{_sup(n)}", f"{a}{_sup(m + n)}",
                  [f"{a}{_sup(m * n)}", f"{a * a}{_sup(m + n)}", f"{a}{_sup(abs(m - n))}"], r, "Darajalar")
    if kind == "divpow":
        a, m, n = r.randint(2, 7), r.randint(5, 9), r.randint(2, 4)
        return _q(f"Soddalashtiring: {a}{_sup(m)} : {a}{_sup(n)}", f"{a}{_sup(m - n)}",
                  [f"{a}{_sup(m + n)}", f"{a}{_sup(m // n)}", f"1{_sup(m - n)}"], r, "Darajalar")
    k = r.randint(2, 15)
    return _q(f"Hisoblang: √{k * k}", k, [k + 1, k * k // 2, k - 1], r, "Kvadrat ildiz")


def g_simplify(r):
    a, b, c, d = r.randint(2, 9), r.randint(1, 9), r.randint(1, 9), r.randint(1, 9)
    # a x + b - c x + d  yoki qavs ochish
    if r.random() < 0.5:
        x = a - c
        k = b + d
        xs = f"{x}x" if x != 1 else "x"
        return _q(f"Soddalashtiring: {a}x + {b} − {c}x + {d}", f"{xs} + {k}" if x else str(k),
                  [f"{a + c}x + {k}", f"{xs} + {b - d}", f"{x}x − {k}"], r, "Algebraik ifodalar")
    return _q(f"Qavslarni oching: {a}(x + {b}) − {c}", f"{a}x + {a * b - c}",
              [f"{a}x + {b - c}", f"{a}x + {a * b + c}", f"x + {a * b - c}"], r, "Algebraik ifodalar")


def g_inequality(r):
    a = r.choice([2, 3, 4, 5])
    x0 = r.randint(-8, 8)
    b = r.randint(-10, 10)
    c = a * x0 + b
    bs = f"+ {b}" if b >= 0 else f"− {-b}"
    sign = r.choice(["<", ">", "≤", "≥"])
    return _q(f"Tengsizlikni yeching: {a}x {bs} {sign} {c}", f"x {sign} {x0}",
              [f"x {sign} {-x0}", f"x {sign} {x0 + 1}", f"x {'>' if sign in '<≤' else '<'} {x0}"], r,
              "Chiziqli tengsizliklar")


def g_system(r):
    x, y = r.randint(-6, 8), r.randint(-6, 8)
    a1, b1, a2, b2 = r.randint(1, 4), r.randint(1, 4), r.randint(1, 4), r.randint(1, 4)
    while a1 * b2 == a2 * b1:
        a2, b2 = r.randint(1, 4), r.randint(2, 5)
    c1, c2 = a1 * x + b1 * y, a2 * x - b2 * y
    return _q(f"Sistemani yeching: {a1}x + {b1}y = {c1};  {a2}x − {b2}y = {c2}.  x + y = ?", x + y,
              [x - y, x, y], r, "Tenglamalar sistemasi")


def g_formulas(r):
    kind = r.choice(["sq_plus", "sq_minus", "diff", "factor"])
    a, b = r.randint(2, 9), r.randint(1, 9)
    if kind == "sq_plus":
        return _q(f"(x + {b})² ning yoyilmasi", f"x² + {2 * b}x + {b * b}",
                  [f"x² + {b * b}", f"x² + {b}x + {b * b}", f"x² + {2 * b}x + {2 * b}"], r,
                  "Qisqa ko'paytirish formulalari")
    if kind == "sq_minus":
        return _q(f"(x − {b})² ning yoyilmasi", f"x² − {2 * b}x + {b * b}",
                  [f"x² − {b * b}", f"x² − {2 * b}x − {b * b}", f"x² + {2 * b}x + {b * b}"], r,
                  "Qisqa ko'paytirish formulalari")
    if kind == "diff":
        n, m = r.randint(11, 60), r.randint(1, 10)
        return _q(f"Hisoblang: {n + m}² − {n - m}²", 4 * n * m, [2 * n * m, (2 * m) ** 2, 4 * n * m + 2 * m], r,
                  "Qisqa ko'paytirish formulalari")
    return _q(f"Ko'paytuvchilarga ajrating: x² − {a * a}", f"(x − {a})(x + {a})",
              [f"(x − {a})²", f"(x + {a})²", f"(x − {a * a})(x + 1)"], r, "Ko'paytuvchilarga ajratish")


def _bx(b) -> str:
    """+ 3x / − x / '' (bx hadi matni)."""
    if b == 0:
        return ""
    mag = "" if abs(b) == 1 else str(abs(b))
    return f"+ {mag}x" if b > 0 else f"− {mag}x"


def g_quadratic(r):
    x1, x2 = r.randint(-7, 7), r.randint(-7, 7)
    while x1 == x2:
        x2 = r.randint(-7, 7)
    b, c = -(x1 + x2), x1 * x2
    bs = _bx(b)
    cs = f"+ {c}" if c > 0 else (f"− {-c}" if c < 0 else "")
    kind = r.choice(["roots", "sum", "prod"])
    lo, hi = min(x1, x2), max(x1, x2)
    if kind == "roots":
        return _q(f"Tenglamaning ildizlari: x² {bs} {cs} = 0", f"{lo}; {hi}",
                  [f"{-lo}; {-hi}", f"{lo}; {-hi}", f"{lo + 1}; {hi + 1}"], r, "Kvadrat tenglamalar")
    if kind == "sum":
        return _q(f"x² {bs} {cs} = 0 tenglama ildizlari yig'indisi", x1 + x2, [-(x1 + x2), x1 * x2, b], r,
                  "Viet teoremasi")
    return _q(f"x² {bs} {cs} = 0 tenglama ildizlari ko'paytmasi", x1 * x2, [-(x1 * x2), x1 + x2, -c + 1], r,
              "Viet teoremasi")


def g_linear_func(r):
    k, b = r.choice([-3, -2, -1, 2, 3, 4, 5]), r.randint(-9, 9)
    x = r.randint(-5, 6)
    bs = f"+ {b}" if b >= 0 else f"− {-b}"
    kind = r.choice(["value", "point", "zero"])
    if kind == "value":
        return _q(f"y = {k}x {bs} funksiyaning x = {x} dagi qiymati", k * x + b,
                  [k * x - b, k + x + b, -(k * x + b)], r, "Chiziqli funksiya")
    if kind == "point":
        y = k * x + b
        return _q(f"Qaysi nuqta y = {k}x {bs} grafigiga tegishli?", f"({x}; {y})",
                  [f"({x}; {y + k})", f"({y}; {x})", f"({x}; {-y})"], r, "Chiziqli funksiya")
    # nolini toping: kx + b = 0 -> x = -b/k
    b = k * r.randint(-6, 6)
    bs = f"+ {b}" if b >= 0 else f"− {-b}"
    return _q(f"y = {k}x {bs} funksiya grafigi Ox o'qini qaysi nuqtada kesadi (x)?", -b // k,
              [b // k, b, -b], r, "Chiziqli funksiya")


def g_percent_change(r):
    kind = r.choice(["price", "two_step", "find_base"])
    if kind == "price":
        p0 = r.choice([20000, 45000, 60000, 80000, 120000, 250000])
        p = r.choice([10, 15, 20, 25, 30])
        res = p0 * (100 - p) // 100
        return _q(f"Tovar narxi {p0} so'm edi, {p}% chegirma qilindi. Yangi narxi (so'm)?", res,
                  [p0 * p // 100, p0 * (100 + p) // 100, res - 1000], r, "Foiz masalalari")
    if kind == "two_step":
        n = r.choice([100, 200, 400, 500, 1000])
        p = r.choice([10, 20, 25, 50])
        res = n * (100 + p) // 100 * (100 - p) // 100
        return _q(f"{n} ni avval {p}% ga oshirib, keyin {p}% ga kamaytirdik. Natija?", res,
                  [n, n * (100 + p) // 100, n - n * p // 100], r, "Foiz masalalari")
    p = r.choice([10, 20, 25, 40, 50])
    base = r.choice([80, 120, 200, 250, 300, 400, 600])
    return _q(f"Sonning {p}% i {base * p // 100} ga teng. Sonni toping", base, [base * p // 100 * 2, base + p, base // 2], r,
              "Foiz masalalari")


def g_pythagoras(r):
    triples = [(3, 4, 5), (6, 8, 10), (5, 12, 13), (9, 12, 15), (8, 15, 17), (12, 16, 20), (7, 24, 25)]
    a, b, c = r.choice(triples)
    if r.random() < 0.5:
        return _q(f"To'g'ri burchakli uchburchak katetlari {a} va {b}. Gipotenuzasi?", c,
                  [a + b, c + 1, c - 1], r, "Pifagor teoremasi")
    return _q(f"To'g'ri burchakli uchburchak gipotenuzasi {c}, bir kateti {a}. Ikkinchi kateti?", b,
              [c - a, b + 1, c + a], r, "Pifagor teoremasi")


def g_area(r):
    kind = r.choice(["tri", "circle_len", "circle_area", "trap"])
    if kind == "tri":
        b, h = r.randint(4, 30) * 2, r.randint(3, 20)
        return _q(f"Asosi {b} va balandligi {h} bo'lgan uchburchak yuzi", b * h // 2, [b * h, b + h, b * h // 2 + h], r,
                  "Yuzalar")
    if kind == "circle_len":
        rr = r.randint(2, 15)
        return _q(f"Radiusi {rr} bo'lgan aylana uzunligi (π orqali)", f"{2 * rr}π",
                  [f"{rr}π", f"{rr * rr}π", f"{4 * rr}π"], r, "Aylana va doira")
    if kind == "circle_area":
        rr = r.randint(2, 15)
        return _q(f"Radiusi {rr} bo'lgan doira yuzi (π orqali)", f"{rr * rr}π",
                  [f"{2 * rr}π", f"{rr}π", f"{2 * rr * rr}π"], r, "Aylana va doira")
    a, b, h = r.randint(3, 15), r.randint(3, 15), r.randint(2, 12) * 2
    return _q(f"Asoslari {a} va {b}, balandligi {h} bo'lgan trapetsiya yuzi", (a + b) * h // 2,
              [(a + b) * h, a * b * h // 2, (a + b) * h // 2 + h], r, "Yuzalar")


def g_stats(r):
    n = r.choice([5, 6, 7])
    nums = [r.randint(1, 20) for _ in range(n)]
    kind = r.choice(["median", "mode", "range", "prob"])
    s = ", ".join(map(str, nums))
    if kind == "median":
        srt = sorted(nums)
        med = srt[n // 2] if n % 2 else Fraction(srt[n // 2 - 1] + srt[n // 2], 2)
        return _q(f"Medianani toping: {s}", med, [srt[0], srt[-1], Fraction(sum(nums), n)], r, "Statistika")
    if kind == "mode":
        m = r.randint(1, 20)
        nums = nums[:-2] + [m, m]
        r.shuffle(nums)
        s = ", ".join(map(str, nums))
        others = [x for x in nums if x != m][:3] or [m + 1, m + 2, m + 3]
        return _q(f"Modani toping: {s}", m, others, r, "Statistika")
    if kind == "range":
        return _q(f"Sonlar ko'lami (eng katta − eng kichik): {s}", max(nums) - min(nums),
                  [max(nums) + min(nums), max(nums), max(nums) - min(nums) + 1], r, "Statistika")
    tot, good = r.choice([6, 8, 10, 12, 20]), r.randint(1, 5)
    return _q(f"Qutida {tot} ta shar, ulardan {good} tasi qizil. Tasodifan olingan shar qizil bo'lish ehtimoli?",
              Fraction(good, tot), [Fraction(good, tot - good) if tot != good else Fraction(1, 2),
                                    Fraction(tot - good, tot), Fraction(1, tot)], r, "Ehtimollik")


def g_arith_prog(r):
    a1, d = r.randint(-5, 12), r.choice([-3, -2, 2, 3, 4, 5, 7])
    n = r.randint(5, 20)
    kind = r.choice(["nth", "sum"])
    an = a1 + (n - 1) * d
    if kind == "nth":
        return _q(f"Arifmetik progressiyada a₁ = {a1}, d = {d}. a{_sub(n)} ni toping", an,
                  [a1 + n * d, a1 * n + d, an - d], r, "Arifmetik progressiya")
    sn = (a1 + an) * n // 2
    return _q(f"Arifmetik progressiyada a₁ = {a1}, d = {d}. Dastlabki {n} ta hadi yig'indisi", sn,
              [(a1 + an) * n, sn + d, an * n], r, "Arifmetik progressiya")


def g_geom_prog(r):
    b1, q = r.choice([1, 2, 3, 5]), r.choice([2, 3, -2])
    n = r.randint(3, 6)
    kind = r.choice(["nth", "sum"])
    bn = b1 * q ** (n - 1)
    if kind == "nth":
        return _q(f"Geometrik progressiyada b₁ = {b1}, q = {q}. {n}-hadi", bn, [b1 * q ** n, b1 * q * (n - 1), -bn], r,
                  "Geometrik progressiya")
    sn = b1 * (q ** n - 1) // (q - 1)
    return _q(f"Geometrik progressiyada b₁ = {b1}, q = {q}. Dastlabki {n} ta hadi yig'indisi", sn,
              [sn - b1, bn, b1 * (q ** n)], r, "Geometrik progressiya")


def g_log(r):
    kind = r.choice(["log", "exp_eq", "log_eq", "prop"])
    if kind == "log":
        a, n = r.choice([2, 3, 5, 10]), r.randint(1, 5)
        return _q(f"Hisoblang: log{_sub(a)} {a ** n}", n, [n + 1, a ** n // a, n - 1], r, "Logarifmlar")
    if kind == "exp_eq":
        a, n = r.choice([2, 3, 5, 7]), r.randint(2, 5)
        return _q(f"Tenglamani yeching: {a}{_sup('x')} = {a ** n}", n, [a ** n // a, n + 1, a], r,
                  "Ko'rsatkichli tenglamalar")
    if kind == "log_eq":
        a, n = r.choice([2, 3, 5]), r.randint(2, 4)
        return _q(f"Tenglamani yeching: log{_sub(a)} x = {n}", a ** n, [a * n, n ** a, a ** (n - 1)], r,
                  "Logarifmik tenglamalar")
    a, m, n = r.choice([2, 3, 5]), r.randint(1, 4), r.randint(1, 4)
    return _q(f"Hisoblang: log{_sub(a)} {a ** m} + log{_sub(a)} {a ** n}", m + n, [m * n, a ** (m + n), abs(m - n)], r,
              "Logarifmlar")


SUB = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")


def _sub(n) -> str:
    return str(n).translate(SUB)


def g_trig(r):
    vals = [("sin 30°", "1/2"), ("cos 60°", "1/2"), ("sin 90°", "1"), ("cos 0°", "1"), ("tg 45°", "1"),
            ("sin 0°", "0"), ("cos 90°", "0"), ("sin 45°", "√2/2"), ("cos 45°", "√2/2"),
            ("sin 60°", "√3/2"), ("cos 30°", "√3/2"), ("tg 60°", "√3"), ("tg 30°", "√3/3"),
            ("sin 180°", "0"), ("cos 180°", "−1")]
    kind = r.choice(["value", "rad", "identity"])
    if kind == "value":
        name, v = r.choice(vals)
        others = [x[1] for x in vals if x[1] != v]
        return _q(f"Hisoblang: {name}", v, r.sample(sorted(set(others)), 3), r, "Trigonometriya")
    if kind == "rad":
        deg, rad = r.choice([(30, "π/6"), (45, "π/4"), (60, "π/3"), (90, "π/2"), (180, "π"), (120, "2π/3"),
                             (135, "3π/4"), (270, "3π/2"), (360, "2π")])
        others = [x for x in ["π/6", "π/4", "π/3", "π/2", "π", "2π/3", "3π/4", "3π/2", "2π"] if x != rad]
        return _q(f"{deg}° ni radianda ifodalang", rad, r.sample(others, 3), r, "Trigonometriya")
    s = r.choice([Fraction(3, 5), Fraction(5, 13), Fraction(8, 17), Fraction(1, 2)])
    c2 = 1 - s * s
    return _q(f"sin α = {fmt(s)} bo'lsa, cos² α ni toping", c2, [1 - s, s * s, 1 + s * s], r, "Trigonometriya")


def g_quad_ineq(r):
    x1, x2 = r.randint(-6, 3), r.randint(4, 9)
    b, c = -(x1 + x2), x1 * x2
    bs = _bx(b)
    cs = f"+ {c}" if c > 0 else (f"− {-c}" if c < 0 else "")
    if r.random() < 0.5:
        return _q(f"Tengsizlikni yeching: x² {bs} {cs} < 0", f"({x1}; {x2})",
                  [f"(−∞; {x1}) ∪ ({x2}; +∞)", f"[{x1}; {x2}]", f"({-x2}; {-x1})"], r, "Kvadrat tengsizliklar")
    return _q(f"Tengsizlikni yeching: x² {bs} {cs} > 0", f"(−∞; {x1}) ∪ ({x2}; +∞)",
              [f"({x1}; {x2})", f"(−∞; {x2})", f"({x1}; +∞)"], r, "Kvadrat tengsizliklar")


def g_rational_eq(r):
    x = r.randint(-8, 9)
    a = r.randint(2, 9)
    while x == a:               # maxraj nolga aylanmasin
        x = r.randint(-8, 9)
    # (x² − a²)/(x − a) = x + a = c
    c = x + a
    return _q(f"Tenglamani yeching: (x² − {a * a}) / (x − {a}) = {c}", x, [-x if x else 1, c, x + a], r,
              "Kasr-ratsional tenglamalar")


def g_combinatorics(r):
    kind = r.choice(["fact", "perm", "comb", "rule"])
    if kind == "fact":
        n = r.randint(3, 7)
        return _q(f"Hisoblang: {n}!", math.factorial(n), [math.factorial(n - 1), n * n, math.factorial(n) + n], r,
                  "Kombinatorika")
    if kind == "perm":
        n, k = r.randint(4, 8), r.randint(2, 3)
        v = math.perm(n, k)
        return _q(f"{n} ta kitobdan {k} tasini javonga tartib bilan necha usulda joylash mumkin?", v,
                  [math.comb(n, k), n * k, v // 2], r, "Kombinatorika")
    if kind == "comb":
        n, k = r.randint(5, 10), r.randint(2, 4)
        v = math.comb(n, k)
        return _q(f"{n} kishidan {k} kishilik jamoani necha usulda tanlash mumkin?", v,
                  [math.perm(n, k), n * k, v + n], r, "Kombinatorika")
    a, b = r.randint(3, 8), r.randint(3, 8)
    return _q(f"{a} xil ko'ylak va {b} xil shim bor. Nechta turli juftlik tanlash mumkin?", a * b,
              [a + b, a * b // 2, a * b + a], r, "Kombinatorika")


def g_probability(r):
    kind = r.choice(["dice", "cards", "coins"])
    if kind == "dice":
        s = r.randint(2, 12)
        ways = sum(1 for i in range(1, 7) for j in range(1, 7) if i + j == s)
        p = Fraction(ways, 36)
        return _q(f"Ikki o'yin soqqasi tashlandi. Ochkolar yig'indisi {s} bo'lish ehtimoli?", p,
                  [Fraction(ways, 12), Fraction(1, 36), Fraction(s, 36)], r, "Ehtimollik")
    if kind == "cards":
        tot, good = r.choice([10, 20, 25, 30, 36]), r.choice([2, 4, 5, 6, 9])
        p = Fraction(good, tot)
        return _q(f"{tot} ta kartochkadan {good} tasi yutuqli. Bitta kartochka olinganda yutuq ehtimoli?", p,
                  [Fraction(good, tot - good), Fraction(tot - good, tot), Fraction(1, good)], r, "Ehtimollik")
    n = r.choice([2, 3])
    p = Fraction(1, 2 ** n)
    return _q(f"Tanga {n} marta tashlandi. Hammasida gerb tushish ehtimoli?", p,
              [Fraction(1, n), Fraction(n, 2 ** n), Fraction(1, 2)], r, "Ehtimollik")


def g_derivative(r):
    kind = r.choice(["power", "value", "poly"])
    if kind == "power":
        n = r.randint(2, 6)
        return _q(f"f(x) = x{_sup(n)} funksiya hosilasi", f"{n}x{_sup(n - 1)}",
                  [f"x{_sup(n - 1)}", f"{n}x{_sup(n)}", f"{n - 1}x{_sup(n - 1)}"], r, "Hosila")
    a, b, x0 = r.randint(2, 6), r.randint(-9, 9), r.randint(-4, 5)
    if kind == "value":
        bs = f"+ {b}x" if b >= 0 else f"− {-b}x"
        return _q(f"f(x) = {a}x² {bs} bo'lsa, f′({x0}) ni toping", 2 * a * x0 + b,
                  [a * x0 * x0 + b * x0, 2 * a * x0 - b, a * x0 + b], r, "Hosila")
    c = r.randint(-9, 9)
    bs = f"+ {b}x" if b >= 0 else f"− {-b}x"
    cs = f"+ {c}" if c >= 0 else f"− {-c}"
    der = f"{3 * a}x² + {b}" if b >= 0 else f"{3 * a}x² − {-b}"
    return _q(f"f(x) = {a}x³ {bs} {cs} funksiya hosilasi", der,
              [f"{a}x² {bs.replace('x', '')}", f"{3 * a}x² {bs}", f"{3 * a}x {bs.replace('x', '')}"], r, "Hosila")


def g_function_props(r):
    kind = r.choice(["domain", "even", "zero"])
    if kind == "domain":
        a = r.randint(1, 9)
        return _q(f"y = 1/(x − {a}) funksiyaning aniqlanish sohasi", f"x ≠ {a}",
                  [f"x ≠ {-a}", f"x > {a}", "barcha x"], r, "Funksiya xossalari")
    if kind == "even":
        evens = ["y = x²", "y = x⁴ + 1", "y = |x|", "y = cos x", "y = x² − 3"]
        odds = ["y = x³", "y = x", "y = sin x", "y = x³ + x", "y = 1/x"]
        e = r.choice(evens)
        return _q("Qaysi funksiya juft?", e, r.sample(odds, 3), r, "Funksiya xossalari")
    a, b = r.choice([2, 3, 4, 5]), r.randint(1, 5)
    return _q(f"y = {a}x − {a * b} funksiyaning noli", b, [-b, a * b, a], r, "Funksiya xossalari")


def g_volume(r):
    kind = r.choice(["box", "cube", "cyl", "cone", "sphere"])
    if kind == "box":
        a, b, c = r.randint(2, 12), r.randint(2, 12), r.randint(2, 12)
        return _q(f"O'lchamlari {a}, {b}, {c} bo'lgan to'g'ri burchakli parallelepiped hajmi", a * b * c,
                  [2 * (a * b + b * c + a * c), a + b + c, a * b * c // 2], r, "Hajmlar")
    if kind == "cube":
        a = r.randint(2, 10)
        return _q(f"Qirrasi {a} bo'lgan kub hajmi", a ** 3, [6 * a * a, a * a, 3 * a], r, "Hajmlar")
    if kind == "cyl":
        rr, h = r.randint(1, 8), r.randint(2, 12)
        return _q(f"Radiusi {rr}, balandligi {h} bo'lgan silindr hajmi (π orqali)", f"{rr * rr * h}π",
                  [f"{2 * rr * h}π", f"{rr * h}π", f"{rr * rr * h // 3 or 1}π"], r, "Hajmlar")
    if kind == "cone":
        rr, h = r.randint(1, 6), r.choice([3, 6, 9, 12])
        return _q(f"Radiusi {rr}, balandligi {h} bo'lgan konus hajmi (π orqali)", f"{rr * rr * h // 3}π",
                  [f"{rr * rr * h}π", f"{rr * h}π", f"{rr * rr * h // 2}π"], r, "Hajmlar")
    rr = r.choice([3, 6, 9])
    return _q(f"Radiusi {rr} bo'lgan shar hajmi (π orqali)", f"{4 * rr ** 3 // 3}π",
              [f"{4 * rr * rr}π", f"{rr ** 3}π", f"{2 * rr ** 3}π"], r, "Hajmlar")


def g_word_problems(r):
    kind = r.choice(["work", "meet", "mix"])
    if kind == "work":
        a, b = r.choice([(3, 6), (4, 12), (6, 12), (2, 3), (5, 20), (6, 3), (10, 15), (4, 4)])
        t = Fraction(a * b, a + b)
        return _q(f"Birinchi ishchi ishni {a} kunda, ikkinchisi {b} kunda bajaradi. Birgalikda necha kunda bajarishadi?", t,
                  [Fraction(a + b, 2), a + b, Fraction(a * b, 2)], r, "Matnli masalalar")
    if kind == "meet":
        v1, v2, s = r.choice([40, 50, 60, 70]), r.choice([30, 40, 50, 80]), None
        t = r.choice([2, 3, 4, 5])
        s = (v1 + v2) * t
        return _q(f"Ikki shahar orasi {s} km. Ikki avtomobil bir vaqtda bir-biriga qarab {v1} va {v2} km/soat tezlikda yo'lga chiqdi. Necha soatdan keyin uchrashadi?",
                  t, [t + 1, s // max(v1, v2), s // abs(v1 - v2) if v1 != v2 else t + 2], r, "Matnli masalalar")
    m, p = r.choice([200, 300, 400, 500, 800]), r.choice([10, 15, 20, 25, 40])
    return _q(f"{m} g eritmada {p}% tuz bor. Eritmada necha gramm tuz bor?", m * p // 100,
              [m - m * p // 100, p, m * p // 10], r, "Matnli masalalar")


def g_abs_eq(r):
    kind = r.choice(["abs", "root"])
    if kind == "abs":
        a, b = r.randint(-8, 8), r.randint(1, 9)
        s = f"− {-a}" if a < 0 else f"+ {a}"
        # |x + a| = b  →  x = −a ± b, yig'indi = −2a
        return _q(f"Tenglama ildizlari yig'indisi: |x {s}| = {b}", -2 * a,
                  [2 * b, -a + b, 2 * a], r, "Modulli tenglamalar")
    k = r.randint(2, 9)
    a = r.randint(-5, 9)
    return _q(f"Tenglamani yeching: √(x − {a}) = {k}" if a >= 0 else f"Tenglamani yeching: √(x + {-a}) = {k}",
              k * k + a, [k + a, k * k - a, k * k], r, "Irratsional tenglamalar")


def g_number_theory(r):
    kind = r.choice(["rem", "digits", "count"])
    if kind == "rem":
        a, b = r.randint(100, 999), r.choice([7, 9, 11, 13])
        return _q(f"{a} ni {b} ga bo'lgandagi qoldiq", a % b, [(a % b + 1) % b, b - a % b, a // b % 10], r,
                  "Sonlar nazariyasi")
    if kind == "digits":
        n = r.randint(1000, 9999)
        s = sum(map(int, str(n)))
        return _q(f"{n} sonining raqamlari yig'indisi", s, [s + 1, s - 1, s + 9], r, "Sonlar nazariyasi")
    d = r.choice([3, 4, 6, 7, 8, 9])
    lo, hi = r.choice([100, 200, 300]), r.choice([500, 600, 800, 900])
    cnt = hi // d - (lo - 1) // d
    return _q(f"{lo} dan {hi} gacha (ikkalasi ham) nechta son {d} ga bo'linadi?", cnt, [cnt + 1, cnt - 1, (hi - lo) // d], r,
              "Sonlar nazariyasi")


# --------------------------------------------------------------- dastur
# Har unit: (nom, [(bo'lim nomi, generator), ...5 ta])
SYLLABUS = {
    "basic": [
        ("Natural sonlar ustida amallar", [("Qo'shish va ayirish", g_add_sub), ("Ko'paytirish va bo'lish", g_mul_div),
                                           ("Amallar tartibi", g_order_ops), ("Qo'shish va ayirish", g_add_sub),
                                           ("Ko'paytirish va bo'lish", g_mul_div)]),
        ("Bo'linish belgilari, EKUB va EKUK", [("Bo'linish belgilari", g_divisibility), ("Amallar tartibi", g_order_ops),
                                              ("Bo'linish belgilari", g_divisibility), ("Ko'paytirish va bo'lish", g_mul_div),
                                              ("Bo'linish belgilari", g_divisibility)]),
        ("Oddiy kasrlar: taqqoslash, qo'shish va ayirish", [("Kasrlarni taqqoslash", g_frac_compare), ("Qo'shish va ayirish", g_frac_add),
                                                            ("Qo'shish va ayirish", g_frac_add), ("Kasrlarni taqqoslash", g_frac_compare),
                                                            ("Qo'shish va ayirish", g_frac_add)]),
        ("Oddiy kasrlar: ko'paytirish, bo'lish, aralash sonlar", [("Ko'paytirish va bo'lish", g_frac_mul), ("Aralash sonlar", g_mixed),
                                                                  ("Ko'paytirish va bo'lish", g_frac_mul), ("Qo'shish va ayirish", g_frac_add),
                                                                  ("Aralash sonlar", g_mixed)]),
        ("O'nli kasrlar", [("O'nli kasrlar", g_decimal), ("Yaxlitlash", g_rounding), ("O'nli kasrlar", g_decimal),
                           ("Yaxlitlash", g_rounding), ("O'nli kasrlar", g_decimal)]),
        ("Foizlar", [("Foizlar", g_percent), ("Foizlar", g_percent), ("O'nli kasrlar", g_decimal),
                     ("Foizlar", g_percent), ("Foizlar", g_percent)]),
        ("O'lchov birliklari", [("O'lchov birliklari", g_units), ("O'lchov birliklari", g_units), ("O'nli kasrlar", g_decimal),
                                ("O'lchov birliklari", g_units), ("Foizlar", g_percent)]),
        ("Tenglamalar", [("Chiziqli tenglamalar", g_linear_eq), ("Chiziqli tenglamalar", g_linear_eq), ("Amallar tartibi", g_order_ops),
                         ("Chiziqli tenglamalar", g_linear_eq), ("Chiziqli tenglamalar", g_linear_eq)]),
        ("Perimetr, yuza, burchaklar", [("Perimetr va yuza", g_rect), ("Uchburchak burchaklari", g_triangle_angles),
                                        ("Perimetr va yuza", g_rect), ("Uchburchak burchaklari", g_triangle_angles),
                                        ("Perimetr va yuza", g_rect)]),
        ("O'rta arifmetik va harakat masalalari", [("O'rta arifmetik", g_mean), ("Harakat masalalari", g_speed),
                                                   ("O'rta arifmetik", g_mean), ("Harakat masalalari", g_speed),
                                                   ("Harakat masalalari", g_speed)]),
        ("Nisbat va proporsiya", [("Nisbat va proporsiya", g_ratio), ("Nisbat va proporsiya", g_ratio), ("Foizlar", g_percent),
                                  ("Nisbat va proporsiya", g_ratio), ("Nisbat va proporsiya", g_ratio)]),
        ("Butun sonlar", [("Butun sonlar", g_integers), ("Butun sonlar", g_integers), ("Chiziqli tenglamalar", g_linear_eq),
                          ("Butun sonlar", g_integers), ("Butun sonlar", g_integers)]),
    ],
    "intermediate": [
        ("Darajalar va ildizlar", [("Darajalar", g_powers)] * 5),
        ("Algebraik ifodalar", [("Algebraik ifodalar", g_simplify), ("Algebraik ifodalar", g_simplify), ("Darajalar", g_powers),
                                ("Algebraik ifodalar", g_simplify), ("Algebraik ifodalar", g_simplify)]),
        ("Chiziqli tenglamalar", [("Chiziqli tenglamalar", g_linear_eq)] * 4 + [("Algebraik ifodalar", g_simplify)]),
        ("Chiziqli tengsizliklar", [("Chiziqli tengsizliklar", g_inequality)] * 4 + [("Chiziqli tenglamalar", g_linear_eq)]),
        ("Tenglamalar sistemasi", [("Tenglamalar sistemasi", g_system)] * 4 + [("Chiziqli tenglamalar", g_linear_eq)]),
        ("Qisqa ko'paytirish formulalari", [("Qisqa ko'paytirish formulalari", g_formulas)] * 5),
        ("Kvadrat tenglamalar", [("Kvadrat tenglamalar", g_quadratic)] * 4 + [("Qisqa ko'paytirish formulalari", g_formulas)]),
        ("Chiziqli funksiya", [("Chiziqli funksiya", g_linear_func)] * 4 + [("Tenglamalar sistemasi", g_system)]),
        ("Foiz masalalari", [("Foiz masalalari", g_percent_change)] * 4 + [("Nisbat va proporsiya", g_ratio)]),
        ("Pifagor teoremasi va yuzalar", [("Pifagor teoremasi", g_pythagoras), ("Yuzalar", g_area), ("Pifagor teoremasi", g_pythagoras),
                                          ("Yuzalar", g_area), ("Yuzalar", g_area)]),
        ("Statistika va ehtimollik", [("Statistika", g_stats)] * 5),
        ("Arifmetik progressiya", [("Arifmetik progressiya", g_arith_prog)] * 4 + [("Kvadrat tenglamalar", g_quadratic)]),
    ],
    "advanced": [
        ("Ko'rsatkichli ifodalar va logarifmlar", [("Logarifmlar", g_log)] * 5),
        ("Trigonometriya", [("Trigonometriya", g_trig)] * 5),
        ("Progressiyalar", [("Arifmetik progressiya", g_arith_prog), ("Geometrik progressiya", g_geom_prog),
                            ("Arifmetik progressiya", g_arith_prog), ("Geometrik progressiya", g_geom_prog),
                            ("Geometrik progressiya", g_geom_prog)]),
        ("Kvadrat tengsizliklar va kasr-ratsional tenglamalar", [("Kvadrat tengsizliklar", g_quad_ineq), ("Kasr-ratsional tenglamalar", g_rational_eq),
                                                                 ("Kvadrat tengsizliklar", g_quad_ineq), ("Kvadrat tenglamalar", g_quadratic),
                                                                 ("Kasr-ratsional tenglamalar", g_rational_eq)]),
        ("Kombinatorika", [("Kombinatorika", g_combinatorics)] * 5),
        ("Ehtimollik", [("Ehtimollik", g_probability)] * 4 + [("Kombinatorika", g_combinatorics)]),
        ("Hosila", [("Hosila", g_derivative)] * 5),
        ("Funksiya xossalari", [("Funksiya xossalari", g_function_props)] * 4 + [("Hosila", g_derivative)]),
        ("Hajmlar", [("Hajmlar", g_volume)] * 4 + [("Yuzalar", g_area)]),
        ("Matnli masalalar", [("Matnli masalalar", g_word_problems)] * 5),
        ("Modulli va irratsional tenglamalar", [("Modulli va irratsional", g_abs_eq)] * 4 + [("Kvadrat tenglamalar", g_quadratic)]),
        ("Sonlar nazariyasi", [("Sonlar nazariyasi", g_number_theory)] * 4 + [("Kombinatorika", g_combinatorics)]),
    ],
}

UNIT_Q = 6          # unit: 5 bo'lim × 6 = 30
MIDEND_Q = 5        # mid/end: 9 bo'lim × 5 = 45


def _seed(level, kind, unit_no, variant) -> int:
    s = f"jony-math|{level}|{kind}|{unit_no}|{variant}"
    return sum((i + 1) * ord(ch) for i, ch in enumerate(s)) * 7919


def _make_parts(r, specs, per_part, part_prefix="Part"):
    parts = []
    for i, (title, gen) in enumerate(specs, 1):
        qs, seen = [], set()
        tries = 0
        while len(qs) < per_part and tries < 200:
            tries += 1
            q = gen(r)
            key = (q["q"], tuple(sorted(q["options"])))
            if key in seen:
                continue
            seen.add(key)
            qs.append(q)
        parts.append({"title": f"{part_prefix} {i} · {title}",
                      "instructions": "To'g'ri javobni tanlang.",
                      "passage": "", "script": "", "questions": qs})
    return parts


def build(level: str, kind: str, unit_no, variant: str) -> dict:
    """Bitta shablon: {title, parts}."""
    r = random.Random(_seed(level, kind, unit_no, variant))
    units = SYLLABUS[level]
    lt = LEVEL_TITLES[level]
    if kind == "unit":
        name, specs = units[unit_no - 1]
        parts = _make_parts(r, specs, UNIT_Q)
        title = f"Matematika {lt} · Unit {unit_no} — {name}"
    else:
        pool = units[:6] if kind == "mid" else units
        # 9 bo'lim: har unitdan bittadan (kerak bo'lsa takror), aralash
        specs = []
        while len(specs) < 9:
            for name, us in pool:
                specs.append(r.choice(us))
                if len(specs) == 9:
                    break
        parts = _make_parts(r, specs, MIDEND_Q)
        title = f"Matematika {lt} · {'Mid-course' if kind == 'mid' else 'End of course'}"
    if variant != "A":
        title += f" — {variant} varianti"
    return {"title": title, "parts": parts}


def all_keys():
    for level in LEVELS:
        for u in range(1, 13):
            yield level, "unit", u
        yield level, "mid", None
        yield level, "end", None
