# File: utils/risk_manager.py
# Purpose: Capital risk control & position sizing
# Design: Deterministic, conservative, confidence-aware

import logging
from typing import Optional

logger = logging.getLogger("RiskManager")


class RiskManager:
    """
    Decides HOW MUCH capital can be risked.
    Does NOT place trades.
    Does NOT track positions.
    """

    def __init__(self, config):
        self.config = config

        # Hard safety limits
        self.max_position_pct = config.MAX_POSITION_PCT          # e.g. 0.08
        self.max_portfolio_risk_pct = getattr(
            config, "MAX_PORTFOLIO_RISK_PCT", 0.08
        )

        self.min_position_usd = config.MIN_POSITION_USD

        # Adaptive sizing
        self.enable_confidence_scaling = getattr(
            config, "ENABLE_ADAPTIVE_SIZING", True
        )

        self.high_conf_threshold = getattr(
            config, "HIGH_CONFIDENCE_THRESHOLD", 0.75
        )
        self.low_conf_threshold = getattr(
            config, "LOW_CONFIDENCE_THRESHOLD", 0.55
        )

        self.high_conf_multiplier = getattr(
            config, "HIGH_CONFIDENCE_MULTIPLIER", 1.2
        )
        self.low_conf_multiplier = getattr(
            config, "LOW_CONFIDENCE_MULTIPLIER", 0.7
        )

        logger.info("🛡️ RiskManager initialized")

    # =====================================================
    # POSITION SIZING
    # =====================================================

    def calculate_position_size(
        self,
        available_capital: float,
        total_capital: float,
        confidence: float,
    ) -> float:
        """
        Returns position VALUE (USD), not quantity.
        """

        if available_capital <= 0 or total_capital <= 0:
            return 0.0

        # Base allocation
        base_allocation = total_capital * self.max_position_pct

        # === CONFIDENCE SCALING ===
        allocation = base_allocation

        if self.enable_confidence_scaling:
            if confidence >= self.high_conf_threshold:
                allocation *= self.high_conf_multiplier
            elif confidence <= self.low_conf_threshold:
                allocation *= self.low_conf_multiplier

        # === AVAILABLE CAPITAL SAFETY ===
        allocation = min(allocation, available_capital)

        # === HARD FLOOR ===
        if allocation < self.min_position_usd:
            logger.debug(
                f"❌ Allocation ${allocation:.2f} < min ${self.min_position_usd}"
            )
            return 0.0

        return round(allocation, 2)

    # =====================================================
    # PORTFOLIO RISK CHECK
    # =====================================================

    def can_open_position(
        self,
        current_exposure: float,
        total_capital: float,
    ) -> bool:
        """
        Ensures portfolio-level risk cap is not exceeded.
        """

        if total_capital <= 0:
            return False

        exposure_pct = current_exposure / total_capital

        if exposure_pct >= self.max_portfolio_risk_pct:
            logger.warning(
                f"🚫 Portfolio risk cap hit "
                f"({exposure_pct:.1%} >= {self.max_portfolio_risk_pct:.1%})"
            )
            return False

        return True

    # =====================================================
    # DRAWDOWN ADAPTATION (OPTIONAL)
    # =====================================================

    def drawdown_adjustment(
        self,
        starting_capital: float,
        current_capital: float,
    ) -> float:
        """
        Returns a multiplier (0.0–1.0) based on drawdown.
        """

        if starting_capital <= 0:
            return 1.0

        drawdown = (starting_capital - current_capital) / starting_capital

        if drawdown <= 0:
            return 1.0

        # Linear drawdown response
        if drawdown < 0.05:
            return 1.0
        elif drawdown < 0.10:
            return 0.85
        elif drawdown < 0.20:
            return 0.65
        else:
            logger.error("🚨 Severe drawdown detected — risk reduced heavily")
            return 0.4
