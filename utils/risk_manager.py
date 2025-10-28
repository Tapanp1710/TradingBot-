"""
Risk Management Module v3.0 - PRODUCTION READY
- Input validation
- Kelly Criterion support
- Dynamic risk adjustment
- Portfolio risk monitoring
- ATR-aware position sizing
"""
import logging
from typing import Dict, Tuple, Optional

logger = logging.getLogger('TradingBot')


class RiskManager:
    """Manage trade risk and position sizing with production safeguards"""
    
    def __init__(self, config):
        self.config = config
        
        # Validate config
        self._validate_config()
        
        # Risk limits (with defaults)
        self.max_position_pct = getattr(config, 'MAX_POSITION_PCT', 0.15)  # FIXED from 0.25 to 0.15
        self.min_position_usd = getattr(config, 'MIN_POSITION_USD', 50)
        self.min_capital_usd = getattr(config, 'MIN_CAPITAL_USD', 100)
        
        # Kelly Criterion settings
        self.use_kelly = getattr(config, 'USE_KELLY_CRITERION', False)
        self.kelly_fraction = getattr(config, 'KELLY_FRACTION', 0.25)  # Quarter Kelly
        
        logger.info("✅ Risk Manager initialized")
        logger.info(f"   Max position: {self.max_position_pct:.0%}")
        logger.info(f"   Min position: ${self.min_position_usd}")
        logger.info(f"   Kelly Criterion: {'ENABLED' if self.use_kelly else 'DISABLED'}")
    
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
        total_capital: float = None,  # NEW: Added total_capital parameter
        win_rate: Optional[float] = None,
        avg_win: Optional[float] = None,
        avg_loss: Optional[float] = None
    ) -> float:
        """
        Calculate position size with multiple methods
        
        CRITICAL FIX: Now uses total_capital for max position calculation
        to avoid "exceeds capital" bug
        
        Args:
            available_capital: Available capital for trading
            confidence: Signal confidence (0-1)
            total_capital: Total portfolio value (IMPORTANT!)
            win_rate: Historical win rate (for Kelly)
            avg_win: Average win percentage (for Kelly)
            avg_loss: Average loss percentage (for Kelly)
        
        Returns:
            Position size in dollars
        """
        
        # Use total capital if provided, otherwise fallback to available
        if total_capital is None:
            total_capital = available_capital
        
        # Input validation
        if available_capital <= 0 or total_capital <= 0:
            logger.warning(f"Invalid capital: available=${available_capital}, total=${total_capital}")
            return 0
        
        if not (0 <= confidence <= 1):
            logger.warning(f"Invalid confidence: {confidence}, clamping to [0,1]")
            confidence = max(0, min(1, confidence))
        
        # Use Kelly Criterion if enabled and stats available
        if self.use_kelly and all([win_rate, avg_win, avg_loss]):
            position_size = self._kelly_position_size(
                total_capital, confidence, win_rate, avg_win, avg_loss
            )
        else:
            # Standard fixed-risk sizing
            position_size = self._fixed_risk_position_size(
                available_capital, total_capital, confidence
            )
        
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
        
        # CRITICAL: Base risk on TOTAL capital, not available
        base_risk = total_capital * self.config.MAX_RISK_PER_TRADE
        
        # Adjust for confidence if enabled
        if getattr(self.config, 'ENABLE_ADAPTIVE_SIZING', False):
            risk_multiplier = self._get_confidence_multiplier(confidence)
            adjusted_risk = base_risk * risk_multiplier
        else:
            adjusted_risk = base_risk
        
        # Calculate position size: Risk / Stop Loss %
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
        """
        Calculate position size using Kelly Criterion
        
        Kelly % = (win_rate * avg_win - (1 - win_rate) * avg_loss) / avg_win
        """
        
        try:
            # Validate inputs
            if avg_win <= 0:
                return 0
            
            # Kelly formula
            kelly_pct = (win_rate * avg_win - (1 - win_rate) * avg_loss) / avg_win
            
            # Clamp to reasonable range
            kelly_pct = max(0, min(kelly_pct, 0.5))  # Max 50%
            
            # Apply Kelly fraction (e.g., quarter Kelly for safety)
            fractional_kelly = kelly_pct * self.kelly_fraction
            
            # Adjust for confidence
            adjusted_kelly = fractional_kelly * confidence
            
            # Calculate position size
            position_size = total_capital * adjusted_kelly
            
            logger.debug(f"Kelly: {kelly_pct:.2%} → Fractional: {fractional_kelly:.2%} "
                        f"→ Adjusted: {adjusted_kelly:.2%}")
            
            return position_size
        
        except Exception as e:
            logger.error(f"Kelly calculation error: {e}")
            return self._fixed_risk_position_size(total_capital, total_capital, confidence)
    
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
            # For ATR, use fallback for calculation
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
        
        # CRITICAL FIX: Maximum position as % of TOTAL capital
        max_position = total_capital * self.max_position_pct
        position_size = min(position_size, max_position)
        
        # Cannot exceed available capital (with safety buffer)
        position_size = min(position_size, available_capital * 0.95)
        
        # Minimum position size
        if position_size < self.min_position_usd:
            return 0
        
        # Round to 2 decimals
        return round(position_size, 2)
    
    def check_portfolio_risk(
        self,
        open_positions: Dict,
        available_capital: float,
        total_capital: float
    ) -> Tuple[bool, float]:
        """
        Check if portfolio risk is acceptable
        
        Returns:
            (is_acceptable: bool, current_risk_pct: float)
        """
        
        if not open_positions:
            return True, 0.0
        
        # Calculate total at-risk capital
        total_risk = 0
        
        for symbol, position in open_positions.items():
            try:
                entry_price = position.get('entry_price', 0)
                stop_loss = position.get('stop_loss', 0)
                amount = position.get('amount', 0)
                
                # Risk per position = (entry - stop_loss) * amount
                if entry_price > stop_loss > 0:
                    risk = (entry_price - stop_loss) * amount
                else:
                    # Fallback: use position size * stop loss %
                    risk = position.get('position_size', 0) * self._get_stop_loss_pct()
                
                total_risk += risk
            except Exception as e:
                logger.error(f"Error calculating risk for {symbol}: {e}")
                continue
        
        # Risk as % of total capital
        risk_pct = total_risk / total_capital if total_capital > 0 else 0
        
        # Check limit
        max_risk = self.config.MAX_PORTFOLIO_RISK
        is_acceptable = risk_pct <= max_risk
        
        if not is_acceptable:
            logger.warning(f"⚠️ Portfolio risk {risk_pct:.2%} exceeds limit {max_risk:.2%}")
        
        return is_acceptable, risk_pct
    
    def should_take_trade(
        self,
        available_capital: float,
        open_positions_count: int,
        portfolio_risk_pct: float = 0
    ) -> Tuple[bool, str]:
        """
        Determine if new trade should be taken
        
        Returns:
            (should_take: bool, reason: str)
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
        
        # Validate stop loss
        if stop_loss <= 0 or stop_loss >= entry_price:
            logger.warning(f"Invalid stop loss {stop_loss} for entry {entry_price}")
            stop_loss = entry_price * 0.98  # 2% fallback
        
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
        
        # Validate take profit
        if take_profit <= entry_price:
            logger.warning(f"Invalid take profit {take_profit} for entry {entry_price}")
            take_profit = entry_price * 1.03  # 3% fallback
        
        return round(take_profit, 8)
    
    def calculate_risk_reward_ratio(
        self,
        entry_price: float,
        stop_loss: float,
        take_profit: float
    ) -> float:
        """
        Calculate risk-reward ratio
        
        Returns:
            Risk-reward ratio (e.g., 2.0 means 2:1 reward:risk)
        """
        
        if entry_price <= 0 or stop_loss <= 0 or take_profit <= 0:
            return 0
        
        risk = entry_price - stop_loss
        reward = take_profit - entry_price
        
        if risk <= 0:
            return 0
        
        return reward / risk
    
    def get_stats(self) -> Dict:
        """Get risk manager statistics"""
        return {
            'max_risk_per_trade': self.config.MAX_RISK_PER_TRADE,
            'max_portfolio_risk': self.config.MAX_PORTFOLIO_RISK,
            'max_positions': self.config.MAX_OPEN_POSITIONS,
            'max_position_pct': self.max_position_pct,
            'min_position_usd': self.min_position_usd,
            'adaptive_sizing': getattr(self.config, 'ENABLE_ADAPTIVE_SIZING', False),
            'kelly_enabled': self.use_kelly,
            'kelly_fraction': self.kelly_fraction if self.use_kelly else None
        }
