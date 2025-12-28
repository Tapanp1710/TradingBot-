# File: ml/ml_gate.py
# Purpose: Gate ML influence based on system health & drift
# Design: Policy-only ML permission controller

import time
import logging
from typing import Dict, Optional

logger = logging.getLogger("MLGate")


class MLGate:
    """
    Controls whether ML predictions are allowed to influence trading.
    """

    def __init__(
        self,
        cooldown_minutes: int = 60,
        min_confidence: float = 0.55,
        allow_partial: bool = True,
    ):
        """
        cooldown_minutes: minimum time ML stays disabled after drift
        min_confidence: minimum ML confidence to be considered
        allow_partial: allow reduced ML weighting instead of full disable
        """
        self.cooldown_seconds = cooldown_minutes * 60
        self.min_confidence = min_confidence
        self.allow_partial = allow_partial

        self.ml_enabled = True
        self.last_disabled_ts: Optional[float] = None
        self.disable_reason: Optional[str] = None

        logger.info("🧠 MLGate initialized")

    # ======================================================
    # MAIN EVALUATION
    # ======================================================

    def evaluate(
        self,
        *,
        risk_state: Dict,
        tactical_drift: Optional[Dict] = None,
        strategic_drift: Optional[Dict] = None,
    ) -> Dict:
        """
        Decide ML availability and weighting.
        """

        # ----------------------------
        # HARD BLOCKS
        # ----------------------------

        if risk_state.get("blocked"):
            return self._disable("Risk throttler blocked trading")

        if strategic_drift and strategic_drift.get("drift_detected"):
            return self._disable("Strategic drift detected")

        # ----------------------------
        # TACTICAL DEGRADATION
        # ----------------------------

        if tactical_drift and tactical_drift.get("drift"):
            severity = tactical_drift.get("severity", 0.5)

            if not self.allow_partial:
                return self._disable("Tactical drift")

            weight = max(0.0, 1.0 - severity)
            return self._partial(weight, "Tactical drift")

        # ----------------------------
        # COOLDOWN HANDLING
        # ----------------------------

        if not self.ml_enabled:
            if self._cooldown_elapsed():
                self._enable()
            else:
                return self._disabled_state()

        return {
            "ml_enabled": True,
            "ml_weight": 1.0,
            "reason": None,
        }

    # ======================================================
    # CONFIDENCE FILTER
    # ======================================================

    def filter_prediction(
        self,
        signal: str,
        confidence: float,
    ) -> Dict:
        """
        Validate ML prediction confidence.
        """
        if not self.ml_enabled:
            return {
                "use_ml": False,
                "signal": "HOLD",
                "confidence": 0.0,
                "reason": "ML disabled",
            }

        if confidence < self.min_confidence:
            return {
                "use_ml": False,
                "signal": "HOLD",
                "confidence": confidence,
                "reason": "Low ML confidence",
            }

        return {
            "use_ml": True,
            "signal": signal,
            "confidence": confidence,
            "reason": None,
        }

    # ======================================================
    # STATE MANAGEMENT
    # ======================================================

    def _disable(self, reason: str) -> Dict:
        if self.ml_enabled:
            logger.warning(f"🚫 ML DISABLED: {reason}")

        self.ml_enabled = False
        self.last_disabled_ts = time.time()
        self.disable_reason = reason

        return self._disabled_state()

    def _enable(self):
        logger.info("✅ ML RE-ENABLED after cooldown")
        self.ml_enabled = True
        self.disable_reason = None
        self.last_disabled_ts = None

    def _partial(self, weight: float, reason: str) -> Dict:
        logger.warning(f"⚠️ ML DEGRADED ({weight:.2f}x): {reason}")

        return {
            "ml_enabled": True,
            "ml_weight": round(weight, 3),
            "reason": reason,
        }

    def _disabled_state(self) -> Dict:
        return {
            "ml_enabled": False,
            "ml_weight": 0.0,
            "reason": self.disable_reason,
        }

    def _cooldown_elapsed(self) -> bool:
        if not self.last_disabled_ts:
            return True
        return (time.time() - self.last_disabled_ts) >= self.cooldown_seconds
