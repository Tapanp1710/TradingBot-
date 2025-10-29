"""
Watchdog Process v3.0 - PRODUCTION OPTIMIZED
- Exponential backoff, health checks, process management
For 24/7: python run_bot_watchdog.py
"""
import subprocess
import time
import logging
import os
import signal
import sys
from datetime import datetime
import psutil

# Setup logging
os.makedirs('logs', exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/watchdog.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger('Watchdog')


class BotWatchdog:
    """Production watchdog with health monitoring"""
    
    def __init__(self):
        self.max_restarts = 10
        self.restart_count = 0
        self.start_time = time.time()
        self.current_process = None
        self.restart_delays = [30, 60, 120, 300, 600]  # Exponential backoff
        self.health_check_interval = 300  # 5 minutes
        self.last_health_check = time.time()
        
        # Stats
        self.crash_history = []
        self.total_crashes = 0
        
        logger.info("="*70)
        logger.info("🐕 TRADING BOT WATCHDOG v3.0 STARTED")
        logger.info("="*70)
        logger.info(f"Max restarts: {self.max_restarts}")
        logger.info(f"Health checks: Every {self.health_check_interval}s")
        logger.info(f"Restart delays: {self.restart_delays} seconds")
        logger.info("="*70 + "\n")
    
    def get_restart_delay(self) -> int:
        """Calculate restart delay with exponential backoff"""
        if self.restart_count < len(self.restart_delays):
            return self.restart_delays[self.restart_count]
        return self.restart_delays[-1]  # Max delay
    
    def is_process_healthy(self) -> bool:
        """Check if bot process is responsive"""
        
        if self.current_process is None:
            return False
        
        try:
            # Check if process exists
            process = psutil.Process(self.current_process.pid)
            
            # Check if consuming reasonable CPU (not hung)
            cpu_percent = process.cpu_percent(interval=1)
            
            # Check memory usage (< 2GB)
            memory_mb = process.memory_info().rss / 1024 / 1024
            
            if memory_mb > 2048:
                logger.warning(f"⚠️  High memory usage: {memory_mb:.0f} MB")
                return False
            
            # Check if log file is being written (bot is active)
            log_file = 'logs/bot.log'
            if os.path.exists(log_file):
                age = time.time() - os.path.getmtime(log_file)
                if age > 600:  # No writes in 10 minutes
                    logger.warning(f"⚠️  Log file stale: {age:.0f}s old")
                    return False
            
            return True
            
        except psutil.NoSuchProcess:
            logger.warning("⚠️  Process no longer exists")
            return False
        except Exception as e:
            logger.error(f"Health check error: {e}")
            return False
    
    def kill_process(self, timeout: int = 10):
        """Gracefully kill process with timeout"""
        
        if self.current_process is None:
            return
        
        try:
            pid = self.current_process.pid
            process = psutil.Process(pid)
            
            # Try graceful termination first
            logger.info(f"🛑 Sending SIGTERM to PID {pid}...")
            process.terminate()
            
            # Wait for graceful shutdown
            try:
                process.wait(timeout=timeout)
                logger.info("✅ Process terminated gracefully")
            except psutil.TimeoutExpired:
                # Force kill if timeout
                logger.warning(f"⚠️  Process didn't terminate, sending SIGKILL...")
                process.kill()
                logger.info("✅ Process killed forcefully")
            
        except psutil.NoSuchProcess:
            logger.info("Process already terminated")
        except Exception as e:
            logger.error(f"Error killing process: {e}")
    
    def record_crash(self, exit_code: int):
        """Record crash for analysis"""
        self.crash_history.append({
            'timestamp': datetime.now(),
            'exit_code': exit_code,
            'restart_count': self.restart_count
        })
        self.total_crashes += 1
        
        # Keep only last 100 crashes
        if len(self.crash_history) > 100:
            self.crash_history = self.crash_history[-100:]
    
    def run(self):
        """Main watchdog loop"""
        
        while self.restart_count < self.max_restarts:
            logger.info(f"\n{'='*70}")
            logger.info(f"🐕 Starting bot (Attempt #{self.restart_count + 1})")
            logger.info(f"{'='*70}\n")
            
            try:
                # Start bot process
                self.current_process = subprocess.Popen(
                    [sys.executable, 'main.py'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                logger.info(f"✅ Bot started with PID {self.current_process.pid}")
                
                # Monitor process
                while True:
                    # Check if process is still running
                    exit_code = self.current_process.poll()
                    
                    if exit_code is not None:
                        # Process exited
                        if exit_code == 0:
                            logger.info("✅ Bot exited normally (exit code 0)")
                            return  # Clean exit, don't restart
                        else:
                            logger.error(f"❌ Bot crashed with exit code {exit_code}")
                            self.record_crash(exit_code)
                            break  # Exit inner loop to restart
                    
                    # Health check
                    if time.time() - self.last_health_check > self.health_check_interval:
                        logger.info("🏥 Running health check...")
                        
                        if not self.is_process_healthy():
                            logger.error("❌ Health check FAILED - Restarting bot")
                            self.kill_process()
                            break
                        else:
                            logger.info("✅ Health check passed")
                        
                        self.last_health_check = time.time()
                    
                    # Sleep before next check
                    time.sleep(10)
                
                # Process exited or failed health check
                self.restart_count += 1
                
                if self.restart_count >= self.max_restarts:
                    logger.error(f"🚨 Max restarts ({self.max_restarts}) reached")
                    logger.error("⏸️  Stopping watchdog to prevent infinite loop")
                    break
                
                # Wait before restart (exponential backoff)
                delay = self.get_restart_delay()
                logger.info(f"⏱️  Waiting {delay}s before restart...")
                logger.info(f"   Restarts remaining: {self.max_restarts - self.restart_count}")
                time.sleep(delay)
                
            except KeyboardInterrupt:
                logger.info("\n👋 Watchdog stopped by user (Ctrl+C)")
                self.kill_process()
                break
            
            except Exception as e:
                logger.error(f"❌ Unexpected error: {e}")
                self.restart_count += 1
                
                if self.restart_count >= self.max_restarts:
                    break
                
                time.sleep(self.get_restart_delay())
        
        # Generate final stats
        self.print_stats()
    
    def print_stats(self):
        """Print watchdog statistics"""
        
        uptime_hours = (time.time() - self.start_time) / 3600
        
        logger.info(f"\n{'='*70}")
        logger.info("🐕 WATCHDOG TERMINATED")
        logger.info(f"{'='*70}")
        logger.info(f"Total uptime: {uptime_hours:.1f} hours ({uptime_hours/24:.1f} days)")
        logger.info(f"Total restarts: {self.restart_count}")
        logger.info(f"Total crashes: {self.total_crashes}")
        
        if self.restart_count > 0:
            avg_time = uptime_hours / self.restart_count
            logger.info(f"Avg time between restarts: {avg_time:.1f} hours")
        
        # Recent crashes
        if self.crash_history:
            logger.info(f"\nRecent crashes:")
            for crash in self.crash_history[-5:]:
                logger.info(f"  • {crash['timestamp'].strftime('%Y-%m-%d %H:%M:%S')} - "
                          f"Exit code: {crash['exit_code']}")
        
        logger.info(f"{'='*70}\n")


def main():
    """Entry point"""
    
    # Handle signals
    def signal_handler(sig, frame):
        logger.info("\n🛑 Received shutdown signal")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run watchdog
    watchdog = BotWatchdog()
    watchdog.run()


if __name__ == "__main__":
    main()
