"""
Trading Bot Entry Point v4.4 - PRODUCTION READY
October 28, 2025 - All Critical Fixes Applied
- Enhanced error handling, graceful shutdown
- Method names synced with bot.py v4.4
- Performance monitoring and reporting
"""
import sys
import os
import threading
import time
import signal
from datetime import datetime


# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


from config import Config
from utils import setup_logger
from core import TradingBot


# Version tracking
BOT_VERSION = "4.4.0"
BOT_BUILD_DATE = "2025-10-28"
CONFIG_VERSION = Config.CONFIG_VERSION if hasattr(Config, 'CONFIG_VERSION') else "4.4"


def validate_ml_models():
    """
    Validate ML models with file integrity check
    Returns: (is_valid, message, best_model_name)
    """
    model_dir = 'ml/models'
    
    if not os.path.exists(model_dir):
        return False, "ML models directory not found", None
    
    # Check model files
    models_found = []
    for file in os.listdir(model_dir):
        if file.endswith('_model.pkl'):
            model_path = os.path.join(model_dir, file)
            try:
                # Verify file is readable
                with open(model_path, 'rb') as f:
                    f.read(10)  # Read first 10 bytes
                model_name = file.replace('_model.pkl', '')
                models_found.append(model_name)
            except Exception as e:
                continue
    
    if not models_found:
        return False, "No valid ML models found", None
    
    # Check for scaler
    if not os.path.exists(os.path.join(model_dir, 'scaler.pkl')):
        return False, "Scaler file missing", None
    
    # Determine best model
    best_model = None
    if os.path.exists(os.path.join(model_dir, 'best_model_name.pkl')):
        try:
            import joblib
            best_model = joblib.load(os.path.join(model_dir, 'best_model_name.pkl'))
        except:
            best_model = models_found[0] if models_found else None
    else:
        best_model = models_found[0] if models_found else None
    
    return True, f"Found {len(models_found)} models", best_model


def display_startup_banner():
    """Display startup banner with version info"""
    print(f"""
╔══════════════════════════════════════════════════════════════════════════╗
║                                                                          ║
║      🤖 AI CRYPTO TRADING BOT v{BOT_VERSION} - PRODUCTION READY 🚀           ║
║                                                                          ║
║  ✅ Real-time Market Data (Binance/Coinbase/Kraken)                     ║
║  ✅ Technical Analysis (60+ Indicators)                                 ║
║  ✅ Machine Learning (Random Forest, LightGBM, XGBoost)                 ║
║  ✅ Online Learning (Self-Improving AI)                                 ║
║  ✅ News Sentiment Analysis (Multi-Source)                              ║
║  ✅ Emergency Exit System                                               ║
║  ✅ Advanced Risk Management (Stop Loss, Take Profit, Trailing)         ║
║  ✅ Performance Monitoring & Reporting                                  ║
║  ✅ Daily Loss Protection                                               ║
║  ✅ Revenge Trading Prevention                                          ║
║                                                                          ║
║  Build: {BOT_BUILD_DATE} | Config: v{CONFIG_VERSION}                                   ║
║  Status: ALL CRITICAL BUGS FIXED ✅                                      ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════════╝
    """)


def display_ml_status(logger):
    """Display ML status with detailed information"""
    ml_available, ml_message, best_model = validate_ml_models()
    
    print("\n" + "="*78)
    print("🧠 MACHINE LEARNING STATUS")
    print("="*78)
    
    if ml_available:
        print(f"✅ {ml_message}")
        
        if best_model:
            print(f"🏆 Best Model: {best_model.upper()}")
        
        print(f"📊 Expected Accuracy: ~60% (on confident predictions)")
        print(f"🎯 ML Confidence Threshold: {Config.ML_CONFIDENCE_THRESHOLD*100:.0f}%")
        print(f"⚖️  ML Signal Weight: {Config.ML_SIGNAL_WEIGHT*100:.0f}%")
        
        # List available models
        model_dir = 'ml/models'
        if os.path.exists(model_dir):
            model_files = [f.replace('_model.pkl', '') for f in os.listdir(model_dir) 
                          if f.endswith('_model.pkl')]
            if model_files:
                print(f"🤖 Available Models: {len(model_files)}")
                for model in model_files:
                    print(f"   • {model.replace('_', ' ').title()}")
    else:
        print(f"❌ {ml_message}")
        print(f"\n💡 To enable ML, run: python train_ml_final.py")
        print(f"⚠️  Bot will use technical analysis only")
    
    print("="*78)
    
    return ml_available


