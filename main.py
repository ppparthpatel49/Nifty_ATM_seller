#!/usr/bin/env python3
# ============================================================================
#  🤖 NIFTY ATM OPTION SELLER — TELEGRAM BOT
#
#  Data:     NSE India (free, no account, ~3s delay)
#  Strategy: Pivot R1/S1 Breakout + SuperTrend (7,3) Trailing SL
#  Alerts:   Telegram messages for SELL PUT / SELL CALL / EXIT
#
#  Usage:    python main.py
# ============================================================================

import time
import logging
import sys
from datetime import datetime, timedelta

import config
from data_fetcher import NSEFetcher
from strategy import StrategyEngine, PivotCalculator
from telegram_sender import TelegramBot

# ---- Logging ----
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(config.LOG_FILE),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


def is_market_hours() -> bool:
    """Check if current time is within NSE market hours (9:15 AM - 3:30 PM IST)."""
    now = datetime.now()
    market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
    market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
    return market_open <= now <= market_close


def is_weekday() -> bool:
    return datetime.now().weekday() < 5


def wait_for_market_open():
    now = datetime.now()
    market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
    if now < market_open:
        wait_seconds = (market_open - now).total_seconds()
        logger.info(f"Waiting {wait_seconds/60:.0f} min for market open...")
        print(f"\n⏳ Market opens at 9:15 AM IST. Waiting {wait_seconds/60:.0f} min...\n")
        time.sleep(wait_seconds)


