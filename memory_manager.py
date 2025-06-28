import asyncpg
import json
import os

DB_URL = os.getenv("DATABASE_URL")  # ✅ Railway DB URL from environment

class MemoryManager:
    def __init__(self):
        self.pool = None

    async def connect(self):
        self.pool = await asyncpg.create_pool(dsn=DB_URL)

    async def get_memory(self, user_id: int) -> dict:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("SELECT memory FROM user_memory WHERE user_id = $1", user_id)
            if row and row["memory"]:
                try:
                    return json.loads(row["memory"])  # ✅ Convert JSON string to dict
                except json.JSONDecodeError:
                    return {}
            return {}

    async def save_memory(self, user_id: int, memory: dict):
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO user_memory (user_id, memory)
                VALUES ($1, $2)
                ON CONFLICT (user_id)
                DO UPDATE SET memory = EXCLUDED.memory
            """, user_id, json.dumps(memory))  # ✅ Store dict as JSON string
