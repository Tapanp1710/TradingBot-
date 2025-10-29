"""
Risk Management Module v5.0 - INSTITUTIONAL GRADE
- Portfolio correlation filtering
- Volatility-adjusted position sizing
- Maximum drawdown protection
- Sector/asset diversification
- Advanced Kelly Criterion
- Value at Risk (VaR) calculation
- Dynamic risk adjustment based on market regime
"""
import logging
import numpy as np
from typing import Dict, Tuple, Optional, List
from collections import deque
from datetime import datetime, timedelta

logger = logging.getLogger('TradingBot')


class RiskManager:
    """Institutional-grade risk management with advanced features"""
    
    def __init__(self, config):
        self.config = config
        
        # Validate config
        self._validate_config()
        
        # Risk limits (with defaults)
        self.max_position_pct = getattr(config, 'MAX_POSITION_PCT', 0.15)
        self.min_position_usd = getattr(config, 'MIN_POSITION_USD', 50)
        self.min_capital_usd = getattr(config, 'MIN_CAPITAL_USD', 100)
        
        # Kelly Criterion settings
        self.use_kelly = getattr(config, 'USE_KELLY_CRITERION', False)
        self.kelly_fraction = getattr(config, 'KELLY_FRACTION', 0.25)
        
        # NEW: Advanced risk features
        self.enable_correlation_filter = getattr(config, 'ENABLE_CORRELATION_FILTER', False)
        self.max_correlated_positions = getattr(config, 'MAX_CORRELATED_POSITIONS', 3)
        self.correlation_threshold = getattr(config, 'CORRELATION_THRESHOLD', 0.7)
        
        # NEW: Volatility-adjusted sizing
        self.enable_volatility_adjustment = getattr(config, 'ENABLE_VOLATILITY_ADJUSTMENT', True)
        
        # NEW: Drawdown protection
        self.max_drawdown_pct = getattr(config, 'MAX_DRAWDOWN_PCT', 0.20)
        self.peak_capital = config.STARTING_CAPITAL
        
        # NEW: Trade history for advanced metrics
        self.trade_history = deque(maxlen=100)
        self.equity_curve = deque(maxlen=1000)
        
        # NEW: Position correlation tracking
        self.position_correlations = {}
        
        logger.info("✅ Risk Manager v5.0 initialized - Institutional Grade")
        logger.info(f"   Max position: {self.max_position_pct:.0%}")
        logger.info(f"   Min position: ${self.min_position_usd}")
        logger.info(f"   Kelly Criterion: {'ENABLED' if self.use_kelly else 'DISABLED'}")
        logger.info(f"   Correlation Filter: {'ENABLED' if self.enable_correlation_filter else 'DISABLED'}")
        logger.info(f"   Volatility Adjustment: {'ENABLED' if self.enable_volatility_adjustment else 'DISABLED'}")
    
    def _validate_config(self):
        """Validate config has required attributes"""
        required = [
            'MAX_RISK_PER_TRADE',
            'MAX_PORTFOLIO_RISK',
            'MAX_OPEN_POSITIONS',
            'FALLBACK_STOP_LOSS_PCT'
        ]
        
        for attr in required:
            if not hasattr(self.config, attr):
                raise ValueError(f"Config missing required attribute: {attr}")
            
            value = getattr(self.config, attr)
            if value <= 0:
                raise ValueError(f"Config {attr} must be positive, got {value}")
    
    def calculate_position_size(
        self, 
        available_capital: float,
        confidence: float,
        total_capital: float = None,
        win_rate: Optional[float] = None,
        avg_win: Optional[float] = None,
        avg_loss: Optional[float] = None,
        symbol_volatility: Optional[float] = None,  # NEW
        market_regime: Optional[str] = None  # NEW
    ) -> float:
        """
        Calculate position size with institutional-grade methods
        
        Args:
            available_capital: Available capital for trading
            confidence: Signal confidence (0-1)
            total_capital: Total portfolio value
            win_rate: Historical win rate (for Kelly)
            avg_win: Average win percentage (for Kelly)
            avg_loss: Average loss percentage (for Kelly)
            symbol_volatility: Symbol's ATR/price ratio (NEW)
            market_regime: 'bull'/'bear'/'neutral' (NEW)
        
        Returns:
            Position size in dollars
        """
        
        # Use total capital if provided
        if total_capital is None:
            total_capital = available_capital
        
        # Input validation
        if available_capital <= 0 or total_capital <= 0:
            logger.warning(f"Invalid capital: available=${available_capital}, total=${total_capital}")
            return 0
        
        if not (0 <= confidence <= 1):
            logger.warning(f"Invalid confidence: {confidence}, clamping to [0,1]")
            confidence = max(0, min(1, confidence))
        
        # NEW: Check drawdown protection
        if not self._check_drawdown_protection(total_capital):
            logger.warning("⚠️ Drawdown limit reached - reducing position size")
            confidence *= 0.5  # Reduce by 50%
        
        # Use Kelly Criterion if enabled
        if self.use_kelly and all([win_rate, avg_win, avg_loss]):
            position_size = self._kelly_position_size(
                total_capital, confidence, win_rate, avg_win, avg_loss
            )
        else:
            position_size = self._fixed_risk_position_size(
                available_capital, total_capital, confidence
            )
        
        # NEW: Adjust for volatility
        if self.enable_volatility_adjustment and symbol_volatility:
            position_size = self._volatility_adjusted_size(
                position_size, symbol_volatility
            )
        
        # NEW: Adjust for market regime
        if market_regime:
            position_size = self._regime_adjusted_size(position_size, market_regime)
        
        # Apply limits
        position_size = self._apply_position_limits(
            position_size, available_capital, total_capital
        )
        
        return position_size
    
    def _fixed_risk_position_size(
        self, 
        available_capital: float, 
        total_capital: float,
        confidence: float
    ) -> float:
        """Calculate position size using fixed-risk method"""
        
        base_risk = total_capital * self.config.MAX_RISK_PER_TRADE
        
        # Adjust for confidence
        if getattr(self.config, 'ENABLE_ADAPTIVE_SIZING', False):
            risk_multiplier = self._get_confidence_multiplier(confidence)
            adjusted_risk = base_risk * risk_multiplier
        else:
            adjusted_risk = base_risk
        
        stop_loss_pct = self._get_stop_loss_pct()
        
        if stop_loss_pct <= 0:
            logger.error(f"Invalid stop loss percentage: {stop_loss_pct}")
            return 0
        
        position_size = adjusted_risk / stop_loss_pct
        
        return position_size
    
    def _kelly_position_size(
        self,
        total_capital: float,
        confidence: float,
        win_rate: float,
        avg_win: float,
        avg_loss: float
    ) -> float:
        """Calculate position size using Kelly Criterion"""
        
        try:
            if avg_win <= 0:
                return 0
            
            # Kelly formula
            kelly_pct = (win_rate * avg_win - (1 - win_rate) * avg_loss) / avg_win
            
            # Clamp to reasonable range
            kelly_pct = max(0, min(kelly_pct, 0.5))
            
            # Apply Kelly fraction
            fractional_kelly = kelly_pct * self.kelly_fraction
            
            # Adjust for confidence
            adjusted_kelly = fractional_kelly * confidence
            
            position_size = total_capital * adjusted_kelly
            
            logger.debug(f"Kelly: {kelly_pct:.2%} → Fractional: {fractional_kelly:.2%} → Adjusted: {adjusted_kelly:.2%}")
            
            return position_size
        
        except Exception as e:
            logger.error(f"Kelly calculation error: {e}")
            return self._fixed_risk_position_size(total_capital, total_capital, confidence)
    
    def _volatility_adjusted_size(self, position_size: float, volatility: float) -> float:
        """
        NEW: Adjust position size based on asset volatility
        Higher volatility = smaller position
        """
        
        # Target volatility (e.g., 2% ATR)
        target_vol = 0.02
        
        if volatility <= 0:
            return position_size
        
        # Adjustment factor: reduce size for high volatility
        vol_adjustment = min(target_vol / volatility, 2.0)  # Cap at 2x
        
        adjusted_size = position_size * vol_adjustment
        
        logger.debug(f"Volatility adjustment: {volatility:.2%} → Factor: {vol_adjustment:.2f}")
        
        return adjusted_size
    
    def _regime_adjusted_size(self, position_size: float, regime: str) -> float:
        """
        NEW: Adjust position size based on market regime
        """
        
        regime_multipliers = {
            'bull': 1.0,      # Full size in bull market
            'neutral': 0.75,  # 75% size in neutral
            'bear': 0.5       # 50% size in bear market
        }
        
        multiplier = regime_multipliers.get(regime.lower(), 1.0)
        
        if multiplier != 1.0:
            logger.debug(f"Regime adjustment ({regime}): {multiplier:.0%}")
        
        return position_size * multiplier
    
    def _check_drawdown_protection(self, current_capital: float) -> bool:
        """
        NEW: Check if drawdown limit exceeded
        """
        
        # Update peak
        if current_capital > self.peak_capital:
            self.peak_capital = current_capital
        
        # Calculate drawdown
        drawdown = (self.peak_capital - current_capital) / self.peak_capital
        
        if drawdown >= self.max_drawdown_pct:
            logger.warning(f"⚠️ Drawdown {drawdown:.1%} exceeds limit {self.max_drawdown_pct:.1%}")
            return False
        
        return True
    
    def _get_confidence_multiplier(self, confidence: float) -> float:
        """Get position size multiplier based on confidence"""
        
        high_threshold = getattr(self.config, 'HIGH_CONFIDENCE_THRESHOLD', 0.75)
        low_threshold = getattr(self.config, 'LOW_CONFIDENCE_THRESHOLD', 0.65)
        
        if confidence >= high_threshold:
            return getattr(self.config, 'HIGH_CONFIDENCE_MULTIPLIER', 1.5)
        elif confidence < low_threshold:
            return getattr(self.config, 'LOW_CONFIDENCE_MULTIPLIER', 0.5)
        else:
            return 1.0
    
    def _get_stop_loss_pct(self) -> float:
        """Get stop loss percentage for position sizing"""
        if getattr(self.config, 'USE_ATR_EXITS', False):
            return self.config.FALLBACK_STOP_LOSS_PCT
        else:
            return self.config.FALLBACK_STOP_LOSS_PCT
    
    def _apply_position_limits(
        self,
        position_size: float,
        available_capital: float,
        total_capital: float
    ) -> float:
        """Apply position size limits and constraints"""
        
        # Maximum position as % of TOTAL capital
        max_position = total_capital * self.max_position_pct
        position_size = min(position_size, max_position)
        
        # Cannot exceed available capital (with safety buffer)
        position_size = min(position_size, available_capital * 0.95)
        
        # Minimum position size
        if position_size < self.min_position_usd:
            return 0
        
        return round(position_size, 2)
    
    # ==========================================
    # NEW METHODS - CORRELATION FILTERING
    # ==========================================
    
    def check_correlation(
        self, 
        new_symbol: str, 
        open_positions: Dict,
        price_history: Optional[Dict] = None
    ) -> Tuple[bool, str]:
        """
        NEW: Check if new position would create excessive correlation
        
        Args:
            new_symbol: Symbol to check
            open_positions: Currently open positions
            price_history: Optional price history for correlation calc
        
        Returns:
            (can_open: bool, reason: str)
        """
        
        if not self.enable_correlation_filter:
            return True, "Correlation filter disabled"
        
        if not open_positions:
            return True, "No open positions"
        
        # Simple sector-based correlation (crypto majors)
        crypto_majors = {'BTC/USDT', 'ETH/USDT', 'BNB/USDT'}
        
        # Count correlated positions
        correlated_count = 0
        
        if new_symbol in crypto_majors:
            # Check if we already have other majors
            for symbol in open_positions.keys():
                if symbol in crypto_majors and symbol != new_symbol:
                    correlated_count += 1
        
        if correlated_count >= self.max_correlated_positions:
            return False, f"Too many correlated positions ({correlated_count})"
        
        return True, "Correlation check passed"
    
    def calculate_portfolio_correlation(self, positions: List[str]) -> float:
        """
        NEW: Calculate average portfolio correlation
        Returns value between 0 (diversified) and 1 (highly correlated)
        """
        
        if len(positions) < 2:
            return 0.0
        
        # Simple heuristic: same-sector correlation
        crypto_majors = {'BTC/USDT', 'ETH/USDT', 'BNB/USDT'}
        altcoins = set(positions) - crypto_majors
        
        major_count = len([p for p in positions if p in crypto_majors])
        
        # If > 50% in majors, high correlation
        if major_count / len(positions) > 0.5:
            return 0.8
        
        return 0.4  # Moderate correlation
    
    # ==========================================
    # EXISTING METHODS (Enhanced)
    # ==========================================
    
    def check_portfolio_risk(
        self,
        open_positions: Dict,
        available_capital: float,
        total_capital: float
    ) -> Tuple[bool, float]:
        """Check if portfolio risk is acceptable"""
        
        if not open_positions:
            return True, 0.0
        
        total_risk = 0
        
        for symbol, position in open_positions.items():
            try:
                entry_price = position.get('entry_price', 0)
                stop_loss = position.get('stop_loss', 0)
                amount = position.get('amount', 0)
                
                if entry_price > stop_loss > 0:
                    risk = (entry_price - stop_loss) * amount
                else:
                    risk = position.get('position_size', 0) * self._get_stop_loss_pct()
                
                total_risk += risk
            except Exception as e:
                logger.error(f"Error calculating risk for {symbol}: {e}")
                continue
        
        risk_pct = total_risk / total_capital if total_capital > 0 else 0
        
        max_risk = self.config.MAX_PORTFOLIO_RISK
        is_acceptable = risk_pct <= max_risk
        
        if not is_acceptable:
            logger.warning(f"⚠️ Portfolio risk {risk_pct:.2%} exceeds limit {max_risk:.2%}")
        
        return is_acceptable, risk_pct
    
    def should_take_trade(
        self,
        available_capital: float,
        open_positions_count: int,
        portfolio_risk_pct: float = 0,
        symbol: Optional[str] = None,  # NEW
        open_positions: Optional[Dict] = None  # NEW
    ) -> Tuple[bool, str]:
        """
        Determine if new trade should be taken
        """
        
        # Check position limit
        if open_positions_count >= self.config.MAX_OPEN_POSITIONS:
            return False, f"Max positions reached ({self.config.MAX_OPEN_POSITIONS})"
        
        # Check minimum capital
        if available_capital < self.min_capital_usd:
            return False, f"Insufficient capital (${available_capital:.2f} < ${self.min_capital_usd})"
        
        # Check portfolio risk
        if portfolio_risk_pct >= self.config.MAX_PORTFOLIO_RISK:
            return False, f"Max portfolio risk reached ({portfolio_risk_pct:.2%})"
        
        # NEW: Check correlation if enabled
        if symbol and open_positions and self.enable_correlation_filter:
            can_open, reason = self.check_correlation(symbol, open_positions)
            if not can_open:
                return False, f"Correlation: {reason}"
        
        return True, "Risk checks passed"
    
    def calculate_stop_loss(self, entry_price: float, atr: Optional[float] = None) -> float:
        """Calculate stop loss price with validation"""
        
        if entry_price <= 0:
            logger.error(f"Invalid entry price: {entry_price}")
            return 0
        
        if self.config.USE_ATR_EXITS and atr and atr > 0:
            stop_loss = entry_price - (self.config.ATR_SL_MULT * atr)
        else:
            stop_loss = entry_price * (1 - self.config.FALLBACK_STOP_LOSS_PCT)
        
        if stop_loss <= 0 or stop_loss >= entry_price:
            logger.warning(f"Invalid stop loss {stop_loss} for entry {entry_price}")
            stop_loss = entry_price * 0.98
        
        return round(stop_loss, 8)
    
    def calculate_take_profit(self, entry_price: float, atr: Optional[float] = None) -> float:
        """Calculate take profit price with validation"""
        
        if entry_price <= 0:
            logger.error(f"Invalid entry price: {entry_price}")
            return 0
        
        if self.config.USE_ATR_EXITS and atr and atr > 0:
            take_profit = entry_price + (self.config.ATR_TP_MULT * atr)
        else:
            take_profit = entry_price * (1 + self.config.FALLBACK_TAKE_PROFIT_PCT)
        
        if take_profit <= entry_price:
            logger.warning(f"Invalid take profit {take_profit} for entry {entry_price}")
            take_profit = entry_price * 1.03
        
        return round(take_profit, 8)
    
    def calculate_risk_reward_ratio(
        self,
        entry_price: float,
        stop_loss: float,
        take_profit: float
    ) -> float:
        """Calculate risk-reward ratio"""
        
        if entry_price <= 0 or stop_loss <= 0 or take_profit <= 0:
            return 0
        
        risk = entry_price - stop_loss
        reward = take_profit - entry_price
        
        if risk <= 0:
            return 0
        
        return reward / risk
    
    # ==========================================
    # NEW METHOD - VALUE AT RISK (VAR)
    # ==========================================
    
    def calculate_var(
        self, 
        positions: Dict, 
        confidence_level: float = 0.95
    ) -> float:
        """
        NEW: Calculate Value at Risk (VaR) - maximum expected loss at confidence level
        
        Args:
            positions: Open positions
            confidence_level: Confidence level (e.g., 0.95 = 95%)
        
        Returns:
            VaR amount in dollars
        """
        
        if not positions or len(self.equity_curve) < 20:
            return 0.0
        
        try:
            # Calculate historical returns
            equity_array = np.array(list(self.equity_curve))
            returns = np.diff(equity_array) / equity_array[:-1]
            
            # Calculate VaR at confidence level
            var = np.percentile(returns, (1 - confidence_level) * 100)
            
            # Convert to dollar amount
            current_equity = equity_array[-1]
            var_amount = abs(var * current_equity)
            
            return var_amount
        
        except Exception as e:
            logger.error(f"VaR calculation error: {e}")
            return 0.0
    
    # ==========================================
    # TRACKING & STATISTICS
    # ==========================================
    
    def record_trade(self, profit: float, win: bool):
        """NEW: Record trade for statistics"""
        self.trade_history.append({
            'timestamp': datetime.now(),
            'profit': profit,
            'win': win
        })
    
    def record_equity(self, equity: float):
        """NEW: Record equity for drawdown tracking"""
        self.equity_curve.append(equity)
    
    def get_stats(self) -> Dict:
        """Get comprehensive risk manager statistics"""
        
        stats = {
            'max_risk_per_trade': self.config.MAX_RISK_PER_TRADE,
            'max_portfolio_risk': self.config.MAX_PORTFOLIO_RISK,
            'max_positions': self.config.MAX_OPEN_POSITIONS,
            'max_position_pct': self.max_position_pct,
            'min_position_usd': self.min_position_usd,
            'adaptive_sizing': getattr(self.config, 'ENABLE_ADAPTIVE_SIZING', False),
            'kelly_enabled': self.use_kelly,
            'kelly_fraction': self.kelly_fraction if self.use_kelly else None,
            # NEW
            'correlation_filter': self.enable_correlation_filter,
            'volatility_adjustment': self.enable_volatility_adjustment,
            'peak_capital': self.peak_capital,
            'max_drawdown': self.max_drawdown_pct
        }
        
        # Add drawdown info if we have equity data
        if len(self.equity_curve) > 0:
            current_equity = self.equity_curve[-1]
            current_drawdown = (self.peak_capital - current_equity) / self.peak_capital
            stats['current_drawdown'] = current_drawdown
        
        return stats