def main():
    print("""
    ╔══════════════════════════════════════════════════════╗
    ║   🤖 NIFTY ATM OPTION SELLER — TELEGRAM BOT        ║
    ║   Data:     NSE India (Free, No Account)            ║
    ║   Strategy: Pivot R1/S1 + SuperTrend (7,3)          ║
    ║   Alerts:   Telegram                                ║
    ╚══════════════════════════════════════════════════════╝
    """)

    # ---- Initialize ----
    logger.info("Initializing bot...")

    telegram = TelegramBot(config.TELEGRAM_BOT_TOKEN, config.TELEGRAM_CHAT_ID)

    try:
        nse = NSEFetcher()
        print("📡 Data Source: NSE India (Direct)")
    except Exception as e:
        logger.error(f"NSE init failed: {e}")
        print(f"\n❌ ERROR: {e}")
        return

    strategy = StrategyEngine(config)

    telegram.send_bot_started()
    logger.info("Bot initialized successfully.")
    print("✅ Bot started! Monitoring Nifty...\n")

    # ---- State ----
    last_signal = None
    pivots = None
    prev_date = None
    status_sent_time = None

    # ============================================================
    #  MAIN LOOP
    # ============================================================
    try:
        while True:
            try:
                now = datetime.now()

                # ---- Skip weekends ----
                if not is_weekday():
                    logger.info("Weekend. Sleeping 1 hour...")
                    time.sleep(3600)
                    continue

                # ---- Wait for market hours ----
                if not is_market_hours():
                    if now.hour >= 15 and now.minute >= 35:
                        # After close — send daily summary
                        if prev_date == now.date() and strategy.daily_trades > 0:
                            telegram.send_daily_summary(
                                strategy.daily_trades,
                                strategy.total_wins,
                                strategy.total_losses,
                                strategy.daily_pnl,
                            )
                            prev_date = None
                            strategy.reset_daily()

                        tomorrow = (now + timedelta(days=1)).replace(
                            hour=9, minute=10, second=0, microsecond=0
                        )
                        sleep_secs = (tomorrow - now).total_seconds()
                        logger.info(f"Market closed. Sleeping {sleep_secs/3600:.1f} hrs...")
                        time.sleep(min(sleep_secs, 3600))
                        continue
                    else:
                        wait_for_market_open()
                        continue

                # ---- New day → Recalculate pivots ----
                today = now.date()
                if prev_date != today:
                    logger.info("New day. Calculating pivot points...")
                    prev_hlc = nse.get_previous_day_hlc()
                    if prev_hlc:
                        pivots = PivotCalculator.calculate(
                            prev_hlc["high"], prev_hlc["low"], prev_hlc["close"]
                        )
                        logger.info(f"Pivots: R1={pivots['R1']}, PP={pivots['PP']}, S1={pivots['S1']}")
                        print(f"📊 Pivots: R1={pivots['R1']} | PP={pivots['PP']} | S1={pivots['S1']}")
                    else:
                        logger.error("Failed to get previous day data!")
                        time.sleep(60)
                        continue

                    strategy.reset_daily()
                    prev_date = today
                    last_signal = None

                if pivots is None:
                    logger.error("No pivot data. Retrying...")
                    time.sleep(30)
                    continue

                # ---- Fetch 5-min candles (Yahoo history + NSE live tick) ----
                df = nse.get_5min_candles(days=3)

                if df.empty:
                    logger.warning("No candle data. Retrying...")
                    time.sleep(config.SCAN_INTERVAL_SEC)
                    continue

                # ---- Get VIX ----
                vix = nse.get_india_vix()

                # ---- Run Strategy ----
                result = strategy.process_candle(df, pivots, vix)

                signal = result.get("signal")
                spot = result.get("spot", 0)
                atm = result.get("atm_strike", 0)
                st_val = result.get("supertrend", 0)
                st_dir = result.get("st_direction", "")
                vwap = result.get("vwap", 0)
                score = result.get("signal_score", 0)
                hedge_offset = config.STRIKE_INTERVAL * 6  # 300 pts

                # ---- Live status in terminal ----
                trade_str = (
                    f"SHORT {result['trade_strike']} PE" if result["trade_type"] == 1
                    else f"SHORT {result['trade_strike']} CE" if result["trade_type"] == -1
                    else "FLAT"
                )
                print(
                    f"\r⏰ {now.strftime('%H:%M:%S')} | "
                    f"Spot: {spot:.1f} | ATM: {atm} | "
                    f"ST: {st_dir} @ {st_val:.1f} | "
                    f"R1: {pivots['R1']} | S1: {pivots['S1']} | "
                    f"Pos: {trade_str} | "
                    f"Trades: {result['daily_trades']} | PnL: {result['daily_pnl']:+.1f}",
                    end="", flush=True,
                )

                # ---- Send Telegram Signals ----
                if signal and signal != last_signal:

                    if signal == "SELL_PUT":
                        hedge_strike = atm - hedge_offset
                        telegram.send_sell_put_signal(
                            spot=spot, atm_strike=atm, r1=pivots["R1"],
                            supertrend=st_val, vwap=vwap, signal_score=score,
                            hedge_strike=hedge_strike,
                        )
                        logger.info(f"🟢 SELL PUT: {atm} PE @ {spot}")
                        print(f"\n🟢 SELL PUT SIGNAL SENT: {atm} PE")

                    elif signal == "SELL_CALL":
                        hedge_strike = atm + hedge_offset
                        telegram.send_sell_call_signal(
                            spot=spot, atm_strike=atm, s1=pivots["S1"],
                            supertrend=st_val, vwap=vwap, signal_score=score,
                            hedge_strike=hedge_strike,
                        )
                        logger.info(f"🔴 SELL CALL: {atm} CE @ {spot}")
                        print(f"\n🔴 SELL CALL SIGNAL SENT: {atm} CE")

                    elif signal == "EXIT_PUT":
                        telegram.send_exit_signal(
                            exit_type="SL", spot=spot,
                            strike=result["trade_strike"],
                            option_type="PE",
                            reason="SuperTrend flipped BEARISH",
                            pnl_pts=result["daily_pnl"],
                        )
                        logger.info(f"⚠️ EXIT PUT @ {spot}")
                        print(f"\n⚠️ EXIT PUT SIGNAL SENT")

                    elif signal == "EXIT_CALL":
                        telegram.send_exit_signal(
                            exit_type="SL", spot=spot,
                            strike=result["trade_strike"],
                            option_type="CE",
                            reason="SuperTrend flipped BULLISH",
                            pnl_pts=result["daily_pnl"],
                        )
                        logger.info(f"⚠️ EXIT CALL @ {spot}")
                        print(f"\n⚠️ EXIT CALL SIGNAL SENT")

                    elif signal == "FORCE_EXIT":
                        opt_type = "PE" if result["trade_type"] == 1 else "CE"
                        telegram.send_exit_signal(
                            exit_type="TIME", spot=spot,
                            strike=result["trade_strike"],
                            option_type=opt_type,
                            reason="Force exit — market closing",
                            pnl_pts=result["daily_pnl"],
                        )
                        logger.info(f"⏰ FORCE EXIT @ {spot}")
                        print(f"\n⏰ FORCE EXIT SIGNAL SENT")

                    last_signal = signal

                # ---- Status update every 30 min (if in trade) ----
                if status_sent_time is None or (now - status_sent_time).seconds >= 1800:
                    if result["trade_type"] != 0:
                        telegram.send_status_update(
                            spot=spot, atm_strike=atm, supertrend=st_val,
                            st_dir=st_dir, r1=pivots["R1"], s1=pivots["S1"],
                            pp=pivots["PP"], vwap=vwap,
                            trade_type=result["trade_type"],
                            trade_strike=result["trade_strike"],
                            trail_sl=result["trail_sl"],
                            daily_trades=result["daily_trades"],
                            daily_pnl=result["daily_pnl"],
                        )
                        status_sent_time = now

                # ---- Sleep ----
                time.sleep(config.SCAN_INTERVAL_SEC)

            except KeyboardInterrupt:
                raise
            except Exception as e:
                logger.error(f"Loop error: {e}", exc_info=True)
                print(f"\n❌ Error: {e}. Retrying in 30s...")
                time.sleep(30)

    except KeyboardInterrupt:
        print("\n\n🛑 Bot stopped by user.")
        telegram.send_bot_stopped("Manual stop (Ctrl+C)")
        logger.info("Bot stopped by user.")

    finally:
        if strategy.daily_trades > 0:
            telegram.send_daily_summary(
                strategy.daily_trades,
                strategy.total_wins,
                strategy.total_losses,
                strategy.daily_pnl,
            )


if __name__ == "__main__":
    main()
