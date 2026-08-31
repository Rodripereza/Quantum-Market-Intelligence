from __future__ import annotations
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

class NioModelDelivery(BaseModel):
    brand: str
    deliveries: int = Field(ge=0)

class NioMonthlyDeliveryRecord(BaseModel):
    period: str
    year: int
    month: int
    total: int = Field(ge=0)
    brands: Dict[str, int] = Field(default_factory=dict)
    models: Dict[str, NioModelDelivery] = Field(default_factory=dict)
    yoy_pct: Optional[float] = None
    mom_pct: Optional[float] = None
    ytd: Optional[int] = None
    source: str = "Deliveries.xlsx"
    source_type: str = "user_dataset"
    verified: bool = False

class NioDeliverySnapshot(BaseModel):
    latest_period: str
    latest_total: int
    ytd_total: int
    yoy_pct: Optional[float] = None
    mom_pct: Optional[float] = None
    avg_3m: Optional[float] = None
    avg_6m: Optional[float] = None
    annualized_run_rate: Optional[float] = None
    brand_mix: Dict[str, float] = Field(default_factory=dict)
    latest_brand_deliveries: Dict[str, int] = Field(default_factory=dict)
    latest_model_deliveries: Dict[str, int] = Field(default_factory=dict)

class NioDeliveryIntelligence(BaseModel):
    delivery_score: float = Field(ge=0, le=100)
    momentum_state: str
    trend_3m: str
    brand_diversification: str
    delivery_regime: str
    confidence: str
    evidence: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)

class NioAspModelMixItem(BaseModel):
    model: str
    brand: str
    deliveries: int = Field(ge=0)
    estimated_price_rmb: Optional[float] = None


class NioAspQuarter(BaseModel):
    quarter: str
    year: int
    quarter_number: int
    deliveries: int = Field(ge=0)
    priced_deliveries: int = Field(ge=0)
    price_coverage_pct: float = 0.0
    model_mix_asp_rmb: Optional[float] = None
    reported_asp_rmb: Optional[float] = None
    calibration_factor: Optional[float] = None
    forecast_asp_rmb: Optional[float] = None
    forecast_vehicle_revenue_rmb: Optional[float] = None
    is_forecast: bool = False
    asp_qoq_pct: Optional[float] = None
    model_mix: List[NioAspModelMixItem] = Field(default_factory=list)


class NioAspIntelligence(BaseModel):
    engine: str = "NIO ASP & Revenue Intelligence"
    engine_id: str = "DE-NIO-ASP-001.0"
    version: str = "0.1.0"
    currency: str = "CNY"
    methodology: str
    latest_quarter: Optional[str] = None
    calibration_factor: float = 1.0
    asp_trend: str = "UNKNOWN"
    premiumization_state: str = "UNKNOWN"
    confidence: str = "LOW"
    quarterly: List[NioAspQuarter] = Field(default_factory=list)


class NioDeliveryMomentumIntelligence(BaseModel):
    engine: str = "NIO Delivery Momentum Engine"
    engine_id: str = "DE-NIO-DM-001.0"
    version: str = "0.1.0"
    methodology: str
    latest_period: str
    score: float = Field(ge=0, le=100)
    business_momentum_score: float = Field(ge=0, le=100)
    regime: str
    trend: str
    confidence: str
    components: Dict[str, dict] = Field(default_factory=dict)
    evidence: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)


class NioDeliveryResponse(BaseModel):
    symbol: str = "NIO"
    engine: str = "NIO Delivery Intelligence"
    engine_id: str = "DE-CI-NIO-001.0"
    version: str = "0.2.0"
    status: str = "operational"
    dataset_source: str = "Deliveries.xlsx"
    snapshot: NioDeliverySnapshot
    intelligence: NioDeliveryIntelligence
    asp_intelligence: Optional[NioAspIntelligence] = None
    delivery_momentum: Optional[NioDeliveryMomentumIntelligence] = None
    monthly: List[NioMonthlyDeliveryRecord]
