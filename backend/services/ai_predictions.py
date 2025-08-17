import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.optimizers import Adam
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error
import asyncio
from typing import Dict, List, Tuple, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StockPricePredictor:
    """
    AI-powered stock price prediction using LSTM neural networks
    """
    
    def __init__(self):
        self.models = {}  # Store trained models for each symbol
        self.scalers = {}  # Store scalers for each symbol
        self.prediction_history = {}  # Store prediction accuracy history
        
    async def gather_market_data(self, symbol: str, period: str = "5y") -> pd.DataFrame:
        """
        Gather comprehensive market data for a given symbol
        
        Args:
            symbol: Stock symbol
            period: Data period (1y, 2y, 5y, max)
            
        Returns:
            DataFrame with OHLCV data and technical indicators
        """
        try:
            logger.info(f"Gathering market data for {symbol}")
            
            # Get stock data from Yahoo Finance
            stock = yf.Ticker(symbol)
            df = stock.history(period=period)
            
            if df.empty:
                raise ValueError(f"No data found for symbol {symbol}")
            
            # Add technical indicators
            df = self._add_technical_indicators(df)
            
            # Add market sentiment indicators (simplified)
            df = self._add_sentiment_indicators(df)
            
            # Clean and prepare data
            df = df.dropna()
            
            logger.info(f"Successfully gathered {len(df)} data points for {symbol}")
            return df
            
        except Exception as e:
            logger.error(f"Error gathering data for {symbol}: {str(e)}")
            raise
    
    def _add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add technical indicators to the dataframe"""
        try:
            # Moving averages
            df['SMA_20'] = df['Close'].rolling(window=20).mean()
            df['SMA_50'] = df['Close'].rolling(window=50).mean()
            df['EMA_12'] = df['Close'].ewm(span=12).mean()
            df['EMA_26'] = df['Close'].ewm(span=26).mean()
            
            # RSI
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))
            
            # MACD
            df['MACD'] = df['EMA_12'] - df['EMA_26']
            df['MACD_Signal'] = df['MACD'].ewm(span=9).mean()
            df['MACD_Histogram'] = df['MACD'] - df['MACD_Signal']
            
            # Bollinger Bands
            df['BB_Middle'] = df['Close'].rolling(window=20).mean()
            bb_std = df['Close'].rolling(window=20).std()
            df['BB_Upper'] = df['BB_Middle'] + (bb_std * 2)
            df['BB_Lower'] = df['BB_Middle'] - (bb_std * 2)
            
            # Volume indicators
            df['Volume_SMA'] = df['Volume'].rolling(window=20).mean()
            df['Volume_Ratio'] = df['Volume'] / df['Volume_SMA']
            
            # Volatility
            df['Volatility'] = df['Close'].rolling(window=20).std()
            df['Volatility_Ratio'] = df['Volatility'] / df['Close']
            
            # Price momentum
            df['Price_Change'] = df['Close'].pct_change()
            df['Price_Change_5'] = df['Close'].pct_change(periods=5)
            df['Price_Change_20'] = df['Close'].pct_change(periods=20)
            
            return df
            
        except Exception as e:
            logger.error(f"Error adding technical indicators: {str(e)}")
            return df
    
    def _add_sentiment_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add simplified sentiment indicators"""
        try:
            # Market trend indicator
            df['Trend'] = np.where(df['SMA_20'] > df['SMA_50'], 1, 0)
            
            # Volatility regime
            df['Vol_Regime'] = np.where(df['Volatility_Ratio'] > df['Volatility_Ratio'].quantile(0.8), 'High', 
                                      np.where(df['Volatility_Ratio'] < df['Volatility_Ratio'].quantile(0.2), 'Low', 'Medium'))
            
            # RSI regime
            df['RSI_Regime'] = np.where(df['RSI'] > 70, 'Overbought',
                                      np.where(df['RSI'] < 30, 'Oversold', 'Neutral'))
            
            return df
            
        except Exception as e:
            logger.error(f"Error adding sentiment indicators: {str(e)}")
            return df
    
    def prepare_lstm_data(self, df: pd.DataFrame, lookback_days: int = 60) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare data for LSTM model training
        
        Args:
            df: DataFrame with market data
            lookback_days: Number of days to look back for prediction
            
        Returns:
            X: Input features (lookback_days, features)
            y: Target values (next day's close price)
        """
        try:
            # Select features for the model
            feature_columns = [
                'Close', 'Volume', 'SMA_20', 'SMA_50', 'EMA_12', 'EMA_26',
                'RSI', 'MACD', 'MACD_Signal', 'MACD_Histogram',
                'BB_Middle', 'BB_Upper', 'BB_Lower',
                'Volume_Ratio', 'Volatility_Ratio', 'Price_Change_5', 'Price_Change_20'
            ]
            
            # Filter available features
            available_features = [col for col in feature_columns if col in df.columns]
            data = df[available_features].values
            
            # Normalize the data
            scaler = MinMaxScaler()
            data_scaled = scaler.fit_transform(data)
            
            # Create sequences for LSTM
            X, y = [], []
            for i in range(lookback_days, len(data_scaled)):
                X.append(data_scaled[i-lookback_days:i])
                y.append(data_scaled[i, 0])  # Predict close price (first column)
            
            X = np.array(X)
            y = np.array(y)
            
            return X, y, scaler
            
        except Exception as e:
            logger.error(f"Error preparing LSTM data: {str(e)}")
            raise
    
    def build_lstm_model(self, input_shape: Tuple[int, int], learning_rate: float = 0.001) -> Sequential:
        """
        Build LSTM neural network model
        
        Args:
            input_shape: Shape of input data (lookback_days, features)
            learning_rate: Learning rate for optimizer
            
        Returns:
            Compiled LSTM model
        """
        try:
            model = Sequential([
                LSTM(units=100, return_sequences=True, input_shape=input_shape),
                Dropout(0.2),
                LSTM(units=100, return_sequences=True),
                Dropout(0.2),
                LSTM(units=100, return_sequences=False),
                Dropout(0.2),
                Dense(units=50, activation='relu'),
                Dropout(0.2),
                Dense(units=1, activation='linear')
            ])
            
            optimizer = Adam(learning_rate=learning_rate)
            model.compile(optimizer=optimizer, loss='mse', metrics=['mae'])
            
            return model
            
        except Exception as e:
            logger.error(f"Error building LSTM model: {str(e)}")
            raise
    
    async def train_model(self, symbol: str, lookback_days: int = 60, epochs: int = 100) -> Dict:
        """
        Train LSTM model for a given symbol
        
        Args:
            symbol: Stock symbol
            lookback_days: Number of days to look back
            epochs: Number of training epochs
            
        Returns:
            Training results and model performance
        """
        try:
            logger.info(f"Training LSTM model for {symbol}")
            
            # Gather data
            df = await self.gather_market_data(symbol)
            
            # Prepare data
            X, y, scaler = self.prepare_lstm_data(df, lookback_days)
            
            # Split data into train and validation sets
            split_idx = int(len(X) * 0.8)
            X_train, X_val = X[:split_idx], X[split_idx:]
            y_train, y_val = y[:split_idx], y[split_idx:]
            
            # Build and train model
            model = self.build_lstm_model((X.shape[1], X.shape[2]))
            
            # Early stopping to prevent overfitting
            early_stopping = tf.keras.callbacks.EarlyStopping(
                monitor='val_loss', patience=10, restore_best_weights=True
            )
            
            history = model.fit(
                X_train, y_train,
                validation_data=(X_val, y_val),
                epochs=epochs,
                batch_size=32,
                callbacks=[early_stopping],
                verbose=0
            )
            
            # Evaluate model
            val_predictions = model.predict(X_val)
            
            # Inverse transform predictions
            val_predictions_original = scaler.inverse_transform(
                np.concatenate([val_predictions, np.zeros((len(val_predictions), X.shape[2]-1))], axis=1)
            )[:, 0]
            
            y_val_original = scaler.inverse_transform(
                np.concatenate([y_val.reshape(-1, 1), np.zeros((len(y_val), X.shape[2]-1))], axis=1)
            )[:, 0]
            
            # Calculate metrics
            mse = mean_squared_error(y_val_original, val_predictions_original)
            mae = mean_absolute_error(y_val_original, val_predictions_original)
            rmse = np.sqrt(mse)
            
            # Calculate accuracy metrics
            accuracy = self._calculate_prediction_accuracy(y_val_original, val_predictions_original)
            
            # Store model and scaler
            self.models[symbol] = model
            self.scalers[symbol] = scaler
            
            # Store prediction history
            self.prediction_history[symbol] = {
                'last_training': datetime.now().isoformat(),
                'validation_metrics': {
                    'mse': float(mse),
                    'mae': float(mae),
                    'rmse': float(rmse),
                    'accuracy': accuracy
                },
                'training_history': {
                    'loss': [float(x) for x in history.history['loss']],
                    'val_loss': [float(x) for x in history.history['val_loss']],
                    'mae': [float(x) for x in history.history['mae']],
                    'val_mae': [float(x) for x in history.history['val_mae']]
                }
            }
            
            logger.info(f"Model training completed for {symbol}. RMSE: {rmse:.4f}, Accuracy: {accuracy:.2f}%")
            
            return {
                'symbol': symbol,
                'training_status': 'completed',
                'validation_metrics': self.prediction_history[symbol]['validation_metrics'],
                'training_history': self.prediction_history[symbol]['training_history']
            }
            
        except Exception as e:
            logger.error(f"Error training model for {symbol}: {str(e)}")
            return {
                'symbol': symbol,
                'training_status': 'failed',
                'error': str(e)
            }
    
    def _calculate_prediction_accuracy(self, actual: np.ndarray, predicted: np.ndarray) -> float:
        """Calculate directional accuracy of predictions"""
        try:
            # Calculate directional accuracy (up/down movement)
            actual_direction = np.diff(actual) > 0
            predicted_direction = np.diff(predicted) > 0
            
            accuracy = np.mean(actual_direction == predicted_direction) * 100
            return accuracy
            
        except Exception as e:
            logger.error(f"Error calculating prediction accuracy: {str(e)}")
            return 0.0
    
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
            if symbol not in self.models:
                return {
                    'symbol': symbol,
                    'error': 'Model not trained. Please train the model first.'
                }
            
            # Get recent data for prediction
            df = await self.gather_market_data(symbol, period="1y")
            X, _, scaler = self.prepare_lstm_data(df)
            
            if len(X) == 0:
                return {
                    'symbol': symbol,
                    'error': 'Insufficient data for prediction'
                }
            
            # Get the most recent sequence
            latest_sequence = X[-1:]
            
            # Make predictions
            predictions = []
            current_sequence = latest_sequence.copy()
            
            for _ in range(days_ahead):
                # Predict next day
                pred = self.models[symbol].predict(current_sequence, verbose=0)
                predictions.append(pred[0, 0])
                
                # Update sequence for next prediction
                new_row = np.zeros((1, current_sequence.shape[2]))
                new_row[0, 0] = pred[0, 0]  # Update close price
                # You could update other features here for more accurate multi-step prediction
                
                current_sequence = np.roll(current_sequence, -1, axis=1)
                current_sequence[0, -1] = new_row[0]
            
            # Inverse transform predictions
            predictions_original = scaler.inverse_transform(
                np.concatenate([np.array(predictions).reshape(-1, 1), 
                              np.zeros((len(predictions), X.shape[2]-1))], axis=1)
            )[:, 0]
            
            # Calculate confidence intervals (simplified)
            confidence_intervals = self._calculate_confidence_intervals(predictions_original)
            
            # Get current price for comparison
            current_price = df['Close'].iloc[-1]
            
            return {
                'symbol': symbol,
                'current_price': float(current_price),
                'predictions': [float(p) for p in predictions_original],
                'prediction_dates': [
                    (datetime.now() + timedelta(days=i+1)).strftime('%Y-%m-%d')
                    for i in range(days_ahead)
                ],
                'confidence_intervals': confidence_intervals,
                'model_accuracy': self.prediction_history[symbol]['validation_metrics']['accuracy'],
                'prediction_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error predicting price for {symbol}: {str(e)}")
            return {
                'symbol': symbol,
                'error': str(e)
            }
    
    def _calculate_confidence_intervals(self, predictions: np.ndarray) -> Dict:
        """Calculate confidence intervals for predictions"""
        try:
            # Simple confidence intervals based on historical volatility
            # In a real implementation, you might use more sophisticated methods
            
            # Calculate prediction volatility
            pred_volatility = np.std(predictions) * 0.1  # Simplified
            
            confidence_intervals = {
                'lower_68': [float(p - pred_volatility) for p in predictions],
                'upper_68': [float(p + pred_volatility) for p in predictions],
                'lower_95': [float(p - 2*pred_volatility) for p in predictions],
                'upper_95': [float(p + 2*pred_volatility) for p in predictions]
            }
            
            return confidence_intervals
            
        except Exception as e:
            logger.error(f"Error calculating confidence intervals: {str(e)}")
            return {}
    
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
            if symbol not in self.models:
                return {
                    'symbol': symbol,
                    'error': 'Model not trained. Please train the model first.'
                }
            
            # Get historical data
            df = await self.gather_market_data(symbol, period="1y")
            
            # Prepare data for backtesting
            X, y, scaler = self.prepare_lstm_data(df)
            
            # Use the last test_period_days for backtesting
            if len(X) < test_period_days:
                test_period_days = len(X)
            
            X_test = X[-test_period_days:]
            y_test = y[-test_period_days:]
            
            # Make predictions
            predictions = self.models[symbol].predict(X_test, verbose=0)
            
            # Inverse transform
            predictions_original = scaler.inverse_transform(
                np.concatenate([predictions, np.zeros((len(predictions), X.shape[2]-1))], axis=1)
            )[:, 0]
            
            y_test_original = scaler.inverse_transform(
                np.concatenate([y_test.reshape(-1, 1), np.zeros((len(y_test), X.shape[2]-1))], axis=1)
            )[:, 0]
            
            # Calculate backtesting metrics
            backtest_metrics = self._calculate_backtest_metrics(y_test_original, predictions_original)
            
            return {
                'symbol': symbol,
                'backtest_period_days': test_period_days,
                'metrics': backtest_metrics,
                'actual_prices': [float(p) for p in y_test_original],
                'predicted_prices': [float(p) for p in predictions_original],
                'backtest_dates': df.index[-test_period_days:].strftime('%Y-%m-%d').tolist()
            }
            
        except Exception as e:
            logger.error(f"Error backtesting model for {symbol}: {str(e)}")
            return {
                'symbol': symbol,
                'error': str(e)
            }
    
    def _calculate_backtest_metrics(self, actual: np.ndarray, predicted: np.ndarray) -> Dict:
        """Calculate comprehensive backtesting metrics"""
        try:
            # Basic error metrics
            mse = mean_squared_error(actual, predicted)
            mae = mean_absolute_error(actual, predicted)
            rmse = np.sqrt(mse)
            
            # Percentage errors
            mape = np.mean(np.abs((actual - predicted) / actual)) * 100
            
            # Directional accuracy
            actual_direction = np.diff(actual) > 0
            predicted_direction = np.diff(predicted) > 0
            directional_accuracy = np.mean(actual_direction == predicted_direction) * 100
            
            # Profit/Loss simulation (simplified)
            # This is a basic simulation - in reality, you'd need more sophisticated trading logic
            cumulative_return = np.sum((predicted - actual) / actual) * 100
            
            return {
                'mse': float(mse),
                'mae': float(mae),
                'rmse': float(rmse),
                'mape': float(mape),
                'directional_accuracy': float(directional_accuracy),
                'cumulative_return': float(cumulative_return)
            }
            
        except Exception as e:
            logger.error(f"Error calculating backtest metrics: {str(e)}")
            return {}
    
    def get_model_status(self, symbol: str = None) -> Dict:
        """Get status of trained models"""
        if symbol:
            return self.prediction_history.get(symbol, {})
        else:
            return {
                'trained_models': list(self.models.keys()),
                'model_count': len(self.models),
                'prediction_history': self.prediction_history
            }
    
    def delete_model(self, symbol: str) -> Dict:
        """Delete a trained model"""
        try:
            if symbol in self.models:
                del self.models[symbol]
                del self.scalers[symbol]
                if symbol in self.prediction_history:
                    del self.prediction_history[symbol]
                
                return {
                    'symbol': symbol,
                    'status': 'deleted',
                    'message': f'Model for {symbol} has been deleted'
                }
            else:
                return {
                    'symbol': symbol,
                    'status': 'not_found',
                    'message': f'No model found for {symbol}'
                }
                
        except Exception as e:
            logger.error(f"Error deleting model for {symbol}: {str(e)}")
            return {
                'symbol': symbol,
                'status': 'error',
                'error': str(e)
            }

# Global instance
ai_predictor = StockPricePredictor()
