import fastf1
import pandas as pd
import os
import logging
import time
from fastf1.exceptions import RateLimitExceededError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class F1DataIngestor:
    """
    Ingesta de datos de F1 usando FastF1 con manejo de rate limits y reintentos
    Descarga datos de vueltas individuales para predicción de Pit Stops y Neumáticos
    """
    
    def __init__(self, cache_dir='cache/'):
        self.cache_dir = cache_dir
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
        fastf1.Cache.enable_cache(cache_dir)

    def fetch_season_data(self, year):
        """Descargar todas las vueltas de una temporada"""
        all_laps = []
        
        try:
            schedule = fastf1.get_event_schedule(year)
        except RateLimitExceededError:
            logger.warning(f"Límite alcanzado. Esperando 60s...")
            time.sleep(60)
            schedule = fastf1.get_event_schedule(year)
        
        # Filtrar solo carreras puntuables (omitir testings)
        events = schedule[schedule['EventFormat'] != 'testing']
        
        for _, event in events.iterrows():
            success = False
            retries = 0
            max_retries = 5
            
            while not success and retries < max_retries:
                try:
                    logger.info(f"Cargando: {year} - {event['EventName']} (Intento {retries + 1}/{max_retries})")
                    session = fastf1.get_session(year, event['RoundNumber'], 'R')
                    
                    # telemetry=False para no saturar API
                    session.load(laps=True, telemetry=False, weather=True)
                    
                    laps = session.laps.copy()
                    
                    # Metadatos cruciales
                    laps['Year'] = year
                    laps['EventName'] = event['EventName']
                    laps['TrackType'] = self._get_track_type(event['EventName'])
                    
                    # Datos de clima
                    weather = session.weather_data
                    if not weather.empty:
                        laps['TrackTemp'] = weather['TrackTemp'].mean()
                        laps['Rainfall'] = 1 if weather['Rainfall'].any() else 0
                    else:
                        laps['TrackTemp'] = 35.0
                        laps['Rainfall'] = 0

                    all_laps.append(laps)
                    success = True
                    logger.info(f"✅ {event['EventName']} cargada correctamente")
                    
                    # Pausa entre carreras para ser "buenos ciudadanos"
                    time.sleep(2)
                    
                except RateLimitExceededError:
                    retries += 1
                    wait_time = 60 * retries
                    logger.warning(f"🔴 Bloqueo de API. Esperando {wait_time}s antes de reintentar...")
                    time.sleep(wait_time)
                    
                except Exception as e:
                    logger.error(f"❌ Error cargando {event['EventName']}: {e}")
                    break
                
        if not all_laps:
            logger.error(f"No se pudo descargar datos de {year}")
            return pd.DataFrame()
            
        result = pd.concat(all_laps, ignore_index=True)
        logger.info(f"✅ Temporada {year} completada: {len(result)} vueltas")
        return result

    def fetch_multiple_seasons(self, years_list, output_file='dataset_f1_multiaño_raw.csv'):
        """Descargar múltiples temporadas incremental"""
        for year in years_list:
            # Verificar si el año ya está descargado
            if os.path.exists(output_file):
                df_existing = pd.read_csv(output_file)
                if 'Year' in df_existing.columns and year in df_existing['Year'].unique():
                    logger.info(f"⏭️  Temporada {year} ya existe. Saltando...")
                    continue

            logger.info(f"\n{'='*50}")
            logger.info(f"INICIANDO DESCARGA TEMPORADA {year}")
            logger.info(f"{'='*50}")
            
            year_df = self.fetch_season_data(year)
            
            if not year_df.empty:
                header = not os.path.exists(output_file)
                year_df.to_csv(output_file, mode='a', index=False, header=header)
                logger.info(f"✅ Temporada {year} guardada en {output_file}")
            
            logger.info("⏳ Pausa de seguridad entre temporadas...")
            time.sleep(10)

        return pd.read_csv(output_file) if os.path.exists(output_file) else pd.DataFrame()

    def _get_track_type(self, event_name):
        """Clasificar tipo de circuito (callejero vs permanente)"""
        street_circuits = ['Monaco', 'Singapore', 'Baku', 'Jeddah', 'Las Vegas', 'Australia', 'Miami']
        return 'Street' if any(s in event_name for s in street_circuits) else 'Permanent'


class F1SafetyCarIngestor:
    """
    Ingesta de datos para predicción de Safety Car a nivel de GP
    Carga un registro por carrera (no por vuelta)
    """
    
    def __init__(self, cache_dir='cache/'):
        self.cache_dir = cache_dir
        self.street_circuits = [
            'Monaco', 'Singapore', 'Baku', 'Jeddah', 'Las Vegas', 
            'Melbourne', 'Miami', 'Montreal'
        ]
        fastf1.Cache.enable_cache(cache_dir)

    def fetch_sc_history(self, years_list, output_file='dataset_sc_future.csv'):
        """Descargar historial de Safety Cars por GP"""
        all_events = []
        
        for year in years_list:
            logger.info(f"\n{'='*50}")
            logger.info(f"DESCARGANDO TEMPORADA {year} (SC)")
            logger.info(f"{'='*50}")
            
            try:
                schedule = fastf1.get_event_schedule(year)
                events = schedule[schedule['EventFormat'] != 'testing']
            except Exception as e:
                logger.error(f"❌ Error obtener calendario {year}: {e}")
                continue

            for _, event in events.iterrows():
                try:
                    logger.info(f"Procesando GP: {event['EventName']}")
                    session = fastf1.get_session(year, event['RoundNumber'], 'R')
                    session.load(laps=True, telemetry=False, weather=True)

                    # Identificar si hubo SC (4), VSC (6) o Red Flag (7)
                    status_presentes = session.laps['TrackStatus'].unique()
                    had_sc = 1 if any(str(s) in ['4', '6', '7'] for s in status_presentes) else 0

                    # Datos de clima
                    weather = session.weather_data
                    event_data = {
                        'Year': year,
                        'EventName': event['EventName'],
                        'Location': event['Location'],
                        'TrackType': 'Street' if any(s in event['EventName'] for s in self.street_circuits) else 'Permanent',
                        'AirTemp_Avg': weather['AirTemp'].mean() if not weather.empty else 25.0,
                        'TrackTemp_Avg': weather['TrackTemp'].mean() if not weather.empty else 35.0,
                        'Rainfall_Any': 1 if not weather.empty and weather['Rainfall'].any() else 0,
                        'Total_Drivers': len(session.drivers),
                        'Target_Had_SC': had_sc
                    }
                    all_events.append(event_data)
                    logger.info(f"✅ {event['EventName']}: SC={had_sc}")
                    time.sleep(1)

                except Exception as e:
                    logger.error(f"❌ Error en {event['EventName']}: {e}")
                    continue

        df = pd.DataFrame(all_events)
        df.to_csv(output_file, index=False)
        logger.info(f"✅ Datos de Safety Car guardados: {output_file} ({len(df)} carreras)")
        return df