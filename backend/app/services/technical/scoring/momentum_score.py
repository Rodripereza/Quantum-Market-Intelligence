"""QMI contextual Momentum Score Engine."""

from __future__ import annotations

import pandas as pd

from app.indicators import (
    calculate_atr,
    calculate_macd,
    calculate_roc,
    calculate_rsi,
    calculate_stochastic,
)
from app.services.technical.scoring.models import (
    MomentumComponent,
    MomentumScoreResult,
    RegimeResult,
)


class MomentumScoringError(ValueError):
    """Raised when the contextual Momentum Score cannot be calculated."""


class MomentumScoreEngine:
    """Interpret momentum according to QMI market context."""

    MIN_OBSERVATIONS = 60

    STRONG_TREND_WEIGHTS = {
        "rsi": 0.25,
        "macd": 0.35,
        "stochastic": 0.10,
        "roc": 0.20,
        "divergence": 0.10,
    }
    RANGE_WEIGHTS = {
        "rsi": 0.35,
        "macd": 0.20,
        "stochastic": 0.25,
        "roc": 0.10,
        "divergence": 0.10,
    }
    DEFAULT_WEIGHTS = {
        "rsi": 0.30,
        "macd": 0.30,
        "stochastic": 0.15,
        "roc": 0.15,
        "divergence": 0.10,
    }

    def calculate(self, market_data: pd.DataFrame, regime: RegimeResult) -> MomentumScoreResult:
        self._validate(market_data)
        if regime is None:
            raise MomentumScoringError("Market regime result is required.")

        rsi = calculate_rsi(market_data, period=14)
        macd = calculate_macd(market_data)
        stoch = calculate_stochastic(market_data, k_period=14, d_period=3)
        roc20 = calculate_roc(market_data, period=20)
        atr14 = calculate_atr(market_data, period=14)

        rsi_value = self._latest(rsi)
        rsi_5 = self._lagged(rsi, 5)
        if rsi_value is None:
            raise MomentumScoringError("Insufficient data for RSI.")

        rsi_score, rsi_state = self._score_rsi(
            rsi_value,
            None if rsi_5 is None else rsi_value - rsi_5,
            regime.primary_regime,
        )
        macd_score, macd_state = self._score_macd(macd, atr14)
        stochastic_score, stochastic_state = self._score_stochastic(
            stoch, regime.primary_regime
        )
        roc_score, roc_state = self._score_roc(roc20)
        divergence_type, divergence_strength, divergence_score = self._detect_divergence(
            market_data, rsi
        )

        weights = self._weights_for_regime(regime.primary_regime)
        components = {
            "rsi": MomentumComponent("rsi", rsi_score, weights["rsi"], rsi_value, rsi_state),
            "macd": MomentumComponent(
                "macd", macd_score, weights["macd"],
                self._latest(macd["MACD_HISTOGRAM"]), macd_state
            ),
            "stochastic": MomentumComponent(
                "stochastic", stochastic_score, weights["stochastic"],
                self._latest(stoch["STOCH_K_14"]), stochastic_state
            ),
            "roc": MomentumComponent(
                "roc", roc_score, weights["roc"], self._latest(roc20), roc_state
            ),
            "divergence": MomentumComponent(
                "divergence", divergence_score, weights["divergence"],
                divergence_strength, divergence_type
            ),
        }

        score = max(-100.0, min(100.0, sum(c.contribution for c in components.values())))
        delta_5 = self._historical_delta(market_data, regime, 5, score)
        delta_10 = self._historical_delta(market_data, regime, 10, score)

        return MomentumScoreResult(
            score=score,
            state=self._state_label(score, delta_5),
            confidence=self._confidence(
                components, regime, divergence_type, divergence_strength
            ),
            regime_context=regime.primary_regime,
            momentum_delta_5=delta_5,
            momentum_delta_10=delta_10,
            acceleration=self._acceleration_label(score, delta_5),
            divergence_type=divergence_type,
            divergence_strength=divergence_strength,
            data_quality=self._data_quality(market_data),
            weights=weights,
            components=components,
            observations_available=len(market_data),
        )

    def _historical_delta(self, market_data, regime, sessions, current_score):
        if len(market_data) <= self.MIN_OBSERVATIONS + sessions:
            return None
        try:
            old = self._component_score_only(market_data.iloc[:-sessions], regime)
            return current_score - old
        except Exception:
            return None

    def _component_score_only(self, market_data, regime):
        rsi = calculate_rsi(market_data, period=14)
        macd = calculate_macd(market_data)
        stoch = calculate_stochastic(market_data, k_period=14, d_period=3)
        roc20 = calculate_roc(market_data, period=20)
        atr14 = calculate_atr(market_data, period=14)

        rsi_value = self._latest(rsi)
        lag5 = self._lagged(rsi, 5)
        if rsi_value is None:
            raise MomentumScoringError("Insufficient historical RSI.")
        rsi_score, _ = self._score_rsi(
            rsi_value,
            None if lag5 is None else rsi_value - lag5,
            regime.primary_regime,
        )
        macd_score, _ = self._score_macd(macd, atr14)
        stoch_score, _ = self._score_stochastic(stoch, regime.primary_regime)
        roc_score, _ = self._score_roc(roc20)
        _, _, div_score = self._detect_divergence(market_data, rsi)
        w = self._weights_for_regime(regime.primary_regime)
        return max(-100.0, min(100.0,
            rsi_score*w["rsi"] + macd_score*w["macd"]
            + stoch_score*w["stochastic"] + roc_score*w["roc"]
            + div_score*w["divergence"]
        ))

    @staticmethod
    def _weights_for_regime(regime):
        if regime in {"STRONG_BULL", "STRONG_BEAR"}:
            return dict(MomentumScoreEngine.STRONG_TREND_WEIGHTS)
        if regime == "RANGE":
            return dict(MomentumScoreEngine.RANGE_WEIGHTS)
        return dict(MomentumScoreEngine.DEFAULT_WEIGHTS)

    @staticmethod
    def _score_rsi(rsi_value, rsi_delta_5, regime):
        if regime == "STRONG_BULL":
            points = [(0,-50),(30,-50),(40,-20),(50,10),(60,35),(70,65),(80,80),(85,55),(100,20)]
        elif regime in {"BULL","WEAK_BULL"}:
            points = [(0,-40),(30,-40),(40,-15),(50,10),(60,35),(70,60),(80,55),(100,20)]
        elif regime == "RANGE":
            points = [(0,70),(20,70),(30,55),(40,30),(50,0),(60,0),(70,-30),(80,-55),(100,-70)]
        elif regime == "STRONG_BEAR":
            points = [(0,-25),(20,-25),(30,-70),(40,-75),(50,-45),(60,-15),(100,20)]
        else:
            points = [(0,-20),(20,-20),(30,-55),(40,-60),(50,-35),(60,-10),(70,15),(100,30)]

        base = MomentumScoreEngine._interpolate(rsi_value, points)
        modifier = 0.0
        if rsi_delta_5 is not None:
            modifier = MomentumScoreEngine._interpolate(
                rsi_delta_5,
                [(-30,-20),(-15,-20),(-8,-12),(-3,-5),(3,0),(8,5),(15,12),(30,20)]
            )
        score = max(-100.0, min(100.0, base + modifier))
        state = "RISING" if (rsi_delta_5 or 0) > 3 else "FALLING" if (rsi_delta_5 or 0) < -3 else "STABLE"
        return score, f"{state}_RSI_{rsi_value:.1f}"

    @staticmethod
    def _score_macd(macd, atr14):
        line = MomentumScoreEngine._latest(macd["MACD_12_26"])
        signal = MomentumScoreEngine._latest(macd["MACD_SIGNAL_9"])
        hist = MomentumScoreEngine._latest(macd["MACD_HISTOGRAM"])
        hist3 = MomentumScoreEngine._lagged(macd["MACD_HISTOGRAM"], 3)
        atr = MomentumScoreEngine._latest(atr14)
        if None in (line, signal, hist) or atr is None or atr <= 0:
            return 0.0, "INSUFFICIENT"

        norm_hist = max(-3.0, min(3.0, hist / atr))
        magnitude = min(15.0, abs(norm_hist) / 3.0 * 15.0)
        score = (30.0 if line > signal else -30.0)
        score += 20.0 if line > 0 else -20.0
        score += 20.0 if hist > 0 else -20.0

        if hist3 is not None:
            delta = hist - hist3
            if delta > 0:
                score += 15.0
                state = "ACCELERATING_BULLISH" if hist >= 0 else "BEARISH_DECELERATING"
            elif delta < 0:
                score -= 15.0
                state = "ACCELERATING_BEARISH" if hist <= 0 else "BULLISH_DECELERATING"
            else:
                state = "STABLE"
        else:
            state = "UNKNOWN"

        score += magnitude if hist > 0 else -magnitude
        return max(-100.0, min(100.0, score)), state

    @staticmethod
    def _score_stochastic(stoch, regime):
        k = MomentumScoreEngine._latest(stoch["STOCH_K_14"])
        d = MomentumScoreEngine._latest(stoch["STOCH_D_3"])
        k3 = MomentumScoreEngine._lagged(stoch["STOCH_K_14"], 3)
        if k is None or d is None:
            return 0.0, "INSUFFICIENT"

        cross_score = 25.0 if k > d else -25.0
        rising = k3 is not None and k > k3

        if regime == "RANGE":
            level = 50.0 if k < 20 else 35.0 if k < 30 else -50.0 if k > 80 else -35.0 if k > 70 else 0.0
        else:
            level = 35.0 if k >= 80 else 20.0 if k >= 60 else -35.0 if k <= 20 else -20.0 if k <= 40 else 0.0
            if regime in {"BEAR","WEAK_BEAR","STRONG_BEAR"}:
                level *= -1.0

        slope = 15.0 if rising else -15.0 if k3 is not None else 0.0
        score = max(-100.0, min(100.0, cross_score + level + slope))
        return score, "BULLISH_CROSS" if k > d else "BEARISH_CROSS"

    @staticmethod
    def _score_roc(roc20):
        valid = pd.to_numeric(roc20, errors="coerce").dropna()
        if valid.empty:
            return 0.0, "INSUFFICIENT"
        current = float(valid.iloc[-1])
        history = valid.iloc[-252:] if len(valid) > 252 else valid
        percentile = 100.0 * float((history <= current).mean())
        score = max(-100.0, min(100.0, (percentile - 50.0) * 2.0))
        state = "STRONG_POSITIVE" if score >= 60 else "POSITIVE" if score >= 20 else "NEUTRAL" if score > -20 else "NEGATIVE" if score > -60 else "STRONG_NEGATIVE"
        return score, f"{state}_PCTL_{percentile:.1f}"

    @staticmethod
    def _detect_divergence(market_data, rsi):
        if len(market_data) < 45:
            return "NONE", 0.0, 0.0
        close = pd.to_numeric(market_data["Close"], errors="coerce")
        rsi_num = pd.to_numeric(rsi, errors="coerce")
        prev_close, curr_close = close.iloc[-40:-20], close.iloc[-20:]
        prev_rsi, curr_rsi = rsi_num.iloc[-40:-20].dropna(), rsi_num.iloc[-20:].dropna()
        if prev_close.empty or curr_close.empty or prev_rsi.empty or curr_rsi.empty:
            return "NONE", 0.0, 0.0

        ph, ch = float(prev_close.max()), float(curr_close.max())
        pl, cl = float(prev_close.min()), float(curr_close.min())
        prh, crh = float(prev_rsi.max()), float(curr_rsi.max())
        prl, crl = float(prev_rsi.min()), float(curr_rsi.min())

        def strength(price_pct, osc_delta):
            return max(0.0, min(100.0,
                0.55 * min(100.0, abs(price_pct)*10.0)
                + 0.45 * min(100.0, abs(osc_delta)*4.0)
            ))

        if ch > ph and crh < prh:
            st = strength((ch/ph-1)*100, crh-prh)
            return "REGULAR_BEARISH", st, -st
        if cl < pl and crl > prl:
            st = strength((cl/pl-1)*100, crl-prl)
            return "REGULAR_BULLISH", st, st
        if cl > pl and crl < prl:
            st = strength((cl/pl-1)*100, crl-prl)
            return "HIDDEN_BULLISH", st, st*0.75
        if ch < ph and crh > prh:
            st = strength((ch/ph-1)*100, crh-prh)
            return "HIDDEN_BEARISH", st, -st*0.75
        return "NONE", 0.0, 0.0

    @staticmethod
    def _confidence(components, regime, divergence_type, divergence_strength):
        directional = [components[k].score for k in ("rsi","macd","stochastic","roc")]
        meaningful = [s for s in directional if abs(s) >= 10]
        if not meaningful:
            agreement = 50.0
        else:
            pos = sum(s > 0 for s in meaningful)
            neg = sum(s < 0 for s in meaningful)
            agreement = 100.0 * max(pos, neg) / len(meaningful)

        temporal = 70.0
        regime_alignment = float(regime.confidence)
        divergence_quality = 60.0 if divergence_type == "NONE" else divergence_strength
        confidence = (
            0.30*agreement + 0.25*temporal + 0.20*regime_alignment
            + 0.15*divergence_quality + 0.10*100.0
        )
        # Correlation penalty: oscillator unanimity is not independent evidence.
        if all(v > 20 for v in directional) or all(v < -20 for v in directional):
            confidence -= 5.0
        return max(0.0, min(100.0, confidence))

    @staticmethod
    def _state_label(score, delta_5):
        accel = delta_5 is not None and abs(delta_5) >= 8
        if score >= 70:
            return "STRONG_BULLISH_ACCELERATING" if accel and delta_5 > 0 else "STRONG_BULLISH"
        if score >= 20:
            if accel and delta_5 > 0: return "BULLISH_ACCELERATING"
            if accel and delta_5 < 0: return "BULLISH_DECELERATING"
            return "BULLISH_STABLE"
        if score > -20:
            return "NEUTRAL"
        if score > -70:
            if accel and delta_5 < 0: return "BEARISH_ACCELERATING"
            if accel and delta_5 > 0: return "BEARISH_DECELERATING"
            return "BEARISH_STABLE"
        return "STRONG_BEARISH_ACCELERATING" if accel and delta_5 < 0 else "STRONG_BEARISH"

    @staticmethod
    def _acceleration_label(score, delta_5):
        if delta_5 is None: return "UNKNOWN"
        if delta_5 >= 10: return "ACCELERATING_BULLISH"
        if delta_5 <= -10: return "ACCELERATING_BEARISH"
        if score > 20 and delta_5 < -5: return "DECELERATING_BULLISH"
        if score < -20 and delta_5 > 5: return "DECELERATING_BEARISH"
        return "STABLE"

    @staticmethod
    def _data_quality(market_data):
        numeric = market_data[["High","Low","Close"]].apply(pd.to_numeric, errors="coerce")
        completeness = 100.0 * (1.0 - numeric.isna().mean().mean())
        length_quality = min(100.0, len(market_data)/252.0*100.0)
        return max(0.0, min(100.0, 0.8*completeness + 0.2*length_quality))

    @staticmethod
    def _latest(series):
        valid = pd.to_numeric(series, errors="coerce").dropna()
        return None if valid.empty else float(valid.iloc[-1])

    @staticmethod
    def _lagged(series, periods):
        valid = pd.to_numeric(series, errors="coerce").dropna()
        return None if len(valid) <= periods else float(valid.iloc[-1-periods])

    @staticmethod
    def _interpolate(value, points):
        points = sorted(points)
        if value <= points[0][0]: return float(points[0][1])
        if value >= points[-1][0]: return float(points[-1][1])
        for (x0,y0),(x1,y1) in zip(points, points[1:]):
            if x0 <= value <= x1:
                return float(y0 + ((value-x0)/(x1-x0))*(y1-y0))
        return 0.0

    @staticmethod
    def _validate(market_data):
        if not isinstance(market_data, pd.DataFrame) or market_data.empty:
            raise MomentumScoringError("market_data must be a non-empty pandas DataFrame.")
        if len(market_data) < MomentumScoreEngine.MIN_OBSERVATIONS:
            raise MomentumScoringError(
                f"Momentum Score requires at least {MomentumScoreEngine.MIN_OBSERVATIONS} observations; received {len(market_data)}."
            )
        missing = {"High","Low","Close"}.difference(market_data.columns)
        if missing:
            raise MomentumScoringError(
                "Momentum Score requires columns: " + ", ".join(sorted(missing))
            )


momentum_score_engine = MomentumScoreEngine()
