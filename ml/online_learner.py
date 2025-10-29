"""
Online Learning System v5.0 - ENHANCED
- Continuous ML Model Updates
- Adaptive learning rates
- Feature importance tracking
- Performance-based model selection
- Advanced validation metrics
"""
import numpy as np
import joblib
import logging
from datetime import datetime
from sklearn.linear_model import SGDClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from collections import deque
from typing import Dict, Optional, List
import os

logger = logging.getLogger('TradingBot')


class OnlineLearner:
    """
    Enhanced online/incremental learning for trading models
    Updates model weights after each trade with advanced tracking
    """
    
    def __init__(self, config, base_model=None):
        self.config = config
        self.base_model = base_model  # Original trained model (fallback)
        
        # Initialize online model
        self.online_model = self._initialize_online_model()
        
        # Trade buffer for batch updates
        self.trade_buffer = deque(maxlen=config.BATCH_UPDATE_SIZE)
        
        # Performance tracking
        self.update_count = 0
        self.validation_history = deque(maxlen=config.VALIDATION_WINDOW)
        
        # NEW: Detailed metrics tracking
        self.metrics_history = {
            'accuracy': deque(maxlen=50),
            'precision': deque(maxlen=50),
            'recall': deque(maxlen=50),
            'f1': deque(maxlen=50)
        }
        
        # NEW: Feature importance tracking
        self.feature_importance = None
        self.feature_update_count = {}
        
        # Model checkpoints
        self.best_model = None
        self.best_accuracy = 0.0
        self.best_f1_score = 0.0
        
        # NEW: Adaptive learning rate
        self.current_learning_rate = config.ONLINE_LEARNING_RATE
        self.learning_rate_decay = getattr(config, 'DECAY_RATE', 0.95)
        
        # NEW: Trade outcome tracking
        self.recent_predictions = deque(maxlen=100)
        
        logger.info("✅ Online Learning System v5.0 initialized")
        logger.info(f"   Update method: {config.ONLINE_LEARNING_METHOD}")
        logger.info(f"   Learning rate: {config.ONLINE_LEARNING_RATE}")
        logger.info(f"   Batch size: {config.BATCH_UPDATE_SIZE}")
    
    def _initialize_online_model(self):
        """Initialize online learning model with SGD"""
        if self.config.ONLINE_LEARNING_METHOD == 'sgd':
            model = SGDClassifier(
                loss='log_loss',
                learning_rate='constant',
                eta0=self.config.ONLINE_LEARNING_RATE,
                random_state=42,
                warm_start=True,
                # NEW: Enhanced parameters
                penalty='l2',
                alpha=0.0001,
                max_iter=1000,
                tol=1e-3
            )
            logger.info("Using enhanced SGD for online learning")
        else:
            model = self.base_model
            logger.info("Using incremental updates on base model")
        
        return model
    
    def record_trade(self, symbol: str, features: List[float], signal: str, entry_price: float):
        """
        NEW: Record trade entry for later outcome tracking
        """
        self.recent_predictions.append({
            'symbol': symbol,
            'features': features,
            'signal': signal,
            'entry_price': entry_price,
            'entry_time': datetime.now(),
            'prediction': None  # Will be filled when trade closes
        })
    
    def update_model(self, features: List[float], outcome: int):
        """
        NEW: Simplified method - called when trade closes
        
        Args:
            features: Feature vector used for prediction
            outcome: 1 if profitable, 0 if loss
        """
        trade_data = {
            'features': features,
            'actual': outcome,
            'prediction': None  # Not needed for update
        }
        
        self.update_from_trade(trade_data)
    
    def update_from_trade(self, trade_data: dict):
        """
        Update model from completed trade
        
        Args:
            trade_data: {
                'features': [feature values],
                'prediction': model prediction (optional),
                'actual': 1=profit, 0=loss,
                'profit': amount (optional),
                'symbol': symbol name (optional)
            }
        """
        if not self.config.ENABLE_ONLINE_LEARNING:
            return
        
        # Add to buffer
        self.trade_buffer.append(trade_data)
        
        # Update based on method
        if self.config.UPDATE_MODEL_PER_TRADE:
            self._immediate_update(trade_data)
        elif len(self.trade_buffer) >= self.config.BATCH_UPDATE_SIZE:
            self._batch_update()
    
    def _immediate_update(self, trade_data: dict):
        """Update model immediately after single trade"""
        
        # Wait for minimum trades
        if self.update_count < self.config.MIN_TRADES_BEFORE_UPDATE:
            self.update_count += 1
            logger.info(f"📚 Collecting data... ({self.update_count}/{self.config.MIN_TRADES_BEFORE_UPDATE})")
            return
        
        X = np.array([trade_data['features']])
        y = np.array([trade_data['actual']])
        
        try:
            # Partial fit (incremental update)
            if hasattr(self.online_model, 'partial_fit'):
                self.online_model.partial_fit(X, y, classes=[0, 1])
            else:
                self.online_model.fit(X, y)
            
            self.update_count += 1
            
            # Track validation
            prediction = trade_data.get('prediction', None)
            if prediction is not None:
                self.validation_history.append({
                    'prediction': prediction,
                    'actual': trade_data['actual'],
                    'correct': int(round(prediction) == trade_data['actual'])
                })
            
            # NEW: Calculate metrics
            metrics = self._calculate_metrics()
            
            # Log update
            symbol = trade_data.get('symbol', 'Unknown')
            logger.info(f"📚 Model updated from {symbol} trade")
            if prediction is not None:
                logger.info(f"   Prediction: {prediction:.2f} | Actual: {trade_data['actual']}")
            logger.info(f"   Accuracy: {metrics['accuracy']:.1%} | F1: {metrics['f1']:.2f}")
            
            # NEW: Adaptive learning rate decay
            if self.update_count % 50 == 0:
                self._adjust_learning_rate()
            
            # Save checkpoint periodically
            if self.update_count % self.config.SAVE_MODEL_AFTER_UPDATES == 0:
                self._save_checkpoint(metrics['accuracy'])
            
            # Rollback if performance drops
            if self.config.ENABLE_MODEL_ROLLBACK:
                if metrics['accuracy'] < self.best_accuracy - self.config.MAX_PERFORMANCE_DROP:
                    self._rollback_model()
        
        except Exception as e:
            logger.error(f"❌ Online learning update failed: {e}")
    
    def _batch_update(self):
        """Update model on batch of trades"""
        
        if len(self.trade_buffer) < self.config.BATCH_UPDATE_SIZE:
            return
        
        X = np.array([t['features'] for t in self.trade_buffer])
        y = np.array([t['actual'] for t in self.trade_buffer])
        
        try:
            # Batch partial fit
            if hasattr(self.online_model, 'partial_fit'):
                self.online_model.partial_fit(X, y, classes=[0, 1])
            else:
                self.online_model.fit(X, y)
            
            self.update_count += len(self.trade_buffer)
            
            # Calculate batch metrics
            predictions = self.online_model.predict(X)
            accuracy = accuracy_score(y, predictions)
            
            try:
                precision = precision_score(y, predictions, zero_division=0)
                recall = recall_score(y, predictions, zero_division=0)
                f1 = f1_score(y, predictions, zero_division=0)
            except:
                precision = recall = f1 = 0.0
            
            logger.info(f"📚 Batch update: {len(self.trade_buffer)} trades")
            logger.info(f"   Accuracy: {accuracy:.1%} | Precision: {precision:.2f} | Recall: {recall:.2f}")
            
            # Store metrics
            self.metrics_history['accuracy'].append(accuracy)
            self.metrics_history['precision'].append(precision)
            self.metrics_history['recall'].append(recall)
            self.metrics_history['f1'].append(f1)
            
            # Clear buffer
            self.trade_buffer.clear()
        
        except Exception as e:
            logger.error(f"❌ Batch update failed: {e}")
    
    def _calculate_metrics(self) -> Dict[str, float]:
        """NEW: Calculate comprehensive performance metrics"""
        
        if len(self.validation_history) == 0:
            return {
                'accuracy': 0.0,
                'precision': 0.0,
                'recall': 0.0,
                'f1': 0.0
            }
        
        # Extract predictions and actuals
        predictions = [t['prediction'] for t in self.validation_history if t.get('prediction') is not None]
        actuals = [t['actual'] for t in self.validation_history if t.get('prediction') is not None]
        
        if not predictions:
            return {
                'accuracy': 0.0,
                'precision': 0.0,
                'recall': 0.0,
                'f1': 0.0
            }
        
        # Convert to binary
        pred_binary = [1 if p >= 0.5 else 0 for p in predictions]
        
        accuracy = accuracy_score(actuals, pred_binary)
        
        try:
            precision = precision_score(actuals, pred_binary, zero_division=0)
            recall = recall_score(actuals, pred_binary, zero_division=0)
            f1 = f1_score(actuals, pred_binary, zero_division=0)
        except:
            precision = recall = f1 = 0.0
        
        return {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1': f1
        }
    
    def _calculate_recent_accuracy(self) -> float:
        """Calculate accuracy on recent trades"""
        if len(self.validation_history) == 0:
            return 0.0
        
        correct = sum(t['correct'] for t in self.validation_history if 'correct' in t)
        return correct / len(self.validation_history)
    
    def _adjust_learning_rate(self):
        """NEW: Adaptive learning rate adjustment"""
        
        # Decay learning rate
        self.current_learning_rate *= self.learning_rate_decay
        
        # Update model if it supports it
        if hasattr(self.online_model, 'eta0'):
            self.online_model.eta0 = self.current_learning_rate
            logger.info(f"📉 Learning rate adjusted: {self.current_learning_rate:.5f}")
    
    def _save_checkpoint(self, accuracy: float):
        """Save model checkpoint"""
        
        try:
            # Create directory if needed
            os.makedirs(os.path.dirname(self.config.ONLINE_MODEL_PATH), exist_ok=True)
            
            # Save current model
            joblib.dump(self.online_model, self.config.ONLINE_MODEL_PATH)
            
            # Update best model if improved
            if accuracy > self.best_accuracy:
                self.best_accuracy = accuracy
                self.best_model = joblib.loads(joblib.dumps(self.online_model))
                
                # Save best model separately
                best_path = self.config.ONLINE_MODEL_PATH.replace('.pkl', '_best.pkl')
                joblib.dump(self.best_model, best_path)
                
                logger.info(f"✅ New best model saved! Accuracy: {accuracy:.1%}")
            else:
                logger.info(f"📊 Checkpoint saved (Accuracy: {accuracy:.1%})")
        
        except Exception as e:
            logger.error(f"❌ Failed to save checkpoint: {e}")
    
    def _rollback_model(self):
        """Rollback to best previous model"""
        
        if self.best_model is None:
            logger.warning("⚠️ No previous model to rollback to")
            return
        
        self.online_model = joblib.loads(joblib.dumps(self.best_model))
        logger.warning("⚠️ Model performance dropped - ROLLED BACK to best checkpoint")
    
    def predict(self, features: np.ndarray):
        """Make prediction with online-updated model"""
        return self.online_model.predict_proba(features)
    
    def get_stats(self) -> Dict:
        """Get comprehensive online learning statistics"""
        
        metrics = self._calculate_metrics()
        
        stats = {
            'total_updates': self.update_count,
            'recent_accuracy': self._calculate_recent_accuracy(),
            'best_accuracy': self.best_accuracy,
            'buffer_size': len(self.trade_buffer),
            'learning_rate': self.current_learning_rate,
            # NEW: Additional metrics
            'precision': metrics['precision'],
            'recall': metrics['recall'],
            'f1_score': metrics['f1']
        }
        
        return stats
    
    def get_performance_summary(self) -> str:
        """NEW: Get human-readable performance summary"""
        
        stats = self.get_stats()
        
        summary = f"""
📊 Online Learning Performance:
   Updates: {stats['total_updates']}
   Recent Accuracy: {stats['recent_accuracy']:.1%}
   Best Accuracy: {stats['best_accuracy']:.1%}
   Precision: {stats['precision']:.2f}
   Recall: {stats['recall']:.2f}
   F1 Score: {stats['f1_score']:.2f}
   Learning Rate: {stats['learning_rate']:.5f}
"""
        return summary
