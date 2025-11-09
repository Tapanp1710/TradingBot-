"""
Enhanced Trading Bot v6.5 - Complete Integration
Integrates all new features with existing bot structure
"""
import ccxt
import time
import logging
from datetime import datetime
import pandas as pd
import numpy as np

# Import your existing modules
from dynamic_config import DynamicConfig

# Import new enhancement modules
from short_position_manager import ShortPositionManager
from multi_timeframe_analyzer import MultiTimeframeAnalyzer
from contrarian_signal_generator import ContrarianSignalGenerator

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/bot_enhanced.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class EnhancedTradingBot:
    """
    Enhanced Trading Bot with all new features integrated
    """
    
    def __init__(self, starting_capital=1000):
        """Initialize bot with all components"""
        # Core config
        self.config = DynamicConfig(starting_capital=starting_capital)
        
        # Exchange connection
        self.exchange = self._init_exchange()
        
        # Enhancement modules
        self.short_manager = ShortPositionManager(self.config, self.exchange)
        self.mtf_analyzer = MultiTimeframeAnalyzer(self.exchange, self.config)
        self.contrarian = ContrarianSignalGenerator(self.config)
        
        # Position tracking
        self.positions = {}  # Your existing position dict
        
        # Performance tracking
        self.total_trades = 0
        self.winning_trades = 0
        
        logger.info("✅ Enhanced Trading Bot v6.5 initialized")
        self.config.print_summary()
    
    def _init_exchange(self):
        """Initialize exchange connection"""
        if self.config.PAPER_TRADING:
            logger.info("📝 PAPER TRADING MODE")
            exchange = ccxt.binance({
                'apiKey': self.config.API_KEY,
                'secret': self.config.API_SECRET,
                'enableRateLimit': True,
                'options': {'defaultType': 'future'}  # For margin/shorts
            })
        else:
            logger.info("💰 LIVE TRADING MODE")
            exchange = ccxt.binance({
                'apiKey': self.config.API_KEY,
                'secret': self.config.API_SECRET,
                'enableRateLimit': True,
                'options': {'defaultType': 'future'}
            })
        
        return exchange
    
    # ===================================================================
    # CORE CALCULATION FUNCTIONS (from your existing bot)
    # ===================================================================
    
    def calculate_atr(self, symbol, period=14):
        """
        Calculate Average True Range
        (Use your existing implementation or this one)
        """
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, '1h', limit=period+1)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            
            high = df['high']
            low = df['low']
            close = df['close']
            
            tr1 = high - low
            tr2 = abs(high - close.shift())
            tr3 = abs(low - close.shift())
            
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            atr = tr.rolling(window=period).mean().iloc[-1]
            
            atr_pct = atr / close.iloc[-1]
            return atr_pct
            
        except Exception as e:
            logger.error(f"❌ Error calculating ATR for {symbol}: {e}")
            return 0.015  # Fallback
    
    def calculate_rsi(self, symbol, period=14):
        """
        Calculate RSI
        (Use your existing implementation or this one)
        """
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, '1h', limit=period+1)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            return rsi.iloc[-1]
            
        except Exception as e:
            logger.error(f"❌ Error calculating RSI for {symbol}: {e}")
            return 50  # Neutral
    
    def calculate_macd(self, symbol):
        """
        Calculate MACD
        (Use your existing implementation or this one)
        """
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, '1h', limit=50)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            
            exp1 = df['close'].ewm(span=12, adjust=False).mean()
            exp2 = df['close'].ewm(span=26, adjust=False).mean()
            macd = exp1 - exp2
            signal = macd.ewm(span=9, adjust=False).mean()
            
            return macd.iloc[-1], signal.iloc[-1]
            
        except Exception as e:
            logger.error(f"❌ Error calculating MACD for {symbol}: {e}")
            return 0, 0
    
    def generate_signal(self, symbol):
        """
        Generate trading signal using your existing logic
        Returns: ('BUY'/'SELL'/'HOLD', confidence)
        """
        try:
            # Calculate indicators
            rsi = self.calculate_rsi(symbol)
            macd, signal_line = self.calculate_macd(symbol)
            
            # Basic signal logic (replace with your existing logic)
            if rsi < 35 and macd > signal_line:
                confidence = 0.65
                return 'BUY', confidence
            elif rsi > 65 and macd < signal_line:
                confidence = 0.65
                return 'SELL', confidence
            else:
                return 'HOLD', 0.40
                
        except Exception as e:
            logger.error(f"❌ Error generating signal for {symbol}: {e}")
            return 'HOLD', 0
    
    # ===================================================================
    # POSITION MANAGEMENT (from your existing bot)
    # ===================================================================
    
    def enter_long_position(self, symbol, confidence):
        """
        Enter long position (your existing logic + regime adjustments)
        """
        try:
            # Get regime-adjusted parameters
            regime_params = self.config.get_regime_adjusted_params()
            
            # Calculate position size
            position_size = self.config.CURRENT_CAPITAL * self.config.MAX_POSITION_PCT
            position_size *= regime_params['position_size_mult']  # NEW: Regime adjustment
            
            # Get current price
            ticker = self.exchange.fetch_ticker(symbol)
            current_price = ticker['last']
            
            # Calculate quantity
            quantity = position_size / current_price
            
            # Calculate ATR-based stops
            atr = self.calculate_atr(symbol)
            stop_loss = current_price * (1 - atr * regime_params['stop_loss_mult'])  # NEW: Regime-adjusted
            take_profit = current_price * (1 + atr * regime_params['take_profit_mult'])  # NEW: Regime-adjusted
            
            # Store position
            self.positions[symbol] = {
                'type': 'LONG',
                'entry_price': current_price,
                'quantity': quantity,
                'size': position_size,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'confidence': confidence,
                'entry_time': datetime.now(),
                'regime': self.config.get_market_regime()  # NEW: Track regime
            }
            
            # Execute order (paper or real)
            if self.config.PAPER_TRADING:
                logger.info(f"📈 PAPER LONG {symbol} @ ${current_price:.4f}")
                logger.info(f"   Size: {quantity:.4f} units (${position_size:.2f})")
                logger.info(f"   SL: ${stop_loss:.4f} | TP: ${take_profit:.4f}")
                logger.info(f"   Regime: {self.config.get_market_regime()}")
            else:
                order = self.exchange.create_market_buy_order(symbol, quantity)
                logger.info(f"✅ REAL LONG {symbol}")
            
            # Record in config
            self.config.record_trade_executed()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error entering long {symbol}: {e}")
            return False
    
    def monitor_positions(self):
        """
        Monitor open positions for TP/SL
        (Integrate with your existing position monitoring)
        """
        for symbol, position in list(self.positions.items()):
            try:
                ticker = self.exchange.fetch_ticker(symbol)
                current_price = ticker['last']
                
                entry = position['entry_price']
                pnl_pct = ((current_price - entry) / entry) * 100
                
                # Check stop-loss
                if current_price <= position['stop_loss']:
                    logger.info(f"🛑 STOP-LOSS {symbol} @ ${current_price:.4f}")
                    self.close_position(symbol, current_price, 'STOP_LOSS')
                
                # Check take-profit
                elif current_price >= position['take_profit']:
                    logger.info(f"💰 TAKE-PROFIT {symbol} @ ${current_price:.4f}")
                    self.close_position(symbol, current_price, 'TAKE_PROFIT')
                
            except Exception as e:
                logger.error(f"❌ Error monitoring {symbol}: {e}")
    
    def close_position(self, symbol, exit_price, reason):
        """
        Close position and update stats
        """
        position = self.positions.pop(symbol, None)
        if not position:
            return
        
        entry = position['entry_price']
        pnl_pct = ((exit_price - entry) / entry) * 100
        pnl_usd = position['size'] * (pnl_pct / 100)
        
        # Update stats
        self.total_trades += 1
        if pnl_usd > 0:
            self.winning_trades += 1
        
        # Update capital
        self.config.update_capital(self.config.CURRENT_CAPITAL + pnl_usd)
        
        logger.info(f"   Entry: ${entry:.4f} → Exit: ${exit_price:.4f}")
        logger.info(f"   P&L: ${pnl_usd:+.2f} ({pnl_pct:+.2f}%)")
        logger.info(f"   Win Rate: {self.get_win_rate():.1f}%")
    
    def get_win_rate(self):
        """Calculate win rate"""
        if self.total_trades == 0:
            return 0
        return (self.winning_trades / self.total_trades) * 100
    
    # ===================================================================
    # MAIN TRADING LOOP (with all new features)
    # ===================================================================
    
    def run(self):
        """
        Main trading loop with all enhancements integrated
        """
        logger.info("🚀 Starting enhanced trading bot...")
        
        scan_count = 0
        
        while True:
            try:
                scan_count += 1
                logger.info(f"\n{'='*70}")
                logger.info(f"🔍 SCAN #{scan_count} | Positions: {len(self.positions)}/{self.config.MAX_OPEN_POSITIONS}")
                logger.info(f"{'='*70}")
                
                # === 1. UPDATE MARKET REGIME ===
                for symbol in self.config.WATCHLIST[:5]:  # Sample for regime
                    atr = self.calculate_atr(symbol)
                    self.config.update_atr_history(symbol, atr)
                
                regime_params = self.config.get_regime_adjusted_params()
                logger.info(f"📊 Regime: {self.config.get_market_regime()} | SL: {regime_params['stop_loss_mult']:.1f}x | TP: {regime_params['take_profit_mult']:.1f}x")
                
                # === 2. MONITOR EXISTING POSITIONS ===
                if self.positions:
                    logger.info(f"👀 Monitoring {len(self.positions)} positions...")
                    self.monitor_positions()
                    
                    # NEW: Monitor short positions
                    closed_shorts = self.short_manager.monitor_short_positions()
                    for trade in closed_shorts:
                        logger.info(f"📉 Short closed: {trade['symbol']} | P&L: ${trade['pnl']:+.2f}")
                        self.config.update_capital(self.config.CURRENT_CAPITAL + trade['pnl'])
                        self.total_trades += 1
                        if trade['pnl'] > 0:
                            self.winning_trades += 1
                
                # === 3. SCAN FOR NEW OPPORTUNITIES ===
                if len(self.positions) < self.config.MAX_OPEN_POSITIONS:
                    logger.info(f"🔎 Scanning for opportunities ({self.config.MAX_OPEN_POSITIONS - len(self.positions)} slots available)...")
                    
                    # Get adjusted threshold (idle rebalancing)
                    threshold = self.config.get_adjusted_threshold_for_idle()
                    
                    scan_results = []
                    
                    for symbol in self.config.WATCHLIST:
                        # === NEW: Multi-timeframe analysis ===
                        if self.config.ENABLE_MULTI_TIMEFRAME:
                            mtf_result = self.mtf_analyzer.get_multi_timeframe_signal(symbol)
                            
                            if mtf_result['alignment'] in ['PERFECT', 'STRONG']:
                                final_confidence = mtf_result['confidence'] + mtf_result['confidence_boost']
                                logger.info(f"✅ {symbol}: {mtf_result['signal']} ({final_confidence:.1%}) - {mtf_result['alignment']} alignment")
                                
                                scan_results.append({
                                    'symbol': symbol,
                                    'signal': mtf_result['signal'],
                                    'confidence': final_confidence
                                })
                        else:
                            # Use single-timeframe (your existing method)
                            signal, confidence = self.generate_signal(symbol)
                            if signal != 'HOLD':
                                scan_results.append({
                                    'symbol': symbol,
                                    'signal': signal,
                                    'confidence': confidence
                                })
                    
                    # === NEW: Track signals for contrarian ===
                    self.contrarian.track_signals(scan_results)
                    
                    # === NEW: Check for contrarian opportunities ===
                    contrarian_opp = self.contrarian.detect_extreme_bearish_sentiment()
                    if contrarian_opp:
                        logger.info(f"🔄 CONTRARIAN OPPORTUNITY: {contrarian_opp['symbol']}")
                        logger.info(f"   Reason: {contrarian_opp['reason']}")
                        logger.info(f"   Risk: {contrarian_opp['risk_level']}")
                        
                        # Add to scan results with smaller size
                        scan_results.append({
                            'symbol': contrarian_opp['symbol'],
                            'signal': contrarian_opp['contrarian_signal'],
                            'confidence': contrarian_opp['confidence'],
                            'contrarian': True,
                            'size_mult': contrarian_opp['position_size_mult']
                        })
                    
                    # === 4. PROCESS SIGNALS ===
                    for result in scan_results:
                        # Skip if already in position
                        if result['symbol'] in self.positions:
                            continue
                        
                        # BUY signal (long)
                        if result['signal'] == 'BUY' and result['confidence'] > threshold:
                            logger.info(f"🟢 BUY signal: {result['symbol']} @ {result['confidence']:.1%}")
                            
                            # Track signal
                            self.config.track_buy_signal(result['confidence'], result['symbol'])
                            
                            # Enter position
                            self.enter_long_position(result['symbol'], result['confidence'])
                            break  # One at a time
                        
                        # === NEW: SELL signal (short) ===
                        elif result['signal'] == 'SELL' and result['confidence'] > self.config.SHORT_CONFIDENCE_THRESHOLD:
                            if self.config.ENABLE_SHORT_SELLING:
                                logger.info(f"🔴 SHORT signal: {result['symbol']} @ {result['confidence']:.1%}")
                                
                                current_price = self.exchange.fetch_ticker(result['symbol'])['last']
                                atr = self.calculate_atr(result['symbol'])
                                
                                self.short_manager.open_short_position(
                                    result['symbol'],
                                    current_price,
                                    result['confidence'],
                                    atr
                                )
                                self.config.record_trade_executed()
                                break
                    
                    # === 5. INCREMENT NO-SIGNAL COUNTER ===
                    if not scan_results:
                        self.config.increment_scans_without_signal()
                        logger.info("❌ No opportunities found")
                    
                    # === NEW: Force deployment if idle ===
                    if self.config.should_force_deployment():
                        logger.info("⚡ FORCE DEPLOYMENT TRIGGERED")
                        # Lower standards and try again
                        # (Implement your force deployment logic)
                
                else:
                    logger.info("⏸️ Max positions reached, skipping new trades")
                
                # === 6. HEARTBEAT ===
                if scan_count % 25 == 0:  # Every ~10 minutes
                    logger.info(f"\n💓 HEARTBEAT")
                    logger.info(f"Capital: ${self.config.CURRENT_CAPITAL:.2f}")
                    logger.info(f"Trades: {self.total_trades} | Win Rate: {self.get_win_rate():.1f}%")
                    logger.info(f"Regime: {self.config.get_market_regime()}")
                    logger.info(f"Idle: {self.config.get_hours_since_last_trade():.1f}h")
                
                # Sleep
                time.sleep(self.config.SCAN_INTERVAL)
                
            except KeyboardInterrupt:
                logger.info("\n🛑 Shutdown signal received")
                break
            except Exception as e:
                logger.error(f"❌ Error in main loop: {e}", exc_info=True)
                time.sleep(30)  # Wait before retry
        
        logger.info("👋 Bot stopped")


# ===================================================================
# MAIN ENTRY POINT
# ===================================================================

if __name__ == "__main__":
    # Initialize bot
    bot = EnhancedTradingBot(starting_capital=1000)
    
    # Run
    try:
        bot.run()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
