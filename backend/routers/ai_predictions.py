from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import asyncio
from services.ai_predictions import ai_predictor
import logging

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai-predictions", tags=["AI Predictions"])

# Pydantic models for request/response
class TrainModelRequest(BaseModel):
    symbol: str
    lookback_days: Optional[int] = 60
    epochs: Optional[int] = 100

class PredictionRequest(BaseModel):
    symbol: str
    days_ahead: Optional[int] = 30

class BacktestRequest(BaseModel):
    symbol: str
    test_period_days: Optional[int] = 90

class PortfolioSymbolsRequest(BaseModel):
    portfolio_name: str

@router.post("/train")
async def train_model(request: TrainModelRequest, background_tasks: BackgroundTasks):
    """
    Train an LSTM model for stock price prediction
    
    This endpoint will:
    1. Gather comprehensive market data (5 years of OHLCV + technical indicators)
    2. Prepare data for LSTM training
    3. Train a deep learning model with early stopping
    4. Validate model performance
    5. Store the trained model for future predictions
    """
    try:
        logger.info(f"Training request received for {request.symbol}")
        
        # Start training in background
        background_tasks.add_task(
            ai_predictor.train_model,
            request.symbol,
            request.lookback_days,
            request.epochs
        )
        
        return {
            "message": f"Training started for {request.symbol}",
            "symbol": request.symbol,
            "status": "training_started",
            "estimated_time": "5-15 minutes depending on data size and epochs"
        }
        
    except Exception as e:
        logger.error(f"Error starting training for {request.symbol}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Training failed: {str(e)}")

@router.get("/train/status/{symbol}")
async def get_training_status(symbol: str):
    """
    Get the training status and results for a specific symbol
    """
    try:
        status = ai_predictor.get_model_status(symbol)
        
        if not status:
            return {
                "symbol": symbol,
                "status": "not_trained",
                "message": f"No trained model found for {symbol}"
            }
        
        return {
            "symbol": symbol,
            "status": "trained",
            "last_training": status.get("last_training"),
            "validation_metrics": status.get("validation_metrics", {}),
            "training_history": status.get("training_history", {})
        }
        
    except Exception as e:
        logger.error(f"Error getting training status for {symbol}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving status: {str(e)}")

