"""
Production Trading Bot Configuration - v5.0 INSTITUTIONAL GRADE
October 28, 2025 - Phase 1-3 Upgrades Integrated
ALL NEW FEATURES ENABLED
"""
import os


class Config:
    """Bot configuration class v5.0 - INSTITUTIONAL GRADE"""
    
    # ===================================================================
    # VERSION
    # ===================================================================
    BOT_VERSION = "5.0.0"
    CONFIG_VERSION = "5.0"
    
    # ===================================================================
    # EXCHANGE
    # ===================================================================
    EXCHANGE = "binance"
    API_KEY = os.getenv('EXCHANGE_API_KEY', '')
    API_SECRET = os.getenv('EXCHANGE_API_SECRET', '')
    PAPER_TRADING = True
    
    # ===================================================================
    # NEW: MULTI-EXCHANGE SUPPORT (Phase 1)
    # ===================================================================
    ENABLE_MULTI_EXCHANGE = False  # Set True to enable
    EXCHANGES_LIST = [
        # Format: (exchange_id, api_key, api_secret)
        (EXCHANGE, API_KEY, API_SECRET),
        # Add more exchanges:
        # ('coinbase', os.getenv('COINBASE_API_KEY', ''), os.getenv('COINBASE_API_SECRET', '')),
        # ('kraken', os.getenv('KRAKEN_API_KEY', ''), os.getenv('KRAKEN_API_SECRET', '')),
    ]
    
    # Arbitrage settings
    MIN_ARBITRAGE_PROFIT = 0.005  # 0.5% minimum profit after fees
    
    # ===================================================================
    # CAPITAL & RISK - ✅ ENHANCED
    # ===================================================================
    STARTING_CAPITAL = 15000
    INITIAL_CAPITAL = 15000
    MAX_RISK_PER_TRADE = 0.02
    MAX_PORTFOLIO_RISK = 0.08
    
    MAX_OPEN_POSITIONS = 8
    
    MAX_POSITION_PCT = 0.06
    MAX_POSITION_PCT_BEAR = 0.04
    MAX_POSITION_PCT_NEUTRAL = 0.055
    
    MIN_POSITION_USD = 50
    MIN_CAPITAL_USD = 100
    USE_KELLY_CRITERION = False
    KELLY_FRACTION = 0.25
    
    # NEW: Risk Manager v5.0 Features
    ENABLE_CORRELATION_FILTER = True
    MAX_CORRELATED_POSITIONS = 3
    CORRELATION_THRESHOLD = 0.7
    ENABLE_VOLATILITY_ADJUSTMENT = True
    MAX_DRAWDOWN_PCT = 0.20
    
    # ===================================================================
    # POSITION MANAGEMENT - ✅ ENHANCED
    # ===================================================================
    MAX_POSITION_HOURS = 24
    STALE_BAND_ATR_MULT = 1.5
    
    MIN_ATR_PCT = 0.003
    NEUTRAL_REGIME_MIN_ATR_PCT = 0.003
    NEUTRAL_REGIME_CONFIDENCE_ADJUST = -0.05
    ENABLE_DYNAMIC_CAPACITY = True
    
    # ===================================================================
    # MARKET FILTER - ✅ ENHANCED
    # ===================================================================
    ENABLE_MARKET_FILTER = False
    MARKET_FILTER_ENABLED = False
    MIN_FEAR_GREED_INDEX = 20
    MAX_FEAR_GREED_INDEX = 80
    MIN_BTC_VOLATILITY = 0.8
    AUTO_PAUSE_ON_BEAR_MARKET = True
    BEAR_DETECTION_THRESHOLD = -0.02
    
    # ===================================================================
    # STOP LOSS & TAKE PROFIT - ✅ OPTIMIZED
    # ===================================================================
    USE_ATR_EXITS = True
    ATR_PERIOD = 14
    
    ATR_SL_MULT = 1.2
    ATR_TP_MULT = 3.6
    
    MAX_SL_PCT = 0.04
    MAX_TP_PCT = 0.15
    FALLBACK_STOP_LOSS_PCT = 0.025
    FALLBACK_TAKE_PROFIT_PCT = 0.075
    
    # ===================================================================
    # TRAILING STOPS - ✅ ENHANCED
    # ===================================================================
    ENABLE_ATR_TRAILING = True
    TRAIL_ACTIVATE_ATR_MULT = 1.5
    TRAIL_DISTANCE_ATR_MULT = 0.8
    
    # ===================================================================
    # PARTIAL TAKE PROFIT - ✅ ENABLED
    # ===================================================================
    ENABLE_PARTIAL_TP = True
    PARTIAL_TP_PCT = 0.50
    PARTIAL_TP_TRIGGER_ATR_MULT = 1.5
    
    # ===================================================================
    # DAILY LOSS PROTECTION - ✅ ENABLED
    # ===================================================================
    ENABLE_DAILY_LOSS_CAP = True
    MAX_DAILY_LOSS_PCT = 0.02
    MAX_DAILY_LOSS_AMOUNT = 300
    
    # ===================================================================
    # NEW: MULTI-TIMEFRAME ANALYSIS (Phase 2)
    # ===================================================================
    ENABLE_MULTI_TIMEFRAME = False  # ⚡ NEW FEATURE
    TIMEFRAMES = ['1h', '4h', '1d']
    TIMEFRAME_WEIGHTS = [0.5, 0.3, 0.2]
    
    # ===================================================================
    # SIGNAL SETTINGS - ✅ ENHANCED v5.0
    # ===================================================================
    SIGNAL_CONFIDENCE_THRESHOLD = 0.45
    HIGH_CONFIDENCE_THRESHOLD = 0.75
    LOW_CONFIDENCE_THRESHOLD = 0.60
    
    # Signal quality thresholds
    MIN_QUALITY_SCORE = 50  # NEW: Minimum quality score to trade (0-100)
    
    # RSI
    RSI_PERIOD = 14
    RSI_OVERSOLD = 35
    RSI_OVERBOUGHT = 65
    
    # MACD
    MACD_FAST = 12
    MACD_SLOW = 26
    MACD_SIGNAL = 9
    
    # Bollinger Bands
    BB_PERIOD = 20
    BB_STD = 2
    
    # ===================================================================
    # LOSS STREAK DETECTION - ✅ ENABLED
    # ===================================================================
    ENABLE_STREAK_DETECTION = True
    MAX_CONSECUTIVE_LOSSES = 3
    COOLDOWN_AFTER_LOSSES_HOURS = 2
    PREVENT_REVENGE_TRADING = True
    REVENGE_TRADE_COOLDOWN_MINS = 60
    CONSECUTIVE_LOSS_LIMIT = 3
    MIN_WIN_RATE_TO_TRADE = 0.40
    
    # ===================================================================
    # EMERGENCY EXIT - ✅ ENABLED
    # ===================================================================
    EMERGENCY_EXIT_ENABLED = True
    EMERGENCY_LOSS_PCT = 0.08
    EMERGENCY_CLOSE_ALL = True
    EMERGENCY_CHECK_INTERVAL = 1800
    BEAR_SENTIMENT_THRESHOLD = -0.35
    BEAR_FEAR_INDEX = 25
    BEAR_BTC_DROP = -8
    MIN_BEAR_SIGNALS = 1
    PAUSE_DURATION_HOURS = 6
    MIN_EMERGENCY_WAIT_HOURS = 3
    AUTO_RESUME_ENABLED = True
    
    # ===================================================================
    # FEES & SLIPPAGE - ✅ ACCURATE
    # ===================================================================
    TRADING_FEE = 0.001
    INCLUDE_SLIPPAGE = True
    SLIPPAGE_RATE = 0.0005
    APPLY_INDIAN_TAX = True
    CAPITAL_GAINS_TAX = 0.30
    TDS_RATE = 0.01
    
    # ===================================================================
    # WATCHLISTS - ✅ ENHANCED
    # ===================================================================
    USE_ROTATING_WATCHLISTS = True
    
    WATCHLIST_BEAR = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT']
    
    WATCHLIST_A = [
        'BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'SOL/USDT',
        'XRP/USDT', 'AVAX/USDT', 'ADA/USDT', 'MATIC/USDT'
    ]
    
    WATCHLIST_B = [
        'DOT/USDT', 'LINK/USDT', 'UNI/USDT', 'ATOM/USDT',
        'ARB/USDT', 'OP/USDT', 'DOGE/USDT', 'SHIB/USDT',
        'LTC/USDT', 'PEPE/USDT'
    ]
    
    WATCHLIST_C = [
        'INJ/USDT', 'SUI/USDT', 'TIA/USDT', 'FET/USDT', 'NEAR/USDT'
    ]
    
    WATCHLIST = WATCHLIST_A + WATCHLIST_B + WATCHLIST_C
    GROUP_SCAN_OFFSET = 20
    
    # ===================================================================
    # ML & ONLINE LEARNING - ✅ ENHANCED v5.0
    # ===================================================================
    ENABLE_ONLINE_LEARNING = True
    ML_ENABLED = True
    ML_MODEL_TO_USE = 'ensemble'  # NEW: 'ensemble', 'lightgbm', 'random_forest', 'xgboost'
    ML_CONFIDENCE_THRESHOLD = 0.65
    ML_SIGNAL_WEIGHT = 0.50
    BEARISH_CONFIDENCE_BOOST = 0.10
    
    # NEW: Ensemble Model Settings
    ENABLE_ENSEMBLE_ML = True
    ENSEMBLE_MODELS = ['random_forest', 'lightgbm', 'xgboost']
    ENSEMBLE_WEIGHTS = {
        'rf': 0.35,
        'lgb': 0.35,
        'xgb': 0.30
    }
    
    # Online Learning Parameters
    ONLINE_LEARNING_METHOD = 'sgd'
    UPDATE_MODEL_PER_TRADE = True
    MIN_TRADES_BEFORE_UPDATE = 6
    BATCH_UPDATE_SIZE = 12
    ONLINE_LEARNING_RATE = 0.01
    MOMENTUM = 0.9
    DECAY_RATE = 0.95
    
    # Model persistence
    SAVE_MODEL_AFTER_UPDATES = 50
    ONLINE_MODEL_PATH = 'ml/models/online_model.pkl'
    
    # Safety limits
    MAX_PERFORMANCE_DROP = 0.15
    ENABLE_MODEL_ROLLBACK = True
    VALIDATION_WINDOW = 20
    
    # Additional ML settings
    ML_RETRAIN_INTERVAL = 100
    ML_MIN_SAMPLES = 50
    ML_FEATURE_SET = 'enhanced'  # NEW: 'basic' or 'enhanced' (25 features)
    USE_FEATURE_ENGINEERING = True
    
    # ===================================================================
    # NEW: SENTIMENT ANALYSIS v5.0 (Phase 3)
    # ===================================================================
    ENABLE_SENTIMENT_ANALYSIS = True  # ⚡ NEW FEATURE
    SENTIMENT_WEIGHT = 0.15  # Weight in signal combination
    SENTIMENT_CACHE_DURATION = 300  # 5 minutes
    
    # Sentiment sources
    SENTIMENT_SOURCES = [
        'cryptocompare',  # News
        'reddit',         # Social
        'google',         # News aggregator
        'fear_greed',     # Market sentiment index
        'coingecko',      # Community votes
        'messari'         # Professional analysis
    ]
    
    # Sentiment thresholds
    SENTIMENT_BULLISH_THRESHOLD = 0.3
    SENTIMENT_BEARISH_THRESHOLD = -0.3
    SENTIMENT_ANOMALY_THRESHOLD = 2.5  # Standard deviations
    
    # ===================================================================
    # ADVANCED FEATURES - ✅ ENHANCED v5.0
    # ===================================================================
    ENABLE_ADAPTIVE_SIZING = True
    HIGH_CONFIDENCE_MULTIPLIER = 1.15
    LOW_CONFIDENCE_MULTIPLIER = 0.85
    
    ENABLE_ARBITRAGE = False  # Enable if using multi-exchange
    MIN_ARBITRAGE_PROFIT = 0.003
    MAX_ARBITRAGE_CAPITAL = 0.15
    MIN_ARBITRAGE_VOLUME = 50000
    
    # NEW: Signal Quality Filtering
    ENABLE_QUALITY_FILTER = True
    MIN_SIGNAL_QUALITY_GRADE = 'C'  # 'A', 'B', or 'C'
    
    # ===================================================================
    # TIMING - ✅ OPTIMIZED
    # ===================================================================
    SCAN_INTERVAL = 20
    ENABLE_TIME_FILTERS = False
    TRADING_START_HOUR = 19
    TRADING_END_HOUR = 2
    ENABLE_OPPORTUNISTIC_SCAN = True
    OPPORTUNISTIC_SCAN_INTERVAL = 180
    TOP_MOVER_THRESHOLD = 0.025
    ARBITRAGE_INTERVAL = 60
    
    # ===================================================================
    # LOGGING - ✅ ENHANCED
    # ===================================================================
    LOG_LEVEL = "INFO"
    LOG_FILE = "logs/bot.log"
    SAVE_TRADE_HISTORY = True
    TRADE_HISTORY_FILE = "trade_history.csv"
    PERFORMANCE_FILE = "data/performance.csv"
    BACKTEST_RESULTS_FILE = "data/backtest_results.csv"
    
    # NEW: Enhanced logging
    LOG_SIGNAL_DETAILS = True
    LOG_SENTIMENT_SCORES = True
    LOG_ML_PREDICTIONS = True
    
    # ===================================================================
    # MONITORING - ✅ ENHANCED v5.0
    # ===================================================================
    ENABLE_HEARTBEAT = True
    HEARTBEAT_INTERVAL = 300
    ENABLE_PERFORMANCE_MONITOR = True
    PERFORMANCE_LOG_INTERVAL = 3600
    MAX_DRAWDOWN_ALERT = 0.08
    MIN_WIN_RATE_ALERT = 0.38
    IDLE_CAPACITY_ALERT_SCANS = 25
    FLAT_PNL_ALERT_SCANS = 40
    MIN_CAPACITY_UTILIZATION = 0.25
    AUTO_PAUSE_ON_DRAWDOWN = 0.10
    AUTO_PAUSE_ON_LOSSES = 5
    
    # ===================================================================
    # SYSTEM - ✅ ENHANCED
    # ===================================================================
    ENABLE_MEMORY_MANAGEMENT = True
    GC_INTERVAL = 100
    MAX_MEMORY_MB = 500
    MAX_SCANS_PER_CYCLE = 100
    RATE_LIMIT_DELAY = 0.1
    ENABLE_GARBAGE_COLLECTION = True
    GC_COLLECTION_INTERVAL = 100
    RATE_LIMIT_SLEEP = 0.5
    MAX_API_RETRIES = 3
    API_RETRY_DELAY = 2
    LOG_MAX_BYTES = 10 * 1024 * 1024
    LOG_BACKUP_COUNT = 5
    
    # ===================================================================
    # NOTIFICATIONS - ✅ UNCHANGED
    # ===================================================================
    ENABLE_TELEGRAM_ALERTS = False
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')
    ALERT_ON_TRADES = True
    ALERT_ON_ERRORS = True
    ALERT_ON_DAILY_PNL = True
    
    # NEW: Enhanced alerts
    ALERT_ON_SENTIMENT_ANOMALY = True
    ALERT_ON_QUALITY_FILTER = False
    
    # ===================================================================
    # DEBUG - ✅ UNCHANGED
    # ===================================================================
    DEBUG_MODE = False
    VERBOSE_LOGGING = True
    SAVE_PREDICTIONS = True
    FAST_MODE = False
    DRY_RUN = False
    
    # ===================================================================
    # NEW: FEATURE FLAGS v5.0
    # ===================================================================
    # Enable/disable specific v5.0 features for testing
    FEATURES = {
        'multi_exchange': ENABLE_MULTI_EXCHANGE,
        'multi_timeframe': ENABLE_MULTI_TIMEFRAME,
        'sentiment_analysis': ENABLE_SENTIMENT_ANALYSIS,
        'ensemble_ml': ENABLE_ENSEMBLE_ML,
        'correlation_filter': ENABLE_CORRELATION_FILTER,
        'volatility_adjustment': ENABLE_VOLATILITY_ADJUSTMENT,
        'quality_filter': ENABLE_QUALITY_FILTER,
    }

S I G N A L _ C O N F I D E N C E _ T H R E S H O L D   =   0 . 2 5 
 M I N _ A T R _ P C T   =   0 . 0 0 1 
 M L _ C O N F I D E N C E _ T H R E S H O L D   =   0 . 4 0 
 M I N _ Q U A L I T Y _ S C O R E   =   2 0 
 E N A B L E _ C O R R E L A T I O N _ F I L T E R   =   F a l s e 
 E N A B L E _ Q U A L I T Y _ F I L T E R   =   F a l s e  
 