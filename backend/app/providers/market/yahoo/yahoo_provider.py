import yfinance as yf


class YahooProvider:
    """
    Provider encargado de obtener datos desde Yahoo Finance.
    """

    @staticmethod
    def get_quote(symbol: str) -> dict:
        ticker = yf.Ticker(symbol)

        info = ticker.fast_info

        return {
            "symbol": symbol.upper(),
            "price": info.get("lastPrice"),
            "previous_close": info.get("previousClose"),
            "open": info.get("open"),
            "day_high": info.get("dayHigh"),
            "day_low": info.get("dayLow"),
            "volume": info.get("lastVolume"),
            "currency": info.get("currency"),
            "exchange": info.get("exchange"),
        }
    @staticmethod
    def get_history(
        symbol: str,
        period: str = "1y",
        interval: str = "1d",
    ) -> list:

        ticker = yf.Ticker(symbol)

        history = ticker.history(
            period=period,
            interval=interval,
        )

        result = []

        for date, row in history.iterrows():
            result.append(
                {
                    "date": date.strftime("%Y-%m-%d"),
                    "open": float(row["Open"]),
                    "high": float(row["High"]),
                    "low": float(row["Low"]),
                    "close": float(row["Close"]),
                    "volume": int(row["Volume"]),
                }
            )

        return result