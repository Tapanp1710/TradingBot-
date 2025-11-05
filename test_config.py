from dynamic_config import DynamicConfig

# Test initialization
config = DynamicConfig(starting_capital=1000)
config.print_summary()

# Check values
print("\n✅ VERIFICATION:")
print(f"Version: {config.CONFIG_VERSION}")
print(f"Tier: {config.CAPITAL_TIER}")
print(f"Positions: {config.MAX_OPEN_POSITIONS}")
print(f"Position %: {config.MAX_POSITION_PCT*100:.1f}%")
print(f"Allocation: {config.MAX_OPEN_POSITIONS * config.MAX_POSITION_PCT * 100:.0f}%")
