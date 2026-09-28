# -*- coding: utf-8 -*-
"""WRITING AI BAHOSI (2026-09-28).

Jahongir: "Writingni ham avtobaholaydigan qilib qoysak yaxshi bo'lardi.
Hech qanday muammolarsiz bo'lishi yaxshi bolardi".

Mock Writing insholarini AI examiner baholaydi, yakuniy ballni esa
mavjud kalkulyator (mock_marking) chiqaradi — AI va examiner bir xil
arifmetikadan foydalanadi:

  IELTS  har topshiriq 4 mezon (Task Achievement/Response, Coherence
         and Cohesion, Lexical Resource, Grammatical Range and
         Accuracy), har biri butun band 0-9. Task 2 ikki barobar
         og'ir: mezon = (T1 + 2*T2) / 3, keyin mock_marking.ielts_band —
         o'rtacha BIR marta IELTS qoidasi bilan yaxlitlanadi.
  CEFR   yangi 3 topshiriqli format: 1.1 -> 0-5, 1.2 -> 0-6, Part 2 ->
         0-6, keyin mock_marking.cefr_writing_new -> 0-75 va daraja
         (8 -> 45 va 12 -> 57 dan boshqasi TAXMINIY).

Qoidalar:
  - Bo'sh insho AI'ga yuborilmaydi va 0 oladi; IELTS'da 1-20 so'zli
    javob — rasmiy qoida bo'yicha Band 1 (AI'siz). Hammasi shunday
    bo'lsa AI umuman chaqirilmaydi.
  - Topshiriqlar AI'ga "T1/T2/T3" identifikatori bilan boradi — javob
    shu bo'yicha bog'lanadi ("Task 2" va 2-savol chalkashmaydi).
  - O'quvchi ismi AI'ga yuborilmaydi — faqat topshiriq va insho.
  - Provayder xatosi matni saqlanmaydi, faqat qisqa kod.
  - Bitta so'rov = bitta topshiruv (Vercel 30 s): chaqiruvchi
    exam_online / mock_practice alohida endpointda ishlatadi.

Testda AI["call"] almashtiriladi: fn(system, user_text) -> str.
"""
import base64
import html
import json
import re
from datetime import datetime
from typing import Optional

import mock_marking
import cefr_score as C

# IELTS rasmiy qoidasi: 20 so'z va undan kam javob — Band 1 (bo'sh — 0).
# Bunday javob AI'ga yuborilmaydi.
IELTS_SHORT = 20
ESSAY_MAX_CHARS = 6000    # AI'ga yuboriladigan insho chegarasi
SKILLS = ("ielts_writing", "cefr_writing")


class WritingAIError(Exception):
    """code: no_key | rate_limit | ai_error | bad_reply | shape"""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def _default_call(system: str, user_text: str) -> str:
    from student_app import _ai_reply
    # max_tokens katta: "thinking" modellarida o'ylash tokenlari ham shu
    # chegaraga kiradi — javob kesilib qolmasin (2026-09-28 ko'rigi)
    return _ai_reply(system, [{"role": "user", "text": user_text}],
                     max_tokens=6000, temperature=0.1, json_mode=True,
                     per_call=18)


AI = {"call": None}


def _call(system: str, user_text: str) -> str:
    fn = AI.get("call") or _default_call
    try:
        return fn(system, user_text)
    except WritingAIError:
        raise
    except RuntimeError as e:
        if "no-key" in str(e):
            raise WritingAIError("no_key") from None
        raise WritingAIError("ai_error") from None
    except TimeoutError:
        raise WritingAIError("rate_limit") from None
    except LookupError as e:
        # Kalit rad etildi (401/403) — qayta urinishdan foyda yo'q
        if "authentication" in str(e).lower():
            raise WritingAIError("no_key") from None
        raise WritingAIError("ai_error") from None
    except Exception:
        raise WritingAIError("ai_error") from None


# ------------------------------------------------------------ yordamchi
def words(text) -> int:
    """So'z soni — sahifadagi sanagich bilan bir xil (bo'shliq bo'yicha)."""
    return len(re.findall(r"\S+", str(text or "")))


