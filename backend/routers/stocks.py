from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from pymongo.errors import DuplicateKeyError
from bson import ObjectId
from datetime import datetime

from database import get_collection
from models import StockModel, StockCreateRequest, StockUpdateRequest

router = APIRouter(prefix="/stocks", tags=["Stock Management"])

@router.get("/", response_model=List[StockModel])
async def get_all_stocks(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None, description="Search by symbol or company name"),
    sector: Optional[str] = Query(None, description="Filter by sector"),
    industry: Optional[str] = Query(None, description="Filter by industry"),
    exchange: Optional[str] = Query(None, description="Filter by exchange")
):
    """Get all stock definitions with optional filtering"""
    collection = get_collection("stocks")
    
    # Build query filter
    query = {}
    if search:
        query["$or"] = [
            {"symbol": {"$regex": search, "$options": "i"}},
            {"company_name": {"$regex": search, "$options": "i"}}
        ]
    if sector:
        query["sector"] = {"$regex": sector, "$options": "i"}
    if industry:
        query["industry"] = {"$regex": industry, "$options": "i"}
    if exchange:
        query["exchange"] = {"$regex": exchange, "$options": "i"}
    
    cursor = collection.find(query).skip(skip).limit(limit).sort("symbol", 1)
    stocks = []
    
    async for stock in cursor:
        stock["_id"] = str(stock["_id"])
        stocks.append(StockModel(**stock))
    
    return stocks

@router.get("/{stock_id}", response_model=StockModel)
async def get_stock(stock_id: str):
    """Get a specific stock by ID"""
    if not ObjectId.is_valid(stock_id):
        raise HTTPException(status_code=400, detail="Invalid stock ID")
    
    collection = get_collection("stocks")
    stock = await collection.find_one({"_id": ObjectId(stock_id)})
    
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    
    stock["_id"] = str(stock["_id"])
    return StockModel(**stock)

@router.get("/symbol/{symbol}", response_model=StockModel)
async def get_stock_by_symbol(symbol: str):
    """Get a stock by symbol"""
    collection = get_collection("stocks")
    stock = await collection.find_one({"symbol": symbol.upper()})
    
    if not stock:
        raise HTTPException(status_code=404, detail=f"Stock with symbol '{symbol}' not found")
    
    stock["_id"] = str(stock["_id"])
    return StockModel(**stock)

@router.post("/", response_model=StockModel)
async def create_stock(stock_data: StockCreateRequest):
    """Create a new stock definition"""
    collection = get_collection("stocks")
    
    # Normalize symbol to uppercase
    symbol = stock_data.symbol.upper()
    
    # Check if stock with same symbol already exists
    existing = await collection.find_one({"symbol": symbol})
    if existing:
        raise HTTPException(
            status_code=400, 
            detail=f"Stock with symbol '{symbol}' already exists"
        )
    
    # Create new stock document
    now = datetime.utcnow()
    stock_doc = {
        "symbol": symbol,
        "company_name": stock_data.company_name,
        "industry": stock_data.industry,
        "sector": stock_data.sector,
        "exchange": stock_data.exchange,
        "country": stock_data.country.upper(),
        "currency": stock_data.currency.upper(),
        "market_cap": stock_data.market_cap,
        "description": stock_data.description,
        "website": stock_data.website,
        "created_at": now,
        "updated_at": now
    }
    
    try:
        result = await collection.insert_one(stock_doc)
        stock_doc["_id"] = str(result.inserted_id)
        return StockModel(**stock_doc)
    except DuplicateKeyError:
        raise HTTPException(
            status_code=400, 
            detail=f"Stock with symbol '{symbol}' already exists"
        )

@router.put("/{stock_id}", response_model=StockModel)
async def update_stock(stock_id: str, stock_data: StockUpdateRequest):
    """Update a stock definition"""
    if not ObjectId.is_valid(stock_id):
        raise HTTPException(status_code=400, detail="Invalid stock ID")
    
    collection = get_collection("stocks")
    
    # Check if stock exists
    existing = await collection.find_one({"_id": ObjectId(stock_id)})
    if not existing:
        raise HTTPException(status_code=404, detail="Stock not found")
    
    # Check if new symbol conflicts with existing stock (if symbol is being changed)
    if stock_data.symbol:
        new_symbol = stock_data.symbol.upper()
        if new_symbol != existing["symbol"]:
            symbol_conflict = await collection.find_one({
                "symbol": new_symbol,
                "_id": {"$ne": ObjectId(stock_id)}
            })
            if symbol_conflict:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Stock with symbol '{new_symbol}' already exists"
                )
    
    # Build update document
    update_doc = {"updated_at": datetime.utcnow()}
    
    if stock_data.symbol is not None:
        update_doc["symbol"] = stock_data.symbol.upper()
    if stock_data.company_name is not None:
        update_doc["company_name"] = stock_data.company_name
    if stock_data.industry is not None:
        update_doc["industry"] = stock_data.industry
    if stock_data.sector is not None:
        update_doc["sector"] = stock_data.sector
    if stock_data.exchange is not None:
        update_doc["exchange"] = stock_data.exchange
    if stock_data.country is not None:
        update_doc["country"] = stock_data.country.upper()
    if stock_data.currency is not None:
        update_doc["currency"] = stock_data.currency.upper()
    if stock_data.market_cap is not None:
        update_doc["market_cap"] = stock_data.market_cap
    if stock_data.description is not None:
        update_doc["description"] = stock_data.description
    if stock_data.website is not None:
        update_doc["website"] = stock_data.website
    
    # Update the document
    result = await collection.update_one(
        {"_id": ObjectId(stock_id)},
        {"$set": update_doc}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Stock not found")
    
    # Return updated stock
    updated_stock = await collection.find_one({"_id": ObjectId(stock_id)})
    updated_stock["_id"] = str(updated_stock["_id"])
    return StockModel(**updated_stock)

@router.delete("/{stock_id}")
async def delete_stock(stock_id: str):
    """Delete a stock definition"""
    if not ObjectId.is_valid(stock_id):
        raise HTTPException(status_code=400, detail="Invalid stock ID")
    
    collection = get_collection("stocks")
    
    # Check if stock exists
    existing = await collection.find_one({"_id": ObjectId(stock_id)})
    if not existing:
        raise HTTPException(status_code=404, detail="Stock not found")
    
    # TODO: Check if stock is referenced in trades or options before deletion
    # For now, we'll allow deletion
    
    # Delete the stock
    result = await collection.delete_one({"_id": ObjectId(stock_id)})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Stock not found")
    
    return {"message": "Stock deleted successfully"}

@router.get("/sectors/list")
async def get_sectors():
    """Get list of unique sectors"""
    collection = get_collection("stocks")
    sectors = await collection.distinct("sector")
    return {"sectors": sorted(sectors)}

@router.get("/industries/list")
async def get_industries():
    """Get list of unique industries"""
    collection = get_collection("stocks")
    industries = await collection.distinct("industry")
    return {"industries": sorted(industries)}

@router.get("/exchanges/list")
async def get_exchanges():
    """Get list of unique exchanges"""
    collection = get_collection("stocks")
    exchanges = await collection.distinct("exchange")
    return {"exchanges": sorted(exchanges)}
