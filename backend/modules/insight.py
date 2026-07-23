"""
Analytics Studio — Insight Engine Module

Responsibility: Transform quantitative analytics and prediction results into plain-English structured business findings,
categorize findings, assign severity levels, and estimate confidence.

Includes:
- LLM Context preparation (prepare_llm_context)
- Gemini-driven JSON insight generation (generate_insights_via_llm)
- Strict Pydantic validation pipeline (validate_insights)
- Grounded deterministic fallback generator (generate_fallback_insights)
- Main orchestrator enforcing 4-6 count constraint (generate_insights)
"""

import json
import logging
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from typing import Any, Optional

import config
from models import Analytics, Dataset, Insight, Prediction

logger = logging.getLogger(__name__)

# Constants for schema constraints
VALID_CATEGORIES = {"Opportunity", "Risk", "Trend"}
VALID_SEVERITIES = {"low", "medium", "high"}


def prepare_llm_context(
    analytics: Analytics,
    dataset: Dataset,
    prediction: Optional[Prediction] = None,
) -> dict[str, Any]:
    """
    Prepares a clean, compact context payload from Dataset, QualityReport,
    Analytics, and Prediction objects to send to Gemini.
    """
    numeric_summary = analytics.summary.get("numeric_summary", {})
    categorical_summary = analytics.summary.get("categorical_summary", {})
    missing_summary = analytics.summary.get("missing_summary", [])
    correlations = analytics.correlations.get("matrix", {})
    outliers = analytics.outliers.get("columns", [])

    prediction_payload = None
    if prediction and prediction.available:
        prediction_payload = {
            "target_column": prediction.target_column,
            "problem_type": prediction.problem_type,
            "model_type": prediction.model_type,
            "metrics": prediction.metrics,
            "features_used": prediction.features_used,
        }

    context = {
        "dataset_metadata": {
            "filename": dataset.filename,
            "rows": dataset.rows,
            "columns": dataset.columns,
            "quality_score": dataset.quality.quality_score,
            "missing_values_count": dataset.quality.missing_values_count,
            "duplicate_rows_count": dataset.quality.duplicate_rows_count,
        },
        "numeric_summary": numeric_summary,
        "categorical_summary": categorical_summary,
        "missing_summary": missing_summary,
        "correlations": correlations,
        "outliers": outliers,
        "prediction": prediction_payload,
    }
    return context


def generate_insights_via_llm(context: dict[str, Any], timeout_seconds: float = 15.0) -> str:
    """
    Invokes Google Gemini gemini-2.0-flash using google-genai SDK.
    Uses locked generation settings: temperature=0.2, top_p=0.9, top_k=40, response_mime_type="application/json".
    Must complete within timeout_seconds.
    """
    if not config.GEMINI_API_KEY or config.GEMINI_API_KEY.strip() == "" or config.GEMINI_API_KEY == "your_gemini_api_key_here":
        raise ValueError("GEMINI_API_KEY is not set or invalid in configuration.")

    try:
        from google import genai
        from google.genai import types
    except ImportError as e:
        raise ImportError("google-genai SDK is not installed in the python environment.") from e

    prompt = f"""
You are an expert data analyst and business strategist.
Analyze the following dataset context and produce between 4 and 6 high-value business insights.

DATASET CONTEXT:
{json.dumps(context, indent=2)}

CRITICAL REQUIREMENTS FOR OUTPUT:
1. Return ONLY a valid JSON array of objects. Do not wrap in markdown or backticks if possible, but JSON mime type is active.
2. Each object in the array MUST strictly follow this JSON schema:
   {{
     "id": "ins_1",
     "title": "Short plain-English title",
     "description": "Detailed business finding explaining the context and impact.",
     "severity": "low" | "medium" | "high",
     "category": "Opportunity" | "Risk" | "Trend",
     "evidence": {{ "metric_name": "exact metric claim with real computed number" }},
     "confidence": 0.85
   }}
3. Do NOT include a "recommendation" field.
4. "severity" MUST be strictly one of: "low", "medium", "high".
5. "category" MUST be strictly one of: "Opportunity", "Risk", "Trend".
6. "confidence" MUST be a float between 0.0 and 1.0 (e.g. 0.94), NEVER a string or percentage.
7. "evidence" MUST contain specific key-value pairs referencing real computed values from the provided context (e.g. "Marketing_Spend vs Revenue correlation = 0.842", "Missing values: CustomerAge (18.4%)", "Prediction Accuracy = 0.964"). No vague claims.
8. Provide between 4 and 6 distinct insights.
"""

    def _call_api() -> str:
        client = genai.Client(api_key=config.GEMINI_API_KEY)
        gen_config = types.GenerateContentConfig(
            temperature=0.2,
            top_p=0.9,
            top_k=40,
            response_mime_type="application/json",
        )
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=gen_config,
        )
        return response.text or ""

    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(_call_api)
        try:
            return future.result(timeout=timeout_seconds)
        except FuturesTimeoutError as e:
            raise TimeoutError(f"Gemini API call timed out after {timeout_seconds} seconds.") from e


