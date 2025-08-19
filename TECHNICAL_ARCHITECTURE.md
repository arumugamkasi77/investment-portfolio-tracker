# Technical Architecture Documentation

## 🏗️ System Overview

The Investment Portfolio Tracker is a full-stack web application built with modern technologies, designed for scalability, maintainability, and performance.

## 🔧 Technology Stack

### **Backend Stack**
- **Language**: Python 3.9+
- **Framework**: FastAPI 0.104.1
- **ASGI Server**: Uvicorn with standard extras
- **Database**: MongoDB 5.0+ with Motor async driver
- **ORM**: Pymongo for direct MongoDB operations
- **Data Validation**: Pydantic v2
- **Market Data**: Yahoo Finance API via yfinance library
- **HTTP Client**: Requests library for external API calls

### **Frontend Stack**
- **Language**: TypeScript 4.9+
- **Framework**: React 18
- **UI Library**: Material-UI (MUI) v7
- **Routing**: React Router DOM v6
- **HTTP Client**: Axios
- **Date Handling**: Day.js
- **Build Tool**: Create React App with TypeScript template

### **Infrastructure**
- **Database**: MongoDB Atlas or local MongoDB
- **Development**: Local development environment
- **Deployment**: Docker-ready (configuration available)

## 🗄️ Database Architecture

### **MongoDB Collections**

#### **1. Trades Collection**
```javascript
{
  _id: ObjectId,
  portfolio_name: String,      // Indexed
  symbol: String,              // Indexed
  instrument_type: String,     // "STOCK" | "OPTION"
  quantity: Number,
  trade_type: String,          // "BUY" | "SELL"
  executed_price: Number,
  brokerage: Number,
  remarks: String,
  trade_date: Date,            // Indexed
  created_at: Date,
  updated_at: Date
}
```

**Indexes:**
- `{ portfolio_name: 1, symbol: 1 }` - Compound index for portfolio queries
- `{ trade_date: -1 }` - For date-based queries
- `{ portfolio_name: 1, trade_date: -1 }` - For portfolio performance

#### **2. Portfolios Collection**
```javascript
{
  _id: ObjectId,
  portfolio_name: String,      // Unique, Indexed
  owner: String,
  description: String,
  created_at: Date,
  updated_at: Date
}
```

**Indexes:**
- `{ portfolio_name: 1 }` - Unique index for portfolio names

#### **3. Stocks Collection**
```javascript
{
  _id: ObjectId,
  symbol: String,              // Unique, Indexed
  company_name: String,
  industry: String,
  sector: String,
  exchange: String,
  country: String,
  currency: String,
  market_cap: Number,
  description: String,
  website: String,
  created_at: Date,
  updated_at: Date
}
```

**Indexes:**
- `{ symbol: 1 }` - Unique index for stock symbols

#### **4. Options Collection**
```javascript
{
  _id: ObjectId,
  underlying_symbol: String,   // Indexed
  strike_price: Number,
  expiration_date: Date,       // Indexed
  option_type: String,         // "CALL" | "PUT"
  contract_size: Number,
  exchange: String,
  currency: String,
  description: String,
  created_at: Date,
  updated_at: Date
}
```

**Indexes:**
- `{ underlying_symbol: 1, expiration_date: -1 }` - For option queries
- `{ expiration_date: 1 }` - For expiry-based queries

#### **5. Market Data Collection**
```javascript
{
  _id: ObjectId,
  symbol: String,              // Indexed
  current_price: Number,
  last_updated: Date,
  source: String,              // "yahoo_finance" | "manual"
  change: Number,
  change_percent: String
}
```

**Indexes:**
- `{ symbol: 1 }` - For price lookups
- `{ last_updated: -1 }` - For data freshness

#### **6. Daily Snapshots Collection** ⭐ *NEW*
```javascript
{
  _id: ObjectId,
  portfolio_name: String,      // Indexed
  symbol: String,              // Indexed
  instrument_type: String,     // "STOCK" | "OPTION"
  snapshot_date: Date,         // Indexed - Date of the snapshot
  position_quantity: Number,   // Net position quantity
  average_cost: Number,        // Average cost per unit
  current_price: Number,       // Market price as of snapshot date
  market_value: Number,        // Total market value
  total_cost: Number,          // Total cost basis
  net_cost: Number,           // Net cost after sells
  unrealized_pl: Number,       // Unrealized P&L
  realized_pl: Number,         // Realized P&L from sales
  inception_pl: Number,        // Total P&L since inception
  created_at: Date,
  updated_at: Date
}
```

