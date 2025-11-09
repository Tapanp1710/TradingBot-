"""
Dynamic Trading Bot Configuration v6.5.0 - ENHANCED WITH ADVANCED FEATURES
November 9, 2025 - Production-ready with all improvements
- Capital-based adjustments
- Adaptive confidence thresholds (time, win-rate, volatility, signals)
- ML enabled for all accounts > $500
- Signal surge detection and filtering
- SHORT SELLING capability (margin trading)
- Multi-timeframe confirmation
- Market regime detection and swing mode
- Contrarian signal detection
- Idle capital rebalancing
"""
import os
from datetime import datetime, timedelta
import pytz


class DynamicConfig:
    """
    Production-ready configuration with ALL advanced features:
    - Capital-based dynamic adjustments
    - Real-time adaptive thresholds (4 strategies)
    - ML ensemble enabled (Random Forest + LightGBM + XGBoost)
    - Signal tracking and surge filtering
    - Win-rate adjustments
    - Market volatility sensing
    - SHORT SELLING (NEW)
    - Multi-timeframe analysis (NEW)
    - Market regime detection (NEW)
    - Contrarian signals (NEW)
    - Idle capital rebalancing (NEW)
    """
    
    def __init__(self, starting_capital=None):
        """Initialize with starting capital and signal tracking"""
        self._starting_capital = starting_capital or float(os.getenv('STARTING_CAPITAL', '1000'))
        self._current_capital = self._starting_capital
        self._last_update = datetime.now()
        
        # Signal tracking
        self._recent_buy_signals = []
        self._signal_check_window_secs = 60
        self._signal_history_limit = 50
        
        # NEW: Market regime tracking
        self._atr_history = []
        self._current_regime = 'NORMAL'
        
        # NEW: Idle capital tracking
        self._last_trade_time = datetime.now()
        self._scans_without_signal = 0
        
        # Static values
        self.BOT_VERSION = "6.5.0"
        self.CONFIG_VERSION = "6.5.0-ENHANCED"
        self.EXCHANGE = "binance"
        self.API_KEY = os.getenv('EXCHANGE_API_KEY', '')
        self.API_SECRET = os.getenv('EXCHANGE_API_SECRET', '')
        self.PAPER_TRADING = os.getenv('PAPER_TRADING', 'True').lower() == 'true'
        
        # Initialize all parameters
        self._update_all_params()
    
    
    # ===================================================================
    # CAPITAL UPDATE METHOD
    # ===================================================================
    
    def update_capital(self, new_capital):
        """
        Call this after every trade or daily to recalculate all parameters
        """
        old_tier = self._get_tier(self._current_capital)
        old_positions = self.MAX_OPEN_POSITIONS
        
        self._current_capital = new_capital
        new_tier = self._get_tier(new_capital)
        
        self._update_all_params()
        self._last_update = datetime.now()
        
        # Notify on tier changes
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
    # TIER & CALCULATION HELPERS (UNCHANGED)
    # ===================================================================
    
    def _get_tier(self, cap):
        """Get capital tier - FIXED boundaries"""
        if cap < 250:
            return 'micro'
        elif cap < 500:
            return 'small'
        elif cap <= 1000:
            return 'medium'
        elif cap < 3000:
            return 'large'
        else:
            return 'whale'
    
    def _calc_positions(self, cap):
        """Proper position counts based on capital"""
        if cap < 200:
            return 2
        elif cap < 400:
            return 2
        elif cap < 600:
            return 3
        elif cap <= 1000:
            return 3
        elif cap < 2000:
            return 4
        elif cap < 3500:
            return 5
        elif cap < 7000:
            return 6
        else:
            return 8
    
    def _calc_position_pct(self, cap, pos):
        """Position size as % of capital"""
        base = 0.90 / pos
        return min(base * 1.2, 0.50)
    
    def _calc_min_pos(self, cap, pos):
        """Minimum position size in USD"""
        avg = (cap * 0.90) / pos
        return max(40, int(avg * 0.45))
    
    def _calc_risk(self, cap):
        """Max risk per trade"""
        if cap < 500:
            return 0.030
        elif cap < 2000:
            return 0.025
        elif cap < 5000:
            return 0.022
        else:
            return 0.020
    
    def _calc_drawdown(self, cap):
        """Max drawdown limit"""
        if cap < 500:
            return 0.20
        elif cap <= 1000:
            return 0.17
        elif cap < 2000:
            return 0.15
        elif cap < 5000:
            return 0.13
        else:
            return 0.10
    
    def _calc_atr(self, cap):
        """ATR percentage minimum"""
        if cap < 300:
            return 0.0010
        elif cap < 500:
            return 0.0012
        elif cap <= 1000:
            return 0.0015
        elif cap < 5000:
            return 0.0020
        else:
            return 0.0025
    
    def _calc_sl_mult(self, cap):
        """Stop loss ATR multiplier"""
        if cap < 300:
            return 1.5
        elif cap < 500:
            return 1.6
        elif cap <= 1000:
            return 1.7
        elif cap < 5000:
            return 1.8
        else:
            return 2.0
    
    def _calc_sl_pct(self, cap):
        """Max stop loss percentage"""
        if cap < 300:
            return 0.035
        elif cap < 500:
            return 0.030
        elif cap <= 1000:
            return 0.025
        elif cap < 5000:
            return 0.022
        else:
            return 0.020
    
    def _calc_tp_mult(self, cap):
        """Take profit ATR multiplier"""
        if cap < 300:
            return 1.2
        elif cap < 500:
            return 1.3
        elif cap <= 1000:
            return 1.3
        elif cap < 5000:
            return 1.5
        else:
            return 1.9
    
    def _calc_trail(self, cap):
        """Trailing stop activation multiplier"""
        if cap < 300:
            return 1.0
        elif cap < 500:
            return 1.1
        elif cap <= 1000:
            return 1.3
        elif cap < 5000:
            return 1.5
        else:
            return 1.8
    
    def _calc_daily_loss(self, cap):
        """Daily loss limit percentage"""
        if cap < 300:
            return 0.050
        elif cap < 500:
            return 0.045
        elif cap <= 1000:
            return 0.040
        elif cap < 2000:
            return 0.035
        elif cap < 5000:
            return 0.030
        else:
            return 0.025
    
    def _calc_confidence(self, cap):
        """Base confidence threshold"""
        if cap < 300:
            return 0.50
        elif cap < 500:
            return 0.52
        elif cap <= 1000:
            return 0.60
        elif cap < 2000:
            return 0.57
        elif cap < 5000:
            return 0.58
        else:
            return 0.60
    
    def _calc_quality(self, cap):
        """Min quality score (0-100)"""
        if cap < 300:
            return 40
        elif cap < 500:
            return 45
        elif cap <= 1000:
            return 50
        elif cap < 2000:
            return 55
        elif cap < 5000:
            return 60
        else:
            return 65
    
    def _calc_rsi(self, cap):
        """RSI oversold threshold"""
        if cap < 300:
            return 38
        elif cap < 500:
            return 36
        elif cap <= 1000:
            return 35
        elif cap < 5000:
            return 33
        else:
            return 30
    
    def _calc_losses(self, cap):
        """Max consecutive losses before cooldown"""
        if cap < 500:
            return 2
        elif cap <= 1000:
            return 3
        elif cap < 2000:
            return 4
        else:
            return 5
    
    def _calc_cooldown(self, cap):
        """Cooldown hours after losses"""
        if cap < 300:
            return 0.5
        elif cap < 500:
            return 0.75
        elif cap <= 1000:
            return 1.0
        elif cap < 5000:
            return 1.5
        else:
            return 2.0
    
    def _calc_winrate(self, cap):
        """Min win rate to trade"""
        if cap < 300:
            return 0.25
        elif cap < 500:
            return 0.28
        elif cap <= 1000:
            return 0.30
        elif cap < 5000:
            return 0.33
        else:
            return 0.35
    
    def _calc_emergency(self, cap):
        """Emergency exit loss threshold"""
        if cap < 300:
            return 0.15
        elif cap < 500:
            return 0.14
        elif cap <= 1000:
            return 0.12
        elif cap < 5000:
            return 0.10
        else:
            return 0.08
    
    def _calc_pause(self, cap):
        """Pause duration hours"""
        if cap < 300:
            return 1
        elif cap < 500:
            return 2
        elif cap <= 1000:
            return 3
        elif cap < 5000:
            return 4
        else:
            return 6
    
    def _calc_slippage(self, cap):
        """Slippage rate"""
        if cap < 300:
            return 0.0008
        elif cap < 500:
            return 0.0007
        elif cap <= 1000:
            return 0.0006
        elif cap < 5000:
            return 0.0004
        else:
            return 0.0003
    
    def _calc_scan_offset(self, cap):
        """Scan offset coins"""
        if cap < 300:
            return 8
        elif cap < 500:
            return 10
        elif cap <= 1000:
            return 12
        elif cap < 5000:
            return 15
        else:
            return 20
    
    def _calc_scan_int(self, cap):
        """Scan interval seconds"""
        if cap < 300:
            return 15
        elif cap < 500:
            return 18
        elif cap <= 1000:
            return 20
        elif cap < 5000:
            return 25
        else:
            return 30
    
    def _calc_multipliers(self, cap):
        """Position sizing multipliers (high, low)"""
        if cap < 500:
            return 1.25, 0.75
        elif cap <= 1000:
            return 1.20, 0.80
        elif cap < 5000:
            return 1.15, 0.85
        else:
            return 1.10, 0.90
    
    def _calc_grade(self, cap):
        """Signal quality grade"""
        if cap < 250:
            return 'D'
        elif cap <= 1000:
            return 'C'
        elif cap < 5000:
            return 'B'
        else:
            return 'A'
    
    def _calc_ml_trades(self, cap):
        """Min trades before ML update"""
        if cap < 500:
            return 4
        elif cap <= 1000:
            return 6
        elif cap < 5000:
            return 8
        else:
            return 10
    
    
    # ===================================================================
    # SIGNAL TRACKING & FILTERING (UNCHANGED)
    # ===================================================================
    
    def track_buy_signal(self, confidence, symbol):
        """Track incoming BUY signal"""
        now = datetime.now()
        self._recent_buy_signals.append((now, confidence, symbol))
        
        if len(self._recent_buy_signals) > self._signal_history_limit:
            self._recent_buy_signals = self._recent_buy_signals[-self._signal_history_limit:]
        
        recent_count = self.get_recent_signal_count()
        if recent_count >= 3:
            print(f"SIGNAL SURGE: {recent_count} signals in {self._signal_check_window_secs}s - Threshold will increase")
        
        # Reset scans counter
        self._scans_without_signal = 0
    
    def get_recent_signal_count(self, window_secs=None):
        """Count BUY signals in recent window"""
        if window_secs is None:
            window_secs = self._signal_check_window_secs
        
        now = datetime.now()
        cutoff = now - timedelta(seconds=window_secs)
        
        recent = [s for s in self._recent_buy_signals if s[0] >= cutoff]
        return len(recent)
    
    def get_recent_signals(self, window_secs=None):
        """Get all signals in recent window"""
        if window_secs is None:
            window_secs = self._signal_check_window_secs
        
        now = datetime.now()
        cutoff = now - timedelta(seconds=window_secs)
        
        return [s for s in self._recent_buy_signals if s[0] >= cutoff]
    
    def _get_signal_count_adjustment(self, count):
        """Get threshold adjustment based on signal frequency"""
        if count >= 5:
            return +0.15
        elif count >= 4:
            return +0.10
        elif count >= 3:
            return +0.05
        else:
            return 0.0
    
    
    # ===================================================================
    # NEW: MARKET REGIME DETECTION
    # ===================================================================
    
    def update_atr_history(self, symbol, atr_value):
        """Track ATR values for regime detection"""
        self._atr_history.append({
            'timestamp': datetime.now(),
            'symbol': symbol,
            'atr': atr_value
        })
        
        # Keep last 50 readings
        if len(self._atr_history) > 50:
            self._atr_history.pop(0)
    
    def get_market_regime(self):
        """
        Determine current market regime based on ATR
        Returns: 'VOLATILE', 'FLAT', or 'NORMAL'
        """
        if len(self._atr_history) < 10:
            return 'NORMAL'
        
        # Calculate average ATR
        recent_atrs = [entry['atr'] for entry in self._atr_history[-20:]]
        avg_atr = sum(recent_atrs) / len(recent_atrs)
        
        # Classify regime
        if avg_atr > 0.025:  # 2.5%+
            new_regime = 'VOLATILE'
        elif avg_atr < 0.008:  # 0.8%-
            new_regime = 'FLAT'
        else:
            new_regime = 'NORMAL'
        
        # Track regime changes
        if self._current_regime != new_regime:
            old_regime = self._current_regime
            self._current_regime = new_regime
            print(f"\n🔔 MARKET REGIME CHANGE: {old_regime} → {new_regime}")
            print(f"   Avg ATR: {avg_atr*100:.2f}%")
            self._print_regime_strategy(new_regime)
        
        return self._current_regime
    
    def _print_regime_strategy(self, regime):
        """Print strategy adjustments for regime"""
        if regime == 'VOLATILE':
            print("   📈 SCALP MODE ACTIVATED:")
            print("   - Quick entries/exits (2-5 min holds)")
            print("   - Tight stops (2-3%)")
            print("   - Small TPs (2-3%)")
        elif regime == 'FLAT':
            print("   📊 SWING MODE ACTIVATED:")
            print("   - Patient entries")
            print("   - Wide stops (4-5%)")
            print("   - Large TPs (5-7%)")
            print("   - Reduced frequency")
        else:
            print("   ⚖️ NORMAL MODE:")
            print("   - Balanced approach")
    
    def get_regime_adjusted_params(self):
        """Get trading parameters adjusted for current regime"""
        regime = self.get_market_regime()
        
        if regime == 'VOLATILE':
            return {
                'stop_loss_mult': 1.5,
                'take_profit_mult': 1.3,
                'confidence_threshold': 0.60,
                'max_hold_hours': 6,
                'position_size_mult': 1.0
            }
        elif regime == 'FLAT':
            return {
                'stop_loss_mult': 2.5,
                'take_profit_mult': 2.5,
                'confidence_threshold': 0.65,
                'max_hold_hours': 72,
                'position_size_mult': 0.8
            }
        else:  # NORMAL
            return {
                'stop_loss_mult': 1.7,
                'take_profit_mult': 1.3,
                'confidence_threshold': 0.60,
                'max_hold_hours': 36,
                'position_size_mult': 1.0
            }
    
    
    # ===================================================================
    # NEW: IDLE CAPITAL REBALANCING
    # ===================================================================
    
    def record_trade_executed(self):
        """Call this when a trade is executed"""
        self._last_trade_time = datetime.now()
        self._scans_without_signal = 0
    
    def increment_scans_without_signal(self):
        """Call this after each scan with no signal"""
        self._scans_without_signal += 1
    
    def get_hours_since_last_trade(self):
        """Get hours since last trade"""
        return (datetime.now() - self._last_trade_time).total_seconds() / 3600
    
    def get_adjusted_threshold_for_idle(self):
        """
        Lower confidence threshold during extended idle periods
        """
        hours_idle = self.get_hours_since_last_trade()
        base_threshold = self.SIGNAL_CONFIDENCE_THRESHOLD
        
        # No adjustment if recently traded
        if hours_idle < 2:
            return base_threshold
        
        # Progressive lowering
        if hours_idle > 6:
            reduction = 0.10
        elif hours_idle > 4:
            reduction = 0.08
        else:
            reduction = 0.05
        
        relaxed = base_threshold - reduction
        relaxed = max(0.50, relaxed)  # Never below 50%
        
        if relaxed < base_threshold:
            print(f"💡 IDLE CAPITAL ADJUSTMENT: Threshold lowered to {relaxed:.1%} (idle {hours_idle:.1f}h)")
        
        return relaxed
    
    def should_force_deployment(self):
        """Determine if forced trade deployment needed"""
        hours_idle = self.get_hours_since_last_trade()
        
        # Never force before 3 hours
        if hours_idle < 3:
            return False
        
        # Force if idle for 3+ hours
        if hours_idle >= 3:
            print(f"\n⚡ FORCE DEPLOYMENT TRIGGERED (idle {hours_idle:.1f}h)")
            return True
        
        return False
    
    
    # ===================================================================
    # ADAPTIVE CONFIDENCE THRESHOLD (UNCHANGED)
    # ===================================================================
    
    def _get_time_based_adjustment(self, hour):
        """Strategy 1: Time-based adjustment"""
        if hour in [21, 22, 23, 0, 1, 2]:
            return 0.0
        elif hour in [6, 7, 8, 9, 17, 18, 19]:
            return -0.10
        elif hour in [3, 4, 5]:
            return -0.15
        else:
            return -0.05
    
    def _get_winrate_adjustment(self, win_rate):
        """Strategy 2: Performance-based adjustment"""
        if win_rate < 30:
            return +0.10
        elif win_rate < 45:
            return +0.05
        elif win_rate > 70:
            return -0.05
        elif win_rate > 60:
            return 0.0
        else:
            return 0.0
    
    def _get_signal_availability_adjustment(self, recent_signals):
        """Strategy 3: Market condition adjustment"""
        above_60 = sum(1 for s in recent_signals if s[1] >= 0.60)
        above_55 = sum(1 for s in recent_signals if s[1] >= 0.55)
        above_50 = sum(1 for s in recent_signals if s[1] >= 0.50)
        total = len(recent_signals)
        
        if above_55 < 2 and total > 10:
            return -0.10
        elif above_50 >= 5 and above_55 < 3:
            return -0.05
        elif above_60 >= 5:
            return +0.05
        else:
            return 0.0
    
    def _get_volatility_adjustment(self, avg_atr):
        """Strategy 4: Volatility-based adjustment"""
        if avg_atr < 0.01:
            return -0.10
        elif avg_atr < 0.015:
            return -0.05
        elif avg_atr > 0.035:
            return +0.05
        elif avg_atr > 0.05:
            return +0.10
        else:
            return 0.0
    
    def get_adaptive_confidence(self, 
                               win_rate=None, 
                               recent_signals=None,
                               market_volatility=None,
                               hour=None):
        """Master adaptive threshold combining all strategies"""
        base_threshold = self._calc_confidence(self._current_capital)
        adjustments = []
        
        if hour is None:
            hour = datetime.now().hour
        
        time_adj = self._get_time_based_adjustment(hour)
        adjustments.append(("time", time_adj))
        
        if win_rate is not None:
            wr_adj = self._get_winrate_adjustment(win_rate)
            adjustments.append(("winrate", wr_adj))
        
        if recent_signals is not None and len(recent_signals) > 0:
            signal_adj = self._get_signal_availability_adjustment(recent_signals)
            adjustments.append(("signals", signal_adj))
        
        if market_volatility is not None:
            vol_adj = self._get_volatility_adjustment(market_volatility)
            adjustments.append(("volatility", vol_adj))
        
        final_threshold = base_threshold
        for name, adj in adjustments:
            final_threshold += adj
        
        final_threshold = max(0.45, min(0.75, final_threshold))
        
        if abs(final_threshold - base_threshold) > 0.05:
            print(f"\nADAPTIVE THRESHOLD ACTIVE")
            print(f"   Base: {base_threshold:.1%} → Adjusted: {final_threshold:.1%}")
            for name, adj in adjustments:
                if abs(adj) > 0.01:
                    print(f"   {name.capitalize()}: {adj:+.1%}")
        
        return final_threshold
    
    def get_adaptive_confidence_with_signals(self, 
                                            win_rate=None, 
                                            market_volatility=None,
                                            hour=None):
        """Enhanced version including tracked signals"""
        base_threshold = self._calc_confidence(self._current_capital)
        adjustments = []
        
        if hour is None:
            hour = datetime.now().hour
        
        time_adj = self._get_time_based_adjustment(hour)
        adjustments.append(("time", time_adj))
        
        if win_rate is not None:
            wr_adj = self._get_winrate_adjustment(win_rate)
            adjustments.append(("winrate", wr_adj))
        
        if market_volatility is not None:
            vol_adj = self._get_volatility_adjustment(market_volatility)
            adjustments.append(("volatility", vol_adj))
        
        signal_count = self.get_recent_signal_count()
        signal_adj = self._get_signal_count_adjustment(signal_count)
        adjustments.append(("signals", signal_adj))
        
        final_threshold = base_threshold
        for name, adj in adjustments:
            final_threshold += adj
        
        final_threshold = max(0.45, min(0.80, final_threshold))
        
        if abs(final_threshold - base_threshold) > 0.05:
            print(f"\nFULL ADAPTIVE THRESHOLD (with Signal Tracking)")
            print(f"   Base: {base_threshold:.1%} → Adjusted: {final_threshold:.1%}")
            for name, adj in adjustments:
                if abs(adj) > 0.01:
                    direction = "↑" if adj > 0 else "↓"
                    print(f"   {direction} {name.capitalize()}: {adj:+.1%}")
        
        return final_threshold
    
    def get_simple_adaptive_confidence(self, hour=None):
        """Simple time-based threshold (IMMEDIATE USE)"""
        if hour is None:
            hour = datetime.now().hour
        
        base = self._calc_confidence(self._current_capital)
        time_adj = self._get_time_based_adjustment(hour)
        
        final = base + time_adj
        final = max(0.45, min(0.70, final))
        
        return final
    
    def should_use_adaptive_threshold(self):
        """Determine if adaptive thresholds should be used"""
        return self._current_capital >= 300
    
    
    # ===================================================================
    # UPDATE ALL PARAMETERS
    # ===================================================================
    
    def _update_all_params(self):
        """Recalculate ALL parameters based on current capital"""
        cap = self._current_capital
        
        # Core tracking
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
        # NEW: SHORT SELLING
        # ===================================================================
        self.ENABLE_SHORT_SELLING = cap > 3000  # Only for larger accounts
        self.SHORT_POSITION_PCT = 0.5  # Shorts are 50% size of longs
        self.SHORT_MAX_POSITIONS = 2 if cap > 3000 else 0
        self.SHORT_CONFIDENCE_THRESHOLD = 0.65  # Higher threshold for shorts
        self.SHORT_MAX_LEVERAGE = 2  # 2x max leverage
        self.SHORT_SL_MULT = 1.3  # Tighter stops for shorts
        self.SHORT_TP_MULT = 1.0  # Faster profit taking
        
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
        # NEW: MULTI-TIMEFRAME (Always enabled now)
        # ===================================================================
        self.ENABLE_MULTI_TIMEFRAME = True  # Always on
        self.TIMEFRAMES = ['1h', '4h', '1d']
        self.TIMEFRAME_WEIGHTS = [0.5, 0.3, 0.2]
        self.REQUIRE_TIMEFRAME_ALIGNMENT = cap > 1000  # Strict alignment for larger accounts
        
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
        # NEW: CONTRARIAN SIGNALS
        # ===================================================================
        self.ENABLE_CONTRARIAN_SIGNALS = cap > 1000
        self.CONTRARIAN_SELL_THRESHOLD = 0.80  # 80%+ coins showing SELL
        self.CONTRARIAN_BUY_THRESHOLD = 0.80   # 80%+ coins showing BUY
        self.CONTRARIAN_CONFIDENCE = 0.58      # Lower confidence for contrarian
        self.CONTRARIAN_POSITION_SIZE_MULT = 0.7  # Smaller positions
        
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
        # ML & ONLINE LEARNING - FULLY ENABLED
        # ===================================================================
        self.ENABLE_ONLINE_LEARNING = True
        self.ML_ENABLED = True
        self.ML_MODEL_TO_USE = 'ensemble'
        self.ML_CONFIDENCE_THRESHOLD = self.SIGNAL_CONFIDENCE_THRESHOLD
        self.ML_SIGNAL_WEIGHT = 0.40
        self.BEARISH_CONFIDENCE_BOOST = 0.10
        
        self.ENABLE_ENSEMBLE_ML = True
        self.ENSEMBLE_MODELS = ['random_forest', 'lightgbm', 'xgboost']
        self.ENSEMBLE_WEIGHTS = {'rf': 0.35, 'lgb': 0.35, 'xgb': 0.30}
        
        self.ONLINE_LEARNING_METHOD = 'sgd'
        self.UPDATE_MODEL_PER_TRADE = True
        self.MIN_TRADES_BEFORE_UPDATE = 4
        self.BATCH_UPDATE_SIZE = 8
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
        self.ML_FEATURE_SET = 'enhanced'
        self.USE_FEATURE_ENGINEERING = True
        
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
        # SIGNAL TRACKING & FILTERING
        # ===================================================================
        self.ENABLE_SIGNAL_TRACKING = True
        self.SIGNAL_SURGE_WINDOW_SECS = 60
        self.SIGNAL_SURGE_THRESHOLD = 3
        self.AUTO_ADJUST_THRESHOLD_ON_SURGE = True
        self.THRESHOLD_INCREASE_PER_SIGNAL = 0.05
        self.MAX_THRESHOLD_ON_SURGE = 0.80
        self.MIN_THRESHOLD_BASE = 0.45
        
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
        self.LOG_ML_PREDICTIONS = True
        
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
            'adaptive_threshold': True,
            'signal_tracking': True,
            'short_selling': self.ENABLE_SHORT_SELLING,  # NEW
            'contrarian_signals': self.ENABLE_CONTRARIAN_SIGNALS,  # NEW
            'regime_detection': True,  # NEW
            'idle_rebalancing': True,  # NEW
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
    # PROPERTIES & HELPERS (UNCHANGED)
    # ===================================================================
    
    @property
    def total_pnl_pct(self):
        """Calculate P&L percentage"""
        return ((self._current_capital - self._starting_capital) / self._starting_capital) * 100
    
    def get_capital_tier(self):
        """Get current capital tier"""
        return self._get_tier(self._current_capital)
    
    def validate_capital_settings(self):
        """Validate all settings"""
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
            print("All settings validated!")
        
        print(f"{'='*70}\n")
        return len(warnings) == 0
    
    def print_capital_summary(self):
        """Print config summary"""
        tier = self.get_capital_tier()
        pnl = self.total_pnl_pct
        pnl_indicator = "PROFIT" if pnl >= 0 else "LOSS"
        
        print(f"\n{'='*70}")
        print(f"DYNAMIC CONFIG v6.5.0 - Tier: {tier.upper()}")
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
        print(f"Partial TP: ENABLED @ {self.PARTIAL_TP_TRIGGER_ATR_MULT:.1f}x ATR")
        print(f"Watchlist: {len(self.WATCHLIST)} coins | Scan: {self.SCAN_INTERVAL}s")
        print(f"\nML Status:")
        print(f"  ML Enabled: True")
        print(f"  Ensemble ML: True")
        print(f"  Models: {', '.join(self.ENSEMBLE_MODELS)}")
        print(f"  ML Signal Weight: {self.ML_SIGNAL_WEIGHT*100:.0f}%")
        print(f"\nNEW Features (v6.5):")
        print(f"  Short Selling: {'Enabled' if self.ENABLE_SHORT_SELLING else 'Disabled'} (capital > $3000)")
        print(f"  Multi-Timeframe: Always Enabled ({len(self.TIMEFRAMES)} timeframes)")
        print(f"  Market Regime: {self._current_regime}")
        print(f"  Contrarian Signals: {'Enabled' if self.ENABLE_CONTRARIAN_SIGNALS else 'Disabled'}")
        print(f"  Idle Rebalancing: Active")
        print(f"\nAdaptive Features:")
        print(f"  Time-based Threshold: Enabled")
        print(f"  Win-rate Adjustment: Enabled")
        print(f"  Volatility Adjustment: Enabled")
        print(f"  Signal Tracking: Enabled (surge detection at {self.SIGNAL_SURGE_THRESHOLD}+ signals)")
        print(f"  Auto Threshold Adjustment: Enabled")
        print(f"\nLast Update: {self._last_update.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*70}\n")
    
    def print_summary(self):
        """Alias for backward compatibility"""
        self.print_capital_summary()


# Backward compatibility
Config = DynamicConfig


# Testing & Validation
if __name__ == "__main__":
    print("="*70)
    print("DYNAMIC CONFIG v6.5.0 - COMPLETE TESTING")
    print("="*70)
    
    # Initialize
    config = DynamicConfig(starting_capital=1000)
    config.print_summary()
    config.validate_capital_settings()
    
    # Test new features
    print("\n" + "="*70)
    print("NEW FEATURES TESTING")
    print("="*70)
    
    # Test regime detection
    config.update_atr_history("BTC/USDT", 0.005)
    config.update_atr_history("ETH/USDT", 0.006)
    regime = config.get_market_regime()
    print(f"\nCurrent Regime: {regime}")
    
    # Test regime-adjusted params
    params = config.get_regime_adjusted_params()
    print(f"Regime Params: {params}")
    
    # Test idle rebalancing
    print(f"\nHours Idle: {config.get_hours_since_last_trade():.2f}")
    print(f"Should Force: {config.should_force_deployment()}")
    
    # Test adaptive thresholds
    simple_threshold = config.get_simple_adaptive_confidence()
    print(f"\nSimple adaptive (current hour): {simple_threshold:.1%}")
