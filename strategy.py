# ============================================================================
#  STRATEGY ENGINE — Pivot + SuperTrend (7,3) + Filters
#  Exact same logic as the TradingView Pine Script
# ============================================================================

import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)


class SuperTrendCalculator:
    """Calculate SuperTrend indicator."""

    @staticmethod
    def calculate(df: pd.DataFrame, period: int = 7, multiplier: float = 3.0) -> pd.DataFrame:
        """
        Add SuperTrend columns to DataFrame.
        Requires: high, low, close columns.
        Adds: st_value, st_direction (1=Bullish/green, -1=Bearish/red)
        """
        df = df.copy()
        hl2 = (df['high'] + df['low']) / 2

        # ATR calculation
        tr1 = df['high'] - df['low']
        tr2 = abs(df['high'] - df['close'].shift(1))
        tr3 = abs(df['low'] - df['close'].shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()

        # Basic bands
        upper_basic = hl2 + (multiplier * atr)
        lower_basic = hl2 - (multiplier * atr)

        # Final bands with logic
        upper_band = pd.Series(np.nan, index=df.index)
        lower_band = pd.Series(np.nan, index=df.index)
        supertrend = pd.Series(np.nan, index=df.index)
        direction = pd.Series(0, index=df.index)  # 1=Bull, -1=Bear

        for i in range(period, len(df)):
            # Upper band
            if upper_basic.iloc[i] < upper_band.iloc[i-1] or df['close'].iloc[i-1] > upper_band.iloc[i-1]:
                upper_band.iloc[i] = upper_basic.iloc[i]
            else:
                upper_band.iloc[i] = upper_band.iloc[i-1]

            # Lower band
            if lower_basic.iloc[i] > lower_band.iloc[i-1] or df['close'].iloc[i-1] < lower_band.iloc[i-1]:
                lower_band.iloc[i] = lower_basic.iloc[i]
            else:
                lower_band.iloc[i] = lower_band.iloc[i-1]

            # Direction & Value
            if i == period:
                if df['close'].iloc[i] <= upper_band.iloc[i]:
                    direction.iloc[i] = -1  # Bearish
                    supertrend.iloc[i] = upper_band.iloc[i]
                else:
                    direction.iloc[i] = 1   # Bullish
                    supertrend.iloc[i] = lower_band.iloc[i]
            else:
                prev_dir = direction.iloc[i-1]
                if prev_dir == 1:  # Was bullish
                    if df['close'].iloc[i] < lower_band.iloc[i]:
                        direction.iloc[i] = -1  # Flip to bearish
                        supertrend.iloc[i] = upper_band.iloc[i]
                    else:
                        direction.iloc[i] = 1
                        supertrend.iloc[i] = lower_band.iloc[i]
                else:  # Was bearish
                    if df['close'].iloc[i] > upper_band.iloc[i]:
                        direction.iloc[i] = 1  # Flip to bullish
                        supertrend.iloc[i] = lower_band.iloc[i]
                    else:
                        direction.iloc[i] = -1
                        supertrend.iloc[i] = upper_band.iloc[i]

        df['st_value'] = supertrend
        df['st_direction'] = direction  # 1=Bullish, -1=Bearish
        return df


class PivotCalculator:
    """Calculate Classic Pivot Points."""

    @staticmethod
    def calculate(prev_high: float, prev_low: float, prev_close: float) -> dict:
        pp = (prev_high + prev_low + prev_close) / 3
        r1 = 2 * pp - prev_low
        r2 = pp + (prev_high - prev_low)
        r3 = prev_high + 2 * (pp - prev_low)
        s1 = 2 * pp - prev_high
        s2 = pp - (prev_high - prev_low)
        s3 = prev_low - 2 * (prev_high - pp)
        return {
            'PP': round(pp, 2),
            'R1': round(r1, 2), 'R2': round(r2, 2), 'R3': round(r3, 2),
            'S1': round(s1, 2), 'S2': round(s2, 2), 'S3': round(s3, 2),
        }


class VWAPCalculator:
    """Calculate intraday VWAP."""

    @staticmethod
    def calculate(df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df['date'] = df['datetime'].dt.date
        df['typical_price'] = (df['high'] + df['low'] + df['close']) / 3
        df['tp_volume'] = df['typical_price'] * df['volume']

        # Cumulative within each day
        df['cum_tp_vol'] = df.groupby('date')['tp_volume'].cumsum()
        df['cum_vol'] = df.groupby('date')['volume'].cumsum()
        df['vwap'] = df['cum_tp_vol'] / df['cum_vol'].replace(0, np.nan)

        df.drop(columns=['date', 'typical_price', 'tp_volume', 'cum_tp_vol', 'cum_vol'],
                inplace=True)
        return df


class StrategyEngine:
    """
    Main strategy engine — runs the Pivot + SuperTrend logic.
    Returns signals: 'SELL_PUT', 'SELL_CALL', 'EXIT_PUT', 'EXIT_CALL', 'FORCE_EXIT', or None
    """

    def __init__(self, config):
        self.config = config
        self.st_calc = SuperTrendCalculator()
        self.pivot_calc = PivotCalculator()
        self.vwap_calc = VWAPCalculator()

        # Trade state
        self.trade_type = 0       # 0=flat, 1=short PUT, -1=short CALL
        self.trade_entry = None
        self.trade_sl = None
        self.trade_strike = None
        self.daily_trades = 0
        self.daily_pnl = 0.0
        self.total_wins = 0
        self.total_losses = 0

        # Previous candle state (for crossover detection)
        self.prev_close = None
        self.prev_st_dir = None

    def reset_daily(self):
        """Reset daily counters."""
        self.daily_trades = 0
        self.daily_pnl = 0.0

    def get_atm_strike(self, spot: float) -> int:
        """Calculate ATM strike."""
        interval = self.config.STRIKE_INTERVAL
        return int(round(spot / interval) * interval)

    def process_candle(self, df: pd.DataFrame, pivots: dict, vix: float) -> dict:
        """
        Process the latest candle and return signal info.

        Returns dict:
        {
            'signal': 'SELL_PUT' | 'SELL_CALL' | 'EXIT_PUT' | 'EXIT_CALL' | 'FORCE_EXIT' | None,
            'spot': float,
            'atm_strike': int,
            'supertrend': float,
            'st_direction': str,
            'vwap': float,
            'pivots': dict,
            'signal_score': int,
            'trade_type': int,
            'trade_strike': int,
            'trail_sl': float,
            'vix': float,
        }
        """
        if df.empty or len(df) < 20:
            return {'signal': None}

        # ---- Calculate indicators ----
        df = self.st_calc.calculate(df, self.config.ST_PERIOD, self.config.ST_MULTIPLIER)
        df = self.vwap_calc.calculate(df)

        # Get latest and previous candle
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) >= 2 else latest

        spot = float(latest['close'])
        prev_close = float(prev['close'])
        st_value = float(latest['st_value'])
        st_dir = int(latest['st_direction'])      # 1=Bull, -1=Bear
        prev_st_dir = int(prev['st_direction'])
        vwap = float(latest['vwap']) if not np.isnan(latest['vwap']) else spot
        volume = float(latest['volume'])
        avg_vol = float(df['volume'].tail(20).mean())

        atm_strike = self.get_atm_strike(spot)

        R1 = pivots['R1']
        S1 = pivots['S1']

        # ---- Time checks ----
        current_time = latest['datetime']
        no_trade_h, no_trade_m = map(int, self.config.NO_TRADE_AFTER.split(':'))
        exit_h, exit_m = map(int, self.config.FORCE_EXIT_TIME.split(':'))

        current_hour = current_time.hour
        current_min = current_time.minute

        no_new_trade = (current_hour > no_trade_h or
                        (current_hour == no_trade_h and current_min >= no_trade_m))
        force_exit_time = (current_hour > exit_h or
                           (current_hour == exit_h and current_min >= exit_m))

        # ---- Breakout detection ----
        cross_above_r1 = spot > R1 and prev_close <= R1
        cross_below_s1 = spot < S1 and prev_close >= S1

        # ---- SuperTrend flip detection ----
        st_flip_bear = st_dir == -1 and prev_st_dir == 1
        st_flip_bull = st_dir == 1 and prev_st_dir == -1

        is_bull_st = st_dir == 1
        is_bear_st = st_dir == -1

        # ---- Filter checks ----
        vwap_bull_ok = (not self.config.USE_VWAP_FILTER) or (spot > vwap)
        vwap_bear_ok = (not self.config.USE_VWAP_FILTER) or (spot < vwap)
        vol_ok = (not self.config.USE_VOLUME_FILTER) or (volume >= avg_vol * self.config.VOLUME_MULTIPLIER)
        vix_ok = (not self.config.USE_VIX_FILTER) or (self.config.VIX_MIN <= vix <= self.config.VIX_MAX)

        can_trade = (self.daily_trades < self.config.MAX_TRADES_PER_DAY and
                     not no_new_trade and vix_ok)

        # ---- Signal score ----
        bull_score = sum([cross_above_r1, is_bull_st, vwap_bull_ok, vol_ok, True])  # 5th = base
        bear_score = sum([cross_below_s1, is_bear_st, vwap_bear_ok, vol_ok, True])

        signal = None

        # ---- EXIT LOGIC (check first) ----
        if self.trade_type == 1 and st_flip_bear:
            pnl = spot - self.trade_entry
            self.daily_pnl += pnl
            if pnl > 0:
                self.total_wins += 1
            else:
                self.total_losses += 1
            signal = 'EXIT_PUT'
            self.trade_type = 0
            self.trade_entry = None
            self.trade_sl = None

        elif self.trade_type == -1 and st_flip_bull:
            pnl = self.trade_entry - spot
            self.daily_pnl += pnl
            if pnl > 0:
                self.total_wins += 1
            else:
                self.total_losses += 1
            signal = 'EXIT_CALL'
            self.trade_type = 0
            self.trade_entry = None
            self.trade_sl = None

        elif self.trade_type != 0 and force_exit_time:
            if self.trade_type == 1:
                pnl = spot - self.trade_entry
            else:
                pnl = self.trade_entry - spot
            self.daily_pnl += pnl
            if pnl > 0:
                self.total_wins += 1
            else:
                self.total_losses += 1
            signal = 'FORCE_EXIT'
            self.trade_type = 0
            self.trade_entry = None
            self.trade_sl = None

        # ---- ENTRY LOGIC ----
        elif cross_above_r1 and is_bull_st and vwap_bull_ok and vol_ok and can_trade and self.trade_type != 1:
            if self.trade_type == -1:  # Close opposite
                pnl = self.trade_entry - spot
                self.daily_pnl += pnl
            self.trade_type = 1
            self.trade_entry = spot
            self.trade_sl = st_value
            self.trade_strike = atm_strike
            self.daily_trades += 1
            signal = 'SELL_PUT'
            bull_score = sum([True, is_bull_st, vwap_bull_ok, vol_ok, True])

        elif cross_below_s1 and is_bear_st and vwap_bear_ok and vol_ok and can_trade and self.trade_type != -1:
            if self.trade_type == 1:  # Close opposite
                pnl = spot - self.trade_entry
                self.daily_pnl += pnl
            self.trade_type = -1
            self.trade_entry = spot
            self.trade_sl = st_value
            self.trade_strike = atm_strike
            self.daily_trades += 1
            signal = 'SELL_CALL'
            bear_score = sum([True, is_bear_st, vwap_bear_ok, vol_ok, True])

        # ---- Update trailing SL ----
        if self.trade_type != 0:
            self.trade_sl = st_value

        # ---- Build result ----
        result = {
            'signal': signal,
            'spot': spot,
            'atm_strike': atm_strike,
            'supertrend': st_value,
            'st_direction': 'BULLISH' if is_bull_st else 'BEARISH',
            'vwap': vwap,
            'pivots': pivots,
            'signal_score': bull_score if signal == 'SELL_PUT' else bear_score if signal == 'SELL_CALL' else 0,
            'trade_type': self.trade_type,
            'trade_strike': self.trade_strike or atm_strike,
            'trail_sl': self.trade_sl or st_value,
            'vix': vix,
            'daily_trades': self.daily_trades,
            'daily_pnl': self.daily_pnl,
            'total_wins': self.total_wins,
            'total_losses': self.total_losses,
            'volume_ok': vol_ok,
            'vwap_ok': vwap_bull_ok if is_bull_st else vwap_bear_ok,
            'vix_ok': vix_ok,
        }
        return result
