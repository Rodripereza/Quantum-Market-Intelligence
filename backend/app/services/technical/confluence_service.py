from __future__ import annotations

from typing import Any


class TechnicalConfluenceService:
    """
    DE-TA-008.1 — Confluence Diagnostics & Explainability

    First fusion layer of QMI.

    This engine does NOT generate BUY / SELL recommendations.
    It normalizes independent technical evidence into:
      - direction_score [-100, +100]
      - technical_state
      - confidence [0, 100]
      - agreement [0, 100]
      - explicit engine conflicts

    Direction weights:
      Market Structure       22%
      Trend                  18%
      Strength               12%
      Momentum               12%
      Liquidity              14%
      Support / Resistance   10%
      Volume                  7%

    Volatility is intentionally excluded from directional voting and is
    used as a confidence / risk modifier (5% architecture allocation).
    """

    DIRECTION_WEIGHTS = {
        "structure": 0.22,
        "trend": 0.18,
        "strength": 0.12,
        "momentum": 0.12,
        "liquidity": 0.14,
        "support_resistance": 0.10,
        "volume": 0.07,
    }

    def analyze(
        self,
        technical: dict[str, Any],
        market_structure: dict[str, Any],
        support_resistance: dict[str, Any],
        liquidity: dict[str, Any],
    ) -> dict[str, Any]:
        scoring = technical.get("scoring") or {}

        trend = scoring.get("trend") or {}
        strength = scoring.get("strength") or {}
        momentum = scoring.get("momentum") or {}
        volatility = scoring.get("volatility_engine") or {}
        volume = scoring.get("volume") or {}

        engines = {
            "structure": self._normalize_structure(market_structure),
            "trend": self._normalize_directional_engine(
                trend,
                state_keys=("state", "trend", "direction"),
            ),
            "strength": self._normalize_strength(strength),
            "momentum": self._normalize_directional_engine(
                momentum,
                state_keys=("state", "direction", "acceleration"),
            ),
            "liquidity": self._normalize_liquidity(liquidity),
            "support_resistance": self._normalize_support_resistance(
                support_resistance
            ),
            "volume": self._normalize_directional_engine(
                volume,
                state_keys=("direction", "state"),
            ),
        }

        volatility_context = self._normalize_volatility(volatility)

        available_weight = sum(
            self.DIRECTION_WEIGHTS[name]
            for name, data in engines.items()
            if data["available"]
        )

        weighted_sum = sum(
            engines[name]["score"] * self.DIRECTION_WEIGHTS[name]
            for name in self.DIRECTION_WEIGHTS
            if engines[name]["available"]
        )

        direction_score = (
            weighted_sum / available_weight
            if available_weight > 0
            else 0.0
        )
        direction_score = round(self._clamp(direction_score), 1)

        state = self._state_from_score(direction_score)

        engine_diagnostics = self._build_engine_diagnostics(
            engines=engines,
            available_weight=available_weight,
        )

        agreement = self._agreement(
            engines=engines,
            direction_score=direction_score,
        )

        weighted_engine_confidence = self._weighted_confidence(engines)
        data_quality = self._data_quality(
            technical=technical,
            engines=engines,
        )

        volatility_modifier = self._volatility_confidence_modifier(
            volatility_context
        )

        # Confidence is deliberately not the same thing as direction.
        # Strong directional evidence can still have modest confidence if
        # engines disagree or data quality is weak.
        confidence = (
            weighted_engine_confidence * 0.45
            + agreement * 0.30
            + data_quality * 0.20
            + volatility_modifier * 0.05
        )
        confidence = round(
            max(0.0, min(100.0, confidence)),
            1,
        )

        conflicts = self._detect_conflicts(engines)

        confidence_diagnostics = {
            "weighted_engine_confidence": round(
                weighted_engine_confidence,
                1,
            ),
            "agreement_component": round(
                agreement * 0.30,
                1,
            ),
            "engine_confidence_component": round(
                weighted_engine_confidence * 0.45,
                1,
            ),
            "data_quality_component": round(
                data_quality * 0.20,
                1,
            ),
            "volatility_component": round(
                volatility_modifier * 0.05,
                1,
            ),
            "volatility_modifier": round(
                volatility_modifier,
                1,
            ),
            "formula": (
                "45% weighted engine confidence + "
                "30% agreement + 20% data quality + "
                "5% volatility modifier"
            ),
        }

        bullish_engines = sum(
            1
            for item in engines.values()
            if item["available"] and item["score"] >= 20
        )
        bearish_engines = sum(
            1
            for item in engines.values()
            if item["available"] and item["score"] <= -20
        )
        neutral_engines = sum(
            1
            for item in engines.values()
            if item["available"] and abs(item["score"]) < 20
        )

        return {
            "engine": "QMI Technical Confluence Engine",
            "engine_id": "DE-TA-008.1",
            "version": "0.2.0",
            "status": "operational",
            "technical_confluence": {
                "direction_score": direction_score,
                "state": state,
                "confidence": confidence,
                "agreement": agreement,
                "data_quality": data_quality,
                "bullish_engines": bullish_engines,
                "bearish_engines": bearish_engines,
                "neutral_engines": neutral_engines,
                "conflict_count": len(conflicts),
                "conflicts": conflicts,
                "engines": engines,
                "diagnostics": {
                    "engine_contributions": engine_diagnostics,
                    "confidence": confidence_diagnostics,
                    "dominant_positive_engine": self._dominant_engine(
                        engine_diagnostics,
                        positive=True,
                    ),
                    "dominant_negative_engine": self._dominant_engine(
                        engine_diagnostics,
                        positive=False,
                    ),
                    "largest_abs_contribution": self._largest_contribution(
                        engine_diagnostics
                    ),
                    "available_direction_weight": round(
                        available_weight,
                        4,
                    ),
                    "normalization_factor": round(
                        1.0 / available_weight
                        if available_weight > 0
                        else 0.0,
                        4,
                    ),
                },
                "volatility_context": volatility_context,
                "weights": {
                    **self.DIRECTION_WEIGHTS,
                    "volatility_confidence": 0.05,
                },
                "architecture": {
                    "direction_engine": [
                        "structure",
                        "trend",
                        "strength",
                        "momentum",
                        "liquidity",
                        "support_resistance",
                        "volume",
                    ],
                    "confidence_engine": [
                        "engine_confidence",
                        "agreement",
                        "data_quality",
                        "volatility_context",
                    ],
                    "decision_signal": False,
                    "note": (
                        "DE-TA-008.0 produces fused technical evidence only. "
                        "It does not issue BUY, HOLD or SELL decisions."
                    ),
                },
            },
        }

    def _normalize_structure(
        self,
        structure: dict[str, Any],
    ) -> dict[str, Any]:
        trend = structure.get("trend") or {}
        validation = structure.get("validation") or {}

        state = str(
            structure.get("structural_state")
            or trend.get("state")
            or "NEUTRAL"
        ).upper()

        trend_bias = str(
            trend.get("bias")
            or state
            or "NEUTRAL"
        ).upper()

        validation_score = self._first_number(
            validation,
            (
                "overall_score",
                "score",
                "structure_quality",
            ),
        )
        trend_confidence = self._number(
            trend.get("confidence"),
            50.0,
        )

        magnitude = (
            validation_score
            if validation_score is not None
            else trend_confidence
        )
        magnitude = max(35.0, min(100.0, magnitude))

        sign = self._direction_sign(
            trend_bias,
            state,
        )

        score = magnitude * sign

        confidence = (
            validation_score
            if validation_score is not None
            else trend_confidence
        )

        return self._engine_payload(
            score=score,
            confidence=confidence,
            state=state,
            source="market_structure",
            data_quality=100.0,
            details={
                "structural_state": state,
                "trend_bias": trend_bias,
                "validation_score": validation_score,
            },
        )

    def _normalize_strength(
        self,
        engine: dict[str, Any],
    ) -> dict[str, Any]:
        raw_score = self._number(engine.get("score"), 0.0)
        dmi = str(
            engine.get("dmi_direction")
            or engine.get("direction")
            or "NEUTRAL"
        ).upper()

        sign = self._direction_sign(dmi)

        # Strength magnitude is not inherently directional. Direction comes
        # from DMI / engine direction; magnitude comes from the score.
        score = abs(raw_score) * sign

        confidence = self._first_number(
            engine,
            ("confidence", "data_quality"),
        )
        if confidence is None:
            confidence = min(100.0, 50.0 + abs(raw_score) * 0.5)

        return self._engine_payload(
            score=score,
            confidence=confidence,
            state=dmi,
            source="technical.strength",
            data_quality=self._number(
                engine.get("data_quality"),
                100.0,
            ),
            details={
                "raw_score": raw_score,
                "dmi_direction": dmi,
                "strength": engine.get("strength"),
            },
        )

    def _normalize_directional_engine(
        self,
        engine: dict[str, Any],
        state_keys: tuple[str, ...],
    ) -> dict[str, Any]:
        if not engine:
            return self._unavailable()

        raw_score = self._number(engine.get("score"), 0.0)

        state = "NEUTRAL"
        for key in state_keys:
            value = engine.get(key)
            if value not in (None, ""):
                state = str(value).upper()
                break

        # Prefer the engine's signed score. If a legacy engine returns a
        # magnitude-only score, infer sign from the state / direction.
        if raw_score == 0:
            score = 0.0
        elif raw_score > 0 and self._direction_sign(state) < 0:
            score = -abs(raw_score)
        else:
            score = raw_score

        confidence = self._first_number(
            engine,
            ("confidence", "data_quality"),
        )
        if confidence is None:
            confidence = min(100.0, 50.0 + abs(score) * 0.4)

        return self._engine_payload(
            score=score,
            confidence=confidence,
            state=state,
            source="technical",
            data_quality=self._number(
                engine.get("data_quality"),
                100.0,
            ),
            details={
                "raw_score": raw_score,
            },
        )

    def _normalize_liquidity(
        self,
        liquidity: dict[str, Any],
    ) -> dict[str, Any]:
        bias = liquidity.get("liquidity_bias") or (
            liquidity.get("summary") or {}
        ).get("liquidity_bias") or {}

        if not bias:
            return self._unavailable()

        score = self._number(bias.get("score"), 0.0)
        confidence = self._number(
            bias.get("confidence"),
            50.0,
        )

        return self._engine_payload(
            score=score,
            confidence=confidence,
            state=str(
                bias.get("state") or "BALANCED"
            ).upper(),
            source="liquidity_bias",
            data_quality=100.0,
            details={
                "dominant_liquidity": bias.get(
                    "dominant_liquidity"
                ),
                "bearish_pressure": bias.get(
                    "bearish_pressure"
                ),
                "bullish_pressure": bias.get(
                    "bullish_pressure"
                ),
            },
        )

    def _normalize_support_resistance(
        self,
        sr: dict[str, Any],
    ) -> dict[str, Any]:
        if not sr:
            return self._unavailable()

        current_price = self._number(
            sr.get("current_price"),
            0.0,
        )
        summary = sr.get("summary") or {}
        support = summary.get("nearest_support")
        resistance = summary.get("nearest_resistance")
        active_zone = summary.get("active_zone")

        score = 0.0
        confidence = 55.0
        state = "BALANCED"

        if active_zone:
            zone_type = str(
                active_zone.get("type") or ""
            ).upper()
            strength = self._number(
                active_zone.get("strength"),
                60.0,
            )
            if zone_type == "SUPPORT":
                score = min(65.0, strength * 0.65)
                state = "AT_SUPPORT"
            elif zone_type == "RESISTANCE":
                score = -min(65.0, strength * 0.65)
                state = "AT_RESISTANCE"
            confidence = strength
        else:
            support_distance = (
                self._number(
                    support.get("distance_pct"),
                    999.0,
                )
                if isinstance(support, dict)
                else 999.0
            )
            resistance_distance = (
                self._number(
                    resistance.get("distance_pct"),
                    999.0,
                )
                if isinstance(resistance, dict)
                else 999.0
            )

            support_strength = (
                self._number(
                    support.get("strength"),
                    50.0,
                )
                if isinstance(support, dict)
                else 0.0
            )
            resistance_strength = (
                self._number(
                    resistance.get("strength"),
                    50.0,
                )
                if isinstance(resistance, dict)
                else 0.0
            )

            support_pull = (
                support_strength
                / max(1.0, support_distance)
            )
            resistance_pull = (
                resistance_strength
                / max(1.0, resistance_distance)
            )

            total = support_pull + resistance_pull

            if total > 0:
                score = (
                    (support_pull - resistance_pull)
                    / total
                    * 55.0
                )
                confidence = min(
                    90.0,
                    45.0 + total * 1.5,
                )

            if score >= 15:
                state = "SUPPORT_ADVANTAGE"
            elif score <= -15:
                state = "RESISTANCE_ADVANTAGE"

        return self._engine_payload(
            score=score,
            confidence=confidence,
            state=state,
            source="support_resistance",
            data_quality=100.0,
            details={
                "current_price": current_price,
                "nearest_support": support,
                "nearest_resistance": resistance,
                "active_zone": active_zone,
            },
        )

    def _normalize_volatility(
        self,
        volatility: dict[str, Any],
    ) -> dict[str, Any]:
        if not volatility:
            return {
                "available": False,
                "score": 0.0,
                "state": "UNKNOWN",
                "confidence": 50.0,
                "risk_modifier": "UNKNOWN",
            }

        state = str(
            volatility.get("state")
            or volatility.get("risk_environment")
            or "NEUTRAL"
        ).upper()

        confidence = self._number(
            volatility.get("confidence"),
            60.0,
        )

        compression = bool(
            volatility.get("compression", False)
        )
        expansion = bool(
            volatility.get("expansion", False)
        )

        if expansion:
            risk_modifier = "ELEVATED"
        elif compression:
            risk_modifier = "COMPRESSION"
        else:
            risk_modifier = str(
                volatility.get("risk_environment")
                or "NORMAL"
            ).upper()

        return {
            "available": True,
            "score": self._number(
                volatility.get("score"),
                0.0,
            ),
            "state": state,
            "confidence": confidence,
            "risk_modifier": risk_modifier,
            "compression": compression,
            "expansion": expansion,
            "data_quality": self._number(
                volatility.get("data_quality"),
                100.0,
            ),
        }

    def _build_engine_diagnostics(
        self,
        engines: dict[str, dict[str, Any]],
        available_weight: float,
    ) -> list[dict[str, Any]]:
        """
        Makes the confluence score auditable.

        raw_contribution:
            score * configured weight

        normalized_contribution:
            raw contribution re-scaled by the sum of currently available
            directional weights. The sum of normalized contributions equals
            direction_score (subject to rounding).
        """
        diagnostics: list[dict[str, Any]] = []

        for name, weight in self.DIRECTION_WEIGHTS.items():
            payload = engines.get(name) or {}
            available = bool(payload.get("available"))
            score = float(payload.get("score", 0.0))

            raw_contribution = score * weight
            normalized_contribution = (
                raw_contribution / available_weight
                if available and available_weight > 0
                else 0.0
            )

            vote = (
                "BULLISH"
                if score >= 20
                else "BEARISH"
                if score <= -20
                else "NEUTRAL"
            )

            diagnostics.append({
                "engine": name,
                "available": available,
                "score": round(score, 1),
                "state": payload.get("state"),
                "confidence": payload.get("confidence"),
                "configured_weight": round(weight, 4),
                "configured_weight_pct": round(weight * 100.0, 1),
                "effective_weight_pct": round(
                    (
                        weight / available_weight * 100.0
                        if available and available_weight > 0
                        else 0.0
                    ),
                    1,
                ),
                "raw_contribution": round(
                    raw_contribution,
                    3,
                ),
                "normalized_contribution": round(
                    normalized_contribution,
                    2,
                ),
                "vote": vote,
                "source": payload.get("source"),
            })

        diagnostics.sort(
            key=lambda item: abs(
                item["normalized_contribution"]
            ),
            reverse=True,
        )

        return diagnostics

    @staticmethod
    def _dominant_engine(
        diagnostics: list[dict[str, Any]],
        positive: bool,
    ) -> dict[str, Any] | None:
        candidates = [
            item
            for item in diagnostics
            if item["available"]
            and (
                item["normalized_contribution"] > 0
                if positive
                else item["normalized_contribution"] < 0
            )
        ]

        if not candidates:
            return None

        if positive:
            return max(
                candidates,
                key=lambda item: item["normalized_contribution"],
            )

        return min(
            candidates,
            key=lambda item: item["normalized_contribution"],
        )

    @staticmethod
    def _largest_contribution(
        diagnostics: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        available = [
            item
            for item in diagnostics
            if item["available"]
        ]

        if not available:
            return None

        return max(
            available,
            key=lambda item: abs(
                item["normalized_contribution"]
            ),
        )

    def _agreement(
        self,
        engines: dict[str, dict[str, Any]],
        direction_score: float,
    ) -> float:
        if not engines:
            return 0.0

        dominant_sign = (
            1 if direction_score >= 10
            else -1 if direction_score <= -10
            else 0
        )

        total_weight = 0.0
        agreeing_weight = 0.0

        for name, payload in engines.items():
            if not payload["available"]:
                continue

            weight = self.DIRECTION_WEIGHTS[name]
            total_weight += weight
            score = payload["score"]

            engine_sign = (
                1 if score >= 15
                else -1 if score <= -15
                else 0
            )

            if dominant_sign == 0:
                if engine_sign == 0:
                    agreeing_weight += weight
                else:
                    agreeing_weight += weight * 0.35
            elif engine_sign == dominant_sign:
                agreeing_weight += weight
            elif engine_sign == 0:
                agreeing_weight += weight * 0.5

        if total_weight <= 0:
            return 0.0

        return round(
            agreeing_weight / total_weight * 100.0,
            1,
        )

    def _weighted_confidence(
        self,
        engines: dict[str, dict[str, Any]],
    ) -> float:
        weighted = 0.0
        total = 0.0

        for name, payload in engines.items():
            if not payload["available"]:
                continue
            weight = self.DIRECTION_WEIGHTS[name]
            weighted += payload["confidence"] * weight
            total += weight

        return (
            weighted / total
            if total > 0
            else 0.0
        )

    def _data_quality(
        self,
        technical: dict[str, Any],
        engines: dict[str, dict[str, Any]],
    ) -> float:
        qualities = [
            payload["data_quality"]
            for payload in engines.values()
            if payload["available"]
            and payload.get("data_quality") is not None
        ]

        if not qualities:
            return 100.0

        return round(
            max(0.0, min(100.0, min(qualities))),
            1,
        )

    def _volatility_confidence_modifier(
        self,
        volatility: dict[str, Any],
    ) -> float:
        if not volatility.get("available"):
            return 50.0

        base = self._number(
            volatility.get("confidence"),
            60.0,
        )

        if volatility.get("expansion"):
            return max(35.0, base - 15.0)

        if volatility.get("compression"):
            # Compression is not bad data, but future directional
            # resolution is less certain.
            return max(45.0, base - 8.0)

        return base

    def _detect_conflicts(
        self,
        engines: dict[str, dict[str, Any]],
    ) -> list[dict[str, Any]]:
        conflicts: list[dict[str, Any]] = []

        pairs = [
            ("structure", "momentum"),
            ("structure", "volume"),
            ("structure", "liquidity"),
            ("trend", "momentum"),
            ("trend", "volume"),
            ("trend", "liquidity"),
            ("momentum", "liquidity"),
        ]

        for left, right in pairs:
            a = engines.get(left) or {}
            b = engines.get(right) or {}

            if not a.get("available") or not b.get("available"):
                continue

            a_score = float(a.get("score", 0.0))
            b_score = float(b.get("score", 0.0))

            if (
                abs(a_score) >= 20
                and abs(b_score) >= 20
                and a_score * b_score < 0
            ):
                severity = min(
                    100.0,
                    (abs(a_score) + abs(b_score)) / 2.0,
                )

                conflicts.append({
                    "type": (
                        f"{left.upper()}_VS_{right.upper()}"
                    ),
                    "left_engine": left,
                    "left_score": round(a_score, 1),
                    "right_engine": right,
                    "right_score": round(b_score, 1),
                    "severity": round(severity, 1),
                })

        conflicts.sort(
            key=lambda item: item["severity"],
            reverse=True,
        )
        return conflicts

    def _engine_payload(
        self,
        score: float,
        confidence: float,
        state: str,
        source: str,
        data_quality: float,
        details: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return {
            "available": True,
            "score": round(self._clamp(score), 1),
            "state": state,
            "confidence": round(
                max(0.0, min(100.0, confidence)),
                1,
            ),
            "data_quality": round(
                max(0.0, min(100.0, data_quality)),
                1,
            ),
            "source": source,
            "details": details or {},
        }

    @staticmethod
    def _unavailable() -> dict[str, Any]:
        return {
            "available": False,
            "score": 0.0,
            "state": "UNAVAILABLE",
            "confidence": 0.0,
            "data_quality": None,
            "source": None,
            "details": {},
        }

    @staticmethod
    def _direction_sign(*values: Any) -> int:
        text = " ".join(
            str(value).upper()
            for value in values
            if value is not None
        )

        bearish_tokens = (
            "BEAR",
            "SELL",
            "LOWER",
            "NEGATIVE",
            "DOWNTREND",
        )
        bullish_tokens = (
            "BULL",
            "BUY",
            "HIGHER",
            "POSITIVE",
            "UPTREND",
        )

        if any(token in text for token in bearish_tokens):
            return -1
        if any(token in text for token in bullish_tokens):
            return 1
        return 0

    @staticmethod
    def _first_number(
        data: dict[str, Any],
        keys: tuple[str, ...],
    ) -> float | None:
        for key in keys:
            value = data.get(key)
            try:
                if value is not None:
                    return float(value)
            except (TypeError, ValueError):
                continue
        return None

    @staticmethod
    def _number(value: Any, default: float) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return float(default)

    @staticmethod
    def _clamp(value: float) -> float:
        return max(-100.0, min(100.0, float(value)))

    @staticmethod
    def _state_from_score(score: float) -> str:
        if score >= 65:
            return "STRONG_BULLISH"
        if score >= 25:
            return "BULLISH"
        if score <= -65:
            return "STRONG_BEARISH"
        if score <= -25:
            return "BEARISH"
        return "NEUTRAL"
