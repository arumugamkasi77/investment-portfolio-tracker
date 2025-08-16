from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict
from pydantic import BaseModel

from services.market_data import market_data_service

router = APIRouter(prefix="/market-data", tags=["Market Data"])

class PriceResponse(BaseModel):
    symbol: str
    price: float
    change: float
    change_percent: str
    volume: int
    last_updated: str
    source: str
    market_cap: Optional[int] = None
    currency: str = "USD"

class MultiplePricesResponse(BaseModel):
    prices: Dict[str, Optional[PriceResponse]]
    success_count: int
    total_requested: int

@router.get("/price/{symbol}", response_model=Optional[PriceResponse])
async def get_stock_price(symbol: str):
    """Get current price for a single stock symbol"""
    try:
        price_data = await market_data_service.get_stock_price(symbol.upper())
        if price_data:
            return PriceResponse(**price_data)
        else:
            raise HTTPException(
                status_code=404, 
                detail=f"Price data not found for symbol: {symbol}"
            )
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error fetching price data: {str(e)}"
        )

@router.post("/prices", response_model=MultiplePricesResponse)
async def get_multiple_stock_prices(symbols: List[str]):
    """Get current prices for multiple stock symbols"""
    try:
        if not symbols:
            raise HTTPException(status_code=400, detail="No symbols provided")
        
        if len(symbols) > 50:  # Limit to prevent abuse
            raise HTTPException(status_code=400, detail="Too many symbols (max 50)")
        
        price_data = await market_data_service.get_multiple_prices(symbols)
        
        # Convert to response format
        prices = {}
        success_count = 0
        
        for symbol, data in price_data.items():
            if data:
                prices[symbol] = PriceResponse(**data)
                success_count += 1
            else:
                prices[symbol] = None
        
        return MultiplePricesResponse(
            prices=prices,
            success_count=success_count,
            total_requested=len(symbols)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error fetching multiple prices: {str(e)}"
        )

@router.get("/cache-info")
async def get_cache_info():
    """Get information about the price data cache"""
    return market_data_service.get_cache_info()

@router.post("/refresh-price/{symbol}")
async def refresh_stock_price(symbol: str):
    """Force refresh price data for a symbol (bypass cache)"""
    try:
        # Clear cache for this symbol
        symbol = symbol.upper()
        if symbol in market_data_service.cache:
            del market_data_service.cache[symbol]
        
        # Fetch fresh data
        price_data = await market_data_service.get_stock_price(symbol)
        if price_data:
            return PriceResponse(**price_data)
        else:
            raise HTTPException(
                status_code=404, 
                detail=f"Price data not found for symbol: {symbol}"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error refreshing price data: {str(e)}"
        )
