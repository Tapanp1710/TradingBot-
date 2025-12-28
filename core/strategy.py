# File: core/strategy.py
# Refactored: Pure signal generation (TA + ML only)

from typing import Tuple, Dict, List
import logging
import numpy as np
import pandas as pd

from config import Config
from utils import TechnicalIndicators

logger = logging.getLogger("TradingBot")


class TradingStrategy:
    """
    Pure trading decision engine.
    Responsibilities:
    - Technical analysis
    - ML inference
    - Multi-timeframe confirmation
    - Signal combination
    """

    def __init__(self, config: Config, exchange_manager=None):
        self.config = config
        self.exchange = exchange_manager

        self.timeframes = getattr(config, "TIMEFRAMES", ["1h", "4h", "1d"])
        self.timeframe_weights = getattr(config, "TIMEFRAME_WEIGHTS", [0.5, 0.3, 0.2])

        self.ml_enabled = False
        self.ml_model = None
        self.scaler = None
        self.online_learner = None

        self._load_ml()

    # ======================================================
    # PUBLIC API
    # ======================================================

    def generate_signal(self, df: pd.DataFrame, symbol: str) -> Dict:
        """
        Main entry point.
        Returns a PURE decision object.
        """
        if df is None or df.empty or len(df) < 50:
            return self._empty_signal()

        try:
            df = TechnicalIndicators.add_all_indicators(df)

            tech_signal, tech_conf = self._technical_analysis(df)

            mtf_signal, mtf_conf = self._multi_timeframe(symbol, tech_signal, tech_conf)
            ob_signal, ob_score = self._orderbook(symbol)
            vwap_signal, vwap_conf = self._vwap(df, symbol)
            vol_signal, vol_strength = self._volume_profile(df)

            ml_signal, ml_conf, features = self._ml(df)

            final_signal, final_conf = self._combine(
                tech_signal, tech_conf,
                mtf_signal, mtf_conf,
                ob_signal, ob_score,
                vwap_signal, vwap_conf,
                vol_signal, vol_strength,
                ml_signal, ml_conf
            )

            indicators = self._extract_indicators(df.iloc[-1])

            return {
                "signal": final_signal,
                "confidence": final_conf,
                "features": features,
                "indicators": indicators,
                "tech_confidence": tech_conf,
                "ml_confidence": ml_conf,
                "mtf_confidence": mtf_conf,
                "orderbook_score": ob_score,
                "vwap_confidence": vwap_conf,
                "volume_strength": vol_strength,
            }

        except Exception as e:
            logger.error(f"Signal generation failed for {symbol}: {e}")
            return self._empty_signal()

    # ======================================================
    # TECHNICAL ANALYSIS
    # ======================================================

    def _technical_analysis(self, df: pd.DataFrame) -> Tuple[str, float]:
        latest, prev = df.iloc[-1], df.iloc[-2]

        buy, sell = 0.0, 0.0

        sma20, sma50 = latest.get("sma_20"), latest.get("sma_50")
        if sma20 and sma50:
            buy += 1.5 if sma20 > sma50 else 0
            sell += 0.8 if sma20 < sma50 else 0

        macd, macd_sig = latest.get("macd"), latest.get("macd_signal")
        if macd and macd_sig:
            buy += 1.5 if macd > macd_sig else 0
            sell += 0.8 if macd < macd_sig else 0

        rsi = latest.get("rsi", 50)
        if rsi < 45:
            buy += 1.5
        elif rsi > 60:
            sell += 1.0

        bb_pos = self._bb_position(latest)
        if bb_pos < 0.3:
            buy += 1.2
        elif bb_pos > 0.7:
            sell += 1.0

        price_change = ((latest["close"] - prev["close"]) / prev["close"]) * 100
        buy += 0.8 if price_change > 0.5 else 0
        sell += 0.8 if price_change < -0.5 else 0

        total = buy + sell
        if total == 0:
            return "HOLD", 0.4

        if buy > sell:
            return "BUY", min(buy / total, 0.95)
        if sell > buy:
            return "SELL", min(sell / total, 0.95)

        return "HOLD", 0.4

    # ======================================================
    # MULTI-TIMEFRAME
    # ======================================================

    def _multi_timeframe(self, symbol, base_signal, base_conf):
        if not self.exchange or not self.config.ENABLE_MULTI_TIMEFRAME:
            return base_signal, base_conf

        weighted_conf = 0.0
        score = 0.0

        for tf, w in zip(self.timeframes, self.timeframe_weights):
            try:
                df = self.exchange.fetch_ohlcv(symbol, tf, 100)
                df = TechnicalIndicators.add_all_indicators(df)
                sig, conf = self._technical_analysis(df)

                score += (1 if sig == "BUY" else -1 if sig == "SELL" else 0) * w
                weighted_conf += conf * w
            except Exception:
                continue

        if score > 0.4:
            return "BUY", min(weighted_conf, 0.95)
        if score < -0.4:
            return "SELL", min(weighted_conf, 0.95)

        return "HOLD", weighted_conf or base_conf

    # ======================================================
    # ORDERBOOK / VWAP / VOLUME
    # ======================================================

    def _orderbook(self, symbol):
        if not self.exchange:
            return "HOLD", 0.0
        try:
            d = self.exchange.analyze_order_book_depth(symbol)
            return d.get("signal", "HOLD"), abs(d.get("imbalance", 0))
        except Exception:
            return "HOLD", 0.0

    def _vwap(self, df, symbol):
        try:
            tp = (df["high"] + df["low"] + df["close"]) / 3
            vwap = (tp * df["volume"]).sum() / df["volume"].sum()
            price = df.iloc[-1]["close"]
            dist = (price - vwap) / vwap * 100

            if dist < -2:
                return "BUY", min(abs(dist) / 5, 0.9)
            if dist > 2:
                return "SELL", min(abs(dist) / 5, 0.9)
            return "HOLD", 0.5
        except Exception:
            return "HOLD", 0.5

    def _volume_profile(self, df):
        try:
            avg = df["volume"].rolling(20).mean().iloc[-1]
            cur = df.iloc[-1]["volume"]
            ratio = cur / avg if avg else 1

            if ratio > 1.5:
                return "BUY", min(ratio / 3, 1.0)
            if ratio < 0.7:
                return "WEAK", 0.3
            return "HOLD", 0.5
        except Exception:
            return "HOLD", 0.5

    # ======================================================
    # ML
    # ======================================================

    def _load_ml(self):
        try:
            import joblib, os
            if os.path.exists("ml/models/random_forest_model.pkl"):
                self.ml_model = joblib.load("ml/models/random_forest_model.pkl")
                self.scaler = joblib.load("ml/models/scaler.pkl")
                self.ml_enabled = True
                logger.info("ML models loaded")
        except Exception as e:
            logger.warning(f"ML disabled: {e}")

    def _ml(self, df):
        if not self.ml_enabled:
            return "HOLD", 0.5, []

        features = self._features(df)
        X = self.scaler.transform([features])
        proba = self.ml_model.predict_proba(X)[0][1]

        if proba > 0.55:
            return "BUY", proba, features
        if proba < 0.45:
            return "SELL", 1 - proba, features

        return "HOLD", 0.5, features

    # ======================================================
    # SIGNAL COMBINATION
    # ======================================================

    def _combine(
        self,
        tech_s, tech_c,
        mtf_s, mtf_c,
        ob_s, ob_c,
        vwap_s, vwap_c,
        vol_s, vol_c,
        ml_s, ml_c
    ):
        weights = {
            "tech": 0.5,
            "ml": 0.3 if self.ml_enabled else 0,
            "mtf": 0.1,
            "ob": 0.05,
            "vwap": 0.05,
        }

        def score(sig, conf):
            return (1 if sig == "BUY" else -1 if sig == "SELL" else 0) * conf

        total = (
            score(tech_s, tech_c) * weights["tech"]
            + score(ml_s, ml_c) * weights["ml"]
            + score(mtf_s, mtf_c) * weights["mtf"]
            + score(ob_s, ob_c) * weights["ob"]
            + score(vwap_s, vwap_c) * weights["vwap"]
        )

        conf = abs(total)
        threshold = self.config.SIGNAL_CONFIDENCE_THRESHOLD

        if total > threshold - 0.15:
            return "BUY", min(conf, 0.95)
        if total < -(threshold - 0.1):
            return "SELL", min(conf, 0.95)

        return "HOLD", conf

    # ======================================================
    # HELPERS
    # ======================================================

    def _bb_position(self, row):
        hi, lo, c = row.get("bb_upper"), row.get("bb_lower"), row.get("close")
        if not hi or not lo or hi <= lo:
            return 0.5
        return max(0, min(1, (c - lo) / (hi - lo)))

    def _features(self, df):
        return [float(x) if np.isfinite(x) else 0.0 for x in df.iloc[-1].fillna(0).values][:67]

    def _extract_indicators(self, row):
        return {
            "price": row.get("close"),
            "rsi": row.get("rsi"),
            "macd": row.get("macd"),
            "atr": row.get("atr"),
        }

    def _empty_signal(self):
        return {
            "signal": "HOLD",
            "confidence": 0.0,
            "features": [],
            "indicators": {},
            "tech_confidence": 0.0,
            "ml_confidence": 0.0,
            "mtf_confidence": 0.0,
            "orderbook_score": 0.0,
            "vwap_confidence": 0.0,
            "volume_strength": 0.0,
        }
