"""
Bounce Trading Strategy - Buy Dips at Weekly Lows
Reserves one position slot for mean reversion trades
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, Dict
import logging

logger = logging.getLogger('TradingBot')

class BounceTrader:
    """Handle bounce trading for oversold coins at weekly lows"""
    
    def __init__(self, config, exchange):
        self.config = config
        self.exchange = exchange
        self.bounce_positions = {}  # Track bounce trades separately
        
    def scan_for_bounce_opportunity(self, watchlist) -> Optional[Dict]:
        """
        Scan for coins at weekly lows - bounce candidates
        Returns: opportunity dict or None
        """
        if not self.config.ENABLE_BOUNCE_TRADING:
            return None
        
        try:
            logger.info("🎯 Scanning for BOUNCE opportunity (weekly low buys)...")
            
            best_opportunity = None
            best_dip_pct = 0
            
            for symbol in watchlist:
                try:
                    # Fetch 7 day data
                    df = self.exchange.fetch_ohlcv(symbol, '1d', limit=7)
                    if df is None or len(df) < 7:
                        continue
                    
                    # Get current price
                    current_price = self.exchange.fetch_current_price(symbol)
                    if not current_price or current_price <= 0:
                        continue
                    
                    # Calculate weekly low
                    weekly_low = df['low'].min()
                    weekly_high = df['high'].max()
                    weekly_range = weekly_high - weekly_low
                    
                    # Check if current price is near weekly low
                    distance_from_low = ((current_price - weekly_low) / weekly_low) * 100
                    dip_magnitude = ((weekly_high - current_price) / weekly_high) * 100
                    
                    logger.debug(f"   {symbol}: Current=${current_price:.4f} | "
                               f"Weekly Low=${weekly_low:.4f} | Distance={distance_from_low:.2f}%")
                    
                    # Check if within threshold of weekly low
                    threshold = self.config.BOUNCE_THRESHOLD_PCT * 100
                    
                    if distance_from_low <= threshold and dip_magnitude > best_dip_pct:
                        # This is a good bounce candidate
                        best_dip_pct = dip_magnitude
                        
                        # Calculate position size
                        position_size = max(
                            self.config.BOUNCE_MIN_POSITION_SIZE,
                            self.config.STARTING_CAPITAL * 0.10  # 10% of capital
                        )
                        
                        # Calculate stops
                        stop_loss = current_price * (1 - self.config.BOUNCE_STOP_LOSS_PCT)
                        
                        best_opportunity = {
                            'symbol': symbol,
                            'signal': 'BUY',
                            'strategy': 'BOUNCE',
                            'confidence': 0.85,  # High confidence - at weekly low
                            'price': current_price,
                            'position_size': position_size,
                            'stop_loss': stop_loss,
                            'take_profit': None,  # No fixed TP
                            'weekly_low': weekly_low,
                            'weekly_high': weekly_high,
                            'dip_pct': dip_magnitude,
                            'distance_from_low_pct': distance_from_low,
                            'trailing_config': {
                                'activate_pct': self.config.BOUNCE_TRAIL_ACTIVATE_PCT,
                                'distance_pct': self.config.BOUNCE_TRAIL_DISTANCE_PCT
                            }
                        }
                        
                        logger.info(f"💎 {symbol}: BOUNCE candidate - {dip_magnitude:.1f}% off weekly high | "
                                  f"{distance_from_low:.2f}% from weekly low")
                
                except Exception as e:
                    logger.debug(f"Error scanning {symbol} for bounce: {e}")
                    continue
            
            if best_opportunity:
                logger.info(f"✅ BOUNCE opportunity found: {best_opportunity['symbol']} - "
                          f"{best_opportunity['dip_pct']:.1f}% dip | "
                          f"${best_opportunity['position_size']:.0f} position")
            
            return best_opportunity
            
        except Exception as e:
            logger.error(f"Bounce scan error: {e}")
            return None
    
    def monitor_bounce_position(self, symbol: str, position: Dict, current_price: float) -> Optional[str]:
        """
        Monitor bounce position with trailing stop only (no fixed TP)
        Returns: 'SELL' if exit triggered, None otherwise
        """
        try:
            entry_price = position['entry_price']
            stop_loss = position['stop_loss']
            strategy = position.get('strategy', 'REGULAR')
            
            if strategy != 'BOUNCE':
                return None
            
            # Calculate current P&L
            pnl_pct = ((current_price - entry_price) / entry_price) * 100
            
            # Initialize trailing if not exists
            if 'trailing_active' not in position:
                position['trailing_active'] = False
                position['highest_price'] = entry_price
            
            # Update highest price
            if current_price > position['highest_price']:
                position['highest_price'] = current_price
            
            # Activate trailing if profit threshold reached
            activate_pct = position.get('trailing_config', {}).get('activate_pct', 0.01) * 100
            
            if not position['trailing_active'] and pnl_pct >= activate_pct:
                position['trailing_active'] = True
                logger.info(f"🎯 {symbol}: BOUNCE trailing activated @ ${current_price:.4f} (+{pnl_pct:.2f}%)")
            
            # Update trailing stop if active
            if position['trailing_active']:
                trail_distance = position.get('trailing_config', {}).get('distance_pct', 0.015)
                new_stop = position['highest_price'] * (1 - trail_distance)
                
                if new_stop > position['stop_loss']:
                    position['stop_loss'] = new_stop
                    logger.info(f"📈 {symbol}: BOUNCE trailing stop moved to ${new_stop:.4f} "
                              f"(protecting +{((new_stop - entry_price) / entry_price * 100):.2f}%)")
            
            # Check if stop loss hit
            if current_price <= position['stop_loss']:
                final_pnl = ((current_price - entry_price) / entry_price) * 100
                logger.info(f"🛑 {symbol}: BOUNCE trailing stop hit @ ${current_price:.4f} | "
                          f"P&L: {final_pnl:+.2f}%")
                return 'SELL'
            
            return None
            
        except Exception as e:
            logger.error(f"Bounce monitoring error for {symbol}: {e}")
            return None
