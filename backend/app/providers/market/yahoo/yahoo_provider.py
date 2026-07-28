from typing import Any

import pandas as pd
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
    def get_quotes(symbols: list[str]) -> dict[str, dict[str, Any]]:
        """
        Descarga conjuntamente las últimas cotizaciones de varios activos.

        Se solicitan cinco sesiones para disponer de al menos dos cierres
        válidos incluso cuando existen fines de semana o festivos.
        """
        normalized_symbols = [
            symbol.strip().upper()
            for symbol in symbols
            if symbol and symbol.strip()
        ]

        if not normalized_symbols:
            return {}

        data = yf.download(
            tickers=normalized_symbols,
            period="5d",
            interval="1d",
            group_by="ticker",
            auto_adjust=False,
            progress=False,
            threads=True,
        )

        if data.empty:
            return {}

        quotes: dict[str, dict[str, Any]] = {}

        for symbol in normalized_symbols:
            try:
                symbol_data = YahooProvider._extract_symbol_data(
                    data=data,
                    symbol=symbol,
                    total_symbols=len(normalized_symbols),
                )

                close_series = symbol_data["Close"].dropna()

                if close_series.empty:
                    continue

                price = float(close_series.iloc[-1])

                previous_close = (
                    float(close_series.iloc[-2])
                    if len(close_series) >= 2
                    else price
                )

                change = price - previous_close

                change_pct = (
                    (change / previous_close) * 100
                    if previous_close
                    else 0.0
                )

                volume_series = symbol_data.get("Volume")

                volume = None

                if volume_series is not None:
                    valid_volume = volume_series.dropna()

                    if not valid_volume.empty:
                        volume = int(valid_volume.iloc[-1])

                quotes[symbol] = {
                    "symbol": symbol,
                    "price": round(price, 4),
                    "previous_close": round(previous_close, 4),
                    "change": round(change, 4),
                    "change_pct": round(change_pct, 4),
                    "volume": volume,
                }

            except (KeyError, IndexError, TypeError, ValueError):
                continue

        return quotes

    @staticmethod
    def _extract_symbol_data(
        data: pd.DataFrame,
        symbol: str,
        total_symbols: int,
    ) -> pd.DataFrame:
        """
        Normaliza la estructura devuelta por yfinance.

        Con varios símbolos, las columnas suelen ser MultiIndex.
        Con un único símbolo, puede devolverse un DataFrame convencional.
        """
        if total_symbols == 1:
            if isinstance(data.columns, pd.MultiIndex):
                first_level = data.columns.get_level_values(0)

                if symbol in first_level:
                    return data[symbol]

                second_level = data.columns.get_level_values(1)

                if symbol in second_level:
                    return data.xs(symbol, axis=1, level=1)

            return data

        if not isinstance(data.columns, pd.MultiIndex):
            raise KeyError(f"Missing grouped data for {symbol}")

        first_level = data.columns.get_level_values(0)

        if symbol in first_level:
            return data[symbol]

        second_level = data.columns.get_level_values(1)

        if symbol in second_level:
            return data.xs(symbol, axis=1, level=1)

        raise KeyError(f"Missing market data for {symbol}")

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