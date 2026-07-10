from app.providers.market.yahoo.yahoo_provider import YahooProvider


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