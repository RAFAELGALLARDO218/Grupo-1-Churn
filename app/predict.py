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
    """Carga el modelo guardado"""
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"No existe el modelo en: {MODEL_PATH}")
    return joblib.load(MODEL_PATH)

def predict_churn(features: dict):
    """
    Función original de predicción de churn con reglas simples
    Más la integración del modelo de matrícula
    """
    
    tenure = features.get('tenure', 0)
    monthly_charges = features.get('monthly_charges', 0)
    contract = features.get('contract', 'Month-to-month')
    
    if contract == 'Month-to-month' and monthly_charges > 70:
        prediction = 1
        risk = "Alto"
        reason = "Contrato mensual con cargo alto"
    elif tenure < 12 and monthly_charges > 60:
        prediction = 1
        risk = "Medio-Alto"
        reason = "Cliente nuevo con cargo elevado"
    elif tenure < 6:
        prediction = 1
        risk = "Medio"
        reason = "Cliente muy nuevo"
    elif contract == 'Two year' and tenure > 24:
        prediction = 0
        risk = "Bajo"
        reason = "Cliente con contrato largo y antigüedad"
    else:
        prediction = 0
        risk = "Bajo"
        reason = "Cliente estable"
    
    try:
        # Cargar modelo
        model = load_model()
        
        # Preparar datos para el modelo
        data = pd.DataFrame([features], columns=FEATURE_COLUMNS)
        
        # Hacer predicción
        pred_matricula = model.predict(data)[0]
        probs = model.predict_proba(data)[0]
        
        # Resultados de matrícula
        matricula_pred = int(pred_matricula)
        matricula_label = "SI" if matricula_pred == 1 else "NO"
        prob_no = float(probs[0])
        prob_si = float(probs[1])
        
    except Exception as e:
        matricula_pred = None
        matricula_label = "Error"
        prob_no = None
        prob_si = None
        error_modelo = str(e)
    
    result = {
        # Resultados de Churn
        "churn_prediction": prediction,
        "churn_label": "Churn" if prediction == 1 else "No Churn",
        "risk_level": risk,
        "churn_reason": reason,
        
        # Resultados de Matrícula
        "matricula_prediction": matricula_pred,
        "matricula_label": matricula_label,
        "probability_no": prob_no,
        "probability_si": prob_si,
    }
    
    # Agregar error si existe
    if 'error_modelo' in locals():
        result["error"] = error_modelo
    
    return result

def predict_matriculado(payload: dict):
    """
    Función independiente que solo predice matrícula (mantenida por compatibilidad)
    """
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