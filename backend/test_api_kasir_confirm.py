import asyncio
import httpx
from app.core.security import create_access_token

async def test_api():
    # Create token for kasir (user_id=2, wait we found it's actually kasir_id)
    # The actual order ID for ORD-20260605-0007 was 13 in the test script.
    kasir_id = 28 # From the test script output
    order_id = 13 # From the test script output

    token = create_access_token(data={"sub": str(kasir_id)})
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"http://localhost:8000/api/v1/orders/{order_id}/kasir/confirm",
            headers={"Authorization": f"Bearer {token}"}
        )
        print(response.status_code)
        print(response.text)

if __name__ == "__main__":
    asyncio.run(test_api())