def validate_insights(raw_response: str) -> list[Insight]:
    """
    Pydantic validation pipeline:
    Parses raw response JSON and validates every item against the Insight Pydantic model.
    Raises ValueError/ValidationError if parsing or validation fails.
    """
    if not raw_response or not raw_response.strip():
        raise ValueError("Empty response received from LLM.")

    # Strip markdown fences if present
    cleaned = raw_response.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()

    data = json.loads(cleaned)
    if isinstance(data, dict):
        # Handle case where LLM wrapped in {"insights": [...]}
        data = data.get("insights", data.get("data", [data]))

    if not isinstance(data, list):
        raise ValueError(f"Expected JSON array of insights, got {type(data).__name__}")

    validated_list: list[Insight] = []
    for idx, item in enumerate(data):
        if not isinstance(item, dict):
            raise ValueError(f"Item at index {idx} is not a dictionary.")

        # Coerce category case if minor mismatch (e.g., "trend" -> "Trend")
        cat = str(item.get("category", "")).strip().capitalize()
        if cat in VALID_CATEGORIES:
            item["category"] = cat

        # Coerce severity case
        sev = str(item.get("severity", "")).strip().lower()
        if sev in VALID_SEVERITIES:
            item["severity"] = sev

        # Coerce confidence rounding
        conf = item.get("confidence")
        if isinstance(conf, (int, float)):
            item["confidence"] = round(float(conf), 2)

        # Validate with Pydantic
        insight_obj = Insight.model_validate(item)

        # Additional domain contract checks
        if insight_obj.category not in VALID_CATEGORIES:
            raise ValueError(f"Invalid category '{insight_obj.category}' for insight {insight_obj.id}")
        if insight_obj.severity not in VALID_SEVERITIES:
            raise ValueError(f"Invalid severity '{insight_obj.severity}' for insight {insight_obj.id}")
        if not (0.0 <= insight_obj.confidence <= 1.0):
            raise ValueError(f"Confidence {insight_obj.confidence} out of range 0.0-1.0")

        validated_list.append(insight_obj)

    if not validated_list:
        raise ValueError("No valid insights were parsed from response.")

    return validated_list


