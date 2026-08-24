"""
Pydantic schemas for the QMI Technical Analysis API.

These models define the public contract returned by the technical
analysis endpoints.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class MacdResponse(BaseModel):
    """Latest MACD indicator values."""

    line: float | None = Field(default=None, description="Latest MACD line value.")
    signal: float | None = Field(default=None, description="Latest MACD signal-line value.")
    histogram: float | None = Field(default=None, description="Latest MACD histogram value.")


class TrendResponse(BaseModel):
    """Latest trend-indicator values."""

    sma_20: float | None = None
    sma_50: float | None = None
    sma_200: float | None = None
    ema_20: float | None = None
    ema_50: float | None = None
    ema_200: float | None = None


class MomentumResponse(BaseModel):
    """Latest momentum-indicator values."""

    rsi_14: float | None = Field(default=None, ge=0, le=100)
    macd: MacdResponse


class VolatilityResponse(BaseModel):
    """Latest volatility-indicator values."""

    atr_14: float | None = Field(
        default=None,
        ge=0,
        description="Latest 14-period Average True Range.",
    )


class TrendScoreComponentResponse(BaseModel):
    """One weighted component of the QMI Trend Score."""

    name: str
    score: float = Field(ge=-100, le=100)
    weight: float = Field(ge=0, le=1)
    value: float | None = None
    state: str | None = None
    contribution: float


class TrendScoreResponse(BaseModel):
    """QMI normalized Trend Score."""

    score: float = Field(ge=-100, le=100)
    direction: str
    data_quality: float = Field(ge=0, le=100)
    components: dict[str, TrendScoreComponentResponse]
    observations_required: int = Field(ge=1)
    observations_available: int = Field(ge=1)



class StrengthScoreComponentResponse(BaseModel):
    """One weighted component of QMI Trend Strength."""

    name: str
    score: float = Field(ge=0, le=100)
    weight: float = Field(ge=0, le=1)
    value: float | None = None
    state: str | None = None
    contribution: float


class StrengthScoreResponse(BaseModel):
    """QMI normalized Trend Strength Score."""

    score: float = Field(ge=0, le=100)
    strength: str
    dmi_direction: str
    regime_conflict: bool
    data_quality: float = Field(ge=0, le=100)
    components: dict[str, StrengthScoreComponentResponse]
    observations_required: int = Field(ge=1)
    observations_available: int = Field(ge=1)



class MarketRegimeResponse(BaseModel):
    """QMI primary market-regime classification."""

    primary_regime: str
    direction: str
    trend_score: float = Field(ge=-100, le=100)
    strength_score: float = Field(ge=0, le=100)
    strength: str
    dmi_direction: str
    regime_conflict: bool
    confidence: float = Field(ge=0, le=100)
    trend_agreement: float = Field(ge=0, le=100)
    strength_quality: float = Field(ge=0, le=100)
    structure_quality: float = Field(ge=0, le=100)
    temporal_stability: float = Field(ge=0, le=100)
    transition_state: str
    regime_age: int | None = Field(
        default=None,
        ge=1,
        description=(
            "Reserved for the later multi-session temporal layer. "
            "None in snapshot-only DE-TA-001C."
        ),
    )



class MomentumScoreComponentResponse(BaseModel):
    """One weighted contextual component of the QMI Momentum Score."""

    name: str
    score: float = Field(ge=-100, le=100)
    weight: float = Field(ge=0, le=1)
    value: float | None = None
    state: str | None = None
    contribution: float


class MomentumScoreResponse(BaseModel):
    """QMI contextual Momentum Score."""

    score: float = Field(ge=-100, le=100)
    state: str
    confidence: float = Field(ge=0, le=100)
    regime_context: str
    momentum_delta_5: float | None = None
    momentum_delta_10: float | None = None
    acceleration: str
    divergence_type: str
    divergence_strength: float = Field(ge=0, le=100)
    data_quality: float = Field(ge=0, le=100)
    weights: dict[str, float]
    components: dict[str, MomentumScoreComponentResponse]
    observations_required: int = Field(ge=1)
    observations_available: int = Field(ge=1)



class VolatilityScoreComponentResponse(BaseModel):
    """One weighted component of the QMI Volatility Score."""

    name: str
    score: float = Field(ge=0, le=100)
    weight: float = Field(ge=0, le=1)
    value: float | None = None
    state: str | None = None
    contribution: float


class VolatilityScoreResponse(BaseModel):
    """QMI Volatility Engine response."""

    score: float = Field(ge=0, le=100)
    state: str
    direction: str
    confidence: float = Field(ge=0, le=100)
    risk_environment: str
    atr_normalized: float
    atr_percentile: float = Field(ge=0, le=100)
    historical_volatility_20: float
    historical_volatility_60: float
    hv_ratio: float | None = None
    bollinger_bandwidth: float
    bandwidth_percentile: float = Field(ge=0, le=100)
    volatility_delta_5: float | None = None
    volatility_delta_10: float | None = None
    compression: bool
    expansion: bool
    data_quality: float = Field(ge=0, le=100)
    components: dict[str, VolatilityScoreComponentResponse]
    observations_required: int = Field(ge=1)
    observations_available: int = Field(ge=1)



class VolumeScoreComponentResponse(BaseModel):
    """One weighted component of the QMI Volume Score."""

    name: str
    score: float = Field(ge=-100, le=100)
    weight: float = Field(ge=0, le=1)
    value: float | None = None
    state: str | None = None
    contribution: float


class VolumeScoreResponse(BaseModel):
    """QMI Volume & Participation Engine response."""

    score: float = Field(ge=-100, le=100)
    state: str
    direction: str
    confidence: float = Field(ge=0, le=100)
    participation_score: float = Field(ge=0, le=100)
    relative_volume: float
    volume_zscore: float
    up_down_ratio: float | None = None
    obv: float
    obv_slope_5: float
    obv_slope_20: float
    adl: float
    adl_slope: float
    volume_trend: float
    dry_up: bool
    climax: str
    divergence_type: str
    divergence_strength: float = Field(ge=0, le=100)
    breakout_confirmation: str
    false_breakout_risk: bool
    data_quality: float = Field(ge=0, le=100)
    components: dict[str, VolumeScoreComponentResponse]
    observations_required: int = Field(ge=1)
    observations_available: int = Field(ge=1)


class TechnicalScoringResponse(BaseModel):
    """Decision Engine scoring currently available for technical analysis."""

    trend: TrendScoreResponse
    strength: StrengthScoreResponse
    regime: MarketRegimeResponse
    momentum: MomentumScoreResponse
    volatility_engine: VolatilityScoreResponse
    volume: VolumeScoreResponse


class TechnicalSignalsResponse(BaseModel):
    """Legacy descriptive signals retained for API compatibility."""

    trend: str
    momentum: str
    macd: str


class TechnicalAnalysisResponse(BaseModel):
    """Complete technical-analysis snapshot for one market symbol."""

    symbol: str = Field(min_length=1, examples=["NIO"])
    last_price: float | None = None
    observations: int = Field(ge=1)
    trend: TrendResponse
    momentum: MomentumResponse
    volatility: VolatilityResponse
    scoring: TechnicalScoringResponse
    signals: TechnicalSignalsResponse
