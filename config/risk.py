# File: config/risk.py
# Purpose: Centralized capital protection & risk constraints
# Design: Config-only (no trading logic)

from dataclasses import dataclass


@dataclass
class RiskConfig:
    # ==========================================================
    # CAPITAL & POSITION SIZING
    # ==========================================================

    STARTING_CAPITAL: float = 10000.0

    MAX_OPEN_POSITIONS: int = 5

    # Max % of available capital per position
    MAX_POSITION_PCT: float = 0.20  # 20%

    # Absolute minimum position size
    MIN_POSITION_USD: float = 50.0

    # Adaptive sizing
    ENABLE_ADAPTIVE_SIZING: bool = True
    HIGH_CONFIDENCE_THRESHOLD: float = 0.75
    LOW_CONFIDENCE_THRESHOLD: float = 0.45
    HIGH_CONFIDENCE_MULTIPLIER: float = 1.25
    LOW_CONFIDENCE_MULTIPLIER: float = 0.6

    # ==========================================================
    # STOP LOSS / TAKE PROFIT (ATR + HARD LIMITS)
    # ==========================================================

    USE_ATR_EXITS: bool = True

    ATR_SL_MULT: float = 1.5
    ATR_TP_MULT: float = 3.0

    # Hard safety caps (percent of entry)
    MAX_SL_PCT: float = 0.03      # 3%
    MAX_TP_PCT: float = 0.08      # 8%

    # Fallback if ATR disabled/unavailable
    FALLBACK_STOP_LOSS_PCT: float = 0.02
    FALLBACK_TAKE_PROFIT_PCT: float = 0.05

    # ==========================================================
    # TRAILING STOPS
    # ==========================================================

    ENABLE_ATR_TRAILING: bool = True
    TRAIL_ACTIVATE_ATR_MULT: float = 1.0
    TRAIL_DISTANCE_ATR_MULT: float = 1.2

    # Partial take profit (optional)
    ENABLE_PARTIAL_TP: bool = False
    PARTIAL_TP_TRIGGER_ATR_MULT: float = 1.5

    # ==========================================================
    # DAILY LOSS & DRAWDOWN PROTECTION
    # ==========================================================

    ENABLE_DAILY_LOSS_CAP: bool = True

    # % of starting capital (0.04 = 4%)
    MAX_DAILY_LOSS_PCT: float = 0.04

    # Absolute amount
    MAX_DAILY_LOSS_AMOUNT: float = 400.0

    # Hard portfolio drawdown protection
    ENABLE_MAX_DRAWDOWN: bool = True
    MAX_DRAWDOWN_PCT: float = 0.25  # 25%

    # ==========================================================
    # REVENGE TRADING PROTECTION
    # ==========================================================

    PREVENT_REVENGE_TRADING: bool = True
    REVENGE_TRADE_COOLDOWN_MINS: int = 30
    CONSECUTIVE_LOSS_LIMIT: int = 2

    # ==========================================================
    # STALE POSITION HANDLING
    # ==========================================================

    # Max hours to hold a position
    MAX_POSITION_HOURS: int = 24

    # ATR-based stagnation band
    STALE_BAND_ATR_MULT: float = 0.6

    # ==========================================================
    # RISK THROTTLING (GLOBAL SAFETY)
    # ==========================================================

    ENABLE_RISK_THROTTLE: bool = True

    # Reduce exposure if win-rate drops
    MIN_ACCEPTABLE_WIN_RATE: float = 0.40

    # Risk multiplier bounds
    MIN_RISK_MULTIPLIER: float = 0.4
    MAX_RISK_MULTIPLIER: float = 1.2

    # ==========================================================
    # HELPER METHODS (SAFE, PURE)
    # ==========================================================

    def clamp_position_pct(self, pct: float) -> float:
        """
        Ensures position sizing never exceeds allowed bounds.
        """
        return max(0.0, min(pct, self.MAX_POSITION_PCT))

    def daily_loss_limit_pct(self) -> float:
        """
        Daily loss cap as percentage (for dashboards).
        """
        return self.MAX_DAILY_LOSS_PCT * 100

    def is_loss_cap_hit(self, loss_pct: float, loss_amount: float) -> bool:
        """
        Unified daily loss check.
        """
        return (
            loss_pct >= (self.MAX_DAILY_LOSS_PCT * 100)
            or loss_amount >= self.MAX_DAILY_LOSS_AMOUNT
        )