def generate_fallback_insights(
    analytics: Analytics,
    dataset: Dataset,
    prediction: Optional[Prediction] = None,
) -> list[Insight]:
    """
    Deterministic fallback generator:
    Constructs grounded, real-evidence insights directly from Analytics, Dataset,
    and Prediction fields if Gemini API fails or returns invalid response.
    Guarantees at least 4 valid Insight objects.
    """
    insights: list[Insight] = []
    count = 1

    # 1. Dataset Quality & Missing Values Insight
    missing_summary = analytics.summary.get("missing_summary", [])
    highest_missing = max(missing_summary, key=lambda x: x.get("missing_percentage", 0)) if missing_summary else None

    if highest_missing and highest_missing.get("missing_percentage", 0) > 0:
        col_name = highest_missing["column"]
        pct = highest_missing["missing_percentage"]
        m_cnt = highest_missing["missing_count"]
        insights.append(
            Insight(
                id=f"ins_fb_{count}",
                title=f"Data Completeness Risk in {col_name}",
                description=f"Column '{col_name}' has the highest missing data rate in the dataset ({pct}% missing). This may introduce bias in analytics and predictive modeling.",
                severity="medium" if pct < 20 else "high",
                category="Risk",
                evidence={
                    "column": col_name,
                    "missing_percentage": f"{pct}%",
                    "missing_count": m_cnt,
                    "quality_score": f"{dataset.quality.quality_score:.1f}%",
                },
                confidence=0.95,
            )
        )
        count += 1
    else:
        insights.append(
            Insight(
                id=f"ins_fb_{count}",
                title="High Dataset Quality & Completeness",
                description="The dataset exhibits excellent data quality with minimal to no missing records across all analyzed columns.",
                severity="low",
                category="Opportunity",
                evidence={
                    "quality_score": f"{dataset.quality.quality_score:.1f}%",
                    "missing_values_count": dataset.quality.missing_values_count,
                    "duplicate_rows_count": dataset.quality.duplicate_rows_count,
                },
                confidence=0.98,
            )
        )
        count += 1

    # 2. Strongest Correlation Pair Insight
    corr_data = analytics.correlations
    if corr_data.get("available") and corr_data.get("matrix") and corr_data.get("columns"):
        cols = corr_data["columns"]
        matrix = corr_data["matrix"]
        max_corr_val = 0.0
        best_pair = None

        for i in range(len(cols)):
            for j in range(i + 1, len(cols)):
                c1, c2 = cols[i], cols[j]
                val = matrix.get(c1, {}).get(c2)
                if val is not None and abs(val) > abs(max_corr_val):
                    max_corr_val = val
                    best_pair = (c1, c2)

        if best_pair:
            c1, c2 = best_pair
            direction = "positive" if max_corr_val > 0 else "negative"
            strength = "strong" if abs(max_corr_val) > 0.7 else "moderate" if abs(max_corr_val) > 0.3 else "weak"
            insights.append(
                Insight(
                    id=f"ins_fb_{count}",
                    title=f"{strength.capitalize()} {direction.capitalize()} Correlation: {c1} & {c2}",
                    description=f"A {strength} {direction} correlation ({max_corr_val:.3f}) was identified between '{c1}' and '{c2}', indicating potential colinearity or dependent relationship.",
                    severity="low" if strength == "weak" else "medium",
                    category="Trend",
                    evidence={
                        "feature_pair": f"{c1} vs {c2}",
                        "pearson_correlation": f"{max_corr_val:.3f}",
                    },
                    confidence=0.92,
                )
            )
            count += 1

    # 3. Outlier Detection Summary
    outliers = analytics.outliers.get("columns", [])
    total_outliers = sum(len(item.get("outlier_indices", [])) for item in outliers)
    most_outliers_col = max(outliers, key=lambda x: len(x.get("outlier_indices", []))) if outliers else None

    if most_outliers_col and len(most_outliers_col.get("outlier_indices", [])) > 0:
        col_out_name = most_outliers_col["name"]
        col_out_cnt = len(most_outliers_col["outlier_indices"])
        insights.append(
            Insight(
                id=f"ins_fb_{count}",
                title=f"Statistical Outliers Detected in {col_out_name}",
                description=f"Identified {col_out_cnt} statistical outlier values in column '{col_out_name}' using 1.5x IQR boundaries. Total outliers across dataset: {total_outliers}.",
                severity="medium",
                category="Risk",
                evidence={
                    "primary_column": col_out_name,
                    "column_outlier_count": col_out_cnt,
                    "total_dataset_outliers": total_outliers,
                },
                confidence=0.88,
            )
        )
        count += 1

    # 4. Prediction Model Insight (if prediction exists)
    if prediction and prediction.available:
        target = prediction.target_column or "Target"
        model_name = prediction.model_type
        metric_str = ", ".join(f"{k.upper()} = {v}" for k, v in prediction.metrics.items())
        insights.append(
            Insight(
                id=f"ins_fb_{count}",
                title=f"Predictive Model Performance for {target}",
                description=f"Baseline ML model ({model_name}) evaluated on target '{target}' using features [{', '.join(prediction.features_used)}]. Metrics: {metric_str}.",
                severity="low",
                category="Opportunity",
                evidence={
                    "target_column": target,
                    "model_type": model_name,
                    "metrics": prediction.metrics,
                    "features_count": len(prediction.features_used),
                },
                confidence=0.90,
            )
        )
        count += 1

    # 5. Dataset Dimension & Volume Trend Insight
    if len(insights) < 4:
        insights.append(
            Insight(
                id=f"ins_fb_{count}",
                title="Dataset Dimension Breakdown",
                description=f"Active dataset contains {dataset.rows:,} rows and {dataset.columns} columns across schema types.",
                severity="low",
                category="Trend",
                evidence={
                    "filename": dataset.filename,
                    "total_rows": dataset.rows,
                    "total_columns": dataset.columns,
                },
                confidence=0.99,
            )
        )
        count += 1

    # 6. Additional Numeric Distribution Insight if still < 4
    if len(insights) < 4:
        num_summary = analytics.summary.get("numeric_summary", {})
        if num_summary:
            first_col = list(num_summary.keys())[0]
            stats = num_summary[first_col]
            insights.append(
                Insight(
                    id=f"ins_fb_{count}",
                    title=f"Numeric Distribution Overview: {first_col}",
                    description=f"Column '{first_col}' exhibits mean={stats.get('mean')}, min={stats.get('min')}, max={stats.get('max')}.",
                    severity="low",
                    category="Trend",
                    evidence={
                        "column": first_col,
                        "mean": stats.get("mean"),
                        "std_dev": stats.get("std_dev"),
                    },
                    confidence=0.95,
                )
            )

    return insights[:6]


