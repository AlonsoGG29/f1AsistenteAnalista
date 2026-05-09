import xgboost as xgb
from sklearn.model_selection import train_test_split
import joblib
import os

class F1ModelTrainer:
    def __init__(self, data):
        self.data = data.to_pandas() if hasattr(data, 'to_pandas') else data
        self.features = ['Year', 'TyreLife', 'LapTime', 'LapDelta', 'RollingLapTime', 'TrackTemp', 'Rainfall']
        if not os.path.exists('models'): os.makedirs('models')

    def train_all(self):
        self.train_pit_model()
        self.train_tyre_model()
        self.train_sc_model()

    def train_pit_model(self):
        print("Entrenando Predictor de Paradas (Pit Stops)...")
        X = self.data[self.features]
        y = self.data['target_pit']
        model = xgb.XGBClassifier(objective='binary:logistic', n_estimators=100)
        model.fit(X, y)
        joblib.dump(model, 'models/pit_predictor.joblib')

    def train_tyre_model(self):
        print("Entrenando Predictor de Neumáticos...")
        # Solo aprendemos de las vueltas donde hay un cambio de neumático
        pit_data = self.data.dropna(subset=['target_next_tyre'])
        X = pit_data[self.features]
        # Convertir compuestos a códigos numéricos
        y = pit_data['target_next_tyre'].astype('category').cat.codes
        model = xgb.XGBClassifier(objective='multi:softprob', n_estimators=100)
        model.fit(X, y)
        joblib.dump(model, 'models/tyre_predictor.joblib')

    def train_sc_model(self):
        print("Entrenando Predictor de Safety Car...")
        X = self.data[self.features]
        y = self.data['target_sc_upcoming']
        model = xgb.XGBClassifier(n_estimators=100, scale_pos_weight=5) # SC es evento raro
        model.fit(X, y)
        joblib.dump(model, 'models/sc_predictor.joblib')