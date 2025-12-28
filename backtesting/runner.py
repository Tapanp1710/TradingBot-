# File: backtesting/runner.py
# Purpose: Unified entrypoint

from backtesting.backtest_engine import BacktestEngine
from backtesting.metrics import PerformanceMetrics


def run_backtest(config, historical_data):
    engine = BacktestEngine(config, historical_data)
    report = engine.run()

    metrics = PerformanceMetrics.compute(
        equity_curve=[],  # plug curve here if tracked
        trades=engine.trade_log,
    )

    return report, metrics
