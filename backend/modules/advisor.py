"""
Analytics Studio — Executive Advisor Module

Responsibility: Provide contextual, plain-language executive business explanations for specific
Insight objects selected by the user.

Includes:
- Context payload preparation (prepare_llm_context)
- Gemini 2.0 Flash LLM generation with 10-15s timeout (generate_explanation_via_llm)
- Deterministic fallback generation (generate_fallback_explanation)
- Main orchestrator (generate_explanation)
"""

import json
import logging
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from typing import Any, Optional

import config
from models import AdvisorResponse, Insight

logger = logging.getLogger(__name__)


def prepare_llm_context(target: Insight | dict[str, Any]) -> dict[str, Any]:
    """
    Prepares a clean, compact context payload from a target Insight object or dict for Gemini.
    """
    if isinstance(target, Insight):
        return {
            "type": "insight",
            "id": target.id,
            "title": target.title,
            "description": target.description,
            "severity": target.severity,
            "category": target.category,
            "evidence": target.evidence,
            "confidence": target.confidence,
        }
    elif isinstance(target, dict):
        return target
    else:
        return {"raw_target": str(target)}


def generate_explanation_via_llm(context: dict[str, Any], timeout_seconds: float = 12.0) -> AdvisorResponse:
    """
    Calls Google Gemini 2.0 Flash SDK to generate a 2-3 sentence executive plain-language explanation.
    Uses strict generation settings: temperature=0.2, top_p=0.9, top_k=40, response_mime_type="application/json".
    """
    if not config.GEMINI_API_KEY or config.GEMINI_API_KEY.strip() == "" or config.GEMINI_API_KEY == "your_gemini_api_key_here":
        raise ValueError("GEMINI_API_KEY is not set or invalid in configuration.")

    try:
        from google import genai
        from google.genai import types
    except ImportError as e:
        raise ImportError("google-genai SDK is not installed in the python environment.") from e

    prompt = f"""
You are an executive AI business advisor for an enterprise analytics platform.
Provide a concise, plain-language explanation of the following business finding suitable for an executive.

CONTEXT FINDING:
{json.dumps(context, indent=2)}

CRITICAL REQUIREMENTS FOR OUTPUT:
1. Explain the practical business implications in 2-3 short, clear sentences.
2. Do NOT use technical jargon, ML terminology, or statistical formulas.
3. Return ONLY a valid JSON object matching this exact schema:
   {{
     "explanation": "2-3 clear executive sentences explaining what this finding means for strategic decision making."
   }}
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
            raw_text = future.result(timeout=timeout_seconds)
        except FuturesTimeoutError as e:
            raise TimeoutError(f"Gemini API call timed out after {timeout_seconds} seconds.") from e

    if not raw_text or not raw_text.strip():
        raise ValueError("Empty response received from LLM.")

    # Parse raw JSON response into AdvisorResponse
    try:
        data = json.loads(raw_text)
        if isinstance(data, dict) and "explanation" in data and isinstance(data["explanation"], str):
            return AdvisorResponse(explanation=data["explanation"].strip())
        raise ValueError("JSON response missing 'explanation' string key.")
    except Exception as parse_err:
        logger.warning(f"Failed to parse Gemini response for Advisor: {parse_err}. Raw text: {raw_text[:100]}")
        raise parse_err


def generate_fallback_explanation(target: Insight | dict[str, Any]) -> AdvisorResponse:
    """
    Generates a deterministic fallback explanation built directly from the target's fields if Gemini fails.
    """
    if isinstance(target, Insight):
        confidence_pct = int(target.confidence * 100)
        text = (
            f"Executive Finding: '{target.title}' indicates a {target.severity}-severity {target.category.lower()} scenario. "
            f"{target.description} (Model Confidence: {confidence_pct}%)."
        )
    elif isinstance(target, dict):
        title = target.get("title", "Business Finding")
        desc = target.get("description", "Analytics observation requires executive review.")
        text = f"Executive Summary for '{title}': {desc}"
    else:
        text = f"Business observation recorded: {str(target)}"

    return AdvisorResponse(explanation=text)


def generate_explanation(target: Insight | dict[str, Any]) -> AdvisorResponse:
    """
    Main orchestrator for Executive Advisor explanation:
    1. Prepares LLM context.
    2. Attempts Gemini API call with 12s timeout.
    3. Falls back to deterministic sentence on API failure, timeout, or missing key.
    """
    context = prepare_llm_context(target)
    try:
        explanation_obj = generate_explanation_via_llm(context)
        logger.info("Successfully generated advisor explanation via Gemini 2.0 Flash.")
        return explanation_obj
    except Exception as e:
        logger.warning(f"Executive Advisor LLM generation failed/skipped: {e}. Utilizing deterministic fallback.")
        return generate_fallback_explanation(target)
