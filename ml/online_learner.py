"""
Online Learning System - Continuous ML Model Updates
Updates model after every trade for real-time adaptation
"""
import numpy as np
import joblib
import logging
from datetime import datetime
from sklearn.linear_model import SGDClassifier
from collections import deque

logger = logging.getLogger('TradingBot')


class OnlineLearner:
    """
    Manages online/incremental learning for trading models
    Updates model weights after each trade
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
        self.feature_importance = None
        
        # Model checkpoints
        self.best_model = None
        self.best_accuracy = 0.0
        
        logger.info("✅ Online Learning System initialized")
        logger.info(f"   Update method: {config.ONLINE_LEARNING_METHOD}")
        logger.info(f"   Learning rate: {config.ONLINE_LEARNING_RATE}")
    
    def _initialize_online_model(self):
        """
        Initialize online learning model
        Uses SGDClassifier for true incremental learning
        """
        if self.config.ONLINE_LEARNING_METHOD == 'sgd':
            # Stochastic Gradient Descent - true online learning
            model = SGDClassifier(
                loss='log_loss',           # For probability predictions
                learning_rate='constant',
                eta0=self.config.ONLINE_LEARNING_RATE,
                random_state=42,
                warm_start=True           # Allow partial_fit
            )
            logger.info("Using SGD for online learning")
        else:
            # Use existing model with incremental updates
            model = self.base_model
            logger.info("Using incremental updates on base model")
        
        return model
    
    def update_from_trade(self, trade_data: dict):
        """
        Update model from completed trade
        
        Args:
            trade_data: {
                'features': [67 feature values],
                'prediction': 0.75,  # Model predicted 75% profit chance
                'actual': 1.0,       # Actual outcome: 1=profit, 0=loss
                'profit': 20.15,
                'symbol': 'SOL/USDT'
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
        
        # Wait for minimum trades before starting
        if self.update_count < self.config.MIN_TRADES_BEFORE_UPDATE:
            self.update_count += 1
            logger.info(f"Collecting data... ({self.update_count}/{self.config.MIN_TRADES_BEFORE_UPDATE})")
            return
        
        X = np.array([trade_data['features']])
        y = np.array([trade_data['actual']])
        
        try:
            # Partial fit (incremental update)
            if hasattr(self.online_model, 'partial_fit'):
                self.online_model.partial_fit(X, y, classes=[0, 1])
            else:
                # For models without partial_fit, do mini-batch
                self.online_model.fit(X, y)
            
            self.update_count += 1
            
            # Track validation
            self.validation_history.append({
                'prediction': trade_data['prediction'],
                'actual': trade_data['actual'],
                'correct': int(round(trade_data['prediction']) == trade_data['actual'])
            })
            
            # Log update
            accuracy = self._calculate_recent_accuracy()
            logger.info(f"📚 Model updated from {trade_data['symbol']} trade")
            logger.info(f"   Prediction: {trade_data['prediction']:.2f} | Actual: {trade_data['actual']}")
            logger.info(f"   Recent accuracy: {accuracy:.1%} ({len(self.validation_history)} trades)")
            
            # Save checkpoint periodically
            if self.update_count % self.config.SAVE_MODEL_AFTER_UPDATES == 0:
                self._save_checkpoint(accuracy)
            
            # Rollback if performance drops
            if self.config.ENABLE_MODEL_ROLLBACK and accuracy < self.best_accuracy - self.config.MAX_PERFORMANCE_DROP:
                self._rollback_model()
        
        except Exception as e:
            logger.error(f"❌ Online learning update failed: {e}")
    
    def _batch_update(self):
        """Update model on batch of trades"""
        
        if len(self.trade_buffer) < self.config.BATCH_UPDATE_SIZE:
            return
        
        # Extract features and labels
        X = np.array([t['features'] for t in self.trade_buffer])
        y = np.array([t['actual'] for t in self.trade_buffer])
        
        try:
            # Batch partial fit
            if hasattr(self.online_model, 'partial_fit'):
                self.online_model.partial_fit(X, y, classes=[0, 1])
            else:
                self.online_model.fit(X, y)
            
            self.update_count += len(self.trade_buffer)
            
            # Calculate batch accuracy
            predictions = self.online_model.predict(X)
            batch_accuracy = np.mean(predictions == y)
            
            logger.info(f"📚 Batch update: {len(self.trade_buffer)} trades")
            logger.info(f"   Batch accuracy: {batch_accuracy:.1%}")
            
            # Clear buffer
            self.trade_buffer.clear()
        
        except Exception as e:
            logger.error(f"❌ Batch update failed: {e}")
    
    def _calculate_recent_accuracy(self):
        """Calculate accuracy on recent trades"""
        if len(self.validation_history) == 0:
            return 0.0
        
        correct = sum(t['correct'] for t in self.validation_history)
        return correct / len(self.validation_history)
    
    def _save_checkpoint(self, accuracy: float):
        """Save model checkpoint"""
        
        try:
            # Save current model
            joblib.dump(self.online_model, self.config.ONLINE_MODEL_PATH)
            
            # Update best model if improved
            if accuracy > self.best_accuracy:
                self.best_accuracy = accuracy
                self.best_model = joblib.loads(joblib.dumps(self.online_model))  # Deep copy
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
        
        self.online_model = joblib.loads(joblib.dumps(self.best_model))  # Deep copy
        logger.warning("⚠️ Model performance dropped - ROLLED BACK to best checkpoint")
    
    def predict(self, features: np.ndarray):
        """Make prediction with online-updated model"""
        return self.online_model.predict_proba(features)
    
    def get_stats(self):
        """Get online learning statistics"""
        return {
            'total_updates': self.update_count,
            'recent_accuracy': self._calculate_recent_accuracy(),
            'best_accuracy': self.best_accuracy,
            'buffer_size': len(self.trade_buffer)
        }
