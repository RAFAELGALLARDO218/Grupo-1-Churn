
# ============================================================
# API para Churn - Sirve los endpoints
# ============================================================

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from app.db import test_connection, get_churn_data, get_churn_statistics
from app.predict import predict_churn

app = FastAPI(title="API Churn Prediction")

# ============================================================
# MODELO DE DATOS PARA PREDICCIÓN
# ============================================================

class PredictChurnRequest(BaseModel):
    customerid: int
    gender: str
    seniorcitizen: int
    partner: str
    dependents: str
    tenure: int
    phoneservice: str
    multiplelines: str
    internetservice: str
    onlinesecurity: str
    onlinebackup: str
    deviceprotection: str
    techsupport: str
    streamingtv: str
    streamingmovies: str
    contract: str
    paperlessbilling: str
    paymentmethod: str
    monthlycharges: float
    totalcharges: float

# ============================================================
# ENDPOINTS
# ============================================================

@app.get("/")
def root():
    return {"message": "API Churn Prediction activa"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/db-health")
def db_health():
    return test_connection()

@app.get("/churn-clientes")
def get_churn_clientes(limit: int = Query(default=20, ge=1, le=70000)):
    try:
        data = get_churn_data(limit=limit)
        return {
            "status": "ok",
            "count": len(data),
            "limit": limit,
            "data": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/churn-clientes/stats")
def get_churn_stats():
    try:
        stats = get_churn_statistics()
        return {
            "status": "ok",
            "stats": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/predict-churn")
def predict_churn_endpoint(payload: PredictChurnRequest):
    try:
        result = predict_churn(payload.model_dump())
        return {
            "status": "ok",
            "prediction": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

