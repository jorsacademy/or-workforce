# Workforce Optimization and Analytics

<!-- portfolio-umbrella:start -->
## Portfolio role

This repository is the primary umbrella repository for this Jors Academy research area. Related projects have been consolidated under `projects/` so the methods, implementations, experiments, and case studies can be maintained and explored from one place.

### Included projects

- [`call-center-workforce-optimization`](projects/call-center-workforce-optimization/)
- [`hybrid-personnel-scheduling-staff-rostering`](projects/hybrid-personnel-scheduling-staff-rostering/)
- [`optimal-conference-meeting-scheduling-cp-sat`](projects/optimal-conference-meeting-scheduling-cp-sat/)

Each consolidated project keeps its own files and a `SOURCE_REPOSITORY.md` provenance record. The snapshot preserves the source repository's default-branch files at consolidation time; repository-level history and metadata remain separate from the snapshot.
<!-- portfolio-umbrella:end -->

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
