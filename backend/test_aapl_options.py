#!/usr/bin/env python3
"""
Test script to check what AAPL options are available in Yahoo Finance
"""
import asyncio
import sys
import os
from datetime import datetime

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import yfinance as yf

async def test_aapl_options():
    """Test what AAPL options are available in Yahoo Finance"""
    
    print("Checking AAPL options availability in Yahoo Finance...")
    print("=" * 60)
    
    try:
        # Get AAPL ticker
        aapl = yf.Ticker("AAPL")
        
        # Get available expiration dates
        print("Available expiration dates:")
        available_dates = aapl.options
        for i, date in enumerate(available_dates[:10]):  # Show first 10
            print(f"  {i+1}. {date}")
        
        if len(available_dates) > 10:
            print(f"  ... and {len(available_dates) - 10} more dates")
        
        # Check if our target date (2025-08-22) is available
        target_date = "2025-08-22"
        if target_date in available_dates:
            print(f"\n✅ Target date {target_date} is available!")
            
            # Get option chain for this date
            print(f"\nFetching option chain for {target_date}...")
            option_chain = aapl.option_chain(target_date)
            
            print(f"\nCall options (first 10):")
            if not option_chain.calls.empty:
                for i, row in option_chain.calls.head(10).iterrows():
                    strike = row['strike']
                    last_price = row.get('lastPrice', 0)
                    bid = row.get('bid', 0)
                    ask = row.get('ask', 0)
                    volume = row.get('volume', 0)
                    print(f"  Strike: ${strike:8.2f} | Price: ${last_price:6.2f} | Bid: ${bid:6.2f} | Ask: ${ask:6.2f} | Vol: {volume}")
            else:
                print("  No call options found")
            
            print(f"\nPut options (first 10):")
            if not option_chain.puts.empty:
                for i, row in option_chain.puts.head(10).iterrows():
                    strike = row['strike']
                    last_price = row.get('lastPrice', 0)
                    bid = row.get('bid', 0)
                    ask = row.get('ask', 0)
                    volume = row.get('volume', 0)
                    print(f"  Strike: ${strike:8.2f} | Price: ${last_price:6.2f} | Bid: ${bid:6.2f} | Ask: ${ask:6.2f} | Vol: {volume}")
            else:
                print("  No put options found")
            
            # Look for options around $2275 strike
            print(f"\nLooking for options around $2275 strike...")
            calls_around_strike = option_chain.calls[option_chain.calls['strike'].between(2270, 2280)]
            puts_around_strike = option_chain.puts[option_chain.puts['strike'].between(2270, 2280)]
            
            if not calls_around_strike.empty:
                print(f"Call options around $2275:")
                for i, row in calls_around_strike.iterrows():
                    strike = row['strike']
                    last_price = row.get('lastPrice', 0)
                    print(f"  Strike: ${strike:.2f} | Price: ${last_price:.2f}")
            else:
                print("No call options found around $2275 strike")
                
            if not puts_around_strike.empty:
                print(f"Put options around $2275:")
                for i, row in puts_around_strike.iterrows():
                    strike = row['strike']
                    last_price = row.get('lastPrice', 0)
                    print(f"  Strike: ${strike:.2f} | Price: ${last_price:.2f}")
            else:
                print("No put options found around $2275 strike")
                
        else:
            print(f"\n❌ Target date {target_date} is NOT available")
            print("Available dates are:")
            for date in available_dates:
                print(f"  {date}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("Test completed!")

if __name__ == "__main__":
    asyncio.run(test_aapl_options())
