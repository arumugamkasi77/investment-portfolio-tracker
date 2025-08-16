# Investment Portfolio Tracker

A comprehensive investment portfolio management system with real-time market data, P&L tracking, and full CRUD operations for trades, portfolios, stocks, and options.

## 🏗️ System Architecture

### **Backend (Python FastAPI)**
- **Framework**: FastAPI with async/await support
- **Database**: MongoDB with Motor async driver
- **Market Data**: Yahoo Finance integration via yfinance
- **API**: RESTful endpoints with automatic OpenAPI documentation

### **Frontend (React TypeScript)**
- **Framework**: React 18 with TypeScript
- **UI Library**: Material-UI (MUI) v7
- **State Management**: React hooks and context
- **Routing**: React Router DOM v6
- **HTTP Client**: Axios for API communication

## 🚀 Features

### **Core Portfolio Management**
- ✅ **Portfolio Dashboard**: Total market value, P&L overview
- ✅ **Portfolio View**: Detailed positions with real-time P&L calculations
- ✅ **Trade Management**: Full CRUD operations for buy/sell transactions
- ✅ **Real-time Market Data**: Live price updates from Yahoo Finance

### **Static Data Management**
- ✅ **Portfolio Management**: Create, edit, delete portfolio definitions
- ✅ **Stock Management**: Manage stock symbols and company information
- ✅ **Option Management**: Handle listed stock options with strike/expiry

### **Advanced Features**
- ✅ **P&L Calculations**: Inception P&L, mark-to-market valuations
- ✅ **Multi-instrument Support**: Stocks and Options
- ✅ **Brokerage Tracking**: Include transaction costs in calculations
- ✅ **Responsive Design**: Mobile-friendly interface

## 📊 Database Schema

### **Collections**

