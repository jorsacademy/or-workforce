# Garment Line Workforce Planning

A workforce-analytics and operations-research project for labor-intensive garment production. The project uses historical line/team productivity records to forecast near-term performance and then adds an explicit optimization layer for worker reallocation and overtime planning.

## Problem

The data contains daily/team production context including department, team, targeted productivity, standard minute value (SMV), work in progress (WIP), overtime, incentive, style changes, number of workers, interruption variables, and actual productivity.

The useful OR question is not only **"what will productivity be?"** but also:

> Given a fixed headcount and a limited overtime budget, how should workers and overtime be allocated across active teams to improve expected productivity?

## Modeling protocol

The pre-shift forecasting model deliberately excludes `idle_time` and `idle_men` because they are realized interruption outcomes and would leak post-shift information into a planning model. The target is `actual_productivity`.

Candidate regressors are compared on development dates using date-grouped cross-validation. The most recent dates are reserved as a strict temporal holdout before the final model is refit on all available history.

Reported metrics include MAE, RMSE, R², and target-attainment accuracy derived from whether predicted/actual productivity meets `targeted_productivity`.

## Optimization layer

The selected forecasting model is used as a local response surrogate. For every active team, the planner estimates finite-difference productivity gains for:

- one additional worker;
- one additional overtime block.

A mixed-integer linear program then reallocates integer workers and overtime blocks subject to:

- fixed total available headcount;
- minimum/maximum staffing bounds around the current line staffing;
- a global overtime-block budget;
- per-team overtime limits.

The objective maximizes the surrogate improvement net of an overtime penalty.

This is intentionally framed as **decision support, not causal optimization**. Historical associations between staffing/overtime and productivity can be confounded by workload, urgency, product mix, and management decisions. A plant deployment should validate intervention effects experimentally or with stronger causal designs before treating the optimizer as prescriptive policy.

## Data

The repository includes the compact raw CSV after the hydration workflow completes. The file contains 1,197 observations. `wip` has missing values and is imputed inside the modeling pipeline rather than filled globally.

```text
data/raw/garments_worker_productivity.csv
```

The license/attribution notice is kept under `data/ATTRIBUTION.md`.

## Setup

```bash
cd productivity/garment-workforce-planning
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Windows:

```bash
.venv\Scripts\activate
pip install -r requirements.txt
```

## Validate data

```bash
python scripts/validate_data.py
```

## Train forecasting model

```bash
python -m src.train --config config.yaml
```

Outputs:

```text
reports/model_comparison.csv
reports/temporal_holdout_predictions.csv
reports/metrics.json
artifacts/productivity_model.joblib
```

## Optimize one production day

By default the planner uses the latest date in the historical file as a reproducible planning case:

```bash
python -m src.plan --config config.yaml
```

Or select a date explicitly:

```bash
python -m src.plan --config config.yaml --date 2015-03-11
```

The resulting table contains current vs optimized workers, overtime blocks, baseline productivity, local marginal gains, and the surrogate productivity after reallocation.

## Repository layout

```text
garment-workforce-planning/
├── README.md
├── config.yaml
├── requirements.txt
├── Makefile
├── data/
│   ├── ATTRIBUTION.md
│   ├── README.md
│   └── raw/
├── notebooks/
│   └── 01_exploration.ipynb
├── scripts/
│   ├── download_data.py
│   └── validate_data.py
├── src/
│   ├── __init__.py
│   ├── data.py
│   ├── modeling.py
│   ├── optimization.py
│   ├── plan.py
│   └── train.py
├── reports/
│   └── README.md
└── tests/
    ├── test_data.py
    ├── test_modeling.py
    └── test_optimization.py
```
