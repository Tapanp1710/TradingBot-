# File: core/execution_engine.py
# Purpose: Safe, atomic trade execution (BUY / SELL)
# Design: Dumb execution, audit-ready, idempotent, slippage-aware

from typing import Optional, Dict
from dataclasses import dataclass
from datetime import datetime, timezone
import logging
import uuid

from core.portfolio import Portfolio

logger = logging.getLogger("ExecutionEngine")


# =========================================================
# EXECUTION RESULT (STANDARDIZED)
# =========================================================

@dataclass
class ExecutionResult:
    execution_id: str
    symbol: str
    side: str
    requested_price: float
    executed_price: float
    size: float
    notional: float
    fee: float
    tax: float
    pnl: Optional[float]
    reason: str
    timestamp: datetime


# =========================================================
# EXECUTION ENGINE
# =========================================================

class ExecutionEngine:
    """
    Executes trades against the Portfolio.
    - No strategy
    - No ML
    - No indicators
    - Atomic & auditable
    """

    def __init__(
        self,
        portfolio: Portfolio,
        trading_fee_pct: float,
        apply_tax: bool = False,
        tax_pct: float = 0.0,
        enable_slippage: bool = True,
        slippage_pct: float = 0.0005,  # 0.05%
    ):
        self.portfolio = portfolio
        self.trading_fee_pct = trading_fee_pct
        self.apply_tax = apply_tax
        self.tax_pct = tax_pct

        self.enable_slippage = enable_slippage
        self.slippage_pct = slippage_pct

        self._execution_lock = set()  # idempotency guard

        logger.info("⚙️ ExecutionEngine initialized (slippage=%s)", enable_slippage)

    # =====================================================
    # INTERNAL HELPERS
    # =====================================================

    def _apply_slippage(self, price: float, side: str) -> float:
        if not self.enable_slippage:
            return price

        if side == "BUY":
            return price * (1 + self.slippage_pct)
        else:  # SELL
            return price * (1 - self.slippage_pct)

    def _execution_key(self, symbol: str, side: str) -> str:
        return f"{symbol}:{side}"

    # =====================================================
    # BUY
    # =====================================================

    def execute_buy(
        self,
        symbol: str,
        size: float,
        price: float,
        confidence: float,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        metadata: Optional[Dict] = None,
    ) -> Optional[ExecutionResult]:

        if size <= 0 or price <= 0:
            logger.error(f"❌ Invalid BUY params for {symbol}")
            return None

        key = self._execution_key(symbol, "BUY")
        if key in self._execution_lock:
            logger.warning(f"⚠️ Duplicate BUY blocked for {symbol}")
            return None

        self._execution_lock.add(key)

        try:
            executed_price = self._apply_slippage(price, "BUY")
            notional = size * executed_price
            fee = notional * self.trading_fee_pct

            success = self.portfolio.open_position(
                symbol=symbol,
                size=size,
                price=executed_price,
                fee=fee,
                confidence=confidence,
                stop_loss=stop_loss,
                take_profit=take_profit,
                metadata=metadata,
            )

            if not success:
                logger.warning(f"❌ BUY failed for {symbol}")
                return None

            result = ExecutionResult(
                execution_id=str(uuid.uuid4()),
                symbol=symbol,
                side="BUY",
                requested_price=price,
                executed_price=executed_price,
                size=size,
                notional=notional,
                fee=fee,
                tax=0.0,
                pnl=None,
                reason="OPEN",
                timestamp=datetime.now(timezone.utc),
            )

            logger.info(
                f"🟢 BUY {symbol} @ {executed_price:.4f} "
                f"(req {price:.4f}, slip {executed_price-price:+.4f})"
            )

            return result

        finally:
            self._execution_lock.discard(key)

    # =====================================================
    # SELL
    # =====================================================

    def execute_sell(
        self,
        symbol: str,
        price: float,
        reason: str = "EXIT",
    ) -> Optional[ExecutionResult]:

        if price <= 0:
            logger.error(f"❌ Invalid SELL price for {symbol}")
            return None

        key = self._execution_key(symbol, "SELL")
        if key in self._execution_lock:
            logger.warning(f"⚠️ Duplicate SELL blocked for {symbol}")
            return None

        position = self.portfolio.positions.get(symbol)
        if not position:
            logger.error(f"❌ No open position for {symbol}")
            return None

        self._execution_lock.add(key)

        try:
            executed_price = self._apply_slippage(price, "SELL")
            notional = position.size * executed_price
            fee = notional * self.trading_fee_pct

            gross_pnl = notional - position.entry_value
            tax = 0.0

            if self.apply_tax and gross_pnl > 0:
                tax = gross_pnl * self.tax_pct

            trade = self.portfolio.close_position(
                symbol=symbol,
                price=executed_price,
                fee=fee,
                tax=tax,
                reason=reason,
            )

            if trade is None:
                logger.error(f"❌ SELL failed for {symbol}")
                return None

            result = ExecutionResult(
                execution_id=str(uuid.uuid4()),
                symbol=symbol,
                side="SELL",
                requested_price=price,
                executed_price=executed_price,
                size=position.size,
                notional=notional,
                fee=fee,
                tax=tax,
                pnl=trade.get("net_pnl"),
                reason=reason,
                timestamp=datetime.now(timezone.utc),
            )

            logger.info(
                f"🔴 SELL {symbol} @ {executed_price:.4f} | "
                f"P&L={result.pnl:+.2f}"
            )

            return result

        finally:
            self._execution_lock.discard(key)
