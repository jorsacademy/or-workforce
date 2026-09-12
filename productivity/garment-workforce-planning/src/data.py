from __future__ import annotations

from pathlib import Path

import pandas as pd

REQUIRED_COLUMNS = {
    "date",
    "quarter",
    "department",
    "day",
    "team",
    "targeted_productivity",
    "smv",
    "wip",
    "over_time",
    "incentive",
    "idle_time",
    "idle_men",
    "no_of_style_change",
    "no_of_workers",
    "actual_productivity",
}

NUMERIC_COLUMNS = [
    "team",
    "targeted_productivity",
    "smv",
    "wip",
    "over_time",
    "incentive",
    "idle_time",
    "idle_men",
    "no_of_style_change",
    "no_of_workers",
    "actual_productivity",
]


def load_workforce_data(path: str | Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df.columns = [str(c).strip().lower() for c in df.columns]
    missing = REQUIRED_COLUMNS.difference(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    out = df.copy()
    out["department"] = (
        out["department"].astype(str).str.strip().str.lower().replace({"sweing": "sewing"})
    )
    out["quarter"] = out["quarter"].astype(str).str.strip()
    out["day"] = out["day"].astype(str).str.strip().str.title()
    out["date"] = pd.to_datetime(out["date"], errors="coerce")

    for col in NUMERIC_COLUMNS:
        out[col] = pd.to_numeric(out[col], errors="coerce")

    if out["date"].isna().any():
        bad = int(out["date"].isna().sum())
        raise ValueError(f"Could not parse {bad} date values")
    if out["actual_productivity"].isna().any():
        raise ValueError("Target contains missing/non-numeric values")

    return out.sort_values(["date", "department", "team"]).reset_index(drop=True)


def prepare_feature_frame(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    date = pd.to_datetime(out["date"])
    out["month"] = date.dt.month
    out["day_of_month"] = date.dt.day
    out["week_of_year"] = date.dt.isocalendar().week.astype(int)
    return out


def temporal_split(df: pd.DataFrame, holdout_fraction: float = 0.20) -> tuple[pd.DataFrame, pd.DataFrame]:
    dates = pd.Index(sorted(pd.to_datetime(df["date"]).unique()))
    if len(dates) < 5:
        raise ValueError("At least five unique dates are required for temporal evaluation")
    n_holdout = max(1, int(round(len(dates) * holdout_fraction)))
    cutoff_dates = set(dates[-n_holdout:])
    holdout_mask = pd.to_datetime(df["date"]).isin(cutoff_dates)
    dev = df.loc[~holdout_mask].copy()
    holdout = df.loc[holdout_mask].copy()
    if dev.empty or holdout.empty:
        raise ValueError("Temporal split produced an empty partition")
    return dev, holdout
