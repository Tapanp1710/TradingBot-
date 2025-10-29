# """
# Production Trading Bot Configuration v5.0 - BALANCED FOR ACTUAL TRADING
# Optimized for profitability with reasonable trade frequency
# All features enabled with balanced thresholds
# """
# import os

# class Config:
#     """Complete bot configuration - Balanced for real trading"""
    
#     # ===================================================================
#     # VERSION
#     # ===================================================================
#     BOT_VERSION = "5.0.0"
#     CONFIG_VERSION = "5.0"
    
#     # ===================================================================
#     # EXCHANGE
#     # ===================================================================
#     EXCHANGE = "binance"
#     API_KEY = os.getenv('EXCHANGE_API_KEY', '')
#     API_SECRET = os.getenv('EXCHANGE_API_SECRET', '')
#     PAPER_TRADING = True
    
#     # ===================================================================
#     # MULTI-EXCHANGE SUPPORT
#     # ===================================================================
#     ENABLE_MULTI_EXCHANGE = False
#     EXCHANGES_LIST = [(EXCHANGE, API_KEY, API_SECRET)]
#     MIN_ARBITRAGE_PROFIT = 0.005
    
#     # ===================================================================
#     # CAPITAL & RISK - BALANCED
#     # ===================================================================
#     STARTING_CAPITAL = 200
#     INITIAL_CAPITAL = 200
#     MAX_RISK_PER_TRADE = 0.02
#     MAX_PORTFOLIO_RISK = 0.10
#     MAX_OPEN_POSITIONS = 12                 # 🔴 12 positions for more opportunities
#     MAX_POSITION_PCT = 0.12                 # 7% per position
#     MAX_POSITION_PCT_BEAR = 0.05
#     MAX_POSITION_PCT_NEUTRAL = 0.06
#     MIN_POSITION_USD = 75                   # 🔴 Lower minimum to $75
#     MIN_CAPITAL_USD = 150
#     USE_KELLY_CRITERION = False
#     KELLY_FRACTION = 0.25
    
#     # Risk Manager v5.0 Features - LESS STRICT
#     ENABLE_CORRELATION_FILTER = False       # 🔴 OFF - too restrictive
#     MAX_CORRELATED_POSITIONS = 5
#     CORRELATION_THRESHOLD = 0.80
#     ENABLE_VOLATILITY_ADJUSTMENT = False    # 🔴 OFF - too restrictive
#     MAX_DRAWDOWN_PCT = 0.15
    
#     # ===================================================================
#     # POSITION MANAGEMENT
#     # ===================================================================
#     MAX_POSITION_HOURS = 48
#     STALE_BAND_ATR_MULT = 2.0
#     MIN_ATR_PCT = 0.0015                    # 🔴 0.15% - More flexible (was 0.3%)
#     NEUTRAL_REGIME_MIN_ATR_PCT = 0.002
#     NEUTRAL_REGIME_CONFIDENCE_ADJUST = -0.05
#     ENABLE_DYNAMIC_CAPACITY = True
    
#     # ===================================================================
#     # MARKET FILTER - RELAXED
#     # ===================================================================
#     ENABLE_MARKET_FILTER = False            # 🔴 OFF - blocks too many trades
#     MARKET_FILTER_ENABLED = False
#     MIN_FEAR_GREED_INDEX = 15               # Wider range
#     MAX_FEAR_GREED_INDEX = 85               # Wider range
#     MIN_BTC_VOLATILITY = 0.3
#     AUTO_PAUSE_ON_BEAR_MARKET = True
#     BEAR_DETECTION_THRESHOLD = -0.25
    
#     # ===================================================================
#     # STOP LOSS & TAKE PROFIT - BALANCED
#     # ===================================================================
#     USE_ATR_EXITS = True
#     ATR_PERIOD = 14
#     ATR_SL_MULT = 1.4                       # 1.4x ATR
#     ATR_TP_MULT = 2.8                       # 2.8x ATR (2:1 R/R)
#     MAX_SL_PCT = 0.035                      # 3.5% max
#     MAX_TP_PCT = 0.12                       # 12% max
#     FALLBACK_STOP_LOSS_PCT = 0.02
#     FALLBACK_TAKE_PROFIT_PCT = 0.06
    
