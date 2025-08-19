import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import tensorflow as tf
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error
import asyncio
from typing import Dict, List, Tuple, Optional
import logging
import os
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StockPricePredictor:
    """
    AI-powered stock price prediction using simplified LSTM neural networks
    """
    
    def __init__(self):
        self.prediction_history = {}  # Store prediction accuracy history
        
    async def gather_market_data(self, symbol: str, period: str = "2y") -> pd.DataFrame:
        """
        Gather market data for a given symbol (simplified to prevent hanging)
        
        Args:
            symbol: Stock symbol
            period: Data period (default 2y to prevent hanging)
            
        Returns:
            DataFrame with OHLCV data and basic technical indicators
        """
        try:
            logger.info(f"Gathering market data for {symbol}")
            
            # Get stock data from Yahoo Finance
            stock = yf.Ticker(symbol)
            df = stock.history(period=period)
            
            if df.empty:
                raise ValueError(f"No data found for symbol {symbol}")
            
            # Add basic technical indicators only
            df = self._add_basic_technical_indicators(df)
            
            # Clean and prepare data
            df = df.dropna()
            
            logger.info(f"Successfully gathered {len(df)} data points for {symbol}")
            return df
            
        except Exception as e:
            logger.error(f"Error gathering data for {symbol}: {str(e)}")
            raise
    
    def _add_basic_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add basic technical indicators to the dataframe"""
        try:
            # Moving averages
            df['SMA_20'] = df['Close'].rolling(window=20).mean()
            df['SMA_50'] = df['Close'].rolling(window=50).mean()
            
            # RSI
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))
            
            # MACD
            ema12 = df['Close'].ewm(span=12).mean()
            ema26 = df['Close'].ewm(span=26).mean()
            df['MACD'] = ema12 - ema26
            df['MACD_Signal'] = df['MACD'].ewm(span=9).mean()
            
            # Volume indicators
            df['Volume_SMA'] = df['Volume'].rolling(window=20).mean()
            df['Volume_Ratio'] = df['Volume'] / df['Volume_SMA']
            
            # Price changes
            df['Price_Change_1'] = df['Close'].pct_change(1)
            df['Price_Change_5'] = df['Close'].pct_change(5)
            
            return df
            
        except Exception as e:
            logger.error(f"Error adding technical indicators: {str(e)}")
            return df
    
    def prepare_lstm_data(self, df: pd.DataFrame, lookback_days: int = 60) -> Tuple[np.ndarray, np.ndarray, MinMaxScaler]:
        """
        Prepare data for LSTM model training
        
        Args:
            df: DataFrame with market data
            lookback_days: Number of days to look back for prediction
            
        Returns:
            X: Input features (lookback_days, features)
            y: Target values (next day's close price)
            scaler: Fitted MinMaxScaler for inverse transformation
        """
        try:
            # Select feature columns
            feature_columns = ['Close', 'Volume', 'SMA_20', 'SMA_50', 'RSI', 'MACD', 'MACD_Signal', 'Volume_Ratio', 'Price_Change_1', 'Price_Change_5']
            
            # Filter available columns
            available_columns = [col for col in feature_columns if col in df.columns]
            if len(available_columns) < 3:
                available_columns = ['Close', 'Volume', 'SMA_20']  # Fallback to basic features
            
            # Prepare data
            data = df[available_columns].values
            
            # Scale the data
            scaler = MinMaxScaler()
            data_scaled = scaler.fit_transform(data)
            
            # Create sequences
            X, y = [], []
            for i in range(lookback_days, len(data_scaled)):
                X.append(data_scaled[i-lookback_days:i])
                y.append(data_scaled[i, 0])  # Predict Close price
            
            X = np.array(X)
            y = np.array(y)
            
            logger.info(f"Prepared LSTM data with {len(available_columns)} features: {available_columns}")
            logger.info(f"Training set: {len(X)} samples")
            
            return X, y, scaler
            
        except Exception as e:
            logger.error(f"Error preparing LSTM data: {str(e)}")
            raise
    
    def build_lstm_model(self, input_shape: tuple) -> tf.keras.Model:
        """
        Build a simplified LSTM model for stock price prediction
        
        Args:
            input_shape: Shape of input data (timesteps, features)
            
        Returns:
            Compiled Keras model
        """
        model = tf.keras.Sequential([
            # Simple LSTM architecture to prevent hanging
            tf.keras.layers.LSTM(32, return_sequences=True, input_shape=input_shape),
            tf.keras.layers.Dropout(0.1),
            tf.keras.layers.LSTM(16, return_sequences=False),
            tf.keras.layers.Dropout(0.1),
            tf.keras.layers.Dense(8, activation='relu'),
            tf.keras.layers.Dense(1, activation='linear')
        ])
        
        # Use legacy Adam optimizer for M1/M2 Mac performance
        try:
            optimizer = tf.keras.optimizers.legacy.Adam(learning_rate=0.001)
        except:
            optimizer = tf.keras.optimizers.Adam(learning_rate=0.001)
        
        model.compile(
            optimizer=optimizer,
            loss='mse',
            metrics=['mae']
        )
        
        return model
    
    async def train_model(self, symbol: str, lookback_days: int = 60, epochs: int = 30) -> Dict:
        """
        Train LSTM model for stock price prediction (simplified to prevent hanging)
        
        Args:
            symbol: Stock symbol to train
            lookback_days: Number of days to look back for prediction
            epochs: Number of training epochs (reduced to prevent hanging)
            
        Returns:
            Training results dictionary
        """
        try:
            logger.info(f"Training simplified LSTM model for {symbol}")
            
            # Gather and prepare data
            df = await self.gather_market_data(symbol)
            X, y, scaler = self.prepare_lstm_data(df, lookback_days)
            
            if len(X) < 100:
                raise ValueError(f"Insufficient data for {symbol}: {len(X)} samples")
            
            # Split data (80% training, 20% validation)
            split_idx = int(len(X) * 0.8)
            X_train, X_val = X[:split_idx], X[split_idx:]
            y_train, y_val = y[:split_idx], y[split_idx:]
            
            logger.info(f"Training set: {len(X_train)} samples, Validation set: {len(X_val)} samples")
            
            # Build simplified model
            model = self.build_lstm_model((lookback_days, X.shape[2]))
            
            # Simple callbacks to prevent hanging
            callbacks = [
                tf.keras.callbacks.EarlyStopping(
                    monitor='val_loss',
                    patience=5,
                    restore_best_weights=True
                )
            ]
            
            # Train with simplified parameters
            history = model.fit(
                X_train, y_train,
                validation_data=(X_val, y_val),
                epochs=epochs,
                batch_size=32,
                callbacks=callbacks,
                verbose=1,
                shuffle=True
            )
            
            # Evaluate model
            val_loss = model.evaluate(X_val, y_val, verbose=0)
            train_loss = model.evaluate(X_train, y_train, verbose=0)
            
            # Calculate accuracy metrics
            y_pred = model.predict(X_val, verbose=0)
            mae = np.mean(np.abs(y_val - y_pred.flatten()))
            rmse = np.sqrt(np.mean((y_val - y_pred.flatten()) ** 2))
            
            # Calculate accuracy as percentage of predictions within 5% of actual
            accuracy = np.mean(np.abs((y_val - y_pred.flatten()) / y_val) < 0.05) * 100
            
            # Save model to disk
            models_dir = "models"
            if not os.path.exists(models_dir):
                os.makedirs(models_dir)
            
            model_path = os.path.join(models_dir, f"{symbol}_lstm_model.h5")
            model.save(model_path)
            
            # Store training results
            training_results = {
                'symbol': symbol,
                'status': 'completed',
                'model_path': model_path,
                'training_date': datetime.now().isoformat(),
                'data_points': len(X),
                'features_used': X.shape[2],
                'training_samples': len(X_train),
                'validation_samples': len(X_val),
                'epochs_trained': len(history.history['loss']),
                'final_train_loss': float(train_loss[0]),
                'final_val_loss': float(val_loss[0]),
                'mae': float(mae),
                'rmse': float(rmse),
                'accuracy': float(accuracy),
                'model_architecture': 'Simplified LSTM (32->16->8->1)'
            }
            
            self.prediction_history[symbol] = training_results
            
            logger.info(f"Model training completed for {symbol}. RMSE: {rmse:.4f}, Accuracy: {accuracy:.2f}%")
            
            return training_results
            
        except Exception as e:
            logger.error(f"Error training model for {symbol}: {str(e)}")
            error_result = {
                'symbol': symbol,
                'status': 'failed',
                'error': str(e),
                'training_date': datetime.now().isoformat()
            }
            self.prediction_history[symbol] = error_result
            return error_result
    
    async def predict_price(self, symbol: str, days_ahead: int = 30) -> Dict:
        """
        Predict stock price for the next N days
        
        Args:
            symbol: Stock symbol
            days_ahead: Number of days to predict ahead
            
        Returns:
            Prediction results with confidence intervals
        """
        try:
            if symbol not in self.prediction_history:
                return {
                    'symbol': symbol,
                    'error': 'Model not trained. Please train the model first.'
                }
            
            # Load model from disk
            model_path = self.prediction_history[symbol].get('model_path')
            if not model_path or not os.path.exists(model_path):
                return {
                    'symbol': symbol,
                    'error': 'Model file not found. Please retrain the model.'
                }
            
            # Load the model
            model = tf.keras.models.load_model(model_path)
            
            # Get recent data for prediction
            df = await self.gather_market_data(symbol, period="6mo")
            X, y, scaler = self.prepare_lstm_data(df, lookback_days=60)
            
            if len(X) == 0:
                return {
                    'symbol': symbol,
                    'error': 'Insufficient recent data for prediction'
                }
            
            # Make prediction
            latest_sequence = X[-1:]
            prediction_scaled = model.predict(latest_sequence, verbose=0)
            
            # Inverse transform to get actual price
            prediction_actual = scaler.inverse_transform(
                np.concatenate([prediction_scaled, np.zeros((1, scaler.n_features_in_ - 1))], axis=1)
            )[:, 0]
            
            # Get current price for comparison
            current_price = df['Close'].iloc[-1]
            predicted_price = prediction_actual[0]
            
            # Calculate confidence (simple approach)
            confidence = max(0, min(100, 100 - abs((predicted_price - current_price) / current_price * 100)))
            
            return {
                'symbol': symbol,
                'current_price': float(current_price),
                'predicted_price': float(predicted_price),
                'price_change': float(predicted_price - current_price),
                'price_change_percent': float((predicted_price - current_price) / current_price * 100),
                'confidence': float(confidence),
                'prediction_date': datetime.now().isoformat(),
                'days_ahead': days_ahead
            }
            
        except Exception as e:
            logger.error(f"Error predicting price for {symbol}: {str(e)}")
            return {
                'symbol': symbol,
                'error': f'Prediction failed: {str(e)}'
            }
    
    async def backtest_model(self, symbol: str, test_period_days: int = 90) -> Dict:
        """
        Backtest the trained model on historical data
        
        Args:
            symbol: Stock symbol
            test_period_days: Number of days to test
            
        Returns:
            Backtesting results and performance metrics
        """
        try:
            if symbol not in self.prediction_history:
                return {
                    'symbol': symbol,
                    'error': 'Model not trained. Please train the model first.'
                }
            
            # Load model from disk
            model_path = self.prediction_history[symbol].get('model_path')
            if not model_path or not os.path.exists(model_path):
                return {
                    'symbol': symbol,
                    'error': 'Model file not found. Please retrain the model.'
                }
            
            # Load the model
            model = tf.keras.models.load_model(model_path)
            
            # Get data for backtesting
            df = await self.gather_market_data(symbol, period="6mo")
            X, y, scaler = self.prepare_lstm_data(df, lookback_days=60)
            
            if len(X) < test_period_days:
                return {
                    'symbol': symbol,
                    'error': f'Insufficient data for {test_period_days} day backtest'
                }
            
            # Use last test_period_days for backtesting
            X_test = X[-test_period_days:]
            y_test = y[-test_period_days:]
            
            # Make predictions
            predictions_scaled = model.predict(X_test, verbose=0)
            
            # Inverse transform predictions
            predictions_actual = []
            for pred in predictions_scaled:
                pred_reshaped = np.concatenate([pred, np.zeros(scaler.n_features_in_ - 1)])
                pred_actual = scaler.inverse_transform(pred_reshaped.reshape(1, -1))[0, 0]
                predictions_actual.append(pred_actual)
            
            # Calculate metrics
            actual_prices = scaler.inverse_transform(
                np.concatenate([y_test.reshape(-1, 1), np.zeros((len(y_test), scaler.n_features_in_ - 1))], axis=1)
            )[:, 0]
            
            mae = np.mean(np.abs(np.array(predictions_actual) - actual_prices))
            rmse = np.sqrt(np.mean((np.array(predictions_actual) - actual_prices) ** 2))
            accuracy = np.mean(np.abs((np.array(predictions_actual) - actual_prices) / actual_prices) < 0.05) * 100
            
            return {
                'symbol': symbol,
                'backtest_period_days': test_period_days,
                'mae': float(mae),
                'rmse': float(rmse),
                'accuracy': float(accuracy),
                'test_samples': len(X_test),
                'backtest_date': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error backtesting model for {symbol}: {str(e)}")
            return {
                'symbol': symbol,
                'error': f'Backtest failed: {str(e)}'
            }
    
    def get_model_status(self, symbol: str = None) -> Dict:
        """Get status of trained models"""
        if symbol:
            return self.prediction_history.get(symbol, {})
        else:
            # Get list of symbols that have been trained (from prediction history)
            trained_symbols = list(self.prediction_history.keys())
            
            return {
                'trained_models': trained_symbols,
                'model_count': len(trained_symbols),
                'prediction_history': self.prediction_history
            }
    
    def delete_model(self, symbol: str) -> Dict:
        """Delete a trained model"""
        try:
            if symbol in self.prediction_history:
                # Get model file path
                model_path = self.prediction_history[symbol].get('model_path')
                
                # Delete model file if it exists
                if model_path and os.path.exists(model_path):
                    os.remove(model_path)
                
                # Remove from prediction history
                del self.prediction_history[symbol]
                
                return {
                    'symbol': symbol,
                    'status': 'deleted',
                    'message': f'Model for {symbol} has been deleted'
                }
            else:
                return {
                    'symbol': symbol,
                    'error': 'Model not found'
                }
                
        except Exception as e:
            logger.error(f"Error deleting model for {symbol}: {str(e)}")
            return {
                'symbol': symbol,
                'error': f'Delete failed: {str(e)}'
            }
    
    async def get_model_insights(self, symbol: str) -> Dict:
        """Get insights about a trained model"""
        try:
            if symbol not in self.prediction_history:
                return {
                    'symbol': symbol,
                    'error': 'Model not trained. Please train the model first.'
                }
            
            model_info = self.prediction_history[symbol]
            
            # Basic performance analysis
            if 'accuracy' in model_info:
                if model_info['accuracy'] > 70:
                    performance_rating = "Excellent"
                    interpretation = "Model shows strong predictive power"
                elif model_info['accuracy'] > 50:
                    performance_rating = "Good"
                    interpretation = "Model shows reasonable predictive power"
                else:
                    performance_rating = "Fair"
                    interpretation = "Model may need improvement"
            else:
                performance_rating = "Unknown"
                interpretation = "Accuracy metrics not available"
            
            # Feature insights
            features_used = model_info.get('features_used', 0)
            if features_used >= 8:
                feature_rating = "Comprehensive"
                feature_description = f"Using {features_used} features including price, volume, and technical indicators"
            elif features_used >= 5:
                feature_rating = "Moderate"
                feature_description = f"Using {features_used} features for prediction"
            else:
                feature_rating = "Basic"
                feature_description = f"Using {features_used} basic features"
            
            # Improvement recommendations
            recommendations = []
            if model_info.get('accuracy', 0) < 60:
                recommendations.append("Consider increasing training data period")
                recommendations.append("Try different lookback periods")
                recommendations.append("Add more technical indicators")
            
            if model_info.get('epochs_trained', 0) < 20:
                recommendations.append("Increase training epochs for better convergence")
            
            if not recommendations:
                recommendations.append("Model is performing well - consider ensemble methods for further improvement")
            
            return {
                'symbol': symbol,
                'performance_analysis': {
                    'rating': performance_rating,
                    'interpretation': interpretation,
                    'accuracy': model_info.get('accuracy', 'N/A'),
                    'rmse': model_info.get('rmse', 'N/A')
                },
                'key_features': {
                    'rating': feature_rating,
                    'description': feature_description,
                    'features_count': features_used
                },
                'improvement_recommendations': recommendations,
                'last_updated': model_info.get('training_date', 'N/A')
            }
            
        except Exception as e:
            logger.error(f"Error getting insights for {symbol}: {str(e)}")
            return {
                'symbol': symbol,
                'error': f'Failed to get insights: {str(e)}'
            }
