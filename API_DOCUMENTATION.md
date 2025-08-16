# API Documentation

## 🔌 Overview

The Investment Portfolio Tracker API provides RESTful endpoints for managing investment portfolios, trades, and market data. All endpoints return JSON responses and use standard HTTP status codes.

**Base URL**: `http://localhost:8000` (Development)

## 📋 Authentication

Currently, the API operates without authentication. In production, consider implementing JWT tokens or API keys.

## 📊 Response Format

### **Success Response**
```json
{
  "data": {},           // Main response data
  "message": "Success", // Success message
  "status": "success",  // Status indicator
  "timestamp": "2025-08-16T10:30:00Z"
}
```

### **Error Response**
```json
{
  "detail": "Error description",
  "status_code": 400,
  "timestamp": "2025-08-16T10:30:00Z"
}
```

## 🎯 Portfolio Management

### **Get All Portfolios**
```http
GET /portfolios/
```

**Response:**
```json
{
  "data": [
    {
      "portfolio_name": "Growth Portfolio",
      "total_market_value": 125000.00,
      "total_pl": 15000.00,
      "total_pl_percent": 13.64
    },
    {
      "portfolio_name": "Conservative Portfolio",
      "total_market_value": 75000.00,
      "total_pl": 5000.00,
      "total_pl_percent": 7.14
    }
  ],
  "message": "Portfolios retrieved successfully",
  "status": "success",
  "timestamp": "2025-08-16T10:30:00Z"
}
```

### **Get Portfolio Positions**
```http
GET /portfolios/{portfolio_name}/positions
```

**Parameters:**
- `portfolio_name` (path): Name of the portfolio

**Response:**
```json
{
  "data": [
    {
      "portfolio_name": "Growth Portfolio",
      "symbol": "AAPL",
      "instrument_type": "STOCK",
      "position_quantity": 100,
      "average_cost": 145.50,
      "current_price": 150.00,
      "market_value": 15000.00,
      "total_cost": 14550.00,
      "net_cost": 14550.00,
      "unrealized_pl": 450.00,
      "unrealized_pl_percent": 3.09,
      "inception_pl": 450.00,
      "dtd_pl": 0.0,
      "mtd_pl": 0.0,
      "ytd_pl": 0.0
    }
  ],
  "message": "Portfolio positions retrieved successfully",
  "status": "success",
  "timestamp": "2025-08-16T10:30:00Z"
}
```

### **Get Portfolio Performance**
```http
GET /portfolios/{portfolio_name}/performance
```

**Parameters:**
- `portfolio_name` (path): Name of the portfolio

**Response:**
```json
{
  "data": {
    "portfolio_name": "Growth Portfolio",
    "total_market_value": 125000.00,
    "total_cost": 110000.00,
    "total_pl": 15000.00,
    "total_pl_percent": 13.64,
    "unrealized_pl": 15000.00,
    "realized_pl": 0.00,
    "inception_pl": 15000.00
  },
  "message": "Portfolio performance retrieved successfully",
  "status": "success",
  "timestamp": "2025-08-16T10:30:00Z"
}
```

### **Update Market Price**
```http
POST /portfolios/{portfolio_name}/market-price/{symbol}
```

**Parameters:**
- `portfolio_name` (path): Name of the portfolio
- `symbol` (path): Stock/option symbol

**Request Body:**
```json
{
  "current_price": 155.00
}
```

**Response:**
```json
{
  "data": {
    "symbol": "AAPL",
    "current_price": 155.00,
    "updated_at": "2025-08-16T10:30:00Z"
  },
  "message": "Market price updated successfully",
  "status": "success",
  "timestamp": "2025-08-16T10:30:00Z"
}
```

## 💰 Trade Management

### **Get All Trades**
```http
GET /trades/
```

**Query Parameters:**
- `portfolio_name` (optional): Filter by portfolio
- `symbol` (optional): Filter by symbol
- `trade_type` (optional): Filter by trade type (BUY/SELL)
- `start_date` (optional): Filter trades from date (YYYY-MM-DD)
- `end_date` (optional): Filter trades to date (YYYY-MM-DD)

