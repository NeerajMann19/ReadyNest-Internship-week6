"""
Analytics Studio — Prediction Engine Module

Computes machine learning baseline prediction models (LinearRegression for regression,
LogisticRegression for classification) based on deterministic schema rules, missing value handling,
train/test split, scaling, label encoding, and 4-decimal metric evaluation.
"""

from typing import Any
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
)
from models import Dataset, Prediction


def sanitize_float(val: Any) -> float | None:
    """Converts value to float, handling NaN and Infinity safely."""
    if val is None or pd.isna(val):
        return None
    try:
        fval = float(val)
        if np.isnan(fval) or np.isinf(fval):
            return None
        return round(fval, 4)
    except (ValueError, TypeError):
        return None


def is_id_like_column(col_name: str) -> bool:
    """Checks if a column name follows common ID-like naming heuristics."""
    name_lower = col_name.strip().lower()
    if name_lower in ("id", "uuid", "_id", "index"):
        return True
    if name_lower.endswith("_id") or name_lower.startswith("id_"):
        return True
    return False


def compute_prediction(dataset_obj: Dataset, df: pd.DataFrame, target_column: str) -> Prediction:
    """
    Computes baseline ML prediction (LinearRegression or LogisticRegression) for the given target_column.
    Strictly enforces task type rules, numeric feature selection, missing value drops, min 20 rows check,
    constant target check, 80/20 train/test split, scaler, label encoder, and 4-decimal metrics.
    """
    # 1. Target Column Existence Validation
    schema_col_names = [col.name for col in dataset_obj.column_schema]
    if target_column not in df.columns or target_column not in schema_col_names:
        return Prediction(
            available=False,
            reason="Target column does not exist.",
            target_column=target_column,
            problem_type="unknown",
            model_type="none",
            metrics={},
            stratified=None,
            label_mapping=None,
            features_used=[],
            row_counts={},
            predictions=[],
        )

    # 2. Feature Selection (Numeric columns only, excluding target, ID-like, and datetime columns)
    feature_cols: list[str] = []
    for col in dataset_obj.column_schema:
        if col.name in df.columns and col.name != target_column:
            if col.data_type == "numeric" and not is_id_like_column(col.name):
                feature_cols.append(col.name)

    if not feature_cols:
        return Prediction(
            available=False,
            reason="No usable numeric feature columns available for prediction.",
            target_column=target_column,
            problem_type="unknown",
            model_type="none",
            metrics={},
            stratified=None,
            label_mapping=None,
            features_used=[],
            row_counts={},
            predictions=[],
        )

    # 3. Missing Value Handling Before Training
    clean_df = df.dropna(subset=[target_column] + feature_cols).copy()
    total_cleaned_rows = len(clean_df)

    # 4. Minimum Dataset Size Check
    if total_cleaned_rows < 20:
        return Prediction(
            available=False,
            reason="Dataset must contain at least 20 rows.",
            target_column=target_column,
            problem_type="unknown",
            model_type="none",
            metrics={},
            stratified=None,
            label_mapping=None,
            features_used=feature_cols,
            row_counts={"total_cleaned": total_cleaned_rows},
            predictions=[],
        )

    # 5. Constant Target Column Check
    if clean_df[target_column].nunique() < 2:
        return Prediction(
            available=False,
            reason="Target column must contain at least two distinct values.",
            target_column=target_column,
            problem_type="unknown",
            model_type="none",
            metrics={},
            stratified=None,
            label_mapping=None,
            features_used=feature_cols,
            row_counts={"total_cleaned": total_cleaned_rows},
            predictions=[],
        )

    # 6. Task Type Detection Rule
    target_schema_type = "numeric"
    for col in dataset_obj.column_schema:
        if col.name == target_column:
            target_schema_type = col.data_type
            break

    target_nunique = int(clean_df[target_column].nunique())
    if target_schema_type == "numeric" and target_nunique > 10:
        problem_type = "regression"
        model_type = "LinearRegression"
    else:
        problem_type = "classification"
        model_type = "LogisticRegression"

    # 7. Prepare Target Vector (y) and Label Encoding if Classification
    label_encoder: LabelEncoder | None = None
    label_mapping: dict[str, Any] | None = None

    if problem_type == "classification":
        label_encoder = LabelEncoder()
        # Fit LabelEncoder on FULL cleaned target column before split
        y_raw = clean_df[target_column].astype(str)
        y = label_encoder.fit_transform(y_raw)
        # Store label mapping for response (e.g. {"0": "Fail", "1": "Pass"})
        label_mapping = {str(idx): str(cls_val) for idx, cls_val in enumerate(label_encoder.classes_)}
    else:
        y = pd.to_numeric(clean_df[target_column], errors="coerce").values

    X = clean_df[feature_cols].apply(pd.to_numeric, errors="coerce").values

    # 8. Train / Test Split & Stratification
    stratified: bool | None = None
    if problem_type == "classification":
        # Check minimum class count in y
        class_counts = pd.Series(y).value_counts()
        min_class_count = int(class_counts.min()) if len(class_counts) > 0 else 0
        if min_class_count >= 2:
            try:
                X_train, X_test, y_train, y_test = train_test_split(
                    X, y, test_size=0.2, shuffle=True, random_state=42, stratify=y
                )
                stratified = True
            except ValueError:
                X_train, X_test, y_train, y_test = train_test_split(
                    X, y, test_size=0.2, shuffle=True, random_state=42, stratify=None
                )
                stratified = False
        else:
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, shuffle=True, random_state=42, stratify=None
            )
            stratified = False
    else:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, shuffle=True, random_state=42
        )
        stratified = None

    train_count = len(X_train)
    test_count = len(X_test)

    # 9. Feature Scaling
    if problem_type == "classification":
        scaler = StandardScaler()
        # Fit ONLY on training features to prevent data leakage
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
    else:
        X_train_scaled = X_train
        X_test_scaled = X_test

    # 10. Model Training and Evaluation Metrics
    metrics: dict[str, float] = {}
    sample_predictions: list[dict[str, Any]] = []

    if problem_type == "regression":
        reg_model = LinearRegression()
        reg_model.fit(X_train_scaled, y_train)
        y_pred = reg_model.predict(X_test_scaled)

        mae_val = round(float(mean_absolute_error(y_test, y_pred)), 4)
        mse_val = float(mean_squared_error(y_test, y_pred))
        rmse_val = round(float(np.sqrt(mse_val)), 4)
        r2_val = round(float(r2_score(y_test, y_pred)), 4)

        metrics = {
            "mae": mae_val,
            "rmse": rmse_val,
            "r2": r2_val,
        }

        # Format up to first 10 sample predictions
        for i in range(min(10, len(y_test))):
            act = sanitize_float(y_test[i])
            prd = sanitize_float(y_pred[i])
            sample_predictions.append({"actual": act, "predicted": prd})

    else:
        clf_model = LogisticRegression(max_iter=1000, random_state=42)
        clf_model.fit(X_train_scaled, y_train)
        y_pred = clf_model.predict(X_test_scaled)

        acc_val = round(float(accuracy_score(y_test, y_pred)), 4)
        prec_val = round(float(precision_score(y_test, y_pred, average="weighted", zero_division=0)), 4)
        rec_val = round(float(recall_score(y_test, y_pred, average="weighted", zero_division=0)), 4)
        f1_val = round(float(f1_score(y_test, y_pred, average="weighted", zero_division=0)), 4)

        metrics = {
            "accuracy": acc_val,
            "precision": prec_val,
            "recall": rec_val,
            "f1": f1_val,
        }

        # Format up to first 10 sample predictions (mapped back to original target labels)
        for i in range(min(10, len(y_test))):
            if label_encoder is not None:
                act_label = str(label_encoder.inverse_transform([y_test[i]])[0])
                prd_label = str(label_encoder.inverse_transform([y_pred[i]])[0])
            else:
                act_label = str(y_test[i])
                prd_label = str(y_pred[i])
            sample_predictions.append({"actual": act_label, "predicted": prd_label})

    row_counts = {
        "total_cleaned": total_cleaned_rows,
        "train_count": train_count,
        "test_count": test_count,
    }

    return Prediction(
        available=True,
        reason=None,
        target_column=target_column,
        problem_type=problem_type,
        model_type=model_type,
        metrics=metrics,
        stratified=stratified,
        label_mapping=label_mapping,
        features_used=feature_cols,
        row_counts=row_counts,
        predictions=sample_predictions,
    )

