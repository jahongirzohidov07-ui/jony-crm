"""Read-only salary goals; use the existing SMM bonus scale without changing payroll."""
import calendar
import math
import roles


def examiner_salary_goal(pay, today):
    """Display milestones only; the established examiner payroll stays unchanged."""
    days = calendar.monthrange(today.year, today.month)[1] - today.day + 1
    result = {"next_salary": None, "gap_points": None, "target_points": None,
              "progress": 0, "days_left": days if pay["period"] == today.strftime("%Y-%m") else 0}
    if pay.get("volunteer"):
        return {**result, "status": "volunteer"}
    if pay.get("no_exams") or not pay.get("exam_count"):
        return {**result, "status": "no_exams", "next_salary": pay["min"]}
    if pay["salary"] >= pay["max"]:
        return {**result, "status": "maximum", "progress": 100}
    target = min((math.floor(pay["salary"] / 100_000) + 1) * 100_000, pay["max"])
    points = target / pay["unit"]
    return {**result, "status": "active", "next_salary": target,
            "target_points": points,
            "gap_points": round(max(0, points - pay["points"]), 2),
            "progress": round(min(100, max(0, pay["points"] / points * 100)), 1)}

FIXED_SALARY_TIERS = [(0, 100, 1_500_000), (101, 150, 2_000_000),
                      (151, 200, 3_000_000), (201, 300, 5_000_000),
                      (301, None, 8_000_000)]


def student_plan_state(db, branch_id, year, month):
    """Use the branch's student headcount target, never a money target."""
    import models
    if not branch_id:
        return None
    school_year = year if month >= 9 else year - 1
    target = db.query(models.PlanTarget).filter(
        models.PlanTarget.branch_id == branch_id,
        models.PlanTarget.year == school_year,
        models.PlanTarget.month == month,
        models.PlanTarget.metric == "students",
    ).first()
    count = db.query(models.Student).filter(
        models.Student.branch_id == branch_id,
        models.Student.status == "active",
    ).count()
    plan = max(0, float(target.value or 0)) if target else 0
    return {"plan": plan, "fact": count}


def student_fixed_salary(count):
    for minimum, maximum, salary in FIXED_SALARY_TIERS:
        if maximum is None or count <= maximum:
            return salary


def smm_salary_goal(user, state, today):
    count = int(state["fact"]) if state else 0
    fixed = student_fixed_salary(count) if user.branch_id else None
    configured = bool(user.branch_id and state and state["plan"] > 0)
    raw_percent = count / state["plan"] * 100 if configured else None
    bonus = roles.smm_sales_bonus(raw_percent)[0] if configured else 0
    percent = round(raw_percent, 1) if configured else None
    steps = sorted(roles.SMM_SALES_BONUS, key=lambda row: row[0])
    next_step = next((row for row in steps
                      if configured and row[0] > raw_percent and row[1] > bonus), None)
    target_count = math.ceil(state["plan"] * next_step[0] / 100) if next_step else None
    remaining = max(0, target_count - count) if next_step else None
    target_fixed = student_fixed_salary(target_count) if next_step else None
    next_fixed_count = next((n for n in (101, 151, 201, 301) if n > count), None) if user.branch_id else None
    return {
        "period": today.strftime("%Y-%m"),
        "full_name": user.full_name,
        "branch": user.branch.name if user.branch_id and user.branch else None,
        "branch_id": user.branch_id,
        "fix_salary": fixed,
        "bonus": bonus,
        "total": fixed + bonus if fixed is not None else None,
        "plan": state["plan"] if configured else 0,
        "fact": state["fact"] if state else 0,
        "percent": percent,
        "status": "no_branch" if not user.branch_id else "active" if configured else "no_plan",
        "next_percent": next_step[0] if next_step else None,
        "next_bonus": next_step[1] if next_step else None,
        "next_total": target_fixed + next_step[1] if next_step and target_fixed is not None else None,
        "target_count": target_count,
        "next_fixed_count": next_fixed_count,
        "next_fixed_salary": student_fixed_salary(next_fixed_count) if next_fixed_count else None,
        "fixed_status": "active" if fixed is not None else "unconfigured",
        "gap": remaining,
        "days_left": calendar.monthrange(today.year, today.month)[1] - today.day + 1,
        "scale": [{"min": mn, "bonus": bo, "label": label} for mn, bo, label in steps],
        "fixed_scale": [{"min": mn, "max": mx, "salary": salary}
                        for mn, mx, salary in FIXED_SALARY_TIERS],
    }


def own_smm_salary(user, db, today, load_state):
    # Never fall back to all-branch revenue for an unassigned employee.
    state = load_state(db, user.branch_id, today.year, today.month) if user.branch_id else None
    return smm_salary_goal(user, state, today)
