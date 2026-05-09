from ingestion import F1DataIngestor
from features import F1FeatureEngine
from trainer import F1ModelTrainer
import os

def main():
    print("--- Iniciando Pipeline de ML F1 (FastF1 + XGBoost) ---")
    
    ingestor = F1DataIngestor()
    
    # Intentar cargar local si ya existe para no descargar siempre
    if not os.path.exists('dataset_f1_raw.csv'):
        print("Descargando datos de 2023... esto tardara unos minutos.")
        data_raw = ingestor.fetch_season_data(2023)
        data_raw.to_csv('dataset_f1_raw.csv', index=False)
    else:
        import pandas as pd
        print("Cargando datos locales...")
        data_raw = pd.read_csv('dataset_f1_raw.csv')

    print("Procesando Features con Polars...")
    engine = F1FeatureEngine(data_raw)
    dataset = engine.build_ml_dataset()

    print("Entrenando modelos...")
    trainer = F1ModelTrainer(dataset)
    trainer.train_all()

    print("--- Proceso completado. Modelos guardados en /models ---")

if __name__ == "__main__":
    main()