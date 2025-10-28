"""
Emergency Exit Manager v3.0 - OPTIMIZED
- Config-driven thresholds
- Better error handling
- Partial liquidation protection
- Daily emergency limit
- Fee-aware P&L
"""
import logging
import time
from typing import Tuple, Optional
from datetime import datetime, timezone
from .bear_detector import BearMarketDetector
from .regime_detector import MarketRegimeDetector
from .fear_greed import FearGreedMonitor

logger = logging.getLogger('TradingBot')


class EmergencyExitManager:
    """Coordinate emergency exit decisions with production safeguards"""
    
    def __init__(self, bot):
        self.bot = bot
        self.config = bot.config
        
        # Initialize detectors
        try:
            self.bear_detector = BearMarketDetector(
                api_key=getattr(self.config, 'CRYPTOPANIC_API_KEY', None)
            )
            self.regime_detector = MarketRegimeDetector()
            self.fear_greed = FearGreedMonitor()
            logger.info("✅ All emergency detectors initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize detectors: {e}")
            raise
        
        # Load thresholds from config (with fallbacks)
        self.SENTIMENT_THRESHOLD = getattr(self.config, 'BEAR_SENTIMENT_THRESHOLD', -0.4)
        self.FEAR_INDEX_THRESHOLD = getattr(self.config, 'BEAR_FEAR_INDEX', 20)
        self.BTC_DROP_THRESHOLD = getattr(self.config, 'BEAR_BTC_DROP', -15)
        self.MIN_SIGNALS_REQUIRED = getattr(self.config, 'MIN_BEAR_SIGNALS', 2)
        
        # Emergency state
        self.emergency_exit_active = False
        self.exit_timestamp = None
        self.exit_reason = None
        
        # Rate limiting for emergency exits
        self.emergency_exits_today = 0
        self.last_emergency_date = datetime.now(timezone.utc).date()
        self.max_emergency_exits_per_day = 3
        
        logger.info(f"🛡️ Emergency thresholds: Sentiment<{self.SENTIMENT_THRESHOLD}, "
                   f"Fear<{self.FEAR_INDEX_THRESHOLD}, BTC<{self.BTC_DROP_THRESHOLD}%")
    
    def check_emergency_exit(self) -> Tuple[bool, str]:
        """
        Check if conditions warrant emergency exit
        Returns: (should_exit: bool, reason: str)
        """
        
        # Already in emergency mode
        if self.emergency_exit_active:
            return True, f"Already in emergency mode: {self.exit_reason}"
        
        # Check daily limit
        today = datetime.now(timezone.utc).date()
        if today != self.last_emergency_date:
            self.emergency_exits_today = 0
            self.last_emergency_date = today
        
        if self.emergency_exits_today >= self.max_emergency_exits_per_day:
            logger.warning(f"⚠️ Max emergency exits ({self.max_emergency_exits_per_day}) reached today")
            return False, "Daily emergency exit limit reached"
        
        try:
            # Gather all signals with error handling
            news_sentiment = self._safe_get_sentiment()
            fear_index, fear_class = self._safe_get_fear_greed()
            market_regime = self._safe_get_regime()
            btc_24h_change = self._safe_get_btc_change()
            
            # Count bear signals
            bear_signals = 0
            reasons = []
            
            # Signal 1: Extremely negative news
            if news_sentiment is not None and news_sentiment < self.SENTIMENT_THRESHOLD:
                bear_signals += 1
                reasons.append(f"Negative news sentiment ({news_sentiment:+.2f})")
            
            # Signal 2: Extreme fear
            if fear_index is not None and fear_index < self.FEAR_INDEX_THRESHOLD:
                bear_signals += 1
                reasons.append(f"Extreme fear ({fear_index}/100)")
            
            # Signal 3: Technical bear market
            if market_regime == "BEAR":
                bear_signals += 1
                reasons.append("Technical bear market confirmed")
            
            # Signal 4: BTC flash crash (double weight)
            if btc_24h_change is not None and btc_24h_change < self.BTC_DROP_THRESHOLD:
                bear_signals += 2
                reasons.append(f"BTC crash ({btc_24h_change:+.1f}%)")
            
            # Log current status
            logger.info(f"🔍 Emergency Check - Signals: {bear_signals}/{self.MIN_SIGNALS_REQUIRED} | "
                       f"Sentiment: {news_sentiment:+.2f if news_sentiment else 'N/A'} | "
                       f"Fear: {fear_index if fear_index else 'N/A'} | "
                       f"Regime: {market_regime} | BTC 24h: {btc_24h_change:+.1f}%" 
                       if btc_24h_change else "N/A")
            
            # Decision: Need minimum signals
            if bear_signals >= self.MIN_SIGNALS_REQUIRED:
                reason_str = " + ".join(reasons)
                return True, reason_str
            
            return False, "Market conditions acceptable"
        
        except Exception as e:
            logger.error(f"❌ Emergency check error: {e}")
            return False, f"Check failed: {e}"
    
    def _safe_get_sentiment(self) -> Optional[float]:
        """Get sentiment with error handling"""
        try:
            return self.bear_detector.get_market_sentiment()
        except Exception as e:
            logger.error(f"Failed to get sentiment: {e}")
            return None
    
    def _safe_get_fear_greed(self) -> Tuple[Optional[int], Optional[str]]:
        """Get fear/greed index with error handling"""
        try:
            return self.fear_greed.get_fear_greed_index()
        except Exception as e:
            logger.error(f"Failed to get fear/greed: {e}")
            return None, None
    
    def _safe_get_regime(self) -> str:
        """Get market regime with error handling"""
        try:
            btc_df = self.bot.get_market_data('BTC/USDT', '1h', limit=250)
            if btc_df is None or btc_df.empty:
                return "UNKNOWN"
            return self.regime_detector.detect_regime(btc_df)
        except Exception as e:
            logger.error(f"Failed to get regime: {e}")
            return "UNKNOWN"
    
    def _safe_get_btc_change(self) -> Optional[float]:
        """Get BTC 24h change with error handling"""
        try:
            btc_df = self.bot.get_market_data('BTC/USDT', '1h', limit=250)
            if btc_df is None or btc_df.empty or len(btc_df) < 24:
                return None
            return self._get_24h_change(btc_df)
        except Exception as e:
            logger.error(f"Failed to get BTC change: {e}")
            return None
    
    def execute_emergency_exit(self, reason: str):
        """
        EMERGENCY: Liquidate all positions with safeguards
        """
        
        logger.critical("\n" + "="*80)
        logger.critical("🚨 EMERGENCY EXIT TRIGGERED")
        logger.critical("="*80)
        logger.critical(f"Reason: {reason}")
        logger.critical(f"Emergency exits today: {self.emergency_exits_today + 1}/{self.max_emergency_exits_per_day}")
        logger.critical("Liquidating ALL positions NOW...")
        
        self.emergency_exit_active = True
        self.exit_timestamp = time.time()
        self.exit_reason = reason
        self.emergency_exits_today += 1
        
        positions = self.bot.get_open_positions()
        
        if not positions:
            logger.info("✅ No positions to close")
            return
        
        # Close all positions with tracking
        closed_count = 0
        failed_count = 0
        total_pnl = 0
        
        for position in positions:
            try:
                symbol = position['symbol']
                entry_price = position['entry_price']
                amount = position['amount']
                
                # Get current price
                current_price = self.bot.get_current_price(symbol)
                
                if not current_price or current_price <= 0:
                    logger.error(f"❌ Invalid price for {symbol}, using last known")
                    current_price = entry_price  # Failsafe
                
                # Calculate gross P&L
                gross_pnl = (current_price - entry_price) * amount
                pnl_pct = ((current_price - entry_price) / entry_price) * 100
                
                # Estimate fees
                position_value = current_price * amount
                exit_fee = position_value * self.config.TRADING_FEE
                net_pnl = gross_pnl - exit_fee
                
                total_pnl += net_pnl
                
                logger.warning(f"🚨 EMERGENCY SELL: {symbol} @ ${current_price:.2f} - "
                             f"P&L: ${net_pnl:+.2f} ({pnl_pct:+.2f}%)")
                
                # Execute market sell
                self.bot.close_position(
                    symbol=symbol,
                    reason="EMERGENCY_EXIT",
                    exit_price=current_price
                )
                
                closed_count += 1
            
            except Exception as e:
                logger.error(f"❌ Failed to close {symbol}: {e}")
                failed_count += 1
        
        # Summary
        logger.critical(f"✅ Emergency exit complete:")
        logger.critical(f"   Closed: {closed_count}/{len(positions)} positions")
        if failed_count > 0:
            logger.critical(f"   ⚠️ Failed: {failed_count} positions (MANUAL INTERVENTION REQUIRED!)")
        logger.critical(f"💰 Total Emergency P&L: ${total_pnl:+.2f} (after fees)")
        logger.critical(f"⏸️  Trading paused for 24 hours")
        logger.critical("="*80 + "\n")
        
        # Pause trading
        pause_hours = getattr(self.config, 'PAUSE_DURATION_HOURS', 24)
        self.bot.pause_trading(duration_hours=pause_hours)
    
    def check_resume_conditions(self) -> bool:
        """
        Check if conditions improved enough to resume trading
        """
        
        if not self.emergency_exit_active:
            return True
        
        # Must wait at least 12 hours
        min_wait_hours = getattr(self.config, 'MIN_EMERGENCY_WAIT_HOURS', 12)
        elapsed_hours = (time.time() - self.exit_timestamp) / 3600
        
        if elapsed_hours < min_wait_hours:
            logger.debug(f"⏸️  Still waiting: {elapsed_hours:.1f}/{min_wait_hours} hours")
            return False
        
        # Check if auto-resume enabled
        if not getattr(self.config, 'AUTO_RESUME_ENABLED', True):
            logger.info("⏸️  Auto-resume disabled - manual intervention required")
            return False
        
        try:
            # Re-check conditions
            news_sentiment = self._safe_get_sentiment()
            fear_index, _ = self._safe_get_fear_greed()
            market_regime = self._safe_get_regime()
            
            # Resume thresholds (more lenient than exit)
            resume_conditions = [
                news_sentiment is None or news_sentiment > -0.2,  # News improved
                fear_index is None or fear_index > 30,             # Fear reduced
                market_regime != "BEAR"                            # Not bear market
            ]
            
            resume = all(resume_conditions)
            
            if resume:
                logger.info("✅ Conditions improved - Resuming trading")
                logger.info(f"   Sentiment: {news_sentiment:+.2f if news_sentiment else 'N/A'}")
                logger.info(f"   Fear: {fear_index if fear_index else 'N/A'}")
                logger.info(f"   Regime: {market_regime}")
                
                self.emergency_exit_active = False
                self.exit_timestamp = None
                self.exit_reason = None
                return True
            
            logger.info(f"⏸️  Still in emergency mode ({elapsed_hours:.1f}h) - "
                       f"Sentiment: {news_sentiment:+.2f if news_sentiment else 'N/A'}, "
                       f"Fear: {fear_index if fear_index else 'N/A'}, "
                       f"Regime: {market_regime}")
            return False
        
        except Exception as e:
            logger.error(f"❌ Resume check error: {e}")
            return False
    
    def _get_24h_change(self, df) -> float:
        """Calculate 24h price change safely"""
        try:
            if df is None or df.empty or len(df) < 24:
                return 0.0
            
            price_now = float(df['close'].iloc[-1])
            price_24h_ago = float(df['close'].iloc[-24])
            
            if price_24h_ago <= 0:
                return 0.0
            
            return ((price_now - price_24h_ago) / price_24h_ago) * 100
        except Exception as e:
            logger.error(f"Error calculating 24h change: {e}")
            return 0.0
    
    def get_stats(self) -> dict:
        """Get emergency system statistics"""
        return {
            'emergency_active': self.emergency_exit_active,
            'exit_reason': self.exit_reason,
            'exits_today': self.emergency_exits_today,
            'max_exits_per_day': self.max_emergency_exits_per_day,
            'time_in_emergency': (time.time() - self.exit_timestamp) / 3600 
                                 if self.exit_timestamp else 0,
            'sentiment_threshold': self.SENTIMENT_THRESHOLD,
            'fear_threshold': self.FEAR_INDEX_THRESHOLD,
            'btc_drop_threshold': self.BTC_DROP_THRESHOLD
        }
    
    def force_resume(self):
        """Manually force resume (admin override)"""
        logger.warning("⚠️ MANUAL RESUME - Emergency mode overridden")
        self.emergency_exit_active = False
        self.exit_timestamp = None
        self.exit_reason = None
