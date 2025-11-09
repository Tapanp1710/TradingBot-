"""
Contrarian Signal Generator v1.0
Detects extreme market sentiment for contrarian trades
"""
from datetime import datetime
import logging

class ContrarianSignalGenerator:
    def __init__(self, config):
        self.config = config
        self.signal_history = []
        self.max_history = 20
        self.logger = logging.getLogger(__name__)
    
    def track_signals(self, scan_results):
        """Track signals from each scan"""
        self.signal_history.append({
            'timestamp': datetime.now(),
            'signals': scan_results
        })
        
        if len(self.signal_history) > self.max_history:
            self.signal_history.pop(0)
    
    def detect_extreme_bearish_sentiment(self):
        """Detect when 80%+ signals are SELL"""
        if not self.config.ENABLE_CONTRARIAN_SIGNALS:
            return None
        
        if len(self.signal_history) < 5:
            return None
        
        recent_signals = self.signal_history[-5:]
        all_signals = []
        for scan in recent_signals:
            all_signals.extend(scan['signals'])
        
        if not all_signals:
            return None
        
        sell_count = sum(1 for s in all_signals if s.get('signal') == 'SELL')
        sell_pct = sell_count / len(all_signals)
        
        if sell_pct > self.config.CONTRARIAN_SELL_THRESHOLD:
            sell_signals = [s for s in all_signals if s.get('signal') == 'SELL']
            best = max(sell_signals, key=lambda x: x.get('confidence', 0))
            
            self.logger.info(f"🔄 CONTRARIAN OPPORTUNITY DETECTED")
            self.logger.info(f"   {sell_pct*100:.0f}% of signals are SELL")
            self.logger.info(f"   Market likely oversold")
            
            return {
                'symbol': best['symbol'],
                'original_signal': 'SELL',
                'contrarian_signal': 'BUY',
                'confidence': self.config.CONTRARIAN_CONFIDENCE,
                'reason': f"Contrarian: {sell_pct*100:.0f}% SELL signals",
                'risk_level': 'HIGH',
                'position_size_mult': self.config.CONTRARIAN_POSITION_SIZE_MULT
            }
        
        return None
    
    def detect_extreme_bullish_sentiment(self):
        """Detect when 80%+ signals are BUY"""
        if not self.config.ENABLE_CONTRARIAN_SIGNALS:
            return None
        
        if len(self.signal_history) < 5:
            return None
        
        recent_signals = self.signal_history[-5:]
        all_signals = []
        for scan in recent_signals:
            all_signals.extend(scan['signals'])
        
        if not all_signals:
            return None
        
        buy_count = sum(1 for s in all_signals if s.get('signal') == 'BUY')
        buy_pct = buy_count / len(all_signals)
        
        if buy_pct > self.config.CONTRARIAN_BUY_THRESHOLD:
            buy_signals = [s for s in all_signals if s.get('signal') == 'BUY']
            best = max(buy_signals, key=lambda x: x.get('confidence', 0))
            
            self.logger.info(f"🔄 CONTRARIAN SHORT OPPORTUNITY")
            self.logger.info(f"   {buy_pct*100:.0f}% of signals are BUY")
            self.logger.info(f"   Market likely overbought")
            
            return {
                'symbol': best['symbol'],
                'original_signal': 'BUY',
                'contrarian_signal': 'SELL',
                'confidence': self.config.CONTRARIAN_CONFIDENCE,
                'reason': f"Contrarian: {buy_pct*100:.0f}% BUY signals (overbought)",
                'risk_level': 'HIGH',
                'position_size_mult': self.config.CONTRARIAN_POSITION_SIZE_MULT
            }
        
        return None
