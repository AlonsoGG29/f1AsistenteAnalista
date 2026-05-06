#!/usr/bin/env python
"""
Test directo de los endpoints para ver qué están retornando
"""
import asyncio
import json
from app.db.session import AsyncSessionLocal
from app.services.query_service import get_drivers, get_races, get_driver_standings


async def test_endpoints():
    async with AsyncSessionLocal() as db:
        print("\n🧪 Probando endpoints...\n")
        
        # Test drivers
        print("1️⃣  GET /api/drivers")
        try:
            total, drivers = await get_drivers(db, skip=0, limit=5)
            print(f"   Total: {total}")
            print(f"   Retornados: {len(drivers)}")
            if drivers:
                print(f"   Primer driver: {drivers[0]}")
            print()
        except Exception as e:
            print(f"   ❌ ERROR: {e}\n")
        
        # Test races
        print("2️⃣  GET /api/races")
        try:
            total, races = await get_races(db, skip=0, limit=5)
            print(f"   Total: {total}")
            print(f"   Retornados: {len(races)}")
            if races:
                print(f"   Primer race: {races[0]}")
            print()
        except Exception as e:
            print(f"   ❌ ERROR: {e}\n")
        
        # Test standings
        print("3️⃣  GET /api/standings/drivers/2024")
        try:
            standings = await get_driver_standings(db, 2024)
            print(f"   Retornados: {len(standings)}")
            if standings:
                print(f"   Primer entry: {standings[0]}")
            print()
        except Exception as e:
            print(f"   ❌ ERROR: {e}\n")


if __name__ == "__main__":
    asyncio.run(test_endpoints())
