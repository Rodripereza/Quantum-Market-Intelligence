import pandas as pd




def calculate_obv(
    market_data: pd.DataFrame,
    price_column: str = "Close",
    volume_column: str = "Volume",
) -> pd.Series:
    """Calculate On-Balance Volume."""
    if not isinstance(market_data, pd.DataFrame) or market_data.empty:
        raise ValueError("market_data must be a non-empty pandas DataFrame.")
    for column in (price_column, volume_column):
        if column not in market_data.columns:
            raise ValueError(f"Missing required column: {column}")

    close = pd.to_numeric(market_data[price_column], errors="coerce")
    volume = pd.to_numeric(market_data[volume_column], errors="coerce").fillna(0.0)

    direction = close.diff().apply(
        lambda value: 1 if value > 0 else -1 if value < 0 else 0
    )
    obv = (direction * volume).fillna(0.0).cumsum()
    obv.name = "OBV"
    return obv


def calculate_adl(
    market_data: pd.DataFrame,
) -> pd.Series:
    """Calculate Accumulation/Distribution Line."""
    if not isinstance(market_data, pd.DataFrame) or market_data.empty:
        raise ValueError("market_data must be a non-empty pandas DataFrame.")

    required = {"High", "Low", "Close", "Volume"}
    missing = required.difference(market_data.columns)
    if missing:
        raise ValueError(
            "ADL requires columns: " + ", ".join(sorted(missing))
        )

    high = pd.to_numeric(market_data["High"], errors="coerce")
    low = pd.to_numeric(market_data["Low"], errors="coerce")
    close = pd.to_numeric(market_data["Close"], errors="coerce")
    volume = pd.to_numeric(market_data["Volume"], errors="coerce").fillna(0.0)

    spread = high - low
    mfm = (((close - low) - (high - close)) / spread).where(spread != 0, 0.0)
    mfv = mfm.fillna(0.0) * volume
    adl = mfv.cumsum()
    adl.name = "ADL"
    return adl


def calculate_relative_volume(
    market_data: pd.DataFrame,
    period: int = 20,
    volume_column: str = "Volume",
) -> pd.Series:
    """Calculate relative volume against the rolling mean."""
    if not isinstance(market_data, pd.DataFrame) or market_data.empty:
        raise ValueError("market_data must be a non-empty pandas DataFrame.")
    if volume_column not in market_data.columns:
        raise ValueError(f"Missing required column: {volume_column}")

    volume = pd.to_numeric(market_data[volume_column], errors="coerce")
    average = volume.rolling(period, min_periods=period).mean()
    rvol = (volume / average).where(average != 0)
    rvol.name = f"RVOL_{period}"
    return rvol


def calculate_volume_zscore(
    market_data: pd.DataFrame,
    period: int = 20,
    volume_column: str = "Volume",
) -> pd.Series:
    """Calculate rolling volume z-score."""
    if not isinstance(market_data, pd.DataFrame) or market_data.empty:
        raise ValueError("market_data must be a non-empty pandas DataFrame.")
    if volume_column not in market_data.columns:
        raise ValueError(f"Missing required column: {volume_column}")

    volume = pd.to_numeric(market_data[volume_column], errors="coerce")
    mean = volume.rolling(period, min_periods=period).mean()
    std = volume.rolling(period, min_periods=period).std(ddof=0)
    zscore = ((volume - mean) / std).where(std != 0, 0.0)
    zscore.name = f"VOLUME_Z_{period}"
    return zscore
