# File: monitoring/risk_throttler.py
# Purpose: Central risk gating using performance, drift, and regime signals
# Design: Policy-only layer (NO execution, NO sizing)

import logging
from typing import Dict, Optional

from config.risk import RiskConfig

logger = logging.getLogger("RiskThrottler")


class RiskThrottler:
    """
    Applies global risk throttling based on system health.
    """

    def __init__(
        self,
        config: RiskConfig,
        tactical_drift_detector=None,
        strategic_drift_detector=None,
    ):
        self.config = config

        self.tactical_drift = tactical_drift_detector
        self.strategic_drift = strategic_drift_detector

        self.trading_paused = False
        self.pause_reason: Optional[str] = None

        logger.info("🚦 RiskThrottler initialized (dual-drift enabled)")

    # ======================================================
    # MAIN ENTRY POINT
    # ======================================================

    def evaluate(
        self,
        *,
        win_rate: Optional[float],
        drawdown_pct: float,
        daily_loss_hit: bool,
        regime_multiplier: float = 1.0,
        consecutive_losses: int = 0,
    ) -> Dict:
        """
        Evaluate all risk signals and return a unified decision.
        """

        reasons = []
        risk_multiplier = 1.0

        # ============================
        # HARD STOPS (CAPITAL SAFETY)
        # ============================

        if daily_loss_hit:
            return self._block("Daily loss cap hit")

        if drawdown_pct >= self.config.MAX_DRAWDOWN_PCT:
            return self._block("Max drawdown exceeded")

        # ============================
        # STRATEGIC DRIFT (SLOW, FINAL)
        # ============================

        strategic_result = None
        if self.strategic_drift:
            strategic_result = self.strategic_drift.evaluate()
            if strategic_result.get("drift_detected"):
                return self._block(
                    f"Strategic drift: {strategic_result.get('reason')}"
                )

        # ============================
        # TACTICAL DRIFT (FAST, SOFT)
        # ============================

        tactical_result = None
        if self.tactical_drift:
            tactical_result = self.tactical_drift.detect_drift()
            if tactical_result.get("drift"):
                severity = tactical_result.get("severity", 0.0)
                throttle = max(
                    self.config.MIN_RISK_MULTIPLIER,
                    1.0 - severity,
                )
                risk_multiplier *= throttle
                reasons.append(
                    f"Tactical drift (severity={severity:.2f})"
                )

        # ============================
        # PERFORMANCE DEGRADATION
        # ============================

        if win_rate is not None and win_rate < self.config.MIN_ACCEPTABLE_WIN_RATE:
            risk_multiplier *= 0.7
            reasons.append("Low win rate")

        if consecutive_losses >= self.config.CONSECUTIVE_LOSS_LIMIT:
            risk_multiplier *= 0.5
            reasons.append("Loss streak")

        # ============================
        # REGIME ADJUSTMENT
        # ============================

        risk_multiplier *= regime_multiplier

        # ============================
        # FINAL CLAMP
        # ============================

        risk_multiplier = max(
            self.config.MIN_RISK_MULTIPLIER,
            min(risk_multiplier, self.config.MAX_RISK_MULTIPLIER),
        )

        return {
            "blocked": False,
            "risk_multiplier": round(risk_multiplier, 3),
            "reasons": reasons,
            "tactical_drift": tactical_result,
            "strategic_drift": strategic_result,
            "paused": False,
        }

    # ======================================================
    # CONTROL HELPERS
    # ======================================================

    def _block(self, reason: str) -> Dict:
        if not self.trading_paused:
            logger.error(f"⛔ TRADING BLOCKED: {reason}")

        self.trading_paused = True
        self.pause_reason = reason

        return {
            "blocked": True,
            "risk_multiplier": 0.0,
            "reasons": [reason],
            "paused": True,
            "pause_reason": reason,
        }

    def resume(self):
        if self.trading_paused:
            logger.info("▶️ Trading resumed")

        self.trading_paused = False
        self.pause_reason = None
