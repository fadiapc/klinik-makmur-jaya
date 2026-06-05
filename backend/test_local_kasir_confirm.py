import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.services.order_service import OrderService
from fastapi import Request
import traceback
from sqlalchemy import text

class MockClient:
    host = "127.0.0.1"

class MockRequest:
    client = MockClient()
    headers = {"user-agent": "test-script"}

class MockRole:
    name = "kasir"

class MockUser:
    role = MockRole()
    # We will set id dynamically

async def run_test():
    async with AsyncSessionLocal() as db:
        res = await db.execute(text("SELECT id FROM users WHERE role_id = (SELECT id FROM roles WHERE name='kasir') LIMIT 1"))
        row = res.fetchone()
        if not row:
            print("No kasir found")
            return
        kasir_id = row[0]
        print(f"Kasir User ID: {kasir_id}")
        
        service = OrderService(db)
        user = MockUser()
        user.id = kasir_id
        request = MockRequest()
        
        # Get ID by order_code
        res = await db.execute(text("SELECT id FROM orders WHERE order_code='ORD-20260605-0007'"))
        row = res.fetchone()
        if not row:
            print("Order not found")
            return
            
        order_id = row[0]
        print(f"Found order ID: {order_id}")
        
        try:
            order = await service.kasir_confirm_payment(order_id, user, request)
            print("SUCCESS! Status is now:", order.status)
        except Exception as e:
            print("ERROR:")
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_test())
