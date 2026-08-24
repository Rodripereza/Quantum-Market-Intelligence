"""Data models used internally by the QMI technical scoring engine."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass(slots=True)
class TrendComponent:
    """One directional component of the QMI Trend Score."""

    name: str
    score: float
    weight: float
    value: float | None = None
    state: str | None = None
    contribution: float = 0.0

    def __post_init__(self) -> None:
        self.score = round(float(self.score), 4)
        self.weight = round(float(self.weight), 4)
        self.contribution = round(self.score * self.weight, 4)


@dataclass(slots=True)
class TrendScoreResult:
    """Complete QMI Trend Score result."""

    score: float
    direction: str
    data_quality: float
    components: dict[str, TrendComponent] = field(default_factory=dict)
    observations_required: int = 220
    observations_available: int = 0

    def to_dict(self) -> dict:
        result = asdict(self)
        result["score"] = round(float(self.score), 2)
        result["data_quality"] = round(float(self.data_quality), 2)
        return result



@dataclass(slots=True)
class StrengthComponent:
    """One non-directional component of QMI Trend Strength."""

    name: str
    score: float
    weight: float
    value: float | None = None
    state: str | None = None
    contribution: float = 0.0

    def __post_init__(self) -> None:
        self.score = round(max(0.0, min(100.0, float(self.score))), 4)
        self.weight = round(float(self.weight), 4)
        self.contribution = round(self.score * self.weight, 4)


@dataclass(slots=True)
class StrengthScoreResult:
    """Complete QMI Trend Strength result."""

    score: float
    strength: str
    dmi_direction: str
    regime_conflict: bool
    data_quality: float
    components: dict[str, StrengthComponent] = field(default_factory=dict)
    observations_required: int = 220
    observations_available: int = 0

    def to_dict(self) -> dict:
        result = asdict(self)
        result["score"] = round(float(self.score), 2)
        result["data_quality"] = round(float(self.data_quality), 2)
        return result



@dataclass(slots=True)
class RegimeResult:
    """QMI market-regime classification derived from trend and strength."""

    primary_regime: str
    direction: str
    trend_score: float
    strength_score: float
    strength: str
    dmi_direction: str
    regime_conflict: bool
    confidence: float
    trend_agreement: float
    strength_quality: float
    structure_quality: float
    temporal_stability: float
    transition_state: str
    regime_age: int | None = None

    def to_dict(self) -> dict:
        result = asdict(self)
        for key in (
            "trend_score",
            "strength_score",
            "confidence",
            "trend_agreement",
            "strength_quality",
            "structure_quality",
            "temporal_stability",
        ):
            result[key] = round(float(result[key]), 2)
        return result



@dataclass(slots=True)
class MomentumComponent:
    """One weighted component of the QMI Momentum Score."""

    name: str
    score: float
    weight: float
    value: float | None = None
    state: str | None = None
    contribution: float = 0.0

    def __post_init__(self) -> None:
        self.score = round(max(-100.0, min(100.0, float(self.score))), 4)
        self.weight = round(float(self.weight), 4)
        self.contribution = round(self.score * self.weight, 4)


@dataclass(slots=True)
class MomentumScoreResult:
    """Complete contextual QMI Momentum result."""

    score: float
    state: str
    confidence: float
    regime_context: str
    momentum_delta_5: float | None
    momentum_delta_10: float | None
    acceleration: str
    divergence_type: str
    divergence_strength: float
    data_quality: float
    weights: dict[str, float] = field(default_factory=dict)
    components: dict[str, MomentumComponent] = field(default_factory=dict)
    observations_required: int = 60
    observations_available: int = 0

    def to_dict(self) -> dict:
        result = asdict(self)
        for key in ("score", "confidence", "divergence_strength", "data_quality"):
            result[key] = round(float(result[key]), 2)
        if result["momentum_delta_5"] is not None:
            result["momentum_delta_5"] = round(float(result["momentum_delta_5"]), 2)
        if result["momentum_delta_10"] is not None:
            result["momentum_delta_10"] = round(float(result["momentum_delta_10"]), 2)
        return result



@dataclass(slots=True)
class VolatilityComponent:
    """One non-directional component of the QMI Volatility Score."""

    name: str
    score: float
    weight: float
    value: float | None = None
    state: str | None = None
    contribution: float = 0.0

    def __post_init__(self) -> None:
        self.score = round(max(0.0, min(100.0, float(self.score))), 4)
        self.weight = round(float(self.weight), 4)
        self.contribution = round(self.score * self.weight, 4)


@dataclass(slots=True)
class VolatilityScoreResult:
    """Complete QMI Volatility Engine result."""

    score: float
    state: str
    direction: str
    confidence: float
    risk_environment: str
    atr_normalized: float
    atr_percentile: float
    historical_volatility_20: float
    historical_volatility_60: float
    hv_ratio: float | None
    bollinger_bandwidth: float
    bandwidth_percentile: float
    volatility_delta_5: float | None
    volatility_delta_10: float | None
    compression: bool
    expansion: bool
    data_quality: float
    components: dict[str, VolatilityComponent] = field(default_factory=dict)
    observations_required: int = 80
    observations_available: int = 0

    def to_dict(self) -> dict:
        result = asdict(self)
        for key in (
            "score",
            "confidence",
            "atr_normalized",
            "atr_percentile",
            "historical_volatility_20",
            "historical_volatility_60",
            "bandwidth_percentile",
            "bollinger_bandwidth",
            "data_quality",
        ):
            result[key] = round(float(result[key]), 4)
        if result["hv_ratio"] is not None:
            result["hv_ratio"] = round(float(result["hv_ratio"]), 4)
        if result["volatility_delta_5"] is not None:
            result["volatility_delta_5"] = round(float(result["volatility_delta_5"]), 2)
        if result["volatility_delta_10"] is not None:
            result["volatility_delta_10"] = round(float(result["volatility_delta_10"]), 2)
        return result



@dataclass(slots=True)
class VolumeComponent:
    """One weighted directional component of the QMI Volume Score."""

    name: str
    score: float
    weight: float
    value: float | None = None
    state: str | None = None
    contribution: float = 0.0

    def __post_init__(self) -> None:
        self.score = round(max(-100.0, min(100.0, float(self.score))), 4)
        self.weight = round(float(self.weight), 4)
        self.contribution = round(self.score * self.weight, 4)


@dataclass(slots=True)
class VolumeScoreResult:
    """Complete QMI Volume & Participation Engine result."""

    score: float
    state: str
    direction: str
    confidence: float
    participation_score: float
    relative_volume: float
    volume_zscore: float
    up_down_ratio: float | None
    obv: float
    obv_slope_5: float
    obv_slope_20: float
    adl: float
    adl_slope: float
    volume_trend: float
    dry_up: bool
    climax: str
    divergence_type: str
    divergence_strength: float
    breakout_confirmation: str
    false_breakout_risk: bool
    data_quality: float
    components: dict[str, VolumeComponent] = field(default_factory=dict)
    observations_required: int = 60
    observations_available: int = 0

    def to_dict(self) -> dict:
        result = asdict(self)
        for key in (
            "score",
            "confidence",
            "participation_score",
            "relative_volume",
            "volume_zscore",
            "obv",
            "obv_slope_5",
            "obv_slope_20",
            "adl",
            "adl_slope",
            "volume_trend",
            "divergence_strength",
            "data_quality",
        ):
            result[key] = round(float(result[key]), 4)
        if result["up_down_ratio"] is not None:
            result["up_down_ratio"] = round(float(result["up_down_ratio"]), 4)
        return result
