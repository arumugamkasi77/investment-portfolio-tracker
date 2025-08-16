#!/bin/bash

# Investment Portfolio Tracker - Complete Startup Script
# This script starts the entire system: Backend, Frontend, and Daily Snapshots

echo "🚀 Starting Investment Portfolio Tracker System..."
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check if a port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null ; then
        echo -e "${RED}Port $1 is already in use!${NC}"
        return 1
    else
        echo -e "${GREEN}Port $1 is available${NC}"
        return 0
    fi
}

# Function to wait for service to be ready
wait_for_service() {
    local url=$1
    local service_name=$2
    local max_attempts=30
    local attempt=1
    
    echo -e "${YELLOW}Waiting for $service_name to be ready...${NC}"
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s "$url/health" > /dev/null 2>&1; then
            echo -e "${GREEN}$service_name is ready!${NC}"
            return 0
        fi
        
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo -e "${RED}$service_name failed to start within expected time${NC}"
    return 1
}

# Function to create daily snapshots
create_daily_snapshots() {
    echo -e "${BLUE}Creating daily snapshots...${NC}"
    
    # Wait a bit for backend to be fully ready
    sleep 5
    
    # Create snapshots for all portfolios
    if curl -s -X POST "http://localhost:8000/scheduler/quick-daily-snapshots" > /dev/null 2>&1; then
        echo -e "${GREEN}Daily snapshots created successfully!${NC}"
    else
        echo -e "${YELLOW}Warning: Could not create daily snapshots (backend might still be starting)${NC}"
    fi
}

# Function to show system status
show_status() {
    echo -e "\n${BLUE}📊 System Status:${NC}"
    echo "=================="
    
    # Backend status
    if curl -s "http://localhost:8000/health" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Backend: Running on http://localhost:8000${NC}"
        echo -e "${BLUE}   📚 API Docs: http://localhost:8000/docs${NC}"
    else
        echo -e "${RED}❌ Backend: Not running${NC}"
    fi
    
    # Frontend status
    if curl -s "http://localhost:3000" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Frontend: Running on http://localhost:3000${NC}"
    else
        echo -e "${RED}❌ Frontend: Not running${NC}"
    fi
    
    # Snapshot status
    if curl -s "http://localhost:8000/enhanced-snapshots/status" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Enhanced Snapshots: Available${NC}"
    else
        echo -e "${YELLOW}⚠️  Enhanced Snapshots: Not available yet${NC}"
    fi
    
    # Scheduler status
    if curl -s "http://localhost:8000/scheduler/status" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Scheduler: Available${NC}"
    else
        echo -e "${YELLOW}⚠️  Scheduler: Not available yet${NC}"
    fi
}

# Function to start backend
start_backend() {
    echo -e "\n${BLUE}🔧 Starting Backend...${NC}"
    
    if ! check_port 8000; then
        echo -e "${RED}Backend port 8000 is already in use!${NC}"
        return 1
    fi
    
    cd backend
    
    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        echo -e "${YELLOW}Creating virtual environment...${NC}"
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    echo -e "${YELLOW}Activating virtual environment...${NC}"
    source venv/bin/activate
    
    # Install/update dependencies
    echo -e "${YELLOW}Installing/updating dependencies...${NC}"
    pip install -r requirements.txt
    
    # Start backend in background
    echo -e "${YELLOW}Starting backend server...${NC}"
    nohup python main.py > ../logs/backend.log 2>&1 &
    BACKEND_PID=$!
    echo $BACKEND_PID > ../logs/backend.pid
    
    cd ..
    
    # Wait for backend to be ready
    if wait_for_service "http://localhost:8000" "Backend"; then
        echo -e "${GREEN}Backend started successfully! (PID: $BACKEND_PID)${NC}"
        return 0
    else
        echo -e "${RED}Backend failed to start!${NC}"
        return 1
    fi
}

# Function to start frontend
start_frontend() {
    echo -e "\n${BLUE}🎨 Starting Frontend...${NC}"
    
    if ! check_port 3000; then
        echo -e "${RED}Frontend port 3000 is already in use!${NC}"
        return 1
    fi
    
    cd frontend
    
    # Install/update dependencies
    echo -e "${YELLOW}Installing/updating dependencies...${NC}"
    npm install
    
    # Start frontend in background
    echo -e "${YELLOW}Starting frontend server...${NC}"
    nohup npm start > ../logs/frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > ../logs/frontend.pid
    
    cd ..
    
    # Wait for frontend to be ready
    echo -e "${YELLOW}Waiting for frontend to be ready...${NC}"
    sleep 10  # Frontend takes longer to start
    
    if curl -s "http://localhost:3000" > /dev/null 2>&1; then
        echo -e "${GREEN}Frontend started successfully! (PID: $FRONTEND_PID)${NC}"
        return 0
    else
        echo -e "${YELLOW}Frontend is starting... (may take a few more seconds)${NC}"
        return 0
    fi
}

