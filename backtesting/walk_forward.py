# File: backtesting/walk_forward.py
# Purpose: Walk-forward validation (train → test → roll)
# Design: Production-grade, no data leakage

from copy import deepcopy
from backtesting.backtest_engine import BacktestEngine
from backtesting.metrics import PerformanceMetrics


class WalkForwardTester:
    """
    Walk-forward testing engine.
    """

    def __init__(
        self,
        base_config,
        historical_data,
        train_size: int,
        test_size: int,
        step_size: int = None,
    ):
        """
        historical_data: list of candles or dict[symbol -> candles]
        train_size: number of candles for training window
        test_size: number of candles for test window
        step_size: how much the window slides (defaults to test_size)
        """
        self.base_config = base_config
        self.data = historical_data
        self.train_size = train_size
        self.test_size = test_size
        self.step_size = step_size or test_size

    def run(self):
        results = []

        total_length = len(self.data)
        start = 0
        window_id = 1

        while start + self.train_size + self.test_size <= total_length:
            train_slice = self.data[start : start + self.train_size]
            test_slice = self.data[
                start + self.train_size :
                start + self.train_size + self.test_size
            ]

            config = deepcopy(self.base_config)

            # --- TRAIN PHASE ---
            train_engine = BacktestEngine(config, train_slice)
            train_engine.run()

            # --- TEST PHASE ---
            test_engine = BacktestEngine(config, test_slice)
            test_engine.run()

            metrics = PerformanceMetrics.compute(
                equity_curve=test_engine.equity_curve,
                trades=test_engine.trade_log,
            )

            results.append({
                "window": window_id,
                "train_start": start,
                "train_end": start + self.train_size,
                "test_start": start + self.train_size,
                "test_end": start + self.train_size + self.test_size,
                "metrics": metrics,
            })

            start += self.step_size
            window_id += 1

        return results
