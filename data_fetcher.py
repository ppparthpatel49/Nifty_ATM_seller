# ============================================================================
#  DATA FETCHER — Yahoo Finance (Reliable, Free, Works Everywhere)
# ============================================================================

import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class DataFetcher:
    """
    Fetches Nifty data using Yahoo Finance.
    ✅ FREE
    ✅ No account needed
    ✅ Works on local PC, GitHub Actions, VPS — everywhere
    ✅ No blocking / 403 issues
    ⚠️ ~15 min delay during market hours (good enough for 5-min candle strategy)
    """

    def __init__(self):
        try:
            import yfinance as yf
            self.yf = yf
            logger.info("Yahoo Finance initialized.")
        except ImportError:
            raise ImportError("Install yfinance: pip install yfinance")

    # ----------------------------------------------------------------
    #  NIFTY 5-MINUTE CANDLES
    # ----------------------------------------------------------------

    def get_5min_candles(self, days: int = 5) -> pd.DataFrame:
        """
        Fetch 5-minute OHLCV candles for Nifty 50.
        Returns DataFrame with: datetime, open, high, low, close, volume
        """
        try:
            ticker = self.yf.Ticker("^NSEI")
            df = ticker.history(period=f"{days}d", interval="5m")

            if df.empty:
                logger.warning("Yahoo returned empty 5-min data.")
                return pd.DataFrame()

            df = df.reset_index()
            df.columns = [c.lower() for c in df.columns]

            # Rename date → datetime if needed
            if "datetime" not in df.columns and "date" in df.columns:
                df = df.rename(columns={"date": "datetime"})

            # Convert to IST and remove timezone info
            if df["datetime"].dt.tz is not None:
                df["datetime"] = df["datetime"].dt.tz_convert("Asia/Kolkata")
            df["datetime"] = df["datetime"].dt.tz_localize(None)

            df = df[["datetime", "open", "high", "low", "close", "volume"]].copy()
            df = df.sort_values("datetime").reset_index(drop=True)

            logger.info(f"Fetched {len(df)} candles. Latest: {df.iloc[-1]['datetime']}")
            return df

        except Exception as e:
            logger.error(f"5-min candle fetch error: {e}")
            return pd.DataFrame()

    # ----------------------------------------------------------------
    #  NIFTY LTP (Latest Traded Price)
    # ----------------------------------------------------------------

    def get_ltp(self) -> float:
        """Get Nifty last traded price."""
        try:
            ticker = self.yf.Ticker("^NSEI")
            data = ticker.history(period="1d", interval="1m")
            if not data.empty:
                return float(data["Close"].iloc[-1])
        except Exception as e:
            logger.error(f"LTP fetch error: {e}")
        return 0.0

    # ----------------------------------------------------------------
    #  PREVIOUS DAY HIGH / LOW / CLOSE (for Pivot calculation)
    # ----------------------------------------------------------------

    def get_previous_day_hlc(self) -> dict:
        """
        Get previous trading day's High, Low, Close.
        Returns: {'high': float, 'low': float, 'close': float}
        """
        try:
            ticker = self.yf.Ticker("^NSEI")
            df = ticker.history(period="7d", interval="1d")

            if len(df) < 2:
                logger.error("Not enough daily data for prev day HLC.")
                return None

            # Second-to-last row = previous completed trading day
            prev = df.iloc[-2]
            result = {
                "high": float(prev["High"]),
                "low": float(prev["Low"]),
                "close": float(prev["Close"]),
            }
            logger.info(
                f"Prev day HLC: H={result['high']:.2f} "
                f"L={result['low']:.2f} C={result['close']:.2f}"
            )
            return result

        except Exception as e:
            logger.error(f"Previous day HLC error: {e}")
            return None

    # ----------------------------------------------------------------
    #  INDIA VIX
    # ----------------------------------------------------------------

    def get_india_vix(self) -> float:
        """Get current India VIX value."""
        try:
            ticker = self.yf.Ticker("^INDIAVIX")
            data = ticker.history(period="5d", interval="1d")
            if not data.empty:
                vix = float(data["Close"].iloc[-1])
                logger.info(f"India VIX: {vix:.2f}")
                return vix
        except Exception as e:
            logger.error(f"VIX fetch error: {e}")
        return 15.0  # Safe default