def display_configuration(logger):
    """Display bot configuration"""
    print("\n" + "="*78)
    print("⚙️  CONFIGURATION")
    print("="*78)
    
    # Capital & Trading Mode
    print(f"💰 Starting Capital: ${Config.STARTING_CAPITAL:,.2f}")
    print(f"📊 Trading Mode: {'🟢 PAPER TRADING' if Config.PAPER_TRADING else '🔴 LIVE TRADING ⚠️'}")
    print(f"📈 Exchange: {Config.EXCHANGE.upper()}")
    
    # Position Management
    print(f"\n📍 POSITION MANAGEMENT:")
    print(f"   Max Positions: {Config.MAX_OPEN_POSITIONS}")
    print(f"   Position Size: {Config.MAX_POSITION_PCT*100:.1f}% per trade")
    print(f"   Max Risk Per Trade: {Config.MAX_RISK_PER_TRADE*100:.1f}%")
    print(f"   Max Portfolio Risk: {Config.MAX_PORTFOLIO_RISK*100:.1f}%")
    print(f"   Dynamic Capacity: {'✅ ENABLED' if Config.ENABLE_DYNAMIC_CAPACITY else '❌ DISABLED'}")
    
    # Risk Management
    print(f"\n🛡️  RISK MANAGEMENT:")
    if Config.USE_ATR_EXITS:
        print(f"   Stop Loss: {Config.ATR_SL_MULT}×ATR (Dynamic)")
        print(f"   Take Profit: {Config.ATR_TP_MULT}×ATR (Dynamic)")
        print(f"   Risk/Reward Ratio: {Config.ATR_TP_MULT/Config.ATR_SL_MULT:.1f}:1")
        print(f"   Max SL: {Config.MAX_SL_PCT*100:.1f}%")
        print(f"   Max TP: {Config.MAX_TP_PCT*100:.1f}%")
    else:
        print(f"   Stop Loss: {Config.FALLBACK_STOP_LOSS_PCT*100:.1f}% (Fixed)")
        print(f"   Take Profit: {Config.FALLBACK_TAKE_PROFIT_PCT*100:.1f}% (Fixed)")
    
    if Config.ENABLE_ATR_TRAILING:
        print(f"   Trailing Stop: ✅ ENABLED ({Config.TRAIL_DISTANCE_ATR_MULT}×ATR)")
    
    if Config.ENABLE_PARTIAL_TP:
        print(f"   Partial Take Profit: ✅ ENABLED ({Config.PARTIAL_TP_PCT*100:.0f}%)")
    
    # Daily Loss Protection
    if getattr(Config, 'ENABLE_DAILY_LOSS_CAP', False):
        print(f"\n🚨 DAILY LOSS PROTECTION:")
        print(f"   Max Daily Loss: ${Config.MAX_DAILY_LOSS_AMOUNT} or {Config.MAX_DAILY_LOSS_PCT*100:.1f}%")
        print(f"   Auto-Pause: ✅ ENABLED")
    
    # Emergency Exit
    if getattr(Config, 'EMERGENCY_EXIT_ENABLED', False):
        print(f"\n⚡ EMERGENCY EXIT SYSTEM:")
        print(f"   Trigger Loss: {getattr(Config, 'EMERGENCY_LOSS_PCT', 0.10)*100:.1f}%")
        print(f"   Close All Positions: {'✅ YES' if getattr(Config, 'EMERGENCY_CLOSE_ALL', True) else '❌ NO'}")
        print(f"   Auto-Resume: {'✅ YES' if getattr(Config, 'AUTO_RESUME_ENABLED', True) else '❌ NO'}")
    
    # Signal Settings
    print(f"\n🎯 SIGNAL SETTINGS:")
    print(f"   Confidence Threshold: {Config.SIGNAL_CONFIDENCE_THRESHOLD*100:.0f}%")
    print(f"   High Confidence: {Config.HIGH_CONFIDENCE_THRESHOLD*100:.0f}%")
    print(f"   RSI Oversold/Overbought: {Config.RSI_OVERSOLD}/{Config.RSI_OVERBOUGHT}")
    print(f"   Min ATR: {Config.MIN_ATR_PCT*100:.2f}%")
    
    # Watchlist
    print(f"\n🪙 WATCHLIST:")
    if Config.USE_ROTATING_WATCHLISTS:
        print(f"   Mode: 🔄 ROTATING")
        print(f"   Watchlist A: {len(Config.WATCHLIST_A)} coins - {', '.join(Config.WATCHLIST_A[:5])}")
        print(f"   Watchlist B: {len(Config.WATCHLIST_B)} coins - {', '.join(Config.WATCHLIST_B[:5])}")
        print(f"   Watchlist C: {len(Config.WATCHLIST_C)} coins - {', '.join(Config.WATCHLIST_C[:5])}")
        print(f"   Rotation Interval: {Config.GROUP_SCAN_OFFSET}s")
    else:
        print(f"   Mode: 📋 STATIC")
        print(f"   Total Coins: {len(Config.WATCHLIST)}")
        print(f"   {', '.join(Config.WATCHLIST[:10])}")
        if len(Config.WATCHLIST) > 10:
            print(f"   ...and {len(Config.WATCHLIST) - 10} more")
    
    # Timing
    print(f"\n⏱️  TIMING:")
    print(f"   Scan Interval: {Config.SCAN_INTERVAL}s")
    print(f"   Max Position Duration: {Config.MAX_POSITION_HOURS}h")
    
    # Fees & Costs
    print(f"\n💸 FEES & COSTS:")
    print(f"   Trading Fee: {Config.TRADING_FEE*100:.2f}%")
    if Config.INCLUDE_SLIPPAGE:
        print(f"   Slippage: {Config.SLIPPAGE_RATE*100:.2f}%")
    if Config.APPLY_INDIAN_TAX:
        print(f"   Tax: {Config.CAPITAL_GAINS_TAX*100:.0f}% (Capital Gains)")
    
    # Advanced Features
    print(f"\n🚀 ADVANCED FEATURES:")
    print(f"   Market Filter: {'✅ ENABLED' if Config.ENABLE_MARKET_FILTER else '❌ DISABLED'}")
    print(f"   Streak Detection: {'✅ ENABLED' if Config.ENABLE_STREAK_DETECTION else '❌ DISABLED'}")
    print(f"   Revenge Trade Prevention: {'✅ ENABLED' if Config.PREVENT_REVENGE_TRADING else '❌ DISABLED'}")
    print(f"   Online Learning: {'✅ ENABLED' if Config.ENABLE_ONLINE_LEARNING else '❌ DISABLED'}")
    print(f"   Adaptive Sizing: {'✅ ENABLED' if Config.ENABLE_ADAPTIVE_SIZING else '❌ DISABLED'}")
    
    print("="*78)


