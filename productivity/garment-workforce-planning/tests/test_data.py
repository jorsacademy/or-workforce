from pathlib import Path

import pandas as pd

from src.data import load_workforce_data, temporal_split


def sample_frame() -> pd.DataFrame:
    rows = []
    for d in pd.date_range("2025-01-01", periods=10):
        rows.append(
            {
                "date": d.strftime("%m/%d/%Y"),
                "quarter": "Quarter1",
                "department": " sweing ",
                "day": "wednesday",
                "team": 1,
                "targeted_productivity": 0.8,
                "smv": 20.0,
                "wip": None,
                "over_time": 600,
                "incentive": 20,
                "idle_time": 0,
                "idle_men": 0,
                "no_of_style_change": 0,
                "no_of_workers": 40,
                "actual_productivity": 0.75,
            }
        )
    return pd.DataFrame(rows)


def test_loader_normalizes_department(tmp_path: Path):
    path = tmp_path / "sample.csv"
    sample_frame().to_csv(path, index=False)
    df = load_workforce_data(path)
    assert df.loc[0, "department"] == "sewing"
    assert pd.api.types.is_datetime64_any_dtype(df["date"])


def test_temporal_split_has_no_date_overlap(tmp_path: Path):
    path = tmp_path / "sample.csv"
    sample_frame().to_csv(path, index=False)
    df = load_workforce_data(path)
    dev, holdout = temporal_split(df, 0.2)
    assert set(dev["date"]).isdisjoint(set(holdout["date"]))
    assert holdout["date"].min() > dev["date"].max()
