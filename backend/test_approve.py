import httpx
import asyncio

async def test_approve():
    async with httpx.AsyncClient() as client:
        # First login as apoteker
        login_res = await client.post(
            "http://localhost:8000/api/v1/auth/login",
            json={
                "email": "apoteker@klinikmakmur.id",
                "password": "Password123!"
            }
        )
        if login_res.status_code != 200:
            print("Login failed!", login_res.text)
            return
            
        token = login_res.json()["access_token"]
        
        orders_res = await client.get(
            "http://localhost:8000/api/v1/orders",
            headers={"Authorization": f"Bearer {token}"}
        )
        orders = orders_res.json()["items"]
        pending = [o for o in orders if o["status"] == "menunggu_verifikasi_resep"]
        if not pending:
            print("No pending prescriptions")
            return
            
        target_id = pending[0]["id"]
        print(f"Approving order {target_id}")
        res = await client.patch(
            f"http://localhost:8000/api/v1/orders/{target_id}/prescription/review",
            json={"action": "approved"},
            headers={"Authorization": f"Bearer {token}"}
        )
        print("Status Code:", res.status_code)
        print("Response:", res.text)

if __name__ == '__main__':
    asyncio.run(test_approve())
