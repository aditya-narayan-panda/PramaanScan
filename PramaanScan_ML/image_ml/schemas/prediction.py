"""
Praman Scan - Pydantic schemas for the prediction API.
"""
from typing import List, Optional
from pydantic import BaseModel, Field


class ModelPrediction(BaseModel):
    model_name: str = Field(..., description="Human readable model name")
    probability_ai_generated: float = Field(..., ge=0.0, le=1.0)


class FeatureImportanceItem(BaseModel):
    feature_group: str
    importance: float = Field(..., ge=0.0, le=1.0)


class PredictionResponse(BaseModel):
    filename: str
    overall_probability: float = Field(..., ge=0.0, le=1.0, description="Soft-voted average probability of AI generation")
    verdict: str = Field(..., description="'Authentic', 'Likely AI Generated', or 'Inconclusive'")
    confidence: str = Field(..., description="'High', 'Medium', 'Low', or 'N/A' for inconclusive results")
    model_agreement_score: float = Field(..., ge=0.0, le=1.0, description="1 - normalised standard deviation across model outputs")
    disagreement_std: float = Field(..., ge=0.0)
    is_inconclusive: bool
    individual_predictions: List[ModelPrediction]
    feature_importance: List[FeatureImportanceItem]
    processing_time_ms: float
    layer: str = "Layer 3 - Machine Learning Verification"
    disclaimer: str = (
        "This result is produced by an AI-assisted classical machine learning "
        "verification layer and should be considered alongside hash and "
        "provenance verification, not as a standalone determination of authenticity."
    )


class HealthResponse(BaseModel):
    status: str
    models_loaded: bool
    app_name: str
    version: str


class ErrorResponse(BaseModel):
    detail: str


class TrainingMetadata(BaseModel):
    trained_at: str
    n_train_samples: int
    n_test_samples: int
    feature_dimension: int
    metrics: dict
    feature_names: Optional[List[str]] = None
