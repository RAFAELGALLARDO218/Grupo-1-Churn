from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from app.db import test_connection, get_postulaciones, get_postulaciones_stats
from app.predict import predict_matriculado

app = FastAPI(title="MVP DataOps Docente")

class PredictMatriculadoRequest(BaseModel):
    periodo: int
    sexo: str
    preferencia: int
    carrera: str
    facultad: str
    puntaje: int
    grupo_depen: str
    region: str
    latitud: float
    longitud: float
    ptje_nem: int
    psu_promlm: int
    pace: str
    gratuidad: str

@app.get("/")
def root():
    return {"message": "API MVP DataOps Docente activa"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/db-health")
def db_health():
    return test_connection()

@app.get("/postulaciones-demo")
def postulaciones_demo(limit: int = Query(default=20, ge=1, le=100)):
    try:
        data = get_postulaciones(limit=limit)
        return {
            "status": "ok",
            "count": len(data),
            "limit": limit,
            "data": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/postulaciones-demo/stats")
def postulaciones_demo_stats():
    try:
        stats = get_postulaciones_stats()
        return {
            "status": "ok",
            "stats": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/predict-matriculado")
def predict_matriculado_endpoint(payload: PredictMatriculadoRequest):
    try:
        result = predict_matriculado(payload.model_dump())
        return {
            "status": "ok",
            "prediction": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
