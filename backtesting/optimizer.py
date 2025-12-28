# File: backtesting/optimizer.py
# Purpose: Parameter optimization using grid search

import copy
from backtesting.backtest_engine import BacktestEngine
from backtesting.metrics import PerformanceMetrics


class StrategyOptimizer:
    def __init__(self, base_config, historical_data):
        self.base_config = base_config
        self.data = historical_data

    def run(self, param_grid: dict, score_key="sharpe"):
        results = []

        for param, values in param_grid.items():
            for value in values:
                config = copy.deepcopy(self.base_config)
                setattr(config, param, value)

                engine = BacktestEngine(config, self.data)
                report = engine.run()

                metrics = PerformanceMetrics.compute(
                    engine.portfolio.snapshot().get("equity_curve", []),
                    engine.trade_log,
                )

                results.append({
                    "param": param,
                    "value": value,
                    "score": metrics.get(score_key, 0),
                    "metrics": metrics,
                })

        return sorted(results, key=lambda x: x["score"], reverse=True)
