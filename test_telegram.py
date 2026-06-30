#!/usr/bin/env python3
# ============================================================================
#  TEST — Verify Telegram + NSE connection
#  Run:  python test_telegram.py
# ============================================================================

import config
from telegram_sender import TelegramBot
from data_fetcher import NSEFetcher


def test():
    print("=" * 50)
    print("  🧪 TESTING TELEGRAM + NSE CONNECTION")
    print("=" * 50)

    # ---- Test 1: NSE Connection ----
    print("\n1️⃣  Testing NSE India connection...")
    try:
        nse = NSEFetcher()
        ltp = nse.get_ltp()
        vix = nse.get_india_vix()
        prev = nse.get_previous_day_hlc()
        if ltp > 0:
            print(f"   ✅ Nifty LTP: {ltp}")
            print(f"   ✅ India VIX: {vix}")
            if prev:
                print(f"   ✅ Prev Day — H:{prev['high']:.2f}  L:{prev['low']:.2f}  C:{prev['close']:.2f}")
            else:
                print(f"   ⚠️ Prev day HLC not available (market may be closed)")
        else:
            print(f"   ⚠️ LTP returned 0 (market may be closed)")
    except Exception as e:
        print(f"   ❌ NSE connection failed: {e}")

    # ---- Test 2: 5-min candles ----
    print("\n2️⃣  Testing 5-min candle data...")
    try:
        df = nse.get_5min_candles(days=2)
        if not df.empty:
            print(f"   ✅ Got {len(df)} candles")
            print(f"   ✅ Latest: {df.iloc[-1]['datetime']}  Close: {df.iloc[-1]['close']:.2f}")
        else:
            print(f"   ⚠️ No candle data (market may be closed)")
    except Exception as e:
        print(f"   ❌ Candle fetch failed: {e}")

    # ---- Test 3: Telegram ----
    print("\n3️⃣  Testing Telegram bot...")
    bot = TelegramBot(config.TELEGRAM_BOT_TOKEN, config.TELEGRAM_CHAT_ID)

    ok = bot.send_message("🧪 <b>Test Message</b>\nNifty ATM Option Bot is working! ✅")
    print(f"   {'✅ Message sent!' if ok else '❌ Failed! Check BOT_TOKEN & CHAT_ID in config.py'}")

    # ---- Test 4: Sample signal ----
    if ok:
        print("\n4️⃣  Sending sample SELL PUT signal...")
        ok2 = bot.send_sell_put_signal(
            spot=24855.30, atm_strike=24850, r1=24820.50,
            supertrend=24790.75, vwap=24780.00, signal_score=5,
            hedge_strike=24550,
        )
        print(f"   {'✅ Sample signal sent!' if ok2 else '❌ Failed!'}")

        print("\n5️⃣  Sending sample EXIT signal...")
        ok3 = bot.send_exit_signal(
            exit_type="SL", spot=24780.00, strike=24850,
            option_type="PE", reason="SuperTrend flipped BEARISH",
            pnl_pts=-30.5,
        )
        print(f"   {'✅ Exit signal sent!' if ok3 else '❌ Failed!'}")

    print("\n" + "=" * 50)
    print("  Check your Telegram for messages!")
    print("=" * 50)


if __name__ == "__main__":
    test()
