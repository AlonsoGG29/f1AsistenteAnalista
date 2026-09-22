"""
Script de entrenamiento rápido para todos los modelos ML de F1
Ejecuta el pipeline completo: Ingesta → Feature Engineering → Entrenamiento
"""

from ingestion import F1DataIngestor, F1SafetyCarIngestor
from features import F1FeatureEngine
from trainer import F1ModelTrainer
import pandas as pd
import os
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def train_pit_stop_models():
    """Entrenar modelos de Pit Stops y Neumáticos"""
    logger.info("\n" + "="*60)
    logger.info("ENTRENAMIENTO: PIT STOPS Y NEUMÁTICOS")
    logger.info("="*60)
    
    # Cargar o descargar datos
    if not os.path.exists('dataset_f1_multiaño_raw.csv'):
        logger.info("📥 Descargando datos de múltiples temporadas...")
        ingestor = F1DataIngestor()
        data_raw = ingestor.fetch_multiple_seasons(
            years_list=[2023, 2024],
            output_file='dataset_f1_multiaño_raw.csv'
        )
    else:
        logger.info("📂 Cargando datos locales...")
        data_raw = pd.read_csv('dataset_f1_multiaño_raw.csv')
        # Convertir tiempos a timedelta
        for col in ['LapTime', 'PitInTime', 'PitOutTime']:
            if col in data_raw.columns:
                try:
                    data_raw[col] = pd.to_timedelta(data_raw[col])
                except:
                    pass

    # Feature Engineering
    logger.info("🔧 Procesando Features con Polars...")
    engine = F1FeatureEngine(data_raw)
    dataset = engine.build_ml_dataset()

    # Entrenamiento
    logger.info("🤖 Entrenando modelos...")
    trainer = F1ModelTrainer(dataset)
    trainer.train_all()
    
    logger.info("✅ Modelos de Pit Stops y Neumáticos completados\n")

def train_safety_car_model():
    """Entrenar modelo de predicción de Safety Car"""
    logger.info("\n" + "="*60)
    logger.info("ENTRENAMIENTO: SAFETY CAR")
    logger.info("="*60)
    
    # Cargar o descargar datos de SC
    if not os.path.exists('dataset_sc_future.csv'):
        logger.info("📥 Descargando datos de Safety Car...")
        ingestor_sc = F1SafetyCarIngestor()
        data_sc = ingestor_sc.fetch_sc_history(
            years_list=[2023, 2024],
            output_file='dataset_sc_future.csv'
        )
    else:
        logger.info("📂 Cargando datos de Safety Car locales...")
        data_sc = pd.read_csv('dataset_sc_future.csv')

    # Feature Engineering para SC
    logger.info("🔧 Procesando Features de Safety Car...")
    engine_sc = F1FeatureEngine(data_sc)
    dataset_sc = engine_sc.build_ml_sc_dataset()

    # Entrenamiento
    logger.info("🤖 Entrenando modelo de Safety Car...")
    trainer = F1ModelTrainer()
    trainer.train_sc_model(data_path='dataset_sc_future.csv')
    
    logger.info("✅ Modelo de Safety Car completado\n")

def main():
    """Ejecutar pipeline completo de ML"""
    logger.info("\n" + "="*60)
    logger.info("🏁 INICIANDO PIPELINE COMPLETO DE ML F1")
    logger.info("="*60 + "\n")
    
    try:
        # Entrenar modelos de Pit Stops
        train_pit_stop_models()
        
        # Entrenar modelo de Safety Car
        train_safety_car_model()
        
        logger.info("\n" + "="*60)
        logger.info("🎉 PIPELINE COMPLETADO CON ÉXITO")
        logger.info("Modelos guardados en: ./models/")
        logger.info("="*60 + "\n")
        
    except Exception as e:
        logger.error(f"\n❌ Error durante el entrenamiento: {e}")
        raise

if __name__ == "__main__":
    main()