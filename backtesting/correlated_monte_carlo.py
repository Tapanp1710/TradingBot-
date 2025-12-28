# File: backtesting/correlated_monte_carlo.py
# Purpose: Monte Carlo with loss-streak correlation (Markov-based)
# Models regime clustering and capital decay risk

import random
import numpy as np
from typing import List, Dict
import logging

logger = logging.getLogger("CorrelatedMonteCarlo")


class CorrelatedMonteCarloSimulator:
    """
    Monte Carlo simulation with correlated win/loss streaks.
    """

    def __init__(
        self,
        trade_returns: List[float],
        starting_capital: float,
        risk_per_trade_pct: float,
        simulations: int = 10_000,
        max_trades: int = 500,
        ruin_threshold_pct: float = 0.30,
    ):
        self.returns = trade_returns
        self.start_capital = starting_capital
        self.risk_pct = risk_per_trade_pct
        self.simulations = simulations
        self.max_trades = max_trades
        self.ruin_level = starting_capital * (1 - ruin_threshold_pct)

        self._build_transition_model()

        logger.info(
            "🔗 Correlated Monte Carlo initialized "
            f"(sims={simulations}, trades={max_trades})"
        )

    # ============================
    # MARKOV MODEL
    # ============================

    def _build_transition_model(self):
        """
        Build empirical win/loss transition probabilities.
        """
        outcomes = [1 if r > 0 else 0 for r in self.returns]

        ww = wl = lw = ll = 0

        for prev, curr in zip(outcomes[:-1], outcomes[1:]):
            if prev == 1 and curr == 1:
                ww += 1
            elif prev == 1 and curr == 0:
                wl += 1
            elif prev == 0 and curr == 1:
                lw += 1
            elif prev == 0 and curr == 0:
                ll += 1

        self.p_win_after_win = ww / max(1, ww + wl)
        self.p_loss_after_loss = ll / max(1, ll + lw)

        # Separate return distributions
        self.win_returns = [r for r in self.returns if r > 0]
        self.loss_returns = [r for r in self.returns if r <= 0]

        logger.info(
            f"Transition model | "
            f"P(W|W)={self.p_win_after_win:.2f} "
            f"P(L|L)={self.p_loss_after_loss:.2f}"
        )

    # ============================
    # SIMULATION
    # ============================

    def run(self) -> Dict:
        final_capitals = []
        drawdowns = []
        ruin_count = 0

        for _ in range(self.simulations):
            equity, max_dd, ruined = self._simulate_path()
            final_capitals.append(equity)
            drawdowns.append(max_dd)
            if ruined:
                ruin_count += 1

        return self._summarize(final_capitals, drawdowns, ruin_count)

    def _simulate_path(self):
        capital = self.start_capital
        peak = capital
        max_dd = 0
        ruined = False

        prev_win = random.choice([True, False])

        for _ in range(self.max_trades):
            if prev_win:
                win = random.random() < self.p_win_after_win
            else:
                win = not (random.random() < self.p_loss_after_loss)

            if win and self.win_returns:
                r = random.choice(self.win_returns)
            else:
                r = random.choice(self.loss_returns)

            pnl = capital * self.risk_pct * r
            capital += pnl

            if capital <= self.ruin_level:
                ruined = True
                break

            peak = max(peak, capital)
            dd = (peak - capital) / peak
            max_dd = max(max_dd, dd)

            prev_win = win

        return capital, max_dd, ruined

    # ============================
    # SUMMARY
    # ============================

    def _summarize(self, finals, drawdowns, ruin_count):
        finals = np.array(finals)
        drawdowns = np.array(drawdowns)

        return {
            "simulations": self.simulations,
            "median_final_capital": float(np.median(finals)),
            "p5_final_capital": float(np.percentile(finals, 5)),
            "p1_final_capital": float(np.percentile(finals, 1)),
            "max_drawdown_p95": float(np.percentile(drawdowns, 95)),
            "max_drawdown_p99": float(np.percentile(drawdowns, 99)),
            "ruin_probability_pct": (ruin_count / self.simulations) * 100,
        }
