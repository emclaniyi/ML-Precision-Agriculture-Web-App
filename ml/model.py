"""Compare, train, and save crop recommendation pipelines.

Run from the repository root with::

    python ml/model.py

The model is selected with stratified cross-validation. Macro-F1 and balanced
accuracy are reported alongside ordinary accuracy so the minority crop classes
are not hidden by the larger classes.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import ExtraTreesClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import make_scorer, f1_score
from sklearn.model_selection import StratifiedKFold, cross_validate
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.svm import SVC, LinearSVC


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = BASE_DIR / "data" / "final_data.csv"
MODEL_PATH = BASE_DIR / "models" / "crop_recommender.joblib"
REPORT_PATH = BASE_DIR / "models" / "model_comparison.csv"
METADATA_PATH = BASE_DIR / "models" / "model_metadata.json"

NUMERIC_COLUMNS = [
    "pH",
    "N",
    "P",
    "K",
    "OC",
    "Particles",
    "Water_holding_content",
]
CATEGORICAL_COLUMNS = ["Soil_type"]
FEATURE_COLUMNS = NUMERIC_COLUMNS + CATEGORICAL_COLUMNS
TARGET_COLUMN = "crop_type"


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_training_data(data: pd.DataFrame) -> None:
    required = set(FEATURE_COLUMNS + [TARGET_COLUMN])
    missing = required - set(data.columns)
    if missing:
        raise ValueError(f"Training data is missing columns: {sorted(missing)}")

    required_columns = FEATURE_COLUMNS + [TARGET_COLUMN]
    if data[required_columns].isna().any().any():
        missing_values = data[required_columns].isna().sum()
        raise ValueError(
            "Training data contains missing values: "
            f"{missing_values[missing_values > 0].to_dict()}"
        )

    numeric = data[NUMERIC_COLUMNS].apply(pd.to_numeric, errors="coerce")
    if numeric.isna().any().any():
        raise ValueError("Training data contains non-numeric soil measurements")
    if not np.isfinite(numeric.to_numpy()).all():
        raise ValueError("Training data contains non-finite soil measurements")

    if data[TARGET_COLUMN].nunique() < 2:
        raise ValueError("Training data must contain at least two crop classes")


def build_metadata(data: pd.DataFrame, comparison: pd.DataFrame) -> dict:
    best = comparison.iloc[0]
    class_by_soil = pd.crosstab(data[TARGET_COLUMN], data["Soil_type"])
    crop_soil_pure_rows = int((class_by_soil.gt(0).sum(axis=1) == 1).sum())
    class_count = int(class_by_soil.shape[0])

    return {
        "dataset": {
            "path": str(DATA_PATH.relative_to(BASE_DIR)),
            "sha256": file_sha256(DATA_PATH),
            "source": "unknown_legacy_dataset",
            "provenance_verified": False,
            "rows": int(len(data)),
            "features": FEATURE_COLUMNS,
            "target": TARGET_COLUMN,
            "classes": sorted(data[TARGET_COLUMN].astype(str).unique().tolist()),
        },
        "validation": {
            "method": "5-fold stratified cross-validation",
            "random_state": 50,
            "selection_order": [
                "macro_f1_mean",
                "balanced_accuracy_mean",
                "accuracy_mean",
            ],
        },
        "selected_model": {
            "name": str(best["model"]),
            "accuracy_mean": float(best["accuracy_mean"]),
            "balanced_accuracy_mean": float(best["balanced_accuracy_mean"]),
            "macro_f1_mean": float(best["macro_f1_mean"]),
        },
        "warnings": [
            "Dataset provenance, units, and license are unverified.",
            "No location, season, yield, or farm identifier is available.",
            f"{crop_soil_pure_rows} of {class_count} crop classes occur in only one soil type.",
            "Metrics should not be interpreted as field performance until the dataset is replaced or validated.",
        ],
    }


def load_training_data() -> tuple[pd.DataFrame, pd.Series]:
    data = pd.read_csv(DATA_PATH)
    validate_training_data(data)

    features = data[FEATURE_COLUMNS].copy()
    features[NUMERIC_COLUMNS] = features[NUMERIC_COLUMNS].apply(pd.to_numeric)
    features["Soil_type"] = features["Soil_type"].astype(str)
    target = data[TARGET_COLUMN].astype(str)
    return features, target


def build_preprocessor() -> ColumnTransformer:
    return ColumnTransformer(
        transformers=[
            ("numeric", StandardScaler(), NUMERIC_COLUMNS),
            ("soil", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_COLUMNS),
        ]
    )


def build_pipeline(classifier) -> Pipeline:
    return Pipeline(
        steps=[
            ("preprocessor", build_preprocessor()),
            ("classifier", classifier),
        ]
    )


def candidate_models() -> dict[str, Pipeline]:
    return {
        "svc_rbf": build_pipeline(SVC(C=2.0, kernel="rbf", random_state=50)),
        "svc_rbf_balanced": build_pipeline(
            SVC(C=2.0, kernel="rbf", class_weight="balanced", random_state=50)
        ),
        "linear_svc_balanced": build_pipeline(
            LinearSVC(C=1.0, class_weight="balanced", max_iter=10000, random_state=50)
        ),
        "logistic_regression_balanced": build_pipeline(
            LogisticRegression(
                C=1.0,
                class_weight="balanced",
                max_iter=5000,
                random_state=50,
            )
        ),
        "random_forest_balanced": build_pipeline(
            RandomForestClassifier(
                n_estimators=400,
                class_weight="balanced_subsample",
                random_state=50,
                n_jobs=-1,
            )
        ),
        "extra_trees_balanced": build_pipeline(
            ExtraTreesClassifier(
                n_estimators=400,
                class_weight="balanced",
                random_state=50,
                n_jobs=-1,
            )
        ),
    }


def evaluate_models(features: pd.DataFrame, target: pd.Series) -> pd.DataFrame:
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=50)
    scoring = {
        "accuracy": "accuracy",
        "balanced_accuracy": "balanced_accuracy",
        "macro_f1": make_scorer(f1_score, average="macro"),
    }
    rows = []
    for name, pipeline in candidate_models().items():
        scores = cross_validate(
            pipeline,
            features,
            target,
            cv=cv,
            scoring=scoring,
            n_jobs=1,
            error_score="raise",
        )
        rows.append(
            {
                "model": name,
                "accuracy_mean": scores["test_accuracy"].mean(),
                "accuracy_std": scores["test_accuracy"].std(),
                "balanced_accuracy_mean": scores["test_balanced_accuracy"].mean(),
                "macro_f1_mean": scores["test_macro_f1"].mean(),
            }
        )

    return pd.DataFrame(rows).sort_values(
        ["macro_f1_mean", "balanced_accuracy_mean", "accuracy_mean"],
        ascending=False,
    )


def train() -> tuple[Pipeline, pd.DataFrame]:
    features, target = load_training_data()
    comparison = evaluate_models(features, target)
    best_name = comparison.iloc[0]["model"]
    best_pipeline = candidate_models()[best_name]
    best_pipeline.fit(features, target)
    return best_pipeline, comparison


if __name__ == "__main__":
    training_data = pd.read_csv(DATA_PATH)
    trained_model, comparison = train()
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(trained_model, MODEL_PATH)
    comparison.to_csv(REPORT_PATH, index=False)
    METADATA_PATH.write_text(
        json.dumps(build_metadata(training_data, comparison), indent=2) + "\n",
        encoding="utf-8",
    )

    print(comparison.to_string(index=False, float_format=lambda value: f"{value:.4f}"))
    print(f"\nSelected: {comparison.iloc[0]['model']}")
    print(f"Saved model: {MODEL_PATH}")
    print(f"Saved comparison: {REPORT_PATH}")
    print(f"Saved metadata: {METADATA_PATH}")
