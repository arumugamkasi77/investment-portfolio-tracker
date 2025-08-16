from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from pymongo.errors import DuplicateKeyError
from bson import ObjectId
from datetime import datetime, date
import json

from database import get_collection
from models import OptionModel, OptionCreateRequest, OptionUpdateRequest

router = APIRouter(prefix="/options", tags=["Options Management"])

def generate_option_symbol(underlying: str, expiration: date, option_type: str, strike: float) -> str:
    """Generate standard option symbol: UNDERLYING + YYMMDD + C/P + 00000000"""
    exp_str = expiration.strftime("%y%m%d")
    type_code = "C" if option_type == "CALL" else "P"
    # Strike price * 1000, padded to 8 digits
    strike_str = f"{int(strike * 1000):08d}"
    return f"{underlying.upper()}{exp_str}{type_code}{strike_str}"

@router.get("/", response_model=List[OptionModel])
async def get_all_options(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    underlying_symbol: Optional[str] = Query(None, description="Filter by underlying symbol"),
    option_type: Optional[str] = Query(None, description="Filter by option type (CALL/PUT)"),
    exchange: Optional[str] = Query(None, description="Filter by exchange"),
    expired: Optional[bool] = Query(None, description="Filter by expiration status"),
    search: Optional[str] = Query(None, description="Search by underlying symbol or option symbol")
):
    """Get all option definitions with optional filtering"""
    collection = get_collection("options")
    
    # Build query filter
    query = {}
    if underlying_symbol:
        query["underlying_symbol"] = underlying_symbol.upper()
    if option_type:
        query["option_type"] = option_type.upper()
    if exchange:
        query["exchange"] = {"$regex": exchange, "$options": "i"}
    if expired is not None:
        today = date.today()
        if expired:
            query["expiration_date"] = {"$lt": today}
        else:
            query["expiration_date"] = {"$gte": today}
    if search:
        query["$or"] = [
            {"underlying_symbol": {"$regex": search, "$options": "i"}},
            {"option_symbol": {"$regex": search, "$options": "i"}}
        ]
    
    cursor = collection.find(query).skip(skip).limit(limit).sort([
        ("underlying_symbol", 1), 
        ("expiration_date", 1), 
        ("option_type", 1), 
        ("strike_price", 1)
    ])
    options = []
    
    async for option in cursor:
        option["_id"] = str(option["_id"])
        options.append(OptionModel(**option))
    
    return options

@router.get("/{option_id}", response_model=OptionModel)
async def get_option(option_id: str):
    """Get a specific option by ID"""
    if not ObjectId.is_valid(option_id):
        raise HTTPException(status_code=400, detail="Invalid option ID")
    
    collection = get_collection("options")
    option = await collection.find_one({"_id": ObjectId(option_id)})
    
    if not option:
        raise HTTPException(status_code=404, detail="Option not found")
    
    option["_id"] = str(option["_id"])
    return OptionModel(**option)

@router.get("/underlying/{symbol}", response_model=List[OptionModel])
async def get_options_by_underlying(
    symbol: str,
    option_type: Optional[str] = Query(None, description="Filter by option type"),
    expired: Optional[bool] = Query(False, description="Include expired options")
):
    """Get all options for a specific underlying symbol"""
    collection = get_collection("options")
    
    query = {"underlying_symbol": symbol.upper()}
    if option_type:
        query["option_type"] = option_type.upper()
    if not expired:
        query["expiration_date"] = {"$gte": date.today()}
    
    cursor = collection.find(query).sort([
        ("expiration_date", 1), 
        ("option_type", 1), 
        ("strike_price", 1)
    ])
    options = []
    
    async for option in cursor:
        option["_id"] = str(option["_id"])
        options.append(OptionModel(**option))
    
    return options

@router.post("/", response_model=OptionModel)
async def create_option(option_data: OptionCreateRequest):
    """Create a new option definition"""
    collection = get_collection("options")
    
    # Normalize data
    underlying = option_data.underlying_symbol.upper()
    option_type = option_data.option_type.upper()
    
    # Generate option symbol if not provided
    option_symbol = option_data.option_symbol
    if not option_symbol:
        option_symbol = generate_option_symbol(
            underlying, 
            option_data.expiration_date, 
            option_type, 
            option_data.strike_price
        )
    else:
        option_symbol = option_symbol.upper()
    
    # Convert string date to datetime for MongoDB compatibility
    try:
        expiration_date = datetime.strptime(option_data.expiration_date, "%Y-%m-%d").date()
        expiration_datetime = datetime.combine(expiration_date, datetime.min.time())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid expiration date format. Use YYYY-MM-DD"
        )
    
    # Check if option with same characteristics already exists
    existing = await collection.find_one({
        "underlying_symbol": underlying,
        "option_type": option_type,
        "strike_price": option_data.strike_price,
        "expiration_date": expiration_datetime
    })
    if existing:
        raise HTTPException(
            status_code=400, 
            detail=f"Option with same characteristics already exists for {underlying}"
        )
    
    # Create new option document
    now = datetime.now()
    
    option_doc = {
        "underlying_symbol": underlying,
        "option_symbol": option_symbol,
        "option_type": option_type,
        "strike_price": option_data.strike_price,
        "expiration_date": expiration_datetime,
        "contract_size": option_data.contract_size,
        "exchange": option_data.exchange,
        "currency": option_data.currency.upper(),
        "description": option_data.description,
        "created_at": now,
        "updated_at": now
    }
    
    try:
        result = await collection.insert_one(option_doc)
        option_doc["_id"] = str(result.inserted_id)
        return OptionModel(**option_doc)
    except DuplicateKeyError:
        raise HTTPException(
            status_code=400, 
            detail="Option with these characteristics already exists"
        )
    except Exception as e:
        print(f"Error creating option: {str(e)}")
        print(f"Option doc: {option_doc}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error creating option: {str(e)}"
        )

