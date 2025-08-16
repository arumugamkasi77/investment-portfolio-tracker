# 🚀 Investment Portfolio Tracker - Startup Guide

This guide shows you how to start the entire system with a single command, including automatic daily snapshots setup.

## 📋 Prerequisites

Before starting, ensure you have:

- ✅ **Python 3.9+** installed and in PATH
- ✅ **Node.js 16+** installed and in PATH  
- ✅ **MongoDB** running on port 27017
- ✅ **Git** for version control

## 🎯 Quick Start (Single Command)

### **For Mac/Linux:**
```bash
./start_investment_system.sh start
```

### **For Windows:**
```cmd
start_investment_system.bat
```

**That's it!** The script will automatically:
1. 🔧 Start the Python backend server
2. 🎨 Start the React frontend server  
3. 📅 Create daily snapshots for today
4. ⏰ Schedule tomorrow's snapshots
5. 📊 Show system status

## 🔄 Daily Operations

### **Start the System (Every Day):**
```bash
./start_investment_system.sh start
```

### **Create Daily Snapshots:**
```bash
./daily_operations.sh snapshots
```

### **Schedule Tomorrow's Snapshots:**
```bash
./daily_operations.sh schedule
```

### **Get P&L Analysis:**
```bash
./daily_operations.sh analysis "Portfolio Name"
```

### **Check System Status:**
```bash
./daily_operations.sh status
```

## 📁 Scripts Overview

### **1. Main Startup Script** (`start_investment_system.sh` / `.bat`)
- **Purpose**: Complete system startup
- **What it does**:
  - Starts backend server (port 8000)
  - Starts frontend server (port 3000)
  - Creates daily snapshots automatically
  - Schedules tomorrow's snapshots
  - Shows system status

### **2. Daily Operations Script** (`daily_operations.sh`)
- **Purpose**: Handle daily tasks
- **Commands**:
  - `snapshots` - Create daily snapshots
  - `schedule` - Schedule tomorrow's snapshots
  - `analysis` - Get DTD/MTD/YTD P&L
  - `status` - Check system health

## 🎮 Manual Control

### **Start Everything:**
```bash
./start_investment_system.sh start
```

### **Stop Everything:**
```bash
./start_investment_system.sh stop
```

### **Restart Everything:**
```bash
./start_investment_system.sh restart
```

### **Check Status:**
```bash
./start_investment_system.sh status
```

## 🌐 Access Points

Once started, you can access:

- **🌐 Web Interface**: http://localhost:3000
- **🔌 API Backend**: http://localhost:8000
- **📚 API Documentation**: http://localhost:8000/docs
- **📊 Enhanced Snapshots**: http://localhost:8000/enhanced-snapshots
- **⏰ Scheduler**: http://localhost:8000/scheduler

## 📅 Daily Workflow

### **Morning Startup (9 AM):**
1. **Start the system**:
   ```bash
   ./start_investment_system.sh start
   ```
2. **Verify snapshots created**:
   ```bash
   ./daily_operations.sh status
   ```

### **Throughout the Day:**
- **Check P&L analysis**:
  ```bash
  ./daily_operations.sh analysis "Portfolio Name"
  ```
- **Create additional snapshots** (if needed):
  ```bash
  ./daily_operations.sh snapshots
  ```

### **Evening (Before Close):**
- **Schedule tomorrow's snapshots**:
  ```bash
  ./daily_operations.sh schedule
  ```

## 🔧 Troubleshooting

### **Port Already in Use:**
```bash
# Check what's using the port
lsof -i :8000  # Backend
lsof -i :3000  # Frontend

# Kill the process
kill -9 <PID>
```

### **Backend Won't Start:**
```bash
# Check logs
tail -f logs/backend.log

# Check MongoDB connection
mongosh --eval "db.runCommand('ping')"
```

### **Frontend Won't Start:**
```bash
# Check logs
tail -f logs/frontend.log

# Check Node.js version
node --version
```

### **Daily Snapshots Not Working:**
```bash
# Check backend health
curl http://localhost:8000/health

# Check enhanced snapshots status
curl http://localhost:8000/enhanced-snapshots/status
```

## 📝 Logs

All system logs are stored in the `logs/` directory:

- **`backend.log`** - Backend server logs
- **`frontend.log`** - Frontend server logs
- **`backend.pid`** - Backend process ID
- **`frontend.pid`** - Frontend process ID

## 🔄 Automation Options

### **Option 1: Manual (Recommended)**
- Run `./start_investment_system.sh start` each morning
- Use `./daily_operations.sh` for daily tasks
- Full control over when operations happen

### **Option 2: Cron Job (Advanced)**
```bash
# Add to crontab (crontab -e)
0 9 * * * cd /path/to/investment && ./start_investment_system.sh start
0 17 * * * cd /path/to/investment && ./daily_operations.sh schedule
```

### **Option 3: Systemd Service (Linux)**
Create a systemd service for automatic startup on boot.

## 🎯 Key Benefits

1. **🚀 Single Command Startup** - Everything starts with one script
2. **📅 Automatic Daily Snapshots** - No manual intervention needed
3. **⏰ Smart Scheduling** - Tomorrow's snapshots automatically scheduled
4. **🔍 Health Monitoring** - Built-in status checking
5. **📝 Comprehensive Logging** - Easy troubleshooting
6. **🔄 Easy Restart** - Simple restart command
7. **🛑 Clean Shutdown** - Proper process management

## 💡 Pro Tips

1. **Always check system status** before creating snapshots
2. **Use the logs** to troubleshoot issues
3. **Schedule snapshots** before market close
4. **Monitor the enhanced snapshots endpoints** for daily P&L tracking
5. **Use the scheduler endpoints** for batch operations

## 🆘 Getting Help

If you encounter issues:

1. **Check the logs** in the `logs/` directory
2. **Verify system status** with `./start_investment_system.sh status`
3. **Check API endpoints** at http://localhost:8000/docs
4. **Review this guide** for troubleshooting steps

---

**🎉 You're all set! Your investment portfolio tracker now starts with a single command and handles daily operations automatically!**
