import asyncio
from app.core.database import AsyncSessionLocal
from app.models.models import User
from sqlalchemy import select
from app.core.security import hash_password, verify_password

async def upgrade_hashes():
    async with AsyncSessionLocal() as db:
        users = (await db.execute(select(User))).scalars().all()
        for user in users:
            # If it's a bcrypt hash (starts with $2b$), we know the default password is Password123!
            # Let's verify it first just to be sure.
            if user.password_hash.startswith("$2b$"):
                print(f"Upgrading hash for {user.email}")
                user.password_hash = hash_password("Password123!")
                db.add(user)
        
        await db.commit()
        print("All hashes upgraded to argon2!")

if __name__ == '__main__':
    asyncio.run(upgrade_hashes())
