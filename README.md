# 🤖 Nifty ATM Option Seller — Telegram Bot

**Automated Telegram alerts for selling ATM Nifty weekly options** based on Pivot Point breakout + SuperTrend (7,3) trailing stop loss.

> 📡 **Data:** NSE India (Free, no broker account needed)
> ☁️ **Cloud:** Runs FREE on GitHub Actions during market hours
> 📱 **Alerts:** Telegram messages for every entry & exit

---

## ⚡ Strategy

```
📈 Nifty closes ABOVE Pivot R1  →  SELL ATM PUT
📉 Nifty closes BELOW Pivot S1  →  SELL ATM CALL
🛑 SuperTrend (7,3) flips       →  EXIT (Trailing SL)
```

### Filters
- ✅ SuperTrend (7,3) direction confirmation
- ✅ VWAP — trade with institutional flow
- ✅ Volume — avoid fake breakouts
- ✅ India VIX — avoid extreme volatility days
- ✅ Max 3 trades/day, no entry after 2:30 PM, force exit 3:15 PM

---

## 📱 Sample Telegram Alert

```
🟢🟢🟢 SELL ATM PUT 🟢🟢🟢
━━━━━━━━━━━━━━━━━━━━━
⏰ Time: 09:50:15 IST
━━━━━━━━━━━━━━━━━━━━━
📊 Nifty Spot: 24855.30
🎯 ATM Strike: 24850
📌 Action: SELL 24850 PE
━━━━━━━━━━━━━━━━━━━━━
📈 Breakout Above R1: 24820.50
✅ SuperTrend: BULLISH @ 24790.75
⚡ Signal Strength: 5/5
━━━━━━━━━━━━━━━━━━━━━
🛑 Trailing SL: SuperTrend @ 24790.75
🛡️ Hedge: BUY 24550 PE
━━━━━━━━━━━━━━━━━━━━━
```

---

## 🚀 Setup

### Option A: Run FREE on GitHub Actions (Recommended)

Zero cost. Runs automatically Mon-Fri during market hours.

#### 1. Fork this repo
Click **Fork** (top right) to copy to your GitHub.

#### 2. Add Telegram secrets
Go to your forked repo → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

| Secret Name | Value |
|-------------|-------|
| `TELEGRAM_BOT_TOKEN` | Your bot token from @BotFather |
| `TELEGRAM_CHAT_ID` | Your chat ID from @userinfobot |

#### 3. Enable Actions
Go to **Actions** tab → Click **"I understand my workflows, go ahead and enable them"**

#### 4. Done! ✅
The bot runs automatically every 5 minutes during market hours (Mon-Fri, 9:15 AM - 3:30 PM IST). You'll get Telegram alerts whenever a signal triggers.

#### 5. Test manually
Actions tab → **Nifty ATM Option Bot** → **Run workflow** → **Run workflow**

---

### Option B: Run on your PC

#### 1. Clone
```bash
git clone https://github.com/YOUR_USERNAME/nifty-telegram-bot.git
cd nifty-telegram-bot
```

#### 2. Install packages
```bash
pip install -r requirements.txt
```

#### 3. Create `.env` file
```bash
TELEGRAM_BOT_TOKEN=7123456789:AAHxxxxxxxxxxxxxxx
TELEGRAM_CHAT_ID=1234567890
```

#### 4. Test
```bash
python test_telegram.py
```

#### 5. Run
```bash
python main.py
```

---

## 📁 Project Structure

```
├── .github/
│   └── workflows/
│       └── nifty_bot.yml      ← GitHub Actions (auto-runs in cloud)
├── config.py                  ← Settings (reads from env vars)
├── main.py                    ← Continuous bot (for local PC)
├── scan_once.py               ← Single scan (for GitHub Actions/cron)
├── strategy.py                ← Pivot + SuperTrend logic
├── data_fetcher.py            ← NSE India data fetcher
├── telegram_sender.py         ← Telegram message formatting
├── test_telegram.py           ← Test setup
├── requirements.txt           ← Python packages
├── start_bot.bat              ← Windows double-click launcher
├── .env                       ← YOUR secrets (never pushed)
├── .gitignore                 ← Keeps secrets safe
└── README.md                  ← This file
```

---

## ⚙️ Configuration

All strategy settings are in `config.py`:

| Setting | Default | Description |
|---------|---------|-------------|
| `ST_PERIOD` | 7 | SuperTrend ATR period |
| `ST_MULTIPLIER` | 3.0 | SuperTrend multiplier |
| `STRIKE_INTERVAL` | 50 | Nifty strike gap |
| `USE_VWAP_FILTER` | True | VWAP confirmation |
| `USE_VOLUME_FILTER` | True | Volume filter |
| `USE_VIX_FILTER` | True | India VIX range check |
| `VIX_MIN / VIX_MAX` | 12 / 25 | Safe VIX range |
| `MAX_TRADES_PER_DAY` | 3 | Daily trade limit |
| `NO_TRADE_AFTER` | 14:30 | No new trades after this |
| `FORCE_EXIT_TIME` | 15:15 | Force close all positions |
| `SCAN_INTERVAL_SEC` | 15 | Check every N seconds (local) |

---

## 📡 Data Source

| Data | Source | Delay |
|------|--------|-------|
| Nifty LTP | NSE India API | ~3 sec |
| India VIX | NSE India API | ~3 sec |
| Previous day HLC | NSE + Yahoo fallback | Instant |
| 5-min candles | Yahoo Finance + NSE live tick | Near real-time |

**Cost: ₹0 | Account needed: None**

---

## 🔔 Telegram Bot Setup

1. Open Telegram → search **@BotFather** → send `/newbot`
2. Copy the **bot token**
3. Search **@userinfobot** → send `/start` → copy **chat ID**
4. Open your new bot → send `/start` to activate it

---

## ❓ FAQ

**Q: Is this free?**
A: Yes. NSE data is free, GitHub Actions gives 2000 free minutes/month, Telegram is free.

**Q: Will it auto-trade?**
A: No. It sends alerts only. You place orders manually.

**Q: How accurate is the data?**
A: NSE LTP has ~3 second delay. 5-min candles from Yahoo may have ~15 min lag, but latest tick comes from NSE directly.

**Q: Will GitHub Actions always run exactly every 5 min?**
A: GitHub Actions cron can have delays of 1-10 minutes during busy periods. For exact timing, run locally with `main.py`.

---

## ⚠️ Disclaimer

> This bot is for **educational purposes only**. Options selling carries **unlimited risk**.
> Always use stop losses and proper position sizing. Paper trade before using real money.
> Past performance does not guarantee future results. The author is not responsible for any financial losses.

---

## 📄 License

MIT License — free to use, modify, and distribute.
