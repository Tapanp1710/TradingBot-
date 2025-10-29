"""
Performance Monitor v1.0
Real-time performance tracking and reporting
"""
import logging
import pandas as pd
from datetime import datetime
from typing import Dict, List

logger = logging.getLogger('TradingBot')

class PerformanceMonitor:
    """Monitor and report bot performance metrics"""
    
    def __init__(self, bot):
        """
        Initialize performance monitor
        Args:
            bot: TradingBot instance
        """
        self.bot = bot
        self.start_time = datetime.now()
        logger.info("Performance monitor initialized")
    
    def generate_report(self):
        """Generate comprehensive performance report"""
        try:
            print("\n" + "="*78)
            print("📊 PERFORMANCE REPORT")
            print("="*78)
            print(f"Report Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Session Duration: {self._get_session_duration()}")
            print()
            
            # Portfolio metrics
            self._print_portfolio_metrics()
            
            # Trading metrics
            self._print_trading_metrics()
            
            # Position details
            self._print_position_details()
            
            # Trade history summary
            self._print_trade_history()
            
            print("="*78 + "\n")
            
        except Exception as e:
            logger.error(f"Report generation error: {e}")
            print(f"❌ Failed to generate report: {e}")
    
    def _get_session_duration(self) -> str:
        """Get session duration as string"""
        duration = datetime.now() - self.start_time
        hours = int(duration.total_seconds() // 3600)
        minutes = int((duration.total_seconds() % 3600) // 60)
        return f"{hours}h {minutes}m"
    
    def _print_portfolio_metrics(self):
        """Print portfolio performance metrics"""
        try:
            portfolio_value = self.bot.calculate_portfolio_value()
            total_pnl = portfolio_value - self.bot.starting_capital
            total_pnl_pct = (total_pnl / self.bot.starting_capital) * 100
            
            print("💼 PORTFOLIO METRICS")
            print("-" * 78)
            print(f"Starting Capital:    ${self.bot.starting_capital:,.2f}")
            print(f"Current Value:       ${portfolio_value:,.2f}")
            print(f"Available Capital:   ${self.bot.available_capital:,.2f}")
            print(f"Total P&L:           ${total_pnl:+,.2f} ({total_pnl_pct:+.2f}%)")
            
            # Daily P&L if available
            if hasattr(self.bot, 'daily_pnl'):
                print(f"Today's P&L:         ${self.bot.daily_pnl:+,.2f}")
            
            print()
        except Exception as e:
            logger.error(f"Portfolio metrics error: {e}")
    
    def _print_trading_metrics(self):
        """Print trading performance metrics"""
        try:
            print("📈 TRADING METRICS")
            print("-" * 78)
            print(f"Total Trades:        {self.bot.total_trades}")
            print(f"Open Positions:      {len(self.bot.positions)}/{self.bot.config.MAX_OPEN_POSITIONS}")
            
            if self.bot.total_trades > 0:
                win_rate = (self.bot.winning_trades / self.bot.total_trades) * 100
                print(f"Winning Trades:      {self.bot.winning_trades}")
                print(f"Losing Trades:       {self.bot.losing_trades}")
                print(f"Win Rate:            {win_rate:.1f}%")
                
                # Average trade metrics
                if hasattr(self.bot, 'trade_history') and self.bot.trade_history:
                    avg_win = self._calculate_avg_win()
                    avg_loss = self._calculate_avg_loss()
                    
                    if avg_win > 0:
                        print(f"Average Win:         +{avg_win:.2f}%")
                    if avg_loss < 0:
                        print(f"Average Loss:        {avg_loss:.2f}%")
                    
                    if avg_win > 0 and avg_loss < 0:
                        profit_factor = abs(avg_win * self.bot.winning_trades) / abs(avg_loss * self.bot.losing_trades)
                        print(f"Profit Factor:       {profit_factor:.2f}")
            else:
                print(f"Winning Trades:      0")
                print(f"Losing Trades:       0")
                print(f"Win Rate:            N/A")
            
            # Fees and costs
            if hasattr(self.bot, 'total_fees_paid'):
                print(f"Total Fees Paid:     ${self.bot.total_fees_paid:.2f}")
            
            if hasattr(self.bot, 'total_tax_paid'):
                print(f"Total Tax Paid:      ${self.bot.total_tax_paid:.2f}")
            
            print()
        except Exception as e:
            logger.error(f"Trading metrics error: {e}")
    
    def _print_position_details(self):
        """Print current open positions"""
        try:
            if not self.bot.positions:
                print("📍 OPEN POSITIONS: None")
                print()
                return
            
            print(f"📍 OPEN POSITIONS ({len(self.bot.positions)})")
            print("-" * 78)
            
            for symbol, pos in self.bot.positions.items():
                current_price = self.bot.get_current_price_safe(symbol)
                
                if current_price:
                    pnl = current_price - pos['entry_price']
                    pnl_pct = (pnl / pos['entry_price']) * 100
                    pnl_usd = (pos['value'] / pos['entry_price']) * pnl
                    
                    emoji = "🟢" if pnl_pct > 0 else "🔴" if pnl_pct < 0 else "⚪"
                    
                    print(f"{emoji} {symbol}")
                    print(f"   Entry:  ${pos['entry_price']:.4f}")
                    print(f"   Current: ${current_price:.4f}")
                    print(f"   P&L:    ${pnl_usd:+.2f} ({pnl_pct:+.2f}%)")
                    print(f"   Size:   ${pos['value']:.2f}")
                    
                    if 'stop_loss' in pos:
                        print(f"   SL:     ${pos['stop_loss']:.4f}")
                    if 'take_profit' in pos:
                        print(f"   TP:     ${pos['take_profit']:.4f}")
                    
                    print()
            
        except Exception as e:
            logger.error(f"Position details error: {e}")
    
    def _print_trade_history(self):
        """Print recent trade history"""
        try:
            if not hasattr(self.bot, 'trade_history') or not self.bot.trade_history:
                print("📜 TRADE HISTORY: No trades yet")
                print()
                return
            
            print(f"📜 RECENT TRADES (Last 10)")
            print("-" * 78)
            
            # Get last 10 trades
            recent_trades = self.bot.trade_history[-10:]
            
            for trade in recent_trades:
                pnl_pct = trade.get('pnl_pct', 0)
                emoji = "✅" if pnl_pct > 0 else "❌"
                
                print(f"{emoji} {trade['symbol']} | "
                      f"Entry: ${trade['entry_price']:.4f} → "
                      f"Exit: ${trade['exit_price']:.4f} | "
                      f"P&L: {pnl_pct:+.2f}%")
            
            print()
            
        except Exception as e:
            logger.error(f"Trade history error: {e}")
    
    def _calculate_avg_win(self) -> float:
        """Calculate average winning trade percentage"""
        try:
            if not self.bot.trade_history:
                return 0.0
            
            wins = [t['pnl_pct'] for t in self.bot.trade_history if t.get('pnl_pct', 0) > 0]
            return sum(wins) / len(wins) if wins else 0.0
        except:
            return 0.0
    
    def _calculate_avg_loss(self) -> float:
        """Calculate average losing trade percentage"""
        try:
            if not self.bot.trade_history:
                return 0.0
            
            losses = [t['pnl_pct'] for t in self.bot.trade_history if t.get('pnl_pct', 0) < 0]
            return sum(losses) / len(losses) if losses else 0.0
        except:
            return 0.0
    
    def get_stats(self) -> Dict:
        """Get performance statistics as dictionary"""
        try:
            portfolio_value = self.bot.calculate_portfolio_value()
            total_pnl = portfolio_value - self.bot.starting_capital
            total_pnl_pct = (total_pnl / self.bot.starting_capital) * 100
            
            win_rate = 0.0
            if self.bot.total_trades > 0:
                win_rate = (self.bot.winning_trades / self.bot.total_trades) * 100
            
            return {
                'portfolio_value': portfolio_value,
                'total_pnl': total_pnl,
                'total_pnl_pct': total_pnl_pct,
                'total_trades': self.bot.total_trades,
                'win_rate': win_rate,
                'open_positions': len(self.bot.positions),
                'session_duration': self._get_session_duration()
            }
        except Exception as e:
            logger.error(f"Stats calculation error: {e}")
            return {}