# Function to setup daily snapshots
setup_daily_snapshots() {
    echo -e "\n${BLUE}📅 Setting up Daily Snapshots...${NC}"
    
    # Wait for backend to be fully ready
    sleep 5
    
    # Create snapshots for today
    create_daily_snapshots
    
    # Schedule tomorrow's snapshots
    echo -e "${BLUE}Scheduling tomorrow's snapshots...${NC}"
    if curl -s -X POST "http://localhost:8000/scheduler/schedule-daily-snapshots?delay_minutes=1440" > /dev/null 2>&1; then
        echo -e "${GREEN}Tomorrow's snapshots scheduled!${NC}"
    else
        echo -e "${YELLOW}Warning: Could not schedule tomorrow's snapshots${NC}"
    fi
}

# Function to create logs directory
create_logs_directory() {
    if [ ! -d "logs" ]; then
        mkdir -p logs
        echo -e "${GREEN}Created logs directory${NC}"
    fi
}

# Function to stop all services
stop_all() {
    echo -e "\n${RED}🛑 Stopping all services...${NC}"
    
    # Stop backend
    if [ -f "logs/backend.pid" ]; then
        BACKEND_PID=$(cat logs/backend.pid)
        if kill -0 $BACKEND_PID 2>/dev/null; then
            kill $BACKEND_PID
            echo -e "${GREEN}Backend stopped (PID: $BACKEND_PID)${NC}"
        fi
        rm -f logs/backend.pid
    fi
    
    # Stop frontend
    if [ -f "logs/frontend.pid" ]; then
        FRONTEND_PID=$(cat logs/frontend.pid)
        if kill -0 $FRONTEND_PID 2>/dev/null; then
            kill $FRONTEND_PID
            echo -e "${GREEN}Frontend stopped (PID: $FRONTEND_PID)${NC}"
        fi
        rm -f logs/frontend.pid
    fi
    
    echo -e "${GREEN}All services stopped${NC}"
}

# Function to show usage
show_usage() {
    echo -e "${BLUE}Usage: $0 [command]${NC}"
    echo ""
    echo "Commands:"
    echo "  start     - Start the entire system (default)"
    echo "  stop      - Stop all services"
    echo "  restart   - Restart all services"
    echo "  status    - Show system status"
    echo "  snapshots - Create daily snapshots"
    echo "  help      - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 start     # Start everything"
    echo "  $0 stop      # Stop everything"
    echo "  $0 status    # Check what's running"
}

# Main execution
case "${1:-start}" in
    "start")
        echo -e "${GREEN}🚀 Starting Investment Portfolio Tracker System...${NC}"
        
        # Create logs directory
        create_logs_directory
        
        # Start backend
        if start_backend; then
            # Start frontend
            if start_frontend; then
                # Setup daily snapshots
                setup_daily_snapshots
                
                echo -e "\n${GREEN}🎉 System started successfully!${NC}"
                echo "=================================================="
                show_status
                
                echo -e "\n${BLUE}💡 Daily Operations:${NC}"
                echo "=================="
                echo "• Daily snapshots are created automatically on startup"
                echo "• Tomorrow's snapshots are scheduled automatically"
                echo "• Use the scheduler endpoints to manage daily operations"
                echo "• Visit http://localhost:8000/docs for API documentation"
                echo "• Visit http://localhost:3000 for the web interface"
                
                echo -e "\n${YELLOW}📝 Logs are available in the 'logs' directory${NC}"
                echo -e "${YELLOW}🔄 To restart: $0 restart${NC}"
                echo -e "${YELLOW}🛑 To stop: $0 stop${NC}"
                
            else
                echo -e "${RED}Frontend failed to start!${NC}"
                stop_all
                exit 1
            fi
        else
            echo -e "${RED}Backend failed to start!${NC}"
            exit 1
        fi
        ;;
        
    "stop")
        stop_all
        ;;
        
    "restart")
        echo -e "${YELLOW}🔄 Restarting system...${NC}"
        stop_all
        sleep 2
        $0 start
        ;;
        
    "status")
        show_status
        ;;
        
    "snapshots")
        create_daily_snapshots
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
