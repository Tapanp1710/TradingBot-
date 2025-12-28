# File: backtesting/backtest_engine.py
# Purpose: Event-driven historical backtesting engine
# Design: Uses SAME logic as live trading

import logging
from datetime import datetime, timezone
from typing import Dict, List

import pandas as pd

from core.portfolio import Portfolio
from core.execution_engine import ExecutionEngine
from core.position_manager import PositionManager
from core.strategy import TradingStrategy
from utils.risk_manager import RiskManager

logger = logging.getLogger("BacktestEngine")


class BacktestEngine:
    """
    Event-driven backtesting engine.
    Simulates candle-by-candle execution.
    """

    def __init__(
        self,
        config,
        historical_data: Dict[str, pd.DataFrame],
    ):
        """
        historical_data:
        {
            "BTC/USDT": DataFrame,
            "ETH/USDT": DataFrame,
            ...
        }
        DataFrame must contain OHLCV + indicators
        """

        self.config = config
        self.historical_data = historical_data
        self.symbols = list(historical_data.keys())

        # === Core components ===
        self.portfolio = Portfolio(config.STARTING_CAPITAL)

        self.execution_engine = ExecutionEngine(
            portfolio=self.portfolio,
            trading_fee_pct=config.TRADING_FEE,
            apply_tax=False,  # Taxes disabled for backtest
        )

        self.strategy = TradingStrategy(config, exchange_manager=None)
        self.risk_manager = RiskManager(config)

        self.position_manager = PositionManager(
            portfolio=self.portfolio,
            execution_engine=self.execution_engine,
            price_fetcher=self._get_price,
            config=config,
        )

        # Backtest state
        self.current_index = 0
        self.timestamps: List[datetime] = []
        self.trade_log: List[Dict] = []

        logger.info("📊 BacktestEngine initialized")

    # =====================================================
    # PRICE FEED (HISTORICAL)
    # =====================================================

    def _get_price(self, symbol: str) -> float:
        df = self.historical_data[symbol]
        return float(df.iloc[self.current_index]["close"])

    # =====================================================
    # MAIN BACKTEST LOOP
    # =====================================================

    def run(self) -> Dict:
        logger.info("▶️ Starting backtest")

        # Align time indices
        self._build_time_axis()

        for self.current_index in range(len(self.timestamps)):
            self._process_candle()

        return self._final_report()

    # =====================================================
    # CANDLE PROCESSING
    # =====================================================

    def _process_candle(self):
        timestamp = self.timestamps[self.current_index]

        # 1. Manage open positions (SL / TP / trailing)
        self.position_manager.monitor_positions()

        # 2. Scan for new entries
        if self.portfolio.position_count() >= self.config.MAX_OPEN_POSITIONS:
            return

        for symbol, df in self.historical_data.items():
            if symbol in self.portfolio.positions:
                continue

            if self.current_index < 50:
                continue  # Warmup

            window = df.iloc[: self.current_index + 1]
            signal = self.strategy.generate_signal(window, symbol)

            if signal["signal"] != "BUY":
                continue

            confidence = signal["confidence"]
            if confidence < self.config.SIGNAL_CONFIDENCE_THRESHOLD:
                continue

            price = self._get_price(symbol)
            atr = signal["indicators"].get("atr", 0)

            allocation = self.risk_manager.calculate_position_size(
                available_capital=self.portfolio.cash_balance,
                total_capital=self.portfolio.cash_balance,
                confidence=confidence,
            )

            if allocation <= 0:
                continue

            size = allocation / price

            stop_loss, take_profit = self._calculate_exits(
                price, atr
            )

            result = self.execution_engine.execute_buy(
                symbol=symbol,
                size=size,
                price=price,
                confidence=confidence,
                stop_loss=stop_loss,
                take_profit=take_profit,
                metadata={"atr": atr},
            )

            if result:
                self.trade_log.append(
                    {
                        "timestamp": timestamp,
                        "symbol": symbol,
                        "side": "BUY",
                        "price": price,
                        "confidence": confidence,
                    }
                )

    # =====================================================
    # EXIT CALCULATION
    # =====================================================

    def _calculate_exits(self, price: float, atr: float):
        if self.config.USE_ATR_EXITS and atr > 0:
            sl = price - atr * self.config.ATR_SL_MULT
            tp = price + atr * self.config.ATR_TP_MULT
            return sl, tp

        return (
            price * (1 - self.config.FALLBACK_STOP_LOSS_PCT),
            price * (1 + self.config.FALLBACK_TAKE_PROFIT_PCT),
        )

    # =====================================================
    # TIME ALIGNMENT
    # =====================================================

    def _build_time_axis(self):
        # Use first symbol as master timeline
        first_df = next(iter(self.historical_data.values()))
        self.timestamps = list(first_df.index)

    # =====================================================
    # REPORT
    # =====================================================

    def _final_report(self) -> Dict:
        equity = self.portfolio.cash_balance
        wins = self.portfolio.win_count
        losses = self.portfolio.loss_count
        trades = self.portfolio.trade_count

        return {
            "starting_capital": self.config.STARTING_CAPITAL,
            "ending_capital": equity,
            "total_pnl": equity - self.config.STARTING_CAPITAL,
            "return_pct": (
                (equity - self.config.STARTING_CAPITAL)
                / self.config.STARTING_CAPITAL
            )
            * 100,
            "total_trades": trades,
            "wins": wins,
            "losses": losses,
            "win_rate": (wins / trades * 100) if trades else 0,
            "open_positions": self.portfolio.position_count(),
        }