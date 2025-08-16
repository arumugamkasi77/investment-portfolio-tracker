#!/usr/bin/env python3
"""
Test script for the specific option AAPL250822C00227500
"""
import asyncio
import sys
import os
from datetime import datetime

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.market_data import market_data_service

async def test_specific_option():
    """Test the specific option from the user's portfolio"""
    
    # The specific option from ARU_IB portfolio
    test_symbol = "AAPL250822C00227500"
    
    print(f"Testing specific option: {test_symbol}")
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
    asyncio.run(test_specific_option())