@router.put("/{option_id}", response_model=OptionModel)
async def update_option(option_id: str, option_data: OptionUpdateRequest):
    """Update an option definition"""
    if not ObjectId.is_valid(option_id):
        raise HTTPException(status_code=400, detail="Invalid option ID")
    
    collection = get_collection("options")
    
    # Check if option exists
    existing = await collection.find_one({"_id": ObjectId(option_id)})
    if not existing:
        raise HTTPException(status_code=404, detail="Option not found")
    
    # Build update document
    update_doc = {"updated_at": datetime.now()}
    
    if option_data.underlying_symbol is not None:
        update_doc["underlying_symbol"] = option_data.underlying_symbol.upper()
    if option_data.option_symbol is not None:
        update_doc["option_symbol"] = option_data.option_symbol.upper()
    if option_data.option_type is not None:
        update_doc["option_type"] = option_data.option_type.upper()
    if option_data.strike_price is not None:
        update_doc["strike_price"] = option_data.strike_price
    if option_data.expiration_date is not None:
        try:
            expiration_date = datetime.strptime(option_data.expiration_date, "%Y-%m-%d").date()
            expiration_datetime = datetime.combine(expiration_date, datetime.min.time())
            update_doc["expiration_date"] = expiration_datetime
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid expiration date format. Use YYYY-MM-DD"
            )
    if option_data.contract_size is not None:
        update_doc["contract_size"] = option_data.contract_size
    if option_data.exchange is not None:
        update_doc["exchange"] = option_data.exchange
    if option_data.currency is not None:
        update_doc["currency"] = option_data.currency.upper()
    if option_data.description is not None:
        update_doc["description"] = option_data.description
    
    # Check for conflicts if key fields are being changed
    if any(field in update_doc for field in ["underlying_symbol", "option_type", "strike_price", "expiration_date"]):
        conflict_query = {
            "underlying_symbol": update_doc.get("underlying_symbol", existing["underlying_symbol"]),
            "option_type": update_doc.get("option_type", existing["option_type"]),
            "strike_price": update_doc.get("strike_price", existing["strike_price"]),
            "expiration_date": update_doc.get("expiration_date", existing["expiration_date"]),
            "_id": {"$ne": ObjectId(option_id)}
        }
        
        conflict = await collection.find_one(conflict_query)
        if conflict:
            raise HTTPException(
                status_code=400, 
                detail="Option with these characteristics already exists"
            )
    
    # Update the document
    result = await collection.update_one(
        {"_id": ObjectId(option_id)},
        {"$set": update_doc}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Option not found")
    
    # Return updated option
    updated_option = await collection.find_one({"_id": ObjectId(option_id)})
    updated_option["_id"] = str(updated_option["_id"])
    return OptionModel(**updated_option)

@router.delete("/{option_id}")
async def delete_option(option_id: str):
    """Delete an option definition"""
    if not ObjectId.is_valid(option_id):
        raise HTTPException(status_code=400, detail="Invalid option ID")
    
    collection = get_collection("options")
    
    # Check if option exists
    existing = await collection.find_one({"_id": ObjectId(option_id)})
    if not existing:
        raise HTTPException(status_code=404, detail="Option not found")
    
    # TODO: Check if option is referenced in trades before deletion
    # For now, we'll allow deletion
    
    # Delete the option
    result = await collection.delete_one({"_id": ObjectId(option_id)})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Option not found")
    
    return {"message": "Option deleted successfully"}

@router.get("/underlyings/list")
async def get_underlying_symbols():
    """Get list of unique underlying symbols"""
    collection = get_collection("options")
    underlyings = await collection.distinct("underlying_symbol")
    return {"underlyings": sorted(underlyings)}

@router.get("/exchanges/list")
async def get_option_exchanges():
    """Get list of unique option exchanges"""
    collection = get_collection("options")
    exchanges = await collection.distinct("exchange")
    return {"exchanges": sorted(exchanges)}

@router.post("/generate-symbol")
async def generate_option_symbol_endpoint(
    underlying_symbol: str,
    expiration_date: date,
    option_type: str,
    strike_price: float
):
    """Generate a standard option symbol"""
    try:
        symbol = generate_option_symbol(underlying_symbol, expiration_date, option_type, strike_price)
        return {"option_symbol": symbol}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error generating symbol: {str(e)}")