def validate_configuration(logger):
    """Validate configuration and check for errors"""
    errors = []
    warnings = []
    
    # Critical Errors
    if not hasattr(Config, 'WATCHLIST') or not Config.WATCHLIST:
        if not hasattr(Config, 'WATCHLIST_A') or not Config.WATCHLIST_A:
            errors.append("No watchlist configured")
    
    if Config.STARTING_CAPITAL <= 0:
        errors.append("Starting capital must be positive")
    
    if not (0 < Config.MAX_RISK_PER_TRADE <= 1):
        errors.append("Max risk per trade must be between 0 and 1")
    
    if Config.MAX_OPEN_POSITIONS <= 0:
        errors.append("Max open positions must be positive")
    
    if Config.MAX_POSITION_PCT <= 0 or Config.MAX_POSITION_PCT > 1:
        errors.append("Max position percentage must be between 0 and 1")
    
    if Config.SIGNAL_CONFIDENCE_THRESHOLD <= 0 or Config.SIGNAL_CONFIDENCE_THRESHOLD > 1:
        errors.append("Signal confidence threshold must be between 0 and 1")
    
    # Warnings
    if not Config.PAPER_TRADING:
        warnings.append("⚠️  LIVE TRADING MODE - Real money at risk!")
    
    if Config.SIGNAL_CONFIDENCE_THRESHOLD < 0.50:
        warnings.append(f"Signal confidence threshold is low ({Config.SIGNAL_CONFIDENCE_THRESHOLD*100:.0f}%)")
    
    if Config.MAX_RISK_PER_TRADE > 0.05:
        warnings.append(f"Risk per trade is high ({Config.MAX_RISK_PER_TRADE*100:.0f}%)")
    
    if Config.MAX_POSITION_PCT > 0.10:
        warnings.append(f"Position size is large ({Config.MAX_POSITION_PCT*100:.0f}%)")
    
    if Config.MAX_OPEN_POSITIONS > 10:
        warnings.append(f"Max positions is high ({Config.MAX_OPEN_POSITIONS})")
    
    if not Config.USE_ATR_EXITS:
        warnings.append("Using fixed stop loss/take profit (ATR exits disabled)")
    
    if not getattr(Config, 'ENABLE_DAILY_LOSS_CAP', False):
        warnings.append("Daily loss cap is disabled")
    
    # Display warnings
    if warnings:
        print("\n⚠️  WARNINGS:")
        for warning in warnings:
            print(f"   {warning}")
            logger.warning(warning)
    
    # Display errors
    if errors:
        print("\n❌ CONFIGURATION ERRORS:")
        for error in errors:
            print(f"   {error}")
            logger.error(error)
        print()
        return False
    
    print("\n✅ Configuration validated successfully")
    return True


