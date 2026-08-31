from __future__ import annotations

import json
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class NioAspRevenueEngine:
    """
    DE-NIO-ASP-001.0

    Estimates quarterly model-mix ASP from monthly model deliveries and a
    versioned model-price database. It can also compare against reported ASP
    anchors and derive a calibration factor for forecast quarters.
    """

    def __init__(self, price_file: Optional[Path] = None):
        self.price_file = price_file or (
            Path(__file__).resolve().parent / "data" / "price_history.json"
        )
        self.price_db = self._load_price_db()

    def _load_price_db(self) -> dict:
        with self.price_file.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    @staticmethod
    def _quarter(month: int) -> int:
        return ((int(month) - 1) // 3) + 1

    @staticmethod
    def _period_date(year: int, month: int) -> date:
        return date(int(year), int(month), 1)

    @staticmethod
    def _parse_date(value: Optional[str]) -> Optional[date]:
        if not value:
            return None
        return date.fromisoformat(value)

    def _price_for(self, model: str, year: int, month: int) -> Optional[dict]:
        target = self._period_date(year, month)
        candidates = []

        for item in self.price_db.get("prices", []):
            aliases = [str(x).upper() for x in item.get("aliases", [])]
            if str(item.get("model", "")).upper() != str(model).upper() and str(model).upper() not in aliases:
                continue

            valid_from = self._parse_date(item.get("valid_from"))
            valid_to = self._parse_date(item.get("valid_to"))

            if valid_from and target < valid_from.replace(day=1):
                continue
            if valid_to and target > valid_to.replace(day=1):
                continue
            candidates.append(item)

        if not candidates:
            return None

        candidates.sort(key=lambda x: x.get("valid_from") or "0001-01-01", reverse=True)
        return candidates[0]

    @staticmethod
    def _effective_price(price_row: dict) -> Optional[float]:
        # transaction_price is preferred. MSRP is only a fallback proxy.
        for key in ("estimated_transaction_price_rmb", "msrp_rmb"):
            value = price_row.get(key)
            if value is not None:
                return float(value)
        return None

    def analyze(self, records: List) -> dict:
        grouped = defaultdict(list)
        for record in records:
            grouped[(int(record.year), self._quarter(record.month))].append(record)

        reported_map = {
            item["quarter"]: item
            for item in self.price_db.get("reported_asp", [])
        }

        quarterly = []
        calibration_samples = []

        for (year, quarter), q_records in sorted(grouped.items()):
            total_deliveries = sum(int(r.total) for r in q_records)
            weighted_value = 0.0
            priced_deliveries = 0
            unpriced_deliveries = 0
            model_detail: Dict[str, dict] = {}

            for record in q_records:
                for model, payload in record.models.items():
                    deliveries = int(payload.deliveries)
                    if deliveries <= 0:
                        continue

                    price_row = self._price_for(model, record.year, record.month)
                    effective_price = self._effective_price(price_row) if price_row else None

                    detail = model_detail.setdefault(
                        model,
                        {
                            "brand": payload.brand,
                            "deliveries": 0,
                            "weighted_value_rmb": 0.0,
                            "price_observations": 0,
                        },
                    )
                    detail["deliveries"] += deliveries

                    if effective_price is None:
                        unpriced_deliveries += deliveries
                        continue

                    weighted_value += deliveries * effective_price
                    priced_deliveries += deliveries
                    detail["weighted_value_rmb"] += deliveries * effective_price
                    detail["price_observations"] += 1

            model_mix_asp = (
                weighted_value / priced_deliveries if priced_deliveries else None
            )
            coverage = (
                priced_deliveries / total_deliveries
                if total_deliveries
                else 0.0
            )

            quarter_id = f"{year}-Q{quarter}"
            reported = reported_map.get(quarter_id)
            reported_asp = (
                float(reported["reported_asp_rmb"])
                if reported and reported.get("reported_asp_rmb") is not None
                else None
            )

            calibration_factor = (
                reported_asp / model_mix_asp
                if reported_asp and model_mix_asp
                else None
            )
            if calibration_factor and coverage >= 0.70:
                calibration_samples.append(calibration_factor)

            model_mix = []
            for model, detail in sorted(model_detail.items()):
                model_asp = (
                    detail["weighted_value_rmb"] / detail["deliveries"]
                    if detail["deliveries"] and detail["weighted_value_rmb"]
                    else None
                )
                model_mix.append(
                    {
                        "model": model,
                        "brand": detail["brand"],
                        "deliveries": detail["deliveries"],
                        "estimated_price_rmb": round(model_asp, 2) if model_asp else None,
                    }
                )

            quarterly.append(
                {
                    "quarter": quarter_id,
                    "year": year,
                    "quarter_number": quarter,
                    "deliveries": total_deliveries,
                    "priced_deliveries": priced_deliveries,
                    "price_coverage_pct": round(coverage * 100, 1),
                    "model_mix_asp_rmb": round(model_mix_asp, 2) if model_mix_asp else None,
                    "reported_asp_rmb": round(reported_asp, 2) if reported_asp else None,
                    "calibration_factor": round(calibration_factor, 4) if calibration_factor else None,
                    "forecast_asp_rmb": None,
                    "forecast_vehicle_revenue_rmb": None,
                    "is_forecast": reported_asp is None,
                    "model_mix": model_mix,
                }
            )

        # Use median-ish robust central factor from recent reported quarters.
        recent = calibration_samples[-4:]
        default_factor = (
            sum(recent) / len(recent)
            if recent
            else float(self.price_db.get("default_calibration_factor", 1.0))
        )

        previous_asp = None
        for row in quarterly:
            if row["reported_asp_rmb"] is not None:
                effective_asp = row["reported_asp_rmb"]
            elif row["model_mix_asp_rmb"] is not None:
                effective_asp = row["model_mix_asp_rmb"] * default_factor
                row["forecast_asp_rmb"] = round(effective_asp, 2)
                row["forecast_vehicle_revenue_rmb"] = round(
                    effective_asp * row["deliveries"], 2
                )
            else:
                effective_asp = None

            row["asp_qoq_pct"] = (
                round((effective_asp / previous_asp - 1) * 100, 1)
                if effective_asp and previous_asp
                else None
            )
            if effective_asp:
                previous_asp = effective_asp

        latest = quarterly[-1] if quarterly else None
        latest_qoq = latest.get("asp_qoq_pct") if latest else None

        if latest_qoq is None:
            premiumization_state = "UNKNOWN"
        elif latest_qoq >= 5:
            premiumization_state = "STRONG_PREMIUMIZATION"
        elif latest_qoq > 1:
            premiumization_state = "PREMIUMIZING"
        elif latest_qoq <= -5:
            premiumization_state = "STRONG_DILUTION"
        elif latest_qoq < -1:
            premiumization_state = "DILUTING"
        else:
            premiumization_state = "STABLE"

        latest_coverage = latest.get("price_coverage_pct", 0) if latest else 0
        confidence = (
            "HIGH" if latest_coverage >= 90
            else "MEDIUM" if latest_coverage >= 70
            else "LOW"
        )

        return {
            "engine": "NIO ASP & Revenue Intelligence",
            "engine_id": "DE-NIO-ASP-001.0",
            "version": "0.1.0",
            "currency": "CNY",
            "methodology": "delivery_weighted_model_price_with_reported_asp_calibration",
            "latest_quarter": latest["quarter"] if latest else None,
            "calibration_factor": round(default_factor, 4),
            "asp_trend": "RISING" if latest_qoq and latest_qoq > 1 else "FALLING" if latest_qoq and latest_qoq < -1 else "STABLE",
            "premiumization_state": premiumization_state,
            "confidence": confidence,
            "quarterly": quarterly,
        }
