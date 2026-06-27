from pathlib import Path
import joblib
import pandas as pd
import numpy as np

MODEL_PATH = Path("artifacts/predictor_matricula_tree.joblib")

# ========== VARIABLES DE TELCO ==========
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
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"No existe el modelo en: {MODEL_PATH}")
    return joblib.load(MODEL_PATH)

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
        'DSL': 0,
        'Fiber optic': 1,
        'No': 2
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
        encoded['internetservice'] = internet_map.get(encoded['internetservice'], 2)
    
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
    Predicción de churn con reglas simples
    + integración del modelo de matrícula
    """
    
    # ========== PARTE 1: PREDICCIÓN CHURN ==========
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
    
    # ========== PARTE 2: PREDICCIÓN MATRÍCULA ==========
    try:
        model = load_model()
        
        # 🔥 CONVERTIR TEXTO A NÚMEROS ANTES DE PASAR AL MODELO 🔥
        features_encoded = encode_features_for_model(features.copy())
        
        # Preparar datos para el modelo
        data = pd.DataFrame([features_encoded], columns=FEATURE_COLUMNS)
        
        # Asegurar que todos los datos sean numéricos
        data = data.apply(pd.to_numeric, errors='coerce').fillna(0)
        
        # Hacer predicción
        pred_matricula = model.predict(data)[0]
        probs = model.predict_proba(data)[0]
        
        matricula_pred = int(pred_matricula)
        matricula_label = "SI" if matricula_pred == 1 else "NO"
        prob_no = float(probs[0]) * 100  # Convertir a porcentaje
        prob_si = float(probs[1]) * 100   # Convertir a porcentaje
        
    except Exception as e:
        matricula_pred = None
        matricula_label = "Error"
        prob_no = None
        prob_si = None
        error_modelo = str(e)
    
    # ========== RESULTADO ==========
    result = {
        "churn_prediction": prediction,
        "churn_label": "Churn" if prediction == 1 else "No Churn",
        "risk_level": risk,
        "churn_reason": reason,
        "matricula_prediction": matricula_pred,
        "matricula_label": matricula_label,
        "probability_no": prob_no,
        "probability_si": prob_si,
    }
    
    if 'error_modelo' in locals():
        result["error"] = error_modelo
    
    return result