# close_positions.py - Save this and run: python close_positions.py
from core.bot import TradingBot
from config import Config

bot = TradingBot(Config())

print("Closing all positions...")
for symbol in list(bot.positions.keys()):
    price = bot.get_current_price_safe(symbol)
    if price:
        bot._execute_sell(symbol, price)
        print(f"✅ Closed {symbol} at ${price}")

print(f"\n💰 Final P&L: ${bot.total_profit:.2f}")
