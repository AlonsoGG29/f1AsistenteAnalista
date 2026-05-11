import joblib
import os
import pandas as pd
import numpy as np
import re
import logging

logger = logging.getLogger(__name__)

class MLService:
    """
    Servicio de predicciones ML para F1
    Expone modelos: Pit Stops, Neumáticos, Safety Car
    """
    
    def __init__(self, models_dir=None):
        if models_dir is None:
            # Ruta relativa desde el backend
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            self.models_dir = os.path.join(base_dir, 'f1_ml', 'models')
        else:
            self.models_dir = models_dir
        
        self.models = {}
        
        # Features para Pit Stops y Neumáticos (a nivel de vuelta)
        self.pit_features = [
            'Year', 'TyreLife', 'LapTime', 'LapDelta', 'RollingLapTime',
            'TrackTemp', 'Rainfall', 'TrackType', 'Compound'
        ]
        
        # Features para Safety Car (a nivel de GP)
        self.sc_features = [
            'Circuit_Risk_Score', 'Adjusted_Risk', 'TrackType',
            'Rainfall_Any', 'TrackTemp_Avg'
        ]
        
        self.tyre_mapping = {}
        self.load_models()

    def load_models(self):
        """Cargar todos los modelos disponibles"""
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
                    logger.info(f"✅ Modelo {key} cargado")
                except Exception as e:
                    logger.error(f"❌ Error cargando modelo {key}: {e}")
            else:
                logger.warning(f"⚠️  Modelo {key} no encontrado en {path}")
        
        # Cargar mapeo de neumáticos
        mapping_path = os.path.join(self.models_dir, 'tyre_mapping.joblib')
        if os.path.exists(mapping_path):
            try:
                self.tyre_mapping = joblib.load(mapping_path)
                logger.info("✅ Mapeo de neumáticos cargado")
            except Exception as e:
                logger.error(f"❌ Error cargando mapeo: {e}")

    def _parse_time(self, time_str):
        """Parsear tiempo en formato min:ss.ms a segundos"""
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

    def _prepare_payload_pit(self, payload: dict):
        """Preparar datos para predicción de Pit Stops/Neumáticos"""
        defaults = {
            'Year': 2024,
            'TyreLife': 10,
            'LapTime': 90.0,
            'LapDelta': 0.5,
            'RollingLapTime': 90.0,
            'TrackTemp': 30.0,
            'Rainfall': 0,
            'TrackType': 'Permanent',
            'Compound': 'MEDIUM'
        }
        
        data = {}
        for col in self.pit_features:
            val = payload.get(col, defaults.get(col))
            if col in ['LapTime', 'RollingLapTime']:
                val = self._parse_time(val)
            data[col] = val
            
        df = pd.DataFrame([data])[self.pit_features]
        # Asegurar tipos categóricos
        for col in ['Compound', 'TrackType']:
            if col in df.columns:
                df[col] = df[col].astype('category')
            
        return df

    def _prepare_payload_sc(self, payload: dict):
        """Preparar datos para predicción de Safety Car"""
        defaults = {
            'Circuit_Risk_Score': 0.3,
            'Adjusted_Risk': 0.35,
            'TrackType': 'Permanent',
            'Rainfall_Any': 0,
            'TrackTemp_Avg': 30.0
        }
        
        data = {}
        for col in self.sc_features:
            val = payload.get(col, defaults.get(col))
            data[col] = val
            
        df = pd.DataFrame([data])[self.sc_features]
        # Asegurar tipo categórico
        if 'TrackType' in df.columns:
            df['TrackType'] = df['TrackType'].astype('category')
            
        return df

    def predict_pit_stop(self, payload: dict):
        """Predecir probabilidad de pit stop en la próxima vuelta"""
        if 'pit' not in self.models:
            return {"error": "Modelo de parada no entrenado"}
        
        try:
            df = self._prepare_payload_pit(payload)
            probs = self.models['pit'].predict_proba(df)
            prob = float(probs[0][1])
            
            return {
                "probability": prob,
                "label": bool(prob > 0.5),
                "confidence": "alta" if abs(prob - 0.5) > 0.25 else "media",
                "description": "Probabilidad de parada de boxes en la próxima vuelta"
            }
        except Exception as e:
            logger.error(f"Error prediciendo pit stop: {e}")
            return {"error": f"Error: {str(e)}"}

    def predict_tyre_strategy(self, payload: dict):
        """Predecir mejor estrategia de neumáticos para siguiente parada"""
        if 'tyre' not in self.models:
            return {"error": "Modelo de neumáticos no entrenado"}
        
        try:
            df = self._prepare_payload_pit(payload)
            probs = self.models['tyre'].predict_proba(df)[0]
            
            recommendations = []
            for idx, prob in enumerate(probs):
                compound_name = self.tyre_mapping.get(idx, f"Compuesto_{idx}")
                recommendations.append({
                    "compound": str(compound_name),
                    "probability": float(prob)
                })
            
            # Heurística: si llueve, aumentar probabilidad de neumáticos de lluvia
            if payload.get('Rainfall', 0) == 1:
                # Buscar si hay neumáticos de lluvia
                wet_compounds = [r for r in recommendations if 'WET' in r['compound'].upper() or 'INTER' in r['compound'].upper()]
                if not wet_compounds:
                    # Añadir como recomendación secundaria
                    recommendations.append({
                        "compound": "INTERMEDIATE",
                        "probability": 0.6
                    })
                    recommendations.append({
                        "compound": "WET",
                        "probability": 0.4
                    })
                else:
                    # Boost existing wet compounds
                    for r in recommendations:
                        if 'WET' in r['compound'].upper() or 'INTER' in r['compound'].upper():
                            r['probability'] = min(1.0, r['probability'] * 1.5)
                    
                    # Renormalizar
                    total = sum(r['probability'] for r in recommendations)
                    for r in recommendations:
                        r['probability'] /= total

            recommendations = sorted(recommendations, key=lambda x: x['probability'], reverse=True)
            return recommendations
            
        except Exception as e:
            logger.error(f"Error prediciendo neumáticos: {e}")
            return {"error": f"Error: {str(e)}"}

    def predict_safety_car(self, payload: dict):
        """Predecir probabilidad de Safety Car en el futuro cercano"""
        if 'sc' not in self.models:
            # Usar heurística simple sin modelo
            return self._heuristic_safety_car(payload)
        
        try:
            df = self._prepare_payload_sc(payload)
            probs = self.models['sc'].predict_proba(df)
            prob = float(probs[0][1])
            
            # Aplicar ajustes heurísticos
            # Circuitos callejeros: mayor riesgo
            if payload.get('TrackType', '') == 'Street':
                prob = min(1.0, prob * 1.3)
            
            # Lluvia: más riesgo
            if payload.get('Rainfall_Any', 0) == 1:
                prob = min(1.0, prob * 1.2)
            
            return {
                "probability": prob,
                "label": bool(prob > 0.45),  # Umbral más bajo para SC
                "confidence": "alta" if prob > 0.65 else "media" if prob > 0.35 else "baja",
                "description": "Probabilidad de Safety Car en las próximas vueltas"
            }
        except Exception as e:
            logger.error(f"Error prediciendo Safety Car: {e}")
            return self._heuristic_safety_car(payload)

    def _heuristic_safety_car(self, payload: dict):
        """Predicción heurística de SC cuando no hay modelo"""
        prob = 0.2  # Base
        
        # Ajustes heurísticos
        if payload.get('TrackType', '') == 'Street':
            prob += 0.2
        
        if payload.get('Rainfall_Any', 0) == 1:
            prob += 0.15
        
        # Temperatura extrema (muy fría o caliente)
        temp = payload.get('TrackTemp_Avg', 30)
        if temp < 15 or temp > 45:
            prob += 0.1
        
        prob = min(1.0, prob)
        
        return {
            "probability": prob,
            "label": bool(prob > 0.45),
            "confidence": "baja",  # Lower confidence for heuristic
            "description": "Predicción heurística (modelo no disponible)"
        }

    def get_model_status(self):
        """Retornar estado de todos los modelos"""
        return {
            "pit_stop": "ready" if 'pit' in self.models else "not_available",
            "tyre_strategy": "ready" if 'tyre' in self.models else "not_available",
            "safety_car": "ready" if 'sc' in self.models else "fallback_heuristic",
            "models_directory": self.models_dir,
            "pit_features": self.pit_features,
            "sc_features": self.sc_features
        }

# Instancia global
ml_service = MLService()
