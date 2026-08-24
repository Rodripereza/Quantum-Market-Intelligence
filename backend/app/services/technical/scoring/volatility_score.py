"""QMI Volatility Engine."""

from __future__ import annotations

import pandas as pd

from app.indicators import (
    calculate_atr,
    calculate_bollinger_bandwidth,
    calculate_historical_volatility,
)
from app.services.technical.scoring.models import (
    VolatilityComponent,
    VolatilityScoreResult,
)


class VolatilityScoringError(ValueError):
    """Raised when the QMI Volatility Engine cannot calculate a result."""


class VolatilityScoreEngine:
    """Measure level, direction and phase of volatility."""

    MIN_OBSERVATIONS = 80

    WEIGHTS = {
        "atr_normalized": 0.30,
        "historical_volatility": 0.25,
        "bollinger_bandwidth": 0.20,
        "volatility_percentile": 0.15,
        "volatility_acceleration": 0.10,
    }

    def calculate(self, market_data: pd.DataFrame) -> VolatilityScoreResult:
        self._validate(market_data)

        close = pd.to_numeric(market_data["Close"], errors="coerce")
        atr14 = calculate_atr(market_data, period=14)
        hv20 = calculate_historical_volatility(market_data, period=20)
        hv60 = calculate_historical_volatility(market_data, period=60)
        bb = calculate_bollinger_bandwidth(market_data, period=20)

        latest_close = self._latest(close)
        latest_atr = self._latest(atr14)
        latest_hv20 = self._latest(hv20)
        latest_hv60 = self._latest(hv60)
        latest_bbw = self._latest(bb["BB_WIDTH_20"])

        if None in (latest_close, latest_atr, latest_hv20, latest_hv60, latest_bbw):
            raise VolatilityScoringError("Insufficient volatility data.")

        atr_normalized_series = (atr14 / close * 100.0).replace([float("inf"), -float("inf")], pd.NA)
        atr_normalized = self._latest(atr_normalized_series)
        if atr_normalized is None:
            raise VolatilityScoringError("Unable to calculate normalized ATR.")

        atr_percentile = self._percentile(atr_normalized_series, atr_normalized)
        hv_percentile = self._percentile(hv20, latest_hv20)
        bbw_percentile = self._percentile(bb["BB_WIDTH_20"], latest_bbw)

        hv_ratio = None if latest_hv60 == 0 else latest_hv20 / latest_hv60

        # Build historical composite score series for deltas.
        score_series = self._composite_history(
            close=close,
            atr14=atr14,
            hv20=hv20,
            hv60=hv60,
            bbw=bb["BB_WIDTH_20"],
        )
        score = self._latest(score_series)
        if score is None:
            raise VolatilityScoringError("Unable to calculate Volatility Score.")

        score_5 = self._lagged(score_series, 5)
        score_10 = self._lagged(score_series, 10)
        delta_5 = None if score_5 is None else score - score_5
        delta_10 = None if score_10 is None else score - score_10

        direction = self._direction(delta_5)
        compression = (
            bbw_percentile < 20
            and atr_percentile < 30
            and hv_percentile < 30
        )
        expansion = (
            delta_5 is not None
            and delta_5 >= 10
            and bbw_percentile >= 50
        )

        components = {
            "atr_normalized": VolatilityComponent(
                "atr_normalized",
                atr_percentile,
                self.WEIGHTS["atr_normalized"],
                atr_normalized,
                f"ATR_PCTL_{atr_percentile:.1f}",
            ),
            "historical_volatility": VolatilityComponent(
                "historical_volatility",
                hv_percentile,
                self.WEIGHTS["historical_volatility"],
                latest_hv20,
                f"HV20_PCTL_{hv_percentile:.1f}",
            ),
            "bollinger_bandwidth": VolatilityComponent(
                "bollinger_bandwidth",
                bbw_percentile,
                self.WEIGHTS["bollinger_bandwidth"],
                latest_bbw,
                f"BBW_PCTL_{bbw_percentile:.1f}",
            ),
            "volatility_percentile": VolatilityComponent(
                "volatility_percentile",
                (atr_percentile + hv_percentile + bbw_percentile) / 3.0,
                self.WEIGHTS["volatility_percentile"],
                None,
                "COMPOSITE_PERCENTILE",
            ),
            "volatility_acceleration": VolatilityComponent(
                "volatility_acceleration",
                self._acceleration_score(delta_5),
                self.WEIGHTS["volatility_acceleration"],
                delta_5,
                direction,
            ),
        }

        confidence = self._confidence(
            atr_percentile=atr_percentile,
            hv_percentile=hv_percentile,
            bbw_percentile=bbw_percentile,
            data_quality=self._data_quality(market_data),
        )

        return VolatilityScoreResult(
            score=score,
            state=self._state(score, compression),
            direction=direction,
            confidence=confidence,
            risk_environment=self._risk_environment(score),
            atr_normalized=atr_normalized,
            atr_percentile=atr_percentile,
            historical_volatility_20=latest_hv20,
            historical_volatility_60=latest_hv60,
            hv_ratio=hv_ratio,
            bollinger_bandwidth=latest_bbw,
            bandwidth_percentile=bbw_percentile,
            volatility_delta_5=delta_5,
            volatility_delta_10=delta_10,
            compression=compression,
            expansion=expansion,
            data_quality=self._data_quality(market_data),
            components=components,
            observations_available=len(market_data),
        )

    def _composite_history(self, close, atr14, hv20, hv60, bbw):
        atrn = (atr14 / close * 100.0).replace([float("inf"), -float("inf")], pd.NA)

        rows = []
        for idx in range(len(close)):
            if idx < 60:
                rows.append(float("nan"))
                continue

            a = atrn.iloc[: idx + 1]
            h = hv20.iloc[: idx + 1]
            b = bbw.iloc[: idx + 1]

            av = self._latest(a)
            hv = self._latest(h)
            bv = self._latest(b)
            if av is None or hv is None or bv is None:
                rows.append(float("nan"))
                continue

            ap = self._percentile(a, av)
            hp = self._percentile(h, hv)
            bp = self._percentile(b, bv)

            composite_pct = (ap + hp + bp) / 3.0
            acceleration_proxy = 50.0
            rows.append(
                ap * self.WEIGHTS["atr_normalized"]
                + hp * self.WEIGHTS["historical_volatility"]
                + bp * self.WEIGHTS["bollinger_bandwidth"]
                + composite_pct * self.WEIGHTS["volatility_percentile"]
                + acceleration_proxy * self.WEIGHTS["volatility_acceleration"]
            )

        result = pd.Series(rows, index=close.index, dtype="float64")
        # Now replace proxy acceleration with delta-based score.
        base = result.copy()
        for idx in range(len(result)):
            if idx < 65 or pd.isna(base.iloc[idx]) or pd.isna(base.iloc[idx - 5]):
                continue
            delta = float(base.iloc[idx] - base.iloc[idx - 5])
            accel_score = self._acceleration_score(delta)
            # remove proxy 50 and add actual acceleration contribution
            result.iloc[idx] = (
                float(base.iloc[idx])
                - 50.0 * self.WEIGHTS["volatility_acceleration"]
                + accel_score * self.WEIGHTS["volatility_acceleration"]
            )

        return result.clip(lower=0.0, upper=100.0)

    @staticmethod
    def _percentile(series: pd.Series, value: float) -> float:
        valid = pd.to_numeric(series, errors="coerce").dropna()
        if valid.empty:
            return 50.0
        history = valid.iloc[-252:] if len(valid) > 252 else valid
        return 100.0 * float((history <= value).mean())

    @staticmethod
    def _acceleration_score(delta_5: float | None) -> float:
        if delta_5 is None:
            return 50.0
        if delta_5 <= -20:
            return 0.0
        if delta_5 >= 20:
            return 100.0
        return 50.0 + delta_5 * 2.5

    @staticmethod
    def _direction(delta_5: float | None) -> str:
        if delta_5 is None:
            return "UNKNOWN"
        if delta_5 >= 20:
            return "RAPID_EXPANSION"
        if delta_5 >= 10:
            return "EXPANDING"
        if delta_5 > 5:
            return "SLIGHT_EXPANSION"
        if delta_5 <= -20:
            return "RAPID_CONTRACTION"
        if delta_5 <= -10:
            return "CONTRACTING"
        if delta_5 < -5:
            return "SLIGHT_CONTRACTION"
        return "STABLE"

    @staticmethod
    def _state(score: float, compression: bool) -> str:
        if compression:
            return "COMPRESSED"
        if score >= 80:
            return "EXTREME"
        if score >= 60:
            return "HIGH"
        if score >= 40:
            return "NORMAL"
        if score >= 20:
            return "LOW"
        return "VERY_LOW"

    @staticmethod
    def _risk_environment(score: float) -> str:
        if score >= 85:
            return "EXTREME"
        if score >= 70:
            return "STRESSED"
        if score >= 55:
            return "ELEVATED"
        if score >= 30:
            return "NORMAL"
        return "CALM"

    @staticmethod
    def _confidence(atr_percentile, hv_percentile, bbw_percentile, data_quality):
        values = [atr_percentile, hv_percentile, bbw_percentile]
        spread = max(values) - min(values)
        agreement = max(0.0, 100.0 - spread)
        return max(
            0.0,
            min(100.0, 0.65 * agreement + 0.35 * data_quality),
        )

    @staticmethod
    def _data_quality(market_data):
        numeric = market_data[["High", "Low", "Close"]].apply(
            pd.to_numeric, errors="coerce"
        )
        completeness = 100.0 * (1.0 - numeric.isna().mean().mean())
        length_quality = min(100.0, len(market_data) / 252.0 * 100.0)
        return max(0.0, min(100.0, 0.8 * completeness + 0.2 * length_quality))

    @staticmethod
    def _latest(series):
        valid = pd.to_numeric(series, errors="coerce").dropna()
        return None if valid.empty else float(valid.iloc[-1])

    @staticmethod
    def _lagged(series, periods):
        valid = pd.to_numeric(series, errors="coerce").dropna()
        return None if len(valid) <= periods else float(valid.iloc[-1 - periods])

    @staticmethod
    def _validate(market_data):
        if not isinstance(market_data, pd.DataFrame) or market_data.empty:
            raise VolatilityScoringError(
                "market_data must be a non-empty pandas DataFrame."
            )
        if len(market_data) < VolatilityScoreEngine.MIN_OBSERVATIONS:
            raise VolatilityScoringError(
                f"Volatility Score requires at least "
                f"{VolatilityScoreEngine.MIN_OBSERVATIONS} observations; "
                f"received {len(market_data)}."
            )
        missing = {"High", "Low", "Close"}.difference(market_data.columns)
        if missing:
            raise VolatilityScoringError(
                "Volatility Score requires columns: "
                + ", ".join(sorted(missing))
            )


volatility_score_engine = VolatilityScoreEngine()
