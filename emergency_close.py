"""
Emergency Position Closer - Run this NOW!
"""

import sys
import os

# Add project path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config
from core.bot import TradingBot

def main():
    print("="*70)
    print("🚨 EMERGENCY POSITION CLOSER")
    print("="*70)
    
    try:
        # Initialize bot
        print("\n⏳ Loading bot...")
        config = Config()
        bot = TradingBot(config)
        
        # Check if positions exist
        if not bot.positions:
            print("\n✅ No positions open - nothing to close")
            return
        
        print(f"\n⚠️  Found {len(bot.positions)} open positions:")
        for symbol, pos in bot.positions.items():
            entry = pos.get('entry_price', 0)
            print(f"  - {symbol} (Entry: ${entry:.8f if entry < 0.01 else entry:.2f})")
        
        # Get confirmation
        print("\n⚠️  WARNING: This will close ALL positions at market price!")
        response = input("⚠️  Type 'YES' to confirm: ")
        
        if response != 'YES':
            print("\n❌ Cancelled - no positions closed")
            return
        
        # Close all positions
        print("\n🚨 Closing positions...")
        closed_count = 0
        total_pnl = 0
        
        for symbol in list(bot.positions.keys()):
            try:
                # Get current price
                price = bot.get_current_price_safe(symbol)
                if not price or price <= 0:
                    print(f"  ⚠️  {symbol}: Can't get price - skipping")
                    continue
                
                # Get position info
                position = bot.positions[symbol]
                entry_price = position['entry_price']
                size = position['position_size']
                pnl = (price - entry_price) / entry_price * size
                total_pnl += pnl
                
                # Display
                price_display = f"${price:.8f}" if price < 0.01 else f"${price:.2f}"
                print(f"  🚨 {symbol}: Closing @ {price_display} | P&L: ${pnl:+.2f}")
                
                # Execute sell
                bot.execute_sell(symbol, price, reason="EMERGENCY MANUAL CLOSE")
                closed_count += 1
                
            except Exception as e:
                print(f"  ❌ {symbol}: Error - {e}")
                continue
        
        # Summary
        print(f"\n{'='*70}")
        print(f"✅ EMERGENCY CLOSE COMPLETE")
        print(f"   Positions closed: {closed_count}")
        print(f"   Total P&L: ${total_pnl:+,.2f}")
        print(f"   Positions remaining: {len(bot.positions)}")
        print(f"{'='*70}")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
