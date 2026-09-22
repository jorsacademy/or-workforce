# Call Center Workforce Optimization

This project demonstrates how mixed-integer linear programming can be used to improve workforce allocation in a 24-hour customer support operation.

The scenario, data, optimization structure, and implementation in this repository are original and were created specifically for this project. The model is not a reproduction of any published scheduling example.

## Problem Overview

A customer support center operates continuously and must assign a limited number of agents to predefined shifts. Demand varies substantially across the day: overnight demand is low, morning demand increases, and the highest workload appears during the afternoon and early evening.

The optimization model determines which shift each agent should work while balancing three operational goals:

1. Minimize total staffing shortage.
2. Reduce the worst hourly shortage so that service gaps are not concentrated in a few periods.
3. Control total staffing cost.

The objective uses hierarchical penalty weights. Total shortage receives the largest penalty, peak hourly shortage receives a smaller penalty, and labor cost is used as the final tie-breaker among otherwise comparable schedules.

## Scenario

The synthetic scenario contains:

- 12 customer support agents
- 8 predefined 6-hour shifts
- 24 hourly demand periods
- Different labor costs by shift
- Agent-specific shift availability restrictions
- At most one shift per agent per day
- Circular shift coverage for shifts that cross midnight

## Mathematical Formulation

### Sets

- `I`: agents
- `K`: shifts
- `T`: hourly time periods

### Parameters

- `A[k,t]`: 1 if shift `k` covers hour `t`, otherwise 0
- `D[t]`: required number of agents at hour `t`
- `C[k]`: labor cost of shift `k`
- `E[i,k]`: 1 if agent `i` is eligible for shift `k`, otherwise 0

### Decision Variables

- `x[i,k]`: 1 if agent `i` is assigned to shift `k`, otherwise 0
- `y[t]`: staffing shortage at hour `t`
- `z`: maximum hourly shortage across the day

### Objective

The model minimizes a weighted combination of total shortage, peak shortage, and labor cost:

`Minimize W1 * sum(y[t]) + W2 * z + sum(C[k] * x[i,k])`

where `W1` is substantially larger than `W2`, and both shortage penalties dominate normal labor-cost differences.

### Constraints

Hourly shortage:

`y[t] >= D[t] - sum(A[k,t] * x[i,k])`

Peak shortage:

`y[t] <= z`

One shift per agent:

`sum(x[i,k]) <= 1`

Eligibility:

`x[i,k] <= E[i,k]`

Non-negativity:

`y[t] >= 0`

## Project Structure

```text
call-center-workforce-optimization/
├── README.md
├── LICENSE.md
├── requirements.txt
├── .gitignore
├── data/
│   └── hourly_demand.csv
└── src/
    └── workforce_optimization.py
```

## Installation

Python 3.10 or newer is recommended.

```bash
pip install -r requirements.txt
```

This project uses Pyomo with the HiGHS solver through `highspy`, so no separate GLPK installation is required.

## Run

```bash
python src/workforce_optimization.py
```

The script prints:

- Solver status
- Objective value
- Agent-to-shift assignments
- Hourly demand
- Hourly scheduled staffing
- Hourly shortage
- Total shortage
- Peak hourly shortage
- Total staffing cost

## Verification

The mathematical model was independently reproduced and solved with SciPy's MILP interface using the HiGHS backend to verify the formulation and solution structure.

For the current synthetic dataset, the verified optimum has:

- Total demand: 95 agent-hours
- Available scheduled capacity: 72 agent-hours
- Minimum total shortage: 23 agent-hours
- Peak hourly shortage: 2 agents
- Total staffing cost: 1140.00 cost units

The 23 agent-hour shortage is also a structural lower bound because 12 agents working one 6-hour shift each can provide at most 72 agent-hours, while total demand equals 95 agent-hours. The optimized schedule reaches this lower bound without concentrating the entire deficit in a few late-day periods.

Multiple agent-level assignments can be mathematically equivalent when agents have interchangeable eligibility. Therefore, exact agent IDs may differ between solver runs while the objective value and operational staffing profile remain optimal.

## Interpretation

A zero-shortage solution indicates that the available workforce and shift structure are sufficient to cover all modeled demand. If shortage remains after optimization, the result identifies when capacity is insufficient. Management can then evaluate alternatives such as hiring, overtime, revised shift definitions, cross-training, or demand-management measures.

In the current scenario, shortage cannot be eliminated with the existing workforce because total required capacity exceeds the maximum available agent-hours. The optimization model therefore distributes the unavoidable deficit while respecting shift eligibility and controlling cost.

## Data

All data in this repository are synthetic and intended solely for educational, academic, and non-commercial research use.

## License

This repository is distributed under a custom non-commercial license. Commercial use is prohibited without prior written permission. See `LICENSE.md` for details.
