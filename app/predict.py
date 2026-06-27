from pathlib import Path
import joblib
import pandas as pd

MODEL_PATH = Path("artifacts/predictor_matricula_tree.joblib")

FEATURE_COLUMNS = [
    "periodo",
    "sexo",
    "preferencia",
    "carrera",
    "facultad",
    "puntaje",
    "grupo_depen",
    "region",
    "latitud",
    "longitud",
    "ptje_nem",
    "psu_promlm",
    "pace",
    "gratuidad",
]

def load_model():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"No existe el modelo en: {MODEL_PATH}")
    return joblib.load(MODEL_PATH)

def predict_matriculado(payload: dict):
    model = load_model()

    data = pd.DataFrame([payload], columns=FEATURE_COLUMNS)

    pred = model.predict(data)[0]
    probs = model.predict_proba(data)[0]

    return {
        "predicted_class": int(pred),
        "predicted_label": "SI" if int(pred) == 1 else "NO",
        "probability_no": float(probs[0]),
        "probability_si": float(probs[1]),
    }
