from __future__ import annotations

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any
from urllib.parse import quote_plus
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET


class NewsService:
    """
    Sprint 005.5 Market Intelligence provider.

    Uses public Google News RSS searches so QMI can expose a real
    normalized feed without requiring an API key in this first version.
    """

    GOOGLE_NEWS_RSS = (
        "https://news.google.com/rss/search?"
        "q={query}&hl=en-US&gl=US&ceid=US:en"
    )

    def _fetch_rss(self, query: str, timeout: int = 8) -> list[dict[str, Any]]:
        url = self.GOOGLE_NEWS_RSS.format(query=quote_plus(query))
        request = Request(
            url,
            headers={"User-Agent": "QMI/1.3 Market Intelligence"},
        )

        with urlopen(request, timeout=timeout) as response:
            payload = response.read()

        root = ET.fromstring(payload)
        items: list[dict[str, Any]] = []

        for item in root.findall("./channel/item"):
            title = (item.findtext("title") or "").strip()
            link = (item.findtext("link") or "").strip()
            published_raw = (item.findtext("pubDate") or "").strip()

            source_node = item.find("source")
            source = (
                (source_node.text or "").strip()
                if source_node is not None
                else "Unknown"
            )

            published_at = None
            if published_raw:
                try:
                    parsed = parsedate_to_datetime(published_raw)
                    if parsed.tzinfo is None:
                        parsed = parsed.replace(tzinfo=timezone.utc)
                    published_at = parsed.astimezone(timezone.utc).isoformat()
                except (TypeError, ValueError, OverflowError):
                    published_at = published_raw

            if title and link:
                items.append(
                    {
                        "title": title,
                        "source": source,
                        "published_at": published_at,
                        "url": link,
                    }
                )

        return items

    @staticmethod
    def _classify(title: str) -> tuple[str, str]:
        text = title.lower()

        negative_terms = (
            "fall", "falls", "fell", "drop", "drops", "dropped",
            "decline", "declines", "loss", "losses", "cut",
            "warning", "risk", "recession", "tariff", "war",
            "sanction", "probe", "lawsuit", "downgrade",
        )
        positive_terms = (
            "rise", "rises", "rose", "gain", "gains", "rally",
            "record", "beat", "beats", "growth", "upgrade",
            "surge", "surges", "strong", "optimism",
        )
        high_impact_terms = (
            "fed", "federal reserve", "inflation", "cpi", "jobs",
            "payroll", "interest rate", "rates", "treasury",
            "tariff", "sanction", "war", "recession", "gdp",
            "earnings", "guidance",
        )

        sentiment = "neutral"
        if any(term in text for term in negative_terms):
            sentiment = "negative"
        elif any(term in text for term in positive_terms):
            sentiment = "positive"

        impact = (
            "high"
            if any(term in text for term in high_impact_terms)
            else "medium"
        )

        return sentiment, impact

    def get_market_intelligence(
        self,
        limit: int = 12,
        query: str = "stock market OR S&P 500 OR Federal Reserve",
    ) -> dict[str, Any]:
        safe_limit = max(1, min(limit, 30))

        try:
            raw_items = self._fetch_rss(query)
        except Exception:
            raw_items = []

        seen_titles: set[str] = set()
        articles: list[dict[str, Any]] = []

        for item in raw_items:
            title = item["title"]
            normalized_title = title.casefold()

            if normalized_title in seen_titles:
                continue

            seen_titles.add(normalized_title)
            sentiment, impact = self._classify(title)

            articles.append(
                {
                    **item,
                    "category": "markets",
                    "sentiment": sentiment,
                    "impact": impact,
                }
            )

            if len(articles) >= safe_limit:
                break

        return {
            "status": "ok" if articles else "degraded",
            "provider": "Google News RSS",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "count": len(articles),
            "articles": articles,
        }
