import joblib
import pandas as pd
import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from huggingface_hub import hf_hub_download
import os

# carrega o pipeline salvo
# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# modelo = joblib.load(os.path.join(BASE_DIR, "modelo_rf.joblib"))

def adicionar_features_temporais(df):
    """Transforma 'ts' em features numéricas cíclicas e flags."""
    df = df.copy()
    dt = pd.to_datetime(df["ts"])

    # Hora do dia (cíclica)
    h = dt.dt.hour + dt.dt.minute / 60
    df["hora_sin"] = np.sin(2 * np.pi * h / 24)
    df["hora_cos"] = np.cos(2 * np.pi * h / 24)

    # Dia da semana (cíclico)
    d = dt.dt.dayofweek
    df["dia_sin"] = np.sin(2 * np.pi * d / 7)
    df["dia_cos"] = np.cos(2 * np.pi * d / 7)

    # Flags
    df["fim_de_semana"] = (d >= 5).astype(int)
    df["madrugada"]     = dt.dt.hour.isin([0, 1, 2, 3, 4, 5]).astype(int)
    df["pos_cafe"]      = dt.dt.hour.between(7, 10).astype(int)
    df["pos_almoco"]    = dt.dt.hour.between(12, 15).astype(int)
    df["pos_jantar"]    = dt.dt.hour.between(19, 22).astype(int)

    return df

FEATURES = [
    "glucose_level",
    "glucose_delta_5",
    "glucose_delta_15",
    "glucose_delta_30",
    "glucose_ma_15",
    "glucose_ma_30",
    "glucose_std_30",
    "hora_sin",
    "hora_cos",
    "dia_sin",
    "dia_cos",
    "fim_de_semana",
    "madrugada",
    "pos_cafe",
    "pos_almoco",
    "pos_jantar",
    "meal_carbs",
    "bolus_dose",
    "basal",
    "iob", 
    "cob"]

modelo_path = hf_hub_download(
    repo_id="CarlosMUT/TCC_Glicemia_RF",
    filename="modelo_lstm.keras",
)
scaler_path = hf_hub_download(
    repo_id="CarlosMUT/TCC_Glicemia_RF",
    filename="scaler_lstm.pkl",
)
modelo = joblib.load(modelo_path)
scaler = joblib.load(scaler_path)

app = FastAPI(title="Glicose Predictor API")

class PacienteInput(BaseModel):
    glucose_level: float
    glucose_delta_5: float
    glucose_delta_15: float
    glucose_delta_30: float
    glucose_ma_15: float
    glucose_ma_30: float
    glucose_std_30: float
    ts: str
    basal: float
    bolus_dose: float
    meal_carbs: float


@app.get("/")
def root():
    return {"status": "ok", "modelo": "random_forest_glicose"}

@app.post("/predict_lstm")
def predict_lstm(dados: PacienteInput):
    # 1. Monta o DataFrame bruto com o histórico
    df = pd.DataFrame(dados.historico)  # lista de dicts com ts, glucose_level, etc.
    
    # 2. Transforma ts em features
    df = adicionar_features_temporais(df)
    
    # 3. Pega a última janela de WINDOW_SIZE (24)
    # (aqui você isola a linha atual e as 23 anteriores)
    features_array = df[FEATURES].values[-24:]
    
    # 4. Normaliza com o scaler salvo
    X = scaler.transform(features_array.reshape(-1, len(FEATURES))).reshape(1, 24, len(FEATURES))
    
    # 5. Prediz
    pred = modelo.predict(X)[0][0]
    
    return {"glicose_prevista_30min": float(pred)}


# @app.post("/predict")
# def predict(dados: PacienteInput):
#     try:
#         # montar DataFrame com uma linha
#         linha = dados.dict()

#         # aplicar a regra de negócio (igual ao treino)
#         if linha["meal_carbs"] == 0:
#             linha["meal_type"] = "Fasting"
#         if linha["meal_type"] is None:
#             linha["meal_type"] = "Fasting"  # fallback

#         df = pd.DataFrame([linha])

#         # prever
#         pred = modelo.predict(df)[0]

#         return {
#             "glicose_prevista_30min": float(pred),
#             "unidade": "mg/dL",
#         }
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


# @app.post("/predict_batch")
# def predict_batch(dados: list[PacienteInput]):
#     linhas = []
#     for d in dados:
#         linha = d.dict()
#         if linha["meal_carbs"] == 0:
#             linha["meal_type"] = "Fasting"
#         if linha["meal_type"] is None:
#             linha["meal_type"] = "Fasting"
#         linhas.append(linha)

#     df = pd.DataFrame(linhas)
#     preds = modelo.predict(df)
#     return {"predicoes": [float(p) for p in preds]}

