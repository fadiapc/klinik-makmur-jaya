import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.repositories.order_repository import OrderRepository
from app.services.order_service import OrderService
from app.models.models import User
from app.schemas.order import PrescriptionReviewRequest
import traceback

async def test_service():
    async with AsyncSessionLocal() as db:
        service = OrderService(db)
        
        # Get apoteker
        from sqlalchemy import select
        apoteker = (await db.execute(select(User).where(User.email == "apoteker@klinikmakmur.id"))).scalar_one()
        
        # We need a dummy request object. The service only uses request.client.host and request.headers.get("user-agent")
        class DummyClient:
            host = "127.0.0.1"
        class DummyRequest:
            client = DummyClient()
            headers = {"user-agent": "test"}
            
        print("Apoteker ID:", apoteker.id)
        
        try:
            # Let's try to approve order 13
            res = await service.review_prescription(
                order_id=13,
                data=PrescriptionReviewRequest(action="approved"),
                current_user=apoteker,
                request=DummyRequest()
            )
            print("Success!", res.order_code)
        except Exception as e:
            print("Crash!")
            traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(test_service())
