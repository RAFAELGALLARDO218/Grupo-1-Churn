from pathlib import Path
import joblib
import pandas as pd
import numpy as np

# ========== RUTAS DE MODELOS ==========
MODEL_CHURN_PATH = Path("artifacts/predictor_churn_tree.joblib")  # Modelo de churn

# ========== COLUMNAS DEL DATASET ==========
FEATURE_COLUMNS = [
    "customerid",
    "gender",
    "seniorcitizen",
    "partner",
    "dependents",
    "tenure",
    "phoneservice",
    "multiplelines",
    "internetservice",
    "onlinesecurity",
    "onlinebackup",
    "deviceprotection",
    "techsupport",
    "streamingtv",
    "streamingmovies",
    "contract",
    "paperlessbilling",
    "paymentmethod",
    "monthlycharges",
    "totalcharges"
]

def load_model():
    """Carga el modelo guardado"""
    if not MODEL_CHURN_PATH.exists():
        raise FileNotFoundError(f"No existe el modelo en: {MODEL_CHURN_PATH}")
    return joblib.load(MODEL_CHURN_PATH)

def encode_features_for_model(features):
    """
    🔥 CONVIERTE TEXTO A NÚMEROS 🔥
    Esto es lo que faltaba en tu predict.py
    """
    encoded = features.copy()
    
    # Mapeo para variables binarias (Sí/No)
    binary_map = {
        'Yes': 1,
        'No': 0,
        'No phone service': 0,
        'No internet service': 0
    }
    
    # Mapeo para género
    gender_map = {
        'Female': 0,
        'Male': 1
    }
    
    # Mapeo para tipo de contrato
    contract_map = {
        'Month-to-month': 0,
        'One year': 1,
        'Two year': 2
    }
    
    # Mapeo para método de pago
    payment_map = {
        'Electronic check': 0,
        'Mailed check': 1,
        'Bank transfer (automatic)': 2,
        'Credit card (automatic)': 3
    }
    
    # Mapeo para servicio de internet
    internet_map = {
        'DSL': 1,
        'Fiber optic': 2,
        'No': 0
    }
    
    # Aplicar mapeos
    if 'gender' in encoded:
        encoded['gender'] = gender_map.get(encoded['gender'], 0)
    
    # Variables binarias
    binary_cols = ['partner', 'dependents', 'phoneservice', 'paperlessbilling',
                   'multiplelines', 'onlinesecurity', 'onlinebackup', 
                   'deviceprotection', 'techsupport', 'streamingtv', 'streamingmovies']
    for col in binary_cols:
        if col in encoded:
            encoded[col] = binary_map.get(encoded[col], 0)
    
    if 'internetservice' in encoded:
        encoded['internetservice'] = internet_map.get(encoded['internetservice'], 0)
    
    if 'contract' in encoded:
        encoded['contract'] = contract_map.get(encoded['contract'], 0)
    
    if 'paymentmethod' in encoded:
        encoded['paymentmethod'] = payment_map.get(encoded['paymentmethod'], 0)
    
    # Asegurar que todos los valores sean numéricos
    for key in encoded:
        if isinstance(encoded[key], str):
            try:
                encoded[key] = float(encoded[key])
            except:
                encoded[key] = 0
    
    return encoded

def predict_churn(features: dict):
    """
    Predicción de churn usando modelo ML + fallback con reglas
    """
    
    try:
        # ========== 1. INTENTAR CON MODELO ML ==========
        model = load_model()
        
        # Convertir texto a números
        features_encoded = encode_features_for_model(features.copy())
        
        # Preparar datos para el modelo
        data = pd.DataFrame([features_encoded], columns=FEATURE_COLUMNS)
        
        # Asegurar que todos los datos sean numéricos
        data = data.apply(pd.to_numeric, errors='coerce').fillna(0)
        
        # 🔥 PREDICCIÓN CON PROBABILIDADES 🔥
        pred_churn = model.predict(data)[0]
        probs = model.predict_proba(data)[0]
        
        # Verificar el orden de las clases
        # Si classes_ = [0, 1] → probs[0] = NO, probs[1] = SI
        prob_no = float(probs[0] * 100)  # Probabilidad de NO churn
        prob_si = float(probs[1] * 100)   # Probabilidad de SI churn
        
        # Determinar nivel de riesgo
        if prob_si > 70:
            risk = "Alto"
            reason = "Alta probabilidad de abandono"
        elif prob_si > 40:
            risk = "Medio"
            reason = "Riesgo moderado de abandono"
        else:
            risk = "Bajo"
            reason = "Cliente estable"
        
        churn_label = "Churn" if pred_churn == 1 else "No Churn"
        
        # ========== RESULTADO CON MODELO ==========
        return {
            "churn_prediction": int(pred_churn),
            "churn_label": churn_label,
            "risk_level": risk,
            "churn_reason": reason,
            "probability_no": round(prob_no, 2),
            "probability_si": round(prob_si, 2),
            "model_used": "ML"
        }
        
    except Exception as e:
        # ========== 2. FALLBACK CON REGLAS MANUALES ==========
        print(f"⚠️ Error en modelo ML, usando fallback: {e}")
        
        tenure = features.get('tenure', 0)
        monthly_charges = features.get('monthlycharges', 0)
        contract = features.get('contract', 'Month-to-month')
        
        # Manejar valores NaN
        if pd.isna(tenure):
            tenure = 0
        if pd.isna(monthly_charges):
            monthly_charges = 0
        if pd.isna(contract):
            contract = 'Month-to-month'
        
        # Lógica simple de predicción
        if contract == 'Month-to-month' and monthly_charges > 70:
            pred_churn = 1
            risk = "Alto"
            reason = "Contrato mensual con cargo alto"
            prob_no = 20.0
            prob_si = 80.0
        elif tenure < 12 and monthly_charges > 60:
            pred_churn = 1
            risk = "Medio-Alto"
            reason = "Cliente nuevo con cargo elevado"
            prob_no = 35.0
            prob_si = 65.0
        elif tenure < 6:
            pred_churn = 1
            risk = "Medio"
            reason = "Cliente muy nuevo"
            prob_no = 45.0
            prob_si = 55.0
        elif contract == 'Two year' and tenure > 24:
            pred_churn = 0
            risk = "Bajo"
            reason = "Cliente con contrato largo y antigüedad"
            prob_no = 90.0
            prob_si = 10.0
        else:
            pred_churn = 0
            risk = "Bajo"
            reason = "Cliente estable"
            prob_no = 75.0
            prob_si = 25.0
        
        churn_label = "Churn" if pred_churn == 1 else "No Churn"
        
        # ========== RESULTADO CON FALLBACK ==========
        return {
            "churn_prediction": int(pred_churn),
            "churn_label": churn_label,
            "risk_level": risk,
            "churn_reason": reason,
            "probability_no": prob_no,
            "probability_si": prob_si,
            "model_used": "Fallback (Reglas)",
            "error": str(e)
        }