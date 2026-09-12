from __future__ import annotations

import argparse
from pathlib import Path

import joblib
import pandas as pd
import yaml

from .data import load_workforce_data
from .optimization import estimate_marginal_gains, solve_reallocation


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--date", default=None, help="YYYY-MM-DD; defaults to latest date")
    parser.add_argument("--total-workers", type=int, default=None)
    parser.add_argument("--overtime-budget-blocks", type=int, default=None)
    args = parser.parse_args()

    project = Path(args.config).resolve().parent
    cfg = yaml.safe_load(Path(args.config).read_text())
    df = load_workforce_data(project / cfg["data"]["path"])
    selected_date = pd.Timestamp(args.date) if args.date else df["date"].max()
    case = df.loc[df["date"] == selected_date].copy().reset_index(drop=True)
    if case.empty:
        raise ValueError(f"No records found for {selected_date.date()}")

    model_path = project / "artifacts" / "productivity_model.joblib"
    if not model_path.exists():
        raise FileNotFoundError("Train the model first: python -m src.train --config config.yaml")
    model = joblib.load(model_path)

    opt = cfg["optimization"]
    marginals = estimate_marginal_gains(
        model,
        case,
        overtime_block_minutes=int(opt.get("overtime_block_minutes", 60)),
    )
    total_workers = args.total_workers or int(round(case["no_of_workers"].sum()))
    overtime_budget = (
        args.overtime_budget_blocks
        if args.overtime_budget_blocks is not None
        else int(opt.get("overtime_budget_blocks", 80))
    )
    solution = solve_reallocation(
        current_workers=case["no_of_workers"].to_numpy(float),
        worker_gain=marginals["worker_gain"].to_numpy(float),
        overtime_block_gain=marginals["overtime_block_gain"].to_numpy(float),
        baseline_productivity=marginals["baseline_productivity"].to_numpy(float),
        total_workers=total_workers,
        worker_flex=int(opt.get("worker_flex", 3)),
        overtime_budget_blocks=overtime_budget,
        max_overtime_blocks_per_team=int(opt.get("max_overtime_blocks_per_team", 20)),
        overtime_penalty=float(opt.get("overtime_penalty", 0.001)),
    )

    identifying = case[["date", "department", "team", "targeted_productivity", "smv", "wip"]].reset_index(drop=True)
    output = pd.concat([identifying, solution], axis=1)
    reports = project / "reports"
    reports.mkdir(exist_ok=True)
    output_path = reports / f"allocation_plan_{selected_date.date().isoformat()}.csv"
    output.to_csv(output_path, index=False)

    print(output.to_string(index=False))
    print(f"\nTotal workers: {int(output['optimized_workers'].sum())}")
    print(f"Overtime blocks used: {int(output['overtime_blocks'].sum())} / {overtime_budget}")
    print(f"Saved: {output_path}")


if __name__ == "__main__":
    main()
