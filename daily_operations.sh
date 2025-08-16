#!/bin/bash

# Daily Operations Script for Investment Portfolio Tracker
# This script handles daily tasks like creating snapshots

echo "📅 Daily Operations for Investment Portfolio Tracker"
echo "===================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check if backend is running
check_backend() {
    if curl -s "http://localhost:8000/health" > /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Function to create daily snapshots
create_daily_snapshots() {
    echo -e "${BLUE}📊 Creating daily snapshots...${NC}"
    
    if ! check_backend; then
        echo -e "${RED}❌ Backend is not running! Please start the system first.${NC}"
        echo -e "${YELLOW}💡 Use: ./start_investment_system.sh start${NC}"
        return 1
    fi
    
    # Create snapshots for all portfolios
    echo -e "${YELLOW}Creating snapshots for all portfolios...${NC}"
    response=$(curl -s -X POST "http://localhost:8000/scheduler/quick-daily-snapshots")
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Daily snapshots created successfully!${NC}"
        echo -e "${BLUE}Response: $response${NC}"
    else
        echo -e "${RED}❌ Failed to create daily snapshots${NC}"
        return 1
    fi
}

# Function to schedule tomorrow's snapshots
schedule_tomorrow_snapshots() {
    echo -e "${BLUE}📅 Scheduling tomorrow's snapshots...${NC}"
    
    if ! check_backend; then
        echo -e "${RED}❌ Backend is not running!${NC}"
        return 1
    fi
    
    # Schedule snapshots for tomorrow (1440 minutes = 24 hours)
    echo -e "${YELLOW}Scheduling snapshots for tomorrow...${NC}"
    response=$(curl -s -X POST "http://localhost:8000/scheduler/schedule-daily-snapshots?delay_minutes=1440")
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Tomorrow's snapshots scheduled!${NC}"
        echo -e "${BLUE}Response: $response${NC}"
    else
        echo -e "${RED}❌ Failed to schedule tomorrow's snapshots${NC}"
        return 1
    fi
}

# Function to get DTD/MTD/YTD analysis
get_pnl_analysis() {
    local portfolio_name=${1:-""}
    
    echo -e "${BLUE}📈 Getting P&L Analysis...${NC}"
    
    if ! check_backend; then
        echo -e "${RED}❌ Backend is not running!${NC}"
        return 1
    fi
    
    if [ -z "$portfolio_name" ]; then
        echo -e "${YELLOW}No portfolio specified. Getting analysis for all portfolios...${NC}"
        # You can modify this to get a list of portfolios first
        echo -e "${YELLOW}Please specify a portfolio name: ./daily_operations.sh analysis PORTFOLIO_NAME${NC}"
        return 1
    fi
    
    echo -e "${YELLOW}Getting DTD/MTD/YTD analysis for $portfolio_name...${NC}"
    response=$(curl -s "http://localhost:8000/enhanced-snapshots/dtd-mtd-ytd/$portfolio_name")
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ P&L analysis retrieved!${NC}"
        echo -e "${BLUE}Analysis: $response${NC}"
    else
        echo -e "${RED}❌ Failed to get P&L analysis${NC}"
        return 1
    fi
}

# Function to check system status
check_system_status() {
    echo -e "${BLUE}🔍 Checking System Status...${NC}"
    
    # Check backend
    if check_backend; then
        echo -e "${GREEN}✅ Backend: Running on http://localhost:8000${NC}"
        echo -e "${BLUE}   📚 API Docs: http://localhost:8000/docs${NC}"
        
        # Check enhanced snapshots
        if curl -s "http://localhost:8000/enhanced-snapshots/status" > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Enhanced Snapshots: Available${NC}"
        else
            echo -e "${YELLOW}⚠️  Enhanced Snapshots: Not available${NC}"
        fi
        
        # Check scheduler
        if curl -s "http://localhost:8000/scheduler/status" > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Scheduler: Available${NC}"
        else
            echo -e "${YELLOW}⚠️  Scheduler: Not available${NC}"
        fi
        
    else
        echo -e "${RED}❌ Backend: Not running${NC}"
    fi
    
    # Check frontend
    if curl -s "http://localhost:3000" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Frontend: Running on http://localhost:3000${NC}"
    else
        echo -e "${RED}❌ Frontend: Not running${NC}"
    fi
}

# Function to show usage
show_usage() {
    echo -e "${BLUE}Usage: $0 [command] [options]${NC}"
    echo ""
    echo "Commands:"
    echo "  snapshots [PORTFOLIO_NAME]  - Create daily snapshots (all or specific portfolio)"
    echo "  schedule                     - Schedule tomorrow's snapshots"
    echo "  analysis PORTFOLIO_NAME     - Get DTD/MTD/YTD P&L analysis"
    echo "  status                       - Check system status"
    echo "  help                         - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 snapshots                 # Create snapshots for all portfolios"
    echo "  $0 snapshots Growth          # Create snapshots for Growth portfolio"
    echo "  $0 schedule                  # Schedule tomorrow's snapshots"
    echo "  $0 analysis Growth           # Get P&L analysis for Growth portfolio"
    echo "  $0 status                    # Check what's running"
    echo ""
    echo "Daily Workflow:"
    echo "  1. Start system: ./start_investment_system.sh start"
    echo "  2. Create snapshots: $0 snapshots"
    echo "  3. Schedule tomorrow: $0 schedule"
    echo "  4. Check analysis: $0 analysis PORTFOLIO_NAME"
}

# Main execution
case "${1:-help}" in
    "snapshots")
        if [ -n "$2" ]; then
            echo -e "${YELLOW}Creating snapshots for portfolio: $2${NC}"
            # You can modify the API call to specify portfolio
            create_daily_snapshots
        else
            create_daily_snapshots
        fi
        ;;
        
    "schedule")
        schedule_tomorrow_snapshots
        ;;
        
    "analysis")
        if [ -n "$2" ]; then
            get_pnl_analysis "$2"
        else
            echo -e "${RED}❌ Please specify a portfolio name${NC}"
            echo -e "${YELLOW}Usage: $0 analysis PORTFOLIO_NAME${NC}"
        fi
        ;;
        
    "status")
        check_system_status
        ;;
        
    "help"|"-h"|"--help")
        show_usage
        ;;
        
    *)
        echo -e "${RED}Unknown command: $1${NC}"
        show_usage
        exit 1
        ;;
esac
