import numpy as np
import pandas as pd

from src.modeling import grouped_oof_predictions, regression_metrics


def make_data() -> pd.DataFrame:
    rows = []
    for i, d in enumerate(pd.date_range("2025-01-01", periods=12)):
        for team in (1, 2):
            workers = 35 + team + (i % 3)
            rows.append(
                {
                    "date": d,
                    "quarter": "Quarter1",
                    "department": "sewing" if team == 1 else "finishing",
                    "day": d.day_name(),
                    "team": team,
                    "targeted_productivity": 0.75,
                    "smv": 18.0 + team,
                    "wip": 500.0 if team == 1 else np.nan,
                    "over_time": 600 + 30 * i,
                    "incentive": 10,
                    "idle_time": 0,
                    "idle_men": 0,
                    "no_of_style_change": i % 2,
                    "no_of_workers": workers,
                    "actual_productivity": 0.55 + 0.004 * workers + 0.001 * i,
                }
            )
    return pd.DataFrame(rows)


def test_grouped_oof_is_complete():
    df = make_data()
    pred = grouped_oof_predictions(df, "ridge", n_splits=4)
    assert pred.shape == (len(df),)
    assert np.isfinite(pred).all()
    metrics = regression_metrics(df["actual_productivity"].to_numpy(), pred)
    assert metrics["mae"] >= 0
