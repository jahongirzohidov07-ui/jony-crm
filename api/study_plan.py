"""Jony Academy planning table, approved 2026-09-15. Hours are estimates, not tracked time."""
import math

# Each IELTS range uses the full course budget. C1 total was raised to 2000.
STAGES = ((0.5, "A1", 105), (2.0, "A2", 330), (3.5, "B1", 780),
          (5.0, "B1+", 1080), (6.5, "B2", 1380), (8.0, "C1", 2000))
DAILY_HOURS = (1, 2, 3, 4, 5)


def equivalent_hours(band):
    """Interpolate the existing skill estimate; never count XP as hours studied."""
    previous_band, previous_hours = 0.0, 0.0
    for upper, _, total in STAGES:
        if band <= upper:
            return previous_hours + max(0, band - previous_band) / (upper - previous_band) * (total - previous_hours)
        previous_band, previous_hours = upper, total
    return 2000.0


def estimate(target, current_band, daily_hours):
    if daily_hours not in DAILY_HOURS:
        raise ValueError("Kunlik vaqt 1–5 soat bo'lishi kerak")
    result = {"daily_hours": daily_hours, "target_hours": None, "remaining_hours": None,
              "target_cefr": None, "days": None, "percent": None,
              "basis": "academy_hours_v1"}
    if not target:
        return result
    if target > 8:
        return result  # The academy has not supplied a C2/8.5–9.0 budget.
    _, cefr, total = next(stage for stage in STAGES if target <= stage[0])
    done = current_band >= target
    remaining = 0 if done else max(1, math.ceil(total - equivalent_hours(current_band)))
    result.update(target_hours=total, remaining_hours=remaining, target_cefr=cefr,
                  days=math.ceil(remaining / daily_hours),
                  percent=100 if done else min(99, round((total - remaining) / total * 100)))
    return result
