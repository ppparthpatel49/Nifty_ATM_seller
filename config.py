# ============================================================================
#  ⚙️ CONFIGURATION
# ============================================================================
#
#  Credentials are loaded from ENVIRONMENT VARIABLES (safe for GitHub).
#  Set them in GitHub Secrets or your local .env file.
#
#  LOCAL: Create a file named .env in this folder:
#     TELEGRAM_BOT_TOKEN=7123456789:AAHxxxxxxx
#     TELEGRAM_CHAT_ID=1234567890
#
#  GITHUB ACTIONS: Add them as Repository Secrets (Settings → Secrets)
#
# ============================================================================

import os

# ---- Load .env file if it exists (for local runs) ----
def _load_env():
    env_file = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_file):
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    os.environ.setdefault(key.strip(), val.strip())

_load_env()

# ---- TELEGRAM ----
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID   = os.environ.get("TELEGRAM_CHAT_ID", "")

# ---- DATA SOURCE ----
NIFTY_SYMBOL       = "NIFTY 50"

# ---- STRATEGY ----
TIMEFRAME          = "5m"
STRIKE_INTERVAL    = 50

# SuperTrend
ST_PERIOD          = 7
ST_MULTIPLIER      = 3.0

# Filters
USE_VWAP_FILTER    = False
USE_VOLUME_FILTER  = False
VOLUME_MULTIPLIER  = 1.0
USE_VIX_FILTER     = True
VIX_MIN            = 12.0
VIX_MAX            = 25.0

# Risk Management
MAX_TRADES_PER_DAY = 3
NO_TRADE_AFTER     = "14:30"
FORCE_EXIT_TIME    = "15:15"

# Scan Interval
SCAN_INTERVAL_SEC  = 15

# Logging
LOG_FILE           = "nifty_bot.log"