def svg_text(image) -> str:
    """IELTS Task 1 grafigi SVG — undagi yozuvlar (sarlavha, o'qlar,
    qiymatlar) AI'ga matn bo'lib boradi. SVG bo'lmasa bo'sh."""
    s = str(image or "")
    m = re.match(r"data:image/svg\+xml;base64,(.+)$", s, re.S)
    if not m:
        return ""
    try:
        svg = base64.b64decode(m.group(1)).decode("utf-8", "ignore")
    except Exception:
        return ""
    out = []
    for t in re.findall(r"<text\b[^>]*>(.*?)</text>", svg, re.S):
        t = re.sub(r"<[^>]+>", " ", t)
        t = html.unescape(re.sub(r"\s+", " ", t).strip())
        if t:
            out.append(t)
    return " | ".join(out)[:4000]


def skill_of(parts) -> Optional[str]:
    """ielts_writing / cefr_writing — faqat mock Writing baholanadi."""
    from exam_online import _mock_section
    sk = _mock_section(parts or [])
    return sk if sk in SKILLS else None


def tasks_of(parts) -> list:
    """Insho topshiriqlari tartib bilan: har biriga matn va sharoit."""
    out = []
    for p in parts or []:
        for q in p.get("questions") or []:
            if (q.get("type") or "") != "essay":
                continue
            out.append({
                "qid": str(q.get("id") or ""),
                "n": q.get("n"),
                "prompt": str(q.get("q") or "").strip(),
                "instructions": str(p.get("instructions") or "").strip()[:1500],
                "passage": str(p.get("passage") or "").strip()[:2000],
                "min_words": int(q.get("min_words") or 0),
                "chart": svg_text(q.get("image")),
            })
    return out


def _json(raw: str) -> dict:
    m = re.search(r"\{.*\}", str(raw or ""), re.S)
    if not m:
        raise WritingAIError("bad_reply")
    try:
        d = json.loads(m.group(0))
    except (ValueError, TypeError):
        raise WritingAIError("bad_reply") from None
    if not isinstance(d, dict) or not isinstance(d.get("tasks"), list):
        raise WritingAIError("bad_reply")
    return d


def _int(v, lo: int, hi: int) -> Optional[int]:
    try:
        x = int(round(float(v)))
    except (TypeError, ValueError):
        return None
    return max(lo, min(hi, x))


def _feedback(v) -> str:
    s = re.sub(r"\s+", " ", str(v or "")).strip()
    return s[:600]


def _pick(rows: list, tid: str, i: int, total: int):
    """AI javobidan shu topshiriq qatori: "T1"/"T2"… identifikatori
    bo'yicha (savol raqami "Task 2" bilan chalkashmasin), bo'lmasa
    tartib bo'yicha (qatorlar soni teng bo'lsa)."""
    r = next((x for x in rows if str(x.get("id") or "").strip().upper() == tid), None)
    if r is None and len(rows) == total:
        r = rows[i]
    if r is None:
        raise WritingAIError("bad_reply")
    return r


# ------------------------------------------------------------ IELTS
IELTS_SYSTEM = """You are a certified IELTS Academic Writing examiner.
Mark each task strictly by the public IELTS Writing band descriptors.
Give each criterion a WHOLE band from 0 to 9:
- ta: Task 1 = Task Achievement (accurate overview, key features,
  comparisons, data used correctly); Task 2 = Task Response (all parts
  of the question addressed, clear position, developed and supported
  ideas).
- cc: Coherence and Cohesion (logical organisation, paragraphing,
  referencing, range and accuracy of cohesive devices).
- lr: Lexical Resource (range, precision, collocation, spelling,
  word formation).
- gra: Grammatical Range and Accuracy (range of structures, error
  frequency and impact).
Rules: under-length answers (Task 1 < 150 words, Task 2 < 250 words)
lose marks in ta; memorised, off-topic or copied-prompt text scores
low in ta; do not reward length alone. For Task 1, FIGURE TEXT lists
only the words and numbers printed on the chart: if exact values are
not given there, judge ta on the overview, key features and
comparisons, and do not penalise figures you cannot verify. Be
consistent and conservative like a real examiner. Write feedback in
Uzbek (Latin script), 2 short sentences: one main strength and the most
important thing to improve. Each task has an id (T1, T2) — copy it.
Reply with JSON only:
{"tasks":[{"id":"T1","ta":<0-9>,"cc":<0-9>,"lr":<0-9>,"gra":<0-9>,"feedback":"..."}]}"""

