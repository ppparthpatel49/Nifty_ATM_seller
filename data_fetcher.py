# ============================================================================
#  DATA FETCHER — NSE INDIA DIRECT (Free, No Account, ~3s delay)
# ============================================================================

import pandas as pd
import numpy as np
import requests
import logging
import time
import json
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class NSEFetcher:
    """
    Fetches live Nifty data directly from NSE India website.
    ✅ FREE
    ✅ No broker account needed
    ✅ ~3 second delay (near real-time)
    ⚠️ Don't hit too fast — use 10-15 sec interval to avoid blocks
    """

    BASE_URL = "https://www.nseindia.com"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/126.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9,hi;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": "https://www.nseindia.com/",
            "Connection": "keep-alive",
        })
        self._cookies_time = 0
        self._refresh_cookies()

    # ----------------------------------------------------------------
    #  SESSION / COOKIE MANAGEMENT
    # ----------------------------------------------------------------

    def _refresh_cookies(self):
        """Load NSE homepage to get fresh cookies (needed for API access)."""
        try:
            r = self.session.get(self.BASE_URL, timeout=10)
            r.raise_for_status()
            self._cookies_time = time.time()
            logger.info("NSE cookies refreshed.")
        except Exception as e:
            logger.error(f"Cookie refresh failed: {e}")

    def _ensure_cookies(self):
        """Re-fetch cookies if older than 4 minutes."""
        if time.time() - self._cookies_time > 240:
            self._refresh_cookies()

    def _get(self, endpoint: str) -> dict:
        """Make GET request to NSE API with auto cookie refresh."""
        self._ensure_cookies()
        url = f"{self.BASE_URL}{endpoint}"
        try:
            r = self.session.get(url, timeout=10)
            if r.status_code == 401 or r.status_code == 403:
                logger.warning("NSE 401/403 — refreshing cookies...")
                self._refresh_cookies()
                time.sleep(1)
                r = self.session.get(url, timeout=10)
            r.raise_for_status()
            return r.json()
        except requests.exceptions.JSONDecodeError:
            logger.error(f"NSE returned non-JSON for {endpoint}")
            return {}
        except Exception as e:
            logger.error(f"NSE request error ({endpoint}): {e}")
            return {}

    # ----------------------------------------------------------------
    #  LIVE MARKET DATA
    # ----------------------------------------------------------------

    def get_nifty_quote(self) -> dict:
        """
        Get full Nifty quote — LTP, open, high, low, close, change, etc.

        Returns dict:
        {
            'ltp': float,
            'open': float,
            'high': float,
            'low': float,
            'prev_close': float,
            'change': float,
            'pchange': float,
            'timestamp': str,
        }
        """
        data = self._get("/api/allIndices")
        if data and "data" in data:
            for idx in data["data"]:
                if idx.get("index") == "NIFTY 50":
                    return {
                        "ltp": float(idx.get("last", 0)),
                        "open": float(idx.get("open", 0)),
                        "high": float(idx.get("high", 0)),
                        "low": float(idx.get("low", 0)),
                        "prev_close": float(idx.get("previousClose", 0)),
                        "change": float(idx.get("variation", 0)),
                        "pchange": float(idx.get("percentChange", 0)),
                        "timestamp": idx.get("timeVal", ""),
                    }
        return {}

    def get_ltp(self) -> float:
        """Get Nifty Last Traded Price."""
        q = self.get_nifty_quote()
        return q.get("ltp", 0.0)

    def get_india_vix(self) -> float:
        """Get current India VIX value."""
        data = self._get("/api/allIndices")
        if data and "data" in data:
            for idx in data["data"]:
                if "VIX" in idx.get("index", "").upper():
                    return float(idx.get("last", 15.0))
        return 15.0

    # ----------------------------------------------------------------
    #  PREVIOUS DAY HIGH / LOW / CLOSE (for Pivot calculation)
    # ----------------------------------------------------------------

    def get_previous_day_hlc(self) -> dict:
        """
        Get previous trading day's High, Low, Close from NSE.
        Uses equity market status + allIndices data.

        Returns: {'high': float, 'low': float, 'close': float}
        """
        # Method 1: From /api/chart-databyindex (intraday chart)
        try:
            data = self._get("/api/chart-databyindex?index=NIFTY%2050&preopen=true")
            if data and "gpiData" in data:
                candles = data["gpiData"]
                if candles and len(candles) > 0:
                    # This gives today's intraday data; we need previous day
                    pass
        except:
            pass

        # Method 2: From allIndices — today's OHLC + previousClose
        # previousClose IS the previous day's close
        # For previous day's H/L, we use equity bhavcopy or index history
        try:
            # Try index historical data
            data = self._get("/api/historical/indicesHistory?indexType=NIFTY%2050&from={}&to={}".format(
                (datetime.now() - timedelta(days=10)).strftime("%d-%m-%Y"),
                datetime.now().strftime("%d-%m-%Y"),
            ))
            if data and "data" in data and "indexCloseOnlineRecords" in data["data"]:
                records = data["data"]["indexCloseOnlineRecords"]
                if len(records) >= 2:
                    prev = records[-2]  # Second to last = previous day
                    return {
                        "high": float(prev.get("EOD_HIGH_INDEX_VAL", 0)),
                        "low": float(prev.get("EOD_LOW_INDEX_VAL", 0)),
                        "close": float(prev.get("EOD_CLOSE_INDEX_VAL", 0)),
                    }
        except:
            pass

        # Method 3: Fallback — use today's previousClose + approximate H/L
        q = self.get_nifty_quote()
        if q:
            prev_close = q.get("prev_close", 0)
            if prev_close > 0:
                logger.warning("Using approximate prev day HLC from NSE quote.")
                return {
                    "high": prev_close * 1.005,   # ~0.5% above as estimate
                    "low": prev_close * 0.995,    # ~0.5% below as estimate
                    "close": prev_close,
                }

        # Method 4: Fallback to Yahoo Finance for historical data only
        try:
            import yfinance as yf
            ticker = yf.Ticker("^NSEI")
            df = ticker.history(period="5d", interval="1d")
            if len(df) >= 2:
                prev = df.iloc[-2]
                logger.info("Used Yahoo Finance for prev day HLC.")
                return {
                    "high": float(prev["High"]),
                    "low": float(prev["Low"]),
                    "close": float(prev["Close"]),
                }
        except Exception as e:
            logger.error(f"Yahoo fallback failed: {e}")

        return None

    # ----------------------------------------------------------------
    #  5-MINUTE CANDLE DATA (built from NSE intraday chart)
    # ----------------------------------------------------------------

    def get_intraday_chart(self) -> pd.DataFrame:
        """
        Fetch today's intraday chart data from NSE.
        Returns 1-minute or 5-minute ticks depending on NSE response.
        """
        data = self._get("/api/chart-databyindex?index=NIFTY%2050")
        if not data or "gpiData" not in data:
            return pd.DataFrame()

        candles = data["gpiData"]
        if not candles:
            return pd.DataFrame()

        # NSE returns [[timestamp_ms, value], ...] or similar
        rows = []
        for c in candles:
            try:
                if isinstance(c, (list, tuple)) and len(c) >= 2:
                    ts = c[0]
                    val = c[1]
                    # Timestamp could be milliseconds
                    if ts > 1e12:
                        ts = ts / 1000
                    dt = datetime.fromtimestamp(ts)
                    rows.append({"datetime": dt, "close": float(val)})
            except:
                continue

        if not rows:
            return pd.DataFrame()

        df = pd.DataFrame(rows)
        return df

    def get_5min_candles(self, days: int = 5) -> pd.DataFrame:
        """
        Get 5-minute OHLCV candles.
        
        NSE's chart API gives only today's intraday data.
        For multi-day 5-min candles (needed for SuperTrend), we use
        Yahoo Finance as historical feeder + NSE for latest tick.
        """
        try:
            import yfinance as yf
            ticker = yf.Ticker("^NSEI")
            df = ticker.history(period=f"{days}d", interval="5m")

            if df.empty:
                logger.warning("Yahoo returned empty 5-min data.")
                return pd.DataFrame()

            df = df.reset_index()
            df.columns = [c.lower() for c in df.columns]

            if "datetime" not in df.columns and "date" in df.columns:
                df = df.rename(columns={"date": "datetime"})

            if df["datetime"].dt.tz is not None:
                df["datetime"] = df["datetime"].dt.tz_convert("Asia/Kolkata")
            df["datetime"] = df["datetime"].dt.tz_localize(None)

            df = df[["datetime", "open", "high", "low", "close", "volume"]].copy()
            df = df.sort_values("datetime").reset_index(drop=True)

            # ---- Append latest NSE tick as current candle ----
            nse_ltp = self.get_ltp()
            if nse_ltp > 0 and not df.empty:
                last_candle_time = df["datetime"].iloc[-1]
                now = datetime.now()
                # If NSE tick is more recent than last Yahoo candle
                if now > last_candle_time + timedelta(minutes=5):
                    new_row = {
                        "datetime": now.replace(second=0, microsecond=0),
                        "open": nse_ltp,
                        "high": nse_ltp,
                        "low": nse_ltp,
                        "close": nse_ltp,
                        "volume": 0,
                    }
                    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

            logger.info(f"Fetched {len(df)} candles (Yahoo + NSE live tick)")
            return df

        except ImportError:
            logger.error("yfinance not installed! Run: pip install yfinance")
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"5-min candle fetch error: {e}")
            return pd.DataFrame()
