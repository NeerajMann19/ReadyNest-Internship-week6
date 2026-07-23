"""
Analytics Studio — API Routes Definition

Registers system endpoints for API access.
Provides /health, POST /dataset/upload, and GET /dataset/{session_id}/analytics.
"""

from fastapi import APIRouter, File, UploadFile, status
from fastapi.responses import JSONResponse
from modules.dataset import process_csv_upload
from modules.analytics import compute_analytics
import storage

router = APIRouter()

MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB


@router.get("/health", summary="Service Health Check")
async def health_check() -> dict[str, str]:
    """Health check endpoint used by Render and local diagnostics."""
    return {"status": "ok"}


@router.post("/dataset/upload", summary="Upload and Validate CSV Dataset")
async def upload_dataset(file: UploadFile = File(...)):
    """
    Accepts CSV file upload, validates constraints, parses schema and quality scores,
    and returns session_id along with canonical Dataset object.
    """
    if not file or not file.filename:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": "No file uploaded.", "code": "INVALID_REQUEST"},
        )

    filename = file.filename
    if not filename.lower().endswith(".csv"):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": "Only .csv files are supported.", "code": "INVALID_REQUEST"},
        )

    try:
        contents = await file.read()
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": f"Failed to read uploaded file: {str(e)}", "code": "INVALID_REQUEST"},
        )

    if len(contents) > MAX_FILE_SIZE_BYTES:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": "File size exceeds maximum limit of 25MB.", "code": "INVALID_REQUEST"},
        )

    try:
        session_id = storage.create_session()
        dataset_obj, df = process_csv_upload(contents, filename, session_id=session_id)
        storage.save_dataset(session_id, dataset_obj, df)
        return {
            "session_id": session_id,
            "dataset": dataset_obj.model_dump(by_alias=True),
        }
    except ValueError as ve:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": str(ve), "code": "INVALID_REQUEST"},
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": f"An error occurred while processing CSV dataset: {str(e)}", "code": "INTERNAL_SERVER_ERROR"},
        )


from modules.prediction import compute_prediction


@router.get("/dataset/{session_id}/analytics", summary="Get Dataset Analytics")
async def get_analytics(session_id: str):
    """
    Retrieves or computes analytics (numeric stats, categorical top values, correlation matrix,
    outliers, missing summary) for the specified session_id.
    """
    if not session_id or not session_id.strip():
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": "Invalid session_id parameter.", "code": "INVALID_REQUEST"},
        )

    session = storage.get_session(session_id)
    if not session:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"message": "Session not found.", "code": "SESSION_NOT_FOUND"},
        )

    if not session.dataset or session.cleaned_dataframe is None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"message": "Dataset not found for this session.", "code": "DATASET_NOT_FOUND"},
        )

    # Return cached analytics if available
    if session.analytics is not None:
        return session.analytics.model_dump(by_alias=True)

    try:
        analytics_obj = compute_analytics(session.dataset, session.cleaned_dataframe)
        storage.save_analytics(session_id, analytics_obj)
        return analytics_obj.model_dump(by_alias=True)
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": f"Failed to compute dataset analytics: {str(e)}", "code": "INTERNAL_SERVER_ERROR"},
        )


@router.get("/dataset/{session_id}/prediction", summary="Get ML Prediction Evaluation")
async def get_prediction(session_id: str, target_column: str):
    """
    Trains (if not cached) and evaluates a baseline prediction model (LinearRegression or LogisticRegression)
    for the specified target_column and session_id.
    """
    if not session_id or not session_id.strip():
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": "Invalid session_id parameter.", "code": "INVALID_REQUEST"},
        )

    if not target_column or not target_column.strip():
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": "Query parameter target_column is required.", "code": "INVALID_REQUEST"},
        )

    session = storage.get_session(session_id)
    if not session:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"message": "Session not found.", "code": "SESSION_NOT_FOUND"},
        )

    if not session.dataset or session.cleaned_dataframe is None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"message": "Dataset not found for this session.", "code": "DATASET_NOT_FOUND"},
        )

    # Return cached prediction for (session_id, target_column) if available
    cached_prediction = storage.get_prediction(session_id, target_column)
    if cached_prediction is not None:
        return cached_prediction.model_dump(by_alias=True)

    try:
        prediction_obj = compute_prediction(session.dataset, session.cleaned_dataframe, target_column)
        storage.save_prediction(session_id, target_column, prediction_obj)
        return prediction_obj.model_dump(by_alias=True)
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": f"Failed to compute dataset prediction: {str(e)}", "code": "INTERNAL_SERVER_ERROR"},
        )


from modules.insight import generate_insights