KEYS = ("ta", "cc", "lr", "gra")


def _ielts_user(todo: list, essays: dict) -> str:
    blocks = []
    for tid, label, t in todo:
        b = [f"### {label} [id={tid}] (minimum {t['min_words'] or '-'} words)",
             f"QUESTION:\n{t['prompt']}"]
        if t["chart"]:
            b.append(f"FIGURE TEXT (words and numbers printed on the chart):\n{t['chart']}")
        e = essays[t["qid"]]
        b.append(f"CANDIDATE'S ANSWER ({words(e)} words):\n{e[:ESSAY_MAX_CHARS]}")
        blocks.append("\n\n".join(b))
    return "\n\n".join(blocks)


def _grade_ielts(tasks: list, answers: dict) -> dict:
    essays = {t["qid"]: str(answers.get(t["qid"]) or "") for t in tasks}
    ids = {t["qid"]: (f"T{i + 1}", f"Task {i + 1}") for i, t in enumerate(tasks)}
    # 0 so'z -> 0; 1-20 so'z -> Band 1 (IELTS qoidasi); qolgani — AI
    todo = [(ids[t["qid"]][0], ids[t["qid"]][1], t) for t in tasks
            if words(essays[t["qid"]]) > IELTS_SHORT]
    got = {}
    if todo:
        d = _json(_call(IELTS_SYSTEM, _ielts_user(todo, essays)))
        rows = [r for r in d["tasks"] if isinstance(r, dict)]
        for i, (tid, _label, t) in enumerate(todo):
            r = _pick(rows, tid, i, len(todo))
            crit = [_int(r.get(k), 0, 9) for k in KEYS]
            if any(c is None for c in crit):
                raise WritingAIError("bad_reply")
            got[t["qid"]] = (crit, _feedback(r.get("feedback")))
    out_tasks = []
    for t in tasks:
        wc = words(essays[t["qid"]])
        if t["qid"] in got:
            crit, fb = got[t["qid"]]
        elif wc > 0:
            crit, fb = [1, 1, 1, 1], "20 so'z yoki undan kam — IELTS qoidasi bo'yicha Band 1."
        else:
            crit, fb = [0, 0, 0, 0], ""
        tb = mock_marking.ielts_band(crit)
        out_tasks.append({
            "qid": t["qid"], "n": t["n"], "label": ids[t["qid"]][1],
            "words": wc, "min_words": t["min_words"],
            "criteria": dict(zip(KEYS, crit)),
            "band": tb["band"] if tb else 0.0,
            "feedback": fb,
            "skipped": t["qid"] not in got,
        })
    # Task 2 ikki barobar og'ir (IELTS): har mezon (T1 + 2*T2) / 3.
    # Yaxlitlash BIR marta — oxirida, mezonlar o'rtachasida (ielts_band)
    if len(out_tasks) == 2:
        a, b = out_tasks[0]["criteria"], out_tasks[1]["criteria"]
        comb = [(a[k] + 2 * b[k]) / 3 for k in KEYS]
    else:
        n = max(1, len(out_tasks))
        comb = [sum(t["criteria"][k] for t in out_tasks) / n for k in KEYS]
    res = mock_marking.compute("ielts_writing", {"marks": comb})
    if res is None:
        raise WritingAIError("shape")
    return {"skill": "ielts_writing", "score": res["band"], "band": res["band"],
            "max": 9.0, "combined": {k: round(v, 2) for k, v in zip(KEYS, comb)},
            "tasks": out_tasks}


# ------------------------------------------------------------ CEFR
def _cefr_scale_text() -> str:
    lines = []
    for part, mx, lvl, ln in C.WRITING_NEW_PARTS:
        bands = ", ".join(f"{b} = {label}" for b, label in C.WRITING_NEW_BANDS[part])
        lines.append(f"- Task {part} (target {lvl}, {ln}): mark 0-{mx}. {bands}")
    return "\n".join(lines)


