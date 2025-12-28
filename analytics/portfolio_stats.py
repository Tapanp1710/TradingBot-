# File: analytics/portfolio_stats.py
# Purpose: Canonical portfolio analytics & performance statistics
# Design: Read-only analytics, no trading logic

from typing import Dict, List, Optional
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
import numpy as np
import logging

logger = logging.getLogger("PortfolioStats")


@dataclass
class TradeRecord:
    timestamp: datetime
    pnl: float
    win: bool


class PortfolioStats:
    """
    Tracks portfolio performance metrics over time.
    """

    def __init__(
        self,
        max_equity_points: int = 2000,
        max_trades: int = 1000,
        rolling_window: int = 50,
    ):
        # Time series
        self.equity_curve: deque = deque(maxlen=max_equity_points)
        self.return_series: deque = deque(maxlen=max_equity_points)

        # Trade history
        self.trades: deque = deque(maxlen=max_trades)

        # Rolling analytics
        self.rolling_window = rolling_window

        # Drawdown tracking
        self.peak_equity: Optional[float] = None
        self.max_drawdown_pct: float = 0.0

        logger.info("📊 PortfolioStats initialized")

    # ======================================================
    # RECORDING METHODS
    # ======================================================

    def record_equity(self, equity: float, timestamp: Optional[datetime] = None):
        """
        Record portfolio equity snapshot.
        """
        if equity <= 0:
            return

        ts = timestamp or datetime.now(timezone.utc)

        if self.equity_curve:
            prev_equity = self.equity_curve[-1][1]
            ret = (equity - prev_equity) / prev_equity if prev_equity > 0 else 0.0
            self.return_series.append(ret)

        self.equity_curve.append((ts, equity))
        self._update_drawdown(equity)

    def record_trade(self, pnl: float):
        """
        Record completed trade.
        """
        trade = TradeRecord(
            timestamp=datetime.now(timezone.utc),
            pnl=pnl,
            win=pnl > 0,
        )
        self.trades.append(trade)

    # ======================================================
    # DRAWNDOWN
    # ======================================================

    def _update_drawdown(self, equity: float):
        if self.peak_equity is None or equity > self.peak_equity:
            self.peak_equity = equity
            return

        drawdown = (self.peak_equity - equity) / self.peak_equity
        self.max_drawdown_pct = max(self.max_drawdown_pct, drawdown)

    def current_drawdown_pct(self) -> float:
        if not self.equity_curve or not self.peak_equity:
            return 0.0

        current_equity = self.equity_curve[-1][1]
        return (self.peak_equity - current_equity) / self.peak_equity

    # ======================================================
    # PERFORMANCE METRICS
    # ======================================================

    def win_rate(self, rolling: bool = False) -> Optional[float]:
        trades = self._get_trades(rolling)
        if not trades:
            return None

        wins = sum(1 for t in trades if t.win)
        return wins / len(trades)

    def profit_factor(self) -> Optional[float]:
        if not self.trades:
            return None

        gains = sum(t.pnl for t in self.trades if t.pnl > 0)
        losses = abs(sum(t.pnl for t in self.trades if t.pnl < 0))

        if losses == 0:
            return None

        return gains / losses

    def expectancy(self) -> Optional[float]:
        if not self.trades:
            return None

        return np.mean([t.pnl for t in self.trades])

    def loss_streak(self) -> int:
        streak = 0
        for trade in reversed(self.trades):
            if trade.win:
                break
            streak += 1
        return streak

    # ======================================================
    # RETURN METRICS
    # ======================================================

    def return_volatility(self) -> Optional[float]:
        if len(self.return_series) < 10:
            return None
        return float(np.std(self.return_series))

    def equity_slope(self) -> Optional[float]:
        """
        Linear trend of equity curve (health indicator).
        """
        if len(self.equity_curve) < 20:
            return None

        y = np.array([e for _, e in self.equity_curve])
        x = np.arange(len(y))

        slope = np.polyfit(x, y, 1)[0]
        return float(slope)

    # ======================================================
    # SNAPSHOT
    # ======================================================

    def snapshot(self) -> Dict:
        """
        Dashboard / monitoring safe snapshot.
        """
        return {
            "equity": self.equity_curve[-1][1] if self.equity_curve else None,
            "peak_equity": self.peak_equity,
            "current_drawdown_pct": self.current_drawdown_pct(),
            "max_drawdown_pct": self.max_drawdown_pct,
            "win_rate": self.win_rate(),
            "rolling_win_rate": self.win_rate(rolling=True),
            "expectancy": self.expectancy(),
            "profit_factor": self.profit_factor(),
            "loss_streak": self.loss_streak(),
            "return_volatility": self.return_volatility(),
            "equity_slope": self.equity_slope(),
            "trade_count": len(self.trades),
        }

    # ======================================================
    # INTERNAL HELPERS
    # ======================================================

    def _get_trades(self, rolling: bool) -> List[TradeRecord]:
        if not self.trades:
            return []

        if rolling and len(self.trades) > self.rolling_window:
            return list(self.trades)[-self.rolling_window :]

        return list(self.trades)
