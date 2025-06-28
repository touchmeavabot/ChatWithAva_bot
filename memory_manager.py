import asyncpg
import json

class MemoryManager:
    def __init__(self, pool):
        self.pool = pool

    async def get_memory(self, user_id):
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("SELECT memory FROM user_memory WHERE user_id = $1", user_id)
            return row["memory"] if row else {}

    async def update_memory(self, user_id, updates: dict):
        async with self.pool.acquire() as conn:
            current = await self.get_memory(user_id)
            current.update(updates)
            await conn.execute("""
                INSERT INTO user_memory (user_id, memory)
                VALUES ($1, $2)
                ON CONFLICT (user_id) DO UPDATE
                SET memory = EXCLUDED.memory
            """, user_id, json.dumps(current))
