"""
scripts/train_models.py
━━━━━━━━━━━━━━━━━━━━━━━
Entrena los tres modelos y los guarda en models_trained/.
Usa XGBoost si está disponible, si no GradientBoostingClassifier.

Uso:
    python scripts/train_models.py \
        --data-dir /ruta/a/csvs \
        --events   /ruta/a/race_events.csv \
        --out-dir  models_trained/

Los CSVs de --data-dir deben ser los del dataset Ergast:
    races.csv, results.csv, status.csv, drivers.csv,
    constructors.csv, qualifying.csv, circuits.csv,
    lap_times.csv, pit_stops.csv
"""
import argparse
import json
import warnings
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import (
    roc_auc_score, classification_report, brier_score_loss,
)
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer

warnings.filterwarnings("ignore")

# Intentar importar XGBoost; si no está, usar GBM de sklearn
try:
    from xgboost import XGBClassifier
    def make_classifier(name: str):
        params = {
            "sc":  dict(n_estimators=400, max_depth=4, learning_rate=0.05,
                        subsample=0.8, colsample_bytree=0.8, use_label_encoder=False,
                        eval_metric="logloss", random_state=42),
            "dnf": dict(n_estimators=300, max_depth=3, learning_rate=0.05,
                        subsample=0.8, colsample_bytree=0.8, use_label_encoder=False,
                        eval_metric="logloss", random_state=42),
            "pos": dict(n_estimators=400, max_depth=4, learning_rate=0.05,
                        subsample=0.8, colsample_bytree=0.8, use_label_encoder=False,
                        eval_metric="logloss", random_state=42),
        }
        return XGBClassifier(**params[name])
    BACKEND = "XGBoost"
except ImportError:
    def make_classifier(name: str):
        params = {
            "sc":  dict(n_estimators=400, max_depth=4, learning_rate=0.05,
                        subsample=0.8, random_state=42),
            "dnf": dict(n_estimators=300, max_depth=3, learning_rate=0.05,
                        subsample=0.8, random_state=42),
            "pos": dict(n_estimators=400, max_depth=4, learning_rate=0.05,
                        subsample=0.8, random_state=42),
        }
        return GradientBoostingClassifier(**params[name])
    BACKEND = "GradientBoostingClassifier (sklearn)"

from feature_engineering import (
    build_safety_car_features,
    build_mechanical_failure_features,
    build_position_features,
    MECHANICAL_DNF_STATUSES,
)


def make_pipeline(clf) -> Pipeline:
    return Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler",  StandardScaler()),
        ("clf",     CalibratedClassifierCV(clf, cv=3, method="isotonic")),
    ])


def evaluate(pipe, X, y, name: str) -> dict:
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    auc_scores = cross_val_score(pipe, X, y, cv=cv, scoring="roc_auc")
    pipe.fit(X, y)
    probs = pipe.predict_proba(X)[:, 1]
    metrics = {
        "model": name,
        "backend": BACKEND,
        "n_samples": int(len(y)),
        "positive_rate": float(y.mean()),
        "cv_auc_mean": float(auc_scores.mean()),
        "cv_auc_std":  float(auc_scores.std()),
        "train_auc":   float(roc_auc_score(y, probs)),
        "brier_score": float(brier_score_loss(y, probs)),
    }
    print(f"\n{'─'*55}")
    print(f"  {name}")
    print(f"  Backend : {BACKEND}")
    print(f"  Muestras: {metrics['n_samples']:,} | Positivos: {metrics['positive_rate']:.1%}")
    print(f"  CV AUC  : {metrics['cv_auc_mean']:.4f} ± {metrics['cv_auc_std']:.4f}")
    print(f"  Train AUC: {metrics['train_auc']:.4f}")
    print(f"  Brier   : {metrics['brier_score']:.4f}  (0=perfecto, 0.25=azar)")
    return metrics


def get_feature_importance(pipe, feature_cols: list) -> dict:
    """Extrae importancia de features si el clf base la expone."""
    try:
        clf = pipe.named_steps["clf"]
        # CalibratedClassifierCV envuelve el estimador
        base = clf.estimators_[0] if hasattr(clf, "estimators_") else clf
        if hasattr(base, "estimator"):
            base = base.estimator
        if hasattr(base, "feature_importances_"):
            imp = base.feature_importances_
            return dict(sorted(
                zip(feature_cols, imp.tolist()),
                key=lambda x: x[1], reverse=True
            ))
    except Exception:
        pass
    return {}