**Indexes:**
- `{ portfolio_name: 1, symbol: 1, snapshot_date: -1 }` - Compound index for P&L queries
- `{ snapshot_date: -1 }` - For date-based historical queries
- `{ portfolio_name: 1, snapshot_date: -1 }` - For portfolio historical analysis

## 🔌 API Architecture

### **RESTful Design Principles**
- **Resource-based URLs**: `/portfolios/{name}/positions`
- **HTTP Methods**: GET, POST, PUT, DELETE
- **Status Codes**: Proper HTTP status codes (200, 201, 400, 404, 500)
- **Response Format**: JSON with consistent structure

### **API Response Structure**
```json
{
  "data": {},           // Main response data
  "message": "",        // Success/error message
  "status": "success",  // Status indicator
  "timestamp": "",      // ISO timestamp
  "errors": []          // Validation errors (if any)
}
```

### **Error Handling Strategy**
```python
# Standard error response
{
  "detail": "Error message",
  "status_code": 400,
  "timestamp": "2025-08-16T10:30:00Z"
}
```

## 🧮 Business Logic Architecture

### **Enhanced P&L Calculation Engine** ⭐ *UPDATED*

#### **NYSE Calendar-Aware P&L Calculations**
The system now supports sophisticated P&L calculations that are aware of NYSE trading calendar:

- **DTD (Day-to-Date)**: Today's P&L - Previous trading day's P&L
- **MTD (Month-to-Date)**: Today's P&L - Last month-end trading day's P&L  
- **YTD (Year-to-Date)**: Today's P&L - Last year-end trading day's P&L

#### **Historical Snapshot System**
```python
class EnhancedSnapshotsService:
    async def create_simple_daily_snapshot(self, snapshot_date: date = None):
        """Create historical P&L snapshots for any date"""
        # Uses historical market data from Yahoo Finance
        # Calculates positions as of the snapshot date
        # Stores comprehensive P&L metrics
        
    def _get_previous_trading_day(self, target_date: date) -> date:
        """NYSE calendar-aware previous trading day calculation"""
        # Skips weekends and major US market holidays
        
    def _get_last_trading_day_of_previous_month(self, target_date: date) -> date:
        """Last trading day of previous month (NYSE calendar)"""
        
    def _get_last_trading_day_of_previous_year(self, target_date: date) -> date:
        """Last trading day of previous year (NYSE calendar)"""
```

#### **Position Aggregation Pipeline**
```python
pipeline = [
    {"$match": {"portfolio_name": portfolio_name}},
    {
        "$group": {
            "_id": {
                "symbol": "$symbol",
                "instrument_type": "$instrument_type"
            },
            "total_quantity_bought": {
                "$sum": {
                    "$cond": [
                        {"$eq": ["$trade_type", "BUY"]},
                        "$quantity",
                        0
                    ]
                }
            },
            "total_quantity_sold": {
                "$sum": {
                    "$cond": [
                        {"$eq": ["$trade_type", "SELL"]},
                        "$quantity",
                        0
                    ]
                }
            },
            "total_cost_bought": {
                "$sum": {
                    "$cond": [
                        {"$eq": ["$trade_type", "BUY"]},
                        {"$add": [
                            {"$multiply": ["$quantity", "$executed_price"]},
                            "$brokerage"
                        ]},
                        0
                    ]
                }
            }
        }
    }
]
```

#### **P&L Calculation Logic**
```python
def calculate_position_pl(position_data, current_price):
    """Calculate P&L for a position"""
    
    # Net position calculation
    net_quantity = position_data["total_quantity_bought"] - position_data["total_quantity_sold"]
    
    if net_quantity <= 0:
        return None  # Closed position
    
    # Cost basis calculation
    total_cost = position_data["total_cost_bought"] - position_data["total_proceeds_sold"]
    average_cost = total_cost / net_quantity
    
    # Market value calculation
    market_value = net_quantity * current_price
    
    # P&L calculations
    unrealized_pl = market_value - total_cost
    inception_pl = market_value + position_data["total_proceeds"] - position_data["total_cost"]
    
    return {
        "net_quantity": net_quantity,
        "average_cost": average_cost,
        "market_value": market_value,
        "unrealized_pl": unrealized_pl,
        "inception_pl": inception_pl
    }
```