@router.post("/predict")
async def predict_price(request: PredictionRequest):
    """
    Predict stock price for the next N days using trained LSTM model
    
    Returns:
    - Current price
    - Predicted prices for next N days
    - Confidence intervals (68% and 95%)
    - Model accuracy metrics
    """
    try:
        logger.info(f"Prediction request received for {request.symbol}")
        
        prediction = await ai_predictor.predict_price(request.symbol, request.days_ahead)
        
        if "error" in prediction:
            raise HTTPException(status_code=400, detail=prediction["error"])
        
        return prediction
        
    except Exception as e:
        logger.error(f"Error making prediction for {request.symbol}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

@router.post("/backtest")
async def backtest_model(request: BacktestRequest):
    """
    Backtest the trained model on historical data
    
    Returns:
    - Backtesting metrics (RMSE, MAE, MAPE, directional accuracy)
    - Actual vs predicted prices
    - Performance analysis
    """
    try:
        logger.info(f"Backtest request received for {request.symbol}")
        
        backtest_results = await ai_predictor.backtest_model(
            request.symbol, 
            request.test_period_days
        )
        
        if "error" in backtest_results:
            raise HTTPException(status_code=400, detail=backtest_results["error"])
        
        return backtest_results
        
    except Exception as e:
        logger.error(f"Error backtesting model for {request.symbol}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Backtesting failed: {str(e)}")

@router.get("/models/status")
async def get_all_models_status():
    """
    Get status of all trained models
    """
    try:
        return ai_predictor.get_model_status()
        
    except Exception as e:
        logger.error(f"Error getting models status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving models status: {str(e)}")

@router.delete("/models/{symbol}")
async def delete_model(symbol: str):
    """
    Delete a trained model for a specific symbol
    """
    try:
        result = ai_predictor.delete_model(symbol)
        return result
        
    except Exception as e:
        logger.error(f"Error deleting model for {symbol}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting model: {str(e)}")

@router.post("/portfolio/symbols")
async def get_portfolio_symbols(request: PortfolioSymbolsRequest):
    """
    Get all stock symbols from a specific portfolio for AI training suggestions
    """
    try:
        # Import existing portfolio service to get symbols
        from routers.portfolios import get_portfolio_positions
        
        positions = await get_portfolio_positions(request.portfolio_name)
        
        if "error" in positions:
            raise HTTPException(status_code=400, detail=positions["error"])
        
        # Extract stock symbols (exclude cash)
        stock_symbols = [
            pos["symbol"] for pos in positions.get("positions", [])
            if pos["symbol"] != "CASH_USD"
        ]
        
        return {
            "portfolio_name": request.portfolio_name,
            "stock_symbols": stock_symbols,
            "symbol_count": len(stock_symbols),
            "message": f"Found {len(stock_symbols)} stocks in portfolio {request.portfolio_name}"
        }
        
    except Exception as e:
        logger.error(f"Error getting portfolio symbols: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving portfolio symbols: {str(e)}")

@router.post("/portfolio/bulk-train")
async def bulk_train_portfolio_models(request: PortfolioSymbolsRequest, background_tasks: BackgroundTasks):
    """
    Start training models for all stocks in a portfolio
    
    This will train LSTM models for all stocks in the specified portfolio
    """
    try:
        # Get portfolio symbols
        from routers.portfolios import get_portfolio_positions
        
        positions = await get_portfolio_positions(request.portfolio_name)
        
        if "error" in positions:
            raise HTTPException(status_code=400, detail=positions["error"])
        
        stock_symbols = [
            pos["symbol"] for pos in positions.get("positions", [])
            if pos["symbol"] != "CASH_USD"
        ]
        
        if not stock_symbols:
            return {
                "portfolio_name": request.portfolio_name,
                "message": "No stocks found in portfolio",
                "symbols_training": []
            }
        
        # Start training for each symbol
        training_symbols = []
        for symbol in stock_symbols:
            try:
                background_tasks.add_task(
                    ai_predictor.train_model,
                    symbol,
                    60,  # Default lookback days
                    100  # Default epochs
                )
                training_symbols.append(symbol)
            except Exception as e:
                logger.error(f"Failed to start training for {symbol}: {str(e)}")
        
        return {
            "portfolio_name": request.portfolio_name,
            "message": f"Started training for {len(training_symbols)} stocks",
            "symbols_training": training_symbols,
            "total_symbols": len(stock_symbols),
            "estimated_time": f"{len(training_symbols) * 10} minutes for all models"
        }
        
    except Exception as e:
        logger.error(f"Error starting bulk training: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Bulk training failed: {str(e)}")

@router.get("/help")
async def get_ai_predictions_help():
    """
    Get help and information about the AI Predictions module
    """
    return {
        "module": "AI Stock Price Predictions",
        "description": "LSTM-based neural network models for stock price prediction",
        "features": [
            "Comprehensive market data gathering (5 years of OHLCV + technical indicators)",
            "Advanced LSTM neural networks with dropout for overfitting prevention",
            "Technical indicators: SMA, EMA, RSI, MACD, Bollinger Bands, Volume analysis",
            "Model validation with early stopping and performance metrics",
            "Price predictions with confidence intervals",
            "Comprehensive backtesting with accuracy metrics",
            "Portfolio-wide model training and management"
        ],
        "endpoints": {
            "POST /train": "Train LSTM model for a specific stock",
            "GET /train/status/{symbol}": "Check training status and results",
            "POST /predict": "Get price predictions for next N days",
            "POST /backtest": "Backtest model performance on historical data",
            "GET /models/status": "Get status of all trained models",
            "DELETE /models/{symbol}": "Delete a trained model",
            "POST /portfolio/symbols": "Get stock symbols from a portfolio",
            "POST /portfolio/bulk-train": "Train models for all stocks in a portfolio"
        },
        "technical_details": {
            "model_architecture": "3-layer LSTM with dropout (100 units each)",
            "features": "17+ technical indicators including price, volume, momentum, and volatility",
            "data_period": "5 years of historical data for robust training",
            "lookback_window": "60 days of historical data for each prediction",
            "validation_split": "80% training, 20% validation",
            "early_stopping": "Patience of 10 epochs to prevent overfitting"
        },
        "usage_tips": [
            "Start with training models for your portfolio stocks",
            "Use backtesting to evaluate model performance before making predictions",
            "Monitor model accuracy and retrain periodically with new data",
            "Consider market conditions when interpreting predictions",
            "Use confidence intervals to understand prediction uncertainty"
        ]
    }
