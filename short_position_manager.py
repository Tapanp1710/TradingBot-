"""
Short Position Manager v1.0
Handles short selling for margin trading
"""
from datetime import datetime
import logging

class ShortPositionManager:
    def __init__(self, config, exchange):
        self.config = config
        self.exchange = exchange
        self.short_positions = []
        self.logger = logging.getLogger(__name__)
    
    def can_open_short(self):
        """Check if short selling is allowed"""
        if not self.config.ENABLE_SHORT_SELLING:
            return False, "Short selling disabled"
        
        if len(self.short_positions) >= self.config.SHORT_MAX_POSITIONS:
            return False, f"Max short positions reached ({self.config.SHORT_MAX_POSITIONS})"
        
        return True, "OK"
    
    def open_short_position(self, symbol, entry_price, confidence, atr):
        """Open a short position"""
        can_short, reason = self.can_open_short()
        if not can_short:
            self.logger.info(f"❌ Cannot short: {reason}")
            return None
        
        # Calculate position size (smaller than longs)
        capital = self.config.CURRENT_CAPITAL
        position_size = capital * self.config.SHORT_POSITION_PCT
        quantity = position_size / entry_price
        
        # Calculate stop-loss (price goes UP = loss for shorts)
        stop_loss = entry_price * (1 + (atr * self.config.SHORT_SL_MULT))
        
        # Calculate take-profit (price goes DOWN = profit for shorts)
        take_profit = entry_price * (1 - (atr * self.config.SHORT_TP_MULT))
        
        position = {
            'symbol': symbol,
            'type': 'SHORT',
            'entry_price': entry_price,
            'quantity': quantity,
            'size': position_size,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'confidence': confidence,
            'entry_time': datetime.now(),
            'leverage': 1,
            'atr': atr
        }
        
        # Execute short order
        if self.config.PAPER_TRADING:
            self.logger.info(f"📉 PAPER SHORT {symbol} @ ${entry_price:.4f}")
            self.logger.info(f"   Size: {quantity:.4f} units (${position_size:.2f})")
            self.logger.info(f"   SL: ${stop_loss:.4f} (+{((stop_loss/entry_price)-1)*100:.2f}%)")
            self.logger.info(f"   TP: ${take_profit:.4f} ({((take_profit/entry_price)-1)*100:.2f}%)")
        else:
            try:
                order = self.exchange.create_order(
                    symbol=symbol,
                    type='market',
                    side='sell',
                    amount=quantity,
                    params={'leverage': 1}
                )
                position['order_id'] = order['id']
                self.logger.info(f"📉 REAL SHORT {symbol} @ ${entry_price:.4f}")
            except Exception as e:
                self.logger.error(f"❌ Short order failed: {e}")
                return None
        
        self.short_positions.append(position)
        return position
    
    def monitor_short_positions(self):
        """Check short positions for TP/SL"""
        closed_positions = []
        
        for position in self.short_positions[:]:
            try:
                symbol = position['symbol']
                current_price = self._get_current_price(symbol)
                
                entry = position['entry_price']
                pnl_pct = ((entry - current_price) / entry) * 100  # Inverted for shorts
                
                # Check stop-loss (price went UP)
                if current_price >= position['stop_loss']:
                    self.logger.info(f"🛑 SHORT STOP-LOSS {symbol} @ ${current_price:.4f}")
                    closed = self._close_short(position, current_price, 'STOP_LOSS')
                    if closed:
                        closed_positions.append(closed)
                        self.short_positions.remove(position)
                
                # Check take-profit (price went DOWN)
                elif current_price <= position['take_profit']:
                    self.logger.info(f"💰 SHORT TAKE-PROFIT {symbol} @ ${current_price:.4f}")
                    closed = self._close_short(position, current_price, 'TAKE_PROFIT')
                    if closed:
                        closed_positions.append(closed)
                        self.short_positions.remove(position)
                
            except Exception as e:
                self.logger.error(f"❌ Error monitoring short {symbol}: {e}")
        
        return closed_positions
    
    def _close_short(self, position, exit_price, reason):
        """Close short position"""
        symbol = position['symbol']
        entry = position['entry_price']
        quantity = position['quantity']
        
        # Calculate P&L (inverted for shorts)
        pnl_pct = ((entry - exit_price) / entry) * 100
        pnl_usd = position['size'] * (pnl_pct / 100)
        
        # Calculate fees
        fees = position['size'] * self.config.TRADING_FEE * 2  # Entry + exit
        pnl_usd -= fees
        
        if self.config.PAPER_TRADING:
            self.logger.info(f"   Entry: ${entry:.4f} → Exit: ${exit_price:.4f}")
            self.logger.info(f"   P&L: ${pnl_usd:+.2f} ({pnl_pct:+.2f}%)")
            self.logger.info(f"   Fees: ${fees:.2f}")
        else:
            try:
                self.exchange.create_order(
                    symbol=symbol,
                    type='market',
                    side='buy',
                    amount=quantity
                )
                self.logger.info(f"✅ Short closed via buy order")
            except Exception as e:
                self.logger.error(f"❌ Failed to close short: {e}")
                return None
        
        return {
            'symbol': symbol,
            'type': 'SHORT',
            'entry_price': entry,
            'exit_price': exit_price,
            'pnl': pnl_usd,
            'pnl_pct': pnl_pct,
            'fees': fees,
            'reason': reason,
            'hold_time': (datetime.now() - position['entry_time']).total_seconds() / 3600
        }
    
    def _get_current_price(self, symbol):
        """Get current market price"""
        ticker = self.exchange.fetch_ticker(symbol)
        return ticker['last']
    
    def get_short_summary(self):
        """Get summary of short positions"""
        if not self.short_positions:
            return "No short positions"
        
        summary = "\n📉 SHORT POSITIONS:\n"
        for pos in self.short_positions:
            current_price = self._get_current_price(pos['symbol'])
            pnl_pct = ((pos['entry_price'] - current_price) / pos['entry_price']) * 100
            summary += f"   {pos['symbol']}: ${current_price:.4f} ({pnl_pct:+.2f}%)\n"
        
        return summary

