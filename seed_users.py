"""
Seed script: create 1 user per role (admin, user).
Run: source venv/bin/activate && python seed_users.py
"""
import asyncio
import os
import bcrypt
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://root:password@localhost/fintrack")

# ─── Seed users ────────────────────────────────────────────────────────────────
USERS = [
    {
        "username":     "adminuser",
        "email":        "admin@fintrack.com",
        "phone_number": "+628100000001",
        "password":     "Admin@1234",
        "role":         "admin",
        "tier":         "premium",
    },
    {
        "username":     "regularuser",
        "email":        "user@fintrack.com",
        "phone_number": "+628100000002",
        "password":     "User@1234",
        "role":         "user",
        "tier":         "regular",
    },
]


def hash_password(password: str) -> str:
    pwd_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


async def seed():
    engine = create_async_engine(DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        for u in USERS:
            # Check if user already exists
            res = await conn.execute(
                text("SELECT id FROM users WHERE username = :uname LIMIT 1"),
                {"uname": u["username"]},
            )
            existing = res.fetchone()
            if existing:
                print(f"⚠  Skipped  {u['username']} — already exists (id={existing[0]})")
                continue

            hashed = hash_password(u["password"])
            await conn.execute(
                text("""
                    INSERT INTO users
                        (username, email, phone_number, hashed_password, role, tier, is_active, created_at, updated_at)
                    VALUES
                        (:username, :email, :phone, :hashed, :role, :tier, true, NOW(), NOW())
                """),
                {
                    "username": u["username"],
                    "email":    u["email"],
                    "phone":    u["phone_number"],
                    "hashed":   hashed,
                    "role":     u["role"],
                    "tier":     u["tier"],
                },
            )
            print(f"✓  Created  {u['role']:10}  {u['username']}  /  {u['email']}  /  {u['phone_number']}  (password: {u['password']})")

    print("\nDone.")


if __name__ == "__main__":
    asyncio.run(seed())
