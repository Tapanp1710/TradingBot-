# File: backtesting/replay_engine.py
# Purpose: Paper-trading replay on historical data

from backtesting.backtest_engine import BacktestEngine


class ReplayEngine(BacktestEngine):
    """
    Same as backtest, but slowed down and inspectable.
    """

    def run_stepwise(self, delay_sec=0.5):
        self._build_time_axis()

        for self.current_index in range(len(self.timestamps)):
            self._process_candle()
            yield {
                "timestamp": self.timestamps[self.current_index],
                "equity": self.portfolio.cash_balance,
                "positions": list(self.portfolio.positions.keys()),
            }

            if delay_sec:
                import time
                time.sleep(delay_sec)
