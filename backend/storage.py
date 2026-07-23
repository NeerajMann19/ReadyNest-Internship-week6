"""
Analytics Studio — In-Memory Session Storage Module

Provides temporary in-memory session management without external database dependencies.
Maintains session state containing canonical objects (Dataset, Analytics, Prediction, Insights, Decision, Report)
and the cleaned pandas DataFrame during active user interactions.

Includes:
- Cache versioning for compiled Executive Reports (REPORT_FORMAT_VERSION = "2026.07")
- Invalidation hooks ensuring stale reports are never served after upstream object mutations
"""

import datetime
import uuid
from typing import Any, Optional
from models import (
    Analytics,
    Dataset,
    Decision,
    Insight,
    Prediction,
    Report,
    SessionState,
)

# In-memory storage dictionary mapping session_id -> SessionState
_SESSIONS: dict[str, SessionState] = {}

# Report Format Version for automatic cache invalidation
REPORT_FORMAT_VERSION: str = "2026.07"

# Report Cache dictionary mapping session_id -> metadata dictionary
# Schema: { "pdf_bytes": bytes, "filename": str, "generated_at": str, "size_bytes": int, "report_format_version": str }
_REPORT_CACHE: dict[str, dict[str, Any]] = {}

# In-memory prediction cache dictionary mapping (session_id, target_column) -> Prediction
_PREDICTION_CACHE: dict[tuple[str, str], Prediction] = {}

# Cache assumes the uploaded dataset is immutable within a session.
# If in-place dataset editing is ever added, this cache key must be extended to include a dataset version/hash.
_DECISION_CACHE: dict[tuple[str, float], Decision] = {}


def invalidate_report_cache(session_id: str) -> None:
    """Purges cached PDF report for the given session_id when upstream data mutates."""
    if session_id in _REPORT_CACHE:
        del _REPORT_CACHE[session_id]


def create_session(session_id: Optional[str] = None) -> str:
    """Creates a new isolated in-memory session and returns the session_id."""
    sid = session_id or str(uuid.uuid4())
    _SESSIONS[sid] = SessionState()
    return sid


def get_session(session_id: str) -> Optional[SessionState]:
    """Retrieves SessionState for the given session_id, or None if not found."""
    return _SESSIONS.get(session_id)


def save_dataset(session_id: str, dataset: Dataset, df: Any = None) -> SessionState:
    """Saves Dataset object and optional cleaned DataFrame into session state."""
    session = _SESSIONS.get(session_id)
    if not session:
        session = SessionState()
        _SESSIONS[session_id] = session

    session.dataset = dataset
    if df is not None:
        session.cleaned_dataframe = df

    invalidate_report_cache(session_id)
    return session


def save_analytics(session_id: str, analytics: Analytics) -> SessionState:
    """Saves Analytics object into session state."""
    session = _SESSIONS.get(session_id)
    if not session:
        session = SessionState()
        _SESSIONS[session_id] = session

    session.analytics = analytics
    invalidate_report_cache(session_id)
    return session


def get_prediction(session_id: str, target_column: str) -> Optional[Prediction]:
    """Retrieves cached Prediction for given session_id and target_column."""
    return _PREDICTION_CACHE.get((session_id, target_column))


def save_prediction(session_id: str, target_column: str, prediction: Prediction) -> SessionState:
    """Saves Prediction object into session state and prediction cache."""
    session = _SESSIONS.get(session_id)
    if not session:
        session = SessionState()
        _SESSIONS[session_id] = session

    session.prediction = prediction
    _PREDICTION_CACHE[(session_id, target_column)] = prediction
    invalidate_report_cache(session_id)
    return session


def save_insights(session_id: str, insights: list[Insight]) -> SessionState:
    """Saves Insights list into session state."""
    session = _SESSIONS.get(session_id)
    if not session:
        session = SessionState()
        _SESSIONS[session_id] = session

    session.insights = insights
    invalidate_report_cache(session_id)
    return session


def get_decision(session_id: str, scenario_input: float) -> Optional[Decision]:
    """Retrieves cached Decision for given session_id and scenario_input value."""
    return _DECISION_CACHE.get((session_id, scenario_input))


def get_latest_decision(session_id: str) -> Optional[Decision]:
    """
    Storage Abstraction: Retrieves the most recently computed Decision object for given session_id.
    Modules must call this helper rather than inspecting cache dictionaries directly.
    """
    session = _SESSIONS.get(session_id)
    if session and session.decision:
        return session.decision

    # Search _DECISION_CACHE for entries matching session_id
    matching = [v for k, v in _DECISION_CACHE.items() if k[0] == session_id]
    if matching:
        return matching[-1]

    return None


def save_decision(session_id: str, scenario_input: float, decision: Decision) -> SessionState:
    """Saves Decision object into session state and decision cache."""
    session = _SESSIONS.get(session_id)
    if not session:
        session = SessionState()
        _SESSIONS[session_id] = session

    session.decision = decision
    _DECISION_CACHE[(session_id, scenario_input)] = decision
    invalidate_report_cache(session_id)
    return session


def get_cached_report(session_id: str) -> Optional[tuple[bytes, str]]:
    """
    Retrieves cached compiled PDF report bytes and filename if available and report_format_version matches.
    If version mismatches or cache is invalid, purges entry and returns None.
    """
    entry = _REPORT_CACHE.get(session_id)
    if not entry:
        return None

    if entry.get("report_format_version") != REPORT_FORMAT_VERSION:
        # Cache version mismatch — invalidate stale report
        del _REPORT_CACHE[session_id]
        return None

    return (entry["pdf_bytes"], entry["filename"])


def save_report_pdf(session_id: str, pdf_bytes: bytes, filename: str) -> None:
    """Saves compiled PDF report bytes and rich metadata into report cache."""
    now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()
    _REPORT_CACHE[session_id] = {
        "pdf_bytes": pdf_bytes,
        "filename": filename,
        "generated_at": now_str,
        "size_bytes": len(pdf_bytes),
        "report_format_version": REPORT_FORMAT_VERSION,
    }


def save_report(session_id: str, report: Report) -> SessionState:
    """Saves Report object into session state."""
    session = _SESSIONS.get(session_id)
    if not session:
        session = SessionState()
        _SESSIONS[session_id] = session

    session.report = report
    return session


def clear_session(session_id: str) -> bool:
    """Clears and removes session from in-memory storage."""
    invalidate_report_cache(session_id)
    if session_id in _SESSIONS:
        del _SESSIONS[session_id]
        return True
    return False