**Response:**
```json
{
  "data": [
    {
      "_id": "64f8a1b2c3d4e5f6a7b8c9d0",
      "portfolio_name": "Growth Portfolio",
      "symbol": "AAPL",
      "instrument_type": "STOCK",
      "quantity": 100,
      "trade_type": "BUY",
      "executed_price": 145.50,
      "brokerage": 5.00,
      "remarks": "Initial position",
      "trade_date": "2025-08-15T00:00:00Z",
      "created_at": "2025-08-15T10:30:00Z",
      "updated_at": "2025-08-15T10:30:00Z"
    }
  ],
  "message": "Trades retrieved successfully",
  "status": "success",
  "timestamp": "2025-08-16T10:30:00Z"
}
```

### **Create Trade**
```http
POST /trades/
```

**Request Body:**
```json
{
  "portfolio_name": "Growth Portfolio",
  "symbol": "MSFT",
  "instrument_type": "STOCK",
  "quantity": 50,
  "trade_type": "BUY",
  "executed_price": 300.00,
  "brokerage": 5.00,
  "remarks": "Adding to position",
  "trade_date": "2025-08-16"
}
```

**Response:**
```json
{
  "data": {
    "_id": "64f8a1b2c3d4e5f6a7b8c9d1",
    "portfolio_name": "Growth Portfolio",
    "symbol": "MSFT",
    "instrument_type": "STOCK",
    "quantity": 50,
    "trade_type": "BUY",
    "executed_price": 300.00,
    "brokerage": 5.00,
    "remarks": "Adding to position",
    "trade_date": "2025-08-16T00:00:00Z",
    "created_at": "2025-08-16T10:30:00Z",
    "updated_at": "2025-08-16T10:30:00Z"
  },
  "message": "Trade created successfully",
  "status": "success",
  "timestamp": "2025-08-16T10:30:00Z"
}
```

### **Get Trade by ID**
```http
GET /trades/{trade_id}
```

**Parameters:**
- `trade_id` (path): MongoDB ObjectId of the trade

**Response:**
```json
{
  "data": {
    "_id": "64f8a1b2c3d4e5f6a7b8c9d0",
    "portfolio_name": "Growth Portfolio",
    "symbol": "AAPL",
    "instrument_type": "STOCK",
    "quantity": 100,
    "trade_type": "BUY",
    "executed_price": 145.50,
    "brokerage": 5.00,
    "remarks": "Initial position",
    "trade_date": "2025-08-15T00:00:00Z",
    "created_at": "2025-08-15T10:30:00Z",
    "updated_at": "2025-08-15T10:30:00Z"
  },
  "message": "Trade retrieved successfully",
  "status": "success",
  "timestamp": "2025-08-16T10:30:00Z"
}
```

### **Update Trade**
```http
PUT /trades/{trade_id}
```

**Parameters:**
- `trade_id` (path): MongoDB ObjectId of the trade

**Request Body:**
```json
{
  "executed_price": 147.00,
  "remarks": "Updated price and remarks"
}
```

**Response:**
```json
{
  "data": {
    "_id": "64f8a1b2c3d4e5f6a7b8c9d0",
    "portfolio_name": "Growth Portfolio",
    "symbol": "AAPL",
    "instrument_type": "STOCK",
    "quantity": 100,
    "trade_type": "BUY",
    "executed_price": 147.00,
    "brokerage": 5.00,
    "remarks": "Updated price and remarks",
    "trade_date": "2025-08-15T00:00:00Z",
    "created_at": "2025-08-15T10:30:00Z",
    "updated_at": "2025-08-16T10:30:00Z"
  },
  "message": "Trade updated successfully",
  "status": "success",
  "timestamp": "2025-08-16T10:30:00Z"
}
```

### **Delete Trade**
```http
DELETE /trades/{trade_id}
```

