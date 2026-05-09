import joblib
import os
import pandas as pd
import numpy as np

class MLService:
    def __init__(self, models_dir=None):
        if models_dir is None:
            # Intentar encontrar la carpeta de modelos relativa a este archivo
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            self.models_dir = os.path.join(base_dir, 'f1_ml', 'models')
        else:
            self.models_dir = models_dir
        self.models = {}
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
                self.models[key] = joblib.load(path)
                print(f"Modelo {key} cargado correctamente.")
            else:
                print(f"Modelo {key} no encontrado en {path}")

    def predict_pit_stop(self, features: dict):
        if 'pit' not in self.models:
            return {"error": "Modelo de parada no cargado"}
        
        df = pd.DataFrame([features])
        prob = self.models['pit'].predict_proba(df)[0][1]
        return {
            "probability": float(prob),
            "label": bool(prob > 0.5),
            "confidence": "alta" if abs(prob - 0.5) > 0.3 else "media"
        }

    def predict_tyre_strategy(self, features: dict):
        if 'tyre' not in self.models:
            return {"error": "Modelo de neumáticos no cargado"}
        
        df = pd.DataFrame([features])
        probs = self.models['tyre'].predict_proba(df)[0]
        
        # Necesitaríamos el mapeo de compuestos, pero por ahora devolvemos los índices
        # En el trainer se guardó tyre_mapping.joblib
        mapping_path = os.path.join(self.models_dir, 'tyre_mapping.joblib')
        if os.path.exists(mapping_path):
            mapping = joblib.load(mapping_path)
        else:
            mapping = {0: "SOFT", 1: "MEDIUM", 2: "HARD"}

        recommendations = []
        for i, p in enumerate(probs):
            recommendations.append({"compound": mapping.get(i, f"C{i}"), "probability": float(p)})
        
        recommendations = sorted(recommendations, key=lambda x: x['probability'], reverse=True)
        return recommendations

    def predict_safety_car(self, features: dict):
        if 'sc' not in self.models:
            return {"error": "Modelo de Safety Car no cargado"}
        
        df = pd.DataFrame([features])
        prob = self.models['sc'].predict_proba(df)[0][1]
        return {
            "probability": float(prob),
            "label": bool(prob > 0.5),
            "confidence": "alta" if abs(prob - 0.5) > 0.3 else "media"
        }

ml_service = MLService()