### **Market Data Service**

#### **Yahoo Finance Integration**
```python
class MarketDataService:
    def __init__(self):
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes
    
    async def get_stock_price(self, symbol: str) -> Optional[Dict]:
        """Get current stock price from Yahoo Finance"""
        
        # Check cache first
        if symbol in self.cache:
            cached_data = self.cache[symbol]
            if time.time() - cached_data["timestamp"] < self.cache_ttl:
                return cached_data["data"]
        
        try:
            # Fetch from Yahoo Finance
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            price_data = {
                "price": info.get("regularMarketPrice", 0),
                "change": info.get("regularMarketChange", 0),
                "change_percent": info.get("regularMarketChangePercent", "0%"),
                "source": "yahoo_finance"
            }
            
            # Update cache
            self.cache[symbol] = {
                "data": price_data,
                "timestamp": time.time()
            }
            
            return price_data
            
        except Exception as e:
            logger.error(f"Error fetching price for {symbol}: {e}")
            return None
```

## 🎨 Frontend Architecture

### **Component Hierarchy** ⭐ *UPDATED*
```
App
├── AutoRefreshProvider (Context)
├── Navbar
├── Router
    ├── Dashboard (Enhanced with overall P&L)
    ├── PortfolioView (Auto-refresh, smooth updates)
    ├── TradeEntry
    ├── PortfolioManagement (Historical snapshots)
    ├── StockManagement
    ├── OptionManagement
    └── AIPredictions (LSTM models - temporarily disabled)
```

#### **Auto-Refresh System** ⭐ *NEW*
```typescript
// Auto-refresh context for real-time updates
const AutoRefreshContext = createContext<{
  isEnabled: boolean;
  intervalSeconds: number;
  toggleAutoRefresh: () => void;
  setIntervalSeconds: (seconds: number) => void;
  updateLastRefreshTime: () => void;
}>(...);

// Auto-refresh control component
const AutoRefreshControl: React.FC<{
  onManualRefresh: () => void;
  isRefreshing: boolean;
  showLastRefreshTime?: boolean;
}> = ({ onManualRefresh, isRefreshing, showLastRefreshTime = true }) => {
  // Toggle auto-refresh, set intervals, manual refresh
  // Optimized layout to prevent UI jumping
};
```

### **State Management**
- **Local State**: React hooks (useState, useEffect)
- **API State**: Custom hooks for data fetching
- **Form State**: Controlled components with validation
- **Global State**: React Context for shared data

### **Service Layer**
```typescript
// API service structure
class ApiService {
  private baseURL: string;
  private axiosInstance: AxiosInstance;
  
  constructor() {
    this.baseURL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
    this.axiosInstance = axios.create({
      baseURL: this.baseURL,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }
  
  // Trade operations
  async getTrades(): Promise<Trade[]> { ... }
  async createTrade(trade: TradeCreateRequest): Promise<Trade> { ... }
  async updateTrade(id: string, trade: TradeUpdateRequest): Promise<Trade> { ... }
  async deleteTrade(id: string): Promise<void> { ... }
  
  // Portfolio operations
  async getPortfolios(): Promise<Portfolio[]> { ... }
  async getPortfolioPositions(name: string): Promise<PortfolioPosition[]> { ... }
  async getPortfolioPerformance(name: string): Promise<PortfolioPerformance> { ... }
}
```

## 🔒 Security Architecture

### **Input Validation**
- **Backend**: Pydantic models with field validation
- **Frontend**: Form validation with error messages
- **API**: Parameter sanitization and type checking

### **Data Protection**
- **MongoDB**: No direct database access from frontend
- **API**: All data access through authenticated endpoints
- **Validation**: Server-side validation for all inputs

