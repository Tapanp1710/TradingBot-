# File: backtesting/equity_curve.py
# Purpose: Track equity and drawdowns

class EquityCurve:
    def __init__(self):
        self.values = []
        self.timestamps = []

    def record(self, timestamp, equity):
        self.timestamps.append(timestamp)
        self.values.append(equity)

    def latest(self):
        return self.values[-1] if self.values else 0.0