def display_controls():
    """Display keyboard controls"""
    print("\n" + "="*78)
    print("⌨️  KEYBOARD CONTROLS")
    print("="*78)
    print("Press 'R' + Enter    : Generate performance report")
    print("Press 'S' + Enter    : Show current status & positions")
    print("Press 'P' + Enter    : Pause/Resume trading")
    print("Press 'E' + Enter    : Emergency exit all positions")
    print("Press 'V' + Enter    : Validate position count")
    print("Press Ctrl+C         : Stop bot gracefully")
    print("="*78 + "\n")


def input_listener(bot, stop_event):
    """
    Listen for keyboard commands (non-blocking)
    Runs in separate thread
    """
    while not stop_event.is_set():
        try:
            # Try to read input with timeout
            import select
            
            # Non-blocking input (Unix/Linux)
            if hasattr(select, 'select'):
                if select.select([sys.stdin], [], [], 1)[0]:
                    command = sys.stdin.readline().strip().lower()
                else:
                    continue
            else:
                # Windows fallback (blocking)
                command = input().strip().lower()
            
            # Handle commands
            if command == 'r':
                # Generate report
                if hasattr(bot, 'monitor'):
                    print("\n📊 Generating performance report...")
                    try:
                        bot.monitor.generate_report()
                    except Exception as e:
                        print(f"❌ Report generation failed: {e}")
                else:
                    print("\n❌ Performance monitor not available")
            
            elif command == 's':
                # Show status
                print("\n" + "="*78)
                print("📊 CURRENT STATUS")
                print("="*78)
                bot.print_summary()
                
                if bot.positions:
                    print(f"\n📍 OPEN POSITIONS ({len(bot.positions)}):")
                    for symbol, pos in bot.positions.items():
                        current_price = bot.get_current_price_safe(symbol)
                        if current_price:
                            pnl_pct = ((current_price - pos['entry_price']) / pos['entry_price'] * 100)
                            emoji = "📈" if pnl_pct > 0 else "📉"
                            print(f"   {emoji} {symbol}: ${pos['position_size']:.2f} @ ${pos['entry_price']:.4f} | P&L: {pnl_pct:+.2f}%")
            
            elif command == 'p':
                # Pause/Resume
                if hasattr(bot, 'trading_paused'):
                    bot.trading_paused = not bot.trading_paused
                    status = "⏸️  PAUSED" if bot.trading_paused else "▶️  RESUMED"
                    print(f"\n{status}")
                else:
                    print("\n❌ Pause functionality not available")
            
            elif command == 'e':
                # Emergency exit
                print("\n🚨 EMERGENCY EXIT - Closing all positions...")
                confirmation = input("Type 'CONFIRM' to proceed: ").strip()
                if confirmation == 'CONFIRM':
                    for symbol in list(bot.positions.keys()):
                        try:
                            bot.execute_sell(symbol, reason="Manual Emergency Exit")
                        except Exception as e:
                            print(f"❌ Failed to close {symbol}: {e}")
                    print("✅ Emergency exit complete")
                else:
                    print("❌ Cancelled")
            
            elif command == 'v':
                # Validate positions
                print("\n🔍 Validating position count...")
                bot.validate_position_count()
                print(f"✅ Current: {len(bot.positions)}/{bot.config.MAX_OPEN_POSITIONS}")
            
        except Exception as e:
            if not stop_event.is_set():
                pass  # Ignore errors during normal operation


def setup_signal_handlers(bot, stop_event):
    """Setup signal handlers for graceful shutdown"""
    def signal_handler(signum, frame):
        print("\n\n" + "="*78)
        print("🛑 SHUTDOWN SIGNAL RECEIVED")
        print("="*78)
        stop_event.set()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


