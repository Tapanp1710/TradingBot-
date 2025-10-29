"""
Loss Streak Detector v2.0 - FULLY FIXED
Prevents trading after consecutive losses with proper method names
"""
import logging
from datetime import datetime, timedelta

logger = logging.getLogger("TradingBot")


class StreakDetector:
    """Track consecutive losses and enforce cooldowns"""

    def __init__(self, config):
        self.config = config
        self.consecutive_losses = 0
        self.last_loss_time = None
        self.cooldown_until = None
        self.recent_losses_by_symbol = {}  # Track losses per symbol

        # Configuration
        self.max_consecutive_losses = getattr(config, 'MAX_CONSECUTIVE_LOSSES', 3)
        self.cooldown_hours = getattr(config, 'COOLDOWN_AFTER_LOSSES_HOURS', 2)
        self.prevent_revenge_trading = getattr(config, 'PREVENT_REVENGE_TRADING', True)
        self.revenge_cooldown_mins = getattr(config, 'REVENGE_TRADE_COOLDOWN_MINS', 30)

        logger.info(f"Streak Detector initialized: max_losses={self.max_consecutive_losses}, cooldown={self.cooldown_hours}h")

    def record_trade(self, symbol: str, profit: float):
        """
        Record trade result
        Args:
            symbol: Trading symbol
            profit: Net P&L (positive = profit, negative = loss)
        """
        if profit < 0:
            # Loss recorded
            self.consecutive_losses += 1
            self.last_loss_time = datetime.now()

            # Calculate cooldown
            if self.consecutive_losses >= self.max_consecutive_losses:
                self.cooldown_until = datetime.now() + timedelta(hours=self.cooldown_hours)
                logger.warning(f"Loss streak detected! {self.consecutive_losses} consecutive losses")
                logger.warning(f"Trading paused until {self.cooldown_until.strftime('%H:%M:%S')}")

            # Track per-symbol losses for revenge trading prevention
            if self.prevent_revenge_trading:
                self.recent_losses_by_symbol[symbol] = datetime.now()
        else:
            # Profit - reset streak
            if self.consecutive_losses > 0:
                logger.info(f"Winning trade! Streak reset (was {self.consecutive_losses} losses)")
            self.consecutive_losses = 0
            self.cooldown_until = None

    def should_trade(self) -> bool:
        """
        Check if trading is allowed globally
        Returns: True if trading allowed, False if blocked by cooldown
        """
        # Check global cooldown
        if self.cooldown_until:
            if datetime.now() < self.cooldown_until:
                return False
            else:
                # Cooldown expired
                logger.info("Cooldown period ended - resuming trading")
                self.cooldown_until = None
                self.consecutive_losses = 0

        return True

    def can_trade_symbol(self, symbol: str) -> bool:
        """
        Check if specific symbol can be traded (revenge trading prevention)
        Args:
            symbol: Trading symbol to check
        Returns: True if symbol can be traded, False if in cooldown
        """
        if not self.prevent_revenge_trading:
            return True

        if symbol in self.recent_losses_by_symbol:
            time_since_loss = (datetime.now() - self.recent_losses_by_symbol[symbol]).total_seconds() / 60

            if time_since_loss < self.revenge_cooldown_mins:
                logger.debug(f"Skipping {symbol} - recent loss {time_since_loss:.0f}m ago (cooldown: {self.revenge_cooldown_mins}m)")
                return False
            else:
                # Cooldown expired for this symbol
                del self.recent_losses_by_symbol[symbol]

        return True

    def get_status(self) -> dict:
        """
        Get current streak status
        Returns: Dict with streak information
        """
        return {
            'consecutive_losses': self.consecutive_losses,
            'cooldown_active': self.cooldown_until is not None,
            'cooldown_until': self.cooldown_until,
            'symbols_in_cooldown': list(self.recent_losses_by_symbol.keys())
        }

    def reset(self):
        """Reset all streak data"""
        self.consecutive_losses = 0
        self.last_loss_time = None
        self.cooldown_until = None
        self.recent_losses_by_symbol.clear()
        logger.info("Streak detector reset")
