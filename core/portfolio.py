# File: core/portfolio.py
# Purpose: Single source of truth for capital, equity, and P&L
# Design: Deterministic, auditable, execution-safe

from dataclasses import dataclass, field
from typing import Dict, Optional
from datetime import datetime, timezone
import logging
import uuid

logger = logging.getLogger("Portfolio")


# ======================================================
# POSITION
# ======================================================

@dataclass
class Position:
    symbol: str
    size: float
    entry_price: float
    entry_value: float
    entry_time: datetime

    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None

    highest_price: float = 0.0
    trailing_active: bool = False

    fees_paid: float = 0.0
    confidence: float = 0.0
    metadata: Dict = field(default_factory=dict)


# ======================================================
# PORTFOLIO
# ======================================================

class Portfolio:
    """
    Authoritative portfolio state.
    ALL capital, P&L, and risk accounting lives here.
    """

    def __init__(self, starting_cash: float):
        self.starting_cash = starting_cash
        self.cash_balance = starting_cash

        self.positions: Dict[str, Position] = {}

        self.realized_pnl = 0.0
        self.total_fees = 0.0
        self.total_tax = 0.0

        self.trade_count = 0
        self.win_count = 0
        self.loss_count = 0

        self.created_at = datetime.now(timezone.utc)
        self._tx_lock = set()  # idempotency guard

        logger.info(f"💼 Portfolio initialized with ${starting_cash:,.2f}")

    # ==================================================
    # READ-ONLY METRICS
    # ==================================================

    def equity(self, prices: Dict[str, float]) -> float:
        total = self.cash_balance
        for symbol, pos in self.positions.items():
            price = prices.get(symbol)
            total += pos.size * price if price and price > 0 else pos.entry_value
        return total

    def unrealized_pnl(self, prices: Dict[str, float]) -> float:
        pnl = 0.0
        for symbol, pos in self.positions.items():
            price = prices.get(symbol)
            if price and price > 0:
                pnl += (price * pos.size) - pos.entry_value
        return pnl

    def position_count(self) -> int:
        return len(self.positions)

    # ==================================================
    # POSITION LIFECYCLE
    # ==================================================

    def open_position(
        self,
        symbol: str,
        size: float,
        price: float,
        fee: float,
        confidence: float,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        metadata: Optional[Dict] = None,
    ) -> bool:
        tx_id = f"OPEN:{symbol}"
        if tx_id in self._tx_lock:
            logger.warning(f"⚠️ Duplicate OPEN blocked for {symbol}")
            return False

        if symbol in self.positions:
            logger.error(f"❌ Position already exists for {symbol}")
            return False

        cost = (size * price) + fee
        if cost > self.cash_balance:
            logger.error(f"❌ Insufficient cash for {symbol}")
            return False

        self._tx_lock.add(tx_id)
        try:
            self.cash_balance -= cost
            self.total_fees += fee

            self.positions[symbol] = Position(
                symbol=symbol,
                size=size,
                entry_price=price,
                entry_value=size * price,
                entry_time=datetime.now(timezone.utc),
                stop_loss=stop_loss,
                take_profit=take_profit,
                highest_price=price,
                fees_paid=fee,
                confidence=confidence,
                metadata=metadata or {},
            )

            self._assert_invariants()

            logger.info(
                f"🟢 OPEN {symbol} | Size={size:.6f} | Price=${price:.2f}"
            )
            return True

        finally:
            self._tx_lock.discard(tx_id)

    def close_position(
        self,
        symbol: str,
        price: float,
        fee: float,
        tax: float = 0.0,
        reason: str = "EXIT",
    ) -> Optional[Dict]:

        tx_id = f"CLOSE:{symbol}"
        if tx_id in self._tx_lock:
            logger.warning(f"⚠️ Duplicate CLOSE blocked for {symbol}")
            return None

        pos = self.positions.get(symbol)
        if not pos:
            logger.error(f"❌ No position to close: {symbol}")
            return None

        self._tx_lock.add(tx_id)
        try:
            exit_value = pos.size * price
            gross_pnl = exit_value - pos.entry_value
            net_pnl = gross_pnl - fee - tax

            self.cash_balance += (exit_value - fee - tax)
            self.realized_pnl += net_pnl
            self.total_fees += fee
            self.total_tax += tax

            self.trade_count += 1
            self.win_count += int(net_pnl > 0)
            self.loss_count += int(net_pnl <= 0)

            trade = {
                "trade_id": str(uuid.uuid4()),
                "timestamp": datetime.now(timezone.utc),
                "symbol": symbol,
                "entry_price": pos.entry_price,
                "exit_price": price,
                "size": pos.size,
                "gross_pnl": gross_pnl,
                "net_pnl": net_pnl,
                "fees": pos.fees_paid + fee,
                "tax": tax,
                "confidence": pos.confidence,
                "hold_hours": (
                    datetime.now(timezone.utc) - pos.entry_time
                ).total_seconds()
                / 3600,
                "reason": reason,
            }

            del self.positions[symbol]
            self._assert_invariants()

            logger.info(
                f"🔴 CLOSE {symbol} | Exit=${price:.2f} | Net P&L=${net_pnl:+.2f}"
            )
            return trade

        finally:
            self._tx_lock.discard(tx_id)

    # ==================================================
    # SAFETY & AUDIT
    # ==================================================

    def _assert_invariants(self):
        assert self.cash_balance >= 0, "Cash balance negative!"
        for pos in self.positions.values():
            assert pos.size > 0, "Invalid position size!"

    def snapshot(self) -> Dict:
        return {
            "cash_balance": self.cash_balance,
            "open_positions": list(self.positions.keys()),
            "realized_pnl": self.realized_pnl,
            "fees": self.total_fees,
            "tax": self.total_tax,
            "trades": self.trade_count,
            "wins": self.win_count,
            "losses": self.loss_count,
        }
