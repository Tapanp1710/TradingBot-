# File: monitoring/regime_analytics.py
# Purpose: Regime-level analytics & observability
# Design: Passive event logger (no decision authority)

from datetime import datetime, timezone
from typing import Dict, List
import logging

logger = logging.getLogger("RegimeAnalytics")


class RegimeAnalytics:
    """
    Tracks regime events for audit & analysis.
    """

    def __init__(self):
        self.events: List[Dict] = []
        logger.info("📊 RegimeAnalytics initialized")

    # ==========================
    # EVENT RECORDERS
    # ==========================

    def record_drift(self, drift_state: Dict):
        if not drift_state.get("drift"):
            return

        event = {
            "timestamp": self._now(),
            "type": "DRIFT",
            "severity": drift_state.get("severity"),
            "recent_win_rate": drift_state.get("recent_win_rate"),
            "baseline_win_rate": drift_state.get("baseline_win_rate"),
            "loss_streak": drift_state.get("loss_streak"),
            "reasons": drift_state.get("reasons"),
        }

        self.events.append(event)
        logger.warning(f"📉 Drift logged | Severity={event['severity']}")

    def record_risk_throttle(
        self,
        multiplier: float,
        loss_streak: int,
        drawdown: float,
    ):
        event = {
            "timestamp": self._now(),
            "type": "RISK_THROTTLE",
            "risk_multiplier": multiplier,
            "loss_streak": loss_streak,
            "drawdown_pct": round(drawdown * 100, 2),
        }

        self.events.append(event)
        logger.info(
            f"🛑 Risk throttled | x{multiplier:.2f} | DD={drawdown:.1%}"
        )

    def record_ml_gate(self, ml_weight: float, accuracy: float | None):
        event = {
            "timestamp": self._now(),
            "type": "ML_GATE",
            "ml_weight": ml_weight,
            "ml_accuracy": accuracy,
        }

        self.events.append(event)

        if ml_weight == 0:
            logger.warning("🚫 ML gated OFF")
        else:
            logger.info(f"🧠 ML weight={ml_weight:.2f}")

    def record_trade(
        self,
        symbol: str,
        net_pnl: float,
        confidence: float,
        regime_snapshot: Dict,
    ):
        event = {
            "timestamp": self._now(),
            "type": "TRADE",
            "symbol": symbol,
            "net_pnl": net_pnl,
            "confidence": confidence,
            "regime": regime_snapshot,
        }

        self.events.append(event)

    # ==========================
    # EXPORT
    # ==========================

    def export(self) -> List[Dict]:
        return self.events

    def clear(self):
        self.events.clear()

    # ==========================
    # INTERNAL
    # ==========================

    @staticmethod
    def _now():
        return datetime.now(timezone.utc).isoformat()
