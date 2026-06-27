from pathlib import Path
import joblib
import pandas as pd
import numpy as np


MODEL_CHURN_PATH = Path("artifacts/predictor_matricula_tree.joblib")


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

#Escalados para mostrar probabilidad
SCALER_MEANS = {
    'customerid': 3500.0,        
    'seniorcitizen': 0.16,     
    'tenure': 37.5,             
    'monthlycharges': 64.8,     
    'totalcharges': 2500.0      
}

SCALER_STDS = {
    'customerid': 2000.0,        
    'seniorcitizen': 0.37,          
    'tenure': 24.5,             
    'monthlycharges': 30.0,      
    'totalcharges': 1800.0       
}

NUMERIC_COLS_TO_SCALE = ['customerid', 'seniorcitizen', 'tenure', 'monthlycharges', 'totalcharges']

def load_model():
    """Carga el modelo guardado"""
    if not MODEL_CHURN_PATH.exists():
        raise FileNotFoundError(f"No existe el modelo en: {MODEL_CHURN_PATH}")
    return joblib.load(MODEL_CHURN_PATH)

def encode_features_for_model(features):

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
        if isinstance(encoded['gender'], str):
            encoded['gender'] = gender_map.get(encoded['gender'], 0)
        else:
            encoded['gender'] = int(encoded['gender'])
    
    # Variables binarias
    binary_cols = ['partner', 'dependents', 'phoneservice', 'paperlessbilling',
                   'multiplelines', 'onlinesecurity', 'onlinebackup', 
                   'deviceprotection', 'techsupport', 'streamingtv', 'streamingmovies']
    for col in binary_cols:
        if col in encoded:
            if isinstance(encoded[col], str):
                encoded[col] = binary_map.get(encoded[col], 0)
            else:
                encoded[col] = int(encoded[col])
    
    if 'internetservice' in encoded:
        if isinstance(encoded['internetservice'], str):
            encoded['internetservice'] = internet_map.get(encoded['internetservice'], 0)
        else:
            encoded['internetservice'] = int(encoded['internetservice'])
    
    if 'contract' in encoded:
        if isinstance(encoded['contract'], str):
            encoded['contract'] = contract_map.get(encoded['contract'], 0)
        else:
            encoded['contract'] = int(encoded['contract'])
    
    if 'paymentmethod' in encoded:
        if isinstance(encoded['paymentmethod'], str):
            encoded['paymentmethod'] = payment_map.get(encoded['paymentmethod'], 0)
        else:
            encoded['paymentmethod'] = int(encoded['paymentmethod'])
    
    # Asegurar que todos los valores sean numéricos
    for key in encoded:
        if isinstance(encoded[key], str):
            try:
                encoded[key] = float(encoded[key])
            except:
                encoded[key] = 0
    
    return encoded

def scale_features(features):

    scaled = features.copy()
    
    for col in NUMERIC_COLS_TO_SCALE:
        if col in scaled:
            mean = SCALER_MEANS.get(col, 0)
            std = SCALER_STDS.get(col, 1)
            if std > 0:
                scaled[col] = (scaled[col] - mean) / std
            else:
                scaled[col] = 0
    
    return scaled

def predict_churn(features: dict):
    """
    Predicción de churn con PROBABILIDADES REALES
    """
    
    try:
        model = load_model()
        
        features_encoded = encode_features_for_model(features.copy())
        
        features_scaled = scale_features(features_encoded)
        
        data = pd.DataFrame([features_scaled], columns=FEATURE_COLUMNS)
        data = data.apply(pd.to_numeric, errors='coerce').fillna(0)
        
        pred_churn = model.predict(data)[0]
        probs = model.predict_proba(data)[0]
        
        # Obtener probabilidades reales (NO FORZADAS)
        prob_no = float(probs[0] * 100)  
        prob_si = float(probs[1] * 100)  
        
        # Determinar nivel de riesgo basado en probabilidad real
        if prob_si > 70:
            risk = "Alto"
            reason = f"Alta probabilidad de abandono ({prob_si:.1f}%)"
        elif prob_si > 40:
            risk = "Medio"
            reason = f"Riesgo moderado de abandono ({prob_si:.1f}%)"
        else:
            risk = "Bajo"
            reason = f"Cliente estable ({prob_si:.1f}% de riesgo)"
        
        churn_label = "Churn" if pred_churn == 1 else "No Churn"
        
        return {
            "churn_prediction": int(pred_churn),
            "churn_label": churn_label,
            "risk_level": risk,
            "churn_reason": reason,
            "probability_no": round(prob_no, 2),
            "probability_si": round(prob_si, 2),
            "model_used": "ML con Scaler (Probabilidades Reales)"
        }
        
    except Exception as e:
        print(f"Error en modelo ML, usando fallback: {e}")
        
        tenure = features.get('tenure', 0)
        monthly_charges = features.get('monthlycharges', 0)
        contract = features.get('contract', 'Month-to-month')
        
        if pd.isna(tenure):
            tenure = 0
        if pd.isna(monthly_charges):
            monthly_charges = 0
        
        if isinstance(contract, str):
            if contract == 'Two year' or contract == '2':
                contract_type = 2
            elif contract == 'One year' or contract == '1':
                contract_type = 1
            else:
                contract_type = 0
        else:
            contract_type = int(contract)
        
        # Reglas con probabilidades realistas
        if contract_type == 0 and monthly_charges > 70:
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
        elif contract_type == 2 and tenure > 24:
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