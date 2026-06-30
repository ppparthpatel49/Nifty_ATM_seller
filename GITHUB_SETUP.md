# 🚀 GitHub Upload & Cloud Deploy — Step by Step

---

## Step 1: Create GitHub Account (skip if you have one)
1. Go to https://github.com
2. Sign up (free)

---

## Step 2: Install Git on your PC
- **Windows:** Download from https://git-scm.com/download/win
- **Mac:** `brew install git`
- **Linux:** `sudo apt install git`

Verify: Open CMD/Terminal → `git --version`

---

## Step 3: Create a New GitHub Repository

### Option A: From GitHub Website
1. Go to https://github.com/new
2. Repository name: `nifty-telegram-bot`
3. Description: `Nifty ATM Option Seller with Telegram Alerts`
4. Select: **Private** (keeps your code private)
5. Do NOT check "Add README" (we already have one)
6. Click **Create repository**

---

## Step 4: Push Code to GitHub

Open CMD/Terminal on your PC. Run these commands ONE BY ONE:

```bash
# 1. Navigate to the bot folder
cd path/to/nifty_telegram_bot

# 2. Initialize git
git init

# 3. Add all files
git add .

# 4. Commit
git commit -m "Initial commit: Nifty ATM Option Seller Bot"

# 5. Connect to your GitHub repo (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/nifty-telegram-bot.git

# 6. Push
git branch -M main
git push -u origin main
```

Enter your GitHub username & password (or personal access token) when asked.

✅ **Code is now on GitHub!**

---

## Step 5: Add Telegram Secrets to GitHub

1. Go to your repo: `https://github.com/YOUR_USERNAME/nifty-telegram-bot`
2. Click **Settings** (tab at top)
3. Left sidebar → **Secrets and variables** → **Actions**
4. Click **New repository secret**

Add these 2 secrets:

| Name | Value |
|------|-------|
| `TELEGRAM_BOT_TOKEN` | `7123456789:AAHxxxxxxxxxxxxxxx` (from @BotFather) |
| `TELEGRAM_CHAT_ID` | `1234567890` (from @userinfobot) |

---

## Step 6: Enable GitHub Actions

1. Go to **Actions** tab in your repo
2. You'll see a yellow banner: "Workflows aren't being run..."
3. Click **"I understand my workflows, go ahead and enable them"**

✅ **Bot is now live on cloud!**

---

## Step 7: Test It

1. Go to **Actions** tab
2. Click **"Nifty ATM Option Bot"** on the left
3. Click **"Run workflow"** button (right side)
4. Click **"Run workflow"** (green button)
5. Wait 1-2 minutes
6. Check your **Telegram** for messages!

---

## Step 8: Sit Back 🎉

The bot now runs **automatically**:
- **When:** Every 5 minutes, Monday-Friday
- **Time:** 9:15 AM - 3:30 PM IST only
- **Cost:** ₹0 (GitHub gives 2000 free minutes/month)
- **What it does:** Checks Nifty, runs strategy, sends Telegram alert if signal

---

## 📊 Monitor Your Bot

- Go to **Actions** tab anytime to see run history
- Each run shows: ✅ success or ❌ failure
- Click any run → see logs → verify what happened

---

## 🔄 Update the Code

If you change settings or code:

```bash
cd path/to/nifty_telegram_bot
git add .
git commit -m "Updated settings"
git push
```

GitHub Actions will automatically use the updated code on next run.

---

## ⚠️ Important Notes

| Topic | Detail |
|-------|--------|
| **Private repo** | Keep it PRIVATE so no one sees your secrets |
| **Free minutes** | GitHub gives 2000 min/month. Bot uses ~75 min/day × 22 days = ~1650 min. Fits within free tier! |
| **Cron delays** | GitHub Actions cron can delay 1-10 min during busy times. For exact timing, run `main.py` locally |
| **State persistence** | `scan_once.py` saves state to `bot_state.json` between runs. On GitHub Actions, state resets each run (no persistence). For full state tracking, run locally |
| **Weekends/Holidays** | Bot auto-skips weekends. NSE holidays are NOT auto-detected — it will run but find no data (harmless) |