CEFR_SYSTEM = """You are a certified examiner of the Uzbekistan CEFR
Multilevel English exam (Writing, new 3-task format). Give each task
ONE holistic whole mark on its official scale:
{scale}
Judge task fulfilment (all points covered, correct register: informal
for 1.1, formal for 1.2, argument for Part 2), organisation, vocabulary
and grammar at the target level. Under-length or off-topic answers lose
marks; memorised or copied text scores low. Be consistent and
conservative like a real examiner. Write feedback in Uzbek (Latin
script), 2 short sentences: one main strength and the most important
thing to improve. Each task has an id (T1, T2, T3) — copy it.
Reply with JSON only:
{{"tasks":[{{"id":"T1","mark":<whole number>,"feedback":"..."}}]}}"""


def _cefr_user(todo: list, essays: dict) -> str:
    blocks = []
    for tid, t, (part, mx, _lv, _ln) in todo:
        b = [f"### Task {part} [id={tid}] (mark 0-{mx}, minimum {t['min_words'] or '-'} words)"]
        if t["instructions"]:
            b.append(f"INSTRUCTIONS:\n{t['instructions']}")
        if t["passage"]:
            b.append(f"INPUT TEXT:\n{t['passage']}")
        b.append(f"QUESTION:\n{t['prompt']}")
        e = essays[t["qid"]]
        b.append(f"CANDIDATE'S ANSWER ({words(e)} words):\n{e[:ESSAY_MAX_CHARS]}")
        blocks.append("\n\n".join(b))
    return "\n\n".join(blocks)


def _grade_cefr(tasks: list, answers: dict) -> dict:
    if len(tasks) != len(C.WRITING_NEW_PARTS):
        raise WritingAIError("shape")
    pairs = list(zip(tasks, C.WRITING_NEW_PARTS))
    essays = {t["qid"]: str(answers.get(t["qid"]) or "") for t in tasks}
    # Bo'sh javob — 0 (AI'siz); qisqasini ham AI baholaydi (shkalada
    # "hajm yetmasa ball tushadi")
    todo = [(f"T{i + 1}", t, spec) for i, (t, spec) in enumerate(pairs)
            if words(essays[t["qid"]]) > 0]
    got = {}
    if todo:
        system = CEFR_SYSTEM.format(scale=_cefr_scale_text())
        d = _json(_call(system, _cefr_user(todo, essays)))
        rows = [r for r in d["tasks"] if isinstance(r, dict)]
        for i, (tid, t, spec) in enumerate(todo):
            r = _pick(rows, tid, i, len(todo))
            mk = _int(r.get("mark"), 0, spec[1])
            if mk is None:
                raise WritingAIError("bad_reply")
            got[t["qid"]] = (mk, _feedback(r.get("feedback")))
    out_tasks, marks = [], []
    for t, (part, mx, _lv, _ln) in pairs:
        mk, fb = got.get(t["qid"], (0, ""))
        marks.append(mk)
        out_tasks.append({
            "qid": t["qid"], "n": t["n"], "part": part, "label": f"Task {part}",
            "words": words(essays[t["qid"]]), "min_words": t["min_words"],
            "mark": mk, "max": mx,
            "level": C.writing_new_band_level(part, mk),
            "feedback": fb,
            "skipped": t["qid"] not in got,
        })
    res = mock_marking.compute("cefr_writing", {"marks": marks})
    if res is None:
        raise WritingAIError("shape")
    return {"skill": "cefr_writing", "score": res["score"], "max": 75,
            "level": res["level"], "exact": bool(res.get("exact")),
            "raw": res.get("raw"), "tasks": out_tasks}


# ------------------------------------------------------------ kirish
def grade(parts, answers) -> dict:
    """Bitta topshiruvning Writing bahosi. Xato bo'lsa WritingAIError."""
    skill = skill_of(parts)
    if not skill:
        raise WritingAIError("shape")
    tasks = tasks_of(parts)
    if not tasks:
        raise WritingAIError("shape")
    ans = answers if isinstance(answers, dict) else {}
    res = (_grade_ielts(tasks, ans) if skill == "ielts_writing"
           else _grade_cefr(tasks, ans))
    res["at"] = datetime.utcnow().isoformat(timespec="seconds")
    return res
