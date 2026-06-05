"""
expiry_service.py - Periodic background check for expiring stock batches.
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import AsyncSessionLocal
from app.models.models import StockBatch
from app.services.notification_service import notifier

logger = logging.getLogger(__name__)

async def check_expiring_stock():
    """
    Check for batches expiring in exactly 90, 60, or 30 days.
    Generates notifications for Admin and Apoteker.
    """
    logger.info("Running scheduled expiry check...")
    
    now = datetime.now(timezone.utc)
    target_days = [30, 60, 90]
    
    async with AsyncSessionLocal() as session:
        # We need to find batches where the expiry date is roughly `now + X days`.
        # To avoid sending notifications multiple times, we can check if it expires within the exact day
        # or we can just send it if it falls into the bucket and we haven't sent it yet.
        # Since we don't have a "notification_sent" flag per batch, we'll just alert anything that
        # crosses the threshold. For simplicity, we alert anything expiring <= 90 days if it's not expired yet.
        # But wait, the user specifically asked for "30 hari, 60 hari, 90 hari".
        # Let's check ranges: 89-90, 59-60, 29-30.
        
        result = await session.execute(
            select(StockBatch).options(selectinload(StockBatch.product)).where(StockBatch.current_stock > 0)
        )
        batches = result.scalars().all()
        
        for batch in batches:
            if not batch.expiry_date:
                continue
                
            # If naive, add UTC timezone
            expiry = batch.expiry_date
            if expiry.tzinfo is None:
                expiry = expiry.replace(tzinfo=timezone.utc)
                
            delta = expiry - now
            days_left = delta.days
            
            if days_left in target_days:
                warn_msg = f"Batch {batch.batch_number} untuk {batch.product.name} akan kadaluarsa dalam {days_left} hari ({expiry.strftime('%Y-%m-%d')}). Sisa stok: {batch.current_stock}."
                await notifier.notify_role("admin", "Peringatan Kadaluarsa", warn_msg, level="warning", type="expiry", link="/admin/products")
                await notifier.notify_role("apoteker", "Peringatan Kadaluarsa", warn_msg, level="warning", type="expiry", link="/apoteker/produk")


async def expiry_check_loop():
    """
    A continuous loop that runs once every 24 hours.
    """
    while True:
        try:
            await check_expiring_stock()
        except Exception as e:
            logger.error(f"Error in expiry_check_loop: {e}")
        
        # Sleep for 24 hours
        await asyncio.sleep(24 * 60 * 60)
