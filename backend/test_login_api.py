import httpx
import asyncio

async def test_login():
    async with httpx.AsyncClient() as client:
        res = await client.post(
            "http://localhost:8000/api/v1/auth/login",
            json={
                "email": "apoteker@klinikmakmur.id",
                "password": "Password123!"
            }
        )
        print("Status Code:", res.status_code)
        print("Response:", res.text)

if __name__ == '__main__':
    asyncio.run(test_login())
