#!/usr/bin/env python3
# ============================================================================
#  TEST — Verify Telegram + Yahoo Finance
#  Run:  python test_telegram.py
# ============================================================================

import config
from telegram_sender import TelegramBot
from data_fetcher import DataFetcher


def test():
    print("=" * 50)
    print("  🧪 TESTING TELEGRAM + DATA CONNECTION")
    print("=" * 50)

    # ---- Test 1: Yahoo Finance ----
    print("\n1️⃣  Testing Yahoo Finance connection...")
    try:
        fetcher = DataFetcher()
        prev = fetcher.get_previous_day_hlc()
        if prev:
            print(f"   ✅ Prev Day — H:{prev['high']:.2f}  L:{prev['low']:.2f}  C:{prev['close']:.2f}")
        else:
            print("   ⚠️ Could not get prev day data")
    except Exception as e:
        print(f"   ❌ Failed: {e}")

    # ---- Test 2: 5-min candles ----
    print("\n2️⃣  Testing 5-min candle data...")
    try:
        df = fetcher.get_5min_candles(days=2)
        if not df.empty:
            print(f"   ✅ Got {len(df)} candles")
            print(f"   ✅ Latest: {df.iloc[-1]['datetime']}  Close: {df.iloc[-1]['close']:.2f}")
        else:
            print("   ⚠️ No candle data (market may be closed)")
    except Exception as e:
        print(f"   ❌ Failed: {e}")

    # ---- Test 3: India VIX ----
    print("\n3️⃣  Testing India VIX...")
    try:
        vix = fetcher.get_india_vix()
        print(f"   ✅ India VIX: {vix:.2f}")
    except Exception as e:
        print(f"   ❌ Failed: {e}")

    # ---- Test 4: Telegram ----
    print("\n4️⃣  Testing Telegram bot...")
    bot = TelegramBot(config.TELEGRAM_BOT_TOKEN, config.TELEGRAM_CHAT_ID)

    ok = bot.send_message("🧪 <b>Test Message</b>\nNifty ATM Option Bot is working! ✅")
    print(f"   {'✅ Message sent!' if ok else '❌ Failed! Check BOT_TOKEN & CHAT_ID in config.py / .env'}")

    if ok:
        print("\n5️⃣  Sending sample SELL PUT signal...")
        ok2 = bot.send_sell_put_signal(
            spot=24855.30, atm_strike=24850, r1=24820.50,
            supertrend=24790.75, vwap=24780.00, signal_score=5,
            hedge_strike=24550,
        )
        print(f"   {'✅ Signal sent!' if ok2 else '❌ Failed!'}")

    print("\n" + "=" * 50)
    print("  Check your Telegram for messages!")
    print("=" * 50)


if __name__ == "__main__":
    test()
