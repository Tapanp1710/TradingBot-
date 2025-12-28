# File: backtesting/monte_carlo.py
# Purpose: Capital survival & drawdown risk simulation
# Design: Distribution-preserving Monte Carlo (no Gaussian lies)

import random
import numpy as np
from typing import List, Dict
import logging

logger = logging.getLogger("MonteCarlo")


class MonteCarloRiskSimulator:
    """
    Monte Carlo simulation using empirical trade returns.
    """

    def __init__(
        self,
        trade_returns: List[float],
        starting_capital: float,
        risk_per_trade_pct: float,
        max_trades: int = 500,
        simulations: int = 10_000,
        ruin_threshold_pct: float = 0.30,
    ):
        """
        trade_returns: list of % returns per trade (e.g. +0.04, -0.02)
        risk_per_trade_pct: capital risked per trade (e.g. 0.01 = 1%)
        ruin_threshold_pct: capital loss considered ruin (e.g. 0.30 = -30%)
        """

        if not trade_returns:
            raise ValueError("Trade return history required")

        self.trade_returns = trade_returns
        self.starting_capital = starting_capital
        self.risk_pct = risk_per_trade_pct
        self.max_trades = max_trades
        self.simulations = simulations
        self.ruin_threshold = starting_capital * (1 - ruin_threshold_pct)

        logger.info(
            f"🎲 Monte Carlo initialized | Sims={simulations} | Trades={max_trades}"
        )

    # ============================
    # CORE SIMULATION
    # ============================

    def run(self) -> Dict:
        """
        Run Monte Carlo simulations.
        """
        final_capitals = []
        max_drawdowns = []
        ruin_count = 0

        for _ in range(self.simulations):
            equity, max_dd, ruined = self._simulate_once()
            final_capitals.append(equity)
            max_drawdowns.append(max_dd)
            if ruined:
                ruin_count += 1

        return self._summarize(final_capitals, max_drawdowns, ruin_count)

    # ============================
    # SINGLE PATH
    # ============================

    def _simulate_once(self):
        capital = self.starting_capital
        peak = capital
        max_drawdown = 0
        ruined = False

        for _ in range(self.max_trades):
            trade_return = random.choice(self.trade_returns)

            risk_amount = capital * self.risk_pct
            pnl = risk_amount * trade_return
            capital += pnl

            if capital <= self.ruin_threshold:
                ruined = True
                break

            peak = max(peak, capital)
            drawdown = (peak - capital) / peak
            max_drawdown = max(max_drawdown, drawdown)

        return capital, max_drawdown, ruined

    # ============================
    # RESULTS
    # ============================

    def _summarize(self, finals, drawdowns, ruin_count) -> Dict:
        finals = np.array(finals)
        drawdowns = np.array(drawdowns)

        return {
            "simulations": self.simulations,
            "starting_capital": self.starting_capital,
            "median_final_capital": float(np.median(finals)),
            "mean_final_capital": float(np.mean(finals)),
            "p5_final_capital": float(np.percentile(finals, 5)),
            "p1_final_capital": float(np.percentile(finals, 1)),
            "max_drawdown_p95": float(np.percentile(drawdowns, 95)),
            "max_drawdown_p99": float(np.percentile(drawdowns, 99)),
            "ruin_probability_pct": (ruin_count / self.simulations) * 100,
        }
