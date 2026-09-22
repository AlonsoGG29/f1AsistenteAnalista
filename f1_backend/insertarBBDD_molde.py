import os
import glob
import kagglehub
import pandas as pd
from sqlalchemy import create_engine

# ==========================================
# 1. CONFIGURACIÓN DE LA BASE DE DATOS
# ==========================================
# Modifica estos valores con las credenciales de tu PostgreSQL
USER = "tu_usuario"
PASSWORD = "tu_password"
HOST = "localhost"
PORT = "5432"
DB_NAME = "f1db"

# Crear la cadena de conexión (Connection String)
connection_string = f"postgresql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DB_NAME}"
engine = create_engine(connection_string)

# ==========================================
# 2. DESCARGAR EL DATASET DE KAGGLE
# ==========================================
print("Descargando dataset desde Kaggle...")
path = kagglehub.dataset_download("jtrotman/formula-1-race-data")
print(f"Archivos descargados en: {path}\n")

# ==========================================
# 3. PROCESAR E INSERTAR LOS ARCHIVOS CSV
# ==========================================
# Buscamos todos los archivos .csv en la ruta de descarga
csv_files = glob.glob(os.path.join(path, "*.csv"))

if not csv_files:
    print("No se encontraron archivos CSV en la ruta especificada.")
else:
    print(f"Se encontraron {len(csv_files)} archivos para procesar.")
    
    for file_path in csv_files:
        # Extraer el nombre del archivo sin extensión para usarlo como nombre de tabla
        file_name = os.path.basename(file_path)
        table_name = os.path.splitext(file_name)[0]
        
        print(f"Procesando tabla: '{table_name}'...")
        
        try:
            # Leer el CSV con Pandas
            # Nota: Mantenemos 'keep_default_na=False' o manejamos nulos si el CSV usa '\N' para valores vacíos (común en Ergast F1)
            df = pd.read_csv(file_path, na_values=['\\N', 'NaN', ''])
            
            # Insertar en PostgreSQL
            # 'if_exists="replace"' sobrescribe la tabla si ya existe. Cambiar a "append" si solo quieres sumar datos.
            # 'index=False' evita que el índice de Pandas se cree como una columna en la BBDD.
            df.to_sql(
                name=table_name, 
                con=engine, 
                if_exists="replace", 
                index=False,
                chunksize=5000 # Lo sube en bloques de 5000 filas para no saturar la memoria
            )
            print(f"✓ ¡Tabla '{table_name}' importada con éxito! ({len(df)} filas)")
            
        except Exception as e:
            print(f"✗ Error al procesar {file_name}: {e}")

print("\nProceso de importación finalizado.")