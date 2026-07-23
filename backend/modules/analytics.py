"""
Analytics Studio — Analytics Engine Module

Computes summary statistics (numeric/categorical), pairwise Pearson correlation matrix,
missing value summaries, and IQR-based outlier detection from dataset.
"""

import math
from typing import Any
import pandas as pd
from models import Analytics, Dataset


def sanitize_float(val: Any) -> float | None:
    """Sanitizes float values, converting NaN and Infinity to None."""
    if val is None or pd.isna(val):
        return None
    try:
        fval = float(val)
        if math.isnan(fval) or math.isinf(fval):
            return None
        return fval
    except (ValueError, TypeError):
        return None


def round_val(val: float | None, precision: int = 2) -> float | None:
    """Rounds sanitized float value to given precision."""
    sval = sanitize_float(val)
    if sval is None:
        return None
    return round(sval, precision)


def compute_analytics(dataset_obj: Dataset, df: pd.DataFrame) -> Analytics:
    """
    Computes summary statistics, correlation matrix, missing value summary,
    and IQR outlier detection for the provided dataset.
    """
    # 1. Identify numeric and categorical columns locked strictly to Dataset.column_schema data_type
    numeric_cols = [
        col.name for col in dataset_obj.column_schema if col.data_type == "numeric" and col.name in df.columns
    ]
    categorical_cols = [
        col.name for col in dataset_obj.column_schema if col.data_type in ("string", "categorical") and col.name in df.columns
    ]

    # Preserve original Dataset column order
    all_col_names = [col.name for col in dataset_obj.column_schema if col.name in df.columns]

    # --- A. Numeric Statistics Summary ---
    numeric_summary: dict[str, Any] = {}
    for col in numeric_cols:
        series = pd.to_numeric(df[col], errors="coerce").dropna()
        n = len(series)
        if n == 0:
            numeric_summary[col] = {
                "mean": None, "median": None, "min": None, "max": None,
                "std_dev": None, "variance": None, "q1": None, "q3": None
            }
        else:
            mean_val = round_val(series.mean(), 2)
            median_val = round_val(series.median(), 2)
            min_val = round_val(series.min(), 2)
            max_val = round_val(series.max(), 2)
            q1_val = round_val(series.quantile(0.25, interpolation="linear"), 2)
            q3_val = round_val(series.quantile(0.75, interpolation="linear"), 2)

            if n > 1:
                var_raw = series.var(ddof=1)
                std_raw = series.std(ddof=1)
                var_val = round_val(var_raw, 2)
                std_val = round_val(std_raw, 2)
            else:
                var_val = None
                std_val = None

            numeric_summary[col] = {
                "mean": mean_val,
                "median": median_val,
                "min": min_val,
                "max": max_val,
                "std_dev": std_val,
                "variance": var_val,
                "q1": q1_val,
                "q3": q3_val,
            }

    # --- B. Categorical Statistics Summary ---
    categorical_summary: dict[str, Any] = {}
    for col in categorical_cols:
        series = df[col].astype(str).dropna()
        unique_count = int(series.nunique())
        # Frequency descending, value alphabetically ascending for deterministic tie-breaking
        counts = series.value_counts().reset_index()
        counts.columns = ["value", "count"]
        counts_sorted = counts.sort_values(by=["count", "value"], ascending=[False, True]).head(5)
        top_values = [
            {"value": str(row["value"]), "count": int(row["count"])}
            for _, row in counts_sorted.iterrows()
        ]
        categorical_summary[col] = {
            "unique_count": unique_count,
            "top_values": top_values,
        }

    # --- C. Missing Value Summary ---
    total_rows = len(df)
    missing_summary: list[dict[str, Any]] = []
    for col_name in all_col_names:
        missing_count = int(df[col_name].isna().sum())
        missing_pct = round_val((missing_count / total_rows * 100.0) if total_rows > 0 else 0.0, 1)
        missing_summary.append({
            "column": col_name,
            "missing_count": missing_count,
            "missing_percentage": missing_pct,
        })

    # --- D. Correlation Matrix ---
    if len(numeric_cols) < 2:
        correlations_payload = {
            "available": False,
            "reason": "At least two numeric columns are required.",
            "columns": numeric_cols,
            "matrix": {},
        }
    else:
        # Pairwise Pearson correlation (missing values excluded pairwise)
        corr_df = df[numeric_cols].corr(method="pearson")
        matrix: dict[str, dict[str, float | None]] = {}
        for c1 in numeric_cols:
            matrix[c1] = {}
            for c2 in numeric_cols:
                if c1 == c2:
                    # Diagonal policy: strictly fixed at 1.000
                    matrix[c1][c2] = 1.000
                else:
                    raw_corr = corr_df.loc[c1, c2] if (c1 in corr_df.index and c2 in corr_df.columns) else None
                    matrix[c1][c2] = round_val(raw_corr, 3)

        correlations_payload = {
            "available": True,
            "reason": None,
            "columns": numeric_cols,
            "matrix": matrix,
        }

    # --- E. Outlier Detection (IQR Method) ---
    # outlier_indices refers strictly to CLEANED DATAFRAME ROW POSITIONS (0-based positional indexing
    # after df.drop_duplicates(ignore_index=True) from Phase 2).
    if total_rows < 10:
        outliers_payload = {
            "available": False,
            "reason": "Insufficient data for reliable outlier detection.",
            "columns": [],
        }
    else:
        outlier_cols: list[dict[str, Any]] = []
        for col in numeric_cols:
            series = pd.to_numeric(df[col], errors="coerce")
            valid_series = series.dropna()
            if len(valid_series) >= 4:
                q1 = valid_series.quantile(0.25, interpolation="linear")
                q3 = valid_series.quantile(0.75, interpolation="linear")
                iqr = q3 - q1
                lower_bound = round_val(q1 - 1.5 * iqr, 2)
                upper_bound = round_val(q3 + 1.5 * iqr, 2)

                # outlier_indices refers to CLEANED DATAFRAME ROW POSITIONS (0-based positional indexing)
                outlier_indices: list[int] = []
                outlier_values: list[float] = []

                if lower_bound is not None and upper_bound is not None:
                    for idx, val in series.items():
                        if pd.notna(val) and (val < lower_bound or val > upper_bound):
                            outlier_indices.append(int(idx))
                            outlier_values.append(round_val(val, 2))

                outlier_cols.append({
                    "name": col,
                    "lower_bound": lower_bound,
                    "upper_bound": upper_bound,
                    "outlier_indices": outlier_indices,
                    "outlier_values": outlier_values,
                })

        outliers_payload = {
            "available": True,
            "reason": None,
            "columns": outlier_cols,
        }

    summary_payload = {
        "numeric_summary": numeric_summary,
        "categorical_summary": categorical_summary,
        "missing_summary": missing_summary,
    }

    return Analytics(
        summary=summary_payload,
        correlations=correlations_payload,
        charts=[],
        outliers=outliers_payload,
    )
