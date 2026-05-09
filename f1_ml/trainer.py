import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, mean_squared_error
import joblib
import os
import pandas as pd
import numpy as np

class F1ModelTrainer:
    def __init__(self, data):
        # Aseguramos que data sea un DataFrame de pandas para sklearn/xgboost
        if hasattr(data, 'to_pandas'):
            self.data = data.to_pandas()
        else:
            self.data = data
            
        self.features_base = ['Year', 'TyreLife', 'LapTime', 'LapDelta', 'TrackType', 'Compound', 'track_temp', 'air_temp', 'Rainfall']
        if not os.path.exists('models'):
            os.makedirs('models')

    def train_all(self):
        self.train_pit_probability()
        self.train_tyre_strategy()
        self.train_safety_car_probability()
        self.train_lap_time_predictor()

    def train_pit_probability(self):
        print("--- Entrenando Probabilidad de Parada ---")
        X, y = self._prepare_data(self.features_base, 'target_pit')
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
        
        model = xgb.XGBClassifier(n_estimators=100, max_depth=4, learning_rate=0.1, enable_categorical=True)
        model.fit(X_train, y_train)
        
        preds = model.predict_proba(X_test)[:, 1]
        print(f"AUC: {roc_auc_score(y_test, preds):.4f}")
        joblib.dump(model, 'models/pit_predictor.joblib')

    def train_tyre_strategy(self):
        print("--- Entrenando Estrategia de Neumáticos ---")
        # Solo donde hubo parada
        pit_data = self.data[self.data['target_pit'] == 1].copy()
        if pit_data.empty: return
        
        # Simplificamos compuestos
        pit_data['target_next_tyre'] = pit_data['target_next_tyre'].astype('category')
        codes = pit_data['target_next_tyre'].cat.codes
        mapping = dict(enumerate(pit_data['target_next_tyre'].cat.categories))
        joblib.dump(mapping, 'models/tyre_mapping.joblib')

        X = self._prepare_features(pit_data[self.features_base])
        X_train, X_test, y_train, y_test = train_test_split(X, codes, test_size=0.2)
        
        model = xgb.XGBClassifier(objective='multi:softprob', enable_categorical=True)
        model.fit(X_train, y_train)
        joblib.dump(model, 'models/tyre_predictor.joblib')

    def train_safety_car_probability(self):
        print("--- Entrenando Probabilidad de Safety Car ---")
        X, y = self._prepare_data(self.features_base, 'target_sc_upcoming')
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
        
        model = xgb.XGBClassifier(n_estimators=100, enable_categorical=True)
        model.fit(X_train, y_train)
        joblib.dump(model, 'models/sc_predictor.joblib')

    def train_lap_time_predictor(self):
        print("--- Entrenando Predictor de Telemetría (Lap Time) ---")
        X, y = self._prepare_data(self.features_base, 'LapTime')
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
        
        model = xgb.XGBRegressor(n_estimators=150, max_depth=6, enable_categorical=True)
        model.fit(X_train, y_train)
        
        preds = model.predict(X_test)
        print(f"RMSE: {np.sqrt(mean_squared_error(y_test, preds)):.4f}")
        joblib.dump(model, 'models/telemetry_predictor.joblib')

    def _prepare_data(self, features, target):
        df = self.data.dropna(subset=[target] + features)
        X = self._prepare_features(df[features])
        y = df[target]
        return X, y

    def _prepare_features(self, df):
        df = df.copy()
        for col in df.select_dtypes(['object']).columns:
            df[col] = df[col].astype('category')
        return df

if __name__ == "__main__":
    import polars as pl
    if os.path.exists('data_2023_features.csv'):
        data = pl.read_csv('data_2023_features.csv')
        trainer = F1ModelTrainer(data)
        trainer.train_all()