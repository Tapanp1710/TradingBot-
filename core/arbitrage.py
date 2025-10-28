"""
Triangular Arbitrage Detection v3.0 - OPTIMIZED
- Dynamic path discovery, volume validation, slippage
"""
import logging
from typing import List, Dict, Optional, Set, Tuple
from config import Config
import itertools

logger = logging.getLogger('TradingBot')


class ArbitrageScanner:
    """Production arbitrage scanner with validation"""
    
    def __init__(self, config: Config):
        self.config = config
        self.supported_pairs = set()
        self.discovered_paths = []
        self.last_discovery = 0
        
        # Trading parameters
        self.min_volume = getattr(config, 'MIN_ARBITRAGE_VOLUME', 50000)  # $50k min volume
        self.max_execution_time = 10  # seconds
        self.slippage_tolerance = 0.001  # 0.1%
        
        logger.info("🔺 Arbitrage Scanner initialized")
    
    def update_supported_pairs(self, available_pairs: Set[str]):
        """Update list of supported trading pairs"""
        self.supported_pairs = available_pairs
        logger.info(f"📊 Arbitrage scanner updated with {len(available_pairs)} pairs")
    
    def discover_paths(self, base_currencies: List[str] = None) -> List[Tuple]:
        """
        Dynamically discover triangular arbitrage paths
        
        Args:
            base_currencies: Base currencies to start from (e.g., ['USDT', 'BTC'])
        
        Returns:
            List of (pair1, pair2, pair3) tuples
        """
        
        if base_currencies is None:
            base_currencies = ['USDT', 'BTC', 'ETH', 'BNB']
        
        paths = []
        
        # Parse available pairs into a graph structure
        pairs_by_base = {}
        for pair in self.supported_pairs:
            try:
                coin, base = pair.split('/')
                if base not in pairs_by_base:
                    pairs_by_base[base] = []
                pairs_by_base[base].append((coin, pair))
            except:
                continue
        
        # Find triangular paths
        for base in base_currencies:
            if base not in pairs_by_base:
                continue
            
            # Get all coins tradeable with base
            coins_with_base = pairs_by_base[base]
            
            # Find triangular opportunities
            for i, (coin1, pair1) in enumerate(coins_with_base):
                # Find pairs where coin1 is the base
                if coin1 not in pairs_by_base:
                    continue
                
                coins_with_coin1 = pairs_by_base[coin1]
                
                for coin2, pair2 in coins_with_coin1:
                    # Find pair that completes the triangle
                    pair3 = f"{coin2}/{base}"
                    
                    if pair3 in self.supported_pairs:
                        paths.append((pair1, pair2, pair3))
        
        self.discovered_paths = paths
        logger.info(f"🔍 Discovered {len(paths)} potential arbitrage paths")
        
        return paths
    
    def find_opportunities(self, tickers: Dict) -> List[Dict]:
        """
        Find arbitrage opportunities with validation
        
        Args:
            tickers: {symbol: {bid, ask, last, volume, ...}}
        
        Returns:
            List of validated arbitrage opportunities
        """
        
        if not self.config.ENABLE_ARBITRAGE:
            return []
        
        # Discover paths if not done yet
        if not self.discovered_paths:
            self.discover_paths()
        
        opportunities = []
        
        for pair1, pair2, pair3 in self.discovered_paths:
            # Forward direction
            opp_forward = self._calculate_arbitrage_profit(
                pair1, pair2, pair3, tickers, direction='forward'
            )
            if opp_forward:
                opportunities.append(opp_forward)
            
            # Reverse direction
            opp_reverse = self._calculate_arbitrage_profit(
                pair1, pair2, pair3, tickers, direction='reverse'
            )
            if opp_reverse:
                opportunities.append(opp_reverse)
        
        # Sort by profit percentage
        opportunities.sort(key=lambda x: x['profit_pct'], reverse=True)
        
        if opportunities:
            logger.info(f"💰 Found {len(opportunities)} arbitrage opportunities")
            for opp in opportunities[:3]:  # Log top 3
                logger.info(f"   {opp['path']}: {opp['profit_pct']:.3%} profit")
        
        return opportunities
    
    def _calculate_arbitrage_profit(
        self, 
        pair1: str, 
        pair2: str, 
        pair3: str, 
        tickers: Dict,
        direction: str = 'forward'
    ) -> Optional[Dict]:
        """
        Calculate profit with volume and slippage validation
        
        Args:
            direction: 'forward' or 'reverse'
        """
        
        try:
            # Validate pairs exist in tickers
            if not all(pair in tickers for pair in [pair1, pair2, pair3]):
                return None
            
            # Get ticker data
            ticker1 = tickers[pair1]
            ticker2 = tickers[pair2]
            ticker3 = tickers[pair3]
            
            # Validate ticker structure
            required_fields = ['bid', 'ask', 'last']
            if not all(field in ticker1 and field in ticker2 and field in ticker3 
                      for field in required_fields):
                return None
            
            # Get prices
            if direction == 'forward':
                price1 = ticker1.get('ask', 0)  # Buy
                price2 = ticker2.get('ask', 0)  # Buy
                price3 = ticker3.get('bid', 0)  # Sell
            else:
                price1 = ticker1.get('bid', 0)  # Sell
                price2 = ticker2.get('bid', 0)  # Sell
                price3 = ticker3.get('ask', 0)  # Buy
            
            # Validate prices
            if not all([price1 > 0, price2 > 0, price3 > 0]):
                return None
            
            # Check volume (must have sufficient liquidity)
            volume1 = ticker1.get('quoteVolume', 0)
            volume2 = ticker2.get('quoteVolume', 0)
            volume3 = ticker3.get('quoteVolume', 0)
            
            if any(vol < self.min_volume for vol in [volume1, volume2, volume3]):
                return None
            
            # Simulate trade
            amount = 1000  # $1000 test amount
            fee = self.config.TRADING_FEE
            slippage = self.slippage_tolerance
            
            if direction == 'forward':
                # Forward: USDT → Coin1 → Coin2 → USDT
                step1 = (amount / price1) * (1 - fee) * (1 - slippage)
                step2 = (step1 * price2) * (1 - fee) * (1 - slippage)
                step3 = (step2 * price3) * (1 - fee) * (1 - slippage)
            else:
                # Reverse: USDT → Coin2 → Coin1 → USDT
                step1 = (amount / price3) * (1 - fee) * (1 - slippage)
                step2 = (step1 / price2) * (1 - fee) * (1 - slippage)
                step3 = (step2 * price1) * (1 - fee) * (1 - slippage)
            
            # Calculate profit
            profit = step3 - amount
            profit_pct = profit / amount
            
            # Check if profitable after all costs
            if profit_pct > self.config.MIN_ARBITRAGE_PROFIT:
                
                # Calculate execution risk score
                execution_time = self._estimate_execution_time()
                risk_score = self._calculate_risk_score(
                    profit_pct, 
                    min(volume1, volume2, volume3),
                    execution_time
                )
                
                # Build path description
                if direction == 'forward':
                    coin1 = pair1.split('/')[0]
                    coin2 = pair2.split('/')[0]
                    path = f"USDT → {coin1} → {coin2} → USDT"
                else:
                    coin2 = pair3.split('/')[0]
                    coin1 = pair1.split('/')[0]
                    path = f"USDT → {coin2} → {coin1} → USDT"
                
                return {
                    'type': 'triangular',
                    'direction': direction,
                    'path': path,
                    'pairs': [pair1, pair2, pair3],
                    'prices': [price1, price2, price3],
                    'volumes': [volume1, volume2, volume3],
                    'profit_pct': profit_pct,
                    'profit_amount': profit,
                    'starting_amount': amount,
                    'execution_time_est': execution_time,
                    'risk_score': risk_score,
                    'min_volume': min(volume1, volume2, volume3)
                }
            
            return None
            
        except Exception as e:
            logger.debug(f"Arbitrage calculation error: {e}")
            return None
    
    def _estimate_execution_time(self) -> float:
        """
        Estimate time to execute all 3 trades
        Returns: seconds
        """
        # Conservative estimate: 3 seconds per trade
        return 9.0
    
    def _calculate_risk_score(
        self, 
        profit_pct: float, 
        min_volume: float,
        execution_time: float
    ) -> float:
        """
        Calculate risk score (0-100, lower is better)
        
        Factors:
        - Profit margin (higher = lower risk)
        - Volume (higher = lower risk)
        - Execution time (faster = lower risk)
        """
        
        # Profit risk (lower profit = higher risk)
        profit_risk = max(0, (0.01 - profit_pct) / 0.01 * 50)
        
        # Volume risk (lower volume = higher risk)
        volume_risk = max(0, (100000 - min_volume) / 100000 * 30)
        
        # Time risk (longer execution = higher risk)
        time_risk = min(execution_time / self.max_execution_time * 20, 20)
        
        total_risk = profit_risk + volume_risk + time_risk
        
        return min(total_risk, 100)
    
    def is_opportunity_valid(self, opportunity: Dict, current_tickers: Dict) -> bool:
        """
        Validate if opportunity is still valid
        (prices may have changed since detection)
        """
        
        try:
            pairs = opportunity['pairs']
            
            # Check if all pairs still exist in tickers
            if not all(pair in current_tickers for pair in pairs):
                return False
            
            # Recalculate with current prices
            new_opp = self._calculate_arbitrage_profit(
                pairs[0], pairs[1], pairs[2],
                current_tickers,
                direction=opportunity['direction']
            )
            
            # Valid if still profitable (with some tolerance)
            if new_opp and new_opp['profit_pct'] > self.config.MIN_ARBITRAGE_PROFIT * 0.8:
                return True
            
            return False
            
        except Exception as e:
            logger.debug(f"Validation error: {e}")
            return False
    
    def get_stats(self) -> Dict:
        """Get scanner statistics"""
        return {
            'enabled': self.config.ENABLE_ARBITRAGE,
            'supported_pairs': len(self.supported_pairs),
            'discovered_paths': len(self.discovered_paths),
            'min_volume': self.min_volume,
            'min_profit': self.config.MIN_ARBITRAGE_PROFIT
        }
