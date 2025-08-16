# User Guide - Investment Portfolio Tracker

## 🎯 Getting Started

Welcome to the Investment Portfolio Tracker! This comprehensive system helps you manage your investment portfolios, track trades, and monitor performance in real-time.

## 🚀 Quick Start

### **1. Access the Application**
- **Frontend**: Open your browser and go to `http://localhost:3000`
- **Backend API**: Runs on `http://localhost:8000`
- **API Documentation**: Visit `http://localhost:8000/docs` for interactive API docs

### **2. First Steps**
1. **Create a Portfolio**: Go to Portfolio Management → Create New Portfolio
2. **Add Stocks**: Go to Stock Management → Add Stock Definition
3. **Enter Trades**: Go to Trade Entry → Record your first trade
4. **View Dashboard**: Check your portfolio performance on the Dashboard

## 📊 Dashboard Overview

The Dashboard provides a comprehensive overview of all your portfolios:

### **Portfolio Summary Cards**
- **Total Market Value**: Current value of all positions
- **Total P&L**: Overall profit/loss across all portfolios
- **P&L Percentage**: Performance relative to total investment

### **Portfolio List**
- **Portfolio Name**: Click to view detailed positions
- **Market Value**: Current portfolio value
- **P&L**: Total profit/loss for the portfolio
- **P&L %**: Performance percentage

### **Quick Actions**
- **View Portfolio**: Click portfolio name to see positions
- **Add Trade**: Quick access to trade entry
- **Update Prices**: Refresh market data

## 💰 Portfolio Management

### **Creating a Portfolio**
1. Navigate to **Portfolio Management**
2. Click **"Add New Portfolio"**
3. Fill in the details:
   - **Portfolio Name**: Unique identifier (e.g., "Growth Portfolio")
   - **Owner**: Portfolio owner name
   - **Description**: Brief description of strategy
4. Click **"Create Portfolio"**

### **Managing Portfolio Definitions**
- **Edit**: Modify portfolio details
- **Delete**: Remove portfolio (only if no trades exist)
- **View**: See portfolio configuration

## 📈 Portfolio View

### **Position Details**
Each portfolio shows detailed positions with:

- **Symbol**: Stock/option ticker
- **Instrument Type**: STOCK or OPTION
- **Position Quantity**: Net shares/contracts held
- **Average Cost**: Weighted average purchase price
- **Current Price**: Latest market price
- **Market Value**: Current position value
- **Unrealized P&L**: Paper profit/loss
- **Inception P&L**: Total profit/loss from inception

### **P&L Calculations**
- **Unrealized P&L**: Current market value minus cost basis
- **Inception P&L**: Total P&L including realized gains/losses
- **P&L Percentage**: Performance relative to investment

### **Real-time Updates**
- **Market Data**: Prices updated from Yahoo Finance
- **Manual Updates**: Override prices if needed
- **Auto-refresh**: Automatic data updates

## 💼 Trade Management

### **Recording a Trade**
1. Go to **Trade Entry**
2. Fill in trade details:
   - **Portfolio**: Select target portfolio
   - **Symbol**: Stock/option ticker
   - **Instrument Type**: STOCK or OPTION
   - **Quantity**: Number of shares/contracts
   - **Trade Type**: BUY or SELL
   - **Executed Price**: Trade execution price
   - **Brokerage**: Transaction costs
   - **Trade Date**: Date of trade
   - **Remarks**: Additional notes
3. Click **"Record Trade"**

### **Trade Types**
- **BUY**: Increases position, adds to cost basis
- **SELL**: Decreases position, reduces cost basis

### **Managing Trades**
- **View**: See all trades with filtering options
- **Edit**: Modify trade details
- **Delete**: Remove incorrect trades
- **Filter**: Search by portfolio, symbol, date range

### **Trade Impact on Positions**
- **Position Quantity**: Net of all buys and sells
- **Average Cost**: Weighted average of all purchases
- **Realized P&L**: Gains/losses from completed trades
- **Unrealized P&L**: Current paper gains/losses

## 🏢 Static Data Management

### **Stock Definitions**
Manage your stock universe:

1. **Add Stock**: Company information and metadata
2. **Edit Details**: Update company information
3. **Delete**: Remove unused stock definitions

**Required Fields:**
- **Symbol**: Stock ticker (e.g., AAPL)
- **Company Name**: Full company name
- **Exchange**: Trading venue (e.g., NASDAQ)

**Optional Fields:**
- **Industry/Sector**: Business classification
- **Country/Currency**: Geographic and currency info
- **Market Cap**: Company size
- **Website**: Company website

### **Option Definitions**
Manage listed options:

1. **Add Option**: Contract specifications
2. **Edit Details**: Update option information
3. **Delete**: Remove expired options

**Required Fields:**
- **Underlying Symbol**: Stock ticker
- **Strike Price**: Option strike price
- **Expiration Date**: Contract expiry
- **Option Type**: CALL or PUT
- **Contract Size**: Standard is 100

**Optional Fields:**
- **Exchange**: Options exchange
- **Currency**: Contract currency
- **Description**: Custom description

## 📊 Performance Analytics

### **Portfolio Performance**
- **Total Market Value**: Current portfolio worth
- **Total Cost**: Total amount invested
- **Total P&L**: Overall profit/loss
- **P&L Percentage**: Performance metric

