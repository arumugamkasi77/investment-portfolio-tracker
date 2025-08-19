#!/usr/bin/env python3
"""
Script to delete August 18, 2025 snapshots and recreate them properly.
"""

import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import get_daily_snapshots_collection
from datetime import datetime

async def delete_aug_18_snapshots():
    """Delete all snapshots for August 18, 2025."""
    try:
        collection = get_daily_snapshots_collection()
        
        # Create August 18, 2025 datetime
        aug_18 = datetime(2025, 8, 18)
        
        # Delete all snapshots for August 18, 2025
        result = await collection.delete_many({'snapshot_date': aug_18})
        print(f'✅ Deleted {result.deleted_count} snapshots for August 18, 2025')
        
        # Verify deletion
        remaining = await collection.count_documents({'snapshot_date': aug_18})
        print(f'📊 Remaining snapshots for August 18: {remaining}')
        
        if remaining == 0:
            print('🎯 All August 18 snapshots successfully deleted!')
        else:
            print('⚠️  Some snapshots may still exist')
            
    except Exception as e:
        print(f'❌ Error: {e}')

if __name__ == "__main__":
    asyncio.run(delete_aug_18_snapshots())
