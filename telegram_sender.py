# ============================================================================
#  TELEGRAM MESSAGE SENDER
# ============================================================================

import requests
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class TelegramBot:
    """Sends formatted trading signals to Telegram."""

    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"

    def send_message(self, text: str, parse_mode: str = "HTML") -> bool:
        """Send a text message to Telegram."""
        try:
            url = f"{self.base_url}/sendMessage"
            payload = {
                "chat_id": self.chat_id,
                "text": text,
                "parse_mode": parse_mode,
                "disable_web_page_preview": True,
            }
            resp = requests.post(url, json=payload, timeout=10)
            if resp.status_code == 200:
                logger.info("Telegram message sent successfully.")
                return True
            else:
                logger.error(f"Telegram error: {resp.status_code} - {resp.text}")
                return False
        except Exception as e:
            logger.error(f"Telegram send failed: {e}")
            return False

    # ------------------------------------------------------------------
    #  FORMATTED SIGNAL MESSAGES
    # ------------------------------------------------------------------

    def send_sell_put_signal(self, spot: float, atm_strike: int, r1: float,
                             supertrend: float, vwap: float, signal_score: int,
                             hedge_strike: int = None):
        """Send SELL PUT entry signal."""
        now = datetime.now().strftime("%H:%M:%S")
        msg = (
            "🟢🟢🟢 <b>SELL ATM PUT</b> 🟢🟢🟢\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            f"⏰ Time: <b>{now} IST</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            f"📊 Nifty Spot: <b>{spot:.2f}</b>\n"
            f"🎯 ATM Strike: <b>{atm_strike}</b>\n"
            f"📌 Action: <b>SELL {atm_strike} PE</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            f"📈 Breakout Above R1: <b>{r1:.2f}</b>\n"
            f"✅ SuperTrend (7,3): <b>BULLISH @ {supertrend:.2f}</b>\n"
            f"✅ VWAP: <b>{vwap:.2f}</b>\n"
            f"⚡ Signal Strength: <b>{signal_score}/5</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            f"🛑 Trailing SL: <b>SuperTrend @ {supertrend:.2f}</b>\n"
            f"   (Exit when ST flips RED)\n"
        )
        if hedge_strike:
            msg += (
                "━━━━━━━━━━━━━━━━━━━━━\n"
                f"🛡️ Hedge: <b>BUY {hedge_strike} PE</b>\n"
            )
        msg += (
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "⚠️ <i>Use proper position sizing!</i>"
        )
        return self.send_message(msg)

    def send_sell_call_signal(self, spot: float, atm_strike: int, s1: float,
                               supertrend: float, vwap: float, signal_score: int,
                               hedge_strike: int = None):
        """Send SELL CALL entry signal."""
        now = datetime.now().strftime("%H:%M:%S")
        msg = (
            "🔴🔴🔴 <b>SELL ATM CALL</b> 🔴🔴🔴\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            f"⏰ Time: <b>{now} IST</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            f"📊 Nifty Spot: <b>{spot:.2f}</b>\n"
            f"🎯 ATM Strike: <b>{atm_strike}</b>\n"
            f"📌 Action: <b>SELL {atm_strike} CE</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            f"📉 Breakdown Below S1: <b>{s1:.2f}</b>\n"
            f"✅ SuperTrend (7,3): <b>BEARISH @ {supertrend:.2f}</b>\n"
            f"✅ VWAP: <b>{vwap:.2f}</b>\n"
            f"⚡ Signal Strength: <b>{signal_score}/5</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            f"🛑 Trailing SL: <b>SuperTrend @ {supertrend:.2f}</b>\n"
            f"   (Exit when ST flips GREEN)\n"
        )
        if hedge_strike:
            msg += (
                "━━━━━━━━━━━━━━━━━━━━━\n"
                f"🛡️ Hedge: <b>BUY {hedge_strike} CE</b>\n"
            )
        msg += (
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "⚠️ <i>Use proper position sizing!</i>"
        )
        return self.send_message(msg)

    def send_exit_signal(self, exit_type: str, spot: float, strike: int,
                          option_type: str, reason: str, pnl_pts: float = None):
        """Send EXIT signal."""
        now = datetime.now().strftime("%H:%M:%S")
        emoji = "⚠️" if "SL" in reason.upper() or "FLIP" in reason.upper() else "✅"
        msg = (
            f"{emoji}{emoji}{emoji} <b>EXIT {option_type}</b> {emoji}{emoji}{emoji}\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            f"⏰ Time: <b>{now} IST</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            f"📊 Nifty Spot: <b>{spot:.2f}</b>\n"
            f"📌 Close: <b>{strike} {option_type}</b>\n"
            f"📋 Reason: <b>{reason}</b>\n"
        )
        if pnl_pts is not None:
            pnl_emoji = "💰" if pnl_pts >= 0 else "💸"
            msg += f"{pnl_emoji} PnL: <b>{pnl_pts:+.1f} pts</b>\n"
        msg += "━━━━━━━━━━━━━━━━━━━━━"
        return self.send_message(msg)

    def send_status_update(self, spot: float, atm_strike: int, supertrend: float,
                            st_dir: str, r1: float, s1: float, pp: float,
                            vwap: float, trade_type: int, trade_strike: int,
                            trail_sl: float, daily_trades: int, daily_pnl: float):
        """Send periodic status update."""
        now = datetime.now().strftime("%H:%M:%S")
        pos_text = (
            f"SHORT {trade_strike} PE" if trade_type == 1
            else f"SHORT {trade_strike} CE" if trade_type == -1
            else "NO POSITION"
        )
        msg = (
            "📋 <b>STATUS UPDATE</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            f"⏰ {now} IST\n"
            f"📊 Spot: <b>{spot:.2f}</b>  |  ATM: <b>{atm_strike}</b>\n"
            f"📈 R1: {r1:.2f}  |  PP: {pp:.2f}  |  S1: {s1:.2f}\n"
            f"🔀 SuperTrend: <b>{st_dir} @ {supertrend:.2f}</b>\n"
            f"📉 VWAP: {vwap:.2f}\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            f"💼 Position: <b>{pos_text}</b>\n"
            f"🛑 Trail SL: {trail_sl:.2f}\n" if trade_type != 0 else ""
            f"📊 Trades: {daily_trades}  |  PnL: {daily_pnl:+.1f} pts\n"
            "━━━━━━━━━━━━━━━━━━━━━"
        )
        return self.send_message(msg)

    def send_bot_started(self):
        """Send bot startup notification."""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        msg = (
            "🤖 <b>NIFTY ATM OPTION BOT STARTED</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            f"⏰ {now} IST\n"
            "📊 Strategy: Pivot R1/S1 + SuperTrend (7,3)\n"
            "🔔 Alerts: SELL PUT / SELL CALL / EXIT\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "✅ Bot is running. Monitoring Nifty..."
        )
        return self.send_message(msg)

    def send_bot_stopped(self, reason: str = "Manual stop"):
        """Send bot shutdown notification."""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        msg = (
            "🛑 <b>BOT STOPPED</b>\n"
            f"⏰ {now} IST\n"
            f"📋 Reason: {reason}"
        )
        return self.send_message(msg)

    def send_daily_summary(self, total_trades: int, wins: int, losses: int,
                            total_pnl: float):
        """Send end-of-day summary."""
        now = datetime.now().strftime("%Y-%m-%d")
        win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
        pnl_emoji = "💰" if total_pnl >= 0 else "💸"
        msg = (
            "📊 <b>DAILY SUMMARY</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            f"📅 Date: {now}\n"
            f"📈 Total Trades: <b>{total_trades}</b>\n"
            f"✅ Wins: {wins}  |  ❌ Losses: {losses}\n"
            f"🎯 Win Rate: <b>{win_rate:.0f}%</b>\n"
            f"{pnl_emoji} Net PnL: <b>{total_pnl:+.1f} pts</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━"
        )
        return self.send_message(msg)
