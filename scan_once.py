#!/usr/bin/env python3
# ============================================================================
#  🤖 SINGLE SCAN — For GitHub Actions / Cron Jobs
#
#  Runs ONE scan cycle: fetch data → check signals → send Telegram if triggered.
#  Designed for scheduled runners (GitHub Actions, cron, etc.)
#
#  Usage: python scan_once.py
# ============================================================================

import json
import os
import logging
import sys
from datetime import datetime

import config
from data_fetcher import NSEFetcher
from strategy import StrategyEngine, PivotCalculator
from telegram_sender import TelegramBot

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# ---- State file to persist trade state between runs ----
STATE_FILE = "bot_state.json"


def load_state() -> dict:
    """Load saved state from previous run."""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return {
        "trade_type": 0,
        "trade_entry": None,
        "trade_sl": None,
        "trade_strike": None,
        "daily_trades": 0,
        "daily_pnl": 0.0,
        "total_wins": 0,
        "total_losses": 0,
        "last_signal": None,
        "last_date": None,
    }


def save_state(state: dict):
    """Save state for next run."""
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def main():
    logger.info("=" * 50)
    logger.info("🤖 NIFTY BOT — Single Scan")
    logger.info("=" * 50)

    # ---- Validate credentials ----
    if not config.TELEGRAM_BOT_TOKEN or config.TELEGRAM_BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        logger.error("❌ TELEGRAM_BOT_TOKEN not set! Add it to GitHub Secrets or .env file.")
        sys.exit(1)
    if not config.TELEGRAM_CHAT_ID or config.TELEGRAM_CHAT_ID == "YOUR_CHAT_ID_HERE":
        logger.error("❌ TELEGRAM_CHAT_ID not set! Add it to GitHub Secrets or .env file.")
        sys.exit(1)

    # ---- Initialize ----
    telegram = TelegramBot(config.TELEGRAM_BOT_TOKEN, config.TELEGRAM_CHAT_ID)
    nse = NSEFetcher()
    strategy = StrategyEngine(config)

    # ---- Load previous state ----
    state = load_state()
    today = datetime.now().strftime("%Y-%m-%d")

    # Reset daily counters if new day
    if state["last_date"] != today:
        state["daily_trades"] = 0
        state["daily_pnl"] = 0.0
        state["last_signal"] = None
        logger.info("New trading day — counters reset.")

    # Restore strategy state
    strategy.trade_type = state["trade_type"]
    strategy.trade_entry = state["trade_entry"]
    strategy.trade_sl = state["trade_sl"]
    strategy.trade_strike = state["trade_strike"]
    strategy.daily_trades = state["daily_trades"]
    strategy.daily_pnl = state["daily_pnl"]
    strategy.total_wins = state["total_wins"]
    strategy.total_losses = state["total_losses"]

    # ---- Get pivot points ----
    prev_hlc = nse.get_previous_day_hlc()
    if not prev_hlc:
        logger.error("❌ Could not get previous day HLC. Exiting.")
        sys.exit(1)

    pivots = PivotCalculator.calculate(prev_hlc["high"], prev_hlc["low"], prev_hlc["close"])
    logger.info(f"Pivots: R1={pivots['R1']} | PP={pivots['PP']} | S1={pivots['S1']}")

    # ---- Get 5-min candles ----
    df = nse.get_5min_candles(days=3)
    if df.empty:
        logger.warning("No candle data available. Exiting.")
        sys.exit(0)

    # ---- Get VIX ----
    vix = nse.get_india_vix()

    # ---- Run strategy ----
    result = strategy.process_candle(df, pivots, vix)

    signal = result.get("signal")
    spot = result.get("spot", 0)
    atm = result.get("atm_strike", 0)
    st_val = result.get("supertrend", 0)
    st_dir = result.get("st_direction", "")
    vwap = result.get("vwap", 0)
    score = result.get("signal_score", 0)
    hedge_offset = config.STRIKE_INTERVAL * 6

    trade_str = (
        f"SHORT {result['trade_strike']} PE" if result["trade_type"] == 1
        else f"SHORT {result['trade_strike']} CE" if result["trade_type"] == -1
        else "FLAT"
    )
    logger.info(
        f"Spot: {spot:.1f} | ATM: {atm} | ST: {st_dir} @ {st_val:.1f} | "
        f"R1: {pivots['R1']} | S1: {pivots['S1']} | Pos: {trade_str} | "
        f"Signal: {signal or 'None'}"
    )

    # ---- Send Telegram if signal ----
    if signal and signal != state["last_signal"]:

        if signal == "SELL_PUT":
            telegram.send_sell_put_signal(
                spot=spot, atm_strike=atm, r1=pivots["R1"],
                supertrend=st_val, vwap=vwap, signal_score=score,
                hedge_strike=atm - hedge_offset,
            )
            logger.info(f"🟢 SELL PUT sent: {atm} PE")

        elif signal == "SELL_CALL":
            telegram.send_sell_call_signal(
                spot=spot, atm_strike=atm, s1=pivots["S1"],
                supertrend=st_val, vwap=vwap, signal_score=score,
                hedge_strike=atm + hedge_offset,
            )
            logger.info(f"🔴 SELL CALL sent: {atm} CE")

        elif signal == "EXIT_PUT":
            telegram.send_exit_signal(
                exit_type="SL", spot=spot, strike=result["trade_strike"],
                option_type="PE", reason="SuperTrend flipped BEARISH",
                pnl_pts=result["daily_pnl"],
            )
            logger.info("⚠️ EXIT PUT sent")

        elif signal == "EXIT_CALL":
            telegram.send_exit_signal(
                exit_type="SL", spot=spot, strike=result["trade_strike"],
                option_type="CE", reason="SuperTrend flipped BULLISH",
                pnl_pts=result["daily_pnl"],
            )
            logger.info("⚠️ EXIT CALL sent")

        elif signal == "FORCE_EXIT":
            opt = "PE" if result["trade_type"] == 1 else "CE"
            telegram.send_exit_signal(
                exit_type="TIME", spot=spot, strike=result["trade_strike"],
                option_type=opt, reason="Force exit — market closing",
                pnl_pts=result["daily_pnl"],
            )
            logger.info("⏰ FORCE EXIT sent")

        state["last_signal"] = signal
    else:
        logger.info("No new signal.")

    # ---- Save state for next run ----
    state["trade_type"] = strategy.trade_type
    state["trade_entry"] = strategy.trade_entry
    state["trade_sl"] = strategy.trade_sl
    state["trade_strike"] = strategy.trade_strike
    state["daily_trades"] = strategy.daily_trades
    state["daily_pnl"] = strategy.daily_pnl
    state["total_wins"] = strategy.total_wins
    state["total_losses"] = strategy.total_losses
    state["last_date"] = today

    save_state(state)
    logger.info(f"State saved. Done. ✅")


if __name__ == "__main__":
    main()
