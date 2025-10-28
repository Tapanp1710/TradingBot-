"""
Loss Streak Detector v1.0
Detects consecutive losses and triggers cooldown
"""
import logging
from datetime import datetime, timedelta

logger = logging.getLogger("StreakDetector")

class StreakDetector:
    def __init__(self, config):
        self.config = config
        self.recent_trades = []
        self.pause_until = None
        
    def add_trade(self, pnl):
        """Record a completed trade"""
        self.recent_trades.append({
            'pnl': pnl,
            'time': datetime.now(),
            'is_loss': pnl < 0
        })
        
        # Keep only last 10 trades
        if len(self.recent_trades) > 10:
            self.recent_trades = self.recent_trades[-10:]
    
    def check_streak(self):
        """Check for losing streaks"""
        if not self.config.ENABLE_STREAK_DETECTION:
            return True, "Streak detection disabled"
        
        # Check if we're in cooldown
        if self.pause_until:
            if datetime.now() < self.pause_until:
                remaining = (self.pause_until - datetime.now()).total_seconds() / 3600
                return False, f"In cooldown for {remaining:.1f} more hours"
            else:
                # Cooldown expired
                self.pause_until = None
                logger.info("✅ Cooldown expired, resuming trading")
        
        # Check recent trades for losing streak
        if len(self.recent_trades) < self.config.MAX_CONSECUTIVE_LOSSES:
            return True, "Not enough trades to check streak"
        
        # Check last N trades
        last_n = self.recent_trades[-self.config.MAX_CONSECUTIVE_LOSSES:]
        consecutive_losses = all(t['is_loss'] for t in last_n)
        
        if consecutive_losses:
            # Trigger cooldown
            self.pause_until = datetime.now() + timedelta(hours=self.config.COOLDOWN_AFTER_LOSSES_HOURS)
            logger.warning(f"🛑 {self.config.MAX_CONSECUTIVE_LOSSES} consecutive losses detected!")
            logger.warning(f"⏸️  Cooling down until {self.pause_until.strftime('%H:%M:%S')}")
            return False, f"Consecutive losses: {self.config.MAX_CONSECUTIVE_LOSSES}"
        
        return True, "No losing streak"
    
    def get_stats(self):
        """Get recent performance stats"""
        if not self.recent_trades:
            return {
                'total': 0,
                'wins': 0,
                'losses': 0,
                'win_rate': 0,
                'streak': 0
            }
        
        wins = sum(1 for t in self.recent_trades if not t['is_loss'])
        losses = len(self.recent_trades) - wins
        
        # Calculate current streak
        current_streak = 0
        for trade in reversed(self.recent_trades):
            if trade['is_loss']:
                current_streak += 1
            else:
                break
        
        return {
            'total': len(self.recent_trades),
            'wins': wins,
            'losses': losses,
            'win_rate': wins / len(self.recent_trades) if self.recent_trades else 0,
            'current_loss_streak': current_streak
        }
