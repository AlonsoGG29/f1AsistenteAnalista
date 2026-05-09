import xgboost as xgb
from sklearn.model_selection import train_test_split
import joblib
import os
import pandas as pd

class F1ModelTrainer:
    def __init__(self, data):
        self.data = data.to_pandas() if hasattr(data, 'to_pandas') else data
        self.features = ['Year', 'TyreLife', 'LapTime', 'LapDelta', 'RollingLapTime', 'TrackTemp', 'Rainfall', 'TrackType', 'Compound']
        if not os.path.exists('models'): os.makedirs('models')

    def _prepare_features(self, df):
        # Asegurar que las columnas categóricas tengan el tipo correcto para XGBoost
        df = df.copy()
        for col in ['Compound', 'TrackType']:
            if col in df.columns:
                df[col] = df[col].astype('category')
        return df

    def train_all(self):
        self.train_pit_model()
        self.train_tyre_model()
        self.train_sc_model()

    def train_pit_model(self):
        print("Entrenando Predictor de Paradas (Pit Stops)...")
        X = self._prepare_features(self.data[self.features])
        y = self.data['target_pit']
        model = xgb.XGBClassifier(objective='binary:logistic', n_estimators=100, enable_categorical=True)
        model.fit(X, y)
        joblib.dump(model, 'models/pit_predictor.joblib')

    def train_tyre_model(self):
        print("Entrenando Predictor de Neumáticos...")
        pit_data = self.data.dropna(subset=['target_next_tyre']).copy()
        if pit_data.empty: return
        
        X = self._prepare_features(pit_data[self.features])
        # Guardar el mapeo de categorías
        pit_data['target_next_tyre'] = pit_data['target_next_tyre'].astype('category')
        mapping = dict(enumerate(pit_data['target_next_tyre'].cat.categories))
        joblib.dump(mapping, 'models/tyre_mapping.joblib')
        
        y = pit_data['target_next_tyre'].cat.codes
        model = xgb.XGBClassifier(objective='multi:softprob', n_estimators=100, enable_categorical=True)
        model.fit(X, y)
        joblib.dump(model, 'models/tyre_predictor.joblib')

    def train_sc_model(self):
        print("Entrenando Predictor de Safety Car...")
        X = self._prepare_features(self.data[self.features])
        y = self.data['target_sc_upcoming']
        model = xgb.XGBClassifier(n_estimators=100, scale_pos_weight=5, enable_categorical=True)
        model.fit(X, y)
        joblib.dump(model, 'models/sc_predictor.joblib')