### **Error Handling**
- **Graceful Degradation**: Fallback values for missing data
- **User Feedback**: Clear error messages and loading states
- **Logging**: Comprehensive error logging for debugging

## 📈 Performance Architecture

### **Database Optimization**
- **Indexing**: Strategic indexes for common queries
- **Aggregation Pipelines**: Efficient data processing
- **Connection Pooling**: Optimized database connections

### **API Performance**
- **Async Operations**: Non-blocking I/O operations
- **Caching**: Market data caching to reduce API calls
- **Pagination**: Large dataset handling

### **Frontend Performance**
- **Lazy Loading**: Component and route lazy loading
- **Memoization**: React.memo for expensive components
- **Debouncing**: Search input optimization

## 🧪 Testing Strategy

### **Backend Testing**
- **Unit Tests**: Individual function testing
- **Integration Tests**: API endpoint testing
- **Database Tests**: MongoDB operation testing

### **Frontend Testing**
- **Component Tests**: React component testing
- **Integration Tests**: User interaction testing
- **E2E Tests**: Full user journey testing

## 🚀 Deployment Architecture

### **Development Environment**
- **Local MongoDB**: Development database
- **Hot Reload**: FastAPI and React development servers
- **Environment Variables**: Local configuration

### **Production Environment**
- **MongoDB Atlas**: Cloud database service
- **Docker**: Containerized deployment
- **Environment Variables**: Production configuration
- **Logging**: Production logging and monitoring

## 📊 Monitoring & Observability

### **Application Metrics**
- **API Response Times**: Performance monitoring
- **Error Rates**: Error tracking and alerting
- **Database Performance**: Query performance monitoring

### **Business Metrics**
- **Portfolio Performance**: P&L tracking
- **Trade Volume**: Trading activity monitoring
- **User Activity**: Feature usage tracking

## 🆕 Recent Enhancements (August 2025)

### **Historical P&L Snapshots**
- **Feature**: Create P&L snapshots for any historical date
- **Technology**: MongoDB aggregation pipelines with historical Yahoo Finance data
- **Use Case**: MTD/YTD calculations based on actual stored P&L values
- **Key Files**: `backend/services/enhanced_snapshots.py`, `backend/routers/enhanced_snapshots.py`

### **NYSE Calendar-Aware Calculations**
- **Feature**: P&L calculations respect NYSE trading calendar
- **Technology**: Custom date calculation functions with holiday handling
- **Benefits**: Accurate DTD/MTD/YTD based on actual trading days
- **Implementation**: `_get_previous_trading_day()`, `_get_last_trading_day_of_previous_month()`

### **Real-Time Auto-Refresh System**
- **Feature**: Auto-refresh Dashboard and Portfolio View with configurable intervals
- **Technology**: React Context, setInterval, optimized DOM manipulation
- **UX Enhancement**: Smooth updates without layout jumping
- **Performance**: Direct DOM updates for P&L values to prevent React re-renders

### **Enhanced Portfolio Analytics**
- **Dashboard**: Overall DTD/MTD/YTD P&L across all portfolios
- **Portfolio View**: Real-time P&L updates with historical context
- **Data Sources**: Combined real-time market data with stored snapshots
- **Visualization**: Color-coded P&L indicators with trend icons

### **AI Predictions Module** (Temporarily Disabled)
- **Feature**: LSTM-based stock price prediction models
- **Technology**: TensorFlow/Keras, scikit-learn, yfinance
- **Status**: Complete implementation but disabled due to training stability issues
- **Future**: Model architecture needs optimization for production use

### **Performance Optimizations**
- **Database**: Optimized MongoDB queries with proper indexing
- **Frontend**: React.memo, useCallback, useMemo for expensive operations
- **API**: Efficient data merging and caching strategies
- **Market Data**: Thread-pool execution for yfinance calls

### **Error Handling & Resilience**
- **Backend**: Comprehensive error handling with graceful fallbacks
- **Frontend**: Loading states and error boundaries
- **Data**: Fallback to average cost when historical prices unavailable
- **API**: Proper HTTP status codes and error messages

---

**This document provides a comprehensive technical overview of the Investment Portfolio Tracker system architecture, including all recent enhancements and improvements implemented in August 2025.**
