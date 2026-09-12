from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import ExtraTreesRegressor, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .data import prepare_feature_frame

TARGET = "actual_productivity"
CATEGORICAL = ["quarter", "department", "day", "team"]
NUMERIC = [
    "targeted_productivity",
    "smv",
    "wip",
    "over_time",
    "incentive",
    "no_of_style_change",
    "no_of_workers",
    "month",
    "day_of_month",
    "week_of_year",
]
FEATURES = CATEGORICAL + NUMERIC


def feature_matrix(df: pd.DataFrame) -> pd.DataFrame:
    return prepare_feature_frame(df)[FEATURES].copy()


def build_pipeline(name: str, random_state: int = 42) -> Pipeline:
    numeric = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
        ]
    )
    categorical = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ]
    )
    prep = ColumnTransformer(
        [("num", numeric, NUMERIC), ("cat", categorical, CATEGORICAL)],
        remainder="drop",
    )

    if name == "ridge":
        estimator = Ridge(alpha=2.0)
    elif name == "random_forest":
        estimator = RandomForestRegressor(
            n_estimators=300,
            min_samples_leaf=4,
            random_state=random_state,
            n_jobs=-1,
        )
    elif name == "extra_trees":
        estimator = ExtraTreesRegressor(
            n_estimators=300,
            min_samples_leaf=3,
            random_state=random_state,
            n_jobs=-1,
        )
    else:
        raise ValueError(f"Unknown model: {name}")
    return Pipeline([("preprocess", prep), ("model", estimator)])


def regression_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    return {
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "rmse": float(np.sqrt(mean_squared_error(y_true, y_pred))),
        "r2": float(r2_score(y_true, y_pred)),
    }


def grouped_oof_predictions(
    df: pd.DataFrame,
    model_name: str,
    n_splits: int = 5,
    random_state: int = 42,
) -> np.ndarray:
    groups = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
    unique_groups = groups.nunique()
    splits = min(n_splits, unique_groups)
    if splits < 2:
        raise ValueError("Need at least two date groups for cross-validation")

    X = feature_matrix(df)
    y = df[TARGET].to_numpy(float)
    predictions = np.full(len(df), np.nan, dtype=float)
    cv = GroupKFold(n_splits=splits)
    for train_idx, valid_idx in cv.split(X, y, groups=groups):
        model = build_pipeline(model_name, random_state=random_state)
        model.fit(X.iloc[train_idx], y[train_idx])
        predictions[valid_idx] = model.predict(X.iloc[valid_idx])
    if np.isnan(predictions).any():
        raise RuntimeError("OOF prediction vector is incomplete")
    return predictions


def compare_models(
    df: pd.DataFrame,
    candidates: list[str],
    n_splits: int = 5,
    random_state: int = 42,
) -> tuple[pd.DataFrame, dict[str, np.ndarray]]:
    rows: list[dict[str, float | str]] = []
    predictions: dict[str, np.ndarray] = {}
    y = df[TARGET].to_numpy(float)
    for name in candidates:
        pred = grouped_oof_predictions(df, name, n_splits=n_splits, random_state=random_state)
        predictions[name] = pred
        rows.append({"model": name, **regression_metrics(y, pred)})
    return pd.DataFrame(rows).sort_values("mae").reset_index(drop=True), predictions


def target_attainment_accuracy(df: pd.DataFrame, prediction: np.ndarray) -> float:
    target = df["targeted_productivity"].to_numpy(float)
    actual_hit = df[TARGET].to_numpy(float) >= target
    predicted_hit = np.asarray(prediction) >= target
    return float(np.mean(actual_hit == predicted_hit))
