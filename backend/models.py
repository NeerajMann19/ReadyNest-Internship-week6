"""
Analytics Studio — Canonical Domain Models

Defines all core Pydantic v2 domain models and nested structures exchanged
between system modules (Dataset, Analytics, Prediction, Insight, Decision, Report, Advisor).
"""

from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class ColumnSchema(BaseModel):
    """Schema definition for a single dataset column."""
    name: str = Field(..., description="Column name")
    data_type: str = Field(..., description="Inferred data type (e.g., numeric, categorical, datetime)")
    missing_count: int = Field(0, description="Count of missing or null values")
    sample_values: list[Any] = Field(default_factory=list, description="Sample values from column")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "revenue",
                "data_type": "numeric",
                "missing_count": 0,
                "sample_values": [1200.50, 4500.00, 3100.25]
            }
        }
    )


class QualityReport(BaseModel):
    """Data quality metrics for an uploaded dataset."""
    missing_values_count: int = Field(..., description="Total missing values across dataset")
    duplicate_rows_count: int = Field(..., description="Number of duplicate rows")
    quality_score: float = Field(..., description="Quality score between 0.0 and 100.0")
    data_type_issues: list[str] = Field(default_factory=list, description="Identified data quality issues")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "missing_values_count": 12,
                "duplicate_rows_count": 0,
                "quality_score": 95.5,
                "data_type_issues": ["Column 'age' contains 2 string values"]
            }
        }
    )


class Dataset(BaseModel):
    """Canonical Dataset domain object."""
    id: str = Field(..., description="Unique session/dataset identifier")
    filename: str = Field(..., description="Original dataset filename")
    rows: int = Field(..., description="Total row count")
    columns: int = Field(..., description="Total column count")
    column_schema: list[ColumnSchema] = Field(..., alias="schema", description="List of column schemas")
    quality: QualityReport = Field(..., description="Quality assessment report")

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "id": "sess_123456",
                "filename": "sales_q3.csv",
                "rows": 1000,
                "columns": 5,
                "schema": [
                    {
                        "name": "revenue",
                        "data_type": "numeric",
                        "missing_count": 0,
                        "sample_values": [1200.50, 4500.00]
                    }
                ],
                "quality": {
                    "missing_values_count": 0,
                    "duplicate_rows_count": 0,
                    "quality_score": 100.0,
                    "data_type_issues": []
                }
            }
        }
    )


class Analytics(BaseModel):
    """Canonical Analytics domain object."""
    summary: dict[str, Any] = Field(..., description="Summary statistics per column")
    correlations: dict[str, Any] = Field(..., description="Correlation matrix data")
    charts: list[dict[str, Any]] = Field(..., description="Structured chart visual configurations")
    outliers: dict[str, Any] = Field(..., description="Detected outliers per column")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "summary": {"revenue": {"mean": 2500.0, "std": 500.0}},
                "correlations": {"revenue_vs_units": 0.85},
                "charts": [{"id": "chart_1", "type": "bar", "title": "Revenue by Region"}],
                "outliers": {"revenue": [99999.00]}
            }
        }
    )


class Prediction(BaseModel):
    """Canonical Prediction domain object."""
    available: bool = Field(True, description="Whether prediction evaluation was successful")
    reason: str | None = Field(None, description="Reason if prediction unavailable")
    target_column: str | None = Field(None, description="Selected target column name")
    problem_type: str = Field(..., description="ML problem type (classification or regression)")
    model_type: str = Field(..., description="Algorithm used (LinearRegression or LogisticRegression)")
    metrics: dict[str, Any] = Field(default_factory=dict, description="Model evaluation metrics rounded to 4 decimals")
    stratified: bool | None = Field(None, description="Whether classification train/test split was stratified")
    label_mapping: dict[str, Any] | None = Field(None, description="Label encoding map for classification target")
    features_used: list[str] = Field(default_factory=list, description="List of numeric feature column names used")
    row_counts: dict[str, int] = Field(default_factory=dict, description="Row counts breakdown (total_cleaned, train_count, test_count)")
    predictions: list[dict[str, Any]] = Field(default_factory=list, description="Sample test prediction results (at most 10)")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "available": True,
                "reason": None,
                "target_column": "revenue",
                "problem_type": "regression",
                "model_type": "LinearRegression",
                "metrics": {"mae": 12.34, "rmse": 15.67, "r2": 0.985},
                "stratified": None,
                "label_mapping": None,
                "features_used": ["marketing_spend", "discount"],
                "row_counts": {"total_cleaned": 100, "train_count": 80, "test_count": 20},
                "predictions": [{"actual": 2500.0, "predicted": 2480.0}]
            }
        }
    )


