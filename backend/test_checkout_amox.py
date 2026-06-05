import asyncio
import traceback
from app.core.database import AsyncSessionLocal
from app.services.order_service import OrderService
from app.schemas.order import CheckoutRequest, CheckoutItemRequest
from app.models.models import User, Role, OrderType, PaymentMethod, Product
from sqlalchemy import select

class DummyClient:
    host = "127.0.0.1"

class DummyRequest:
    client = DummyClient()
    headers = {"user-agent": "test"}

async def main():
    async with AsyncSessionLocal() as db:
        try:
            # get any patient user
            user = (await db.execute(select(User).where(User.email == 'andi@example.com'))).scalar_one()
            
            # get Amoxicillin 500mg
            amox = (await db.execute(select(Product).where(Product.name == 'Amoxicillin 500mg'))).scalar_one()
            
            service = OrderService(db)
            req = CheckoutRequest(
                items=[CheckoutItemRequest(product_id=amox.id, quantity=1)],
                payment_method=PaymentMethod.TRANSFER,
                notes="test"
            )
            
            print("Trying to checkout...")
            order = await service.checkout(req, user, DummyRequest())
            print("Checkout success! Order ID:", order.id)
            print("Order Code:", order.order_code)
            
            await db.commit()
            
        except Exception as e:
            traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(main())
