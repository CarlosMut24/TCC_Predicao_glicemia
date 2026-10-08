import joblib
import pandas as pd
import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

# carrega o pipeline salvo
modelo = joblib.load("modelo_rf.joblib")

app = FastAPI(title="Glicose Predictor API")


class PacienteInput(BaseModel):
    metodo_medida: str
    glucose_level: float
    basal: float
    bolus_type: str
    bolus_dose: float
    meal_type: Optional[str] = None
    meal_carbs: float
    exercise_intensity: float
    doing_exercise: int


@app.get("/")
def root():
    return {"status": "ok", "modelo": "random_forest_glicose"}


@app.post("/predict")
def predict(dados: PacienteInput):
    try:
        # montar DataFrame com uma linha
        linha = dados.dict()

        # aplicar a regra de negócio (igual ao treino)
        if linha["meal_carbs"] == 0:
            linha["meal_type"] = "Fasting"
        if linha["meal_type"] is None:
            linha["meal_type"] = "Fasting"  # fallback

        df = pd.DataFrame([linha])

        # prever
        pred = modelo.predict(df)[0]

        return {
            "glicose_prevista_30min": float(pred),
            "unidade": "mg/dL",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/predict_batch")
def predict_batch(dados: list[PacienteInput]):
    linhas = []
    for d in dados:
        linha = d.dict()
        if linha["meal_carbs"] == 0:
            linha["meal_type"] = "Fasting"
        if linha["meal_type"] is None:
            linha["meal_type"] = "Fasting"
        linhas.append(linha)

    df = pd.DataFrame(linhas)
    preds = modelo.predict(df)
    return {"predicoes": [float(p) for p in preds]}