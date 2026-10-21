import numpy as np
import pandas as pd
import os
import tensorflow as tf
from sklearn.preprocessing import StandardScaler
from tensorflow.keras import layers, models
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau


def get_csv_root():
    try:
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        BASE_DIR = os.getcwd()
    return os.path.join(BASE_DIR, "..", "processado")

# --- Configurações ---
WINDOW_SIZE = 24       # 24 passos * 5 min = 120 min de histórico
HORIZON = 6            # 6 passos * 5 min = 30 min à frente
STEP = 1               # desliza 1 passo por vez (pode ser 1, 2, 3...)

def criar_janelas(df, feature_cols, target_col="target"):
    """
    Para cada paciente, cria janelas deslizantes.
    Retorna X (n, WINDOW_SIZE, n_features) e y (n,).
    """
    X_list, y_list = [], []

    for pid in df["id_patient"].unique():
        sub = df[df["id_patient"] == pid].sort_values("ts").reset_index(drop=True)

        # Extrai arrays
        feats = sub[feature_cols].values
        target = sub[target_col].values

        # Para cada posição onde há janela completa + target disponível
        for i in range(WINDOW_SIZE, len(sub) - HORIZON + 1):
            # janela de entrada
            janela = feats[i - WINDOW_SIZE:i]

            # target: glicose HORIZON passos à frente
            # Como já temos a coluna "target" (glicose em 30 min),
            # basta pegá-la na posição i
            y_val = target[i]

            if np.isnan(y_val):   # pula se target for NaN
                continue

            X_list.append(janela)
            y_list.append(y_val)

    return np.array(X_list), np.array(y_list)

def criar_modelo(window_size, n_features):
    model = models.Sequential([
        layers.Input(shape=(window_size, n_features)),

        # LSTM: 64 unidades, retorna apenas o último output
        layers.LSTM(64, return_sequences=False),

        # Dropout para regularizar
        layers.Dropout(0.2),

        # Camada densa intermediária
        layers.Dense(32, activation="relu"),

        # Saída: um único valor (glicose em mg/dL)
        layers.Dense(1),
    ])

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
        loss="mse",          # MSE para regressão
        metrics=["mae"],
    )
    return model

# ---- 1. Carregar ----
df_treinamento = pd.read_csv(os.path.join(get_csv_root(), "treinamento_final.csv"))
df_testes = pd.read_csv(os.path.join(get_csv_root(), "testes_final.csv"))

columns_used = [c for c in df_treinamento.columns if c != "id_patient"]
feature_cols = ['timestamp', 'metodo_medida', 'glucose_level', 'basal', 'bolus_type',
       'bolus_dose', 'meal_type', 'meal_carbs', 'meal_time',
       'exercise_intensity', 'doing_exercise', 'target',
       'iob', 'cob']

df_tr = df_treinamento[columns_used].copy()
df_val = df_testes[columns_used].copy()

df_tr = df_tr.rename(columns={"ts": "timestamp"})
df_val = df_val.rename(columns={"ts": "timestamp"})

# ---- 2. Regra de negócio (igual antes) ----
for df in (df_tr, df_val):
    df['meal_carbs'] = df['meal_carbs'].fillna(0)
    df['exercise_intensity'] = df['exercise_intensity'].fillna(0)
    df.loc[df["meal_carbs"] == 0, "meal_type"] = "Fasting"

# ---- 2.5. Remover linhas sem alvo ----
print(f"Tr antes: {len(df_treinamento)}")

for df in (df_tr, df_val):
    df.dropna(subset=["target", "glucose_level"], inplace=True)
    df.reset_index(drop=True, inplace=True)

print(f"Tr depois: {len(df_tr)}")
print(f"Perdidas: {len(df_treinamento) - len(df_tr)} ({100*(1 - len(df_tr)/len(df_treinamento)):.1f}%)")

# ---- 3. Separar X e y ----
y_tr = df_tr["target"]
X_tr = df_tr.drop(columns=["target"])

y_val = df_val["target"]
X_val = df_val.drop(columns=["target"])

# ---- 4. Identificar colunas numéricas e categóricas ----
num_cols = X_tr.select_dtypes(include=["int64", "float64", "bool"]).columns.tolist()
cat_cols = [c for c in X_tr.select_dtypes(include=["object", "category"]).columns if c != "timestamp"]


print("Numéricas:", num_cols)
print("Categóricas:", cat_cols)