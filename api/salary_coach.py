"""Read-only salary goals; use the existing SMM bonus scale without changing payroll."""
import calendar
import roles


def smm_salary_goal(user, state, today):
    fixed = float(user.fix_salary or 0)
    configured = bool(user.branch_id and state and state["plan"] > 0)
    bonus = float(state["bonus"]) if configured else 0.0
    percent = state["percent"] if configured else None
    steps = sorted(roles.SMM_SALES_BONUS, key=lambda row: row[0])
    next_step = next((row for row in steps
                      if configured and row[0] > percent and row[1] > bonus), None)
    remaining = max(0, state["plan"] * next_step[0] / 100 - state["fact"]) if next_step else None
    return {
        "period": today.strftime("%Y-%m"),
        "full_name": user.full_name,
        "branch": user.branch.name if user.branch_id and user.branch else None,
        "branch_id": user.branch_id,
        "fix_salary": fixed,
        "bonus": bonus,
        "total": fixed + bonus,
        "plan": state["plan"] if configured else 0,
        "fact": state["fact"] if state else 0,
        "percent": percent,
        "status": "no_branch" if not user.branch_id else "active" if configured else "no_plan",
        "next_percent": next_step[0] if next_step else None,
        "next_bonus": next_step[1] if next_step else None,
        "next_total": fixed + next_step[1] if next_step else None,
        "gap": remaining,
        "days_left": calendar.monthrange(today.year, today.month)[1] - today.day + 1,
        "scale": [{"min": mn, "bonus": bo, "label": label} for mn, bo, label in steps],
    }


def own_smm_salary(user, db, today, load_state):
    # Never fall back to all-branch revenue for an unassigned employee.
    state = load_state(db, user.branch_id, today.year, today.month) if user.branch_id else None
    return smm_salary_goal(user, state, today)