def generate_insights(
    dataset: Dataset,
    analytics: Analytics,
    prediction: Optional[Prediction] = None,
) -> list[Insight]:
    """
    Main entry point for Insight Engine:
    - Prepares LLM context
    - Calls Gemini LLM primary path
    - Runs Pydantic validation pipeline
    - On failure or insufficient items (<4), uses deterministic fallback generator to fill/generate
    - Enforces returning strictly between 4 and 6 Insights.
    """
    context = prepare_llm_context(analytics, dataset, prediction)
    insights: list[Insight] = []

    # Primary Path: Gemini Generation & Validation
    try:
        raw_response = generate_insights_via_llm(context, timeout_seconds=15.0)
        llm_insights = validate_insights(raw_response)
        insights = llm_insights
        logger.info(f"Successfully generated and validated {len(insights)} insights via Gemini LLM.")
    except Exception as exc:
        logger.warning(f"Gemini LLM insight generation/validation failed ({exc}). Falling back to deterministic generator.")
        insights = []

    # Enforce Count Constraint (4-6 insights)
    if len(insights) > 6:
        # Truncate to top 6
        insights = insights[:6]
    elif len(insights) < 4:
        # Fill remainder with fallback generator
        fallback_items = generate_fallback_insights(analytics, dataset, prediction)
        existing_ids = {ins.id for ins in insights}

        for fb in fallback_items:
            if len(insights) >= 4:
                break
            if fb.id not in existing_ids:
                insights.append(fb)
                existing_ids.add(fb.id)

        # If still < 4 (e.g. ID overlap), append fallback items with unique ID
        for idx, fb in enumerate(fallback_items):
            if len(insights) >= 4:
                break
            new_id = f"ins_fb_fill_{idx+1}"
            if new_id not in existing_ids:
                fb_copy = fb.model_copy(update={"id": new_id})
                insights.append(fb_copy)
                existing_ids.add(new_id)

    return insights