**Parameters:**
- `trade_id` (path): MongoDB ObjectId of the trade

**Response:**
```json
{
  "data": null,
  "message": "Trade deleted successfully",
  "status": "success",
  "timestamp": "2025-08-16T10:30:00Z"
}
```

## 🏢 Static Data Management

### **Portfolio Definitions**

#### **Get All Portfolio Definitions**
```http
GET /portfolio-static/
```

**Response:**
```json
{
  "data": [
    {
      "_id": "64f8a1b2c3d4e5f6a7b8c9d2",
      "portfolio_name": "Growth Portfolio",
      "owner": "John Doe",
      "description": "Aggressive growth strategy",
      "created_at": "2025-08-01T00:00:00Z",
      "updated_at": "2025-08-01T00:00:00Z"
    }
  ],
  "message": "Portfolio definitions retrieved successfully",
  "status": "success",
  "timestamp": "2025-08-16T10:30:00Z"
}
```

#### **Create Portfolio Definition**
```http
POST /portfolio-static/
```

**Request Body:**
```json
{
  "portfolio_name": "Income Portfolio",
  "owner": "Jane Smith",
  "description": "Dividend-focused portfolio"
}
```

#### **Update Portfolio Definition**
```http
PUT /portfolio-static/{portfolio_id}
```

#### **Delete Portfolio Definition**
```http
DELETE /portfolio-static/{portfolio_id}
```

### **Stock Definitions**

#### **Get All Stock Definitions**
```http
GET /stocks/
```

**Response:**
```json
{
  "data": [
    {
      "_id": "64f8a1b2c3d4e5f6a7b8c9d3",
      "symbol": "AAPL",
      "company_name": "Apple Inc.",
      "industry": "Technology",
      "sector": "Consumer Electronics",
      "exchange": "NASDAQ",
      "country": "United States",
      "currency": "USD",
      "market_cap": 2500000000000,
      "description": "Technology company",
      "website": "https://www.apple.com",
      "created_at": "2025-08-01T00:00:00Z",
      "updated_at": "2025-08-01T00:00:00Z"
    }
  ],
  "message": "Stock definitions retrieved successfully",
  "status": "success",
  "timestamp": "2025-08-16T10:30:00Z"
}
```

#### **Create Stock Definition**
```http
POST /stocks/
```

**Request Body:**
```json
{
  "symbol": "MSFT",
  "company_name": "Microsoft Corporation",
  "industry": "Technology",
  "sector": "Software",
  "exchange": "NASDAQ",
  "country": "United States",
  "currency": "USD",
  "market_cap": 2000000000000,
  "description": "Software company",
  "website": "https://www.microsoft.com"
}
```

#### **Update Stock Definition**
```http
PUT /stocks/{stock_id}
```

#### **Delete Stock Definition**
```http
DELETE /stocks/{stock_id}
```

### **Option Definitions**

#### **Get All Option Definitions**
```http
GET /options/
```

**Response:**
```json
{
  "data": [
    {
      "_id": "64f8a1b2c3d4e5f6a7b8c9d4",
      "underlying_symbol": "AAPL",
      "strike_price": 150.00,
      "expiration_date": "2025-12-19T00:00:00Z",
      "option_type": "CALL",
      "contract_size": 100,
      "exchange": "CBOE",
      "currency": "USD",
      "description": "Apple 150 Call Dec 2025",
      "created_at": "2025-08-01T00:00:00Z",
      "updated_at": "2025-08-01T00:00:00Z"
    }
  ],
  "message": "Option definitions retrieved successfully",
  "status": "success",
  "timestamp": "2025-08-16T10:30:00Z"
}
```

#### **Create Option Definition**
```http
POST /options/
```

**Request Body:**
```json
{
  "underlying_symbol": "MSFT",
  "strike_price": 300.00,
  "expiration_date": "2025-12-19",
  "option_type": "PUT",
  "contract_size": 100,
  "exchange": "CBOE",
  "currency": "USD",
  "description": "Microsoft 300 Put Dec 2025"
}
```

