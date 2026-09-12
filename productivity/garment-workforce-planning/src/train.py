from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import pandas as pd
import yaml

from .data import load_workforce_data, temporal_split
from .modeling import (
    TARGET,
    build_pipeline,
    compare_models,
    feature_matrix,
    regression_metrics,
    target_attainment_accuracy,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config.yaml")
    args = parser.parse_args()

    project = Path(args.config).resolve().parent
    cfg = yaml.safe_load(Path(args.config).read_text())
    data_path = project / cfg["data"]["path"]
    df = load_workforce_data(data_path)

    model_cfg = cfg["model"]
    dev, holdout = temporal_split(df, float(model_cfg.get("temporal_holdout_fraction", 0.20)))
    comparison, _ = compare_models(
        dev,
        list(model_cfg["candidates"]),
        n_splits=int(model_cfg.get("cv_splits", 5)),
        random_state=int(model_cfg.get("random_state", 42)),
    )
    best_name = str(comparison.iloc[0]["model"])

    evaluation_model = build_pipeline(best_name, int(model_cfg.get("random_state", 42)))
    evaluation_model.fit(feature_matrix(dev), dev[TARGET])
    holdout_prediction = evaluation_model.predict(feature_matrix(holdout))
    metrics = regression_metrics(holdout[TARGET].to_numpy(float), holdout_prediction)
    metrics["target_attainment_accuracy"] = target_attainment_accuracy(holdout, holdout_prediction)
    metrics["selected_model"] = best_name
    metrics["development_rows"] = int(len(dev))
    metrics["holdout_rows"] = int(len(holdout))
    metrics["holdout_start"] = holdout["date"].min().date().isoformat()
    metrics["holdout_end"] = holdout["date"].max().date().isoformat()

    reports = project / "reports"
    artifacts = project / "artifacts"
    reports.mkdir(exist_ok=True)
    artifacts.mkdir(exist_ok=True)
    comparison.to_csv(reports / "model_comparison.csv", index=False)

    pred_table = holdout[["date", "department", "team", "targeted_productivity", TARGET]].copy()
    pred_table["predicted_productivity"] = holdout_prediction
    pred_table.to_csv(reports / "temporal_holdout_predictions.csv", index=False)
    (reports / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")

    final_model = build_pipeline(best_name, int(model_cfg.get("random_state", 42)))
    final_model.fit(feature_matrix(df), df[TARGET])
    joblib.dump(final_model, artifacts / "productivity_model.joblib")
    (artifacts / "model_metadata.json").write_text(
        json.dumps({"selected_model": best_name, "rows": len(df), "metrics": metrics}, indent=2) + "\n"
    )

    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
