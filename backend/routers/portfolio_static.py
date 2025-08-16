from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from pymongo.errors import DuplicateKeyError
from bson import ObjectId
from datetime import datetime

from database import get_collection
from models import (
    PortfolioStaticModel, 
    PortfolioStaticCreateRequest, 
    PortfolioStaticUpdateRequest
)

router = APIRouter(prefix="/portfolios/static", tags=["Portfolio Static Data"])

@router.get("/", response_model=List[PortfolioStaticModel])
async def get_all_portfolios(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None, description="Search by portfolio name or owner")
):
    """Get all static portfolio definitions"""
    collection = get_collection("portfolio_static")
    
    # Build query filter
    query = {}
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"owner": {"$regex": search, "$options": "i"}}
        ]
    
    cursor = collection.find(query).skip(skip).limit(limit).sort("created_at", -1)
    portfolios = []
    
    async for portfolio in cursor:
        portfolio["_id"] = str(portfolio["_id"])
        portfolios.append(PortfolioStaticModel(**portfolio))
    
    return portfolios

@router.get("/{portfolio_id}", response_model=PortfolioStaticModel)
async def get_portfolio(portfolio_id: str):
    """Get a specific portfolio by ID"""
    if not ObjectId.is_valid(portfolio_id):
        raise HTTPException(status_code=400, detail="Invalid portfolio ID")
    
    collection = get_collection("portfolio_static")
    portfolio = await collection.find_one({"_id": ObjectId(portfolio_id)})
    
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    portfolio["_id"] = str(portfolio["_id"])
    return PortfolioStaticModel(**portfolio)

@router.post("/", response_model=PortfolioStaticModel)
async def create_portfolio(portfolio_data: PortfolioStaticCreateRequest):
    """Create a new static portfolio definition"""
    collection = get_collection("portfolio_static")
    
    # Check if portfolio with same name already exists
    existing = await collection.find_one({"name": portfolio_data.name})
    if existing:
        raise HTTPException(
            status_code=400, 
            detail=f"Portfolio with name '{portfolio_data.name}' already exists"
        )
    
    # Create new portfolio document
    now = datetime.utcnow()
    portfolio_doc = {
        "name": portfolio_data.name,
        "owner": portfolio_data.owner,
        "description": portfolio_data.description,
        "created_at": now,
        "updated_at": now
    }
    
    try:
        result = await collection.insert_one(portfolio_doc)
        portfolio_doc["_id"] = str(result.inserted_id)
        return PortfolioStaticModel(**portfolio_doc)
    except DuplicateKeyError:
        raise HTTPException(
            status_code=400, 
            detail="Portfolio with this name already exists"
        )

@router.put("/{portfolio_id}", response_model=PortfolioStaticModel)
async def update_portfolio(portfolio_id: str, portfolio_data: PortfolioStaticUpdateRequest):
    """Update a portfolio definition"""
    if not ObjectId.is_valid(portfolio_id):
        raise HTTPException(status_code=400, detail="Invalid portfolio ID")
    
    collection = get_collection("portfolio_static")
    
    # Check if portfolio exists
    existing = await collection.find_one({"_id": ObjectId(portfolio_id)})
    if not existing:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    # Check if new name conflicts with existing portfolio (if name is being changed)
    if portfolio_data.name and portfolio_data.name != existing["name"]:
        name_conflict = await collection.find_one({
            "name": portfolio_data.name,
            "_id": {"$ne": ObjectId(portfolio_id)}
        })
        if name_conflict:
            raise HTTPException(
                status_code=400, 
                detail=f"Portfolio with name '{portfolio_data.name}' already exists"
            )
    
    # Build update document
    update_doc = {"updated_at": datetime.utcnow()}
    if portfolio_data.name is not None:
        update_doc["name"] = portfolio_data.name
    if portfolio_data.owner is not None:
        update_doc["owner"] = portfolio_data.owner
    if portfolio_data.description is not None:
        update_doc["description"] = portfolio_data.description
    
    # Update the document
    result = await collection.update_one(
        {"_id": ObjectId(portfolio_id)},
        {"$set": update_doc}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    # Return updated portfolio
    updated_portfolio = await collection.find_one({"_id": ObjectId(portfolio_id)})
    updated_portfolio["_id"] = str(updated_portfolio["_id"])
    return PortfolioStaticModel(**updated_portfolio)

@router.delete("/{portfolio_id}")
async def delete_portfolio(portfolio_id: str):
    """Delete a portfolio definition"""
    if not ObjectId.is_valid(portfolio_id):
        raise HTTPException(status_code=400, detail="Invalid portfolio ID")
    
    collection = get_collection("portfolio_static")
    
    # Check if portfolio exists
    existing = await collection.find_one({"_id": ObjectId(portfolio_id)})
    if not existing:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    # Delete the portfolio
    result = await collection.delete_one({"_id": ObjectId(portfolio_id)})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    return {"message": "Portfolio deleted successfully"}

@router.get("/name/{portfolio_name}", response_model=PortfolioStaticModel)
async def get_portfolio_by_name(portfolio_name: str):
    """Get a portfolio by name"""
    collection = get_collection("portfolio_static")
    portfolio = await collection.find_one({"name": portfolio_name})
    
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    portfolio["_id"] = str(portfolio["_id"])
    return PortfolioStaticModel(**portfolio)
