import joblib
import os
import pandas as pd
import numpy as np
import re

class MLService:
    def __init__(self, models_dir=None):
        if models_dir is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            self.models_dir = os.path.join(base_dir, 'f1_ml', 'models')
        else:
            self.models_dir = models_dir
        
        self.models = {}
        # Coincidir con trainer.py
        self.features = ['Year', 'TyreLife', 'LapTime', 'LapDelta', 'RollingLapTime', 'TrackTemp', 'Rainfall', 'TrackType', 'Compound']
        self.load_models()

    def load_models(self):
        model_files = {
            'pit': 'pit_predictor.joblib',
            'tyre': 'tyre_predictor.joblib',
            'sc': 'sc_predictor.joblib',
        }
        
        for key, filename in model_files.items():
            path = os.path.join(self.models_dir, filename)
            if os.path.exists(path):
                try:
                    self.models[key] = joblib.load(path)
                    print(f"Modelo {key} cargado correctamente.")
                except Exception as e:
                    print(f"Error cargando modelo {key}: {e}")
            else:
                print(f"Modelo {key} no encontrado en {path}")

    def _parse_time(self, time_str):
        if isinstance(time_str, (int, float)):
            return float(time_str)
        
        # Formato min:ss.ms (ej 1:32.123)
        match = re.match(r'(\d+):(\d+\.\d+)', str(time_str))
        if match:
            minutes = int(match.group(1))
            seconds = float(match.group(2))
            return minutes * 60 + seconds
        
        # Solo segundos
        try:
            return float(time_str)
        except:
            return 90.0

    def _prepare_payload(self, payload: dict):
        defaults = {
            'Year': 2023,
            'TyreLife': 10,
            'LapTime': 90.0,
            'LapDelta': 0.0,
            'RollingLapTime': 90.0,
            'TrackTemp': 30.0,
            'Rainfall': 0,
            'TrackType': 'Permanent',
            'Compound': 'MEDIUM'
        }
        
        data = {}
        for col in self.features:
            val = payload.get(col, defaults.get(col))
            if col in ['LapTime', 'RollingLapTime']:
                val = self._parse_time(val)
            data[col] = val
            
        df = pd.DataFrame([data])[self.features]
        # Asegurar tipos categóricos
        for col in ['Compound', 'TrackType']:
            df[col] = df[col].astype('category')
            
        return df

    def predict_pit_stop(self, payload: dict):
        if 'pit' not in self.models:
            return {"error": "Modelo de parada no entrenado."}
        
        try:
            df = self._prepare_payload(payload)
            prob = self.models['pit'].predict_proba(df)[0][1]
            return {
                "probability": float(prob),
                "label": bool(prob > 0.5),
                "confidence": "alta" if abs(prob - 0.5) > 0.3 else "media"
            }
        except Exception as e:
            return {"error": f"Error: {str(e)}"}

    def predict_tyre_strategy(self, payload: dict):
        if 'tyre' not in self.models:
            return {"error": "Modelo de neumáticos no entrenado."}
        
        try:
            df = self._prepare_payload(payload)
            probs = self.models['tyre'].predict_proba(df)[0]
            
            # Cargar mapeo si existe
            mapping_path = os.path.join(self.models_dir, 'tyre_mapping.joblib')
            if os.path.exists(mapping_path):
                mapping = joblib.load(mapping_path)
            else:
                mapping = {0: "HARD", 1: "MEDIUM", 2: "SOFT"}
            
            # Asegurar que INTERMEDIATE y WET estén representados si hay lluvia
            recommendations = []
            for i, p in enumerate(probs):
                compound = mapping.get(i, f"C{i}")
                recommendations.append({"compound": compound, "probability": float(p)})
            
            # Heurística: si Rainfall es 1, boost INTERMEDIATE/WET si no estaban en el top
            if payload.get('Rainfall') == 1:
                # Si el modelo no los conoce (porque no hubo lluvia en el dataset de entrenamiento limitado),
                # los añadimos manualmente con alta probabilidad
                has_wet = any(r['compound'] in ['INTERMEDIATE', 'WET'] for r in recommendations)
                if not has_wet:
                    recommendations.append({"compound": "INTERMEDIATE", "probability": 0.8})
                    recommendations.append({"compound": "WET", "probability": 0.6})
                    # Normalizar
                    total = sum(r['probability'] for r in recommendations)
                    for r in recommendations: r['probability'] /= total

            recommendations = sorted(recommendations, key=lambda x: x['probability'], reverse=True)
            return recommendations
        except Exception as e:
            return {"error": f"Error: {str(e)}"}

    def predict_safety_car(self, payload: dict):
        if 'sc' not in self.models:
            return {"error": "Modelo de Safety Car no entrenado."}
        
        try:
            df = self._prepare_payload(payload)
            prob = self.models['sc'].predict_proba(df)[0][1]
            
            # Heurística relevante: Circuitos urbanos aumentan riesgo
            if payload.get('TrackType') == 'Street':
                prob = min(1.0, prob * 1.5)

            return {
                "probability": float(prob),
                "label": bool(prob > 0.4), # Umbral más bajo para SC
                "confidence": "alta" if abs(prob - 0.4) > 0.2 else "media"
            }
        except Exception as e:
            return {"error": f"Error: {str(e)}"}

ml_service = MLService()
