# Investment Portfolio Tracker

A comprehensive web application for tracking investment portfolios, trades, and performance analytics.

## Features

- **Trade Entry**: Capture trades with Portfolio, Stock/Option details, Quantity, Buy/Sell, Price, Brokerage, and Remarks
- **Portfolio Analytics**: View current portfolio values with Mark-to-Market pricing
- **Performance Tracking**: DTD, MTD, YTD P&L calculations
- **Automated Snapshots**: Daily P&L snapshots for historical tracking

## Tech Stack

- **Frontend**: React with modern UI components
- **Backend**: Python with FastAPI
- **Database**: MongoDB
- **Automation**: Cron jobs for daily snapshots

## Project Structure

```
INVESTMENT/
├── backend/          # Python FastAPI backend
├── frontend/         # React frontend
├── requirements.txt  # Python dependencies
└── README.md
```

## Setup Instructions

### Environment Setup
1. Create and activate virtual environment:
   ```bash
   python3 -m venv investment-env
   source investment-env/bin/activate  # On Windows: investment-env\Scripts\activate
   ```
2. Install dependencies: `pip install -r requirements.txt`

### Prerequisites
- MongoDB running locally on default port (27017)
- Node.js and npm installed

### Backend Setup
1. Navigate to backend directory: `cd backend`
2. Ensure virtual environment is activated: `source ../investment-env/bin/activate`
3. Start the backend server: `uvicorn main:app --host 127.0.0.1 --port 8000 --reload`
4. Verify backend is running: `curl http://127.0.0.1:8000/health`

### Frontend Setup
1. Navigate to frontend directory: `cd frontend`
2. Install dependencies: `npm install`
3. Start development server: `npm start`
4. Access the application at: `http://localhost:3000`

## API Endpoints

### Trades
- `POST /trades/` - Create a new trade
- `GET /trades/` - Get trades with optional filtering
- `GET /trades/{trade_id}` - Get specific trade
- `PUT /trades/{trade_id}` - Update trade
- `DELETE /trades/{trade_id}` - Delete trade
- `GET /trades/portfolio/{portfolio_name}/summary` - Get portfolio trade summary

### Portfolios
- `GET /portfolios/` - Get all portfolios
- `GET /portfolios/{portfolio_name}/positions` - Get portfolio positions with MTM
- `GET /portfolios/{portfolio_name}/performance` - Get portfolio performance metrics
- `POST /portfolios/{portfolio_name}/market-price/{symbol}` - Update market price

### Snapshots
- `POST /snapshots/create` - Create daily snapshots manually
- `GET /snapshots/` - Get snapshots with filtering
- `GET /snapshots/pl-analysis/{portfolio_name}` - Get DTD/MTD/YTD P&L analysis

## Database Schema

- **Trades**: Individual trade records with portfolio, symbol, quantity, price, brokerage
- **Portfolios**: Portfolio configurations and metadata
- **DailySnapshots**: Daily P&L snapshots for historical tracking
- **MarketData**: Current market prices (cached for mark-to-market calculations)

## Features Implemented

✅ **Trade Entry**: Complete form with validation for all required fields
✅ **Portfolio Dashboard**: Overview of all portfolios with basic statistics
✅ **Portfolio View**: Detailed positions with mark-to-market values
✅ **Mark-to-Market**: Real-time position values with unrealized P&L
✅ **Manual Price Updates**: Ability to update market prices for symbols
✅ **API Integration**: Full CRUD operations for trades and portfolios
✅ **Modern UI**: Material-UI based responsive design

## Upcoming Features

🔄 **Daily Snapshots**: Automated daily P&L snapshots (manual creation available)
🔄 **DTD/MTD/YTD P&L**: Historical P&L comparison (framework in place)
⏳ **Real Market Data**: Integration with external market data providers
⏳ **Advanced Analytics**: More detailed performance metrics and charts
