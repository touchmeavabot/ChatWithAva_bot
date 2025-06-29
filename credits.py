import asyncpg
import datetime
import os

WELCOME_CREDITS = 300           # New user bonus
REFILL_AMOUNT = 100             # Daily refill
# We no longer use REFILL_INTERVAL — day-based refill

class CreditManager:
    def __init__(self):
        self.pool = None

    async def connect(self):
        db_url = os.getenv("DATABASE_URL")
        print("🔌 Connecting to:", db_url)
        if not db_url:
            raise ValueError("❌ DATABASE_URL is not set in environment!")
        self.pool = await asyncpg.create_pool(dsn=db_url)

    async def get_credits(self, user_id: int) -> int:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT credits FROM user_credits WHERE user_id = $1", user_id
            )
            return row["credits"] if row else 0

    async def add_credits(self, user_id: int, amount: int):
        async with self.pool.acquire() as conn:
            exists = await conn.fetchval(
                "SELECT EXISTS (SELECT 1 FROM user_credits WHERE user_id = $1)", user_id
            )
            if exists:
                await conn.execute(
                    "UPDATE user_credits SET credits = credits + $1 WHERE user_id = $2",
                    amount, user_id
                )
            else:
                today = datetime.date.today()
                await conn.execute(
                    "INSERT INTO user_credits (user_id, credits, last_refill, initial_bonus_given) VALUES ($1, $2, $3, TRUE)",
                    user_id, amount, today
                )

    async def charge_credits(self, user_id: int, amount: int) -> bool:
        credits = await self.get_credits(user_id)
        if credits < amount:
            return False
        async with self.pool.acquire() as conn:
            await conn.execute(
                "UPDATE user_credits SET credits = credits - $1 WHERE user_id = $2",
                amount, user_id
            )
        return True

    async def deduct_credits(self, user_id: int, amount: int):
        async with self.pool.acquire() as conn:
            await conn.execute(
                "UPDATE user_credits SET credits = credits - $1 WHERE user_id = $2 AND credits >= $1",
                amount, user_id
            )

    async def refill_if_due(self, user_id: int):
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT credits, last_refill FROM user_credits WHERE user_id = $1", user_id
            )

            today = datetime.date.today()

            # ✅ New user — insert with welcome bonus
            if not row:
                await conn.execute(
                    "INSERT INTO user_credits (user_id, credits, last_refill, initial_bonus_given) VALUES ($1, $2, $3, TRUE)",
                    user_id, WELCOME_CREDITS, today
                )
                return f"🎉 Welcome! You've received {WELCOME_CREDITS} credits to start chatting. Enjoy 😉"

            credits = row["credits"]
            last_refill = row["last_refill"]

            # ✅ No refill if user still has credits
            if credits > 0:
                return None

            # ❌ Already refilled today
            if last_refill == today:
                return None

            # ✅ Give refill
            await conn.execute(
                "UPDATE user_credits SET credits = $1, last_refill = $2 WHERE user_id = $3",
                REFILL_AMOUNT, today, user_id
            )
            return f"💖 You've received {REFILL_AMOUNT} free credits! Welcome back 😘"
