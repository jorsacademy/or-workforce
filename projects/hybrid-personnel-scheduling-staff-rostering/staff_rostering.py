"""Hybrid personnel scheduling model for staff rostering problems.

This module builds and solves a synthetic mixed-integer linear programming
(MILP) staff-rostering problem for a regional technical support operations
center. The data are generated locally and do not represent any real company.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

import pulp


@dataclass(frozen=True)
class Shift:
    name: str
    start: int
    end: int
    hours: int
    cost_multiplier: float


STAFF = [f"E{i:02d}" for i in range(1, 19)]
DAYS = list(range(1, 15))
SKILLS = ["network", "systems", "security", "applications"]
SHIFTS: Dict[str, Shift] = {
    "EARLY": Shift("EARLY", 6, 14, 8, 1.00),
    "DAY": Shift("DAY", 9, 17, 8, 1.00),
    "LATE": Shift("LATE", 14, 22, 8, 1.08),
    "NIGHT": Shift("NIGHT", 22, 30, 8, 1.20),
}

# Synthetic hourly wage rates.
WAGE = {staff: 18 + (idx % 5) * 1.75 for idx, staff in enumerate(STAFF)}

# Deterministic synthetic multi-skill matrix.
SKILL_MATRIX: Dict[Tuple[str, str], int] = {}
for idx, staff in enumerate(STAFF):
    for s_idx, skill in enumerate(SKILLS):
        SKILL_MATRIX[(staff, skill)] = int(
            (idx + s_idx) % 3 == 0
            or (idx * 2 + s_idx) % 7 == 0
            or idx % 6 == s_idx
        )

# Ensure every employee has at least one skill and every skill has broad coverage.
for idx, staff in enumerate(STAFF):
    if sum(SKILL_MATRIX[(staff, skill)] for skill in SKILLS) == 0:
        SKILL_MATRIX[(staff, SKILLS[idx % len(SKILLS)])] = 1

# Deterministic day-shift-skill demand profile.
DEMAND: Dict[Tuple[int, str, str], int] = {}
for day in DAYS:
    weekday = (day - 1) % 7
    for shift_name in SHIFTS:
        for skill_idx, skill in enumerate(SKILLS):
            base = 1
            if shift_name == "DAY":
                base += 1
            if shift_name == "LATE" and skill in {"network", "applications"}:
                base += 1
            if shift_name == "NIGHT" and skill == "security":
                base += 1
            if weekday in {0, 1, 2, 3, 4} and shift_name in {"DAY", "LATE"}:
                base += 1 if skill_idx == weekday % len(SKILLS) else 0
            DEMAND[(day, shift_name, skill)] = base

# Planned individual unavailability, kept synthetic and deterministic.
UNAVAILABLE = {
    (STAFF[1], 3),
    (STAFF[4], 5),
    (STAFF[7], 8),
    (STAFF[10], 9),
    (STAFF[13], 12),
    (STAFF[16], 14),
}

MAX_CONSECUTIVE_DAYS = 5
MAX_ROLLING_7_DAY_HOURS = 48
MAX_TOTAL_DAYS = 10
TARGET_DAYS = 8
FAIRNESS_PENALTY = 12.0

# Shift transitions that do not provide enough rest before the next day.
FORBIDDEN_TRANSITIONS = {
    ("NIGHT", "EARLY"),
    ("NIGHT", "DAY"),
    ("LATE", "EARLY"),
}


def build_model() -> tuple[pulp.LpProblem, dict, dict, dict]:
    model = pulp.LpProblem("Hybrid_Staff_Rostering", pulp.LpMinimize)

    x = pulp.LpVariable.dicts(
        "assign",
        ((i, d, w) for i in STAFF for d in DAYS for w in SHIFTS),
        lowBound=0,
        upBound=1,
        cat="Binary",
    )

    y = pulp.LpVariable.dicts(
        "skill_cover",
        (
            (i, d, w, s)
            for i in STAFF
            for d in DAYS
            for w in SHIFTS
            for s in SKILLS
        ),
        lowBound=0,
        upBound=1,
        cat="Binary",
    )

    over_target = pulp.LpVariable.dicts("over_target", STAFF, lowBound=0)
    under_target = pulp.LpVariable.dicts("under_target", STAFF, lowBound=0)

    labor_cost = pulp.lpSum(
        WAGE[i]
        * SHIFTS[w].hours
        * SHIFTS[w].cost_multiplier
        * x[(i, d, w)]
        for i in STAFF
        for d in DAYS
        for w in SHIFTS
    )
    fairness_cost = FAIRNESS_PENALTY * pulp.lpSum(
        over_target[i] + under_target[i] for i in STAFF
    )
    model += labor_cost + fairness_cost

    # Demand coverage by skill, day, and shift.
    for d in DAYS:
        for w in SHIFTS:
            for s in SKILLS:
                model += (
                    pulp.lpSum(y[(i, d, w, s)] for i in STAFF)
                    >= DEMAND[(d, w, s)],
                    f"demand_{d}_{w}_{s}",
                )

    # A skill can only be supplied by an assigned, qualified employee.
    for i in STAFF:
        for d in DAYS:
            for w in SHIFTS:
                for s in SKILLS:
                    model += y[(i, d, w, s)] <= x[(i, d, w)]
                    model += y[(i, d, w, s)] <= SKILL_MATRIX[(i, s)]

                # One employee can cover at most one skill role per shift.
                model += (
                    pulp.lpSum(y[(i, d, w, s)] for s in SKILLS)
                    <= x[(i, d, w)]
                )

    # At most one shift per employee per day.
    for i in STAFF:
        for d in DAYS:
            model += pulp.lpSum(x[(i, d, w)] for w in SHIFTS) <= 1

    # Planned unavailability.
    for i, d in UNAVAILABLE:
        model += pulp.lpSum(x[(i, d, w)] for w in SHIFTS) == 0

    # Maximum consecutive workdays using rolling windows.
    window = MAX_CONSECUTIVE_DAYS + 1
    for i in STAFF:
        for start in range(1, len(DAYS) - window + 2):
            days_window = range(start, start + window)
            model += (
                pulp.lpSum(
                    x[(i, d, w)] for d in days_window for w in SHIFTS
                )
                <= MAX_CONSECUTIVE_DAYS
            )

    # Rolling seven-day hour limit.
    for i in STAFF:
        for start in range(1, len(DAYS) - 7 + 2):
            days_window = range(start, start + 7)
            model += (
                pulp.lpSum(
                    SHIFTS[w].hours * x[(i, d, w)]
                    for d in days_window
                    for w in SHIFTS
                )
                <= MAX_ROLLING_7_DAY_HOURS
            )

    # Rest rules between consecutive days.
    for i in STAFF:
        for d in DAYS[:-1]:
            for w1, w2 in FORBIDDEN_TRANSITIONS:
                model += x[(i, d, w1)] + x[(i, d + 1, w2)] <= 1

    # Total workload cap and fairness deviations from a target number of days.
    for i in STAFF:
        total_days = pulp.lpSum(x[(i, d, w)] for d in DAYS for w in SHIFTS)
        model += total_days <= MAX_TOTAL_DAYS
        model += total_days - TARGET_DAYS == over_target[i] - under_target[i]

    return model, x, y, {"over": over_target, "under": under_target}


def solve_model() -> tuple[pulp.LpProblem, dict, dict]:
    model, x, y, _ = build_model()
    solver = pulp.PULP_CBC_CMD(msg=False)
    model.solve(solver)

    status = pulp.LpStatus[model.status]
    if status != "Optimal":
        raise RuntimeError(f"Optimization did not reach an optimal solution: {status}")

    return model, x, y


def print_schedule(model: pulp.LpProblem, x: dict, y: dict) -> None:
    print(f"Status: {pulp.LpStatus[model.status]}")
    print(f"Objective value: {pulp.value(model.objective):.2f}")
    print()

    for d in DAYS:
        print(f"Day {d}")
        for w in SHIFTS:
            assignments: List[str] = []
            for i in STAFF:
                if pulp.value(x[(i, d, w)]) > 0.5:
                    covered = [
                        s
                        for s in SKILLS
                        if pulp.value(y[(i, d, w, s)]) > 0.5
                    ]
                    role = covered[0] if covered else "unassigned-role"
                    assignments.append(f"{i}:{role}")
            print(f"  {w:<5} -> {', '.join(assignments) if assignments else 'none'}")
        print()


if __name__ == "__main__":
    solved_model, assignment_vars, coverage_vars = solve_model()
    print_schedule(solved_model, assignment_vars, coverage_vars)