#### **Trades Collection**
```json
{
  "_id": "ObjectId",
  "portfolio_name": "string",
  "symbol": "string",
  "instrument_type": "STOCK|OPTION",
  "quantity": "number",
  "trade_type": "BUY|SELL",
  "executed_price": "number",
  "brokerage": "number",
  "remarks": "string",
  "trade_date": "datetime",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

#### **Portfolios Collection**
```json
{
  "_id": "ObjectId",
  "portfolio_name": "string",
  "owner": "string",
  "description": "string",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

#### **Stocks Collection**
```json
{
  "_id": "ObjectId",
  "symbol": "string",
  "company_name": "string",
  "industry": "string",
  "sector": "string",
  "exchange": "string",
  "country": "string",
  "currency": "string",
  "market_cap": "number",
  "description": "string",
  "website": "string"
}
```

#### **Options Collection**
```json
{
  "_id": "ObjectId",
  "underlying_symbol": "string",
  "strike_price": "number",
  "expiration_date": "datetime",
  "option_type": "CALL|PUT",
  "contract_size": "number",
  "exchange": "string",
  "currency": "string",
  "description": "string"
}
```

## 🔌 API Endpoints

### **Portfolio Management**
```
GET    /portfolios/                    # List all portfolios
GET    /portfolios/{name}/positions    # Get portfolio positions
GET    /portfolios/{name}/performance  # Get portfolio performance
POST   /portfolios/{name}/market-price/{symbol} # Update market price
```

### **Trade Management**
```
GET    /trades/                        # List all trades
POST   /trades/                        # Create new trade
GET    /trades/{id}                    # Get specific trade
PUT    /trades/{id}                    # Update trade
DELETE /trades/{id}                    # Delete trade
```

### **Static Data Management**
```
# Portfolios
GET    /portfolio-static/              # List portfolio definitions
POST   /portfolio-static/              # Create portfolio
PUT    /portfolio-static/{id}          # Update portfolio
DELETE /portfolio-static/{id}          # Delete portfolio

# Stocks
GET    /stocks/                        # List stock definitions
POST   /stocks/                        # Create stock
PUT    /stocks/{id}                    # Update stock
DELETE /stocks/{id}                    # Delete stock

# Options
GET    /options/                       # List option definitions
POST   /options/                       # Create option
PUT    /options/{id}                   # Update option
DELETE /options/{id}                   # Delete option
```

### **Market Data**
```
GET    /market-data/price/{symbol}     # Get current price
GET    /market-data/prices             # Get multiple prices
```

## 🧮 P&L Calculation Logic

### **Position Calculation**
```python
# Net Position = Total Bought - Total Sold
net_quantity = total_quantity_bought - total_quantity_sold

# Average Cost = (Total Cost Bought - Total Proceeds Sold) / Net Quantity
average_cost = (total_cost_bought - total_proceeds_sold) / net_quantity

# Market Value = Net Quantity × Current Market Price
market_value = net_quantity × current_price

# Unrealized P&L = Market Value - Net Cost
unrealized_pl = market_value - net_cost

# Inception P&L = Market Value + Proceeds from Sales - Total Cost
inception_pl = market_value + total_proceeds - total_cost
```

### **Trade Impact**
- **BUY**: Increases position, adds to cost basis
- **SELL**: Decreases position, reduces cost basis
- **Brokerage**: Included in cost calculations

## 🛠️ Installation & Setup

### **Prerequisites**
- Python 3.9+
- Node.js 16+
- MongoDB 5.0+
- Git

### **Backend Setup**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### **Frontend Setup**
```bash
cd frontend
npm install
```

### **Environment Configuration**
```bash
# Copy example environment file
cp backend/env_example backend/.env

# Configure MongoDB connection
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=investment_tracker
```

## 🚀 Running the System

### **Start Backend**
```bash
cd backend
python main.py
# Server runs on http://localhost:8000
```

### **Start Frontend**
```bash
cd frontend
npm start
# App runs on http://localhost:3000
```

### **Access API Documentation**
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔧 Development

### **Project Structure**
```
INVESTMENT/
├── backend/                    # Python FastAPI backend
│   ├── routers/               # API route definitions
│   ├── services/              # Business logic services
│   ├── models.py              # Pydantic data models
│   ├── database.py            # MongoDB connection
│   └── main.py                # FastAPI application
├── frontend/                   # React TypeScript frontend
│   ├── src/
│   │   ├── components/        # Reusable UI components
│   │   ├── pages/             # Page components
│   │   ├── services/          # API service layer
│   │   └── types/             # TypeScript type definitions
│   └── package.json
└── README.md                   # This documentation
```

### **Code Quality**
- **Backend**: Type hints, async/await, error handling
- **Frontend**: TypeScript, ESLint, Material-UI components
- **API**: RESTful design, proper HTTP status codes
- **Database**: Indexed queries, efficient aggregations

## 📈 Performance Features

### **Real-time Updates**
- Live market data fetching
- Automatic price updates
- Responsive UI updates

### **Data Optimization**
- MongoDB aggregation pipelines
- Efficient position calculations
- Cached market data

### **Scalability**
- Async/await architecture
- Connection pooling
- Modular service design

## 🔒 Security & Data Integrity

### **Input Validation**
- Pydantic models for data validation
- Frontend form validation
- API parameter sanitization

### **Error Handling**
- Comprehensive error messages
- Graceful fallbacks
- Logging and monitoring

### **Data Consistency**
- Transaction integrity
- Referential integrity checks
- Data validation rules

## 🧪 Testing

### **Backend Tests**
```bash
cd backend
python -m pytest tests/
```

### **Frontend Tests**
```bash
cd frontend
npm test
```

## 📚 API Examples

### **Create a Trade**
```bash
curl -X POST "http://localhost:8000/trades/" \
  -H "Content-Type: application/json" \
  -d '{
    "portfolio_name": "My Portfolio",
    "symbol": "AAPL",
    "instrument_type": "STOCK",
    "quantity": 100,
    "trade_type": "BUY",
    "executed_price": 150.00,
    "brokerage": 5.00
  }'
```

### **Get Portfolio Performance**
```bash
curl "http://localhost:8000/portfolios/My%20Portfolio/performance"
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For issues and questions:
1. Check the API documentation at `/docs`
2. Review the code examples
3. Open an issue on GitHub

---

**Built with ❤️ using FastAPI, React, and MongoDB**
