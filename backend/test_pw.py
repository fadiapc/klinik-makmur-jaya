import asyncio
from app.core.database import AsyncSessionLocal
from app.models.models import User
from sqlalchemy import select
from app.core.security import verify_password

async def main():
    async with AsyncSessionLocal() as db:
        user = (await db.execute(select(User).where(User.email == 'apoteker@klinikmakmur.id'))).scalar_one_or_none()
        if user:
            print(f"User found: {user.email}")
            print(f"Hash: {user.password_hash}")
            is_valid = verify_password("Password123!", user.password_hash)
            print(f"Is Password123! valid? {is_valid}")
        else:
            print("User not found")

if __name__ == '__main__':
    asyncio.run(main())
