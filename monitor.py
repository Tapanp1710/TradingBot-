"""
Real-time Performance Monitoring v3.0 - PRODUCTION OPTIMIZED
- Comprehensive metrics, ML tracking, error handling
"""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
from datetime import datetime
import os
import logging

logger = logging.getLogger('TradingBot')


class PerformanceMonitor:
    """Production-grade performance monitoring and reporting"""
    
    def __init__(self, bot):
        self.bot = bot
        os.makedirs('logs', exist_ok=True)
        logger.info("📊 Performance Monitor initialized")
    
    def generate_report(self):
        """Generate comprehensive performance report"""
        
        if not self.bot.trade_history:
            print("\n⚠️  No trades yet - Report unavailable")
            return
        
        try:
            df = pd.DataFrame(self.bot.trade_history)
            
            # Validate required columns
            required = ['net_profit', 'profit_pct', 'entry_time', 'exit_time']
            missing = [col for col in required if col not in df.columns]
            if missing:
                logger.error(f"Missing columns: {missing}")
                return
            
            # Generate metrics
            metrics = self._calculate_metrics(df)
            
            # Display report
            self._display_report(metrics, df)
            
            # Generate plots
            self._generate_plots(df)
            
            # Save detailed report
            self._save_report(metrics, df)
            
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            print(f"⚠️  Report generation failed: {e}")
    
    def _calculate_metrics(self, df: pd.DataFrame) -> dict:
        """Calculate all performance metrics"""
        
        metrics = {}
        
        # Basic stats
        metrics['total_trades'] = len(df)
        metrics['wins'] = len(df[df['net_profit'] > 0])
        metrics['losses'] = len(df[df['net_profit'] < 0])
        metrics['breakeven'] = len(df[df['net_profit'] == 0])
        
        # Win rate
        metrics['win_rate'] = (metrics['wins'] / metrics['total_trades'] * 100) if metrics['total_trades'] > 0 else 0
        
        # P&L stats
        metrics['total_pnl'] = df['net_profit'].sum()
        metrics['avg_win'] = df[df['net_profit'] > 0]['net_profit'].mean() if metrics['wins'] > 0 else 0
        metrics['avg_loss'] = df[df['net_profit'] < 0]['net_profit'].mean() if metrics['losses'] > 0 else 0
        metrics['largest_win'] = df['net_profit'].max() if len(df) > 0 else 0
        metrics['largest_loss'] = df['net_profit'].min() if len(df) > 0 else 0
        
        # Profit factor
        gross_profit = df[df['net_profit'] > 0]['net_profit'].sum()
        gross_loss = abs(df[df['net_profit'] < 0]['net_profit'].sum())
        metrics['profit_factor'] = gross_profit / gross_loss if gross_loss > 0 else np.inf
        
        # Expectancy
        metrics['expectancy'] = (metrics['win_rate']/100 * metrics['avg_win']) + \
                               ((1 - metrics['win_rate']/100) * metrics['avg_loss'])
        
        # Risk-reward ratio
        metrics['avg_rr_ratio'] = abs(metrics['avg_win'] / metrics['avg_loss']) if metrics['avg_loss'] < 0 else 0
        
        # Sharpe ratio (crypto uses 365 days)
        returns = df['profit_pct'] / 100
        metrics['sharpe_ratio'] = (returns.mean() / returns.std()) * (365 ** 0.5) if len(returns) > 1 and returns.std() > 0 else 0
        
        # Max drawdown
        metrics['max_drawdown'] = self._calculate_max_drawdown(df)
        
        # Consecutive stats
        metrics['max_consecutive_wins'] = self._max_consecutive(df, 'net_profit', lambda x: x > 0)
        metrics['max_consecutive_losses'] = self._max_consecutive(df, 'net_profit', lambda x: x < 0)
        
        # Timing stats
        df['hold_duration_hours'] = (pd.to_datetime(df['exit_time']) - pd.to_datetime(df['entry_time'])).dt.total_seconds() / 3600
        metrics['avg_hold_time'] = df['hold_duration_hours'].mean()
        
        # Fees and taxes
        metrics['total_fees'] = df['total_fees'].sum() if 'total_fees' in df.columns else 0
        metrics['total_tax'] = (df['tax'].sum() + df['tds'].sum()) if 'tax' in df.columns else 0
        
        # ML metrics (if available)
        if 'ml_used' in df.columns and 'ml_confidence' in df.columns:
            ml_trades = df[df['ml_used'] == True]
            if len(ml_trades) > 0:
                ml_wins = len(ml_trades[ml_trades['net_profit'] > 0])
                metrics['ml_win_rate'] = (ml_wins / len(ml_trades) * 100)
                metrics['ml_accuracy'] = self._calculate_ml_accuracy(ml_trades)
                metrics['ml_trades'] = len(ml_trades)
            else:
                metrics['ml_win_rate'] = 0
                metrics['ml_accuracy'] = 0
                metrics['ml_trades'] = 0
        
        return metrics
    
    def _calculate_max_drawdown(self, df: pd.DataFrame) -> float:
        """Calculate maximum drawdown with safety"""
        try:
            if len(df) == 0:
                return 0
            
            cumulative = (1 + df['profit_pct']/100).cumprod()
            running_max = cumulative.expanding().max()
            drawdown = (cumulative - running_max) / running_max
            return float(drawdown.min()) if not drawdown.empty else 0
        except Exception as e:
            logger.error(f"Drawdown calculation error: {e}")
            return 0
    
    def _max_consecutive(self, df: pd.DataFrame, column: str, condition) -> int:
        """Calculate max consecutive occurrences"""
        try:
            mask = df[column].apply(condition)
            groups = (mask != mask.shift()).cumsum()
            consecutive = mask.groupby(groups).sum()
            return int(consecutive.max()) if len(consecutive) > 0 else 0
        except:
            return 0
    
    def _calculate_ml_accuracy(self, ml_df: pd.DataFrame) -> float:
        """Calculate ML prediction accuracy"""
        try:
            correct = 0
            for _, trade in ml_df.iterrows():
                predicted_win = trade['ml_confidence'] > 0.5
                actual_win = trade['net_profit'] > 0
                if predicted_win == actual_win:
                    correct += 1
            return (correct / len(ml_df) * 100) if len(ml_df) > 0 else 0
        except:
            return 0
    
    def _display_report(self, metrics: dict, df: pd.DataFrame):
        """Display formatted report"""
        
        print("\n" + "="*78)
        print("📊 COMPREHENSIVE PERFORMANCE REPORT")
        print("="*78)
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Trading Stats
        print("📈 TRADING STATISTICS")
        print("-" * 78)
        print(f"Total Trades:        {metrics['total_trades']}")
        print(f"Wins:                {metrics['wins']} ({metrics['win_rate']:.2f}%)")
        print(f"Losses:              {metrics['losses']}")
        print(f"Breakeven:           {metrics['breakeven']}")
        print()
        
        # P&L Stats
        print("💰 PROFIT & LOSS")
        print("-" * 78)
        print(f"Total P&L:           ${metrics['total_pnl']:+,.2f}")
        print(f"Average Win:         ${metrics['avg_win']:,.2f}")
        print(f"Average Loss:        ${metrics['avg_loss']:,.2f}")
        print(f"Largest Win:         ${metrics['largest_win']:,.2f}")
        print(f"Largest Loss:        ${metrics['largest_loss']:,.2f}")
        print(f"Expectancy:          ${metrics['expectancy']:+,.2f} per trade")
        print()
        
        # Performance Metrics
        print("📊 PERFORMANCE METRICS")
        print("-" * 78)
        print(f"Profit Factor:       {metrics['profit_factor']:.2f}")
        print(f"Risk-Reward Ratio:   {metrics['avg_rr_ratio']:.2f}")
        print(f"Sharpe Ratio:        {metrics['sharpe_ratio']:.2f}")
        print(f"Max Drawdown:        {metrics['max_drawdown']:.2%}")
        print()
        
        # Streaks
        print("🔥 STREAKS")
        print("-" * 78)
        print(f"Max Consecutive Wins:   {metrics['max_consecutive_wins']}")
        print(f"Max Consecutive Losses: {metrics['max_consecutive_losses']}")
        print(f"Average Hold Time:      {metrics['avg_hold_time']:.1f} hours")
        print()
        
        # Costs
        print("💸 COSTS")
        print("-" * 78)
        print(f"Total Fees Paid:     ${metrics['total_fees']:,.2f}")
        print(f"Total Tax Paid:      ${metrics['total_tax']:,.2f}")
        print()
        
        # ML Stats
        if metrics.get('ml_trades', 0) > 0:
            print("🤖 MACHINE LEARNING")
            print("-" * 78)
            print(f"ML Trades:           {metrics['ml_trades']}")
            print(f"ML Win Rate:         {metrics['ml_win_rate']:.2f}%")
            print(f"ML Accuracy:         {metrics['ml_accuracy']:.2f}%")
            print()
        
        # Current Status
        print("📍 CURRENT STATUS")
        print("-" * 78)
        current_value = self.bot.calculate_portfolio_value()
        print(f"Starting Capital:    ${self.bot.capital:,.2f}")
        print(f"Current Value:       ${current_value:,.2f}")
        print(f"Total Return:        ${current_value - self.bot.capital:+,.2f} "
              f"({(current_value / self.bot.capital - 1) * 100:+.2f}%)")
        print(f"Open Positions:      {len(self.bot.positions)}/{self.bot.config.MAX_OPEN_POSITIONS}")
        print(f"Available Capital:   ${self.bot.available_capital:,.2f}")
        
        print("="*78 + "\n")
    
    def _generate_plots(self, df: pd.DataFrame):
        """Generate performance plots"""
        
        try:
            # Create figure with subplots
            fig, axes = plt.subplots(2, 2, figsize=(15, 10))
            fig.suptitle('Trading Bot Performance Analysis', fontsize=16, fontweight='bold')
            
            # 1. Equity Curve
            df['cumulative_pnl'] = df['net_profit'].cumsum()
            axes[0, 0].plot(df.index, df['cumulative_pnl'], linewidth=2, color='blue')
            axes[0, 0].axhline(y=0, color='red', linestyle='--', alpha=0.5)
            axes[0, 0].set_title('Equity Curve')
            axes[0, 0].set_xlabel('Trade #')
            axes[0, 0].set_ylabel('Cumulative P&L ($)')
            axes[0, 0].grid(True, alpha=0.3)
            
            # 2. Profit Distribution
            axes[0, 1].hist(df['net_profit'], bins=30, color='green', alpha=0.7, edgecolor='black')
            axes[0, 1].axvline(x=0, color='red', linestyle='--', alpha=0.5)
            axes[0, 1].set_title('Profit Distribution')
            axes[0, 1].set_xlabel('Profit ($)')
            axes[0, 1].set_ylabel('Frequency')
            axes[0, 1].grid(True, alpha=0.3)
            
            # 3. Win/Loss Ratio Over Time
            df['is_win'] = df['net_profit'] > 0
            df['win_rate_rolling'] = df['is_win'].rolling(window=10, min_periods=1).mean() * 100
            axes[1, 0].plot(df.index, df['win_rate_rolling'], linewidth=2, color='orange')
            axes[1, 0].axhline(y=50, color='red', linestyle='--', alpha=0.5)
            axes[1, 0].set_title('Rolling Win Rate (10 trades)')
            axes[1, 0].set_xlabel('Trade #')
            axes[1, 0].set_ylabel('Win Rate (%)')
            axes[1, 0].grid(True, alpha=0.3)
            
            # 4. Hold Time Distribution
            if 'hold_duration_hours' in df.columns:
                axes[1, 1].hist(df['hold_duration_hours'], bins=20, color='purple', alpha=0.7, edgecolor='black')
                axes[1, 1].set_title('Hold Time Distribution')
                axes[1, 1].set_xlabel('Hours')
                axes[1, 1].set_ylabel('Frequency')
                axes[1, 1].grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            # Save plot
            plot_path = 'logs/performance_analysis.png'
            plt.savefig(plot_path, dpi=100, bbox_inches='tight')
            plt.close(fig)  # Important: Close to free memory
            
            print(f"📈 Performance charts saved to {plot_path}")
            
        except Exception as e:
            logger.error(f"Plot generation error: {e}")
            plt.close('all')  # Clean up on error
    
    def _save_report(self, metrics: dict, df: pd.DataFrame):
        """Save detailed report to file"""
        
        try:
            report_path = f"logs/report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write("="*78 + "\n")
                f.write("TRADING BOT PERFORMANCE REPORT\n")
                f.write("="*78 + "\n\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                # Write all metrics
                for key, value in metrics.items():
                    if isinstance(value, float):
                        f.write(f"{key}: {value:.4f}\n")
                    else:
                        f.write(f"{key}: {value}\n")
                
                f.write("\n" + "="*78 + "\n")
                f.write("TRADE HISTORY\n")
                f.write("="*78 + "\n\n")
                
                # Write trade summary
                f.write(df.to_string())
            
            print(f"📄 Detailed report saved to {report_path}")
            
        except Exception as e:
            logger.error(f"Report save error: {e}")
