import asyncpg
import datetime
import os

WELCOME_CREDITS = 50
REFILL_AMOUNT = 100
REFILL_INTERVAL = 12 * 60 * 60  # 12 hours in seconds

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
                await conn.execute(
                    "INSERT INTO user_credits (user_id, credits, last_refill, initial_bonus_given) VALUES ($1, $2, $3, TRUE)",
                    user_id, amount, datetime.datetime.utcnow()
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

            now = datetime.datetime.utcnow()

            # ✅ New user — give welcome credits
            if not row:
                await conn.execute(
                    "INSERT INTO user_credits (user_id, credits, last_refill, initial_bonus_given) VALUES ($1, $2, $3, TRUE)",
                    user_id, WELCOME_CREDITS, now
                )
                return f"🎉 Welcome! You've received {WELCOME_CREDITS} credits to start chatting. Enjoy 😉"

            credits = row["credits"]
            last_refill = row["last_refill"]

            # 🔧 Ensure datetime object
            if isinstance(last_refill, datetime.date) and not isinstance(last_refill, datetime.datetime):
                last_refill = datetime.datetime.combine(last_refill, datetime.datetime.min.time())

            # 🚫 Already has credits — no refill
            if credits > 0:
                return None

            # 🔒 Prevent refill if less than 12h has passed
            elapsed_seconds = (now - last_refill).total_seconds()
            if elapsed_seconds < REFILL_INTERVAL:
                return None  # ❌ Not enough time passed

            # ✅ Time-based refill (12h after hitting 0)
            await conn.execute(
                "UPDATE user_credits SET credits = $1, last_refill = $2 WHERE user_id = $3",
                REFILL_AMOUNT, now, user_id
            )
            return f"💖 You've received {REFILL_AMOUNT} free credits! Welcome back 😘"
