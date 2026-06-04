import asyncio
from sqlalchemy import update
from app.core.database import AsyncSessionLocal
from app.models.models import User
from app.core.security import hash_password

async def main():
    async with AsyncSessionLocal() as s:
        h = hash_password('Admin@Klinik123!')
        await s.execute(update(User).where(User.email == 'admin@klinikmakmurjaya.id').values(password_hash=h))
        await s.commit()
    print('Updated password hash to argon2!')

if __name__ == '__main__':
    asyncio.run(main())
