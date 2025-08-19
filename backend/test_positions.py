import asyncio
from datetime import date
from services.enhanced_snapshots import EnhancedSnapshotsService

async def test_positions():
    service = EnhancedSnapshotsService()
    portfolio_name = "ARU_IB"  # Use an existing portfolio
    test_date = date(2025, 8, 18)
    
    print(f'Testing positions for {portfolio_name} on {test_date}')
    try:
        positions = await service.get_portfolio_positions_for_date(portfolio_name, test_date)
        print(f'Found {len(positions)} positions')
        
        if positions:
            for pos in positions[:3]:  # Show first 3
                print(f'  {pos["symbol"]}: Qty={pos["position_quantity"]}, Cost=${pos["average_cost"]}, Price=${pos["current_price"]}, P&L=${pos["inception_pl"]}')
        
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_positions())
