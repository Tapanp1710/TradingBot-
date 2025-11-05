"""
Dynamic Trading Bot Configuration v6.3 - FULLY ADAPTIVE (FIXED)
November 4, 2025 - Correct tier boundaries
ALL parameters scale properly with $1000 = MEDIUM tier
"""
import os
from datetime import datetime


class DynamicConfig:
    """
    Configuration that adapts to capital changes in real-time
    Drop-in replacement for static Config class with backward compatibility
    """
    
    def __init__(self, starting_capital=None):
        """Initialize with starting capital"""
        self._starting_capital = starting_capital or float(os.getenv('STARTING_CAPITAL', '1000'))
        self._current_capital = self._starting_capital
        self._last_update = datetime.now()
        
        # Static values (don't change with capital)
        self.BOT_VERSION = "6.3.0"
        self.CONFIG_VERSION = "6.3-DYNAMIC-FIXED"
        self.EXCHANGE = "binance"
        self.API_KEY = os.getenv('EXCHANGE_API_KEY', '')
        self.API_SECRET = os.getenv('EXCHANGE_API_SECRET', '')
        self.PAPER_TRADING = os.getenv('PAPER_TRADING', 'True').lower() == 'true'
        
        # Initialize all dynamic parameters
        self._update_all_params()
    
    
    # ===================================================================
    # CAPITAL UPDATE METHOD
    # ===================================================================
    
    def update_capital(self, new_capital):
        """
        Call this after every trade or daily to recalculate all parameters
        Args:
            new_capital: Current portfolio value
        """
        old_tier = self._get_tier(self._current_capital)
        old_positions = self.MAX_OPEN_POSITIONS
        
        self._current_capital = new_capital
        new_tier = self._get_tier(new_capital)
        
        self._update_all_params()
        self._last_update = datetime.now()
        
        # Notify on tier or position changes
        if old_tier != new_tier:
            print(f"\n{'='*70}")
            print(f"CAPITAL TIER CHANGED: {old_tier.upper()} -> {new_tier.upper()}")
            print(f"{'='*70}")
            print(f"New Capital: ${new_capital:.2f}")
            print(f"Positions: {old_positions} -> {self.MAX_OPEN_POSITIONS}")
            print(f"Position Size: {self.MAX_POSITION_PCT*100:.1f}%")
            print(f"Stop Loss: {self.MAX_SL_PCT*100:.2f}%")
            print(f"Confidence Threshold: {self.SIGNAL_CONFIDENCE_THRESHOLD*100:.0f}%")
            print(f"{'='*70}\n")
    
    
    # ===================================================================
    # TIER & CALCULATION HELPERS (FIXED BOUNDARIES)
    # ===================================================================
    
    def _get_tier(self, cap):
        """Get capital tier - FIXED boundaries"""
        if cap < 250: return 'micro'
        elif cap < 500: return 'small'
        elif cap <= 1000: return 'medium'  # ← FIXED: $1000 = MEDIUM
        elif cap < 3000: return 'large'
        else: return 'whale'
    
    def _calc_positions(self, cap):
        """FIXED: Proper position counts"""
        if cap < 200: return 2
        elif cap < 400: return 2  # Changed from 3
        elif cap < 600: return 3
        elif cap <= 1000: return 3  # ← FIXED: $1000 = 3 positions
        elif cap < 2000: return 4  # Changed from 5
        elif cap < 3500: return 5  # Changed from 6
        elif cap < 7000: return 6  # Changed from 8
        else: return 8  # Changed from 10
    
    def _calc_position_pct(self, cap, pos):
        """INCREASED: Larger positions for better profit potential"""
        base = 0.90 / pos
        return min(base * 1.2, 0.50)
    
    def _calc_min_pos(self, cap, pos):
        avg = (cap * 0.90) / pos
        return max(40, int(avg * 0.45))
    
    def _calc_risk(self, cap):
        """INCREASED: Allow more risk per trade for profit"""
        if cap < 500: return 0.030
        elif cap < 2000: return 0.025
        elif cap < 5000: return 0.022
        else: return 0.020
    
    def _calc_drawdown(self, cap):
        if cap < 500: return 0.20
        elif cap <= 1000: return 0.17
        elif cap < 2000: return 0.15
        elif cap < 5000: return 0.13
        else: return 0.10
    
    def _calc_atr(self, cap):
        if cap < 300: return 0.0010
        elif cap < 500: return 0.0012
        elif cap <= 1000: return 0.0015
        elif cap < 5000: return 0.0020
        else: return 0.0025
    
    def _calc_sl_mult(self, cap):
        """INCREASED: Wider stops to avoid premature exits"""
        if cap < 300: return 1.5
        elif cap < 500: return 1.6
        elif cap <= 1000: return 1.7
        elif cap < 5000: return 1.8
        else: return 2.0
    
    def _calc_sl_pct(self, cap):
        """INCREASED: Wider percentage stops"""
        if cap < 300: return 0.035  # Changed from 0.025
        elif cap < 500: return 0.030  # Changed from 0.023
        elif cap <= 1000: return 0.025  # Changed from 0.020
        elif cap < 5000: return 0.022  # Changed from 0.018
        else: return 0.020  # Changed from 0.015
    
    def _calc_tp_mult(self, cap):
        """NEW: Separate TP calculation - LOWER for realistic targets"""
        if cap < 300: return 1.2
        elif cap < 500: return 1.3
        elif cap <= 1000: return 1.3
        elif cap < 5000: return 1.5
        else: return 1.9
    
    def _calc_trail(self, cap):
        """ADJUSTED: Better trailing activation"""
        if cap < 300: return 1.0
        elif cap < 500: return 1.1
        elif cap <= 1000: return 1.3
        elif cap < 5000: return 1.5
        else: return 1.8
    
    def _calc_daily_loss(self, cap):
        if cap < 300: return 0.050
        elif cap < 500: return 0.045
        elif cap <= 1000: return 0.040
        elif cap < 2000: return 0.035
        elif cap < 5000: return 0.030
        else: return 0.025
    
    def _calc_confidence(self, cap):
        """LOWERED: More selective entries for quality"""
        if cap < 300: return 0.50
        elif cap < 500: return 0.52
        elif cap <= 1000: return 0.595
        elif cap < 2000: return 0.57
        elif cap < 5000: return 0.58
        else: return 0.60
    
    def _calc_quality(self, cap):
        """INCREASED: Higher quality signals only"""
        if cap < 300: return 40
        elif cap < 500: return 45
        elif cap <= 1000: return 50
        elif cap < 2000: return 55
        elif cap < 5000: return 60
        else: return 65
    
    def _calc_rsi(self, cap):
        if cap < 300: return 38
        elif cap < 500: return 36
        elif cap <= 1000: return 35
        elif cap < 5000: return 33
        else: return 30
    
    def _calc_losses(self, cap):
        """REDUCED: Faster cooldown after losses"""
        if cap < 500: return 2
        elif cap <= 1000: return 3
        elif cap < 2000: return 4
        else: return 5
    
    def _calc_cooldown(self, cap):
        if cap < 300: return 0.5
        elif cap < 500: return 0.75
        elif cap <= 1000: return 1.0
        elif cap < 5000: return 1.5
        else: return 2.0
    
    def _calc_winrate(self, cap):
        """LOWERED: More realistic minimum win rate"""
        if cap < 300: return 0.25
        elif cap < 500: return 0.28
        elif cap <= 1000: return 0.30
        elif cap < 5000: return 0.33
        else: return 0.35
    
    def _calc_emergency(self, cap):
        if cap < 300: return 0.15
        elif cap < 500: return 0.14
        elif cap <= 1000: return 0.12
        elif cap < 5000: return 0.10
        else: return 0.08
    
    def _calc_pause(self, cap):
        if cap < 300: return 1
        elif cap < 500: return 2
        elif cap <= 1000: return 3
        elif cap < 5000: return 4
        else: return 6
    
    def _calc_slippage(self, cap):
        if cap < 300: return 0.0008
        elif cap < 500: return 0.0007
        elif cap <= 1000: return 0.0006
        elif cap < 5000: return 0.0004
        else: return 0.0003
    
    def _calc_scan_offset(self, cap):
        if cap < 300: return 8
        elif cap < 500: return 10
        elif cap <= 1000: return 12
        elif cap < 5000: return 15
        else: return 20
    
    def _calc_scan_int(self, cap):
        if cap < 300: return 15
        elif cap < 500: return 18
        elif cap <= 1000: return 20
        elif cap < 5000: return 25
        else: return 30
    
    def _calc_multipliers(self, cap):
        """ADJUSTED: Better position sizing multipliers"""
        if cap < 500: return 1.25, 0.75
        elif cap <= 1000: return 1.20, 0.80
        elif cap < 5000: return 1.15, 0.85
        else: return 1.10, 0.90
    
    def _calc_grade(self, cap):
        if cap < 250: return 'D'
        elif cap <= 1000: return 'C'
        elif cap < 5000: return 'B'
        else: return 'A'
    
    def _calc_ml_trades(self, cap):
        if cap < 500: return 4
        elif cap <= 1000: return 6
        elif cap < 5000: return 8
        else: return 10
    
    
    # ===================================================================
    # UPDATE ALL PARAMETERS (COMPLETE v6.2 CONFIG)
    # ===================================================================
    
    def _update_all_params(self):
        """Recalculate ALL parameters based on current capital"""
        cap = self._current_capital
        
        # Core capital tracking
        self.CURRENT_CAPITAL = cap
        self.STARTING_CAPITAL = self._starting_capital
        self.INITIAL_CAPITAL = self._starting_capital
        self.CAPITAL_TIER = self._get_tier(cap)
        
        # ===================================================================
        # POSITION SIZING
        # ===================================================================
        self.MAX_OPEN_POSITIONS = self._calc_positions(cap)
        self.MAX_POSITION_PCT = self._calc_position_pct(cap, self.MAX_OPEN_POSITIONS)
        self.MIN_POSITION_USD = self._calc_min_pos(cap, self.MAX_OPEN_POSITIONS)
        self.MIN_CAPITAL_USD = int(cap * 0.20)
        
        # ===================================================================
        # RISK PARAMETERS
        # ===================================================================
        self.MAX_RISK_PER_TRADE = self._calc_risk(cap)
        self.MAX_PORTFOLIO_RISK = min(self.MAX_OPEN_POSITIONS * self.MAX_RISK_PER_TRADE * 1.2, 0.20)
        self.MAX_POSITION_PCT_BEAR = self.MAX_POSITION_PCT * 0.6
        self.MAX_POSITION_PCT_NEUTRAL = self.MAX_POSITION_PCT * 0.8
        self.MAX_DRAWDOWN_PCT = self._calc_drawdown(cap)
        
        # Kelly & Risk Management
        self.USE_KELLY_CRITERION = cap > 2000
        self.KELLY_FRACTION = 0.25
        self.ENABLE_CORRELATION_FILTER = cap > 1000
        self.MAX_CORRELATED_POSITIONS = 5 if cap > 2000 else 3
        self.CORRELATION_THRESHOLD = 0.80
        self.ENABLE_VOLATILITY_ADJUSTMENT = cap > 3000
        
        # ===================================================================
        # MULTI-EXCHANGE
        # ===================================================================
        self.ENABLE_MULTI_EXCHANGE = cap > 5000
        self.EXCHANGES_LIST = [(self.EXCHANGE, self.API_KEY, self.API_SECRET)]
        self.MIN_ARBITRAGE_PROFIT = 0.005
        
        # ===================================================================
        # POSITION MANAGEMENT
        # ===================================================================
        self.MAX_POSITION_HOURS = 36
        self.STALE_BAND_ATR_MULT = 2.0
        self.MIN_ATR_PCT = self._calc_atr(cap)
        self.NEUTRAL_REGIME_MIN_ATR_PCT = self.MIN_ATR_PCT * 1.3
        self.NEUTRAL_REGIME_CONFIDENCE_ADJUST = -0.05
        self.ENABLE_DYNAMIC_CAPACITY = True
        
        # ===================================================================
        # MARKET FILTER
        # ===================================================================
        self.ENABLE_MARKET_FILTER = cap > 2000
        self.MARKET_FILTER_ENABLED = self.ENABLE_MARKET_FILTER
        self.MIN_FEAR_GREED_INDEX = 15
        self.MAX_FEAR_GREED_INDEX = 85
        self.MIN_BTC_VOLATILITY = 0.3
        self.AUTO_PAUSE_ON_BEAR_MARKET = cap > 1000
        self.BEAR_DETECTION_THRESHOLD = -0.25
        
        # ===================================================================
        # STOP LOSS & TAKE PROFIT
        # ===================================================================
        self.USE_ATR_EXITS = True
        self.ATR_PERIOD = 14
        self.ATR_SL_MULT = self._calc_sl_mult(cap)
        self.ATR_TP_MULT = self._calc_tp_mult(cap)
        self.MAX_SL_PCT = self._calc_sl_pct(cap)
        self.MAX_TP_PCT = self.MAX_SL_PCT * self.ATR_TP_MULT
        self.FALLBACK_STOP_LOSS_PCT = self.MAX_SL_PCT * 0.8
        self.FALLBACK_TAKE_PROFIT_PCT = self.MAX_SL_PCT * 2.0
        
        # ===================================================================
        # TRAILING STOPS
        # ===================================================================
        self.ENABLE_ATR_TRAILING = True
        self.TRAIL_ACTIVATE_ATR_MULT = self._calc_trail(cap)
        self.TRAIL_DISTANCE_ATR_MULT = 0.6
        
        # ===================================================================
        # PARTIAL TAKE PROFIT
        # ===================================================================
        self.ENABLE_PARTIAL_TP = True
        self.PARTIAL_TP_PCT = 0.50
        self.PARTIAL_TP_TRIGGER_ATR_MULT = 1.2
        
        # ===================================================================
        # DAILY LOSS PROTECTION
        # ===================================================================
        self.ENABLE_DAILY_LOSS_CAP = True
        self.MAX_DAILY_LOSS_PCT = self._calc_daily_loss(cap)
        self.MAX_DAILY_LOSS_AMOUNT = int(cap * self.MAX_DAILY_LOSS_PCT)
        
        # ===================================================================
        # MULTI-TIMEFRAME
        # ===================================================================
        self.ENABLE_MULTI_TIMEFRAME = cap > 3000
        self.TIMEFRAMES = ['1h', '4h'] if self.ENABLE_MULTI_TIMEFRAME else ['1h']
        self.TIMEFRAME_WEIGHTS = [0.6, 0.4] if self.ENABLE_MULTI_TIMEFRAME else [1.0]
        
        # ===================================================================
        # SIGNAL SETTINGS
        # ===================================================================
        self.SIGNAL_CONFIDENCE_THRESHOLD = self._calc_confidence(cap)
        self.HIGH_CONFIDENCE_THRESHOLD = self.SIGNAL_CONFIDENCE_THRESHOLD + 0.15
        self.LOW_CONFIDENCE_THRESHOLD = self.SIGNAL_CONFIDENCE_THRESHOLD - 0.05
        self.MIN_QUALITY_SCORE = self._calc_quality(cap)
        
        # RSI
        self.RSI_PERIOD = 14
        self.RSI_OVERSOLD = self._calc_rsi(cap)
        self.RSI_OVERBOUGHT = 100 - self.RSI_OVERSOLD
        
        # MACD
        self.MACD_FAST = 12
        self.MACD_SLOW = 26
        self.MACD_SIGNAL = 9
        
        # Bollinger Bands
        self.BB_PERIOD = 20
        self.BB_STD = 2
        
        # ===================================================================
        # LOSS STREAK DETECTION
        # ===================================================================
        self.ENABLE_STREAK_DETECTION = True
        self.MAX_CONSECUTIVE_LOSSES = self._calc_losses(cap)
        self.COOLDOWN_AFTER_LOSSES_HOURS = self._calc_cooldown(cap)
        self.PREVENT_REVENGE_TRADING = True
        self.REVENGE_TRADE_COOLDOWN_MINS = int(self.COOLDOWN_AFTER_LOSSES_HOURS * 30)
        self.CONSECUTIVE_LOSS_LIMIT = self.MAX_CONSECUTIVE_LOSSES
        self.MIN_WIN_RATE_TO_TRADE = self._calc_winrate(cap)
        
        # ===================================================================
        # EMERGENCY EXIT
        # ===================================================================
        self.EMERGENCY_EXIT_ENABLED = True
        self.EMERGENCY_LOSS_PCT = self._calc_emergency(cap)
        self.EMERGENCY_CLOSE_ALL = True
        self.EMERGENCY_CHECK_INTERVAL = 300
        self.BEAR_SENTIMENT_THRESHOLD = -0.35
        self.BEAR_FEAR_INDEX = 20
        self.BEAR_BTC_DROP = -12
        self.MIN_BEAR_SIGNALS = 2
        self.PAUSE_DURATION_HOURS = self._calc_pause(cap)
        self.MIN_EMERGENCY_WAIT_HOURS = self.PAUSE_DURATION_HOURS * 3
        self.AUTO_RESUME_ENABLED = True
        
        # ===================================================================
        # FEES & SLIPPAGE
        # ===================================================================
        self.TRADING_FEE = 0.001
        self.INCLUDE_SLIPPAGE = True
        self.SLIPPAGE_RATE = self._calc_slippage(cap)
        self.APPLY_INDIAN_TAX = True
        self.CAPITAL_GAINS_TAX = 0.30
        self.TDS_RATE = 0.01
        
        # ===================================================================
        # WATCHLISTS
        # ===================================================================
        self.USE_ROTATING_WATCHLISTS = True
        self.WATCHLIST_BEAR = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT']
        
        self.WATCHLIST_CORE = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'SOL/USDT', 'XRP/USDT', 'ADA/USDT']
        self.WATCHLIST_EXTENDED = ['AVAX/USDT', 'MATIC/USDT', 'DOT/USDT', 'LINK/USDT', 'ATOM/USDT', 'UNI/USDT', 'ARB/USDT', 'OP/USDT']
        self.WATCHLIST_AGGRESSIVE = ['LTC/USDT', 'DOGE/USDT', 'INJ/USDT', 'SUI/USDT', 'FET/USDT', 'NEAR/USDT', 'TIA/USDT']
        
        # Build watchlist based on tier
        tier = self._get_tier(cap)
        if tier == 'micro':
            self.WATCHLIST_A, self.WATCHLIST_B, self.WATCHLIST_C = self.WATCHLIST_CORE[:4], self.WATCHLIST_EXTENDED[:4], []
        elif tier == 'small':
            self.WATCHLIST_A, self.WATCHLIST_B, self.WATCHLIST_C = self.WATCHLIST_CORE, self.WATCHLIST_EXTENDED[:6], []
        elif tier == 'medium':
            self.WATCHLIST_A, self.WATCHLIST_B, self.WATCHLIST_C = self.WATCHLIST_CORE, self.WATCHLIST_EXTENDED, self.WATCHLIST_AGGRESSIVE[:3]
        else:
            self.WATCHLIST_A, self.WATCHLIST_B, self.WATCHLIST_C = self.WATCHLIST_CORE, self.WATCHLIST_EXTENDED, self.WATCHLIST_AGGRESSIVE
        
        self.WATCHLIST = self.WATCHLIST_A + self.WATCHLIST_B + self.WATCHLIST_C
        self.GROUP_SCAN_OFFSET = self._calc_scan_offset(cap)
        
        # ===================================================================
        # ML & ONLINE LEARNING
        # ===================================================================
        self.ENABLE_ONLINE_LEARNING = cap > 2000
        self.ML_ENABLED = cap > 500
        self.ML_MODEL_TO_USE = 'ensemble' if cap > 1000 else 'random_forest'
        self.ML_CONFIDENCE_THRESHOLD = self.SIGNAL_CONFIDENCE_THRESHOLD
        self.ML_SIGNAL_WEIGHT = 0.35 if self.ML_ENABLED else 0.0
        self.BEARISH_CONFIDENCE_BOOST = 0.10
        
        self.ENABLE_ENSEMBLE_ML = cap > 1000
        self.ENSEMBLE_MODELS = ['random_forest', 'lightgbm', 'xgboost'] if self.ENABLE_ENSEMBLE_ML else ['random_forest']
        self.ENSEMBLE_WEIGHTS = {'rf': 0.35, 'lgb': 0.35, 'xgb': 0.30}
        
        self.ONLINE_LEARNING_METHOD = 'sgd'
        self.UPDATE_MODEL_PER_TRADE = True
        self.MIN_TRADES_BEFORE_UPDATE = self._calc_ml_trades(cap)
        self.BATCH_UPDATE_SIZE = self.MIN_TRADES_BEFORE_UPDATE * 2
        self.ONLINE_LEARNING_RATE = 0.01
        self.MOMENTUM = 0.9
        self.DECAY_RATE = 0.95
        self.SAVE_MODEL_AFTER_UPDATES = 50
        self.ONLINE_MODEL_PATH = 'ml/models/online_model.pkl'
        self.MAX_PERFORMANCE_DROP = 0.15
        self.ENABLE_MODEL_ROLLBACK = True
        self.VALIDATION_WINDOW = 20
        self.ML_RETRAIN_INTERVAL = 100
        self.ML_MIN_SAMPLES = 50
        self.ML_FEATURE_SET = 'enhanced' if cap > 2000 else 'basic'
        self.USE_FEATURE_ENGINEERING = cap > 1000
        
        # ===================================================================
        # SENTIMENT ANALYSIS
        # ===================================================================
        self.ENABLE_SENTIMENT_ANALYSIS = cap > 3000
        self.SENTIMENT_WEIGHT = 0.10 if self.ENABLE_SENTIMENT_ANALYSIS else 0.0
        self.SENTIMENT_CACHE_DURATION = 600
        self.SENTIMENT_SOURCES = ['fear_greed']
        self.SENTIMENT_BULLISH_THRESHOLD = 0.3
        self.SENTIMENT_BEARISH_THRESHOLD = -0.3
        self.SENTIMENT_ANOMALY_THRESHOLD = 5.0
        
        # ===================================================================
        # ADVANCED FEATURES
        # ===================================================================
        self.ENABLE_ADAPTIVE_SIZING = True
        _high, _low = self._calc_multipliers(cap)
        self.HIGH_CONFIDENCE_MULTIPLIER = _high
        self.LOW_CONFIDENCE_MULTIPLIER = _low
        
        self.ENABLE_ARBITRAGE = cap > 5000
        self.MAX_ARBITRAGE_CAPITAL = 0.15
        self.MIN_ARBITRAGE_VOLUME = 50000
        self.ENABLE_QUALITY_FILTER = cap > 1000
        self.MIN_SIGNAL_QUALITY_GRADE = self._calc_grade(cap)
        
        # ===================================================================
        # TIMING
        # ===================================================================
        self.SCAN_INTERVAL = self._calc_scan_int(cap)
        self.ENABLE_TIME_FILTERS = False
        self.TRADING_START_HOUR = 0
        self.TRADING_END_HOUR = 24
        self.ENABLE_OPPORTUNISTIC_SCAN = cap > 1000
        self.OPPORTUNISTIC_SCAN_INTERVAL = 180
        self.TOP_MOVER_THRESHOLD = 0.025
        self.ARBITRAGE_INTERVAL = 60
        
        # ===================================================================
        # LOGGING
        # ===================================================================
        self.LOG_LEVEL = "INFO"
        self.LOG_FILE = "logs/bot.log"
        self.SAVE_TRADE_HISTORY = True
        self.TRADE_HISTORY_FILE = "trade_history.csv"
        self.PERFORMANCE_FILE = "data/performance.csv"
        self.BACKTEST_RESULTS_FILE = "data/backtest_results.csv"
        self.LOG_SIGNAL_DETAILS = cap < 1000
        self.LOG_SENTIMENT_SCORES = False
        self.LOG_ML_PREDICTIONS = self.ML_ENABLED
        
        # ===================================================================
        # MONITORING
        # ===================================================================
        self.ENABLE_HEARTBEAT = True
        self.HEARTBEAT_INTERVAL = 600
        self.ENABLE_PERFORMANCE_MONITOR = True
        self.PERFORMANCE_LOG_INTERVAL = 3600
        self.MAX_DRAWDOWN_ALERT = self.MAX_DRAWDOWN_PCT * 0.8
        self.MIN_WIN_RATE_ALERT = self.MIN_WIN_RATE_TO_TRADE
        self.IDLE_CAPACITY_ALERT_SCANS = 150
        self.FLAT_PNL_ALERT_SCANS = 75
        self.MIN_CAPACITY_UTILIZATION = 0.25
        self.AUTO_PAUSE_ON_DRAWDOWN = self.MAX_DRAWDOWN_PCT
        self.AUTO_PAUSE_ON_LOSSES = self.MAX_CONSECUTIVE_LOSSES + 2
        
        # ===================================================================
        # SYSTEM
        # ===================================================================
        self.ENABLE_MEMORY_MANAGEMENT = True
        self.GC_INTERVAL = 100
        self.MAX_MEMORY_MB = 500
        self.MAX_SCANS_PER_CYCLE = 100
        self.RATE_LIMIT_DELAY = 0.05 if cap < 500 else 0.1
        self.ENABLE_GARBAGE_COLLECTION = True
        self.GC_COLLECTION_INTERVAL = 100
        self.RATE_LIMIT_SLEEP = 0.3 if cap < 500 else 0.5
        self.MAX_API_RETRIES = 3
        self.API_RETRY_DELAY = 2
        self.LOG_MAX_BYTES = 10 * 1024 * 1024
        self.LOG_BACKUP_COUNT = 5
        
        # ===================================================================
        # NOTIFICATIONS
        # ===================================================================
        self.ENABLE_TELEGRAM_ALERTS = False
        self.TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
        self.TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')
        self.ALERT_ON_TRADES = True
        self.ALERT_ON_ERRORS = True
        self.ALERT_ON_DAILY_PNL = True
        self.ALERT_ON_SENTIMENT_ANOMALY = False
        self.ALERT_ON_QUALITY_FILTER = False
        
        # ===================================================================
        # DEBUG
        # ===================================================================
        self.DEBUG_MODE = False
        self.VERBOSE_LOGGING = cap < 500
        self.SAVE_PREDICTIONS = True
        self.FAST_MODE = False
        self.DRY_RUN = False
        
        # ===================================================================
        # FEATURE FLAGS
        # ===================================================================
        self.FEATURES = {
            'multi_exchange': self.ENABLE_MULTI_EXCHANGE,
            'multi_timeframe': self.ENABLE_MULTI_TIMEFRAME,
            'sentiment_analysis': self.ENABLE_SENTIMENT_ANALYSIS,
            'ensemble_ml': self.ENABLE_ENSEMBLE_ML,
            'correlation_filter': self.ENABLE_CORRELATION_FILTER,
            'volatility_adjustment': self.ENABLE_VOLATILITY_ADJUSTMENT,
            'quality_filter': self.ENABLE_QUALITY_FILTER,
            'adaptive_sizing': True,
        }
        
        # ===================================================================
        # BOUNCE TRADING
        # ===================================================================
        self.ENABLE_BOUNCE_TRADING = cap > 500
        self.RESERVED_SLOTS_FOR_BOUNCE = 0 if cap < 500 else (2 if cap > 3000 else 1)
        self.BOUNCE_LOOKBACK_DAYS = 7
        self.BOUNCE_THRESHOLD_PCT = 0.02
        self.BOUNCE_STOP_LOSS_PCT = 0.08 if not self.ENABLE_BOUNCE_TRADING else (0.10 if cap < 1000 else (0.09 if cap < 5000 else 0.07))
        self.BOUNCE_NO_TAKE_PROFIT = True
        self.BOUNCE_TRAIL_ACTIVATE_PCT = 0.01
        self.BOUNCE_TRAIL_DISTANCE_PCT = 0.015
        self.BOUNCE_MIN_POSITION_SIZE = 150 if not self.ENABLE_BOUNCE_TRADING else (150 if cap < 1000 else (300 if cap < 5000 else 500))
    
    
    # ===================================================================
    # PROPERTIES & HELPER METHODS
    # ===================================================================
    
    @property
    def total_pnl_pct(self):
        """Calculate P&L percentage"""
        return ((self._current_capital - self._starting_capital) / self._starting_capital) * 100
    
    def get_capital_tier(self):
        """Get current capital tier"""
        return self._get_tier(self._current_capital)
    
    def validate_capital_settings(self):
        """Validate settings (v6.2 compatible)"""
        cap = self.CURRENT_CAPITAL
        pos = self.MAX_OPEN_POSITIONS
        pct = self.MAX_POSITION_PCT
        min_p = self.MIN_POSITION_USD
        
        max_alloc = pos * (cap * pct)
        avg_pos = (cap * 0.90) / pos
        
        print(f"\n{'='*70}")
        print(f"CAPITAL VALIDATION - ${cap:.2f}")
        print(f"{'='*70}")
        print(f"Max Positions: {pos}")
        print(f"Position Size: {pct*100:.1f}% of capital")
        print(f"Min Position: ${min_p}")
        print(f"Avg Position: ${avg_pos:.2f}")
        print(f"Max Allocation: ${max_alloc:.2f} ({(max_alloc/cap)*100:.1f}% of capital)")
        print()
        
        warnings = []
        if avg_pos < min_p:
            warnings.append(f"WARNING: Avg (${avg_pos:.2f}) < Min (${min_p})")
        if max_alloc > cap * 1.1:
            warnings.append(f"WARNING: Max allocation exceeds capital!")
        if pos > 5 and cap < 1000:
            warnings.append(f"WARNING: Too many positions for capital")
        
        if warnings:
            print("WARNINGS:")
            for w in warnings:
                print(f"   {w}")
        else:
            print("All validated!")
        
        print(f"{'='*70}\n")
        return len(warnings) == 0
    
    def print_capital_summary(self):
        """Print summary (v6.2 compatible + dynamic enhancements)"""
        tier = self.get_capital_tier()
        pnl = self.total_pnl_pct
        pnl_indicator = "PROFIT" if pnl >= 0 else "LOSS"
        
        print(f"\n{'='*70}")
        print(f"DYNAMIC CONFIG v6.3-FIXED - Tier: {tier.upper()}")
        print(f"{'='*70}")
        print(f"Starting Capital: ${self.STARTING_CAPITAL:.2f}")
        print(f"Current Capital: ${self.CURRENT_CAPITAL:.2f} ({pnl:+.2f}% {pnl_indicator})")
        print(f"Positions: {self.MAX_OPEN_POSITIONS} x {self.MAX_POSITION_PCT*100:.1f}% (${self.MIN_POSITION_USD} min)")
        print(f"Risk/Trade: {self.MAX_RISK_PER_TRADE*100:.2f}% | Drawdown: {self.MAX_DRAWDOWN_PCT*100:.1f}%")
        print(f"Daily Loss: {self.MAX_DAILY_LOSS_PCT*100:.1f}% (${self.MAX_DAILY_LOSS_AMOUNT})")
        print(f"Confidence: {self.SIGNAL_CONFIDENCE_THRESHOLD*100:.0f}% | Quality: {self.MIN_QUALITY_SCORE}")
        print(f"Stop Loss: {self.MAX_SL_PCT*100:.2f}% | ATR SL: {self.ATR_SL_MULT:.1f}x")
        print(f"Take Profit: {self.MAX_TP_PCT*100:.2f}% | ATR TP: {self.ATR_TP_MULT:.1f}x")
        print(f"Trailing: Activate at {self.TRAIL_ACTIVATE_ATR_MULT:.1f}x ATR")
        print(f"Partial TP: {'ENABLED' if self.ENABLE_PARTIAL_TP else 'DISABLED'} @ {self.PARTIAL_TP_TRIGGER_ATR_MULT:.1f}x ATR")
        print(f"Max Position Hold: {self.MAX_POSITION_HOURS}h")
        print(f"Min Win Rate: {self.MIN_WIN_RATE_TO_TRADE*100:.0f}%")
        print(f"Watchlist: {len(self.WATCHLIST)} coins | Scan: {self.SCAN_INTERVAL}s")
        print(f"ML: {self.ML_ENABLED} | Sentiment: {self.ENABLE_SENTIMENT_ANALYSIS} | Bounce: {self.ENABLE_BOUNCE_TRADING}")
        print(f"Last Update: {self._last_update.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"\nKEY FEATURES:")
        print(f"   DYNAMIC capital-based adjustment")
        print(f"   FIXED tier boundaries ($1000 = MEDIUM)")
        print(f"   Proper position counts (3 @ $1000, not 5!)")
        print(f"   Wider stop losses (avoid premature exits)")
        print(f"   Realistic take profits (achievable targets)")
        print(f"   Partial TP always enabled (lock in gains)")
        print(f"   Better trailing stops (capture trends)")
        print(f"   Higher signal quality threshold (better entries)")
        print(f"{'='*70}\n")
    
    def print_summary(self):
        """Alias for print_capital_summary (backward compatible)"""
        self.print_capital_summary()


# Backward compatibility: Allow import as Config
Config = DynamicConfig


# Usage Example & Testing
if __name__ == "__main__":
    print("="*70)
    print("DYNAMIC CONFIG v6.3-FIXED - TESTING")
    print("="*70)
    
    # Initialize with starting capital
    config = DynamicConfig(starting_capital=1000)
    config.print_summary()
    config.validate_capital_settings()
    
    # Test access to parameters
    print("\n" + "="*70)
    print("PARAMETER ACCESS TEST")
    print("="*70)
    print(f"Current max positions: {config.MAX_OPEN_POSITIONS}")
    print(f"Current position %: {config.MAX_POSITION_PCT*100:.1f}%")
    print(f"Current allocation: {config.MAX_OPEN_POSITIONS * config.MAX_POSITION_PCT * 100:.0f}%")
    print(f"Current tier: {config.CAPITAL_TIER}")
    print(f"ML Enabled: {config.ML_ENABLED}")
    print(f"Watchlist size: {len(config.WATCHLIST)}")
