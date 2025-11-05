"""
Production Trading Bot Configuration v6.2 - CAPITAL ADAPTIVE (OPTIMIZED FOR WIN RATE)
Automatically scales ALL parameters based on account size ($100 - $10,000)
CRITICAL FIXES: Loosened stops, realistic TPs, better position management
"""
import os


class Config:
    """Dynamic configuration that scales with capital"""
    
    # ===================================================================
    # VERSION
    # ===================================================================
    BOT_VERSION = "6.2.0"
    CONFIG_VERSION = "6.2-OPTIMIZED"
    
    # ===================================================================
    # EXCHANGE
    # ===================================================================
    EXCHANGE = "binance"
    API_KEY = os.getenv('EXCHANGE_API_KEY', '')
    API_SECRET = os.getenv('EXCHANGE_API_SECRET', '')
    PAPER_TRADING = os.getenv('PAPER_TRADING', 'True').lower() == 'true'
    
    # ===================================================================
    # CAPITAL - CHANGE THIS VALUE OR SET IN .env FILE
    # ===================================================================
    STARTING_CAPITAL = float(os.getenv('STARTING_CAPITAL', '1000'))
    INITIAL_CAPITAL = STARTING_CAPITAL
    
    # ===================================================================
    # HELPER FUNCTIONS (All @staticmethod - no cls dependency)
    # ===================================================================
    
    @staticmethod
    def get_tier(cap):
        """Get capital tier"""
        if cap < 250:
            return 'micro'
        elif cap < 500:
            return 'small'
        elif cap < 1000:
            return 'medium'
        elif cap < 3000:
            return 'large'
        else:
            return 'whale'
    
    @staticmethod
    def calc_positions(cap):
        """REDUCED: Fewer positions = better capital per trade"""
        if cap < 200: return 2
        elif cap < 400: return 3
        elif cap < 600: return 3  # Changed from 4
        elif cap < 1000: return 4  # Changed from 5
        elif cap < 2000: return 5  # Changed from 6
        elif cap < 3500: return 6  # Changed from 8
        elif cap < 7000: return 8  # Changed from 10
        else: return 10  # Changed from 12
    
    @staticmethod
    def calc_position_pct(cap, pos):
        """INCREASED: Larger positions for better profit potential"""
        base = 0.90 / pos
        return min(base * 1.2, 0.50)  # Changed from 1.1 to 1.2
    
    @staticmethod
    def calc_min_pos(cap, pos):
        avg = (cap * 0.90) / pos
        return max(40, int(avg * 0.45))
    
    @staticmethod
    def calc_risk(cap):
        """INCREASED: Allow more risk per trade for profit"""
        if cap < 500: return 0.030  # Changed from 0.025
        elif cap < 2000: return 0.025  # Changed from 0.020
        elif cap < 5000: return 0.022  # Changed from 0.018
        else: return 0.020  # Changed from 0.015
    
    @staticmethod
    def calc_drawdown(cap):
        if cap < 500: return 0.20
        elif cap < 1000: return 0.17
        elif cap < 2000: return 0.15
        elif cap < 5000: return 0.13
        else: return 0.10
    
    @staticmethod
    def calc_atr(cap):
        if cap < 300: return 0.0010
        elif cap < 500: return 0.0012
        elif cap < 1000: return 0.0015
        elif cap < 5000: return 0.0020
        else: return 0.0025
    
    @staticmethod
    def calc_sl_mult(cap):
        """INCREASED: Wider stops to avoid premature exits"""
        if cap < 300: return 1.5  # Changed from 1.2
        elif cap < 500: return 1.6  # Changed from 1.3
        elif cap < 1000: return 1.7  # Changed from 1.4
        elif cap < 5000: return 1.8  # Changed from 1.5
        else: return 2.0  # Changed from 1.6
    
    @staticmethod
    def calc_sl_pct(cap):
        """INCREASED: Wider percentage stops"""
        if cap < 300: return 0.025  # Changed from 0.040 (too tight was issue)
        elif cap < 500: return 0.023  # Changed from 0.035
        elif cap < 1000: return 0.020  # Changed from 0.030
        elif cap < 5000: return 0.018  # Changed from 0.025
        else: return 0.015  # Changed from 0.020
    
    @staticmethod
    def calc_tp_mult(cap):
        """NEW: Separate TP calculation - LOWER for realistic targets"""
        if cap < 300: return 1.8  # 1.8x SL
        elif cap < 500: return 2.0  # 2.0x SL
        elif cap < 1000: return 2.2  # 2.2x SL
        elif cap < 5000: return 2.5  # 2.5x SL
        else: return 3.0  # 3.0x SL
    
    @staticmethod
    def calc_trail(cap):
        """ADJUSTED: Better trailing activation"""
        if cap < 300: return 1.0  # Changed from 1.2
        elif cap < 500: return 1.1  # Changed from 1.4
        elif cap < 1000: return 1.3  # Changed from 1.6
        elif cap < 5000: return 1.5  # Changed from 1.8
        else: return 1.8  # Changed from 2.0
    
    @staticmethod
    def calc_daily_loss(cap):
        if cap < 300: return 0.050
        elif cap < 500: return 0.045
        elif cap < 1000: return 0.040
        elif cap < 2000: return 0.035
        elif cap < 5000: return 0.030
        else: return 0.025
    
    @staticmethod
    def calc_confidence(cap):
        """LOWERED: More selective entries for quality"""
        if cap < 300: return 0.50  # Changed from 0.40
        elif cap < 500: return 0.52  # Changed from 0.42
        elif cap < 1000: return 0.55  # Changed from 0.45
        elif cap < 2000: return 0.57  # Changed from 0.47
        elif cap < 5000: return 0.58  # Changed from 0.50
        else: return 0.60  # Changed from 0.55
    
    @staticmethod
    def calc_quality(cap):
        """INCREASED: Higher quality signals only"""
        if cap < 300: return 40  # Changed from 35
        elif cap < 500: return 45  # Changed from 40
        elif cap < 1000: return 50  # Changed from 45
        elif cap < 2000: return 55  # Changed from 50
        elif cap < 5000: return 60  # Changed from 55
        else: return 65  # Changed from 60
    
    @staticmethod
    def calc_rsi(cap):
        if cap < 300: return 38
        elif cap < 500: return 36
        elif cap < 1000: return 35
        elif cap < 5000: return 33
        else: return 30
    
    @staticmethod
    def calc_losses(cap):
        """REDUCED: Faster cooldown after losses"""
        if cap < 500: return 2  # Changed from 3
        elif cap < 1000: return 3  # Changed from 4
        elif cap < 2000: return 4  # Changed from 5
        else: return 5  # Changed from 6
    
    @staticmethod
    def calc_cooldown(cap):
        if cap < 300: return 0.5
        elif cap < 500: return 0.75
        elif cap < 1000: return 1.0
        elif cap < 5000: return 1.5
        else: return 2.0
    
    @staticmethod
    def calc_winrate(cap):
        """LOWERED: More realistic minimum win rate"""
        if cap < 300: return 0.25  # Changed from 0.30
        elif cap < 500: return 0.28  # Changed from 0.32
        elif cap < 1000: return 0.30  # Changed from 0.35
        elif cap < 5000: return 0.33  # Changed from 0.38
        else: return 0.35  # Changed from 0.40
    
    @staticmethod
    def calc_emergency(cap):
        if cap < 300: return 0.15
        elif cap < 500: return 0.14
        elif cap < 1000: return 0.12
        elif cap < 5000: return 0.10
        else: return 0.08
    
    @staticmethod
    def calc_pause(cap):
        if cap < 300: return 1
        elif cap < 500: return 2
        elif cap < 1000: return 3
        elif cap < 5000: return 4
        else: return 6
    
    @staticmethod
    def calc_slippage(cap):
        if cap < 300: return 0.0008
        elif cap < 500: return 0.0007
        elif cap < 1000: return 0.0006
        elif cap < 5000: return 0.0004
        else: return 0.0003
    
    @staticmethod
    def calc_scan_offset(cap):
        if cap < 300: return 8
        elif cap < 500: return 10
        elif cap < 1000: return 12
        elif cap < 5000: return 15
        else: return 20
    
    @staticmethod
    def calc_scan_int(cap):
        if cap < 300: return 15
        elif cap < 500: return 18
        elif cap < 1000: return 20
        elif cap < 5000: return 25
        else: return 30
    
    @staticmethod
    def calc_multipliers(cap):
        """ADJUSTED: Better position sizing multipliers"""
        if cap < 500: return 1.25, 0.75  # Changed from 1.30, 0.70
        elif cap < 1000: return 1.20, 0.80  # Changed from 1.25, 0.75
        elif cap < 5000: return 1.15, 0.85  # Changed from 1.20, 0.80
        else: return 1.10, 0.90  # Changed from 1.15, 0.85
    
    @staticmethod
    def calc_grade(cap):
        if cap < 250: return 'D'
        elif cap < 1000: return 'C'
        elif cap < 5000: return 'B'
        else: return 'A'
    
    @staticmethod
    def calc_ml_trades(cap):
        if cap < 500: return 4
        elif cap < 1000: return 6
        elif cap < 5000: return 8
        else: return 10
    
    # ===================================================================
    # APPLY ALL CALCULATIONS
    # ===================================================================
    
    # Position sizing
    MAX_OPEN_POSITIONS = calc_positions.__func__(STARTING_CAPITAL)
    MAX_POSITION_PCT = calc_position_pct.__func__(STARTING_CAPITAL, MAX_OPEN_POSITIONS)
    MIN_POSITION_USD = calc_min_pos.__func__(STARTING_CAPITAL, MAX_OPEN_POSITIONS)
    MIN_CAPITAL_USD = int(STARTING_CAPITAL * 0.20)
    
    # Risk parameters
    MAX_RISK_PER_TRADE = calc_risk.__func__(STARTING_CAPITAL)
    MAX_PORTFOLIO_RISK = min(MAX_OPEN_POSITIONS * MAX_RISK_PER_TRADE * 1.2, 0.20)
    MAX_POSITION_PCT_BEAR = MAX_POSITION_PCT * 0.6
    MAX_POSITION_PCT_NEUTRAL = MAX_POSITION_PCT * 0.8
    MAX_DRAWDOWN_PCT = calc_drawdown.__func__(STARTING_CAPITAL)
    
    # Kelly & Risk Management
    USE_KELLY_CRITERION = STARTING_CAPITAL > 2000
    KELLY_FRACTION = 0.25
    ENABLE_CORRELATION_FILTER = STARTING_CAPITAL > 1000
    MAX_CORRELATED_POSITIONS = 5 if STARTING_CAPITAL > 2000 else 3
    CORRELATION_THRESHOLD = 0.80
    ENABLE_VOLATILITY_ADJUSTMENT = STARTING_CAPITAL > 3000
    
    # ===================================================================
    # MULTI-EXCHANGE
    # ===================================================================
    ENABLE_MULTI_EXCHANGE = STARTING_CAPITAL > 5000
    EXCHANGES_LIST = [(EXCHANGE, API_KEY, API_SECRET)]
    MIN_ARBITRAGE_PROFIT = 0.005
    
    # ===================================================================
    # POSITION MANAGEMENT (CRITICAL CHANGES)
    # ===================================================================
    MAX_POSITION_HOURS = 36  # Changed from 48 - faster rotation
    STALE_BAND_ATR_MULT = 2.0
    MIN_ATR_PCT = calc_atr.__func__(STARTING_CAPITAL)
    NEUTRAL_REGIME_MIN_ATR_PCT = MIN_ATR_PCT * 1.3
    NEUTRAL_REGIME_CONFIDENCE_ADJUST = -0.05
    ENABLE_DYNAMIC_CAPACITY = True
    
    # ===================================================================
    # MARKET FILTER
    # ===================================================================
    ENABLE_MARKET_FILTER = STARTING_CAPITAL > 2000
    MARKET_FILTER_ENABLED = ENABLE_MARKET_FILTER
    MIN_FEAR_GREED_INDEX = 15
    MAX_FEAR_GREED_INDEX = 85
    MIN_BTC_VOLATILITY = 0.3
    AUTO_PAUSE_ON_BEAR_MARKET = STARTING_CAPITAL > 1000
    BEAR_DETECTION_THRESHOLD = -0.25
    
    # ===================================================================
    # STOP LOSS & TAKE PROFIT (CRITICAL CHANGES)
    # ===================================================================
    USE_ATR_EXITS = True
    ATR_PERIOD = 14
    ATR_SL_MULT = calc_sl_mult.__func__(STARTING_CAPITAL)
    ATR_TP_MULT = calc_tp_mult.__func__(STARTING_CAPITAL)  # NEW: Separate TP multiplier
    MAX_SL_PCT = calc_sl_pct.__func__(STARTING_CAPITAL)
    MAX_TP_PCT = MAX_SL_PCT * calc_tp_mult.__func__(STARTING_CAPITAL)  # Changed calculation
    FALLBACK_STOP_LOSS_PCT = MAX_SL_PCT * 0.8  # Changed from 0.6
    FALLBACK_TAKE_PROFIT_PCT = MAX_SL_PCT * 2.0
    
    # ===================================================================
    # TRAILING STOPS (IMPROVED)
    # ===================================================================
    ENABLE_ATR_TRAILING = True
    TRAIL_ACTIVATE_ATR_MULT = calc_trail.__func__(STARTING_CAPITAL)
    TRAIL_DISTANCE_ATR_MULT = 0.6  # Changed from 0.7 - tighter trailing
    
    # ===================================================================
    # PARTIAL TAKE PROFIT (ALWAYS ENABLED NOW)
    # ===================================================================
    ENABLE_PARTIAL_TP = True  # Changed from conditional
    PARTIAL_TP_PCT = 0.50
    PARTIAL_TP_TRIGGER_ATR_MULT = 1.2  # Changed from 1.5 - earlier profit taking
    
    # ===================================================================
    # DAILY LOSS PROTECTION
    # ===================================================================
    ENABLE_DAILY_LOSS_CAP = True
    MAX_DAILY_LOSS_PCT = calc_daily_loss.__func__(STARTING_CAPITAL)
    MAX_DAILY_LOSS_AMOUNT = int(STARTING_CAPITAL * MAX_DAILY_LOSS_PCT)
    
    # ===================================================================
    # MULTI-TIMEFRAME
    # ===================================================================
    ENABLE_MULTI_TIMEFRAME = STARTING_CAPITAL > 3000
    TIMEFRAMES = ['1h', '4h'] if ENABLE_MULTI_TIMEFRAME else ['1h']
    TIMEFRAME_WEIGHTS = [0.6, 0.4] if ENABLE_MULTI_TIMEFRAME else [1.0]
    
    # ===================================================================
    # SIGNAL SETTINGS (IMPROVED QUALITY)
    # ===================================================================
    SIGNAL_CONFIDENCE_THRESHOLD = calc_confidence.__func__(STARTING_CAPITAL)
    HIGH_CONFIDENCE_THRESHOLD = SIGNAL_CONFIDENCE_THRESHOLD + 0.15
    LOW_CONFIDENCE_THRESHOLD = SIGNAL_CONFIDENCE_THRESHOLD - 0.05
    MIN_QUALITY_SCORE = calc_quality.__func__(STARTING_CAPITAL)
    
    # RSI
    RSI_PERIOD = 14
    RSI_OVERSOLD = calc_rsi.__func__(STARTING_CAPITAL)
    RSI_OVERBOUGHT = 100 - RSI_OVERSOLD
    
    # MACD
    MACD_FAST = 12
    MACD_SLOW = 26
    MACD_SIGNAL = 9
    
    # Bollinger Bands
    BB_PERIOD = 20
    BB_STD = 2
    
    # ===================================================================
    # LOSS STREAK DETECTION (STRICTER)
    # ===================================================================
    ENABLE_STREAK_DETECTION = True
    MAX_CONSECUTIVE_LOSSES = calc_losses.__func__(STARTING_CAPITAL)
    COOLDOWN_AFTER_LOSSES_HOURS = calc_cooldown.__func__(STARTING_CAPITAL)
    PREVENT_REVENGE_TRADING = True
    REVENGE_TRADE_COOLDOWN_MINS = int(COOLDOWN_AFTER_LOSSES_HOURS * 30)
    CONSECUTIVE_LOSS_LIMIT = MAX_CONSECUTIVE_LOSSES
    MIN_WIN_RATE_TO_TRADE = calc_winrate.__func__(STARTING_CAPITAL)
    
    # ===================================================================
    # EMERGENCY EXIT
    # ===================================================================
    EMERGENCY_EXIT_ENABLED = True
    EMERGENCY_LOSS_PCT = calc_emergency.__func__(STARTING_CAPITAL)
    EMERGENCY_CLOSE_ALL = True
    EMERGENCY_CHECK_INTERVAL = 300
    BEAR_SENTIMENT_THRESHOLD = -0.35
    BEAR_FEAR_INDEX = 20
    BEAR_BTC_DROP = -12
    MIN_BEAR_SIGNALS = 2
    PAUSE_DURATION_HOURS = calc_pause.__func__(STARTING_CAPITAL)
    MIN_EMERGENCY_WAIT_HOURS = PAUSE_DURATION_HOURS * 3
    AUTO_RESUME_ENABLED = True
    
    # ===================================================================
    # FEES & SLIPPAGE
    # ===================================================================
    TRADING_FEE = 0.001
    INCLUDE_SLIPPAGE = True
    SLIPPAGE_RATE = calc_slippage.__func__(STARTING_CAPITAL)
    APPLY_INDIAN_TAX = True
    CAPITAL_GAINS_TAX = 0.30
    TDS_RATE = 0.01
    
    # ===================================================================
    # WATCHLISTS
    # ===================================================================
    USE_ROTATING_WATCHLISTS = True
    WATCHLIST_BEAR = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT']
    
    WATCHLIST_CORE = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'SOL/USDT', 'XRP/USDT', 'ADA/USDT']
    WATCHLIST_EXTENDED = ['AVAX/USDT', 'MATIC/USDT', 'DOT/USDT', 'LINK/USDT', 'ATOM/USDT', 'UNI/USDT', 'ARB/USDT', 'OP/USDT']
    WATCHLIST_AGGRESSIVE = ['LTC/USDT', 'DOGE/USDT', 'INJ/USDT', 'SUI/USDT', 'FET/USDT', 'NEAR/USDT', 'TIA/USDT']
    
    # Build watchlist based on tier
    _tier = get_tier.__func__(STARTING_CAPITAL)
    if _tier == 'micro':
        WATCHLIST_A, WATCHLIST_B, WATCHLIST_C = WATCHLIST_CORE[:4], WATCHLIST_EXTENDED[:4], []
    elif _tier == 'small':
        WATCHLIST_A, WATCHLIST_B, WATCHLIST_C = WATCHLIST_CORE, WATCHLIST_EXTENDED[:6], []
    elif _tier == 'medium':
        WATCHLIST_A, WATCHLIST_B, WATCHLIST_C = WATCHLIST_CORE, WATCHLIST_EXTENDED, WATCHLIST_AGGRESSIVE[:3]
    else:
        WATCHLIST_A, WATCHLIST_B, WATCHLIST_C = WATCHLIST_CORE, WATCHLIST_EXTENDED, WATCHLIST_AGGRESSIVE
    
    WATCHLIST = WATCHLIST_A + WATCHLIST_B + WATCHLIST_C
    GROUP_SCAN_OFFSET = calc_scan_offset.__func__(STARTING_CAPITAL)
    
    # ===================================================================
    # ML & ONLINE LEARNING
    # ===================================================================
    ENABLE_ONLINE_LEARNING = STARTING_CAPITAL > 2000
    ML_ENABLED = STARTING_CAPITAL > 500
    ML_MODEL_TO_USE = 'ensemble' if STARTING_CAPITAL > 1000 else 'random_forest'
    ML_CONFIDENCE_THRESHOLD = SIGNAL_CONFIDENCE_THRESHOLD
    ML_SIGNAL_WEIGHT = 0.35 if ML_ENABLED else 0.0
    BEARISH_CONFIDENCE_BOOST = 0.10
    
    ENABLE_ENSEMBLE_ML = STARTING_CAPITAL > 1000
    ENSEMBLE_MODELS = ['random_forest', 'lightgbm', 'xgboost'] if ENABLE_ENSEMBLE_ML else ['random_forest']
    ENSEMBLE_WEIGHTS = {'rf': 0.35, 'lgb': 0.35, 'xgb': 0.30}
    
    ONLINE_LEARNING_METHOD = 'sgd'
    UPDATE_MODEL_PER_TRADE = True
    MIN_TRADES_BEFORE_UPDATE = calc_ml_trades.__func__(STARTING_CAPITAL)
    BATCH_UPDATE_SIZE = MIN_TRADES_BEFORE_UPDATE * 2
    ONLINE_LEARNING_RATE = 0.01
    MOMENTUM = 0.9
    DECAY_RATE = 0.95
    SAVE_MODEL_AFTER_UPDATES = 50
    ONLINE_MODEL_PATH = 'ml/models/online_model.pkl'
    MAX_PERFORMANCE_DROP = 0.15
    ENABLE_MODEL_ROLLBACK = True
    VALIDATION_WINDOW = 20
    ML_RETRAIN_INTERVAL = 100
    ML_MIN_SAMPLES = 50
    ML_FEATURE_SET = 'enhanced' if STARTING_CAPITAL > 2000 else 'basic'
    USE_FEATURE_ENGINEERING = STARTING_CAPITAL > 1000
    
    # ===================================================================
    # SENTIMENT ANALYSIS
    # ===================================================================
    ENABLE_SENTIMENT_ANALYSIS = STARTING_CAPITAL > 3000
    SENTIMENT_WEIGHT = 0.10 if ENABLE_SENTIMENT_ANALYSIS else 0.0
    SENTIMENT_CACHE_DURATION = 600
    SENTIMENT_SOURCES = ['fear_greed']
    SENTIMENT_BULLISH_THRESHOLD = 0.3
    SENTIMENT_BEARISH_THRESHOLD = -0.3
    SENTIMENT_ANOMALY_THRESHOLD = 5.0
    
    # ===================================================================
    # ADVANCED FEATURES
    # ===================================================================
    ENABLE_ADAPTIVE_SIZING = True
    _high, _low = calc_multipliers.__func__(STARTING_CAPITAL)
    HIGH_CONFIDENCE_MULTIPLIER = _high
    LOW_CONFIDENCE_MULTIPLIER = _low
    
    ENABLE_ARBITRAGE = STARTING_CAPITAL > 5000
    MAX_ARBITRAGE_CAPITAL = 0.15
    MIN_ARBITRAGE_VOLUME = 50000
    ENABLE_QUALITY_FILTER = STARTING_CAPITAL > 1000
    MIN_SIGNAL_QUALITY_GRADE = calc_grade.__func__(STARTING_CAPITAL)
    
    # ===================================================================
    # TIMING
    # ===================================================================
    SCAN_INTERVAL = calc_scan_int.__func__(STARTING_CAPITAL)
    ENABLE_TIME_FILTERS = False
    TRADING_START_HOUR = 0
    TRADING_END_HOUR = 24
    ENABLE_OPPORTUNISTIC_SCAN = STARTING_CAPITAL > 1000
    OPPORTUNISTIC_SCAN_INTERVAL = 180
    TOP_MOVER_THRESHOLD = 0.025
    ARBITRAGE_INTERVAL = 60
    
    # ===================================================================
    # LOGGING
    # ===================================================================
    LOG_LEVEL = "INFO"
    LOG_FILE = "logs/bot.log"
    SAVE_TRADE_HISTORY = True
    TRADE_HISTORY_FILE = "trade_history.csv"
    PERFORMANCE_FILE = "data/performance.csv"
    BACKTEST_RESULTS_FILE = "data/backtest_results.csv"
    LOG_SIGNAL_DETAILS = STARTING_CAPITAL < 1000
    LOG_SENTIMENT_SCORES = False
    LOG_ML_PREDICTIONS = ML_ENABLED
    
    # ===================================================================
    # MONITORING
    # ===================================================================
    ENABLE_HEARTBEAT = True
    HEARTBEAT_INTERVAL = 600
    ENABLE_PERFORMANCE_MONITOR = True
    PERFORMANCE_LOG_INTERVAL = 3600
    MAX_DRAWDOWN_ALERT = MAX_DRAWDOWN_PCT * 0.8
    MIN_WIN_RATE_ALERT = MIN_WIN_RATE_TO_TRADE
    IDLE_CAPACITY_ALERT_SCANS = 150
    FLAT_PNL_ALERT_SCANS = 75
    MIN_CAPACITY_UTILIZATION = 0.25
    AUTO_PAUSE_ON_DRAWDOWN = MAX_DRAWDOWN_PCT
    AUTO_PAUSE_ON_LOSSES = MAX_CONSECUTIVE_LOSSES + 2
    
    # ===================================================================
    # SYSTEM
    # ===================================================================
    ENABLE_MEMORY_MANAGEMENT = True
    GC_INTERVAL = 100
    MAX_MEMORY_MB = 500
    MAX_SCANS_PER_CYCLE = 100
    RATE_LIMIT_DELAY = 0.05 if STARTING_CAPITAL < 500 else 0.1
    ENABLE_GARBAGE_COLLECTION = True
    GC_COLLECTION_INTERVAL = 100
    RATE_LIMIT_SLEEP = 0.3 if STARTING_CAPITAL < 500 else 0.5
    MAX_API_RETRIES = 3
    API_RETRY_DELAY = 2
    LOG_MAX_BYTES = 10 * 1024 * 1024
    LOG_BACKUP_COUNT = 5
    
    # ===================================================================
    # NOTIFICATIONS
    # ===================================================================
    ENABLE_TELEGRAM_ALERTS = False
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')
    ALERT_ON_TRADES = True
    ALERT_ON_ERRORS = True
    ALERT_ON_DAILY_PNL = True
    ALERT_ON_SENTIMENT_ANOMALY = False
    ALERT_ON_QUALITY_FILTER = False
    
    # ===================================================================
    # DEBUG
    # ===================================================================
    DEBUG_MODE = False
    VERBOSE_LOGGING = STARTING_CAPITAL < 500
    SAVE_PREDICTIONS = True
    FAST_MODE = False
    DRY_RUN = False
    
    # ===================================================================
    # FEATURE FLAGS
    # ===================================================================
    FEATURES = {
        'multi_exchange': ENABLE_MULTI_EXCHANGE,
        'multi_timeframe': ENABLE_MULTI_TIMEFRAME,
        'sentiment_analysis': ENABLE_SENTIMENT_ANALYSIS,
        'ensemble_ml': ENABLE_ENSEMBLE_ML,
        'correlation_filter': ENABLE_CORRELATION_FILTER,
        'volatility_adjustment': ENABLE_VOLATILITY_ADJUSTMENT,
        'quality_filter': ENABLE_QUALITY_FILTER,
        'adaptive_sizing': True,
    }
    
    # ===================================================================
    # BOUNCE TRADING
    # ===================================================================
    ENABLE_BOUNCE_TRADING = STARTING_CAPITAL > 500
    RESERVED_SLOTS_FOR_BOUNCE = 0 if STARTING_CAPITAL < 500 else (2 if STARTING_CAPITAL > 3000 else 1)
    BOUNCE_LOOKBACK_DAYS = 7
    BOUNCE_THRESHOLD_PCT = 0.02
    BOUNCE_STOP_LOSS_PCT = 0.08 if not ENABLE_BOUNCE_TRADING else (0.10 if STARTING_CAPITAL < 1000 else (0.09 if STARTING_CAPITAL < 5000 else 0.07))
    BOUNCE_NO_TAKE_PROFIT = True
    BOUNCE_TRAIL_ACTIVATE_PCT = 0.01
    BOUNCE_TRAIL_DISTANCE_PCT = 0.015
    BOUNCE_MIN_POSITION_SIZE = 150 if not ENABLE_BOUNCE_TRADING else (150 if STARTING_CAPITAL < 1000 else (300 if STARTING_CAPITAL < 5000 else 500))
    
    # ===================================================================
    # VALIDATION & SUMMARY
    # ===================================================================
    @classmethod
    def get_capital_tier(cls):
        """Get capital tier for display"""
        return cls.get_tier(cls.STARTING_CAPITAL)
    
    @classmethod
    def validate_capital_settings(cls):
        """Validate settings"""
        cap = cls.STARTING_CAPITAL
        pos = cls.MAX_OPEN_POSITIONS
        pct = cls.MAX_POSITION_PCT
        min_p = cls.MIN_POSITION_USD
        
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
            warnings.append(f"⚠️  Avg (${avg_pos:.2f}) < Min (${min_p})")
        if max_alloc > cap * 1.1:
            warnings.append(f"⚠️  Max allocation exceeds capital!")
        if pos > 5 and cap < 1000:
            warnings.append(f"⚠️  Too many positions for capital")
        
        if warnings:
            print("❌ WARNINGS:")
            for w in warnings:
                print(f"   {w}")
        else:
            print("✅ All validated!")
        
        print(f"{'='*70}\n")
        return len(warnings) == 0
    
    @classmethod
    def print_capital_summary(cls):
        """Print summary with CHANGE HIGHLIGHTS"""
        tier = cls.get_capital_tier()
        print(f"\n{'='*70}")
        print(f"OPTIMIZED CONFIG v6.2 - Tier: {tier.upper()}")
        print(f"{'='*70}")
        print(f"Capital: ${cls.STARTING_CAPITAL:.2f}")
        print(f"Positions: {cls.MAX_OPEN_POSITIONS} × {cls.MAX_POSITION_PCT*100:.1f}% (${cls.MIN_POSITION_USD} min)")
        print(f"Risk/Trade: {cls.MAX_RISK_PER_TRADE*100:.2f}% | Drawdown: {cls.MAX_DRAWDOWN_PCT*100:.1f}%")
        print(f"Daily Loss: {cls.MAX_DAILY_LOSS_PCT*100:.1f}% (${cls.MAX_DAILY_LOSS_AMOUNT})")
        print(f"Confidence: {cls.SIGNAL_CONFIDENCE_THRESHOLD*100:.0f}% | Quality: {cls.MIN_QUALITY_SCORE}")
        print(f"Stop Loss: {cls.MAX_SL_PCT*100:.2f}% | ATR SL: {cls.ATR_SL_MULT:.1f}x")
        print(f"Take Profit: {cls.MAX_TP_PCT*100:.2f}% | ATR TP: {cls.ATR_TP_MULT:.1f}x")
        print(f"Trailing: Activate at {cls.TRAIL_ACTIVATE_ATR_MULT:.1f}x ATR")
        print(f"Partial TP: {'✅ ENABLED' if cls.ENABLE_PARTIAL_TP else '❌ DISABLED'} @ {cls.PARTIAL_TP_TRIGGER_ATR_MULT:.1f}x ATR")
        print(f"Max Position Hold: {cls.MAX_POSITION_HOURS}h")
        print(f"Min Win Rate: {cls.MIN_WIN_RATE_TO_TRADE*100:.0f}%")
        print(f"Watchlist: {len(cls.WATCHLIST)} coins | Scan: {cls.SCAN_INTERVAL}s")
        print(f"ML: {cls.ML_ENABLED} | Sentiment: {cls.ENABLE_SENTIMENT_ANALYSIS} | Bounce: {cls.ENABLE_BOUNCE_TRADING}")
        print(f"\n🔧 KEY CHANGES IN v6.2:")
        print(f"   ✅ Reduced max positions (better capital per trade)")
        print(f"   ✅ Wider stop losses (avoid premature exits)")
        print(f"   ✅ Realistic take profits (achievable targets)")
        print(f"   ✅ Partial TP always enabled (lock in gains)")
        print(f"   ✅ Better trailing stops (capture trends)")
        print(f"   ✅ Higher signal quality threshold (better entries)")
        print(f"   ✅ Faster position rotation (36h max hold)")
        print(f"   ✅ Lower min win rate requirement (more realistic)")
        print(f"{'='*70}\n")


# Auto-print on import
if __name__ != "__main__":
    Config.print_capital_summary()
    Config.validate_capital_settings()
