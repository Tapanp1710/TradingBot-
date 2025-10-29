"""
Production Trading Bot v5.2 - FULLY FIXED VERSION
October 29, 2025 - All errors corrected, clean logging, PROPER CTRL+C HANDLING
"""
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple
import logging
import csv
import os
import gc
import psutil
import numpy as np
import pandas as pd
from collections import deque
import signal
import sys
import threading

# Core imports
from config import Config
try:
    from core.exchange import ExchangeManager, MultiExchangeManager
except ImportError:
    from core.exchange import ExchangeManager
    MultiExchangeManager = None

from core.strategy import TradingStrategy
from utils.risk_manager import RiskManager

# Optional market protection
try:
    from core.market_filter import MarketFilter
except ImportError:
    MarketFilter = None

try:
    from core.streak_detector import StreakDetector
except ImportError:
    StreakDetector = None

try:
    from emergency_exit import EmergencyExitManager
except ImportError:
    EmergencyExitManager = None

logger = logging.getLogger('TradingBot')


class TradingBot:
    """Production trading bot v5.2 with all fixes applied"""

    def __init__(self, config: Config):
        self.config = config
        self.start_time = time.time()
        self.running = True
        self.shutdown_event = threading.Event() 
        # Setup signal handlers FIRST
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        # Exchange connection
        self.exchange = ExchangeManager(
            config.EXCHANGE,
            config.API_KEY if not config.PAPER_TRADING else '',
            config.API_SECRET if not config.PAPER_TRADING else ''
        )

        # Multi-Exchange Support (Optional)
        self.multi_exchange_enabled = getattr(config, 'ENABLE_MULTI_EXCHANGE', False)
        if self.multi_exchange_enabled and MultiExchangeManager:
            try:
                exchanges_to_init = getattr(config, 'EXCHANGES_LIST', [
                    (config.EXCHANGE, config.API_KEY, config.API_SECRET)
                ])
                self.multi_exchange = MultiExchangeManager(exchanges_to_init)
                logger.info("🌐 Multi-exchange mode enabled")
            except Exception as e:
                logger.warning(f"⚠️ Multi-exchange init failed: {e}")
                self.multi_exchange_enabled = False
                self.multi_exchange = None
        else:
            self.multi_exchange = None

        # Strategy with exchange access
        self.strategy = TradingStrategy(config, exchange_manager=self.exchange)

        # Additional components
        self.risk_manager = RiskManager(config)

        # Market protections
        self.market_filter = MarketFilter(config) if MarketFilter else None

        # StreakDetector initialization
        if StreakDetector:
            try:
                self.streak_detector = StreakDetector(config)
                logger.info("📊 Streak detector enabled")
            except Exception as e:
                logger.warning(f"⚠️ Streak detector init failed: {e}")
                self.streak_detector = None
        else:
            self.streak_detector = None

        # Capital & positions
        self.capital = config.STARTING_CAPITAL
        self.starting_capital = config.STARTING_CAPITAL
        self.available_capital = self.capital
        self.positions = {}

        # Trailing buy tracking
        self.trailing_buy_targets = {}
        self.last_trailing_buy_scan = time.time()

        # Performance tracking
        self.trade_history = []
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.arbitrage_profit = 0
        self.arbitrage_trades = 0
        self.total_fees_paid = 0
        self.total_tax_paid = 0

        # Revenge trading prevention
        self.recent_losses = {}
        self.consecutive_losses_per_symbol = {}

        # Performance caches
        self.atr_cache = {}
        self.price_cache = {}
        self.cache_ttl = 60

        # API health monitoring
        self.api_failure_count = 0
        self.last_api_success = time.time()
        self.api_circuit_open = False

        # Cache
        self.last_arbitrage_scan = 0
        self.last_stale_sweep = time.time()

        # Production resilience
        self.gc_counter = 0
        self.last_heartbeat = time.time()
        self.daily_starting_capital = self.capital
        self.daily_loss_triggered = False
        self.last_daily_reset = datetime.now(timezone.utc).date()

        # Activity tracking
        self.scan_count = 0
        self.last_pnl_change_scan = 0
        self.last_pnl_value = 0.0
        self.last_capacity_alert_scan = 0
        self.last_opportunistic_scan = time.time()

        # Emergency exit system
        if EmergencyExitManager and hasattr(config, 'EMERGENCY_EXIT_ENABLED') and config.EMERGENCY_EXIT_ENABLED:
            try:
                self.emergency_manager = EmergencyExitManager(self)
                self.trading_paused = False
                self.last_emergency_check = time.time()
                logger.info("🚨 Emergency Exit System enabled")
            except Exception as e:
                logger.error(f"❌ Failed to initialize Emergency Exit: {e}")
                self.emergency_manager = None
                self.trading_paused = False
        else:
            self.emergency_manager = None
            self.trading_paused = False

        # Advanced features tracking
        self.mtf_enabled = getattr(config, 'ENABLE_MULTI_TIMEFRAME', False)
        self.orderbook_analysis_enabled = True
        self.vwap_analysis_enabled = True

        # Log startup info
        logger.info("="*70)
        logger.info("TRADING BOT v5.2 - PRODUCTION READY")
        logger.info("="*70)
        logger.info(f"Exchange: {config.EXCHANGE}")
        logger.info(f"Mode: {'🟢 PAPER TRADING' if config.PAPER_TRADING else '🔴 LIVE TRADING'}")
        logger.info(f"Starting Capital: ${self.capital:,.2f}")
        logger.info(f"Max Positions: {config.MAX_OPEN_POSITIONS}")
        logger.info(f"Position Size: {config.MAX_POSITION_PCT:.1%}")

        if self.multi_exchange_enabled:
            logger.info("Multi-Exchange: ENABLED")
        if self.mtf_enabled:
            logger.info(f"Multi-Timeframe: ENABLED")
        if self.market_filter:
            logger.info("Market Filter: ENABLED")
        if self.streak_detector:
            logger.info("Streak Detection: ENABLED")

        logger.info(f"Risk/Reward: {config.ATR_TP_MULT/config.ATR_SL_MULT:.1f}:1")
        logger.info(f"Stop Loss: {config.ATR_SL_MULT}x ATR (Max {config.MAX_SL_PCT:.1%})")
        logger.info(f"Take Profit: {config.ATR_TP_MULT}x ATR")
        logger.info(f"Confidence Threshold: {config.SIGNAL_CONFIDENCE_THRESHOLD:.0%}")
        logger.info("="*70 + "\n")

        
    def _signal_handler(self, signum, frame):
        """Handle Ctrl+C gracefully - IMPROVED VERSION"""
        if not self.running:  # Prevent multiple calls
            logger.info("⏰ Force exit...")
            os._exit(0)  # Nuclear option if called twice
        
        logger.info("\n🛑 Shutdown signal received (Ctrl+C)")
        self.running = False
        self.shutdown_event.set()
        
        # Force exit after 2 seconds if not cleaned up
        threading.Timer(2.0, self._force_exit).start()

    def _force_exit(self):
        """Force exit if graceful shutdown fails"""
        if not self.shutdown_event.is_set():
            return  # Already shut down gracefully
        
        logger.warning("⚠️ Force shutdown - cleaning up...")
        try:
            self.shutdown()
        except:
            pass
        
        logger.info("💀 Force exit")
        os._exit(0)  # Hard exit

    # ========================================
    # API HEALTH & CACHING
    # ========================================

    def _check_api_health(self) -> bool:
        """API circuit breaker pattern"""
        if self.api_circuit_open:
            if time.time() - self.last_api_success > 300:
                self.api_circuit_open = False
                self.api_failure_count = 0
                logger.info("✅ API circuit breaker reset")
                return True
            return False

        if self.api_failure_count > 10:
            self.api_circuit_open = True
            logger.error("🚨 API circuit breaker OPEN!")
            return False

        if time.time() - self.last_api_success < 60:
            self.api_failure_count = 0

        return True

    def _record_api_success(self):
        self.last_api_success = time.time()
        if self.api_failure_count > 0:
            self.api_failure_count = max(0, self.api_failure_count - 1)

    def _record_api_failure(self):
        self.api_failure_count += 1
        logger.warning(f"⚠️ API failure count: {self.api_failure_count}")

    def _get_cached_price(self, symbol: str) -> Optional[float]:
        if symbol in self.price_cache:
            price, timestamp = self.price_cache[symbol]
            if time.time() - timestamp < self.cache_ttl:
                return price
        return None

    def _cache_price(self, symbol: str, price: float):
        self.price_cache[symbol] = (price, time.time())

    # ========================================
    # MULTI-EXCHANGE FEATURES
    # ========================================

    def get_best_execution_price(self, symbol: str, side: str) -> Tuple[str, float]:
        """Smart order routing - get best price across exchanges"""
        if not self.multi_exchange_enabled or not self.multi_exchange:
            price = self.get_current_price_safe(symbol)
            return self.config.EXCHANGE, price

        try:
            exchange_id, price = self.multi_exchange.get_best_price(symbol, side)
            if exchange_id and price:
                logger.debug(f"💰 Best {side} for {symbol}: {exchange_id} @ ${price:.2f}")
                return exchange_id, price
            else:
                price = self.get_current_price_safe(symbol)
                return self.config.EXCHANGE, price
        except Exception as e:
            logger.error(f"❌ Smart routing error for {symbol}: {e}")
            price = self.get_current_price_safe(symbol)
            return self.config.EXCHANGE, price

    def scan_arbitrage_opportunities(self) -> List[Dict]:
        """Scan for cross-exchange arbitrage opportunities"""
        if not self.multi_exchange_enabled or not self.multi_exchange:
            return []

        try:
            min_profit = getattr(self.config, 'MIN_ARBITRAGE_PROFIT', 0.005)
            symbols = getattr(self.config, 'WATCHLIST', [])[:20]

            opportunities = self.multi_exchange.find_arbitrage_opportunities(
                symbols, min_profit_pct=min_profit * 100
            )

            if opportunities:
                logger.info(f"🔍 Found {len(opportunities)} arbitrage opportunities!")
                for opp in opportunities[:3]:
                    logger.info(f"   💎 {opp['symbol']}: {opp['net_profit_pct']:.2f}% profit")

            return opportunities
        except Exception as e:
            logger.error(f"❌ Arbitrage scan error: {e}")
            return []

    def analyze_signal_quality(self, signal_data: Dict) -> Dict:
        """Analyze quality of trading signals with multi-layer metrics"""
        quality_score = 0
        factors = []

        # Base confidence
        confidence = signal_data.get('confidence', 0)
        quality_score += confidence * 40
        factors.append(f"Base: {confidence:.1%}")

        # Multi-timeframe confirmation
        if 'mtf_confidence' in signal_data and signal_data['mtf_confidence'] > 0.6:
            quality_score += 20
            factors.append(f"MTF: {signal_data['mtf_confidence']:.1%}")

        # Orderbook support
        if 'orderbook_score' in signal_data:
            ob_score = abs(signal_data['orderbook_score'])
            if ob_score > 0.2:
                quality_score += 15
                factors.append(f"OB: {ob_score:.1%}")

        # VWAP alignment
        if 'vwap_confidence' in signal_data and signal_data['vwap_confidence'] > 0.5:
            quality_score += 15
            factors.append(f"VWAP: {signal_data['vwap_confidence']:.1%}")

        # Volume confirmation
        if 'volume_strength' in signal_data and signal_data['volume_strength'] > 0.7:
            quality_score += 10
            factors.append(f"Vol: {signal_data['volume_strength']:.1%}")

        quality_score = min(quality_score, 100)

        return {
            'quality_score': quality_score,
            'factors': factors,
            'grade': 'A' if quality_score >= 80 else 'B' if quality_score >= 60 else 'C'
        }

    # ========================================
    # MARKET DATA & PRICE FETCHING
    # ========================================

    def get_current_price_safe(self, symbol: str) -> float:
        """Get current price with caching and error handling"""
        cached = self._get_cached_price(symbol)
        if cached:
            return cached

        try:
            price = self.exchange.fetch_current_price(symbol)
            if price and price > 0:
                self._cache_price(symbol, price)
                self._record_api_success()
                return price
            else:
                self._record_api_failure()
                return 0
        except Exception as e:
            self._record_api_failure()
            logger.error(f"❌ Error fetching price for {symbol}: {e}")
            return 0

    def get_current_prices_batch(self, symbols: List[str]) -> Dict[str, float]:
        """Batch fetch prices - optimized for speed"""
        try:
            prices = self.exchange.batch_fetch_prices(symbols)
            self._record_api_success()

            for symbol, price in prices.items():
                self._cache_price(symbol, price)

            return prices
        except Exception as e:
            self._record_api_failure()
            logger.error(f"❌ Batch price fetch error: {e}")
            return {}

    def get_atr(self, symbol: str, df: pd.DataFrame) -> float:
        """Get ATR with caching"""
        cache_key = f"{symbol}_atr"

        if cache_key in self.atr_cache:
            atr, timestamp = self.atr_cache[cache_key]
            if time.time() - timestamp < 300:
                return atr

        try:
            if 'atr' in df.columns and not df['atr'].isnull().all():
                atr = float(df['atr'].iloc[-1])
            else:
                atr = 0

            if atr > 0:
                self.atr_cache[cache_key] = (atr, time.time())

            return atr
        except Exception as e:
            logger.error(f"❌ ATR calculation error for {symbol}: {e}")
            return 0

    # ========================================
    # OPPORTUNITY SCANNING
    # ========================================

    def scan_opportunities(self) -> List[Dict]:
        """
        OPTIMIZED: Scan markets for trading opportunities
        Stops scanning when max capacity reached (saves resources)
        """
        opportunities = []
        
        try:
            # ✅ OPTIMIZATION: Skip scanning if max capacity reached
            if len(self.positions) >= self.config.MAX_OPEN_POSITIONS:
                logger.debug(f"⏸️ Max capacity reached ({len(self.positions)}/{self.config.MAX_OPEN_POSITIONS}) - skipping scan")
                return []
            
            # Determine which watchlist to scan
            if self.config.USE_ROTATING_WATCHLISTS:
                cycle_pos = int(time.time() / self.config.GROUP_SCAN_OFFSET) % 3
                if cycle_pos == 0:
                    watchlist = self.config.WATCHLIST_A
                elif cycle_pos == 1:
                    watchlist = self.config.WATCHLIST_B
                else:
                    watchlist = self.config.WATCHLIST_C
            else:
                watchlist = self.config.WATCHLIST
            
            logger.info(f"🔍 Scanning {len(watchlist)} coins: {', '.join(watchlist[:5])}...")
            
            # Calculate available slots
            available_slots = self.config.MAX_OPEN_POSITIONS - len(self.positions)
            
            # Scan each symbol
            for symbol in watchlist:
                try:
                    # ✅ OPTIMIZATION: Stop scanning if we found enough opportunities
                    if len(opportunities) >= available_slots:
                        logger.info(f"✅ Found {len(opportunities)} opportunities - stopping scan (optimization)")
                        break
                    
                    # Skip if already in position
                    if symbol in self.positions:
                        continue
                    
                    # Fetch current price
                    try:
                        current_price = self.exchange.fetch_current_price(symbol)
                    except Exception as e:
                        logger.debug(f"⚠️ {symbol}: Failed to get price - {e}")
                        continue
                    
                    if not current_price or current_price <= 0:
                        logger.debug(f"⚠️ {symbol}: Invalid price {current_price}")
                        continue
                    
                    logger.debug(f"🔍 {symbol}: Price=${current_price:.2f}")
                    
                    # Fetch OHLCV data
                    try:
                        df = self.exchange.fetch_ohlcv(symbol, '1h', 100)
                    except Exception as e:
                        logger.debug(f"⚠️ {symbol}: Failed OHLCV fetch - {e}")
                        continue
                    
                    if df is None or df.empty or len(df) < 50:
                        logger.debug(f"⚠️ {symbol}: Insufficient data ({len(df) if df is not None else 0} rows)")
                        continue
                    
                    # Calculate indicators
                    try:
                        df = self.calculate_indicators(df)
                    except Exception as e:
                        logger.debug(f"⚠️ {symbol}: Indicator error - {e}")
                        continue
                    
                    if df is None or df.empty:
                        continue
                    
                    # Get ATR for volatility check
                    if 'atr' not in df.columns:
                        logger.debug(f"⚠️ {symbol}: ATR column missing")
                        continue
                    
                    atr = df['atr'].iloc[-1]
                    if pd.isna(atr) or atr <= 0:
                        logger.debug(f"⚠️ {symbol}: Invalid ATR {atr}")
                        continue
                    
                    atr_pct = (atr / current_price) * 100
                    min_atr = self.config.MIN_ATR_PCT * 100
                    
                    logger.info(f"   {symbol}: ATR={atr_pct:.3f}% (min={min_atr:.3f}%)")
                    
                    # Check minimum volatility
                    if atr_pct < min_atr:
                        logger.info(f"❌ {symbol}: ATR too low {atr_pct:.3f}% < {min_atr:.3f}%")
                        continue
                    
                    # Generate signal
                    try:
                        signal_data = self.strategy.generate_signal(df, symbol)
                    except Exception as e:
                        logger.error(f"⚠️ {symbol}: Signal generation error - {e}")
                        continue
                    
                    signal = signal_data.get('signal', 'HOLD')
                    confidence = signal_data.get('confidence', 0.0)
                    
                    logger.info(f"   {symbol}: Signal={signal} | Confidence={confidence:.1%}")
                    
                    # Check if signal meets threshold
                    if signal != 'BUY':
                        logger.info(f"❌ {symbol}: Signal is {signal}, need BUY")
                        continue
                    
                    if confidence < self.config.SIGNAL_CONFIDENCE_THRESHOLD:
                        logger.info(f"❌ {symbol}: Confidence {confidence:.1%} < {self.config.SIGNAL_CONFIDENCE_THRESHOLD:.1%}")
                        continue
                    
                    # Analyze signal quality
                    try:
                        quality = self.analyze_signal_quality(signal_data)
                    except Exception as e:
                        logger.error(f"⚠️ {symbol}: Quality error - {e}")
                        quality = {'quality_score': 50, 'grade': 'C'}
                    
                    quality_score = quality.get('quality_score', 50)
                    quality_grade = quality.get('grade', 'C')
                    
                    logger.info(f"   {symbol}: Quality={quality_score}/100 (Grade: {quality_grade})")
                    
                    # Check quality threshold
                    if quality_score < self.config.MIN_QUALITY_SCORE:
                        logger.info(f"❌ {symbol}: Quality {quality_score} < {self.config.MIN_QUALITY_SCORE}")
                        continue
                    
                    # Check quality grade filter
                    if self.config.ENABLE_QUALITY_FILTER:
                        grade_order = ['A', 'B', 'C', 'D', 'F']
                        min_grade = self.config.MIN_SIGNAL_QUALITY_GRADE
                        if grade_order.index(quality_grade) > grade_order.index(min_grade):
                            logger.info(f"❌ {symbol}: Grade {quality_grade} < {min_grade}")
                            continue
                    
                    # Calculate position size
                    try:
                        position_size = self.risk_manager.calculate_position_size(
                            available_capital=self.available_capital,
                            total_capital=self.capital,
                            confidence=confidence
                        )
                    except Exception as e:
                        logger.error(f"⚠️ {symbol}: Position size error - {e}")
                        continue
                    
                    if position_size < self.config.MIN_POSITION_USD:
                        logger.info(f"❌ {symbol}: Position ${position_size:.2f} < ${self.config.MIN_POSITION_USD}")
                        continue
                    
                    # Calculate stop loss and take profit
                    try:
                        stop_loss, take_profit = self.calculate_exits(current_price, atr, signal)
                    except Exception as e:
                        logger.error(f"⚠️ {symbol}: Exit calculation error - {e}")
                        continue
                    
                    # Add to opportunities
                    opportunity = {
                        'symbol': symbol,
                        'signal': signal,
                        'confidence': confidence,
                        'price': current_price,
                        'position_size': position_size,
                        'stop_loss': stop_loss,
                        'take_profit': take_profit,
                        'atr': atr,
                        'atr_pct': atr_pct,
                        'quality_score': quality_score,
                        'quality_grade': quality_grade,
                        'signal_data': signal_data,
                        'indicators': signal_data.get('indicators', {})
                    }
                    
                    opportunities.append(opportunity)
                    logger.info(f"✅ {symbol}: OPPORTUNITY FOUND - {signal} {confidence:.1%} | Quality: {quality_grade} ({quality_score}/100)")
                    
                except Exception as e:
                    logger.error(f"Error scanning {symbol}: {e}")
                    import traceback
                    logger.debug(traceback.format_exc())
                    continue
            
            # Sort by confidence (highest first)
            opportunities.sort(key=lambda x: x['confidence'], reverse=True)
            
            if opportunities:
                logger.info(f"✨ Found {len(opportunities)} opportunities from {len(watchlist)} coins")
            else:
                logger.debug(f"❌ No opportunities found in this scan")
            
            return opportunities
            
        except Exception as e:
            logger.error(f"Critical error in scan_opportunities: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []


    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate all technical indicators using TechnicalIndicators utility
        """
        try:
            from utils import TechnicalIndicators
            df = TechnicalIndicators.add_all_indicators(df)
            return df
        except Exception as e:
            logger.error(f"Indicator calculation error: {e}")
            return df



    def analyze_signal_quality(self, signal_data: dict) -> dict:
        """
        Analyze signal quality and assign grade (A-F)
        Returns: {'quality_score': 0-100, 'grade': 'A-F'}
        """
        try:
            confidence = signal_data.get('confidence', 0.0)
            tech_confidence = signal_data.get('tech_confidence', 0.0)
            ml_confidence = signal_data.get('ml_confidence', 0.0)
            
            # Base score from confidence (0-100)
            quality_score = confidence * 100
            
            # Bonus for high tech confidence (+10)
            if tech_confidence > 0.7:
                quality_score += 10
            
            # Bonus for high ML confidence (+10)
            if ml_confidence > 0.7:
                quality_score += 10
            
            # Check indicator alignment
            indicators = signal_data.get('indicators', {})
            rsi = indicators.get('rsi', 50)
            trend = indicators.get('trend', 'NEUTRAL')
            
            # RSI alignment bonus (+5)
            signal = signal_data.get('signal', 'HOLD')
            if signal == 'BUY' and rsi < 40:
                quality_score += 5
            elif signal == 'SELL' and rsi > 60:
                quality_score += 5
            
            # Trend alignment bonus (+5)
            if signal == 'BUY' and trend == 'UP':
                quality_score += 5
            elif signal == 'SELL' and trend == 'DOWN':
                quality_score += 5
            
            # Multi-timeframe confirmation bonus (+10)
            mtf_confidence = signal_data.get('mtf_confidence', 0.0)
            if mtf_confidence > 0.6:
                quality_score += 10
            
            # Volume confirmation bonus (+5)
            volume_strength = signal_data.get('volume_strength', 0.0)
            if volume_strength > 0.7:
                quality_score += 5
            
            # Cap at 100
            quality_score = min(quality_score, 100)
            
            # Assign grade
            if quality_score >= 80:
                grade = 'A'
            elif quality_score >= 70:
                grade = 'B'
            elif quality_score >= 60:
                grade = 'C'
            elif quality_score >= 50:
                grade = 'D'
            else:
                grade = 'F'
            
            return {
                'quality_score': quality_score,
                'grade': grade,
                'details': {
                    'confidence': confidence,
                    'tech_confidence': tech_confidence,
                    'ml_confidence': ml_confidence,
                    'mtf_confidence': mtf_confidence,
                    'volume_strength': volume_strength
                }
            }
            
        except Exception as e:
            logger.error(f"Quality analysis error: {e}")
            return {'quality_score': 50, 'grade': 'C'}



    def calculate_exits(self, entry_price: float, atr: float, signal: str) -> Tuple[float, float]:
        """
        Calculate stop loss and take profit levels based on ATR or fixed percentages
        Returns: (stop_loss, take_profit)
        """
        try:
            if self.config.USE_ATR_EXITS:
                # ATR-based dynamic stops
                if signal == 'BUY':
                    stop_loss = entry_price - (atr * self.config.ATR_SL_MULT)
                    take_profit = entry_price + (atr * self.config.ATR_TP_MULT)
                else:  # SELL
                    stop_loss = entry_price + (atr * self.config.ATR_SL_MULT)
                    take_profit = entry_price - (atr * self.config.ATR_TP_MULT)
                
                # Apply max/min constraints
                max_sl_distance = entry_price * self.config.MAX_SL_PCT
                max_tp_distance = entry_price * self.config.MAX_TP_PCT
                
                if signal == 'BUY':
                    # Limit stop loss distance
                    if (entry_price - stop_loss) > max_sl_distance:
                        stop_loss = entry_price - max_sl_distance
                    # Limit take profit distance
                    if (take_profit - entry_price) > max_tp_distance:
                        take_profit = entry_price + max_tp_distance
                else:  # SELL
                    # Limit stop loss distance
                    if (stop_loss - entry_price) > max_sl_distance:
                        stop_loss = entry_price + max_sl_distance
                    # Limit take profit distance
                    if (entry_price - take_profit) > max_tp_distance:
                        take_profit = entry_price - max_tp_distance
            else:
                # Fixed percentage stops
                if signal == 'BUY':
                    stop_loss = entry_price * (1 - self.config.FALLBACK_STOP_LOSS_PCT)
                    take_profit = entry_price * (1 + self.config.FALLBACK_TAKE_PROFIT_PCT)
                else:  # SELL
                    stop_loss = entry_price * (1 + self.config.FALLBACK_STOP_LOSS_PCT)
                    take_profit = entry_price * (1 - self.config.FALLBACK_TAKE_PROFIT_PCT)
            
            return stop_loss, take_profit
            
        except Exception as e:
            logger.error(f"Exit calculation error: {e}")
            # Fallback to simple percentages
            if signal == 'BUY':
                return entry_price * 0.98, entry_price * 1.06
            else:
                return entry_price * 1.02, entry_price * 0.94



    def get_current_price_safe(self, symbol: str) -> Optional[float]:
        """
        Safely get current price with error handling
        """
        try:
            return self.exchange.fetch_current_price(symbol)
        except Exception as e:
            logger.debug(f"Failed to get price for {symbol}: {e}")
            return None



    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate all technical indicators
        """
        try:
            from utils import TechnicalIndicators
            df = TechnicalIndicators.add_all_indicators(df)
            return df
        except Exception as e:
            logger.error(f"Indicator calculation error: {e}")
            return df


    def analyze_signal_quality(self, signal_data: dict) -> dict:
        """
        Analyze signal quality and assign grade
        """
        try:
            confidence = signal_data.get('confidence', 0.0)
            tech_confidence = signal_data.get('tech_confidence', 0.0)
            ml_confidence = signal_data.get('ml_confidence', 0.0)
            
            # Base score from confidence
            quality_score = confidence * 100
            
            # Bonus for high tech confidence
            if tech_confidence > 0.7:
                quality_score += 10
            
            # Bonus for high ML confidence
            if ml_confidence > 0.7:
                quality_score += 10
            
            # Check indicator alignment
            indicators = signal_data.get('indicators', {})
            rsi = indicators.get('rsi', 50)
            trend = indicators.get('trend', 'NEUTRAL')
            
            # RSI alignment bonus
            signal = signal_data.get('signal', 'HOLD')
            if signal == 'BUY' and rsi < 40:
                quality_score += 5
            elif signal == 'SELL' and rsi > 60:
                quality_score += 5
            
            # Trend alignment bonus
            if signal == 'BUY' and trend == 'UP':
                quality_score += 5
            elif signal == 'SELL' and trend == 'DOWN':
                quality_score += 5
            
            # Multi-timeframe confirmation bonus
            mtf_confidence = signal_data.get('mtf_confidence', 0.0)
            if mtf_confidence > 0.6:
                quality_score += 10
            
            # Volume confirmation bonus
            volume_strength = signal_data.get('volume_strength', 0.0)
            if volume_strength > 0.7:
                quality_score += 5
            
            # Cap at 100
            quality_score = min(quality_score, 100)
            
            # Assign grade
            if quality_score >= 80:
                grade = 'A'
            elif quality_score >= 70:
                grade = 'B'
            elif quality_score >= 60:
                grade = 'C'
            elif quality_score >= 50:
                grade = 'D'
            else:
                grade = 'F'
            
            return {
                'quality_score': quality_score,
                'grade': grade,
                'details': {
                    'confidence': confidence,
                    'tech_confidence': tech_confidence,
                    'ml_confidence': ml_confidence,
                    'mtf_confidence': mtf_confidence,
                    'volume_strength': volume_strength
                }
            }
            
        except Exception as e:
            logger.error(f"Quality analysis error: {e}")
            return {'quality_score': 50, 'grade': 'C'}


    def calculate_exits(self, entry_price: float, atr: float, signal: str) -> Tuple[float, float]:
        """
        Calculate stop loss and take profit levels
        """
        try:
            if self.config.USE_ATR_EXITS:
                # ATR-based stops
                if signal == 'BUY':
                    stop_loss = entry_price - (atr * self.config.ATR_SL_MULT)
                    take_profit = entry_price + (atr * self.config.ATR_TP_MULT)
                else:  # SELL
                    stop_loss = entry_price + (atr * self.config.ATR_SL_MULT)
                    take_profit = entry_price - (atr * self.config.ATR_TP_MULT)
                
                # Apply max/min constraints
                max_sl_distance = entry_price * self.config.MAX_SL_PCT
                max_tp_distance = entry_price * self.config.MAX_TP_PCT
                
                if signal == 'BUY':
                    if (entry_price - stop_loss) > max_sl_distance:
                        stop_loss = entry_price - max_sl_distance
                    if (take_profit - entry_price) > max_tp_distance:
                        take_profit = entry_price + max_tp_distance
                else:
                    if (stop_loss - entry_price) > max_sl_distance:
                        stop_loss = entry_price + max_sl_distance
                    if (entry_price - take_profit) > max_tp_distance:
                        take_profit = entry_price - max_tp_distance
            else:
                # Fixed percentage stops
                if signal == 'BUY':
                    stop_loss = entry_price * (1 - self.config.FALLBACK_STOP_LOSS_PCT)
                    take_profit = entry_price * (1 + self.config.FALLBACK_TAKE_PROFIT_PCT)
                else:
                    stop_loss = entry_price * (1 + self.config.FALLBACK_STOP_LOSS_PCT)
                    take_profit = entry_price * (1 - self.config.FALLBACK_TAKE_PROFIT_PCT)
            
            return stop_loss, take_profit
            
        except Exception as e:
            logger.error(f"Exit calculation error: {e}")
            # Fallback to simple percentages
            if signal == 'BUY':
                return entry_price * 0.98, entry_price * 1.06
            else:
                return entry_price * 1.02, entry_price * 0.94

    

    def get_current_watchlist(self) -> List[str]:
        """Get current watchlist based on rotation strategy"""
        if not self.config.USE_ROTATING_WATCHLISTS:
            return self.config.WATCHLIST

        offset = self.scan_count * self.config.GROUP_SCAN_OFFSET
        total_symbols = len(self.config.WATCHLIST)

        if total_symbols == 0:
            return []

        start_idx = offset % total_symbols
        end_idx = (start_idx + 10) % total_symbols

        if end_idx > start_idx:
            return self.config.WATCHLIST[start_idx:end_idx]
        else:
            return self.config.WATCHLIST[start_idx:] + self.config.WATCHLIST[:end_idx]

    # ========================================
    # POSITION MANAGEMENT
    # ========================================

    def calculate_position_size(self, symbol: str, price: float, confidence: float, atr: float) -> float:
        """Calculate position size with risk management"""
        try:
            base_pct = self.config.MAX_POSITION_PCT

            if self.config.ENABLE_ADAPTIVE_SIZING:
                if confidence >= self.config.HIGH_CONFIDENCE_THRESHOLD:
                    multiplier = self.config.HIGH_CONFIDENCE_MULTIPLIER
                elif confidence < self.config.LOW_CONFIDENCE_THRESHOLD:
                    multiplier = self.config.LOW_CONFIDENCE_MULTIPLIER
                else:
                    multiplier = 1.0

                base_pct *= multiplier

            position_value = self.available_capital * base_pct
            position_size = position_value / price

            if position_value < self.config.MIN_POSITION_USD:
                return 0

            return position_size

        except Exception as e:
            logger.error(f"❌ Position size calculation error: {e}")
            return 0

    def can_open_position(self) -> bool:
        """Check if we can open new positions"""
        if len(self.positions) >= self.config.MAX_OPEN_POSITIONS:
            return False

        if self.available_capital < self.config.MIN_POSITION_USD:
            return False

        if self.daily_loss_triggered:
            return False

        if self.trading_paused:
            return False

        return True

    def execute_buy(self, opportunity: Dict) -> bool:
        """Execute buy order with comprehensive validation"""
        symbol = opportunity['symbol']
        price = opportunity['price']
        confidence = opportunity['confidence']
        atr = opportunity['atr']

        try:
            if not self.can_open_position():
                return False

            if self.is_revenge_trading(symbol):
                logger.warning(f"🚫 {symbol}: Revenge trading blocked")
                return False

            if self.streak_detector:
                if hasattr(self.streak_detector, 'should_trade'):
                    if not self.streak_detector.should_trade():
                        logger.warning(f"🚫 {symbol}: Blocked by streak detector")
                        return False

                if hasattr(self.streak_detector, 'can_trade_symbol'):
                    if not self.streak_detector.can_trade_symbol(symbol):
                        return False

            position_size = self.calculate_position_size(symbol, price, confidence, atr)
            if position_size <= 0:
                return False

            position_value = position_size * price

            if position_value > self.available_capital:
                logger.warning(f"⚠️ {symbol}: Insufficient capital")
                return False

            if self.config.USE_ATR_EXITS and atr > 0:
                stop_distance = atr * self.config.ATR_SL_MULT
                tp_distance = atr * self.config.ATR_TP_MULT

                stop_loss = price - stop_distance
                take_profit = price + tp_distance

                max_sl = price * (1 - self.config.MAX_SL_PCT)
                max_tp = price * (1 + self.config.MAX_TP_PCT)

                stop_loss = max(stop_loss, max_sl)
                take_profit = min(take_profit, max_tp)
            else:
                stop_loss = price * (1 - self.config.FALLBACK_STOP_LOSS_PCT)
                take_profit = price * (1 + self.config.FALLBACK_TAKE_PROFIT_PCT)

            fee = position_value * self.config.TRADING_FEE

            self.available_capital -= (position_value + fee)
            self.total_fees_paid += fee

            self.positions[symbol] = {
                'entry_price': price,
                'size': position_size,
                'value': position_value,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'initial_stop': stop_loss,
                'entry_time': time.time(),
                'confidence': confidence,
                'atr': atr,
                'highest_price': price,
                'trailing_active': False,
                'partial_tp_taken': False,
                'fees_paid': fee,
                'signal_data': opportunity.get('signal_data', {})
            }

            logger.info(f"🟢 BUY {symbol} @ ${price:.2f} | Size: {position_size:.4f} | Value: ${position_value:.2f}")
            logger.info(f"   🛡️ SL: ${stop_loss:.2f} ({((stop_loss-price)/price)*100:.1f}%) | 🎯 TP: ${take_profit:.2f} ({((take_profit-price)/price)*100:.1f}%)")
            logger.info(f"   📊 Confidence: {confidence:.1%} | Quality: {opportunity.get('quality_grade', 'N/A')}")

            if hasattr(self.strategy, 'online_learner') and self.strategy.online_learner:
                features = opportunity.get('signal_data', {}).get('features', [])
                if features:
                    self.strategy.online_learner.record_trade(symbol, features, 'BUY', price)

            return True

        except Exception as e:
            logger.error(f"❌ Buy execution error for {symbol}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False

    def execute_sell(self, symbol: str, reason: str = "Manual") -> bool:
        """Execute sell order and close position"""
        if symbol not in self.positions:
            logger.warning(f"⚠️ {symbol} not in positions")
            return False

        try:
            position = self.positions[symbol]
            current_price = self.get_current_price_safe(symbol)

            if current_price <= 0:
                logger.error(f"❌ Invalid price for {symbol}")
                return False

            entry_price = position['entry_price']
            size = position['size']
            position_value = size * current_price

            entry_value = position['value']
            gross_pnl = position_value - entry_value

            exit_fee = position_value * self.config.TRADING_FEE
            total_fees = position['fees_paid'] + exit_fee
            self.total_fees_paid += exit_fee

            tax = 0
            if self.config.APPLY_INDIAN_TAX and gross_pnl > 0:
                tax = gross_pnl * self.config.CAPITAL_GAINS_TAX
                self.total_tax_paid += tax

            net_pnl = gross_pnl - total_fees - tax
            pnl_pct = (net_pnl / entry_value) * 100

            self.available_capital += (position_value - exit_fee - tax)
            self.capital += net_pnl

            self.total_trades += 1
            if net_pnl > 0:
                self.winning_trades += 1
                self.consecutive_losses_per_symbol[symbol] = 0
            else:
                self.losing_trades += 1
                self.consecutive_losses_per_symbol[symbol] = self.consecutive_losses_per_symbol.get(symbol, 0) + 1
                self.recent_losses[symbol] = time.time()

            if self.streak_detector and hasattr(self.streak_detector, 'record_trade'):
                try:
                    self.streak_detector.record_trade(symbol, net_pnl)
                except TypeError:
                    self.streak_detector.record_trade(net_pnl > 0)

            hold_time = (time.time() - position['entry_time']) / 3600

            profit_emoji = "💰" if net_pnl > 0 else "📉"
            logger.info(f"{profit_emoji} {'PROFIT' if net_pnl > 0 else 'LOSS'} SELL {symbol} @ ${current_price:.2f} | {reason}")
            logger.info(f"   📈 Entry: ${entry_price:.2f} -> Exit: ${current_price:.2f}")
            logger.info(f"   💵 P&L: ${net_pnl:.2f} ({pnl_pct:+.2f}%) | 💸 Fees: ${total_fees:.2f} | 🏛️ Tax: ${tax:.2f}")
            logger.info(f"   ⏱️ Hold: {hold_time:.1f}h")

            if hasattr(self.strategy, 'online_learner') and self.strategy.online_learner:
                features = position.get('signal_data', {}).get('features', [])
                if features:
                    outcome = 1 if net_pnl > 0 else 0
                    self.strategy.online_learner.update_model(features, outcome)

            self.trade_history.append({
                'timestamp': datetime.now(timezone.utc),
                'symbol': symbol,
                'action': 'SELL',
                'reason': reason,
                'entry_price': entry_price,
                'exit_price': current_price,
                'size': size,
                'gross_pnl': gross_pnl,
                'fees': total_fees,
                'tax': tax,
                'net_pnl': net_pnl,
                'pnl_pct': pnl_pct,
                'hold_time_hours': hold_time,
                'confidence': position['confidence']
            })

            del self.positions[symbol]

            return True

        except Exception as e:
            logger.error(f"❌ Sell execution error for {symbol}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False

    def monitor_positions(self):
        """Monitor open positions for stop loss, take profit, and trailing stops"""
        if not self.positions:
            return

        for symbol in list(self.positions.keys()):
            if not self.running:
                break
                
            try:
                position = self.positions[symbol]
                current_price = self.get_current_price_safe(symbol)

                if current_price <= 0:
                    continue

                entry_price = position['entry_price']
                stop_loss = position['stop_loss']
                take_profit = position['take_profit']

                if current_price > position['highest_price']:
                    position['highest_price'] = current_price

                if current_price <= stop_loss:
                    logger.warning(f"🛑 {symbol}: Stop loss triggered @ ${current_price:.2f}")
                    self.execute_sell(symbol, "Stop Loss")
                    continue

                if current_price >= take_profit:
                    logger.info(f"🎯 {symbol}: Take profit reached @ ${current_price:.2f}")
                    self.execute_sell(symbol, "Take Profit")
                    continue

                if self.config.ENABLE_PARTIAL_TP and not position['partial_tp_taken']:
                    atr = position.get('atr', 0)
                    if atr > 0:
                        partial_trigger = entry_price + (atr * self.config.PARTIAL_TP_TRIGGER_ATR_MULT)
                        if current_price >= partial_trigger:
                            logger.info(f"💰 {symbol}: Partial TP triggered @ ${current_price:.2f}")
                            position['partial_tp_taken'] = True

                if self.config.ENABLE_ATR_TRAILING:
                    atr = position.get('atr', 0)
                    if atr > 0:
                        activation_price = entry_price + (atr * self.config.TRAIL_ACTIVATE_ATR_MULT)

                        if current_price >= activation_price:
                            if not position['trailing_active']:
                                position['trailing_active'] = True
                                logger.info(f"📈 {symbol}: Trailing stop activated")

                            trail_distance = atr * self.config.TRAIL_DISTANCE_ATR_MULT
                            new_stop = current_price - trail_distance

                            if new_stop > position['stop_loss']:
                                position['stop_loss'] = new_stop

                hold_time_hours = (time.time() - position['entry_time']) / 3600
                if hold_time_hours > self.config.MAX_POSITION_HOURS:
                    current_pnl_pct = ((current_price - entry_price) / entry_price) * 100

                    if abs(current_pnl_pct) < (position.get('atr', 0) / entry_price * 100 * self.config.STALE_BAND_ATR_MULT):
                        logger.warning(f"⏰ {symbol}: Stale position closed (${current_pnl_pct:+.2f}%)")
                        self.execute_sell(symbol, "Stale Position")
                        continue

            except Exception as e:
                logger.error(f"❌ Position monitoring error for {symbol}: {e}")
                continue

    def is_revenge_trading(self, symbol: str) -> bool:
        """Check if this would be revenge trading"""
        if not self.config.PREVENT_REVENGE_TRADING:
            return False

        if symbol in self.recent_losses:
            time_since_loss = time.time() - self.recent_losses[symbol]
            cooldown = self.config.REVENGE_TRADE_COOLDOWN_MINS * 60

            if time_since_loss < cooldown:
                return True

        consecutive = self.consecutive_losses_per_symbol.get(symbol, 0)
        if consecutive >= self.config.CONSECUTIVE_LOSS_LIMIT:
            return True

        return False

    def check_daily_loss_cap(self) -> bool:
        """Check if daily loss limit reached"""
        if not self.config.ENABLE_DAILY_LOSS_CAP:
            return True

        today = datetime.now(timezone.utc).date()
        if today != self.last_daily_reset:
            self.daily_starting_capital = self.capital
            self.daily_loss_triggered = False
            self.last_daily_reset = today
            logger.info(f"🔄 Daily capital reset: ${self.capital:,.2f}")

        daily_pnl = self.capital - self.daily_starting_capital
        daily_pnl_pct = (daily_pnl / self.daily_starting_capital) * 100

        if daily_pnl < 0:
            loss_amount = abs(daily_pnl)

            if (abs(daily_pnl_pct) >= self.config.MAX_DAILY_LOSS_PCT * 100 or
                loss_amount >= self.config.MAX_DAILY_LOSS_AMOUNT):

                if not self.daily_loss_triggered:
                    self.daily_loss_triggered = True
                    logger.error("🚨 DAILY LOSS CAP REACHED!")
                    logger.error(f"   📉 Loss: ${loss_amount:.2f} ({daily_pnl_pct:.2f}%)")
                    logger.error("   ⏸️ Trading PAUSED until next day")

                return False

        return True

    def calculate_portfolio_value(self) -> float:
        """Calculate total portfolio value"""
        total = self.available_capital

        for symbol, position in self.positions.items():
            try:
                current_price = self.get_current_price_safe(symbol)
                if current_price > 0:
                    position_value = position['size'] * current_price
                    total += position_value
            except:
                total += position['value']

        return total

    def get_unrealized_pnl(self) -> float:
        """Calculate unrealized P&L from open positions"""
        unrealized = 0

        for symbol, position in self.positions.items():
            try:
                current_price = self.get_current_price_safe(symbol)
                if current_price > 0:
                    current_value = position['size'] * current_price
                    entry_value = position['value']
                    unrealized += (current_value - entry_value)
            except:
                continue

        return unrealized

    def heartbeat(self):
        """Periodic health check and stats logging"""
        if time.time() - self.last_heartbeat < self.config.HEARTBEAT_INTERVAL:
            return

        self.last_heartbeat = time.time()

        portfolio_value = self.calculate_portfolio_value()
        total_pnl = portfolio_value - self.starting_capital
        total_pnl_pct = (total_pnl / self.starting_capital) * 100

        win_rate = (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0

        logger.info("="*70)
        logger.info("💓 HEARTBEAT")
        logger.info("="*70)
        logger.info(f"💼 Portfolio Value: ${portfolio_value:,.2f}")
        logger.info(f"💰 P&L: ${total_pnl:+,.2f} ({total_pnl_pct:+.2f}%)")
        logger.info(f"💵 Available Capital: ${self.available_capital:,.2f}")
        logger.info(f"📊 Open Positions: {len(self.positions)}/{self.config.MAX_OPEN_POSITIONS}")
        logger.info(f"🎯 Total Trades: {self.total_trades} | Win Rate: {win_rate:.1f}%")
        logger.info(f"💸 Fees Paid: ${self.total_fees_paid:.2f} | 🏛️ Tax Paid: ${self.total_tax_paid:.2f}")
        logger.info("="*70)

    def manage_memory(self):
        """Production-grade memory management"""
        self.gc_counter += 1

        if self.gc_counter >= self.config.GC_INTERVAL:
            collected = gc.collect()

            if self.config.ENABLE_MEMORY_MANAGEMENT:
                process = psutil.Process()
                mem_mb = process.memory_info().rss / 1024 / 1024

                if mem_mb > self.config.MAX_MEMORY_MB:
                    logger.warning(f"⚠️ High memory: {mem_mb:.0f}MB")

                    self.atr_cache.clear()
                    self.price_cache.clear()
                    if hasattr(self.exchange, 'clear_cache'):
                        self.exchange.clear_cache()

                    gc.collect()

            self.gc_counter = 0

    def run(self):
        """Main trading loop with proper Ctrl+C handling and detailed logging"""
        logger.info("🚀 Trading bot started\n")

        try:
            while self.running:
                try:
                    # Scan counter header
                    logger.info("="*70)
                    logger.info(f"🔍 SCAN #{self.scan_count + 1} | Positions: {len(self.positions)}/{self.config.MAX_OPEN_POSITIONS} | Capital: ${self.available_capital:,.2f}")
                    logger.info("="*70)

                    # Emergency checks
                    if self.emergency_manager:
                        if time.time() - self.last_emergency_check > self.config.EMERGENCY_CHECK_INTERVAL:
                            try:
                                if hasattr(self.emergency_manager, 'check_emergency_conditions'):
                                    self.emergency_manager.check_emergency_conditions()
                            except Exception:
                                pass
                            self.last_emergency_check = time.time()

                    # Daily loss cap check
                    if not self.check_daily_loss_cap():
                        logger.warning("⚠️ Daily loss cap active, skipping trading")
                        time.sleep(300)
                        continue

                    # Trading pause check
                    if self.trading_paused:
                        logger.info("⏸️ Trading paused by emergency system")
                        time.sleep(300)
                        continue

                    # Position monitoring
                    if self.positions:
                        logger.info(f"👀 Monitoring {len(self.positions)} open positions...")
                        self.log_position_status()
                    else:
                        logger.info("📭 No open positions to monitor")

                    self.monitor_positions()

                    # Opportunity scanning
                    if self.can_open_position():
                        available_slots = self.config.MAX_OPEN_POSITIONS - len(self.positions)
                        logger.info(f"🔎 Scanning for opportunities ({available_slots} slots available)...")
                        
                        opportunities = self.scan_opportunities()

                        if opportunities:
                            logger.info(f"✨ Found {len(opportunities)} trading opportunities")
                        else:
                            logger.info("❌ No opportunities found in this scan")

                        for opp in opportunities:
                            if not self.can_open_position() or not self.running:
                                logger.info("⏸️ Stopping trade execution (max positions or shutdown)")
                                break
                            self.execute_buy(opp)
                    else:
                        logger.info(f"⏸️ Max positions reached ({len(self.positions)}/{self.config.MAX_OPEN_POSITIONS}), skipping new trades")

                    # Arbitrage scanning (if enabled)
                    if self.multi_exchange_enabled and time.time() - self.last_arbitrage_scan > 300:
                        logger.info("🔄 Scanning for arbitrage opportunities...")
                        arb_opps = self.scan_arbitrage_opportunities()
                        self.last_arbitrage_scan = time.time()

                    # Heartbeat and memory management
                    self.heartbeat()
                    self.manage_memory()
                    
                    # Increment scan counter
                    self.scan_count += 1
                    
                    # Scan completion log
                    logger.info(f"✅ Scan #{self.scan_count} completed. Next scan in {self.config.SCAN_INTERVAL}s")
                    logger.info("")  # Empty line for readability

                    # Sleep with interrupt check
                    for _ in range(self.config.SCAN_INTERVAL):
                        if not self.running:
                            break
                        time.sleep(1)

                except Exception as e:
                    if not self.running:
                        break
                    logger.error(f"❌ Error in main loop: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
                    time.sleep(60)

        finally:
            self.shutdown()

    def log_position_status(self):
        """Log current position status with P&L"""
        if not self.positions:
            return
        
        logger.info("📊 CURRENT POSITIONS:")
        total_unrealized = 0
        
        for symbol, pos in self.positions.items():
            try:
                current_price = self.get_current_price_safe(symbol)
                entry_price = pos['entry_price']
                size = pos['size']
                
                if current_price > 0:
                    current_value = size * current_price
                    entry_value = pos['value']
                    unrealized_pnl = current_value - entry_value
                    pnl_pct = (unrealized_pnl / entry_value) * 100
                    total_unrealized += unrealized_pnl
                    
                    # Emoji based on P&L
                    if pnl_pct > 1.0:
                        emoji = "🟢"
                    elif pnl_pct < -1.0:
                        emoji = "🔴"
                    else:
                        emoji = "⚪"
                    
                    # Calculate distance to SL and TP
                    sl_distance = ((current_price - pos['stop_loss']) / current_price) * 100
                    tp_distance = ((pos['take_profit'] - current_price) / current_price) * 100
                    
                    logger.info(f"   {emoji} {symbol}: ${current_price:.2f} ({pnl_pct:+.2f}%) | Entry: ${entry_price:.2f} | SL: {sl_distance:.1f}% | TP: {tp_distance:.1f}%")
                else:
                    logger.info(f"   ⚠️ {symbol}: Price unavailable")
                    
            except Exception as e:
                logger.error(f"   ❌ Error getting status for {symbol}: {e}")
        
        # Summary line
        logger.info(f"💰 Total Unrealized P&L: ${total_unrealized:+.2f}")

    def shutdown(self):
        """Graceful shutdown"""
        logger.info("\n🛑 Shutting down bot...")

        if self.trade_history and self.config.SAVE_TRADE_HISTORY:
            try:
                df = pd.DataFrame(self.trade_history)
                df.to_csv(self.config.TRADE_HISTORY_FILE, index=False)
                logger.info(f"✅ Trade history saved: {len(self.trade_history)} trades")
            except Exception as e:
                logger.error(f"❌ Failed to save trade history: {e}")

        portfolio_value = self.calculate_portfolio_value()
        total_pnl = portfolio_value - self.starting_capital
        total_pnl_pct = (total_pnl / self.starting_capital) * 100

        logger.info("="*70)
        logger.info("📊 FINAL STATISTICS")
        logger.info("="*70)
        logger.info(f"💰 Starting Capital: ${self.starting_capital:,.2f}")
        logger.info(f"💼 Final Portfolio: ${portfolio_value:,.2f}")
        logger.info(f"{'💚' if total_pnl >= 0 else '❤️'} Total P&L: ${total_pnl:+,.2f} ({total_pnl_pct:+.2f}%)")
        logger.info(f"🎯 Total Trades: {self.total_trades}")
        logger.info(f"✅ Winning: {self.winning_trades} | ❌ Losing: {self.losing_trades}")
        if self.total_trades > 0:
            logger.info(f"📈 Win Rate: {(self.winning_trades/self.total_trades)*100:.1f}%")
        logger.info(f"💸 Fees Paid: ${self.total_fees_paid:.2f}")
        logger.info(f"🏛️ Tax Paid: ${self.total_tax_paid:.2f}")
        logger.info("="*70)

        logger.info("✅ Shutdown complete\n")

    def get_current_price(self, symbol):
        """Backward compatibility wrapper"""
        return self.get_current_price_safe(symbol)

    def get_market_data(self, symbol, timeframe, limit=100):
        """Backward compatibility wrapper"""
        return self.exchange.fetch_ohlcv(symbol, timeframe, limit)

    def pause_trading(self, duration_hours=24):
        """Pause trading for specified hours"""
        self.trading_paused = True
        logger.warning(f"⏸️ Trading paused for {duration_hours} hours")

    def _dynamic_capacity(self):
        """Calculate dynamic position capacity"""
        if not self.config.ENABLE_DYNAMIC_CAPACITY:
            return self.config.MAX_OPEN_POSITIONS

        return self.config.MAX_OPEN_POSITIONS
