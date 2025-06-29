import asyncpg
import datetime
import os

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
            exists = await conn.fetchval(
                "SELECT EXISTS (SELECT 1 FROM user_credits WHERE user_id = $1)", user_id
            )
            if exists:
                await conn.execute(
                    "UPDATE user_credits SET credits = credits + $1 WHERE user_id = $2", amount, user_id
                )
            else:
                await conn.execute(
                    "INSERT INTO user_credits (user_id, credits, last_refill, initial_bonus_given) VALUES ($1, $2, $3, $4)",
                    user_id, amount, datetime.datetime.utcnow(), True
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

            # ✅ New user – create entry safely & give 300 welcome credits
            if not row:
                # Prevent race condition: double check again
                already_exists = await conn.fetchval(
                    "SELECT EXISTS(SELECT 1 FROM user_credits WHERE user_id = $1)", user_id
                )
                if already_exists:
                    print(f"⚠️ User {user_id} row exists but fetch returned None. Skipping reinsert.")
                    return None

                await conn.execute(
                    "INSERT INTO user_credits (user_id, credits, last_refill, initial_bonus_given) VALUES ($1, $2, $3, $4)",
                    user_id, 300, datetime.datetime.utcnow(), True
                )
                print(f"✅ New user {user_id} granted 300 welcome credits.")
                return "🎉 Welcome! You've received 300 Ava Credits to start chatting. Enjoy 😉"

            credits = row["credits"]
            last_refill = row["last_refill"]
            initial_bonus_given = row["initial_bonus_given"]

            print(f"📋 User {user_id} — Credits: {credits}, Bonus Given: {initial_bonus_given} ({type(initial_bonus_given)})")

            # ✅ If bonus not given yet, grant 300 and lock flag
            if not initial_bonus_given:
                # Extra protection: only grant if credits are not already 300
                if credits >= 300:
                    print(f"⚠️ User {user_id} already has 300 credits. Skipping bonus.")
                else:
                    await conn.execute(
                        "UPDATE user_credits SET credits = $1, last_refill = $2, initial_bonus_given = TRUE WHERE user_id = $3",
                        300, datetime.datetime.utcnow(), user_id
                    )
                    print(f"💥 Granted 300 credits to user {user_id} via bonus.")
                    return "🎉 You’ve received your first 300 Ava Credits! Enjoy chatting 😉"

            # ✅ Still has credits — no refill needed
            if credits > 0:
                return None

            # ✅ Refill after 12h
            time_since = (datetime.datetime.utcnow() - last_refill).total_seconds()
            if time_since >= REFILL_INTERVAL:
                await conn.execute(
                    "UPDATE user_credits SET credits = $1, last_refill = $2 WHERE user_id = $3",
                    REFILL_AMOUNT, datetime.datetime.utcnow(), user_id
                )
                print(f"🔁 Refilled 100 credits for user {user_id}.")
                return f"💖 You’ve received {REFILL_AMOUNT} free Ava Credits! Enjoy your time again 😘"

            # ❌ No refill yet
            print(f"⏳ User {user_id} must wait longer for refill.")
            return None
