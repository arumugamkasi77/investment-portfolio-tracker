#!/usr/bin/env python3
"""
Test script with valid (non-expired) option symbols
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.market_data import market_data_service

async def test_valid_options():
    """Test option pricing with valid (non-expired) symbols"""
    
    # Generate valid option symbols for testing
    today = datetime.now()
    
    # Test with options expiring in the next few months
    test_symbols = [
        "AAPL",  # Stock
        "NVDA",  # Stock
        # Generate valid option symbols (you can modify these dates)
        f"AAPL{(today + timedelta(days=30)).strftime('%d%m%y').upper()}C00150000",  # AAPL call expiring in ~30 days
        f"NVDA{(today + timedelta(days=60)).strftime('%d%m%y').upper()}P00180000",  # NVDA put expiring in ~60 days
    ]
    
    print("Testing option pricing with VALID (non-expired) symbols...")
    print("=" * 60)
    
    for symbol in test_symbols:
        print(f"\nTesting symbol: {symbol}")
        try:
            # Check if it's detected as an option
            is_option = market_data_service._is_option_symbol(symbol)
            print(f"  Is option: {is_option}")
            
            if is_option:
                # Parse option symbol
                parsed = market_data_service._parse_option_symbol(symbol)
                print(f"  Parsed: {parsed}")
                
                # Check expiration status
                if parsed:
                    status = market_data_service._get_option_expiration_status(parsed['expiration'])
                    print(f"  Status: {status}")
            
            # Get price
            price_data = await market_data_service.get_stock_price(symbol)
            if price_data:
                print(f"  Price: ${price_data['price']:.2f}")
                print(f"  Source: {price_data['source']}")
                if 'option_details' in price_data:
                    print(f"  Option details: {price_data['option_details']}")
            else:
                print(f"  Price: No data available")
                
        except Exception as e:
            print(f"  Error: {e}")
    
    print("\n" + "=" * 60)
    print("Test completed!")
    print("\nNote: If options show $0.00, they might be:")
    print("1. Expired (check the expiration date)")
    print("2. Not available in Yahoo Finance option chains")
    print("3. Have invalid strike prices or expiration dates")

if __name__ == "__main__":
    asyncio.run(test_valid_options())
