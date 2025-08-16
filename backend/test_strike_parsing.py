#!/usr/bin/env python3
"""
Test script to debug strike price parsing
"""
import re

def test_strike_parsing():
    """Test different strike price parsing methods"""
    
    # The option symbol from the user
    symbol = "AAPL250822C00227500"
    
    print(f"Testing strike price parsing for: {symbol}")
    print("=" * 50)
    
    # Parse the symbol
    match = re.match(r'^([A-Z]{1,5})(\d{6})([CP])(\d{8})$', symbol)
    if match:
        underlying = match.group(1)
        date_str = match.group(2)
        option_type = match.group(3)
        strike_cents = match.group(4)
        
        print(f"Underlying: {underlying}")
        print(f"Date: {date_str}")
        print(f"Type: {option_type}")
        print(f"Strike (raw): {strike_cents}")
        
        # Try different strike price interpretations
        print(f"\nStrike price interpretations:")
        
        # Method 1: Divide by 100 (current method)
        strike_1 = float(strike_cents) / 100
        print(f"  Method 1 (÷100):     ${strike_1:,.2f}")
        
        # Method 2: Divide by 1000
        strike_2 = float(strike_cents) / 1000
        print(f"  Method 2 (÷1000):    ${strike_2:,.2f}")
        
        # Method 3: Divide by 10000
        strike_3 = float(strike_cents) / 10000
        print(f"  Method 3 (÷10000):   ${strike_3:,.2f}")
        
        # Method 4: Divide by 100000
        strike_4 = float(strike_cents) / 100000
        print(f"  Method 4 (÷100000):  ${strike_4:,.2f}")
        
        # Method 5: Divide by 1000000
        strike_5 = float(strike_cents) / 1000000
        print(f"  Method 5 (÷1000000): ${strike_5:,.2f}")
        
        # Method 6: Divide by 10000000
        strike_6 = float(strike_cents) / 10000000
        print(f"  Method 6 (÷10000000): ${strike_6:,.2f}")
        
        # Method 7: Divide by 100000000
        strike_7 = float(strike_cents) / 100000000
        print(f"  Method 7 (÷100000000): ${strike_7:,.2f}")
        
        print(f"\nAnalysis:")
        print(f"  AAPL current price: ~$231")
        print(f"  Reasonable strikes: $100-$300")
        
        # Find the most reasonable strike
        reasonable_strikes = []
        for i, strike in enumerate([strike_1, strike_2, strike_3, strike_4, strike_5, strike_6, strike_7]):
            if 50 <= strike <= 500:  # Reasonable range for AAPL
                reasonable_strikes.append((i+1, strike))
        
        if reasonable_strikes:
            print(f"  Most reasonable strikes:")
            for method, strike in reasonable_strikes:
                print(f"    Method {method}: ${strike:.2f}")
        else:
            print(f"  No reasonable strikes found in range $50-$500")
            
    else:
        print("Symbol doesn't match expected pattern")

if __name__ == "__main__":
    test_strike_parsing()
