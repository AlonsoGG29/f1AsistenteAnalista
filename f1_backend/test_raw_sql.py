#!/usr/bin/env python
"""
Test directo: qué retorna la BD para drivers
"""
import asyncio
from app.db.session import engine
from sqlalchemy import select, text
from app.models.f1_models import Driver


async def test():
    print("\n🧪 Test directo de drivers...\n")
    
    async with engine.begin() as conn:
        # Contar drivers
        count = await conn.scalar(text("SELECT COUNT(*) FROM drivers"))
        print(f"Total drivers en BD: {count}")
        
        if count > 0:
            # Traer 5 drivers
            result = await conn.execute(text("SELECT * FROM drivers LIMIT 5"))
            drivers = result.mappings().all()
            print(f"\nPrimeros 5 drivers:")
            for d in drivers:
                print(f"  - {d['forename']} {d['surname']} (ID: {d['driverid']}, Nationality: {d['nationality']})")


if __name__ == "__main__":
    asyncio.run(test())
