import fastf1
import polars as pl
import pandas as pd
import os

class F1DataIngestor:
    def __init__(self, cache_dir='cache/'):
        self.cache_dir = cache_dir
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
        fastf1.cache.enable_cache(cache_dir)

    def fetch_season_data(self, year, sessions=['R']):
        all_data = []
        schedule = fastf1.get_event_schedule(year)
        
        for _, event in schedule.iterrows():
            if event['EventFormat'] == 'testing': continue
            
            try:
                print(f"Descargando: {year} {event['EventName']}...")
                session = fastf1.get_session(year, event['RoundNumber'], 'R')
                session.load(laps=True, telemetry=True, weather=True)
                
                laps = session.laps.copy()
                weather = session.weather_data
                avg_air_temp = weather['AirTemp'].mean() if not weather.empty else 20.0
                avg_track_temp = weather['TrackTemp'].mean() if not weather.empty else 30.0
                rainfall = weather['Rainfall'].any() if not weather.empty else False

                laps['Year'] = year
                laps['EventName'] = event['EventName']
                laps['TrackType'] = self._get_track_type(event['EventName'])
                laps['AirTemp'] = avg_air_temp
                laps['TrackTemp'] = avg_track_temp
                laps['Rainfall'] = 1 if rainfall else 0
                
                all_data.append(laps)
            except Exception as e:
                print(f"Error en {event['EventName']}: {e}")
                
        if not all_data:
            return pd.DataFrame()
            
        return pd.concat(all_data, ignore_index=True)

    def _get_track_type(self, event_name):
        street_circuits = ['Monaco', 'Singapore', 'Baku', 'Jeddah', 'Las Vegas', 'Australia', 'Miami']
        return 'Street' if any(s in event_name for s in street_circuits) else 'Permanent'

if __name__ == "__main__":
    ingestor = F1DataIngestor()
    # Para demostración, solo cargamos unas pocas rondas si es necesario, 
    # pero aquí permitimos el año completo.
    data = ingestor.fetch_season_data(2023)
    if not data.empty:
        print(f"Dataset creado con {len(data)} vueltas.")
        data.to_csv('data_2023_raw.csv', index=False)