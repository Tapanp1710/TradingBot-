"""
Production Trading Bot Configuration - v4.4 FINAL CORRECTED
October 28, 2025 - All Critical Fixes Applied
"""
import os


class Config:
    """Bot configuration class - OPTIMIZED FOR PROFITABILITY"""
    
    # ===================================================================
    # VERSION
    # ===================================================================
    BOT_VERSION = "4.4.0"
    CONFIG_VERSION = "4.4"
    
    # ===================================================================
    # EXCHANGE
    # ===================================================================
    EXCHANGE = "binance"
    API_KEY = os.getenv('EXCHANGE_API_KEY', '')
    API_SECRET = os.getenv('EXCHANGE_API_SECRET', '')
    PAPER_TRADING = True
    
    # ===================================================================
    # CAPITAL & RISK - ✅ OPTIMIZED
    # ===================================================================
    STARTING_CAPITAL = 15000
    INITIAL_CAPITAL = 15000
    MAX_RISK_PER_TRADE = 0.02
    MAX_PORTFOLIO_RISK = 0.08
    
    # ✅ CRITICAL FIX: Reduced from 12 to 8 for better management
    MAX_OPEN_POSITIONS = 8  # FIXED: Was 12, now 8
    
    # ✅ CRITICAL FIX: Reduced position sizing for safety
    MAX_POSITION_PCT = 0.06  # FIXED: Was 0.08, now 6% (safer)
    MAX_POSITION_PCT_BEAR = 0.04  # FIXED: Was 0.05, now 4%
    MAX_POSITION_PCT_NEUTRAL = 0.055  # FIXED: Was 0.07, now 5.5%
    
    MIN_POSITION_USD = 50
    MIN_CAPITAL_USD = 100
    USE_KELLY_CRITERION = False
    KELLY_FRACTION = 0.25
    
    # ===================================================================
    # POSITION MANAGEMENT - ✅ ENHANCED
    # ===================================================================
    MAX_POSITION_HOURS = 24
    STALE_BAND_ATR_MULT = 1.5
    
    # ✅ OPTIMIZED: More selective entry criteria
    MIN_ATR_PCT = 0.004  # FIXED: Was 0.003, raised to 0.4% for better opportunities
    NEUTRAL_REGIME_MIN_ATR_PCT = 0.003  # Slightly lower for neutral markets
    NEUTRAL_REGIME_CONFIDENCE_ADJUST = -0.05
    ENABLE_DYNAMIC_CAPACITY = True
    
    # ===================================================================
    # MARKET FILTER - ✅ ENHANCED
    # ===================================================================
    ENABLE_MARKET_FILTER = True
    MARKET_FILTER_ENABLED = True
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
    
    # ✅ CRITICAL FIX: Better risk/reward ratio
    ATR_SL_MULT = 1.2  # FIXED: Was 1.5, tightened to 1.2 for smaller losses
    ATR_TP_MULT = 3.6  # FIXED: Was 3.0, raised to 3.6 for better R:R (3:1)
    
    MAX_SL_PCT = 0.04  # FIXED: Was 0.05, now max 4% stop loss
    MAX_TP_PCT = 0.15
    FALLBACK_STOP_LOSS_PCT = 0.025  # FIXED: Was 0.03, now 2.5%
    FALLBACK_TAKE_PROFIT_PCT = 0.075  # FIXED: Was 0.06, now 7.5%
    
    # ===================================================================
    # TRAILING STOPS - ✅ ENHANCED
    # ===================================================================
    ENABLE_ATR_TRAILING = True
    TRAIL_ACTIVATE_ATR_MULT = 1.5  # FIXED: Was 2.0, activates sooner
    TRAIL_DISTANCE_ATR_MULT = 0.8  # FIXED: Was 1.0, tighter trailing
    
    # ===================================================================
    # PARTIAL TAKE PROFIT - ✅ ENABLED
    # ===================================================================
    ENABLE_PARTIAL_TP = True
    PARTIAL_TP_PCT = 0.50
    PARTIAL_TP_TRIGGER_ATR_MULT = 1.5  # FIXED: Was 2.0, takes profit sooner
    
    # ===================================================================
    # DAILY LOSS PROTECTION - ✅ ENABLED
    # ===================================================================
    ENABLE_DAILY_LOSS_CAP = True
    MAX_DAILY_LOSS_PCT = 0.02
    MAX_DAILY_LOSS_AMOUNT = 300
    
    # ===================================================================
    # SIGNAL SETTINGS - ✅ OPTIMIZED
    # ===================================================================
    # ✅ CRITICAL FIX: Raised confidence threshold for better entries
    SIGNAL_CONFIDENCE_THRESHOLD = 0.60  # FIXED: Was 0.55, now 60%
    HIGH_CONFIDENCE_THRESHOLD = 0.75
    LOW_CONFIDENCE_THRESHOLD = 0.60
    
    # RSI
    RSI_PERIOD = 14
    RSI_OVERSOLD = 35  # FIXED: Was 30, slightly less extreme
    RSI_OVERBOUGHT = 65  # FIXED: Was 70, slightly less extreme
    
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
    EMERGENCY_LOSS_PCT = 0.08  # FIXED: Was 0.10, now 8% triggers emergency
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
    # WATCHLISTS - ✅ UNCHANGED
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
    # ML & ONLINE LEARNING - ✅ DISABLED (Can enable when ready)
    # ===================================================================
    ENABLE_ONLINE_LEARNING = False
    ML_ENABLED = False
    ML_MODEL_TO_USE = 'lightgbm'
    ML_CONFIDENCE_THRESHOLD = 0.65
    ML_SIGNAL_WEIGHT = 0.50
    BEARISH_CONFIDENCE_BOOST = 0.10
    ONLINE_LEARNING_METHOD = 'sgd'
    ONLINE_LEARNING_RATE = 0.01
    ONLINE_BATCH_SIZE = 32
    ML_RETRAIN_INTERVAL = 100
    ML_MIN_SAMPLES = 50
    ML_FEATURE_SET = 'full'
    USE_FEATURE_ENGINEERING = True

    # ===================================================================
    # ADVANCED FEATURES - ✅ OPTIMIZED
    # ===================================================================
    ENABLE_MULTI_TIMEFRAME = False
    TIMEFRAMES = ['1h', '4h', '1d']
    TIMEFRAME_WEIGHTS = [0.5, 0.3, 0.2]
    
    ENABLE_ADAPTIVE_SIZING = True
    HIGH_CONFIDENCE_MULTIPLIER = 1.15
    LOW_CONFIDENCE_MULTIPLIER = 0.85
    
    ENABLE_ARBITRAGE = False
    MIN_ARBITRAGE_PROFIT = 0.003
    MAX_ARBITRAGE_CAPITAL = 0.15
    MIN_ARBITRAGE_VOLUME = 50000
    
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
    # LOGGING - ✅ UNCHANGED
    # ===================================================================
    LOG_LEVEL = "INFO"
    LOG_FILE = "logs/bot.log"
    SAVE_TRADE_HISTORY = True
    TRADE_HISTORY_FILE = "trade_history.csv"
    PERFORMANCE_FILE = "data/performance.csv"
    BACKTEST_RESULTS_FILE = "data/backtest_results.csv"
    
    # ===================================================================
    # MONITORING - ✅ OPTIMIZED
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
    # SYSTEM - ✅ UNCHANGED
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
    
    # ===================================================================
    # DEBUG - ✅ UNCHANGED
    # ===================================================================
    DEBUG_MODE = False
    VERBOSE_LOGGING = False
    SAVE_PREDICTIONS = True
    FAST_MODE = False
    DRY_RUN = False
