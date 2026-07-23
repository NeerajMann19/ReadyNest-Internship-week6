"""
Analytics Studio — Executive Report Module

Responsibility: Assemble structured domain objects (Dataset, QualityReport, Analytics,
Prediction, Insights, Decision) into an executive-grade HTML document via Jinja2
and render to PDF via WeasyPrint.

Includes:
- Deterministic Zero-LLM Executive Summary synthesis
- Pre-built presentation-only Jinja2 context assembly
- Graceful WeasyPrint dependency detection & PDF compilation
- Storage abstraction integration (storage.get_latest_decision, storage.get_cached_report)
"""

import datetime
import logging
from pathlib import Path
from typing import Any, Optional

import storage
from models import Analytics, Dataset, Decision, Insight, Prediction, QualityReport

logger = logging.getLogger(__name__)


def build_report_context(
    session_id: str,
    dataset: Dataset,
    analytics: Analytics,
    prediction: Optional[Prediction],
    insights: list[Insight],
    decision: Optional[Decision],
) -> dict[str, Any]:
    """
    Assembles a complete, pre-built context dictionary for Jinja2 template rendering.
    Contains zero business logic or dynamic storage calls — purely presentation-ready data.
    """
    now = datetime.datetime.now(datetime.timezone.utc)
    timestamp_display = now.strftime("%Y-%m-%d %H:%M:%S UTC")

    # 1. Dataset metadata
    meta = {
        "title": "Analytics Studio Executive Report",
        "filename": dataset.filename,
        "rows": f"{dataset.rows:,}",
        "columns": dataset.columns,
        "generated_at": timestamp_display,
    }

    # 2. Quality report
    quality = {
        "quality_score": f"{dataset.quality.quality_score:.1f}",
        "missing_values_count": dataset.quality.missing_values_count,
        "duplicate_rows_count": dataset.quality.duplicate_rows_count,
        "data_type_issues": dataset.quality.data_type_issues,
    }

    # 3. Schema
    schema_list = [
        {
            "name": col.name,
            "data_type": col.data_type,
            "missing_count": col.missing_count,
            "sample_values": col.sample_values[:3] if col.sample_values else [],
        }
        for col in dataset.column_schema
    ]

    # 4. Analytics Summary
    num_summary = analytics.summary.get("numeric_summary", {})
    correlations_matrix = analytics.correlations.get("matrix", {})
    corr_columns = analytics.correlations.get("columns", [])

    strong_correlations = []
    if corr_columns and correlations_matrix:
        for i in range(len(corr_columns)):
            for j in range(i + 1, len(corr_columns)):
                c1, c2 = corr_columns[i], corr_columns[j]
                val = correlations_matrix.get(c1, {}).get(c2)
                if val is not None and abs(val) >= 0.3:
                    strength = "Strong" if abs(val) >= 0.7 else "Moderate"
                    strong_correlations.append(
                        {
                            "pair": f"{c1} vs {c2}",
                            "value": f"{val:.3f}",
                            "strength": strength,
                        }
                    )

    analytics_payload = {
        "numeric": num_summary,
        "strong_correlations": strong_correlations,
    }

    # 5. Deterministic Zero-LLM Executive Summary Synthesis
    exec_takeaways = [ins.title for ins in insights[:3]]
    decision_scenario_str = "None Run"

    if decision:
        decision_scenario_str = f"Based on a simulated {decision.scenario_name}"
        exec_takeaways.append(f"Simulation Recommendation: {decision.recommendation}")

    narrative = (
        f"Executive summary synthesized from active dataset '{dataset.filename}' containing {dataset.rows:,} records. "
        f"Data quality is evaluated at {dataset.quality.quality_score:.1f}%. "
        f"Analytics identified {len(insights)} high-value business insights. "
    )
    if decision:
        narrative += f"Scenario simulation for '{decision.scenario_name}' projects actionable strategic outcomes."

    exec_summary = {
        "narrative": narrative,
        "key_takeaways": exec_takeaways,
    }

    # 6. Insights
    insights_payload = [
        {
            "id": ins.id,
            "title": ins.title,
            "description": ins.description,
            "severity": ins.severity,
            "category": ins.category,
            "evidence": ins.evidence,
            "confidence": ins.confidence,
        }
        for ins in insights
    ]

    context = {
        "meta": meta,
        "quality": quality,
        "dataset_schema": schema_list,
        "exec_summary": exec_summary,
        "analytics_summary": analytics_payload,
        "prediction": prediction,
        "insights": insights_payload,
        "decision": decision,
        "decision_scenario_value": decision_scenario_str,
    }

    return context


