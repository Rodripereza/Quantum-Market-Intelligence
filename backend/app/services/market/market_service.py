from datetime import datetime, timezone

from app.providers.market.yahoo.yahoo_provider import YahooProvider


GLOBAL_MARKET_ASSETS = [
    {
        "ticker": "SPY",
        "provider_symbol": "SPY",
        "name": "S&P 500 ETF",
        "category": "index",
    },
    {
        "ticker": "QQQ",
        "provider_symbol": "QQQ",
        "name": "Nasdaq 100 ETF",
        "category": "index",
    },
    {
        "ticker": "DIA",
        "provider_symbol": "DIA",
        "name": "Dow Jones ETF",
        "category": "index",
    },
    {
        "ticker": "IWM",
        "provider_symbol": "IWM",
        "name": "Russell 2000 ETF",
        "category": "index",
    },
    {
        "ticker": "VIX",
        "provider_symbol": "^VIX",
        "name": "Volatility Index",
        "category": "volatility",
    },
    {
        "ticker": "DXY",
        "provider_symbol": "DX-Y.NYB",
        "name": "US Dollar Index",
        "category": "currency",
    },
    {
        "ticker": "GOLD",
        "provider_symbol": "GC=F",
        "name": "Gold Futures",
        "category": "commodity",
    },
    {
        "ticker": "OIL",
        "provider_symbol": "CL=F",
        "name": "WTI Crude Oil",
        "category": "commodity",
    },
    {
        "ticker": "BTC",
        "provider_symbol": "BTC-USD",
        "name": "Bitcoin",
        "category": "crypto",
    },
]


class MarketService:
    """
    Servicio encargado de validar y preparar los datos de mercado.
    """

    def __init__(self) -> None:
        self.provider = YahooProvider()

    def get_quote(self, symbol: str) -> dict:
        normalized_symbol = symbol.strip().upper()

        if not normalized_symbol:
            raise ValueError("The symbol cannot be empty.")

        quote = self.provider.get_quote(normalized_symbol)

        if quote.get("price") is None:
            raise ValueError(
                f"No market data was found for symbol '{normalized_symbol}'."
            )

        return quote

    def get_global_market(self) -> dict:
        provider_symbols = [
            asset["provider_symbol"]
            for asset in GLOBAL_MARKET_ASSETS
        ]

        quotes = self.provider.get_quotes(provider_symbols)

        assets = []

        for asset_definition in GLOBAL_MARKET_ASSETS:
            provider_symbol = asset_definition["provider_symbol"]
            quote = quotes.get(provider_symbol)

            if quote is None:
                continue

            assets.append(
                {
                    "ticker": asset_definition["ticker"],
                    "provider_symbol": provider_symbol,
                    "name": asset_definition["name"],
                    "category": asset_definition["category"],
                    "price": quote.get("price"),
                    "previous_close": quote.get("previous_close"),
                    "change": quote.get("change"),
                    "change_pct": quote.get("change_pct"),
                    "volume": quote.get("volume"),
                }
            )

        return {
            "source": "Yahoo Finance",
            "status": "live" if assets else "unavailable",
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "assets": assets,
            "requested_assets": len(GLOBAL_MARKET_ASSETS),
            "available_assets": len(assets),
        }

    def get_history(
        self,
        symbol: str,
        period: str = "1y",
        interval: str = "1d",
    ) -> list:
        normalized_symbol = symbol.strip().upper()

        if not normalized_symbol:
            raise ValueError("The symbol cannot be empty.")

        history = self.provider.get_history(
            normalized_symbol,
            period,
            interval,
        )

        if len(history) == 0:
            raise ValueError(
                f"No historical data was found for symbol '{normalized_symbol}'."
            )

        return history