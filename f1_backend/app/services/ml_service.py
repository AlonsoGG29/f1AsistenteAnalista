import joblib
import os
import pandas as pd
import numpy as np

class MLService:
    def __init__(self, models_dir=None):
        if models_dir is None:
            # Intentar encontrar la carpeta de modelos relativa a este archivo
            # f1_backend/app/services/ml_service.py -> f1_backend/app/services -> f1_backend/app -> f1_backend -> root
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            self.models_dir = os.path.join(base_dir, 'f1_ml', 'models')
        else:
            self.models_dir = models_dir
        
        self.models = {}
        self.features = ['Year', 'TyreLife', 'LapTime', 'LapDelta', 'RollingLapTime', 'TrackTemp', 'Rainfall']
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

    def _prepare_payload(self, payload: dict):
        # Aseguramos que todas las columnas necesarias existan con valores por defecto
        defaults = {
            'Year': 2023,
            'TyreLife': 10,
            'LapTime': 90.0,
            'LapDelta': 0.0,
            'RollingLapTime': 90.0,
            'TrackTemp': 30.0,
            'Rainfall': 0
        }
        data = {col: payload.get(col, defaults.get(col)) for col in self.features}
        return pd.DataFrame([data])[self.features]

    def predict_pit_stop(self, payload: dict):
        if 'pit' not in self.models:
            return {"error": "Modelo de parada no entrenado aún."}
        
        try:
            df = self._prepare_payload(payload)
            prob = self.models['pit'].predict_proba(df)[0][1]
            return {
                "probability": float(prob),
                "label": bool(prob > 0.5),
                "confidence": "alta" if abs(prob - 0.5) > 0.3 else "media"
            }
        except Exception as e:
            return {"error": f"Error en predicción: {str(e)}"}

    def predict_tyre_strategy(self, payload: dict):
        if 'tyre' not in self.models:
            return {"error": "Modelo de neumáticos no entrenado aún."}
        
        try:
            df = self._prepare_payload(payload)
            probs = self.models['tyre'].predict_proba(df)[0]
            
            # Mapeo estático si no encontramos el dinámico
            mapping = {0: "HARD", 1: "MEDIUM", 2: "SOFT"}
            
            recommendations = []
            for i, p in enumerate(probs):
                recommendations.append({"compound": mapping.get(i, f"C{i}"), "probability": float(p)})
            
            recommendations = sorted(recommendations, key=lambda x: x['probability'], reverse=True)
            return recommendations
        except Exception as e:
            return {"error": f"Error en recomendación: {str(e)}"}

    def predict_safety_car(self, payload: dict):
        if 'sc' not in self.models:
            return {"error": "Modelo de Safety Car no entrenado aún."}
        
        try:
            df = self._prepare_payload(payload)
            prob = self.models['sc'].predict_proba(df)[0][1]
            return {
                "probability": float(prob),
                "label": bool(prob > 0.5),
                "confidence": "alta" if abs(prob - 0.5) > 0.3 else "media"
            }
        except Exception as e:
            return {"error": f"Error en predicción: {str(e)}"}

ml_service = MLService()