#     # ===================================================================
#     # TRAILING STOPS
#     # ===================================================================
#     ENABLE_ATR_TRAILING = True
#     TRAIL_ACTIVATE_ATR_MULT = 1.8
#     TRAIL_DISTANCE_ATR_MULT = 0.9
    
#     # ===================================================================
#     # PARTIAL TAKE PROFIT
#     # ===================================================================
#     ENABLE_PARTIAL_TP = True
#     PARTIAL_TP_PCT = 0.50
#     PARTIAL_TP_TRIGGER_ATR_MULT = 1.5
    
#     # ===================================================================
#     # DAILY LOSS PROTECTION
#     # ===================================================================
#     ENABLE_DAILY_LOSS_CAP = True
#     MAX_DAILY_LOSS_PCT = 0.03
#     MAX_DAILY_LOSS_AMOUNT = 450
    
#     # ===================================================================
#     # MULTI-TIMEFRAME - OFF (Too Strict)
#     # ===================================================================
#     ENABLE_MULTI_TIMEFRAME = False          # 🔴 OFF - requires alignment on both TFs
#     TIMEFRAMES = ['1h']
#     TIMEFRAME_WEIGHTS = [1.0]
    
#     # ===================================================================
#     # SIGNAL SETTINGS - 🔴 BALANCED FOR TRADES
#     # ===================================================================
#     SIGNAL_CONFIDENCE_THRESHOLD = 0.45    # 🔴 48% - Lower threshold (was 60%)
#     HIGH_CONFIDENCE_THRESHOLD = 0.65
#     LOW_CONFIDENCE_THRESHOLD = 0.40
#     MIN_QUALITY_SCORE = 45                  # 🔴 45 - Lower quality bar (was 60)
    
#     # RSI - Slightly wider bands
#     RSI_PERIOD = 14
#     RSI_OVERSOLD = 35                       # 35 instead of 30
#     RSI_OVERBOUGHT = 65                     # 65 instead of 70
    
#     # MACD
#     MACD_FAST = 12
#     MACD_SLOW = 26
#     MACD_SIGNAL = 9
    
#     # Bollinger Bands
#     BB_PERIOD = 20
#     BB_STD = 2
    
#     # ===================================================================
#     # LOSS STREAK DETECTION - BALANCED
#     # ===================================================================
#     ENABLE_STREAK_DETECTION = True
#     MAX_CONSECUTIVE_LOSSES = 4              # 4 losses (was 3)
#     COOLDOWN_AFTER_LOSSES_HOURS = 1         # 1 hour cooldown
#     PREVENT_REVENGE_TRADING = True
#     REVENGE_TRADE_COOLDOWN_MINS = 20        # 20 minutes
#     CONSECUTIVE_LOSS_LIMIT = 4
#     MIN_WIN_RATE_TO_TRADE = 0.35            # 35% minimum (was 40%)
    
#     # ===================================================================
#     # EMERGENCY EXIT - ENABLED
#     # ===================================================================
#     EMERGENCY_EXIT_ENABLED = True
#     EMERGENCY_LOSS_PCT = 0.12               # 12% portfolio loss
#     EMERGENCY_CLOSE_ALL = True
#     EMERGENCY_CHECK_INTERVAL = 300
#     BEAR_SENTIMENT_THRESHOLD = -0.35
#     BEAR_FEAR_INDEX = 20
#     BEAR_BTC_DROP = -12
#     MIN_BEAR_SIGNALS = 2
#     PAUSE_DURATION_HOURS = 3
#     MIN_EMERGENCY_WAIT_HOURS = 12
#     AUTO_RESUME_ENABLED = True
    
#     # ===================================================================
#     # FEES & SLIPPAGE
#     # ===================================================================
#     TRADING_FEE = 0.001
#     INCLUDE_SLIPPAGE = True
#     SLIPPAGE_RATE = 0.0005
#     APPLY_INDIAN_TAX = True
#     CAPITAL_GAINS_TAX = 0.30
#     TDS_RATE = 0.01
    
