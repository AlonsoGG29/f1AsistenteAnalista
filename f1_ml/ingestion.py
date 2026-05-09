import fastf1
import pandas as pd
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class F1DataIngestor:
    def __init__(self, cache_dir='cache/'):
        self.cache_dir = cache_dir
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
        fastf1.Cache.enable_cache(cache_dir)

    def fetch_season_data(self, year):
        all_laps = []
        schedule = fastf1.get_event_schedule(year)
        
        # Filtrar solo carreras puntuables (omitir testings)
        events = schedule[schedule['EventFormat'] != 'testing']
        
        for _, event in events.iterrows():
            try:
                logger.info(f"Cargando: {year} - {event['EventName']}")
                session = fastf1.get_session(year, event['RoundNumber'], 'R')
                session.load(laps=True, telemetry=True, weather=True)
                
                laps = session.laps.copy()
                
                # Añadir metadatos cruciales
                laps['Year'] = year
                laps['EventName'] = event['EventName']
                laps['TrackType'] = self._get_track_type(event['EventName'])
                
                # Inyectar datos de clima promedio por vuelta si están disponibles
                weather = session.weather_data
                if not weather.empty:
                    laps['AirTemp'] = weather['AirTemp'].mean()
                    laps['TrackTemp'] = weather['TrackTemp'].mean()
                    laps['Rainfall'] = 1 if weather['Rainfall'].any() else 0
                else:
                    laps['AirTemp'], laps['TrackTemp'], laps['Rainfall'] = 25.0, 35.0, 0

                all_laps.append(laps)
            except Exception as e:
                logger.error(f"No se pudo cargar {event['EventName']}: {e}")
                
        if not all_laps:
            return pd.DataFrame()
            
        return pd.concat(all_laps, ignore_index=True)

    def _get_track_type(self, event_name):
        street = ['Monaco', 'Singapore', 'Baku', 'Jeddah', 'Las Vegas', 'Australia', 'Miami']
        return 'Street' if any(s in event_name for s in street) else 'Permanent'