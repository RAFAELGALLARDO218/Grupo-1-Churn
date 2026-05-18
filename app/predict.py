import os
import joblib
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

_model = None

def load_model():
    global _model
    if _model is None:
        model_path = os.path.join("artifacts", "matriculado_model.joblib")
        if os.path.exists(model_path):
            _model = joblib.load(model_path)
    return _model

def predict_matriculado(features: dict):
    # Versión temporal mientras no hay modelo entrenado
    return {
        "prediccion": "NO",
        "probabilidad": 0.35,
        "mensaje": "Modelo en entrenamiento - predicción temporal"
    } 
