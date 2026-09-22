import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
import joblib
import os
import pandas as pd
import polars as pl

class F1ModelTrainer:
    """Entrenador de modelos XGBoost para predicciones de F1"""
    
    def __init__(self, data=None):
        self.data = data.to_pandas() if hasattr(data, 'to_pandas') else data if data is not None else None
        self.models_dir = 'models'
        if not os.path.exists(self.models_dir):
            os.makedirs(self.models_dir)
        
        # Features para pit stops y neumáticos
        self.pit_features = [
            'Year', 'TyreLife', 'LapTime', 'LapDelta', 'RollingLapTime', 
            'TrackTemp', 'Rainfall', 'TrackType', 'Compound'
        ]
        
        # Features para Safety Car (a nivel de GP)
        self.sc_features = [
            'Circuit_Risk_Score', 'Adjusted_Risk', 'TrackType', 
            'Rainfall_Any', 'TrackTemp_Avg'
        ]

    def _prepare_features(self, df, feature_cols):
        """Asegurar que las columnas categóricas tengan el tipo correcto para XGBoost"""
        df = df.copy()
        for col in df.columns:
            if col in feature_cols and df[col].dtype == 'object':
                df[col] = df[col].astype('category')
        return df[feature_cols]

    def train_all(self):
        """Entrenar todos los modelos"""
        if self.data is not None:
            self.train_pit_model()
            self.train_tyre_model()
    
    def train_pit_model(self):
        """Entrenar modelo de predicción de Pit Stops"""
        if self.data is None or 'target_pit' not in self.data.columns:
            print("⚠️  Falta data o target_pit para entrenar modelo de Pit Stops")
            return
        
        print("🏁 Entrenando Predictor de Paradas (Pit Stops)...")
        
        # Filtrar features disponibles
        available_features = [f for f in self.pit_features if f in self.data.columns]
        X = self._prepare_features(self.data, available_features)
        y = self.data['target_pit']
        
        # Entrenar
        model = xgb.XGBClassifier(
            objective='binary:logistic',
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            enable_categorical=True,
            random_state=42
        )
        model.fit(X, y)
        
        # Guardar
        path = os.path.join(self.models_dir, 'pit_predictor.joblib')
        joblib.dump(model, path)
        print(f"✅ Modelo de Pit Stops guardado: {path}")

    def train_tyre_model(self):
        """Entrenar modelo de predicción de cambio de Neumáticos"""
        if self.data is None or 'target_next_tyre' not in self.data.columns:
            print("⚠️  Falta data o target_next_tyre para entrenar modelo de Neumáticos")
            return
        
        print("🏁 Entrenando Predictor de Neumáticos...")
        
        pit_data = self.data.dropna(subset=['target_next_tyre']).copy()
        if pit_data.empty:
            print("⚠️  No hay datos válidos para entrenar modelo de Neumáticos")
            return
        
        # Filtrar features disponibles
        available_features = [f for f in self.pit_features if f in pit_data.columns]
        X = self._prepare_features(pit_data, available_features)
        
        # Guardar el mapeo de categorías
        pit_data['target_next_tyre'] = pit_data['target_next_tyre'].astype('category')
        mapping = dict(enumerate(pit_data['target_next_tyre'].cat.categories))
        mapping_path = os.path.join(self.models_dir, 'tyre_mapping.joblib')
        joblib.dump(mapping, mapping_path)
        
        y = pit_data['target_next_tyre'].cat.codes
        
        # Entrenar
        model = xgb.XGBClassifier(
            objective='multi:softprob',
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            enable_categorical=True,
            random_state=42
        )
        model.fit(X, y)
        
        # Guardar
        path = os.path.join(self.models_dir, 'tyre_predictor.joblib')
        joblib.dump(model, path)
        print(f"✅ Modelo de Neumáticos guardado: {path}")
        print(f"✅ Mapeo de neumáticos guardado: {mapping_path}")

    def train_sc_model(self, data_path='dataset_sc_future.csv'):
        """
        Entrenar modelo de predicción de Safety Car a nivel de GP
        Datos: Nivel de carrera (no de vuelta)
        """
        print("🏁 Entrenando Predictor de Safety Car...")
        
        try:
            # Cargar datos de SC (debe existir en el mismo directorio)
            if not os.path.exists(data_path):
                print(f"⚠️  Archivo {data_path} no encontrado")
                return
            
            df_sc = pd.read_csv(data_path)
            
            # Asegurar tipos de datos
            df_sc['TrackType'] = df_sc['TrackType'].astype('category')
            
            # Filtrar features disponibles
            available_features = [f for f in self.sc_features if f in df_sc.columns]
            X = self._prepare_features(df_sc, available_features)
            
            if 'Target_Had_SC' not in df_sc.columns:
                print("⚠️  Falta columna 'Target_Had_SC' en datos de Safety Car")
                return
            
            y = df_sc['Target_Had_SC']
            
            # Split train/test
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )
            
            # Entrenar
            model = xgb.XGBClassifier(
                n_estimators=150,
                max_depth=5,
                learning_rate=0.05,
                enable_categorical=True,
                objective='binary:logistic',
                random_state=42
            )
            model.fit(X_train, y_train)
            
            # Evaluar
            train_acc = model.score(X_train, y_train)
            test_acc = model.score(X_test, y_test)
            print(f"✅ Accuracy entrenamiento: {train_acc:.2%}")
            print(f"✅ Accuracy test: {test_acc:.2%}")
            
            # Guardar
            path = os.path.join(self.models_dir, 'sc_predictor.joblib')
            joblib.dump(model, path)
            print(f"✅ Modelo de Safety Car guardado: {path}")
            
        except Exception as e:
            print(f"❌ Error al entrenar modelo de Safety Car: {e}")