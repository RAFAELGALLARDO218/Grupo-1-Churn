

def predict_churn(features: dict):
    
    # Reglas simples para demostración
    tenure = features.get('tenure', 0)
    monthly_charges = features.get('monthly_charges', 0)
    contract = features.get('contract', 'Month-to-month')
    
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
    
    return {
        "prediction": prediction,
        "prediction_label": "Churn" if prediction == 1 else "No Churn",
        "risk_level": risk,
        "reason": reason,
        "note": "Predicción basada en reglas (modelo no implementado según indicación del profesor)"
    }