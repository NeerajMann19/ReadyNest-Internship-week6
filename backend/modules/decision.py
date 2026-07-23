"""
Analytics Studio — Decision Simulator Module

Responsibility: Simulate business decisions (specifically percentage price changes),
estimate expected financial and operational impact, generate key business assumptions,
formulate executive recommendations, and produce counter analysis with risk mitigations.

Includes:
- LLM Context preparation (prepare_llm_context)
- Gemini-driven Decision simulation (generate_decision_via_llm)
- Strict Pydantic validation pipeline (validate_decision)
- Grounded deterministic fallback simulator (generate_fallback_decision)
- Main orchestrator (generate_decision)
"""

import json
import logging
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from typing import Any, Optional

import config
from models import Analytics, CounterAnalysis, Decision, Insight, Prediction, QualityReport

logger = logging.getLogger(__name__)


def prepare_llm_context(
    quality_report: QualityReport,
    analytics: Analytics,
    prediction: Optional[Prediction],
    insights: list[Insight],
    scenario_input: float,
) -> dict[str, Any]:
    """
    Prepares a clean, compact context payload containing QualityReport, Analytics,
    Prediction, Insights, and the single percentage price change scenario input.
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

    insights_summary = [
        {
            "id": ins.id,
            "title": ins.title,
            "category": ins.category,
            "severity": ins.severity,
            "evidence": ins.evidence,
        }
        for ins in insights
    ]

    context = {
        "scenario": {
            "type": "percentage_price_change",
            "value": scenario_input,
            "description": f"{scenario_input:+}% price adjustment scenario.",
        },
        "quality_report": {
            "quality_score": quality_report.quality_score,
            "missing_values_count": quality_report.missing_values_count,
            "duplicate_rows_count": quality_report.duplicate_rows_count,
        },
        "numeric_summary": numeric_summary,
        "categorical_summary": categorical_summary,
        "missing_summary": missing_summary,
        "correlations": correlations,
        "outliers": outliers,
        "prediction": prediction_payload,
        "insights": insights_summary,
    }
    return context


def generate_decision_via_llm(context: dict[str, Any], timeout_seconds: float = 15.0) -> str:
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
You are an executive business strategist and financial simulation expert.
Analyze the following dataset context and evaluate the requested business scenario simulation.

EXPLICIT SCENARIO SEMANTICS:
The field `scenario.value` ({context["scenario"]["value"]}) represents a PERCENTAGE PRICE CHANGE (e.g. 5 means a +5% price increase, -10 means a -10% price reduction). It is NEVER a flat currency amount or unit value.

DATASET CONTEXT:
{json.dumps(context, indent=2)}

CRITICAL REQUIREMENTS FOR OUTPUT:
1. Return ONLY a valid JSON object matching this exact Decision schema:
   {{
     "scenario_name": "Price Adjustment Simulation ({context["scenario"]["value"]:+}%)",
     "expected_impact": {{
       "price_change": "{context["scenario"]["value"]:+}%",
       "projected_volume_change": "e.g. -4.2%",
       "net_revenue_impact": "e.g. +5.6%"
     }},
     "confidence": 0.88,
     "assumptions": [
       "Assumption 1 based on dataset evidence",
       "Assumption 2 based on market dynamics"
     ],
     "recommendation": "Clear, actionable executive recommendation statement.",
     "counter_analysis": {{
       "risks": ["Risk 1", "Risk 2"],
       "trade_offs": ["Trade-off 1", "Trade-off 2"],
       "alternative_scenarios": ["Alternative 1", "Alternative 2"],
       "mitigations": ["Mitigation 1", "Mitigation 2"]
     }}
   }}
2. Do NOT add, rename, or remove any top-level or nested fields.
3. "confidence" MUST be a float between 0.0 and 1.0 (e.g. 0.88), NEVER a string or percentage.
4. Ground your financial reasoning, assumptions, and counter analysis directly on the provided Analytics, Prediction metrics, and Insights.
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


def validate_decision(raw_response: str) -> Decision:
    """
    Pydantic validation pipeline:
    Parses raw response JSON and validates against the canonical Decision model.
    Raises ValueError/ValidationError if parsing or validation fails.
    """
    if not raw_response or not raw_response.strip():
        raise ValueError("Empty response received from LLM.")

    cleaned = raw_response.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()

    data = json.loads(cleaned)
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object for Decision, got {type(data).__name__}")

    # Coerce confidence float rounding if present
    conf = data.get("confidence")
    if isinstance(conf, (int, float)):
        data["confidence"] = round(float(conf), 2)

    decision_obj = Decision.model_validate(data)

    if not (0.0 <= decision_obj.confidence <= 1.0):
        raise ValueError(f"Confidence {decision_obj.confidence} out of valid range 0.0 - 1.0.")

    return decision_obj


def generate_fallback_decision(
    quality_report: QualityReport,
    analytics: Analytics,
    prediction: Optional[Prediction],
    insights: list[Insight],
    scenario_input: float,
) -> Decision:
    """
    Deterministic fallback generator:
    Constructs a complete Decision domain object with grounded evidence calculations
    if Gemini LLM API fails, times out, or returns invalid schema.
    """
    sign = "+" if scenario_input > 0 else ""
    scenario_name = f"Price Adjustment Simulation ({sign}{scenario_input}%)"

    # Base price elasticity calculation: -0.7 baseline
    elasticity = -0.7
    estimated_volume_change_pct = scenario_input * elasticity
    net_revenue_impact_pct = scenario_input + estimated_volume_change_pct

    expected_impact = {
        "price_adjustment": f"{sign}{scenario_input:.1f}%",
        "projected_demand_change": f"{estimated_volume_change_pct:+.1f}%",
        "estimated_net_revenue_impact": f"{net_revenue_impact_pct:+.1f}%",
    }

    if prediction and prediction.available and prediction.target_column:
        expected_impact["modeled_target_column"] = prediction.target_column
        expected_impact["model_algorithm"] = prediction.model_type

    assumptions = [
        f"Price elasticity of demand is modeled at {elasticity} based on standard industry baseline.",
        "Competitor market pricing and overall demand volume remain stable during rollout.",
        "Data quality score of dataset is high enough to support directional elasticity projection.",
    ]

    if quality_report.quality_score < 80.0:
        assumptions.append("Quality score is below 80%; additional data cleansing may improve simulation precision.")

    if scenario_input > 0:
        recommendation = (
            f"Proceed with a phased implementation of the {scenario_input:+}% price increase. "
            f"Expected net revenue change is estimated at {net_revenue_impact_pct:+.1f}% assuming a "
            f"{estimated_volume_change_pct:+.1f}% demand volume change."
        )
        counter_analysis = CounterAnalysis(
            risks=[
                f"Customer churn may exceed projected volume contraction of {estimated_volume_change_pct:.1f}%.",
                "Competitor price matching may undercut brand market position.",
            ],
            trade_offs=[
                "Accepting lower overall transaction volume in exchange for higher per-unit gross margin.",
                "Potential short-term dip in customer satisfaction scores.",
            ],
            alternative_scenarios=[
                f"Implement a smaller price adjustment of {scenario_input / 2:+.1f}% initially.",
                "Introduce tiered pricing packages or bundle features to justify price change.",
            ],
            mitigations=[
                "Monitor customer retention rates weekly post-rollout.",
                "Offer grandfathered pricing options for top enterprise tiers.",
            ],
        )
    else:
        recommendation = (
            f"Implement the proposed {scenario_input}% price reduction to drive volume growth. "
            f"Projected demand increase is estimated at {estimated_volume_change_pct:+.1f}%."
        )
        counter_analysis = CounterAnalysis(
            risks=[
                "Margin compression if volume growth fails to offset lower unit price.",
                "Brand equity perception risk associated with discounting.",
            ],
            trade_offs=[
                "Trading short-term unit margin for expanded total user market share.",
                "Higher operational load due to increased volume throughput.",
            ],
            alternative_scenarios=[
                "Offer promotional temporal discounts instead of permanent price cuts.",
                "Bundle secondary features to increase perceived product value.",
            ],
            mitigations=[
                "Establish minimum margin threshold guardrails prior to price cut implementation.",
                "Track customer acquisition cost (CAC) and lifetime value (LTV) ratios.",
            ],
        )

    return Decision(
        scenario_name=scenario_name,
        expected_impact=expected_impact,
        confidence=0.85,
        assumptions=assumptions,
        recommendation=recommendation,
        counter_analysis=counter_analysis,
    )


def generate_decision(
    quality_report: QualityReport,
    analytics: Analytics,
    prediction: Optional[Prediction],
    insights: list[Insight],
    scenario_input: float,
) -> Decision:
    """
    Main entry point for Decision Simulator:
    - Prepares LLM context
    - Calls Gemini LLM primary path
    - Runs Pydantic validation pipeline
    - On failure, uses deterministic fallback generator
    """
    context = prepare_llm_context(quality_report, analytics, prediction, insights, scenario_input)

    try:
        raw_response = generate_decision_via_llm(context, timeout_seconds=15.0)
        decision_obj = validate_decision(raw_response)
        logger.info("Successfully generated and validated Decision via Gemini LLM.")
        return decision_obj
    except Exception as exc:
        logger.warning(f"Gemini LLM decision simulation failed ({exc}). Falling back to deterministic generator.")
        return generate_fallback_decision(quality_report, analytics, prediction, insights, scenario_input)
