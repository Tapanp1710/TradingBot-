# File: monitoring/drift_detector.py
# Purpose: Detect statistical drift in strategy performance
# Design: Passive observer, no retraining, no execution logic

from typing import Dict, Optional
import numpy as np
import logging

from analytics.portfolio_stats import PortfolioStats
from config.risk import RiskConfig

logger = logging.getLogger("DriftDetector")


class DriftDetector:
    """
    Detects performance drift using portfolio statistics.
    """

    def __init__(
        self,
        stats: PortfolioStats,
        config: RiskConfig,
        min_trades: int = 30,
        confirmation_window: int = 3,
    ):
        self.stats = stats
        self.config = config

        self.min_trades = min_trades
        self.confirmation_window = confirmation_window

        self._drift_counter = 0
        self._last_state = False

        logger.info("📉 DriftDetector initialized")

    # ======================================================
    # MAIN EVALUATION
    # ======================================================

    def evaluate(self) -> Dict:
        """
        Evaluate whether performance drift is present.
        """
        snapshot = self.stats.snapshot()
        trade_count = snapshot.get("trade_count", 0)

        if trade_count < self.min_trades:
            return self._result(False, "Insufficient trades")

        signals = []

        # ----------------------------
        # 1. WIN RATE DECAY
        # ----------------------------

        win_rate = snapshot.get("win_rate")
        rolling_win_rate = snapshot.get("rolling_win_rate")

        if win_rate and rolling_win_rate:
            if rolling_win_rate < (win_rate * self.config.WIN_RATE_DECAY_FACTOR):
                signals.append("Win rate decay")

        # ----------------------------
        # 2. EXPECTANCY DECAY
        # ----------------------------

        expectancy = snapshot.get("expectancy")
        if expectancy is not None and expectancy < self.config.MIN_EXPECTANCY:
            signals.append("Negative expectancy")

        # ----------------------------
        # 3. RETURN VOLATILITY SPIKE
        # ----------------------------

        volatility = snapshot.get("return_volatility")
        if volatility and volatility > self.config.MAX_RETURN_VOLATILITY:
            signals.append("Volatility spike")

        # ----------------------------
        # 4. EQUITY TREND REVERSAL
        # ----------------------------

        slope = snapshot.get("equity_slope")
        if slope is not None and slope < self.config.MIN_EQUITY_SLOPE:
            signals.append("Equity slope reversal")

        # ----------------------------
        # DECISION LOGIC
        # ----------------------------

        drift_detected = len(signals) >= self.config.MIN_DRIFT_SIGNALS

        if drift_detected:
            self._drift_counter += 1
        else:
            self._drift_counter = max(0, self._drift_counter - 1)

        confirmed = self._drift_counter >= self.confirmation_window

        if confirmed and not self._last_state:
            logger.error(f"🚨 DRIFT CONFIRMED: {signals}")

        self._last_state = confirmed

        return self._result(confirmed, signals)

    # ======================================================
    # RESULT FORMAT
    # ======================================================

    def _result(self, drift: bool, reason) -> Dict:
        return {
            "drift_detected": drift,
            "reason": reason,
            "confidence": min(1.0, self._drift_counter / self.confirmation_window),
        }
