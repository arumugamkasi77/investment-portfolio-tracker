#!/usr/bin/env python3
"""
Test script to verify portfolio service import
"""
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    print("Testing imports...")
    
    # Test 1: Import portfolio service
    from services.portfolio_service import get_portfolio_positions
    print("✅ Portfolio service imported successfully")
    
    # Test 2: Check if function exists
    if callable(get_portfolio_positions):
        print("✅ get_portfolio_positions is callable")
    else:
        print("❌ get_portfolio_positions is not callable")
        
    # Test 3: Import daily snapshots service
    from services.daily_snapshots import daily_snapshot_service
    print("✅ Daily snapshots service imported successfully")
    
    print("\n✅ All imports successful!")
    
except Exception as e:
    print(f"❌ Import error: {e}")
    import traceback
    traceback.print_exc()
