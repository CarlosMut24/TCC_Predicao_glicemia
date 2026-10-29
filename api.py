import os
import joblib
import pandas as pd
import numpy as np
import shap
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from huggingface_hub import hf_hub_download

# ============================================================
# 1. Definição da classe (necessária para o joblib conseguir carregar o Pipeline)
# ============================================================
from sklearn.base import BaseEstimator, TransformerMixin

class FeaturesTemporais(BaseEstimator, TransformerMixin):
    """Gera features temporais a partir da coluna 'ts' e a remove."""
    def __init__(self, coluna_timestamp="ts"):
        self.coluna_timestamp = coluna_timestamp

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        X = X.copy()
        dt = pd.to_datetime(X[self.coluna_timestamp])
        h = dt.dt.hour + dt.dt.minute / 60
        X["hora_sin"] = np.sin(2 * np.pi * h / 24)
        X["hora_cos"] = np.cos(2 * np.pi * h / 24)
        d = dt.dt.dayofweek
        X["dia_sin"] = np.sin(2 * np.pi * d / 7)
        X["dia_cos"] = np.cos(2 * np.pi * d / 7)
        X["fim_de_semana"] = (d >= 5).astype(int)
        X["madrugada"] = dt.dt.hour.isin([0,1,2,3,4,5]).astype(int)
        X["pos_cafe"] = dt.dt.hour.between(7, 10).astype(int)
        X["pos_almoco"] = dt.dt.hour.between(12, 15).astype(int)
        X["pos_jantar"] = dt.dt.hour.between(19, 22).astype(int)
        X = X.drop(columns=[self.coluna_timestamp])
        return X


# ============================================================
# 2. Carregar modelo e criar o explicador SHAP
# ============================================================
modelo_path = hf_hub_download(
    repo_id="CarlosMUT/TCC_Glicemia_RF",
    filename="modelo_rf_app.joblib",
)
modelo = joblib.load(modelo_path)

# Extrair o RF de dentro do pipeline e criar o explicador
rf = modelo.named_steps["rf"]
explainer = shap.TreeExplainer(rf)
feature_names = modelo.named_steps["preprocessador"].get_feature_names_out()


# ============================================================
# 3. FastAPI
# ============================================================
app = FastAPI(title="Glicose Predictor API")


class PacienteInput(BaseModel):
    glucose_level: float
    metodo_medida: str
    ts: str                       
    meal_type: Optional[str] = None
    meal_carbs: float
    bolus_type: str
    bolus_dose: float
    basal: float
    doing_exercise: int
    exercise_intensity: float
    tempo_desde_ultima_medicao: float
    glucose_delta_desde_ultima: float
    iob: float
    cob: float
    is_cgm: int


def _aplicar_regras_negocio(linha: dict) -> dict:
    """Regra: meal_carbs==0 -> meal_type='Fasting'."""
    if linha.get("meal_carbs", 0) == 0 or linha.get("meal_type") is None:
        linha["meal_type"] = "Fasting"
    return linha


def _explicar(df_bruto: pd.DataFrame, top_k: int = 4) -> dict:
    """Retorna predição + top_k features que mais contribuíram."""
    pred = modelo.predict(df_bruto)[0]

    # Transformar até o pré-processador
    X_trans = modelo[:-1].transform(df_bruto)
    if hasattr(X_trans, "toarray"):
        X_trans = X_trans.toarray()

    sv = explainer.shap_values(X_trans)[0]
    base = explainer.expected_value

    contribuicoes = [
        {
            "feature": str(nome).split("__", 1)[-1],  # remove num__/cat__/remainder__
            "valor": float(vlr),
            "impacto_mgdl": float(s),
        }
        for nome, vlr, s in zip(feature_names, X_trans[0], sv)
    ]
    contribuicoes.sort(key=lambda x: abs(x["impacto_mgdl"]), reverse=True)

    return {
        "predicao_mgdl": float(pred),
        "valor_base_mgdl": float(base),
        "principais_fatores": contribuicoes[:top_k],
    }


@app.get("/")
def root():
    return {"status": "ok", "modelo": "random_forest_glicose"}


@app.post("/predict")
def predict(dados: PacienteInput):
    try:
        linha = _aplicar_regras_negocio(dados.model_dump())
        df = pd.DataFrame([linha])
        pred = modelo.predict(df)[0]
        return {"glicose_prevista_2h": float(pred), "unidade": "mg/dL"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/predict_explain")
def predict_explain(dados: PacienteInput):
    """Predição + explicação SHAP dos principais fatores."""
    try:
        linha = _aplicar_regras_negocio(dados.model_dump())
        df = pd.DataFrame([linha])
        return _explicar(df)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/predict_batch")
def predict_batch(dados: list[PacienteInput]):
    try:
        linhas = [_aplicar_regras_negocio(d.model_dump()) for d in dados]
        df = pd.DataFrame(linhas)
        preds = modelo.predict(df)
        return {"predicoes": [float(p) for p in preds]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# FEATURES = [
#     "glucose_level",
#     "glucose_delta_5",
#     "glucose_delta_15",
#     "glucose_delta_30",
#     "glucose_ma_15",
#     "glucose_ma_30",
#     "glucose_std_30",
#     "hora_sin",
#     "hora_cos",
#     "dia_sin",
#     "dia_cos",
#     "fim_de_semana",
#     "madrugada",
#     "pos_cafe",
#     "pos_almoco",
#     "pos_jantar",
#     "meal_carbs",
#     "bolus_dose",
#     "basal",
#     "iob", 
#     "cob"]

# @app.post("/predict_lstm")
# def predict_lstm(dados: PacienteInput):
#     # 1. Monta o DataFrame bruto com o histórico
#     df = pd.DataFrame(dados.historico)  # lista de dicts com ts, glucose_level, etc.
    
#     # 2. Transforma ts em features
#     df = adicionar_features_temporais(df)
    
#     # 3. Pega a última janela de WINDOW_SIZE (24)
#     # (aqui você isola a linha atual e as 23 anteriores)
#     features_array = df[FEATURES].values[-24:]
    
#     # 4. Normaliza com o scaler salvo
#     X = scaler.transform(features_array.reshape(-1, len(FEATURES))).reshape(1, 24, len(FEATURES))
    
#     # 5. Prediz
#     pred = modelo.predict(X)[0][0]
    
#     return {"glicose_prevista_30min": float(pred)}
