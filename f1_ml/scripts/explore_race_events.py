"""
scripts/explore_race_events.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Ejecuta este script ANTES de entrenar para inspeccionar el dataset
Formula 1 Race Events (jtrotman) y ajustar los nombres de columna
en feature_engineering.py si difieren de los esperados.

Uso:
    python scripts/explore_race_events.py --path /ruta/a/race_events.csv
"""
import argparse
import pandas as pd
import sys

EXPECTED_COLS = {"raceId", "lap", "event_type", "driverId", "constructorId"}
SC_KEYWORDS   = ["safety", "vsc", "red flag"]


def main(path: str) -> None:
    print(f"\n📂 Cargando: {path}")
    try:
        df = pd.read_csv(path, low_memory=False)
    except Exception as e:
        print(f"❌ Error al leer el archivo: {e}"); sys.exit(1)

    print(f"\n{'─'*60}")
    print(f"  Filas: {len(df):,}  |  Columnas: {len(df.columns)}")
    print(f"{'─'*60}")

    print("\n📋 Columnas y tipos:")
    for col in df.columns:
        print(f"  {col:<30} {str(df[col].dtype):<12} nulls: {df[col].isna().sum():,}")

    missing = EXPECTED_COLS - set(df.columns)
    if missing:
        print(f"\n⚠️  Columnas esperadas NO encontradas: {missing}")
        print("   → Ajusta EVENT_COL / RACE_ID_COL en feature_engineering.py")
    else:
        print(f"\n✅ Todas las columnas esperadas están presentes")

    event_cols = [c for c in df.columns if "event" in c.lower() or "type" in c.lower()]
    print(f"\n🔍 Posibles columnas de tipo de evento: {event_cols}")

    for col in event_cols:
        values = df[col].dropna().unique()
        print(f"\n  Valores únicos en '{col}' (máx 40):")
        for v in list(values)[:40]:
            print(f"    · {v}")

    print("\n🚗 Buscando registros de Safety Car / VSC / Red Flag...")
    for col in event_cols:
        mask = df[col].astype(str).str.lower().str.contains(
            "|".join(SC_KEYWORDS), na=False
        )
        n = mask.sum()
        if n > 0:
            print(f"  '{col}': {n:,} registros")
            print(df[mask][col].value_counts().head(10).to_string())

    print(f"\n📊 Primeras 3 filas:")
    print(df.head(3).to_string())
    print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", required=True, help="Ruta al CSV de Race Events")
    args = parser.parse_args()
    main(args.path)