def train_safety_car(data_dir: Path, events_path: str, out_dir: Path) -> dict:
    print("\n🚗 Entrenando modelo de Safety Car...")
    df = build_safety_car_features(
        races_csv       = str(data_dir / "races.csv"),
        circuits_csv    = str(data_dir / "circuits.csv"),
        results_csv     = str(data_dir / "results.csv"),
        race_events_csv = events_path,
        pit_stops_csv   = str(data_dir / "pit_stops.csv")
            if (data_dir / "pit_stops.csv").exists() else None,
    )
    feature_cols = [c for c in df.columns if c not in ("raceId", "had_safety_car")]
    X = df[feature_cols].values
    y = df["had_safety_car"].values

    clf  = make_classifier("sc")
    pipe = make_pipeline(clf)
    metrics = evaluate(pipe, X, y, "Safety Car")
    metrics["features"] = feature_cols
    metrics["feature_importance"] = get_feature_importance(pipe, feature_cols)

    out = out_dir / "safety_car_model.joblib"
    joblib.dump({"pipeline": pipe, "features": feature_cols, "metrics": metrics}, out)
    print(f"  ✅ Guardado: {out}")
    return metrics


def train_mechanical_failure(data_dir: Path, out_dir: Path) -> dict:
    print("\n🔧 Entrenando modelo de Fallo Mecánico...")
    df = build_mechanical_failure_features(
        races_csv        = str(data_dir / "races.csv"),
        results_csv      = str(data_dir / "results.csv"),
        status_csv       = str(data_dir / "status.csv"),
        drivers_csv      = str(data_dir / "drivers.csv"),
        constructors_csv = str(data_dir / "constructors.csv"),
        lap_times_csv    = str(data_dir / "lap_times.csv")
            if (data_dir / "lap_times.csv").exists() else None,
    )
    feature_cols = [c for c in df.columns
                    if c not in ("raceId", "driverId", "constructorId", "is_mechanical")]
    X = df[feature_cols].values
    y = df["is_mechanical"].values

    clf  = make_classifier("dnf")
    pipe = make_pipeline(clf)
    metrics = evaluate(pipe, X, y, "Fallo Mecánico")
    metrics["features"] = feature_cols
    metrics["feature_importance"] = get_feature_importance(pipe, feature_cols)

    out = out_dir / "mechanical_failure_model.joblib"
    joblib.dump({"pipeline": pipe, "features": feature_cols, "metrics": metrics}, out)
    print(f"  ✅ Guardado: {out}")
    return metrics


def train_position(data_dir: Path, out_dir: Path) -> dict:
    print("\n🏆 Entrenando modelo de Posición Final (podio)...")
    df = build_position_features(
        races_csv        = str(data_dir / "races.csv"),
        results_csv      = str(data_dir / "results.csv"),
        qualifying_csv   = str(data_dir / "qualifying.csv"),
        constructors_csv = str(data_dir / "constructors.csv"),
    )
    feature_cols = [c for c in df.columns
                    if c not in ("raceId", "driverId", "constructorId", "podium")]
    X = df[feature_cols].values
    y = df["podium"].values

    clf  = make_classifier("pos")
    pipe = make_pipeline(clf)
    metrics = evaluate(pipe, X, y, "Predicción de Podio")
    metrics["features"] = feature_cols
    metrics["feature_importance"] = get_feature_importance(pipe, feature_cols)

    out = out_dir / "position_model.joblib"
    joblib.dump({"pipeline": pipe, "features": feature_cols, "metrics": metrics}, out)
    print(f"  ✅ Guardado: {out}")
    return metrics


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", required=True, help="Directorio con CSVs Ergast")
    parser.add_argument("--events",   required=True, help="CSV Race Events (jtrotman)")
    parser.add_argument("--out-dir",  default="models_trained/")
    parser.add_argument("--models",   default="sc,dnf,pos",
                        help="Modelos a entrenar separados por coma: sc,dnf,pos")
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    out_dir  = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    to_train = set(args.models.split(","))
    all_metrics = {}

    print(f"\n{'═'*55}")
    print(f"  F1 Analytics — Entrenamiento de modelos ML")
    print(f"  Backend: {BACKEND}")
    print(f"{'═'*55}")

    if "sc" in to_train:
        all_metrics["safety_car"] = train_safety_car(data_dir, args.events, out_dir)
    if "dnf" in to_train:
        all_metrics["mechanical_failure"] = train_mechanical_failure(data_dir, out_dir)
    if "pos" in to_train:
        all_metrics["position"] = train_position(data_dir, out_dir)

    # Guardar métricas consolidadas
    metrics_path = out_dir / "training_metrics.json"
    with open(metrics_path, "w") as f:
        json.dump(all_metrics, f, indent=2)
    print(f"\n📊 Métricas guardadas en: {metrics_path}")
    print("\n✅ Entrenamiento completado\n")


if __name__ == "__main__":
    main()