#     # ===================================================================
#     # WATCHLISTS - EXPANDED
#     # ===================================================================
#     USE_ROTATING_WATCHLISTS = True
#     WATCHLIST_BEAR = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT']
#     WATCHLIST_A = [
#         'BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'SOL/USDT',
#         'XRP/USDT', 'AVAX/USDT', 'ADA/USDT', 'MATIC/USDT'
#     ]
#     WATCHLIST_B = [
#         'DOT/USDT', 'LINK/USDT', 'ATOM/USDT', 'UNI/USDT',
#         'ARB/USDT', 'OP/USDT', 'LTC/USDT', 'DOGE/USDT'
#     ]
#     WATCHLIST_C = [
#         'INJ/USDT', 'SUI/USDT', 'FET/USDT', 'NEAR/USDT', 'TIA/USDT'
#     ]
#     WATCHLIST = WATCHLIST_A + WATCHLIST_B + WATCHLIST_C
#     GROUP_SCAN_OFFSET = 12                  # 12 second rotation
    
#     # ===================================================================
#     # ML & ONLINE LEARNING - BALANCED
#     # ===================================================================
#     ENABLE_ONLINE_LEARNING = False
#     ML_ENABLED = True
#     ML_MODEL_TO_USE = 'ensemble'
#     ML_CONFIDENCE_THRESHOLD = 0.48          # 🔴 48% - Lower ML threshold (was 60%)
#     ML_SIGNAL_WEIGHT = 0.35                 # 35% weight
#     BEARISH_CONFIDENCE_BOOST = 0.10
    
#     ENABLE_ENSEMBLE_ML = True
#     ENSEMBLE_MODELS = ['random_forest', 'lightgbm', 'xgboost']
#     ENSEMBLE_WEIGHTS = {'rf': 0.35, 'lgb': 0.35, 'xgb': 0.30}
    
#     # Online learning parameters
#     ONLINE_LEARNING_METHOD = 'sgd'
#     UPDATE_MODEL_PER_TRADE = True
#     MIN_TRADES_BEFORE_UPDATE = 6
#     BATCH_UPDATE_SIZE = 12
#     ONLINE_LEARNING_RATE = 0.01
#     MOMENTUM = 0.9
#     DECAY_RATE = 0.95
#     SAVE_MODEL_AFTER_UPDATES = 50
#     ONLINE_MODEL_PATH = 'ml/models/online_model.pkl'
#     MAX_PERFORMANCE_DROP = 0.15
#     ENABLE_MODEL_ROLLBACK = True
#     VALIDATION_WINDOW = 20
#     ML_RETRAIN_INTERVAL = 100
#     ML_MIN_SAMPLES = 50
#     ML_FEATURE_SET = 'enhanced'
#     USE_FEATURE_ENGINEERING = True
    
#     # ===================================================================
#     # SENTIMENT ANALYSIS - OFF (Can block trades)
#     # ===================================================================
#     ENABLE_SENTIMENT_ANALYSIS = False       # 🔴 OFF - can be slow/unreliable
#     SENTIMENT_WEIGHT = 0.10
#     SENTIMENT_CACHE_DURATION = 600
#     SENTIMENT_SOURCES = ['fear_greed']
#     SENTIMENT_BULLISH_THRESHOLD = 0.3
#     SENTIMENT_BEARISH_THRESHOLD = -0.3
#     SENTIMENT_ANOMALY_THRESHOLD = 5.0
    
#     # ===================================================================
#     # ADVANCED FEATURES - SELECTIVE
#     # ===================================================================
#     ENABLE_ADAPTIVE_SIZING = True
#     HIGH_CONFIDENCE_MULTIPLIER = 1.15
#     LOW_CONFIDENCE_MULTIPLIER = 0.80
#     ENABLE_ARBITRAGE = False
#     MAX_ARBITRAGE_CAPITAL = 0.15
#     MIN_ARBITRAGE_VOLUME = 50000
#     ENABLE_QUALITY_FILTER = True
#     MIN_SIGNAL_QUALITY_GRADE = 'C'          # 🔴 Accept C grade (was B)
    
