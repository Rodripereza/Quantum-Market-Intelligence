from __future__ import annotations
import json
from pathlib import Path
from app.company_intelligence.nio.schemas import NioMonthlyDeliveryRecord

class NioDeliveryCollector:
    def __init__(self, data_path: Path | None = None) -> None:
        self.data_path = data_path or (
            Path(__file__).resolve().parent / "data" / "deliveries_normalized.json"
        )

    def collect(self) -> list[NioMonthlyDeliveryRecord]:
        if not self.data_path.exists():
            raise FileNotFoundError(
                f"NIO delivery dataset not found: {self.data_path}"
            )

        payload = json.loads(self.data_path.read_text(encoding="utf-8"))
        rows = payload.get("records") or []
        if not rows:
            raise ValueError("NIO delivery dataset contains no monthly records.")

        records = [NioMonthlyDeliveryRecord(**row) for row in rows]
        records.sort(key=lambda item: (item.year, item.month))

        by_period = {item.period: item for item in records}

        running_ytd: dict[int, int] = {}
        previous: NioMonthlyDeliveryRecord | None = None

        for record in records:
            running_ytd[record.year] = running_ytd.get(record.year, 0) + record.total
            record.ytd = running_ytd[record.year]

            if previous and previous.total > 0:
                record.mom_pct = round(
                    ((record.total / previous.total) - 1.0) * 100.0, 1
                )

            prior_period = f"{record.year - 1}-{record.month:02d}"
            prior = by_period.get(prior_period)
            if prior and prior.total > 0:
                record.yoy_pct = round(
                    ((record.total / prior.total) - 1.0) * 100.0, 1
                )

            previous = record

        return records
