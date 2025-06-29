import asyncpg
import datetime
import os

WELCOME_CREDITS = 50  # 🔄 Changed from 300 → 50 for testing
REFILL_AMOUNT = 100
REFILL_INTERVAL = 12 * 60 * 60  # 12 hours (in seconds)

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
            row = await conn.fetchrow("SELECT credits FROM user_credits WHERE user_id = $1", user_id)
            return row["credits"] if row else 0

    async def add_credits(self, user_id: int, amount: int):
        async with self.pool.acquire() as conn:
            exists = await conn.fetchval("SELECT EXISTS (SELECT 1 FROM user_credits WHERE user_id = $1)", user_id)
            if exists:
                await conn.execute(
                    "UPDATE user_credits SET credits = credits + $1 WHERE user_id = $2", amount, user_id
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
                "UPDATE user_credits SET credits = credits - $1 WHERE user_id = $2", amount, user_id
            )
        return True

    async def deduct_credits(self, user_id: int, amount: int):
        async with self.pool.acquire() as conn:
            await conn.execute(
                "UPDATE user_credits SET credits = credits - $1 WHERE user_id = $2 AND credits >= $1",
                amount,
                user_id
            )

    async def refill_if_due(self, user_id: int):
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT credits, last_refill, initial_bonus_given FROM user_credits WHERE user_id = $1", user_id
            )

            now = datetime.datetime.utcnow()

            # ➤ First time user — create new row with 50 welcome credits
            if row is None:
                await conn.execute(
                    "INSERT INTO user_credits (user_id, credits, last_refill, initial_bonus_given) VALUES ($1, $2, $3, TRUE)",
                    user_id, WELCOME_CREDITS, now
                )
                return f"🎉 Welcome! You've received {WELCOME_CREDITS} Ava Credits to start chatting. Enjoy 😉"

            credits = row["credits"]
            last_refill = row["last_refill"]
            initial_bonus_given = row["initial_bonus_given"]

            print(f"📋 User {user_id} — Credits: {credits}, Bonus Given: {initial_bonus_given} ({type(initial_bonus_given)})")

            # ➤ Already has credits, don’t give anything
            if credits > 0:
                return None

            # ➤ Already got the welcome bonus — only allow 12h refill
            if initial_bonus_given:
                time_since = (now - last_refill).total_seconds()
                if time_since >= REFILL_INTERVAL:
                    await conn.execute(
                        "UPDATE user_credits SET credits = $1, last_refill = $2 WHERE user_id = $3",
                        REFILL_AMOUNT, now, user_id
                    )
                    return f"💖 You’ve received {REFILL_AMOUNT} free Ava Credits! Enjoy your time again 😘"
                else:
                    return None

            # 🔁 Edge case fallback: somehow has 0 credits and bonus = false
            await conn.execute(
                "UPDATE user_credits SET credits = $1, last_refill = $2, initial_bonus_given = TRUE WHERE user_id = $3",
                WELCOME_CREDITS, now, user_id
            )
            return f"🎉 You’ve received {WELCOME_CREDITS} Ava Credits to start chatting. Enjoy 😉"
