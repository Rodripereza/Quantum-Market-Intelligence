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

    @staticmethod
    def _normalize_entity(value: str | None) -> str:
        return " ".join(str(value or "").casefold().split())

    @classmethod
    def _portfolio_relevance(
        cls,
        title: str,
        positions: list[Any],
    ) -> tuple[list[str], float]:
        """
        Detects which current portfolio positions are referenced by a headline.

        Score:
        - 1.00: ticker + company match
        - 0.92: company match
        - 0.82: ticker match
        - 0.35: sector match
        - 0.00: no portfolio relationship

        The method intentionally uses only current PortfolioPosition metadata.
        """
        text = cls._normalize_entity(title)
        related_tickers: list[str] = []
        best_score = 0.0

        for position in positions:
            ticker = str(getattr(position, "ticker", "") or "").strip().upper()
            company = str(getattr(position, "company", "") or "").strip()
            sector = str(getattr(position, "sector", "") or "").strip()

            ticker_key = cls._normalize_entity(ticker)
            company_key = cls._normalize_entity(company)
            sector_key = cls._normalize_entity(sector)

            ticker_match = bool(
                ticker_key
                and (
                    f" {ticker_key} " in f" {text} "
                    or f"${ticker_key}" in text
                )
            )
            company_match = bool(company_key and company_key in text)
            sector_match = bool(
                sector_key
                and len(sector_key) >= 4
                and sector_key in text
            )

            score = 0.0
            if ticker_match and company_match:
                score = 1.0
            elif company_match:
                score = 0.92
            elif ticker_match:
                score = 0.82
            elif sector_match:
                score = 0.35

            if score > 0.0:
                if ticker and ticker not in related_tickers:
                    related_tickers.append(ticker)
                best_score = max(best_score, score)

        return related_tickers, round(best_score, 2)

    @staticmethod
    def _build_portfolio_query(positions: list[Any]) -> str:
        """
        Builds a compact Google News query from the current portfolio.

        Example:
            NIO OR "NIO Inc" OR PLTR OR "Palantir Technologies"
        """
        terms: list[str] = []
        seen: set[str] = set()

        for position in positions:
            ticker = str(getattr(position, "ticker", "") or "").strip()
            company = str(getattr(position, "company", "") or "").strip()

            for value, quoted in ((ticker, False), (company, True)):
                if not value:
                    continue

                key = value.casefold()
                if key in seen:
                    continue

                seen.add(key)
                terms.append(f'"{value}"' if quoted and " " in value else value)

        return " OR ".join(terms)

    def get_portfolio_intelligence(
        self,
        positions: list[Any],
        limit: int = 12,
    ) -> dict[str, Any]:
        """
        Returns news related to the CURRENT portfolio.

        Sprint 005.6.1 foundation:
        - generates the search query from PortfolioPosition ticker/company
        - tags each article with related_tickers
        - exposes portfolio_relevant and portfolio_relevance
        - preserves Sprint 005.5 sentiment/impact classification
        """
        safe_limit = max(1, min(limit, 30))
        query = self._build_portfolio_query(positions)

        if not positions or not query:
            return {
                "status": "degraded",
                "provider": "Google News RSS",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "mode": "portfolio",
                "query": query,
                "positions": len(positions),
                "count": 0,
                "articles": [],
            }

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
            related_tickers, relevance = self._portfolio_relevance(
                title,
                positions,
            )

            articles.append(
                {
                    **item,
                    "category": "portfolio" if relevance > 0 else "markets",
                    "sentiment": sentiment,
                    "impact": impact,
                    "related_tickers": related_tickers,
                    "portfolio_relevant": relevance > 0,
                    "portfolio_relevance": relevance,
                }
            )

        impact_rank = {"high": 2, "medium": 1, "low": 0}

        articles.sort(
            key=lambda article: (
                article["portfolio_relevance"],
                impact_rank.get(article["impact"], 0),
                article.get("published_at") or "",
            ),
            reverse=True,
        )

        articles = articles[:safe_limit]

        return {
            "status": "ok" if articles else "degraded",
            "provider": "Google News RSS",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "mode": "portfolio",
            "query": query,
            "positions": len(positions),
            "count": len(articles),
            "articles": articles,
        }


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
