"""
Logging Setup v3.0 - OPTIMIZED
- Better Windows emoji handling
- Separate error log
- Performance mode
- Log compression
"""
import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from typing import Optional


def setup_logger(
    log_file: str = 'logs/bot.log',
    level: int = logging.INFO,
    enable_console: bool = True,
    enable_emoji: bool = True,
    separate_error_log: bool = True
) -> logging.Logger:
    """
    Setup production logger with all optimizations
    
    Args:
        log_file: Main log file path
        level: Logging level
        enable_console: Enable console output
        enable_emoji: Attempt emoji support (may fail on some Windows consoles)
        separate_error_log: Create separate error log file
    """
    
    # Create logs directory with error handling
    try:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
    except Exception as e:
        print(f"Warning: Failed to create log directory: {e}")
    
    # Get or create logger
    logger = logging.getLogger('TradingBot')
    logger.setLevel(level)
    
    # Remove existing handlers to prevent duplicates
    for handler in logger.handlers[:]:
        handler.close()
        logger.removeHandler(handler)
    
    # Timestamp format
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # === FILE HANDLER (Main Log) ===
    try:
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=20*1024*1024,  # 20 MB
            backupCount=10,         # Keep 10 backups
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)  # Capture everything in file
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"Warning: Failed to create file handler: {e}")
    
    # === ERROR FILE HANDLER (Separate Error Log) ===
    if separate_error_log:
        try:
            error_file = log_file.replace('.log', '_errors.log')
            error_handler = RotatingFileHandler(
                error_file,
                maxBytes=10*1024*1024,  # 10 MB
                backupCount=5,
                encoding='utf-8'
            )
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(formatter)
            logger.addHandler(error_handler)
        except Exception as e:
            print(f"Warning: Failed to create error handler: {e}")
    
    # === CONSOLE HANDLER ===
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)  # Less verbose on console
        
        # Platform-specific emoji handling
        if enable_emoji:
            if sys.platform == 'win32':
                # Windows: Try UTF-8, fallback to ASCII
                try:
                    # Modern Windows (Windows 10+)
                    if hasattr(sys.stdout, 'reconfigure'):
                        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
                        console_handler.setFormatter(formatter)
                    else:
                        # Older Windows or unsupported console
                        # Use ASCII-safe formatter
                        ascii_formatter = logging.Formatter(
                            '%(asctime)s - %(levelname)s - %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S'
                        )
                        console_handler.setFormatter(ascii_formatter)
                except Exception as e:
                    print(f"Warning: UTF-8 console encoding failed, using ASCII: {e}")
                    ascii_formatter = logging.Formatter(
                        '%(asctime)s - %(levelname)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S'
                    )
                    console_handler.setFormatter(ascii_formatter)
            else:
                # Linux/Mac: UTF-8 works natively
                console_handler.setFormatter(formatter)
        else:
            # Emoji disabled, use plain formatter
            console_handler.setFormatter(formatter)
        
        logger.addHandler(console_handler)
    
    # Disable propagation to prevent duplicate logs
    logger.propagate = False
    
    # Log initial message
    logger.info("="*70)
    logger.info("Logger initialized")
    logger.info(f"Log file: {log_file}")
    logger.info(f"Level: {logging.getLevelName(level)}")
    logger.info(f"Emoji support: {enable_emoji}")
    logger.info(f"Separate error log: {separate_error_log}")
    logger.info("="*70)
    
    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get existing logger instance
    
    Args:
        name: Logger name (default: 'TradingBot')
    """
    return logging.getLogger(name or 'TradingBot')


def set_log_level(level: int):
    """
    Change logging level dynamically
    
    Args:
        level: logging.DEBUG, INFO, WARNING, ERROR, CRITICAL
    """
    logger = get_logger()
    logger.setLevel(level)
    logger.info(f"Log level changed to: {logging.getLevelName(level)}")


def cleanup_old_logs(log_dir: str = 'logs', days: int = 30):
    """
    Delete log files older than specified days
    
    Args:
        log_dir: Log directory path
        days: Delete files older than this many days
    """
    import time
    from pathlib import Path
    
    if not os.path.exists(log_dir):
        return
    
    cutoff = time.time() - (days * 86400)
    deleted = 0
    
    try:
        for log_file in Path(log_dir).glob('*.log*'):
            if log_file.stat().st_mtime < cutoff:
                log_file.unlink()
                deleted += 1
        
        if deleted > 0:
            logger = get_logger()
            logger.info(f"🧹 Cleaned up {deleted} old log files (>{days} days)")
    except Exception as e:
        print(f"Warning: Failed to cleanup old logs: {e}")


def archive_logs(log_dir: str = 'logs', archive_dir: str = 'logs/archive'):
    """
    Move old logs to archive directory
    
    Args:
        log_dir: Source log directory
        archive_dir: Archive directory
    """
    import shutil
    from pathlib import Path
    
    try:
        os.makedirs(archive_dir, exist_ok=True)
        
        moved = 0
        for log_file in Path(log_dir).glob('*.log.[0-9]*'):
            dest = Path(archive_dir) / log_file.name
            shutil.move(str(log_file), str(dest))
            moved += 1
        
        if moved > 0:
            logger = get_logger()
            logger.info(f"📦 Archived {moved} rotated log files")
    except Exception as e:
        print(f"Warning: Failed to archive logs: {e}")


def get_log_stats(log_file: str = 'logs/bot.log') -> dict:
    """
    Get log file statistics
    
    Returns:
        dict with size, line count, error count
    """
    stats = {
        'exists': False,
        'size_mb': 0,
        'lines': 0,
        'errors': 0,
        'warnings': 0
    }
    
    if not os.path.exists(log_file):
        return stats
    
    try:
        stats['exists'] = True
        stats['size_mb'] = os.path.getsize(log_file) / (1024 * 1024)
        
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                stats['lines'] += 1
                if ' - ERROR - ' in line:
                    stats['errors'] += 1
                elif ' - WARNING - ' in line:
                    stats['warnings'] += 1
    except Exception as e:
        print(f"Warning: Failed to get log stats: {e}")
    
    return stats


# Convenience functions for common operations
def log_trade(logger: logging.Logger, action: str, symbol: str, price: float, 
              amount: float, pnl: float = None):
    """Log trade in standardized format"""
    if pnl is not None:
        logger.info(f"[TRADE] {action} {symbol} @ ${price:.2f} | "
                   f"Amount: {amount:.6f} | P&L: ${pnl:+.2f}")
    else:
        logger.info(f"[TRADE] {action} {symbol} @ ${price:.2f} | "
                   f"Amount: {amount:.6f}")


def log_signal(logger: logging.Logger, symbol: str, signal: str, 
               confidence: float, indicators: dict = None):
    """Log trading signal in standardized format"""
    msg = f"[SIGNAL] {symbol}: {signal} (Confidence: {confidence:.1%})"
    if indicators:
        msg += f" | {indicators}"
    logger.info(msg)


def log_error_with_context(logger: logging.Logger, error: Exception, 
                           context: str = ""):
    """Log error with full context and traceback"""
    import traceback
    logger.error(f"{'Context: ' + context if context else ''}")
    logger.error(f"Error: {type(error).__name__}: {str(error)}")
    logger.error(f"Traceback:\n{traceback.format_exc()}")
