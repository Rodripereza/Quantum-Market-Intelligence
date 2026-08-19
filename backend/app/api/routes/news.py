from fastapi import APIRouter, Query

from app.services.news.news_service import NewsService


router = APIRouter(
    prefix="/api/news",
    tags=["Market Intelligence"],
)

news_service = NewsService()


@router.get("")
def get_market_intelligence(
    limit: int = Query(default=12, ge=1, le=30),
    query: str = Query(
        default="stock market OR S&P 500 OR Federal Reserve",
        min_length=2,
        max_length=200,
    ),
):
    """
    Returns a normalized public market-news feed for the QMI Dashboard.
    Sprint 005.5 foundation: real headlines + basic rule-based
    sentiment and impact classification.
    """
    return news_service.get_market_intelligence(
        limit=limit,
        query=query,
    )