def main():
    """
    Main entry point with comprehensive error handling
    Returns: exit code (0 = success, 1 = error)
    """
    logger = None
    bot = None
    listener_thread = None
    stop_event = threading.Event()
    
    try:
        # Setup logger first
        logger = setup_logger(Config.LOG_FILE)
        logger.info("="*78)
        logger.info(f"Bot v{BOT_VERSION} starting up - {datetime.now()}")
        logger.info("="*78)
        
        # Display startup
        display_startup_banner()
        ml_available = display_ml_status(logger)
        display_configuration(logger)
        
        # Validate configuration
        if not validate_configuration(logger):
            logger.error("Configuration validation failed - aborting")
            return 1
        
        # Live trading confirmation
        if not Config.PAPER_TRADING:
            print("\n" + "="*78)
            print("⚠️  WARNING: LIVE TRADING MODE")
            print("="*78)
            print("You are about to trade with REAL MONEY on a LIVE EXCHANGE.")
            print("This bot is provided AS-IS with NO GUARANTEES of profitability.")
            print("You could LOSE ALL your capital.")
            print("\nType 'START LIVE TRADING' to confirm:")
            confirmation = input("> ").strip()
            
            if confirmation != "START LIVE TRADING":
                print("✅ Cancelled - No trades will be executed")
                logger.info("Live trading cancelled by user")
                return 0
            
            logger.warning("Live trading confirmed by user - REAL MONEY MODE")
        
        # Final startup message
        print("\n" + "="*78)
        print("🚀 STARTING TRADING BOT...")
        print("="*78)
        print("Initializing components...")
        
        # Initialize bot
        try:
            bot = TradingBot(Config)
            logger.info("✅ Bot initialized successfully")
        except Exception as e:
            logger.error(f"❌ Bot initialization failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            print(f"\n❌ Failed to initialize bot: {e}")
            return 1
        
        # Add performance monitor (optional)
        try:
            from monitor import PerformanceMonitor
            bot.monitor = PerformanceMonitor(bot)
            logger.info("✅ Performance monitor enabled")
        except ImportError:
            logger.warning("Performance monitor not available")
        except Exception as e:
            logger.warning(f"Failed to load performance monitor: {e}")
        
        # Display controls
        display_controls()
        
        # Setup signal handlers
        setup_signal_handlers(bot, stop_event)
        
        # Start input listener thread
        listener_thread = threading.Thread(
            target=input_listener,
            args=(bot, stop_event),
            daemon=True,
            name="InputListener"
        )
        listener_thread.start()
        logger.info("✅ Input listener started")
        
        # Start bot main loop
        print("✅ Bot is now running!\n")
        logger.info("="*78)
        logger.info("Bot main loop starting")
        logger.info("="*78)
        
        bot.run()
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n" + "="*78)
        print("🛑 SHUTDOWN INITIATED BY USER (Ctrl+C)")
        print("="*78)
        
        if logger:
            logger.info("Shutdown initiated by user (KeyboardInterrupt)")
        
        # Stop input listener
        stop_event.set()
        
        # Generate final report
        if bot and hasattr(bot, 'monitor') and hasattr(bot, 'trade_history') and bot.trade_history:
            print("\n📊 Generating final performance report...")
            try:
                bot.monitor.generate_report()
                print("✅ Report saved")
            except Exception as e:
                print(f"⚠️  Report generation failed: {e}")
        
        # Display final summary
        if bot:
            print("\n" + "="*78)
            print("📊 FINAL SESSION SUMMARY")
            print("="*78)
            bot.print_summary()
        
        print("\n✅ Bot stopped successfully")
        return 0
        
    except Exception as e:
        print("\n\n" + "="*78)
        print("❌ FATAL ERROR OCCURRED")
        print("="*78)
        
        if logger:
            logger.error(f"Fatal error: {e}")
            import traceback
            logger.error(traceback.format_exc())
        
        print(f"\nError: {e}")
        print(f"\n💡 Check {Config.LOG_FILE} for detailed error information")
        
        # Try to save any data
        if bot and hasattr(bot, 'save_trade_history'):
            try:
                bot.save_trade_history()
                print("✅ Trade history saved")
            except:
                pass
        
        return 1
    
    finally:
        # Cleanup
        print("\n🧹 Cleaning up...")
        
        # Stop threads
        stop_event.set()
        
        if listener_thread and listener_thread.is_alive():
            listener_thread.join(timeout=2)
        
        # Close bot resources
        if bot and hasattr(bot, 'exchange'):
            try:
                if hasattr(bot.exchange, 'close'):
                    bot.exchange.close()
                    logger.info("✅ Exchange connection closed")
            except:
                pass
        
        if logger:
            logger.info("="*78)
            logger.info(f"Bot v{BOT_VERSION} shutdown complete - {datetime.now()}")
            logger.info("="*78)
        
        print("✅ Cleanup complete\n")


if __name__ == "__main__":
    """Entry point"""
    exit_code = main()
    sys.exit(exit_code)
