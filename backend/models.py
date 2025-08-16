from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime, date
from decimal import Decimal

class TradeModel(BaseModel):
    """Model for individual trade records"""
    id: Optional[str] = Field(None, alias="_id")
    portfolio_name: str = Field(..., description="Name of the portfolio")
    symbol: str = Field(..., description="Stock or Listed Option symbol")
    instrument_type: Literal["STOCK", "OPTION"] = Field(..., description="Type of instrument")
    quantity: int = Field(..., description="Number of shares/contracts")
    trade_type: Literal["BUY", "SELL"] = Field(..., description="Buy or Sell transaction")
    executed_price: float = Field(..., description="Price per share/contract")
    brokerage: float = Field(0.0, description="Brokerage fees")
    remarks: Optional[str] = Field(None, description="Optional remarks")
    trade_date: datetime = Field(default_factory=datetime.now, description="Trade execution date")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "portfolio_name": "Growth Portfolio",
                "symbol": "AAPL",
                "instrument_type": "STOCK",
                "quantity": 100,
                "trade_type": "BUY",
                "executed_price": 150.50,
                "brokerage": 5.00,
                "remarks": "Adding tech exposure"
            }
        }

class PortfolioModel(BaseModel):
    """Model for portfolio configurations"""
    id: Optional[str] = Field(None, alias="_id")
    portfolio_name: str = Field(..., description="Unique portfolio name")
    description: Optional[str] = Field(None, description="Portfolio description")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        populate_by_name = True

class MarketDataModel(BaseModel):
    """Model for current market prices"""
    id: Optional[str] = Field(None, alias="_id")
    symbol: str = Field(..., description="Stock or Option symbol")
    current_price: float = Field(..., description="Current market price")
    last_updated: datetime = Field(default_factory=datetime.now)
    
    class Config:
        populate_by_name = True

class DailySnapshotModel(BaseModel):
    """Model for daily P&L snapshots"""
    id: Optional[str] = Field(None, alias="_id")
    portfolio_name: str = Field(..., description="Portfolio name")
    symbol: str = Field(..., description="Symbol")
    snapshot_date: date = Field(..., description="Snapshot date")
    position_quantity: int = Field(..., description="Net position quantity")
    average_cost: float = Field(..., description="Average cost basis")
    market_price: float = Field(..., description="Market price on snapshot date")
    market_value: float = Field(..., description="Total market value")
    unrealized_pl: float = Field(..., description="Unrealized P&L")
    realized_pl: float = Field(..., description="Realized P&L to date")
    inception_pl: float = Field(..., description="Inception P&L (total P&L from inception)")
    total_pl: float = Field(..., description="Total P&L (realized + unrealized)")
    created_at: datetime = Field(default_factory=datetime.now)

    class Config:
        populate_by_name = True

class PortfolioSummaryModel(BaseModel):
    """Model for portfolio summary response"""
    portfolio_name: str
    symbol: str
    instrument_type: str
    position_quantity: int
    average_cost: float
    current_price: float
    market_value: float
    total_cost: float
    unrealized_pl: float
    unrealized_pl_percent: float
    dtd_pl: float = 0.0
    mtd_pl: float = 0.0
    ytd_pl: float = 0.0

class TradeCreateRequest(BaseModel):
    """Request model for creating trades"""
    portfolio_name: str
    symbol: str
    instrument_type: Literal["STOCK", "OPTION"]
    quantity: int
    trade_type: Literal["BUY", "SELL"]
    executed_price: float
    brokerage: float = 0.0
    remarks: Optional[str] = None
    trade_date: Optional[datetime] = None

class TradeUpdateRequest(BaseModel):
    """Request model for updating trades"""
    portfolio_name: Optional[str] = None
    symbol: Optional[str] = None
    instrument_type: Optional[Literal["STOCK", "OPTION"]] = None
    quantity: Optional[int] = None
    trade_type: Optional[Literal["BUY", "SELL"]] = None
    executed_price: Optional[float] = None
    brokerage: Optional[float] = None
    remarks: Optional[str] = None
    trade_date: Optional[datetime] = None

# Static Data Models

class PortfolioStaticModel(BaseModel):
    """Model for static portfolio definitions"""
    id: Optional[str] = Field(None, alias="_id")
    name: str = Field(..., description="Portfolio name", min_length=1, max_length=100)
    owner: str = Field(..., description="Portfolio owner", min_length=1, max_length=100)
    description: Optional[str] = Field(None, description="Portfolio description", max_length=500)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "name": "Growth Portfolio",
                "owner": "John Doe",
                "description": "Long-term growth focused portfolio"
            }
        }

class PortfolioStaticCreateRequest(BaseModel):
    """Request model for creating static portfolios"""
    name: str = Field(..., min_length=1, max_length=100)
    owner: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)