#     # ===================================================================
#     # TIMING
#     # ===================================================================
#     SCAN_INTERVAL = 25                      # 25 seconds (faster)
#     ENABLE_TIME_FILTERS = False
#     TRADING_START_HOUR = 0
#     TRADING_END_HOUR = 24
#     ENABLE_OPPORTUNISTIC_SCAN = True
#     OPPORTUNISTIC_SCAN_INTERVAL = 180
#     TOP_MOVER_THRESHOLD = 0.025
#     ARBITRAGE_INTERVAL = 60
    
#     # ===================================================================
#     # LOGGING
#     # ===================================================================
#     LOG_LEVEL = "INFO"
#     LOG_FILE = "logs/bot.log"
#     SAVE_TRADE_HISTORY = True
#     TRADE_HISTORY_FILE = "trade_history.csv"
#     PERFORMANCE_FILE = "data/performance.csv"
#     BACKTEST_RESULTS_FILE = "data/backtest_results.csv"
#     LOG_SIGNAL_DETAILS = True
#     LOG_SENTIMENT_SCORES = False
#     LOG_ML_PREDICTIONS = True
    
#     # ===================================================================
#     # MONITORING
#     # ===================================================================
#     ENABLE_HEARTBEAT = True
#     HEARTBEAT_INTERVAL = 600
#     ENABLE_PERFORMANCE_MONITOR = True
#     PERFORMANCE_LOG_INTERVAL = 3600
#     MAX_DRAWDOWN_ALERT = 0.12
#     MIN_WIN_RATE_ALERT = 0.40
#     IDLE_CAPACITY_ALERT_SCANS = 150
#     FLAT_PNL_ALERT_SCANS = 75
#     MIN_CAPACITY_UTILIZATION = 0.25
#     AUTO_PAUSE_ON_DRAWDOWN = 0.15
#     AUTO_PAUSE_ON_LOSSES = 6
    
#     # ===================================================================
#     # SYSTEM
#     # ===================================================================
#     ENABLE_MEMORY_MANAGEMENT = True
#     GC_INTERVAL = 100
#     MAX_MEMORY_MB = 500
#     MAX_SCANS_PER_CYCLE = 100
#     RATE_LIMIT_DELAY = 0.1
#     ENABLE_GARBAGE_COLLECTION = True
#     GC_COLLECTION_INTERVAL = 100
#     RATE_LIMIT_SLEEP = 0.5
#     MAX_API_RETRIES = 3
#     API_RETRY_DELAY = 2
#     LOG_MAX_BYTES = 10 * 1024 * 1024
#     LOG_BACKUP_COUNT = 5
    
#     # ===================================================================
#     # NOTIFICATIONS
#     # ===================================================================
#     ENABLE_TELEGRAM_ALERTS = False
#     TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
#     TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')
#     ALERT_ON_TRADES = True
#     ALERT_ON_ERRORS = True
#     ALERT_ON_DAILY_PNL = True
#     ALERT_ON_SENTIMENT_ANOMALY = False
#     ALERT_ON_QUALITY_FILTER = False
    
#     # ===================================================================
#     # DEBUG
#     # ===================================================================
#     DEBUG_MODE = False
#     VERBOSE_LOGGING = False
#     SAVE_PREDICTIONS = True
#     FAST_MODE = False
#     DRY_RUN = False
    
#     # ===================================================================
#     # FEATURE FLAGS v5.0
#     # ===================================================================
#     FEATURES = {
#         'multi_exchange': False,
#         'multi_timeframe': False,           # OFF - too strict
#         'sentiment_analysis': False,        # OFF - can be slow
#         'ensemble_ml': True,
#         'correlation_filter': False,        # OFF - too strict
#         'volatility_adjustment': False,     # OFF - too strict
#         'quality_filter': True,
#     }
#     # ===================================================================
#     # BOUNCE TRADING - RESERVED SLOT FEATURE
#     # ===================================================================
#     ENABLE_BOUNCE_TRADING = True
#     RESERVED_SLOTS_FOR_BOUNCE = 1           # Always keep 1 slot for bounce trades
#     BOUNCE_LOOKBACK_DAYS = 7                # 7 days for weekly low
#     BOUNCE_THRESHOLD_PCT = 0.02             # Buy if within 2% of weekly low
#     BOUNCE_STOP_LOSS_PCT = 0.08             # 8% stop loss (higher than normal)
#     BOUNCE_NO_TAKE_PROFIT = True            # No fixed TP - only trailing
#     BOUNCE_TRAIL_ACTIVATE_PCT = 0.01        # Start trailing after 1% profit
#     BOUNCE_TRAIL_DISTANCE_PCT = 0.015       # Trail 1.5% below peak
#     BOUNCE_MIN_POSITION_SIZE = 150          # Bigger position for bounce trades
"""
Optimized for $200 Capital - WORKING VERSION
"""
import os

