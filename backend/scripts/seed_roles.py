"""
seed_roles.py — One-time script to seed the roles and a default admin account.

Run ONCE after `alembic upgrade head`:
    python scripts/seed_roles.py

What this does:
  1. Creates the four roles: admin, apoteker, kasir, pasien
  2. Creates a default Admin account (change credentials immediately in production!)

The register endpoint depends on the 'pasien' role existing.
The get_current_user dependency depends on roles being populated.
"""

import asyncio
import sys
from pathlib import Path

# Allow running from project root: python scripts/seed_roles.py
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.models.models import Role, User


ROLES = [
    {
        "name": "admin",
        "description": "System administrator — full access to all modules",
    },
    {
        "name": "apoteker",
        "description": "Pharmacist — manages prescriptions, stock, and drug information",
    },
    {
        "name": "kasir",
        "description": "Cashier — handles POS transactions and counter orders",
    },
    {
        "name": "pasien",
        "description": "Patient / Customer — places online orders and uploads prescriptions",
    },
]

DEFAULT_ADMIN = {
    "name": "System Admin",
    "email": "admin@klinikmakmurjaya.id",
    "password": "Admin@Klinik123!",   # ← CHANGE THIS IMMEDIATELY in production
    "phone": None,
}


async def seed() -> None:
    async with AsyncSessionLocal() as db:
        print("─" * 50)
        print("Seeding roles table...")

        role_map: dict[str, Role] = {}
        for role_data in ROLES:
            result = await db.execute(
                select(Role).where(Role.name == role_data["name"])
            )
            role = result.scalar_one_or_none()
            if role is None:
                role = Role(**role_data)
                db.add(role)
                await db.flush()
                print(f"  ✅ Created role: {role.name}")
            else:
                print(f"  ⏭  Role already exists: {role.name}")
            role_map[role.name] = role

        print("\nSeeding default admin account...")
        result = await db.execute(
            select(User).where(User.email == DEFAULT_ADMIN["email"])
        )
        admin = result.scalar_one_or_none()
        if admin is None:
            admin = User(
                name=DEFAULT_ADMIN["name"],
                email=DEFAULT_ADMIN["email"],
                password_hash=hash_password(DEFAULT_ADMIN["password"]),
                role_id=role_map["admin"].id,
                phone=DEFAULT_ADMIN["phone"],
                is_verified=True,   # Admin is pre-verified
                is_active=True,
            )
            db.add(admin)
            await db.flush()
            print(f"  ✅ Admin created: {admin.email}")
            print(f"  ⚠️  Default password: {DEFAULT_ADMIN['password']}")
            print("  ⚠️  CHANGE THIS PASSWORD IMMEDIATELY in production!")
        else:
            print(f"  ⏭  Admin already exists: {admin.email}")

        await db.commit()
        print("\n✅ Seed completed successfully.")
        print("─" * 50)


if __name__ == "__main__":
    asyncio.run(seed())
