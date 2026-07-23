"""
Analytics Studio — Dataset Module

Responsible for reading, parsing, validating, and cleaning uploaded CSV datasets,
inferring column schemas, detecting duplicates/missing values, and calculating quality scores.
"""

import io
import math
from typing import Any
import pandas as pd
from models import Dataset, ColumnSchema, QualityReport

print(f"[DATASET MODULE LOADED] file: {__file__}")


def sanitize_val(val: Any) -> Any:
    """Converts numpy types and NaNs to standard native Python JSON-serializable types."""
    if pd.isna(val):
        return None
    if isinstance(val, (int, float)):
        if math.isnan(val) or math.isinf(val):
            return None
        if isinstance(val, float) and val.is_integer():
            return int(val)
        return float(val) if isinstance(val, float) else int(val)
    if isinstance(val, pd.Timestamp):
        return val.isoformat()
    return str(val)


def process_csv_upload(file_bytes: bytes, filename: str, session_id: str = "") -> tuple[Dataset, pd.DataFrame]:
    """
    Parses and cleans CSV file bytes into a canonical Dataset object and pandas DataFrame.

    Raises ValueError with a user-friendly message if file is empty, corrupted, or unparseable.
    """
    if not file_bytes or len(file_bytes) == 0:
        raise ValueError("Uploaded file is empty.")

    try:
        decoded_content = file_bytes.decode("utf-8")
    except UnicodeDecodeError:
        raise ValueError("File must be UTF-8 encoded text CSV.")

    if not decoded_content.strip():
        raise ValueError("CSV file content is empty or contains only whitespace.")

    try:
        df = pd.read_csv(io.StringIO(decoded_content))
    except Exception as e:
        raise ValueError(f"Failed to parse CSV file: {str(e)}")

    if df.empty or len(df.columns) == 0:
        raise ValueError("Dataset has no rows or columns.")

    original_rows = len(df)
    original_cols = len(df.columns)

    # Strip leading/trailing whitespace from string columns to normalize duplicate checking
    for col in df.select_dtypes(include=["object"]).columns:
        df[col] = df[col].astype(str).str.strip()

    # Determine subset columns for duplicate detection (exclude auto-increment ID column if present)
    non_id_cols = [c for c in df.columns if str(c).lower() not in ("id", "uuid", "_id", "index")]
    subset_cols = non_id_cols if len(non_id_cols) > 0 else None

    # Detect and remove duplicate rows
    df_deduped = df.drop_duplicates(subset=subset_cols, ignore_index=True)
    duplicate_rows_count = int(original_rows - len(df_deduped))
    df = df_deduped.copy()

    data_type_issues: list[str] = []
    schemas: list[ColumnSchema] = []
    total_missing_values = 0

    # Process each column for dtype inference and schema generation
    for col in df.columns:
        col_str = str(col)
        series = df[col]
        missing_count = int(series.isna().sum())
        total_missing_values += missing_count

        inferred_type = "string"

        # Attempt numeric conversion for object columns if applicable
        if series.dtype == "object":
            non_nulls = series.dropna()
            if len(non_nulls) > 0:
                # Try numeric conversion
                numeric_converted = pd.to_numeric(non_nulls, errors="coerce")
                if numeric_converted.notna().sum() / len(non_nulls) >= 0.8:
                    df[col] = pd.to_numeric(series, errors="coerce")
                    series = df[col]
                    inferred_type = "numeric"
                else:
                    # Try datetime conversion
                    try:
                        datetime_converted = pd.to_datetime(non_nulls, errors="coerce")
                        if datetime_converted.notna().sum() / len(non_nulls) >= 0.8:
                            df[col] = pd.to_datetime(series, errors="coerce")
                            series = df[col]
                            inferred_type = "datetime"
                    except Exception:
                        pass
        elif pd.api.types.is_numeric_dtype(series.dtype):
            inferred_type = "numeric"
        elif pd.api.types.is_datetime64_any_dtype(series.dtype):
            inferred_type = "datetime"
        elif pd.api.types.is_bool_dtype(series.dtype):
            inferred_type = "boolean"

        # Check for dtype anomalies
        if series.dtype == "object" and missing_count > (len(series) * 0.5):
            data_type_issues.append(f"Column '{col_str}' has high proportion of missing values ({missing_count} nulls)")

        # Collect up to 5 non-null sample values
        sample_raw = series.dropna().unique()[:5]
        sample_values = [sanitize_val(v) for v in sample_raw if v is not None]

        schemas.append(
            ColumnSchema(
                name=col_str,
                data_type=inferred_type,
                missing_count=missing_count,
                sample_values=sample_values,
            )
        )

    # Compute quality score
    total_cells = len(df) * original_cols if len(df) * original_cols > 0 else 1
    missing_pct = total_missing_values / total_cells
    duplicate_pct = duplicate_rows_count / original_rows if original_rows > 0 else 0.0
    dtype_issue_pct = len(data_type_issues) / original_cols if original_cols > 0 else 0.0

    raw_score = 100.0 - (missing_pct * 40.0) - (duplicate_pct * 30.0) - (dtype_issue_pct * 30.0)
    quality_score = max(0.0, round(raw_score, 1))

    quality_report = QualityReport(
        missing_values_count=total_missing_values,
        duplicate_rows_count=duplicate_rows_count,
        quality_score=quality_score,
        data_type_issues=data_type_issues,
    )

    dataset = Dataset(
        id=session_id or "ds_session",
        filename=filename,
        rows=len(df),
        columns=len(df.columns),
        column_schema=schemas,
        quality=quality_report,
    )

    return dataset, df
