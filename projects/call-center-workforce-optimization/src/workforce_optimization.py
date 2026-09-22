from pathlib import Path

import pandas as pd
from pyomo.environ import (
    Binary,
    ConcreteModel,
    Constraint,
    NonNegativeReals,
    Objective,
    Param,
    RangeSet,
    SolverFactory,
    Var,
    minimize,
    value,
)


NUM_AGENTS = 12
NUM_HOURS = 24
TOTAL_SHORTAGE_PENALTY = 100_000.0
PEAK_SHORTAGE_PENALTY = 1_000.0

SHIFT_DEFINITIONS = {
    0: {"name": "Night", "start": 0, "duration": 6, "cost": 78.0},
    1: {"name": "Early Morning", "start": 3, "duration": 6, "cost": 82.0},
    2: {"name": "Morning", "start": 6, "duration": 6, "cost": 88.0},
    3: {"name": "Late Morning", "start": 9, "duration": 6, "cost": 92.0},
    4: {"name": "Afternoon", "start": 12, "duration": 6, "cost": 96.0},
    5: {"name": "Late Afternoon", "start": 15, "duration": 6, "cost": 101.0},
    6: {"name": "Evening", "start": 18, "duration": 6, "cost": 106.0},
    7: {"name": "Late Evening", "start": 21, "duration": 6, "cost": 112.0},
}

# Each agent has a distinct set of unavailable shifts. This introduces realistic
# scheduling restrictions without reproducing any external dataset.
UNAVAILABLE_SHIFTS = {
    0: {6, 7},
    1: {0, 7},
    2: {0, 1},
    3: {5, 6},
    4: {0, 1},
    5: {6, 7},
    6: {0},
    7: {7},
    8: {0, 1},
    9: {5, 6, 7},
    10: {0},
    11: {6, 7},
}


def covers_hour(start: int, duration: int, hour: int) -> int:
    """Return 1 when a circular 24-hour shift covers the given hour."""
    return int(any((start + offset) % NUM_HOURS == hour for offset in range(duration)))


def load_demand() -> dict[int, int]:
    """Load the synthetic hourly staffing requirements from the project data file."""
    data_path = Path(__file__).resolve().parents[1] / "data" / "hourly_demand.csv"
    demand_df = pd.read_csv(data_path)

    required_columns = {"hour", "required_agents"}
    if set(demand_df.columns) != required_columns:
        raise ValueError(f"Demand file must contain exactly these columns: {required_columns}")

    if len(demand_df) != NUM_HOURS or sorted(demand_df["hour"].tolist()) != list(range(NUM_HOURS)):
        raise ValueError("Demand file must contain one row for every hour from 0 through 23.")

    return dict(zip(demand_df["hour"], demand_df["required_agents"]))


def build_model(demand: dict[int, int]) -> ConcreteModel:
    """Build and return the mixed-integer workforce scheduling model."""
    model = ConcreteModel()

    model.I = RangeSet(0, NUM_AGENTS - 1)
    model.K = RangeSet(0, len(SHIFT_DEFINITIONS) - 1)
    model.T = RangeSet(0, NUM_HOURS - 1)

    shift_coverage = {
        (k, t): covers_hour(
            SHIFT_DEFINITIONS[k]["start"],
            SHIFT_DEFINITIONS[k]["duration"],
            t,
        )
        for k in SHIFT_DEFINITIONS
        for t in range(NUM_HOURS)
    }

    eligibility = {
        (i, k): int(k not in UNAVAILABLE_SHIFTS.get(i, set()))
        for i in range(NUM_AGENTS)
        for k in SHIFT_DEFINITIONS
    }

    model.coverage = Param(model.K, model.T, initialize=shift_coverage)
    model.demand = Param(model.T, initialize=demand)
    model.shift_cost = Param(
        model.K,
        initialize={k: SHIFT_DEFINITIONS[k]["cost"] for k in SHIFT_DEFINITIONS},
    )
    model.eligible = Param(model.I, model.K, initialize=eligibility)

    model.x = Var(model.I, model.K, domain=Binary)
    model.shortage = Var(model.T, domain=NonNegativeReals)
    model.peak_shortage = Var(domain=NonNegativeReals)

    def shortage_rule(m, t):
        scheduled = sum(m.coverage[k, t] * m.x[i, k] for i in m.I for k in m.K)
        return m.shortage[t] >= m.demand[t] - scheduled

    model.shortage_constraint = Constraint(model.T, rule=shortage_rule)

    def peak_shortage_rule(m, t):
        return m.shortage[t] <= m.peak_shortage

    model.peak_shortage_constraint = Constraint(model.T, rule=peak_shortage_rule)

    def one_shift_rule(m, i):
        return sum(m.x[i, k] for k in m.K) <= 1

    model.one_shift_per_agent = Constraint(model.I, rule=one_shift_rule)

    def eligibility_rule(m, i, k):
        return m.x[i, k] <= m.eligible[i, k]

    model.eligibility_constraint = Constraint(model.I, model.K, rule=eligibility_rule)

    total_shortage_term = TOTAL_SHORTAGE_PENALTY * sum(
        model.shortage[t] for t in model.T
    )
    peak_shortage_term = PEAK_SHORTAGE_PENALTY * model.peak_shortage
    labor_cost_term = sum(
        model.shift_cost[k] * model.x[i, k] for i in model.I for k in model.K
    )

    model.objective = Objective(
        expr=total_shortage_term + peak_shortage_term + labor_cost_term,
        sense=minimize,
    )

    return model


def solve_model(model: ConcreteModel) -> None:
    """Solve the model with HiGHS and print an interpretable operating plan."""
    solver = SolverFactory("appsi_highs")
    results = solver.solve(model)

    termination = str(results.solver.termination_condition)
    if termination.lower() not in {"optimal", "locallyoptimal", "globallyoptimal"}:
        raise RuntimeError(
            f"Optimization did not finish with an optimal solution: {termination}"
        )

    print(f"Solver termination: {termination}")
    print(f"Objective value: {value(model.objective):.2f}\n")

    print("Agent assignments")
    print("-----------------")
    for i in model.I:
        assigned_shift = next(
            (k for k in model.K if value(model.x[i, k]) > 0.5),
            None,
        )
        if assigned_shift is None:
            print(f"Agent {i + 1:02d}: Off")
        else:
            shift = SHIFT_DEFINITIONS[int(assigned_shift)]
            print(
                f"Agent {i + 1:02d}: Shift {int(assigned_shift)} - "
                f"{shift['name']} (start {shift['start']:02d}:00, "
                f"duration {shift['duration']}h)"
            )

    total_shortage = 0.0
    total_cost = 0.0

    print("\nHourly staffing")
    print("---------------")
    print("Hour | Demand | Scheduled | Shortage")
    for t in model.T:
        scheduled = sum(
            value(model.coverage[k, t]) * value(model.x[i, k])
            for i in model.I
            for k in model.K
        )
        shortage = value(model.shortage[t])
        total_shortage += shortage
        print(
            f"{int(t):02d}:00 | {int(value(model.demand[t])):6d} | "
            f"{int(round(scheduled)):9d} | {shortage:8.0f}"
        )

    for i in model.I:
        for k in model.K:
            total_cost += value(model.shift_cost[k]) * value(model.x[i, k])

    print(f"\nTotal shortage: {total_shortage:.0f} agent-hours")
    print(f"Peak hourly shortage: {value(model.peak_shortage):.0f} agents")
    print(f"Total staffing cost: {total_cost:.2f}")


def main() -> None:
    demand = load_demand()
    model = build_model(demand)
    solve_model(model)


if __name__ == "__main__":
    main()
