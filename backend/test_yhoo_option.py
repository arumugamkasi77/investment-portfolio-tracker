#!/usr/bin/env python3
"""
Test script for the YHOO option symbol YHOO150416C00030000
"""
import asyncio
import sys
import os
from datetime import datetime

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.market_data import market_data_service

async def test_yhoo_option():
    """Test the YHOO option from the user's example"""
    
    # The specific option from the user's example
    test_symbol = "YHOO150416C00030000"
    
    print(f"Testing YHOO option: {test_symbol}")
    print("=" * 50)
    
    try:
        # Check if it's detected as an option
        is_option = market_data_service._is_option_symbol(test_symbol)
        print(f"Is option: {is_option}")
        
        if is_option:
            # Parse option symbol
            parsed = market_data_service._parse_option_symbol(test_symbol)
            print(f"Parsed: {parsed}")
            
            if parsed:
                # Check expiration status
                status = market_data_service._get_option_expiration_status(parsed['expiration'])
                print(f"Status: {status}")
                
                # Show expiration details
                print(f"Expiration: {parsed['expiration'].strftime('%Y-%m-%d')}")
                print(f"Days until expiration: {(parsed['expiration'].date() - datetime.now().date()).days}")
                
                # Show strike price details
                print(f"Strike: ${parsed['strike']:.2f}")
        
        # Get price
        print(f"\nFetching price for: {test_symbol}")
        price_data = await market_data_service.get_stock_price(test_symbol)
        
        if price_data:
            print(f"✅ Price: ${price_data['price']:.2f}")
            print(f"Source: {price_data['source']}")
            if 'option_details' in price_data:
                print(f"Option details: {price_data['option_details']}")
        else:
            print(f"❌ Price: No data available")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 50)
    print("Test completed!")

if __name__ == "__main__":
    asyncio.run(test_yhoo_option())