class Insight(BaseModel):
    """Canonical Insight domain object."""
    id: str = Field(..., description="Unique insight identifier")
    title: str = Field(..., description="Plain-English insight title")
    description: str = Field(..., description="Detailed business finding")
    severity: str = Field(..., description="Severity level: low, medium, high, critical")
    category: str = Field(..., description="Category: Trend, Outlier, Opportunity, Risk")
    evidence: dict[str, Any] = Field(..., description="Supporting data evidence")
    confidence: float = Field(..., description="Confidence score between 0.0 and 1.0")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "ins_001",
                "title": "Revenue Growth Spurt",
                "description": "Quarterly revenue increased significantly driven by digital marketing.",
                "severity": "medium",
                "category": "Opportunity",
                "evidence": {"growth_rate": "+18.5%"},
                "confidence": 0.92
            }
        }
    )


class CounterAnalysis(BaseModel):
    """Nested Counter Analysis for business decision evaluation."""
    risks: list[str] = Field(..., description="Potential risks associated with decision")
    trade_offs: list[str] = Field(..., description="Identified business trade-offs")
    alternative_scenarios: list[str] = Field(..., description="Alternative courses of action")
    mitigations: list[str] = Field(..., description="Recommended risk mitigations")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "risks": ["Customer churn due to higher price point"],
                "trade_offs": ["Short-term volume drop for higher unit margin"],
                "alternative_scenarios": ["Tiered pricing rollout"],
                "mitigations": ["Grandfather existing loyal customers"]
            }
        }
    )


class Decision(BaseModel):
    """Canonical Decision Simulation domain object."""
    scenario_name: str = Field(..., description="Name of business scenario simulated")
    expected_impact: dict[str, Any] = Field(..., description="Projected financial and metric impact")
    confidence: float = Field(..., description="Simulation confidence score")
    assumptions: list[str] = Field(..., description="Key business assumptions")
    recommendation: str = Field(..., description="Executive recommendation statement")
    counter_analysis: CounterAnalysis = Field(..., description="Counter analysis and risk evaluation")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "scenario_name": "Price Increase",
                "expected_impact": {"net_revenue_change": "+8.2%"},
                "confidence": 0.88,
                "assumptions": ["Elasticity remains at -0.4"],
                "recommendation": "Proceed with 5% price increase across premium product tier.",
                "counter_analysis": {
                    "risks": ["Customer churn increase"],
                    "trade_offs": ["Lower overall unit volume"],
                    "alternative_scenarios": ["Targeted discount bundle"],
                    "mitigations": ["Monitor churn weekly"]
                }
            }
        }
    )


class Report(BaseModel):
    """Canonical Executive Report domain object."""
    sections: list[dict[str, Any]] = Field(..., description="Structured report sections")
    generated_at: str = Field(..., description="ISO timestamp of report generation")
    pdf_path: str = Field(..., description="File path to generated PDF report")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "sections": [{"title": "Executive Summary", "content": "Overall dataset shows steady growth."}],
                "generated_at": "2026-07-22T12:00:00Z",
                "pdf_path": "/exports/reports/report_sess_123456.pdf"
            }
        }
    )


class AdvisorResponse(BaseModel):
    """Canonical Executive Advisor response object."""
    explanation: str = Field(..., description="Plain-English explanation of chart or insight")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "explanation": "This chart illustrates a strong positive correlation between marketing spend and quarterly sales."
            }
        }
    )


class SessionState(BaseModel):
    """In-memory session state model holding incremental domain objects."""
    dataset: Dataset | None = None
    analytics: Analytics | None = None
    prediction: Prediction | None = None
    insights: list[Insight] = Field(default_factory=list)
    decision: Decision | None = None
    report: Report | None = None
    cleaned_dataframe: Any | None = None

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_schema_extra={
            "example": {
                "dataset": None,
                "analytics": None,
                "prediction": None,
                "insights": [],
                "decision": None,
                "report": None,
                "cleaned_dataframe": None
            }
        }
    )
