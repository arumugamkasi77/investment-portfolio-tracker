import asyncio
from datetime import date
from services.enhanced_snapshots import EnhancedSnapshotsService

async def test_snapshot_creation():
    service = EnhancedSnapshotsService()
    test_date = date(2025, 8, 18)
    
    print(f'Testing snapshot creation for {test_date}')
    try:
        result = await service.create_simple_daily_snapshot(test_date)
        print(f'Snapshots created: {len(result)}')
        
        # Check one snapshot to see if P&L is calculated correctly
        if result:
            first_snapshot = result[0]
            print(f'First snapshot: {first_snapshot["symbol"]}')
            print(f'  Portfolio: {first_snapshot["portfolio_name"]}')
            print(f'  Quantity: {first_snapshot["quantity"]}')
            print(f'  Average Cost: ${first_snapshot["average_cost"]}')
            print(f'  Current Price: ${first_snapshot["current_price"]}')
            print(f'  P&L: ${first_snapshot["inception_pl"]}')
            
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_snapshot_creation())
