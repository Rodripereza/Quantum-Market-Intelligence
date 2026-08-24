"""QMI Volume & Participation Engine."""

from __future__ import annotations

import pandas as pd

from app.indicators import (
    calculate_adl,
    calculate_atr,
    calculate_obv,
    calculate_relative_volume,
    calculate_volume_zscore,
)
from app.services.technical.scoring.models import (
    VolumeComponent,
    VolumeScoreResult,
)


class VolumeScoringError(ValueError):
    """Raised when the QMI Volume Engine cannot calculate a result."""


class VolumeScoreEngine:
    """Measure participation and directional volume confirmation."""

    MIN_OBSERVATIONS = 60

    WEIGHTS = {
        "relative_volume": 0.25,
        "obv": 0.20,
        "price_volume": 0.20,
        "adl": 0.15,
        "volume_trend": 0.10,
        "breakout_volume": 0.10,
    }

    def calculate(self, market_data: pd.DataFrame) -> VolumeScoreResult:
        self._validate(market_data)

        close = pd.to_numeric(market_data["Close"], errors="coerce")
        volume = pd.to_numeric(market_data["Volume"], errors="coerce")
        atr14 = calculate_atr(market_data, period=14)
        rvol20 = calculate_relative_volume(market_data, period=20)
        z20 = calculate_volume_zscore(market_data, period=20)
        obv = calculate_obv(market_data)
        adl = calculate_adl(market_data)

        latest_close = self._latest(close)
        latest_volume = self._latest(volume)
        latest_rvol = self._latest(rvol20)
        latest_z = self._latest(z20)
        latest_atr = self._latest(atr14)

        if None in (latest_close, latest_volume, latest_rvol, latest_z, latest_atr):
            raise VolumeScoringError("Insufficient data for volume analysis.")

        price_return = self._price_return(close, 1)
        atr_pct = 0.0 if latest_close == 0 else latest_atr / latest_close * 100.0

        rvol_score = self._rvol_score(
            latest_rvol,
            price_return,
            atr_pct,
        )

        obv_score, obv_state, obv_slope_5, obv_slope_20 = self._obv_score(obv)
        price_volume_score, ud_ratio, pv_state = self._price_volume_score(
            close, volume
        )
        adl_score, adl_state, adl_slope = self._adl_score(adl)
        volume_trend_score, volume_trend_value, volume_trend_state = (
            self._volume_trend_score(volume, close)
        )
        breakout_score, breakout_state, false_breakout_risk = (
            self._breakout_volume_score(
                close=close,
                volume=volume,
                rvol=latest_rvol,
                volume_z=latest_z,
                obv=obv,
                adl=adl,
            )
        )

        divergence_type, divergence_strength = self._detect_volume_divergence(
            close=close,
            obv=obv,
        )

        dry_up = self._dry_up(rvol20)
        climax = self._climax(
            price_return=price_return,
            atr_pct=atr_pct,
            volume_z=latest_z,
        )

        participation_score = self._participation_score(
            relative_volume=latest_rvol,
            volume_z=latest_z,
            volume_trend=volume_trend_value,
        )

        components = {
            "relative_volume": VolumeComponent(
                "relative_volume",
                rvol_score,
                self.WEIGHTS["relative_volume"],
                latest_rvol,
                f"RVOL_{latest_rvol:.2f}",
            ),
            "obv": VolumeComponent(
                "obv",
                obv_score,
                self.WEIGHTS["obv"],
                self._latest(obv),
                obv_state,
            ),
            "price_volume": VolumeComponent(
                "price_volume",
                price_volume_score,
                self.WEIGHTS["price_volume"],
                ud_ratio,
                pv_state,
            ),
            "adl": VolumeComponent(
                "adl",
                adl_score,
                self.WEIGHTS["adl"],
                self._latest(adl),
                adl_state,
            ),
            "volume_trend": VolumeComponent(
                "volume_trend",
                volume_trend_score,
                self.WEIGHTS["volume_trend"],
                volume_trend_value,
                volume_trend_state,
            ),
            "breakout_volume": VolumeComponent(
                "breakout_volume",
                breakout_score,
                self.WEIGHTS["breakout_volume"],
                latest_rvol,
                breakout_state,
            ),
        }

        score = sum(component.contribution for component in components.values())

        # Divergence is a contextual adjustment, capped to avoid dominating.
        if divergence_type == "REGULAR_BULLISH":
            score += min(10.0, divergence_strength * 0.10)
        elif divergence_type == "REGULAR_BEARISH":
            score -= min(10.0, divergence_strength * 0.10)

        score = max(-100.0, min(100.0, score))

        confidence = self._confidence(
            components=components,
            participation_score=participation_score,
            price_return=price_return,
            data_quality=self._data_quality(market_data),
        )

        return VolumeScoreResult(
            score=score,
            state=self._state(score),
            direction=self._direction(score),
            confidence=confidence,
            participation_score=participation_score,
            relative_volume=latest_rvol,
            volume_zscore=latest_z,
            up_down_ratio=ud_ratio,
            obv=self._latest(obv) or 0.0,
            obv_slope_5=obv_slope_5,
            obv_slope_20=obv_slope_20,
            adl=self._latest(adl) or 0.0,
            adl_slope=adl_slope,
            volume_trend=volume_trend_value,
            dry_up=dry_up,
            climax=climax,
            divergence_type=divergence_type,
            divergence_strength=divergence_strength,
            breakout_confirmation=breakout_state,
            false_breakout_risk=false_breakout_risk,
            data_quality=self._data_quality(market_data),
            components=components,
            observations_available=len(market_data),
        )

    @staticmethod
    def _rvol_score(rvol: float, price_return: float, atr_pct: float) -> float:
        if rvol < 0.5:
            magnitude = 10.0
        elif rvol < 0.8:
            magnitude = 20.0
        elif rvol < 1.2:
            magnitude = 35.0
        elif rvol < 1.5:
            magnitude = 50.0
        elif rvol < 2.0:
            magnitude = 70.0
        elif rvol < 3.0:
            magnitude = 85.0
        else:
            magnitude = 100.0

        direction = 1.0 if price_return > 0 else -1.0 if price_return < 0 else 0.0

        if atr_pct <= 0:
            impact_factor = 0.5
        else:
            impact_ratio = abs(price_return) / atr_pct
            impact_factor = max(0.5, min(1.0, impact_ratio))

        return magnitude * direction * impact_factor

    @staticmethod
    def _obv_score(obv: pd.Series) -> tuple[float, str, float, float]:
        valid = pd.to_numeric(obv, errors="coerce").dropna()
        if len(valid) < 21:
            return 0.0, "INSUFFICIENT", 0.0, 0.0

        current = float(valid.iloc[-1])
        slope_5 = current - float(valid.iloc[-6])
        slope_20 = current - float(valid.iloc[-21])
        ema20 = valid.ewm(span=20, adjust=False).mean()
        above_ema = current > float(ema20.iloc[-1])

        score = 0.0
        score += 30.0 if slope_5 > 0 else -30.0
        score += 30.0 if slope_20 > 0 else -30.0
        score += 20.0 if above_ema else -20.0

        recent = valid.iloc[-60:] if len(valid) >= 60 else valid
        if current >= float(recent.max()):
            score += 20.0
            state = "NEW_HIGH"
        elif current <= float(recent.min()):
            score -= 20.0
            state = "NEW_LOW"
        else:
            state = "RISING" if score > 0 else "FALLING" if score < 0 else "FLAT"

        return max(-100.0, min(100.0, score)), state, slope_5, slope_20

    @staticmethod
    def _price_volume_score(
        close: pd.Series,
        volume: pd.Series,
    ) -> tuple[float, float | None, str]:
        returns = close.pct_change()
        recent_returns = returns.iloc[-20:]
        recent_volume = volume.iloc[-20:]

        up_volume = float(recent_volume[recent_returns > 0].sum())
        down_volume = float(recent_volume[recent_returns < 0].sum())

        ratio = None if down_volume == 0 else up_volume / down_volume

        price_change_20 = float(close.iloc[-1] / close.iloc[-21] - 1.0)

        if ratio is None:
            score = 70.0 if price_change_20 > 0 else -70.0 if price_change_20 < 0 else 0.0
        elif ratio >= 1.5:
            score = 70.0
        elif ratio >= 1.1:
            score = 35.0
        elif ratio <= 0.67:
            score = -70.0
        elif ratio <= 0.9:
            score = -35.0
        else:
            score = 0.0

        # Price alignment modifier
        if price_change_20 > 0 and score < 0:
            score *= 0.5
            state = "PRICE_UP_VOLUME_WEAK"
        elif price_change_20 < 0 and score > 0:
            score *= 0.5
            state = "PRICE_DOWN_VOLUME_SUPPORT"
        else:
            state = "CONFIRMED" if abs(score) >= 35 else "NEUTRAL"

        return score, ratio, state

    @staticmethod
    def _adl_score(adl: pd.Series) -> tuple[float, str, float]:
        valid = pd.to_numeric(adl, errors="coerce").dropna()
        if len(valid) < 21:
            return 0.0, "INSUFFICIENT", 0.0

        current = float(valid.iloc[-1])
        slope_20 = current - float(valid.iloc[-21])
        ema20 = valid.ewm(span=20, adjust=False).mean()
        above = current > float(ema20.iloc[-1])

        score = 60.0 if slope_20 > 0 else -60.0
        score += 20.0 if above else -20.0
        score = max(-100.0, min(100.0, score))

        return score, "RISING" if score > 0 else "FALLING", slope_20

    @staticmethod
    def _volume_trend_score(
        volume: pd.Series,
        close: pd.Series,
    ) -> tuple[float, float, str]:
        sma20 = volume.rolling(20, min_periods=20).mean()
        sma50 = volume.rolling(50, min_periods=50).mean()

        latest20 = VolumeScoreEngine._latest(sma20)
        latest50 = VolumeScoreEngine._latest(sma50)
        if latest20 is None or latest50 is None or latest50 == 0:
            return 0.0, 0.0, "INSUFFICIENT"

        trend = (latest20 - latest50) / latest50 * 100.0
        price_change_20 = float(close.iloc[-1] / close.iloc[-21] - 1.0)

        magnitude = min(100.0, abs(trend) * 5.0)
        direction = 1.0 if price_change_20 > 0 else -1.0 if price_change_20 < 0 else 0.0
        score = magnitude * direction

        if trend > 20:
            state = "STRONGLY_INCREASING"
        elif trend > 5:
            state = "INCREASING"
        elif trend < -20:
            state = "STRONGLY_DECREASING"
        elif trend < -5:
            state = "DECREASING"
        else:
            state = "STABLE"

        return score, trend, state

    @staticmethod
    def _breakout_volume_score(
        close: pd.Series,
        volume: pd.Series,
        rvol: float,
        volume_z: float,
        obv: pd.Series,
        adl: pd.Series,
    ) -> tuple[float, str, bool]:
        if len(close) < 21:
            return 0.0, "NOT_EVALUATED", False

        prior_high = float(close.iloc[-21:-1].max())
        prior_low = float(close.iloc[-21:-1].min())
        current = float(close.iloc[-1])

        obv_rising = (float(obv.iloc[-1]) - float(obv.iloc[-6])) > 0
        adl_rising = (float(adl.iloc[-1]) - float(adl.iloc[-6])) > 0

        if current > prior_high:
            quality = 0.0
            quality += 35.0 if rvol >= 1.5 else 15.0 if rvol >= 1.0 else -20.0
            quality += 25.0 if volume_z >= 2 else 10.0 if volume_z >= 1 else 0.0
            quality += 20.0 if obv_rising else -10.0
            quality += 20.0 if adl_rising else -10.0
            false_risk = rvol < 1.0 or (not obv_rising and not adl_rising)
            return max(-100.0, min(100.0, quality)), "BULLISH_BREAKOUT", false_risk

        if current < prior_low:
            quality = 0.0
            quality += 35.0 if rvol >= 1.5 else 15.0 if rvol >= 1.0 else -20.0
            quality += 25.0 if volume_z >= 2 else 10.0 if volume_z >= 1 else 0.0
            quality += 20.0 if not obv_rising else -10.0
            quality += 20.0 if not adl_rising else -10.0
            false_risk = rvol < 1.0 or (obv_rising and adl_rising)
            return -max(-100.0, min(100.0, quality)), "BEARISH_BREAKOUT", false_risk

        return 0.0, "NO_BREAKOUT", False

    @staticmethod
    def _detect_volume_divergence(
        close: pd.Series,
        obv: pd.Series,
    ) -> tuple[str, float]:
        if len(close) < 45 or len(obv) < 45:
            return "NONE", 0.0

        p1 = close.iloc[-40:-20]
        p2 = close.iloc[-20:]
        o1 = obv.iloc[-40:-20]
        o2 = obv.iloc[-20:]

        p1_low, p2_low = float(p1.min()), float(p2.min())
        p1_high, p2_high = float(p1.max()), float(p2.max())
        o1_low, o2_low = float(o1.min()), float(o2.min())
        o1_high, o2_high = float(o1.max()), float(o2.max())

        if p2_low < p1_low and o2_low > o1_low:
            price_pct = abs((p2_low / p1_low - 1.0) * 100.0)
            obv_pct = abs((o2_low - o1_low) / (abs(o1_low) + 1.0) * 100.0)
            strength = min(100.0, price_pct * 8.0 + min(60.0, obv_pct))
            return "REGULAR_BULLISH", strength

        if p2_high > p1_high and o2_high < o1_high:
            price_pct = abs((p2_high / p1_high - 1.0) * 100.0)
            obv_pct = abs((o2_high - o1_high) / (abs(o1_high) + 1.0) * 100.0)
            strength = min(100.0, price_pct * 8.0 + min(60.0, obv_pct))
            return "REGULAR_BEARISH", strength

        return "NONE", 0.0

    @staticmethod
    def _dry_up(rvol: pd.Series) -> bool:
        valid = pd.to_numeric(rvol, errors="coerce").dropna()
        if len(valid) < 3:
            return False
        return bool((valid.iloc[-3:] < 0.6).all())

    @staticmethod
    def _climax(price_return: float, atr_pct: float, volume_z: float) -> str:
        if atr_pct <= 0 or volume_z < 3:
            return "NONE"

        if abs(price_return) >= 2.0 * atr_pct:
            return "BUYING_CLIMAX" if price_return > 0 else "SELLING_CLIMAX"

        return "NONE"

    @staticmethod
    def _participation_score(
        relative_volume: float,
        volume_z: float,
        volume_trend: float,
    ) -> float:
        rvol_component = min(100.0, max(0.0, relative_volume / 3.0 * 100.0))
        z_component = min(100.0, max(0.0, (volume_z + 1.0) / 4.0 * 100.0))
        trend_component = min(100.0, abs(volume_trend) * 3.0)
        return max(
            0.0,
            min(
                100.0,
                0.50 * rvol_component
                + 0.30 * z_component
                + 0.20 * trend_component,
            ),
        )

    @staticmethod
    def _confidence(
        components: dict[str, VolumeComponent],
        participation_score: float,
        price_return: float,
        data_quality: float,
    ) -> float:
        directional = [
            component.score
            for component in components.values()
            if abs(component.score) >= 10
        ]

        if directional:
            positive = sum(value > 0 for value in directional)
            negative = sum(value < 0 for value in directional)
            agreement = 100.0 * max(positive, negative) / len(directional)
        else:
            agreement = 50.0

        temporal_consistency = 70.0
        price_alignment = 100.0 if abs(price_return) > 0 else 60.0

        confidence = (
            0.30 * agreement
            + 0.25 * participation_score
            + 0.20 * temporal_consistency
            + 0.15 * price_alignment
            + 0.10 * data_quality
        )

        # Correlation penalty: OBV and ADL are related evidence.
        obv = components["obv"].score
        adl = components["adl"].score
        if abs(obv) >= 40 and abs(adl) >= 40 and (obv > 0) == (adl > 0):
            confidence -= 5.0

        return max(0.0, min(100.0, confidence))

    @staticmethod
    def _state(score: float) -> str:
        if score >= 70:
            return "STRONG_POTENTIAL_ACCUMULATION"
        if score >= 35:
            return "POTENTIAL_ACCUMULATION"
        if score >= 15:
            return "MILD_BUYING_PRESSURE"
        if score > -15:
            return "NEUTRAL"
        if score > -35:
            return "MILD_SELLING_PRESSURE"
        if score > -70:
            return "POTENTIAL_DISTRIBUTION"
        return "STRONG_POTENTIAL_DISTRIBUTION"

    @staticmethod
    def _direction(score: float) -> str:
        if score >= 15:
            return "BULLISH"
        if score <= -15:
            return "BEARISH"
        return "NEUTRAL"

    @staticmethod
    def _price_return(close: pd.Series, sessions: int) -> float:
        if len(close) <= sessions:
            return 0.0
        previous = float(close.iloc[-1 - sessions])
        current = float(close.iloc[-1])
        if previous == 0:
            return 0.0
        return (current / previous - 1.0) * 100.0

    @staticmethod
    def _data_quality(market_data: pd.DataFrame) -> float:
        numeric = market_data[["High", "Low", "Close", "Volume"]].apply(
            pd.to_numeric, errors="coerce"
        )
        completeness = 100.0 * (1.0 - numeric.isna().mean().mean())
        length_quality = min(100.0, len(market_data) / 252.0 * 100.0)
        return max(
            0.0,
            min(100.0, 0.8 * completeness + 0.2 * length_quality),
        )

    @staticmethod
    def _latest(series: pd.Series) -> float | None:
        valid = pd.to_numeric(series, errors="coerce").dropna()
        return None if valid.empty else float(valid.iloc[-1])

    @staticmethod
    def _validate(market_data: pd.DataFrame) -> None:
        if not isinstance(market_data, pd.DataFrame) or market_data.empty:
            raise VolumeScoringError(
                "market_data must be a non-empty pandas DataFrame."
            )

        if len(market_data) < VolumeScoreEngine.MIN_OBSERVATIONS:
            raise VolumeScoringError(
                f"Volume Score requires at least "
                f"{VolumeScoreEngine.MIN_OBSERVATIONS} observations; "
                f"received {len(market_data)}."
            )

        missing = {"High", "Low", "Close", "Volume"}.difference(
            market_data.columns
        )
        if missing:
            raise VolumeScoringError(
                "Volume Score requires columns: "
                + ", ".join(sorted(missing))
            )


volume_score_engine = VolumeScoreEngine()
