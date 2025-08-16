@echo off
setlocal enabledelayedexpansion

REM Investment Portfolio Tracker - Complete Startup Script for Windows
REM This script starts the entire system: Backend, Frontend, and Daily Snapshots

echo 🚀 Starting Investment Portfolio Tracker System...
echo ==================================================

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python 3.9+ and add it to your PATH
    pause
    exit /b 1
)

REM Check if Node.js is available
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js is not installed or not in PATH
    echo Please install Node.js 16+ and add it to your PATH
    pause
    exit /b 1
)

REM Check if MongoDB is running
netstat -an | findstr ":27017" >nul
if errorlevel 1 (
    echo ⚠️  MongoDB is not running on port 27017
    echo Please start MongoDB before running this script
    echo You can start MongoDB with: mongod
    pause
)

REM Create logs directory
if not exist "logs" mkdir logs

REM Function to check if port is in use
:check_port
set port=%1
netstat -an | findstr ":%port%" >nul
if not errorlevel 1 (
    echo ❌ Port %port% is already in use!
    exit /b 1
) else (
    echo ✅ Port %port% is available
    exit /b 0
)

REM Check backend port
call :check_port 8000
if errorlevel 1 (
    echo Backend port 8000 is already in use!
    pause
    exit /b 1
)

REM Check frontend port
call :check_port 3000
if errorlevel 1 (
    echo Frontend port 3000 is already in use!
    pause
    exit /b 1
)

echo.
echo 🔧 Starting Backend...

REM Start backend
cd backend

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install/update dependencies
echo Installing/updating dependencies...
pip install -r requirements.txt

REM Start backend in background
echo Starting backend server...
start "Backend Server" cmd /c "python main.py > ..\logs\backend.log 2>&1"

cd ..

REM Wait for backend to be ready
echo Waiting for backend to be ready...
:wait_backend
timeout /t 2 /nobreak >nul
curl -s "http://localhost:8000/health" >nul 2>&1
if errorlevel 1 (
    echo -n .
    goto wait_backend
)
echo ✅ Backend is ready!

echo.
echo 🎨 Starting Frontend...

REM Start frontend
cd frontend

REM Install/update dependencies
echo Installing/updating dependencies...
npm install

REM Start frontend in background
echo Starting frontend server...
start "Frontend Server" cmd /c "npm start > ..\logs\frontend.log 2>&1"

cd ..

REM Wait for frontend to be ready
echo Waiting for frontend to be ready...
timeout /t 10 /nobreak >nul

echo.
echo 📅 Setting up Daily Snapshots...

REM Wait for backend to be fully ready
timeout /t 5 /nobreak >nul

REM Create snapshots for today
echo Creating daily snapshots...
curl -s -X POST "http://localhost:8000/scheduler/quick-daily-snapshots" >nul 2>&1
if not errorlevel 1 (
    echo ✅ Daily snapshots created successfully!
) else (
    echo ⚠️  Warning: Could not create daily snapshots (backend might still be starting)
)

REM Schedule tomorrow's snapshots
echo Scheduling tomorrow's snapshots...
curl -s -X POST "http://localhost:8000/scheduler/schedule-daily-snapshots?delay_minutes=1440" >nul 2>&1
if not errorlevel 1 (
    echo ✅ Tomorrow's snapshots scheduled!
) else (
    echo ⚠️  Warning: Could not schedule tomorrow's snapshots
)

echo.
echo 🎉 System started successfully!
echo ==================================================

REM Show system status
echo.
echo 📊 System Status:
echo ==================
curl -s "http://localhost:8000/health" >nul 2>&1
if not errorlevel 1 (
    echo ✅ Backend: Running on http://localhost:8000
    echo    📚 API Docs: http://localhost:8000/docs
) else (
    echo ❌ Backend: Not running
)

curl -s "http://localhost:3000" >nul 2>&1
if not errorlevel 1 (
    echo ✅ Frontend: Running on http://localhost:3000
) else (
    echo ❌ Frontend: Not running
)

echo.
echo 💡 Daily Operations:
echo ===================
echo • Daily snapshots are created automatically on startup
echo • Tomorrow's snapshots are scheduled automatically
echo • Use the scheduler endpoints to manage daily operations
echo • Visit http://localhost:8000/docs for API documentation
echo • Visit http://localhost:3000 for the web interface

echo.
echo 📝 Logs are available in the 'logs' directory
echo 🔄 To restart: Run this script again
echo 🛑 To stop: Close the command windows that opened

echo.
echo Press any key to exit...
pause >nul
