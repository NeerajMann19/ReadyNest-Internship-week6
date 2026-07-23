"""
Analytics Studio — In-Memory Session Storage Module

Provides temporary in-memory session management without external database dependencies.
Maintains session state containing canonical objects (Dataset, Analytics, Prediction, Insights, Decision, Report)
and the cleaned pandas DataFrame during active user interactions.
"""

import uuid
from typing import Any, Optional
from models import (
    SessionState,
    Dataset,
    Analytics,
    Prediction,
    Insight,
    Decision,
    Report,
)

# In-memory storage dictionary mapping session_id -> SessionState
_SESSIONS: dict[str, SessionState] = {}


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
    return session


def save_analytics(session_id: str, analytics: Analytics) -> SessionState:
    """Saves Analytics object into session state."""
    session = _SESSIONS.get(session_id)
    if not session:
        session = SessionState()
        _SESSIONS[session_id] = session

    session.analytics = analytics
    return session


# In-memory prediction cache dictionary mapping (session_id, target_column) -> Prediction
_PREDICTION_CACHE: dict[tuple[str, str], Prediction] = {}


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
    return session


def save_insights(session_id: str, insights: list[Insight]) -> SessionState:
    """Saves Insights list into session state."""
    session = _SESSIONS.get(session_id)
    if not session:
        session = SessionState()
        _SESSIONS[session_id] = session

    session.insights = insights
    return session


# Cache assumes the uploaded dataset is immutable within a session.
# If in-place dataset editing is ever added, this cache key must be extended to include a dataset version/hash.
_DECISION_CACHE: dict[tuple[str, float], Decision] = {}


def get_decision(session_id: str, scenario_input: float) -> Optional[Decision]:
    """Retrieves cached Decision for given session_id and scenario_input value."""
    return _DECISION_CACHE.get((session_id, scenario_input))


def save_decision(session_id: str, scenario_input: float, decision: Decision) -> SessionState:
    """Saves Decision object into session state and decision cache."""
    session = _SESSIONS.get(session_id)
    if not session:
        session = SessionState()
        _SESSIONS[session_id] = session

    session.decision = decision
    _DECISION_CACHE[(session_id, scenario_input)] = decision
    return session



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
    if session_id in _SESSIONS:
        del _SESSIONS[session_id]
        return True
    return False
