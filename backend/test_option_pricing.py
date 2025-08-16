#!/usr/bin/env python3
"""
Test script to debug option pricing functionality
"""
import asyncio
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.market_data import market_data_service

async def test_option_pricing():
    """Test option pricing for various symbols"""
    
    # Test symbols
    test_symbols = [
        "AAPL",  # Stock
        "AAPL251220C00150000",  # Option
        "NVDA",  # Stock
        "NVDA240119P00400000",  # Option
    ]
    
    print("Testing option pricing functionality...")
    print("=" * 50)
    
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
    
    print("\n" + "=" * 50)
    print("Test completed!")

if __name__ == "__main__":
    asyncio.run(test_option_pricing())