@router.get("/dataset/{session_id}/insights", summary="Get Structured Business Insights")
async def get_insights(session_id: str):
    """
    Retrieves or generates structured business insights (Gemini LLM primary, deterministic fallback)
    for the specified session_id. Insights are cached strictly by session_id.
    """
    if not session_id or not session_id.strip():
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": "Invalid session_id parameter.", "code": "INVALID_REQUEST"},
        )

    session = storage.get_session(session_id)
    if not session:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"message": "Session not found.", "code": "SESSION_NOT_FOUND"},
        )

    if not session.dataset:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"message": "Dataset not found for this session.", "code": "DATASET_NOT_FOUND"},
        )

    if not session.analytics:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": "Analytics must be generated before requesting insights.", "code": "ANALYTICS_REQUIRED"},
        )

    # Return cached insights if already generated for this session
    if session.insights and len(session.insights) > 0:
        return {"insights": [insight.model_dump(by_alias=True) for insight in session.insights]}

    try:
        insights = generate_insights(
            dataset=session.dataset,
            analytics=session.analytics,
            prediction=session.prediction,
        )
        storage.save_insights(session_id, insights)
        return {"insights": [insight.model_dump(by_alias=True) for insight in insights]}
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": f"Failed to generate insights: {str(e)}", "code": "INTERNAL_SERVER_ERROR"},
        )


import math
from pydantic import BaseModel, Field
from modules.decision import generate_decision


class DecisionRequest(BaseModel):
    scenario_input: float = Field(..., description="Percentage price change adjustment value (e.g. 5 for +5%, -10 for -10%)")


@router.post("/dataset/{session_id}/decision", summary="Simulate Business Scenario Decision")
async def simulate_decision(session_id: str, body: DecisionRequest):
    """
    Simulates a business scenario decision based on percentage price change (scenario_input).
    Results are cached per (session_id, scenario_input).
    """
    if not session_id or not session_id.strip():
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": "Invalid session_id parameter.", "code": "INVALID_REQUEST"},
        )

    val = body.scenario_input
    # Reject non-numeric, null, NaN, or Infinity inputs
    if val is None or not isinstance(val, (int, float)) or math.isnan(val) or math.isinf(val):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": "scenario_input must be a valid finite number.", "code": "INVALID_INPUT"},
        )

    # SANITY GUARD: This is a crash-prevention limit (|input| <= 10000) to prevent numerical overflow in fallback math or invalid LLM prompts. It is NOT a product business rule restriction.
    if abs(val) > 10000:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": "scenario_input absolute value exceeds sanity limit of 10000.", "code": "INVALID_INPUT"},
        )

    session = storage.get_session(session_id)
    if not session:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"message": "Session not found.", "code": "SESSION_NOT_FOUND"},
        )

    if not session.dataset:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"message": "Dataset not found for this session.", "code": "DATASET_NOT_FOUND"},
        )

    if not session.analytics:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": "Analytics must be generated before running decision simulation.", "code": "ANALYTICS_REQUIRED"},
        )

    if not session.insights or len(session.insights) == 0:
        # Generate insights automatically if not already generated
        session.insights = generate_insights(
            dataset=session.dataset,
            analytics=session.analytics,
            prediction=session.prediction,
        )
        storage.save_insights(session_id, session.insights)

    # Return cached decision if available for (session_id, scenario_input)
    cached_decision = storage.get_decision(session_id, val)
    if cached_decision is not None:
        return {"decision": cached_decision.model_dump(by_alias=True)}

    try:
        decision_obj = generate_decision(
            quality_report=session.dataset.quality,
            analytics=session.analytics,
            prediction=session.prediction,
            insights=session.insights,
            scenario_input=val,
        )
        storage.save_decision(session_id, val, decision_obj)
        return {"decision": decision_obj.model_dump(by_alias=True)}
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": f"Failed to simulate decision: {str(e)}", "code": "INTERNAL_SERVER_ERROR"},
        )


from fastapi import Response
from modules.report import generate_report


@router.post("/dataset/{session_id}/report", summary="Generate and Download Executive PDF Report")
async def export_report(session_id: str):
    """
    Generates and returns the compiled Executive PDF Report (application/pdf) for the active session.
    Catches missing GTK3/Pango system C-libraries and returns clean HTTP 503 Service Unavailable.
    """
    if not session_id or not session_id.strip():
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": "Invalid session_id parameter.", "code": "INVALID_REQUEST"},
        )

    try:
        pdf_bytes, filename = generate_report(session_id)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except KeyError as ke:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"message": str(ke).strip("'"), "code": "SESSION_NOT_FOUND"},
        )
    except ValueError as ve:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": str(ve), "code": "ANALYTICS_REQUIRED"},
        )
    except RuntimeError as re:
        if "WEASYPRINT_DEPENDENCY_MISSING" in str(re):
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "message": "PDF rendering dependencies (GTK3 / Pango / Cairo C-libraries) are unavailable on the server OS.",
                    "code": "WEASYPRINT_DEPENDENCY_MISSING",
                    "details": "On Windows, install GTK3 Runtime (GTK3-Runtime-Win64.exe) or deploy on Linux where Pango/Cairo are natively installed.",
                },
            )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": f"Failed to compile report PDF: {str(re)}", "code": "INTERNAL_SERVER_ERROR"},
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": f"An error occurred while generating report PDF: {str(e)}", "code": "INTERNAL_SERVER_ERROR"},
        )




