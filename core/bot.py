"""
Trading Bot Orchestrator
Design: Thin coordinator, zero intelligence
"""

import time
import signal
import threading
import logging
from datetime import datetime, timezone
from typing import List

from config import Config

from core.exchange import ExchangeManager
from core.strategy import TradingStrategy
from core.execution_engine import ExecutionEngine
from core.portfolio import Portfolio
from core.position_manager import PositionManager
from utils.risk_manager import RiskManager

# Optional protections
try:
    from core.streak_detector import StreakDetector
except ImportError:
    StreakDetector = None

try:
    from emergency_exit import EmergencyExitManager
except ImportError:
    EmergencyExitManager = None

logger = logging.getLogger("TradingBot")


class TradingBot:
    """
    Production-grade trading bot orchestrator.
    """

    def __init__(self, config: Config):
        self.config = config
        self.running = True
        self.shutdown_event = threading.Event()

        # OS signal handling
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)

        # === Core components ===
        self.exchange = ExchangeManager(
            config.EXCHANGE,
            config.API_KEY if not config.PAPER_TRADING else "",
            config.API_SECRET if not config.PAPER_TRADING else "",
        )

        self.portfolio = Portfolio(config.STARTING_CAPITAL)

        self.execution_engine = ExecutionEngine(
            portfolio=self.portfolio,
            trading_fee_pct=config.TRADING_FEE,
            apply_tax=config.APPLY_INDIAN_TAX,
            tax_pct=config.CAPITAL_GAINS_TAX,
        )

        self.strategy = TradingStrategy(config, exchange_manager=self.exchange)
        self.risk_manager = RiskManager(config)
        self.position_manager = PositionManager(
            portfolio=self.portfolio,
            execution_engine=self.execution_engine,
            config=config,
            exchange=self.exchange,
        )

        self.streak_detector = StreakDetector(config) if StreakDetector else None

        self.emergency_manager = (
            EmergencyExitManager(self)
            if EmergencyExitManager and config.EMERGENCY_EXIT_ENABLED
            else None
        )

        self.scan_count = 0

        self._log_startup()

    # ======================================================
    # SIGNAL HANDLING
    # ======================================================

    def _handle_shutdown(self, *_):
        if not self.running:
            return
        logger.warning("🛑 Shutdown signal received")
        self.running = False
        self.shutdown_event.set()

    # ======================================================
    # MAIN LOOP
    # ======================================================

    def run(self):
        logger.info("🚀 Trading bot started")

        try:
            while self.running:
                self._run_cycle()
        finally:
            self.shutdown()

    def _run_cycle(self):
        logger.info("=" * 70)
        logger.info(
            f"🔍 SCAN #{self.scan_count + 1} | "
            f"Positions: {self.portfolio.position_count()}/"
            f"{self.config.MAX_OPEN_POSITIONS}"
        )
        logger.info("=" * 70)

        # Emergency system
        if self.emergency_manager:
            self.emergency_manager.check_emergency_conditions()

        # Manage existing positions
        self.position_manager.monitor_positions()

        # Capacity check
        if self.portfolio.position_count() >= self.config.MAX_OPEN_POSITIONS:
            logger.info("⏸️ Max position capacity reached")
            self._sleep()
            return

        # Scan opportunities
        opportunities = self._scan_market()

        for opp in opportunities:
            if not self.running:
                break

            if self.streak_detector and not self.streak_detector.should_trade():
                logger.warning("🚫 Trading blocked by streak detector")
                break

            self._execute_opportunity(opp)

        self.scan_count += 1
        self._sleep()

    # ======================================================
    # MARKET SCANNING
    # ======================================================

    def _scan_market(self) -> List[dict]:
        watchlist = self.config.WATCHLIST
        results = []

        for symbol in watchlist:
            if symbol in self.portfolio.positions:
                continue

            try:
                df = self.exchange.fetch_ohlcv(symbol, "1h", 100)
                if df is None or len(df) < 50:
                    continue

                signal = self.strategy.generate_signal(df, symbol)
                if signal["signal"] != "BUY":
                    continue

                if signal["confidence"] < self.config.SIGNAL_CONFIDENCE_THRESHOLD:
                    continue

                price = self.exchange.fetch_current_price(symbol)
                atr = signal["indicators"].get("atr", 0)

                position_value = self.risk_manager.calculate_position_size(
                    available_capital=self.portfolio.cash_balance,
                    total_capital=self.portfolio.cash_balance,
                    confidence=signal["confidence"],
                )

                if position_value < self.config.MIN_POSITION_USD:
                    continue

                results.append(
                    {
                        "symbol": symbol,
                        "price": price,
                        "confidence": signal["confidence"],
                        "atr": atr,
                        "signal_data": signal,
                    }
                )

            except Exception as e:
                logger.debug(f"{symbol} scan error: {e}")

        results.sort(key=lambda x: x["confidence"], reverse=True)
        return results

    # ======================================================
    # EXECUTION
    # ======================================================

    def _execute_opportunity(self, opp: dict):
        symbol = opp["symbol"]
        price = opp["price"]
        confidence = opp["confidence"]
        atr = opp["atr"]

        size = self.risk_manager.calculate_position_size(
            available_capital=self.portfolio.cash_balance,
            total_capital=self.portfolio.cash_balance,
            confidence=confidence,
        )

        if size <= 0:
            return

        stop_loss, take_profit = self.position_manager.calculate_exits(
            entry_price=price,
            atr=atr,
            side="BUY",
        )

        self.execution_engine.execute_buy(
            symbol=symbol,
            size=size / price,
            price=price,
            confidence=confidence,
            stop_loss=stop_loss,
            take_profit=take_profit,
            metadata={"strategy": "primary"},
        )

    # ======================================================
    # UTIL
    # ======================================================

    def _sleep(self):
        for _ in range(self.config.SCAN_INTERVAL):
            if not self.running:
                break
            time.sleep(1)

    # ======================================================
    # SHUTDOWN
    # ======================================================

    def shutdown(self):
        logger.info("🛑 Shutting down trading bot")

        snapshot = self.portfolio.snapshot()
        logger.info(f"📊 Final snapshot: {snapshot}")

        logger.info("✅ Shutdown complete")