### **Position Performance**
- **Individual P&L**: Per-position performance
- **Cost Basis**: Investment amount per position
- **Market Value**: Current worth per position
- **Performance Metrics**: P&L and percentages

### **Historical Tracking**
- **Trade History**: Complete transaction record
- **Position Changes**: How positions evolved
- **Performance Trends**: P&L over time

## 🔍 Search and Filtering

### **Portfolio Search**
- **Name Search**: Find portfolios by name
- **Owner Filter**: Filter by portfolio owner
- **Date Range**: Filter by creation date

### **Trade Filtering**
- **Portfolio**: Filter by specific portfolio
- **Symbol**: Filter by stock/option
- **Trade Type**: BUY or SELL only
- **Date Range**: Specific time periods
- **Amount**: Price or quantity ranges

### **Stock/Option Search**
- **Symbol Search**: Find by ticker
- **Industry Filter**: Filter by business sector
- **Exchange Filter**: Filter by trading venue

## 📱 User Interface Features

### **Responsive Design**
- **Desktop**: Full-featured interface
- **Tablet**: Optimized for touch
- **Mobile**: Mobile-friendly layout

### **Navigation**
- **Top Navigation**: Quick access to main sections
- **Breadcrumbs**: Current location indicator
- **Sidebar**: Additional navigation options

### **Data Display**
- **Tables**: Sortable and filterable data
- **Cards**: Summary information
- **Charts**: Visual performance data
- **Forms**: Data entry and editing

## 🔧 Advanced Features

### **Market Data Integration**
- **Real-time Prices**: Live market data
- **Automatic Updates**: Scheduled price refreshes
- **Manual Overrides**: Custom price inputs
- **Data Sources**: Yahoo Finance integration

### **P&L Calculations**
- **Mark-to-Market**: Current position values
- **Cost Basis**: Investment amounts
- **Realized vs Unrealized**: Completed vs paper gains
- **Performance Metrics**: Various P&L measures

### **Data Export**
- **Portfolio Reports**: Summary exports
- **Trade History**: Transaction records
- **Performance Data**: P&L analytics
- **Format Options**: CSV, JSON, PDF

## 🚨 Troubleshooting

### **Common Issues**

#### **Portfolio Not Showing**
- Check if portfolio has trades
- Verify portfolio name spelling
- Ensure portfolio is active

#### **P&L Calculations Incorrect**
- Verify trade data accuracy
- Check market prices are current
- Review brokerage calculations
- Ensure proper trade dates

#### **Market Data Not Updating**
- Check internet connection
- Verify Yahoo Finance access
- Try manual price update
- Check API rate limits

#### **Trades Not Saving**
- Validate all required fields
- Check portfolio exists
- Verify symbol definitions
- Review error messages

### **Data Validation**
- **Required Fields**: Must be filled
- **Data Types**: Correct format required
- **Business Rules**: Logical validation
- **Cross-references**: Valid portfolio/symbol

### **Error Messages**
- **Clear Descriptions**: What went wrong
- **Action Items**: How to fix
- **Field Indicators**: Which fields have issues
- **Help Links**: Additional guidance

## 📚 Best Practices

### **Portfolio Organization**
- **Clear Naming**: Descriptive portfolio names
- **Logical Grouping**: Similar strategies together
- **Regular Review**: Periodic portfolio assessment
- **Documentation**: Notes on strategy and goals

### **Trade Recording**
- **Immediate Entry**: Record trades promptly
- **Accurate Data**: Double-check all details
- **Consistent Format**: Use standard practices
- **Backup Records**: Keep external copies

### **Data Maintenance**
- **Regular Updates**: Keep prices current
- **Clean Data**: Remove obsolete entries
- **Validation**: Verify data accuracy
- **Archiving**: Store historical data

### **Performance Monitoring**
- **Regular Review**: Weekly/monthly check-ins
- **Goal Tracking**: Compare to objectives
- **Risk Assessment**: Monitor position sizes
- **Rebalancing**: Adjust as needed

## 🔮 Future Features

### **Planned Enhancements**
- **Daily Snapshots**: Automated P&L tracking
- **DTD/MTD/YTD P&L**: Time-based performance
- **Advanced Charts**: Visual analytics
- **Risk Metrics**: Position risk analysis
- **Alerts**: Price and performance notifications

### **Integration Options**
- **Broker APIs**: Direct trade import
- **Market Data**: Additional data sources
- **Mobile Apps**: Native mobile applications
- **Cloud Sync**: Multi-device access

## 📞 Support and Help

### **Getting Help**
1. **Documentation**: Check this user guide
2. **API Docs**: Visit `/docs` endpoint
3. **Error Messages**: Read detailed error descriptions
4. **Community**: Check GitHub issues

### **Reporting Issues**
- **Bug Reports**: Describe the problem clearly
- **Feature Requests**: Explain desired functionality
- **Data Issues**: Provide specific examples
- **Performance Problems**: Include system details

### **Contact Information**
- **GitHub**: Repository issues and discussions
- **Documentation**: In-app help and guides
- **Community**: User forums and discussions

---

**This user guide covers all aspects of using the Investment Portfolio Tracker system effectively.**
