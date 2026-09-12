# OR Workforce

A portfolio of applied operations-research and workforce-analytics projects covering staffing, scheduling, labor allocation, productivity, overtime, capacity planning, and data-driven decision support.

## Project map

| # | Domain | Project | Main objective | Status |
|---|---|---|---|---|
| 01 | Workforce Productivity & Allocation | [Garment Line Workforce Planning](productivity/garment-workforce-planning/) | Forecast team productivity and optimize worker/overtime allocation | Ready |

## Repository principles

- Separate prediction from optimization: predictive accuracy alone is not an OR result.
- Keep operational decisions, constraints, budgets, and trade-offs explicit.
- Avoid leakage from post-shift or post-decision variables in planning models.
- Respect time/team/shift boundaries when validating forecasting models.
- Treat observational relationships as decision-support signals, not causal effects.
- Include reproducible data validation, modeling, optimization, and tests.
