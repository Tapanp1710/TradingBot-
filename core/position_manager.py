# File: core/position_manager.py
# Purpose: Monitor open positions and trigger exits (SL / TP / trailing / stale)
# Design: Decision-only. No capital math. No strategy logic.

import time
import logging
from typing import Callable, Dict
from datetime import datetime, timezone

from core.portfolio import Portfolio
from core.execution_engine import ExecutionEngine

logger = logging.getLogger("PositionManager")


class PositionManager:
    """
    Monitors open positions and decides WHEN to exit.
    Execution is delegated to ExecutionEngine.
    """

    def __init__(
        self,
        portfolio: Portfolio,
        execution_engine: ExecutionEngine,
        price_fetcher: Callable[[str], float],
        config,
    ):
        self.portfolio = portfolio
        self.execution_engine = execution_engine
        self.get_price = price_fetcher
        self.config = config

        # Prevent repeated exit attempts
        self._exit_cooldowns: Dict[str, float] = {}

        # Lightweight observability
        self.exit_stats = {
            "STOP_LOSS": 0,
            "TAKE_PROFIT": 0,
            "TRAILING_STOP": 0,
            "STALE_EXIT": 0,
        }

        logger.info("📊 PositionManager initialized")

    # =====================================================
    # MAIN MONITOR
    # =====================================================

    def monitor_positions(self):
        if not self.portfolio.positions:
            return

        for symbol in list(self.portfolio.positions.keys()):
            try:
                self._check_position(symbol)
            except Exception as e:
                logger.error(f"❌ Position check failed for {symbol}: {e}")

    # =====================================================
    # PER-POSITION LOGIC
    # =====================================================

    def _check_position(self, symbol: str):
        position = self.portfolio.positions.get(symbol)
        if not position:
            return

        # Cooldown to prevent repeated sell spam
        last_exit = self._exit_cooldowns.get(symbol)
        if last_exit and time.time() - last_exit < 5:
            return

        current_price = self.get_price(symbol)
        if not current_price or current_price <= 0:
            return

        # Track highest price
        if current_price > position.highest_price:
            position.highest_price = current_price

        # === EXIT PRIORITY ORDER ===
        # 1. Stop Loss
        # 2. Take Profit
        # 3. Trailing Stop
        # 4. Stale Exit

        if self._check_stop_loss(symbol, position, current_price):
            return

        if self._check_take_profit(symbol, position, current_price):
            return

        if self._handle_trailing_stop(symbol, position, current_price):
            return

        self._check_stale_position(symbol, position, current_price)

    # =====================================================
    # EXIT CONDITIONS
    # =====================================================

    def _check_stop_loss(self, symbol, position, price) -> bool:
        if position.stop_loss and price <= position.stop_loss:
            logger.warning(f"🛑 {symbol}: Stop Loss hit @ ${price:.2f}")
            self._exit(symbol, price, "STOP_LOSS")
            return True
        return False

    def _check_take_profit(self, symbol, position, price) -> bool:
        if position.take_profit and price >= position.take_profit:
            logger.info(f"🎯 {symbol}: Take Profit hit @ ${price:.2f}")
            self._exit(symbol, price, "TAKE_PROFIT")
            return True
        return False

    # =====================================================
    # TRAILING STOP
    # =====================================================

    def _handle_trailing_stop(self, symbol, position, price) -> bool:
        if not self.config.ENABLE_ATR_TRAILING:
            return False

        atr = position.metadata.get("atr")
        if not atr or atr <= 0:
            return False

        entry_price = position.entry_price
        activation_price = entry_price + (
            atr * self.config.TRAIL_ACTIVATE_ATR_MULT
        )

        if price < activation_price:
            return False

        if not position.trailing_active:
            position.trailing_active = True
            logger.info(f"📈 {symbol}: Trailing stop activated")

        trail_distance = atr * self.config.TRAIL_DISTANCE_ATR_MULT
        new_stop = price - trail_distance

        if not position.stop_loss or new_stop > position.stop_loss:
            position.stop_loss = new_stop
            logger.debug(f"🔁 {symbol}: Trailing SL → ${new_stop:.2f}")

        return False

    # =====================================================
    # STALE EXIT
    # =====================================================

    def _check_stale_position(self, symbol, position, price):
        max_hold = self.config.MAX_POSITION_HOURS
        if not max_hold:
            return

        hold_hours = (
            datetime.now(timezone.utc) - position.entry_time
        ).total_seconds() / 3600

        if hold_hours < max_hold:
            return

        atr = position.metadata.get("atr")
        if not atr or atr <= 0:
            return

        pnl_pct = (
            (price - position.entry_price) / position.entry_price
        ) * 100

        atr_band = (
            atr / position.entry_price
        ) * 100 * self.config.STALE_BAND_ATR_MULT

        if abs(pnl_pct) < atr_band:
            logger.warning(
                f"⏰ {symbol}: Stale exit after {hold_hours:.1f}h "
                f"({pnl_pct:+.2f}%)"
            )
            self._exit(symbol, price, "STALE_EXIT")

    # =====================================================
    # EXIT HANDLER
    # =====================================================

    def _exit(self, symbol: str, price: float, reason: str):
        self._exit_cooldowns[symbol] = time.time()
        self.exit_stats[reason] += 1

        self.execution_engine.execute_sell(
            symbol=symbol,
            price=price,
            reason=reason,
        )

    # =====================================================
    # STATS
    # =====================================================

    def get_stats(self) -> Dict:
        return dict(self.exit_stats)
