#!/usr/bin/env python3
"""
Test different date format interpretations for option symbols
"""
from datetime import datetime

def test_date_formats(date_str):
    """Test different date format interpretations"""
    print(f"Testing date string: {date_str}")
    print("=" * 40)
    
    # Extract components
    d1, d2 = int(date_str[0:2]), int(date_str[2:4])
    y1, y2 = int(date_str[4:6]), int(date_str[4:6])
    
    # Try different interpretations
    interpretations = [
        ("DDMMYY", d1, d2, 2000 + y1),
        ("MMDDYY", d2, d1, 2000 + y1),
        ("YYMMDD", 2000 + y1, d1, d2),
        ("YYDDMM", 2000 + y1, d2, d1),
        ("DDMMYY (19XX)", d1, d2, 1900 + y1),
        ("MMDDYY (19XX)", d2, d1, 1900 + y1),
    ]
    
    current_date = datetime.now().date()
    
    for format_name, day, month, year in interpretations:
        try:
            test_date = datetime(year, month, day).date()
            days_diff = (test_date - current_date).days
            
            status = "FUTURE" if days_diff > 0 else "TODAY" if days_diff == 0 else "PAST"
            
            print(f"{format_name:12} → {year:04d}-{month:02d}-{day:02d} ({status}, {days_diff:+d} days)")
            
            # Check if this looks like a reasonable option expiration
            if -30 <= days_diff <= 3650:  # Within 30 days past to 10 years future
                print(f"           ⭐ REASONABLE for options!")
            
        except ValueError:
            print(f"{format_name:12} → INVALID DATE")
    
    print()

# Test the specific date from your option
test_date_formats("250822")

# Test a few more examples
print("Other examples:")
test_date_formats("251220")  # Dec 25, 2020
test_date_formats("240119")  # Jan 24, 2019