#### **Update Option Definition**
```http
PUT /options/{option_id}
```

#### **Delete Option Definition**
```http
DELETE /options/{option_id}
```

## 📈 Market Data

### **Get Stock Price**
```http
GET /market-data/price/{symbol}
```

**Parameters:**
- `symbol` (path): Stock symbol

**Response:**
```json
{
  "data": {
    "symbol": "AAPL",
    "price": 150.00,
    "change": 2.50,
    "change_percent": "1.69%",
    "source": "yahoo_finance",
    "last_updated": "2025-08-16T10:30:00Z"
  },
  "message": "Price retrieved successfully",
  "status": "success",
  "timestamp": "2025-08-16T10:30:00Z"
}
```

### **Get Multiple Stock Prices**
```http
GET /market-data/prices
```

**Query Parameters:**
- `symbols` (required): Comma-separated list of symbols

**Example:**
```http
GET /market-data/prices?symbols=AAPL,MSFT,GOOGL
```

**Response:**
```json
{
  "data": [
    {
      "symbol": "AAPL",
      "price": 150.00,
      "change": 2.50,
      "change_percent": "1.69%",
      "source": "yahoo_finance",
      "last_updated": "2025-08-16T10:30:00Z"
    },
    {
      "symbol": "MSFT",
      "price": 300.00,
      "change": 5.00,
      "change_percent": "1.69%",
      "source": "yahoo_finance",
      "last_updated": "2025-08-16T10:30:00Z"
    }
  ],
  "message": "Prices retrieved successfully",
  "status": "success",
  "timestamp": "2025-08-16T10:30:00Z"
}
```

## 🔍 Search and Filtering

### **Search Portfolios**
```http
GET /portfolio-static/?search=growth
```

### **Filter Stocks by Industry**
```http
GET /stocks/?industry=Technology
```

### **Filter Options by Expiry**
```http
GET /options/?expiration_date=2025-12-19
```

### **Filter Trades by Date Range**
```http
GET /trades/?start_date=2025-08-01&end_date=2025-08-16
```

## 📊 Pagination

For endpoints that return large datasets, pagination is supported:

```http
GET /trades/?page=1&limit=20
```

**Response:**
```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 150,
    "pages": 8
  },
  "message": "Trades retrieved successfully",
  "status": "success",
  "timestamp": "2025-08-16T10:30:00Z"
}
```

## 🚨 Error Codes

| Status Code | Description |
|-------------|-------------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request - Invalid input |
| 404 | Not Found - Resource doesn't exist |
| 422 | Validation Error - Invalid data format |
| 500 | Internal Server Error |

## 📝 Data Types

### **Trade Types**
- `BUY`: Purchase transaction
- `SELL`: Sale transaction

### **Instrument Types**
- `STOCK`: Common stock
- `OPTION`: Stock option

### **Option Types**
- `CALL`: Call option
- `PUT`: Put option

### **Date Formats**
- **API Input**: `YYYY-MM-DD` (e.g., "2025-08-16")
- **API Output**: ISO 8601 format (e.g., "2025-08-16T10:30:00Z")

## 🔧 Testing the API

### **Using curl**
```bash
# Get all portfolios
curl http://localhost:8000/portfolios/

# Create a trade
curl -X POST http://localhost:8000/trades/ \
  -H "Content-Type: application/json" \
  -d '{
    "portfolio_name": "Test Portfolio",
    "symbol": "AAPL",
    "instrument_type": "STOCK",
    "quantity": 10,
    "trade_type": "BUY",
    "executed_price": 150.00,
    "brokerage": 5.00
  }'
```

### **Using Postman**
1. Import the API collection
2. Set base URL to `http://localhost:8000`
3. Test endpoints with sample data

### **Using Swagger UI**
Visit `http://localhost:8000/docs` for interactive API documentation.

---

**This documentation covers all available API endpoints with examples and usage instructions.**