class PortfolioStaticUpdateRequest(BaseModel):
    """Request model for updating static portfolios"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    owner: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)

class StockModel(BaseModel):
    """Model for stock definitions"""
    id: Optional[str] = Field(None, alias="_id")
    symbol: str = Field(..., description="Stock symbol", min_length=1, max_length=10)
    company_name: str = Field(..., description="Company name", min_length=1, max_length=200)
    industry: str = Field(..., description="Industry", min_length=1, max_length=100)
    sector: str = Field(..., description="Sector", min_length=1, max_length=100)
    exchange: str = Field(..., description="Exchange", min_length=1, max_length=50)
    country: str = Field(..., description="Country code", min_length=2, max_length=3)
    currency: str = Field(..., description="Currency code", min_length=3, max_length=3)
    market_cap: Optional[float] = Field(None, description="Market capitalization", ge=0)
    description: Optional[str] = Field(None, description="Company description", max_length=1000)
    website: Optional[str] = Field(None, description="Company website", max_length=200)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "symbol": "AAPL",
                "company_name": "Apple Inc.",
                "industry": "Technology",
                "sector": "Consumer Electronics",
                "exchange": "NASDAQ",
                "country": "US",
                "currency": "USD",
                "market_cap": 3000000000000,
                "description": "Apple Inc. designs, manufactures, and markets smartphones, personal computers, tablets, wearables, and accessories worldwide.",
                "website": "https://www.apple.com"
            }
        }

class StockCreateRequest(BaseModel):
    """Request model for creating stocks"""
    symbol: str = Field(..., min_length=1, max_length=10)
    company_name: str = Field(..., min_length=1, max_length=200)
    industry: str = Field(..., min_length=1, max_length=100)
    sector: str = Field(..., min_length=1, max_length=100)
    exchange: str = Field(..., min_length=1, max_length=50)
    country: str = Field(..., min_length=2, max_length=3)
    currency: str = Field(..., min_length=3, max_length=3)
    market_cap: Optional[float] = Field(None, ge=0)
    description: Optional[str] = Field(None, max_length=1000)
    website: Optional[str] = Field(None, max_length=200)

class StockUpdateRequest(BaseModel):
    """Request model for updating stocks"""
    symbol: Optional[str] = Field(None, min_length=1, max_length=10)
    company_name: Optional[str] = Field(None, min_length=1, max_length=200)
    industry: Optional[str] = Field(None, min_length=1, max_length=100)
    sector: Optional[str] = Field(None, min_length=1, max_length=100)
    exchange: Optional[str] = Field(None, min_length=1, max_length=50)
    country: Optional[str] = Field(None, min_length=2, max_length=3)
    currency: Optional[str] = Field(None, min_length=3, max_length=3)
    market_cap: Optional[float] = Field(None, ge=0)
    description: Optional[str] = Field(None, max_length=1000)
    website: Optional[str] = Field(None, max_length=200)

class OptionModel(BaseModel):
    """Model for listed stock options"""
    id: Optional[str] = Field(None, alias="_id")
    underlying_symbol: str = Field(..., description="Underlying stock symbol", min_length=1, max_length=10)
    option_symbol: Optional[str] = Field(None, description="Option symbol (auto-generated if not provided)", max_length=50)
    option_type: Literal["CALL", "PUT"] = Field(..., description="Option type")
    strike_price: float = Field(..., description="Strike price", gt=0)
    expiration_date: date = Field(..., description="Expiration date")
    contract_size: int = Field(100, description="Contract size (shares per contract)", gt=0)
    exchange: str = Field(..., description="Exchange", min_length=1, max_length=50)
    currency: str = Field(..., description="Currency code", min_length=3, max_length=3)
    description: Optional[str] = Field(None, description="Option description", max_length=500)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "underlying_symbol": "AAPL",
                "option_type": "CALL",
                "strike_price": 150.0,
                "expiration_date": "2024-01-19",
                "contract_size": 100,
                "exchange": "CBOE",
                "currency": "USD",
                "description": "Apple call option"
            }
        }

class OptionCreateRequest(BaseModel):
    """Request model for creating options"""
    underlying_symbol: str = Field(..., min_length=1, max_length=10)
    option_symbol: Optional[str] = Field(None, max_length=50)
    option_type: Literal["CALL", "PUT"] = Field(...)
    strike_price: float = Field(..., gt=0)
    expiration_date: str = Field(..., description="Expiration date in YYYY-MM-DD format")
    contract_size: int = Field(100, gt=0)
    exchange: str = Field(..., min_length=1, max_length=50)
    currency: str = Field(..., min_length=3, max_length=3)
    description: Optional[str] = Field(None, max_length=500)

class OptionUpdateRequest(BaseModel):
    """Request model for updating options"""
    underlying_symbol: Optional[str] = Field(None, min_length=1, max_length=10)
    option_symbol: Optional[str] = Field(None, max_length=50)
    option_type: Optional[Literal["CALL", "PUT"]] = Field(None)
    strike_price: Optional[float] = Field(None, gt=0)
    expiration_date: Optional[str] = Field(None, description="Expiration date in YYYY-MM-DD format")
    contract_size: Optional[int] = Field(None, gt=0)
    exchange: Optional[str] = Field(None, min_length=1, max_length=50)
    currency: Optional[str] = Field(None, min_length=3, max_length=3)
    description: Optional[str] = Field(None, max_length=500)
