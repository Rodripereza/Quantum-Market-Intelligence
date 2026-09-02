from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.services.market.market_service import MarketService


class QMIDecisionPriceCaptureService:
    """
    DE-CORE-006.5.2 — Exact Decision Price Capture

    Captures the market quote visible to QMI at observation time and attaches
    it to the action-policy payload before Snapshot Policy / persistence.

    This is a context-enrichment service only:
    - no snapshot is written here
    - no outcome is judged here
    - no model weights are changed
    """

    ENGINE = "QMI Exact Decision Price Capture"
    ENGINE_ID = "DE-CORE-006.5.2"
    VERSION = "0.1.0"

    def __init__(
        self,
        market_service: MarketService | None = None,
    ) -> None:
        self.market_service = market_service or MarketService()

    def enrich(
        self,
        *,
        symbol: str,
        action_policy_response: dict[str, Any],
        fail_open: bool = True,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        normalized_symbol = str(symbol or "").strip().upper()
        response = dict(action_policy_response or {})

        try:
            quote = self.market_service.get_quote(normalized_symbol) or {}
            price = self._number(quote.get("price"))

            if price is None or price <= 0:
                raise ValueError(
                    f"No valid current market price is available for {normalized_symbol}."
                )

            captured_at = datetime.now(timezone.utc).isoformat()

            context = {
                "available": True,
                "decision_price": price,
                "decision_price_currency": quote.get("currency"),
                "decision_price_source": "MARKET_SERVICE_QUOTE",
                "decision_price_captured_at": captured_at,
                "quote_exchange": quote.get("exchange"),
                "quote_previous_close": self._number(
                    quote.get("previous_close")
                ),
                "quote_open": self._number(quote.get("open")),
                "quote_day_high": self._number(quote.get("day_high")),
                "quote_day_low": self._number(quote.get("day_low")),
                "quote_volume": self._number(quote.get("volume")),
            }

            existing = response.get("observation_context") or {}
            response["observation_context"] = {
                **existing,
                **context,
            }

            return response, {
                "engine": self.ENGINE,
                "engine_id": self.ENGINE_ID,
                "version": self.VERSION,
                "status": "operational",
                "symbol": normalized_symbol,
                **context,
            }

        except Exception as exc:
            if not fail_open:
                raise

            context = {
                "available": False,
                "decision_price": None,
                "decision_price_currency": None,
                "decision_price_source": None,
                "decision_price_captured_at": None,
            }

            existing = response.get("observation_context") or {}
            response["observation_context"] = {
                **existing,
                **context,
            }

            return response, {
                "engine": self.ENGINE,
                "engine_id": self.ENGINE_ID,
                "version": self.VERSION,
                "status": "degraded",
                "symbol": normalized_symbol,
                **context,
                "error": f"{type(exc).__name__}: {exc}",
            }

    @staticmethod
    def _number(value: Any) -> float | None:
        try:
            if value is None:
                return None
            return float(value)
        except (TypeError, ValueError):
            return None
