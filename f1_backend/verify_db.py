#!/usr/bin/env python
"""
Script de verificación: prueba si la BD tiene datos y pueden consultarse
"""
import asyncio
from app.db.session import engine
from sqlalchemy import text


async def verify_data():
    print("\n🔍 Verificando datos en la BD...\n")
    
    async with engine.begin() as conn:
        # Verificar drivers
        drivers_count = await conn.scalar(text("SELECT COUNT(*) FROM drivers"))
        print(f"📌 Drivers: {drivers_count}")
        
        # Verificar constructors
        constructors_count = await conn.scalar(text("SELECT COUNT(*) FROM constructors"))
        print(f"📌 Constructors: {constructors_count}")
        
        # Verificar races
        races_count = await conn.scalar(text("SELECT COUNT(*) FROM races"))
        print(f"📌 Races: {races_count}")
        
        # Verificar results
        results_count = await conn.scalar(text("SELECT COUNT(*) FROM results"))
        print(f"📌 Results: {results_count}")
        
        # Verificar standings
        standings_count = await conn.scalar(text("SELECT COUNT(*) FROM driver_standings"))
        print(f"📌 Driver Standings: {standings_count}")
        
        # Verificar lap_times
        laptimes_count = await conn.scalar(text("SELECT COUNT(*) FROM lap_times"))
        print(f"📌 Lap Times: {laptimes_count}")
        
        # Verificar pit_stops
        pitstops_count = await conn.scalar(text("SELECT COUNT(*) FROM pit_stops"))
        print(f"📌 Pit Stops: {pitstops_count}")
        
        print("\n" + "="*50)
        if all([drivers_count, constructors_count, races_count]):
            print("✅ BD tiene datos. Los endpoints deberían funcionar.")
        else:
            print("⚠️  BD vacía o incompleta. Verifica que los datos estén cargados.")
        print("="*50 + "\n")


if __name__ == "__main__":
    asyncio.run(verify_data())