def render_report_html(context: dict[str, Any]) -> str:
    """
    Renders presentation-only report context into HTML using Jinja2 templates.
    No storage calls or data logic inside.
    """
    try:
        from jinja2 import Environment, FileSystemLoader
    except ImportError as e:
        raise ImportError("jinja2 package is missing from the environment.") from e

    templates_dir = Path(__file__).resolve().parent.parent / "templates"
    env = Environment(loader=FileSystemLoader(templates_dir), autoescape=True)
    template = env.get_template("report.html")
    return template.render(context)


def render_report_pdf(html_str: str) -> bytes:
    """
    Compiles HTML string into PDF binary using WeasyPrint.
    Passes metadata and catches missing GTK/Pango system C-libraries.
    """
    try:
        from weasyprint import HTML
    except Exception as e:
        logger.error(f"WeasyPrint import or initialization failed: {e}")
        raise RuntimeError("WEASYPRINT_DEPENDENCY_MISSING: System C-libraries (libgobject-2.0-0, cairo, pango) are missing from system DLL path.") from e

    try:
        pdf_bytes = HTML(string=html_str).write_pdf()
        return pdf_bytes
    except Exception as e:
        logger.error(f"Failed to compile PDF via WeasyPrint: {e}")
        if "libgobject" in str(e) or "cairo" in str(e) or "pango" in str(e) or "dlopen" in str(e):
            raise RuntimeError("WEASYPRINT_DEPENDENCY_MISSING: System C-libraries (libgobject-2.0-0, cairo, pango) are missing from system DLL path.") from e
        raise e


def generate_report(session_id: str) -> tuple[bytes, str]:
    """
    Main orchestrator for Executive Report Generation:
    1. Checks report cache via storage abstraction.
    2. Validates minimum required artifacts (Dataset + Analytics + Insights).
    3. Fetches optional Prediction & latest Decision via storage abstraction.
    4. Builds pre-built Jinja2 context.
    5. Renders HTML & compiles PDF.
    6. Saves to cache with timestamped filename format: AnalyticsStudio_Executive_Report_{YYYYMMDD}_{HHMMSS}.pdf
    """
    # 1. Storage Abstraction Cache Check
    cached = storage.get_cached_report(session_id)
    if cached:
        logger.info(f"Returning cached PDF report for session_id '{session_id}'.")
        return cached

    session = storage.get_session(session_id)
    if not session:
        raise KeyError(f"Session '{session_id}' not found.")

    if not session.dataset:
        raise KeyError(f"Dataset for session '{session_id}' not found.")

    # 2. Explicit Minimum Artifact Boundaries Check
    if not session.analytics or not session.insights or len(session.insights) == 0:
        raise ValueError("Analytics and Insights must be generated before exporting the executive report.")

    # 3. Storage Abstraction for optional Decision
    latest_decision = storage.get_latest_decision(session_id)
    prediction = session.prediction

    # 4. Context assembly & HTML render
    context = build_report_context(
        session_id=session_id,
        dataset=session.dataset,
        analytics=session.analytics,
        prediction=prediction,
        insights=session.insights,
        decision=latest_decision,
    )

    html_str = render_report_html(context)

    # 5. PDF compilation
    pdf_bytes = render_report_pdf(html_str)

    # 6. Timestamped filename format: AnalyticsStudio_Executive_Report_{YYYYMMDD}_{HHMMSS}.pdf
    now = datetime.datetime.now(datetime.timezone.utc)
    filename = f"AnalyticsStudio_Executive_Report_{now.strftime('%Y%m%d_%H%M%S')}.pdf"

    # Save to storage cache
    storage.save_report_pdf(session_id, pdf_bytes, filename)

    return (pdf_bytes, filename)
