#!/usr/bin/env python3
"""
Test script to check all options at $227.50 strike for AAPL Aug 22, 2025
"""
import asyncio
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import yfinance as yf

async def test_aapl_strike_227():
    """Test all options at $227.50 strike for AAPL Aug 22, 2025"""
    
    print("Checking AAPL options at $227.50 strike for Aug 22, 2025...")
    print("=" * 60)
    
    try:
        # Get AAPL ticker
        aapl = yf.Ticker("AAPL")
        
        # Target date and strike
        target_date = "2025-08-22"
        target_strike = 227.50
        
        print(f"Target: {target_date} at ${target_strike} strike")
        print("-" * 40)
        
        # Check if date is available
        if target_date in aapl.options:
            print(f"✅ Date {target_date} is available")
            
            # Get option chain for this date
            option_chain = aapl.option_chain(target_date)
            
            # Look for options at exactly $227.50 strike
            print(f"\nSearching for options at exactly ${target_strike} strike...")
            
            # Check call options
            calls_at_strike = option_chain.calls[option_chain.calls['strike'] == target_strike]
            print(f"\nCall options at ${target_strike}:")
            if not calls_at_strike.empty:
                for i, row in calls_at_strike.iterrows():
                    print(f"  ✅ CALL: ${row['strike']:.2f} | Price: ${row.get('lastPrice', 0):.2f} | Bid: ${row.get('bid', 0):.2f} | Ask: ${row.get('ask', 0):.2f}")
            else:
                print(f"  ❌ No CALL options found at ${target_strike}")
            
            # Check put options
            puts_at_strike = option_chain.puts[option_chain.puts['strike'] == target_strike]
            print(f"\nPut options at ${target_strike}:")
            if not puts_at_strike.empty:
                for i, row in puts_at_strike.iterrows():
                    print(f"  ✅ PUT: ${row['strike']:.2f} | Price: ${row.get('lastPrice', 0):.2f} | Bid: ${row.get('bid', 0):.2f} | Ask: ${row.get('ask', 0):.2f}")
            else:
                print(f"  ❌ No PUT options found at ${target_strike}")
            
            # Look for options around $227.50 strike (±$5)
            print(f"\nSearching for options around ${target_strike} strike (±$5)...")
            calls_around = option_chain.calls[option_chain.calls['strike'].between(target_strike - 5, target_strike + 5)]
            puts_around = option_chain.puts[option_chain.puts['strike'].between(target_strike - 5, target_strike + 5)]
            
            print(f"\nCall options around ${target_strike}:")
            if not calls_around.empty:
                for i, row in calls_around.iterrows():
                    print(f"  CALL: ${row['strike']:.2f} | Price: ${row.get('lastPrice', 0):.2f}")
            else:
                print("  No call options found around this strike")
                
            print(f"\nPut options around ${target_strike}:")
            if not puts_around.empty:
                for i, row in puts_around.iterrows():
                    print(f"  PUT: ${row['strike']:.2f} | Price: ${row.get('lastPrice', 0):.2f}")
            else:
                print("  No put options found around this strike")
                
        else:
            print(f"❌ Date {target_date} is NOT available")
            print("Available dates are:")
            for date in aapl.options[:10]:
                print(f"  {date}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("Test completed!")

if __name__ == "__main__":
    asyncio.run(test_aapl_strike_227())