class Config:
    """Small capital configuration - $200"""
    
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
    # MULTI-EXCHANGE SUPPORT
    # ===================================================================
    ENABLE_MULTI_EXCHANGE = False
    EXCHANGES_LIST = [(EXCHANGE, API_KEY, API_SECRET)]
    MIN_ARBITRAGE_PROFIT = 0.005
    
    # ===================================================================
    # CAPITAL & RISK - 🔴 FIXED FOR $200
    # ===================================================================
    STARTING_CAPITAL = 200
    INITIAL_CAPITAL = 200
    MAX_RISK_PER_TRADE = 0.02
    MAX_PORTFOLIO_RISK = 0.10
    MAX_OPEN_POSITIONS = 4                  # 🔴 4 positions (not 12!)
    MAX_POSITION_PCT = 0.22                 # 🔴 22% = $44 per position
    MAX_POSITION_PCT_BEAR = 0.18
    MAX_POSITION_PCT_NEUTRAL = 0.20
    MIN_POSITION_USD = 35                   # 🔴 $35 minimum (was $75!)
    MIN_CAPITAL_USD = 50
    USE_KELLY_CRITERION = False
    KELLY_FRACTION = 0.25
    
    # Risk Manager
    ENABLE_CORRELATION_FILTER = False
    MAX_CORRELATED_POSITIONS = 4
    CORRELATION_THRESHOLD = 0.80
    ENABLE_VOLATILITY_ADJUSTMENT = False
    MAX_DRAWDOWN_PCT = 0.20
    
    # ===================================================================
    # POSITION MANAGEMENT
    # ===================================================================
    MAX_POSITION_HOURS = 48
    STALE_BAND_ATR_MULT = 2.0
    MIN_ATR_PCT = 0.0015
    NEUTRAL_REGIME_MIN_ATR_PCT = 0.002
    NEUTRAL_REGIME_CONFIDENCE_ADJUST = -0.05
    ENABLE_DYNAMIC_CAPACITY = True
    
    # ===================================================================
    # MARKET FILTER
    # ===================================================================
    ENABLE_MARKET_FILTER = False
    MARKET_FILTER_ENABLED = False
    MIN_FEAR_GREED_INDEX = 15
    MAX_FEAR_GREED_INDEX = 85
    MIN_BTC_VOLATILITY = 0.3
    AUTO_PAUSE_ON_BEAR_MARKET = True
    BEAR_DETECTION_THRESHOLD = -0.25
    
    # ===================================================================
    # STOP LOSS & TAKE PROFIT
    # ===================================================================
    USE_ATR_EXITS = True
    ATR_PERIOD = 14
    ATR_SL_MULT = 1.2                       # Tighter
    ATR_TP_MULT = 3.5                       # Bigger target
    MAX_SL_PCT = 0.03
    MAX_TP_PCT = 0.10
    FALLBACK_STOP_LOSS_PCT = 0.02
    FALLBACK_TAKE_PROFIT_PCT = 0.07
    
    # ===================================================================
    # TRAILING STOPS
    # ===================================================================
    ENABLE_ATR_TRAILING = True
    TRAIL_ACTIVATE_ATR_MULT = 1.5
    TRAIL_DISTANCE_ATR_MULT = 0.8
    
    # ===================================================================
    # PARTIAL TAKE PROFIT
    # ===================================================================
    ENABLE_PARTIAL_TP = False               # OFF for small capital
    PARTIAL_TP_PCT = 0.50
    PARTIAL_TP_TRIGGER_ATR_MULT = 1.5
    
    # ===================================================================
    # DAILY LOSS PROTECTION
    # ===================================================================
    ENABLE_DAILY_LOSS_CAP = True
    MAX_DAILY_LOSS_PCT = 0.05
    MAX_DAILY_LOSS_AMOUNT = 10              # $10 not $450!
    
    # ===================================================================
    # MULTI-TIMEFRAME
    # ===================================================================
    ENABLE_MULTI_TIMEFRAME = False
    TIMEFRAMES = ['1h']
    TIMEFRAME_WEIGHTS = [1.0]
    
    # ===================================================================
    # SIGNAL SETTINGS
    # ===================================================================
    SIGNAL_CONFIDENCE_THRESHOLD = 0.50      # 42%
    HIGH_CONFIDENCE_THRESHOLD = 0.65
    LOW_CONFIDENCE_THRESHOLD = 0.35
    MIN_QUALITY_SCORE = 42
    
    RSI_PERIOD = 14
    RSI_OVERSOLD = 35
    RSI_OVERBOUGHT = 65
    
    MACD_FAST = 12
    MACD_SLOW = 26
    MACD_SIGNAL = 9
    
    BB_PERIOD = 20
    BB_STD = 2
    
    # ===================================================================
    # LOSS STREAK DETECTION
    # ===================================================================
    ENABLE_STREAK_DETECTION = True
    MAX_CONSECUTIVE_LOSSES = 3
    COOLDOWN_AFTER_LOSSES_HOURS = 1
    PREVENT_REVENGE_TRADING = True
    REVENGE_TRADE_COOLDOWN_MINS = 30
    CONSECUTIVE_LOSS_LIMIT = 3
    MIN_WIN_RATE_TO_TRADE = 0.30
    
    # ===================================================================
    # EMERGENCY EXIT
    # ===================================================================
    EMERGENCY_EXIT_ENABLED = True
    EMERGENCY_LOSS_PCT = 0.15
    EMERGENCY_CLOSE_ALL = True
    EMERGENCY_CHECK_INTERVAL = 300
    BEAR_SENTIMENT_THRESHOLD = -0.35
    BEAR_FEAR_INDEX = 20
    BEAR_BTC_DROP = -12
    MIN_BEAR_SIGNALS = 2
    PAUSE_DURATION_HOURS = 2
    MIN_EMERGENCY_WAIT_HOURS = 6
    AUTO_RESUME_ENABLED = True
    
    # ===================================================================
    # FEES & SLIPPAGE
    # ===================================================================
    TRADING_FEE = 0.001
    INCLUDE_SLIPPAGE = True
    SLIPPAGE_RATE = 0.0005
    APPLY_INDIAN_TAX = True
    CAPITAL_GAINS_TAX = 0.30
    TDS_RATE = 0.01
    
    # ===================================================================
    # WATCHLISTS
    # ===================================================================
    USE_ROTATING_WATCHLISTS = True
    WATCHLIST_BEAR = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT']
    WATCHLIST_A = [
        'BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'SOL/USDT',
        'XRP/USDT', 'AVAX/USDT'
    ]
    WATCHLIST_B = [
        'DOT/USDT', 'LINK/USDT', 'ATOM/USDT', 'MATIC/USDT',
        'ARB/USDT', 'OP/USDT'
    ]
    WATCHLIST_C = [
        'INJ/USDT', 'SUI/USDT', 'FET/USDT', 'NEAR/USDT'
    ]
    WATCHLIST = WATCHLIST_A + WATCHLIST_B + WATCHLIST_C
    GROUP_SCAN_OFFSET = 15
    
    # ===================================================================
    # ML & ONLINE LEARNING
    # ===================================================================
    ENABLE_ONLINE_LEARNING = False
    ML_ENABLED = True
    ML_MODEL_TO_USE = 'ensemble'
    ML_CONFIDENCE_THRESHOLD = 0.45
    ML_SIGNAL_WEIGHT = 0.35
    BEARISH_CONFIDENCE_BOOST = 0.10
    
    ENABLE_ENSEMBLE_ML = True
    ENSEMBLE_MODELS = ['random_forest', 'lightgbm', 'xgboost']
    ENSEMBLE_WEIGHTS = {'rf': 0.35, 'lgb': 0.35, 'xgb': 0.30}
    
    ONLINE_LEARNING_METHOD = 'sgd'
    UPDATE_MODEL_PER_TRADE = True
    MIN_TRADES_BEFORE_UPDATE = 6
    BATCH_UPDATE_SIZE = 12
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
    ML_FEATURE_SET = 'enhanced'
    USE_FEATURE_ENGINEERING = True
    
    # ===================================================================
    # SENTIMENT ANALYSIS
    # ===================================================================
    ENABLE_SENTIMENT_ANALYSIS = False
    SENTIMENT_WEIGHT = 0.10
    SENTIMENT_CACHE_DURATION = 600
    SENTIMENT_SOURCES = ['fear_greed']
    SENTIMENT_BULLISH_THRESHOLD = 0.3
    SENTIMENT_BEARISH_THRESHOLD = -0.3
    SENTIMENT_ANOMALY_THRESHOLD = 5.0
    
    # ===================================================================
    # ADVANCED FEATURES
    # ===================================================================
    ENABLE_ADAPTIVE_SIZING = True
    HIGH_CONFIDENCE_MULTIPLIER = 1.10
    LOW_CONFIDENCE_MULTIPLIER = 0.85
    ENABLE_ARBITRAGE = False
    MAX_ARBITRAGE_CAPITAL = 0.15
    MIN_ARBITRAGE_VOLUME = 50000
    ENABLE_QUALITY_FILTER = True
    MIN_SIGNAL_QUALITY_GRADE = 'D'
    
    # ===================================================================
    # TIMING
    # ===================================================================
    SCAN_INTERVAL = 20
    ENABLE_TIME_FILTERS = False
    TRADING_START_HOUR = 0
    TRADING_END_HOUR = 24
    ENABLE_OPPORTUNISTIC_SCAN = False
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
    LOG_SIGNAL_DETAILS = True
    LOG_SENTIMENT_SCORES = False
    LOG_ML_PREDICTIONS = True
    
    # ===================================================================
    # MONITORING
    # ===================================================================
    ENABLE_HEARTBEAT = True
    HEARTBEAT_INTERVAL = 600
    ENABLE_PERFORMANCE_MONITOR = True
    PERFORMANCE_LOG_INTERVAL = 3600
    MAX_DRAWDOWN_ALERT = 0.15
    MIN_WIN_RATE_ALERT = 0.35
    IDLE_CAPACITY_ALERT_SCANS = 150
    FLAT_PNL_ALERT_SCANS = 75
    MIN_CAPACITY_UTILIZATION = 0.20
    AUTO_PAUSE_ON_DRAWDOWN = 0.18
    AUTO_PAUSE_ON_LOSSES = 5
    
    # ===================================================================
    # SYSTEM
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
    VERBOSE_LOGGING = False
    SAVE_PREDICTIONS = True
    FAST_MODE = False
    DRY_RUN = False
    
    # ===================================================================
    # FEATURE FLAGS
    # ===================================================================
    FEATURES = {
        'multi_exchange': False,
        'multi_timeframe': False,
        'sentiment_analysis': False,
        'ensemble_ml': True,
        'correlation_filter': False,
        'volatility_adjustment': False,
        'quality_filter': True,
    }
    
    # ===================================================================
    # BOUNCE TRADING - OFF
    # ===================================================================
    ENABLE_BOUNCE_TRADING = False
    RESERVED_SLOTS_FOR_BOUNCE = 0
    BOUNCE_LOOKBACK_DAYS = 7
    BOUNCE_THRESHOLD_PCT = 0.02
    BOUNCE_STOP_LOSS_PCT = 0.08
    BOUNCE_NO_TAKE_PROFIT = True
    BOUNCE_TRAIL_ACTIVATE_PCT = 0.01
    BOUNCE_TRAIL_DISTANCE_PCT = 0.015
    BOUNCE_MIN_POSITION_SIZE = 150
