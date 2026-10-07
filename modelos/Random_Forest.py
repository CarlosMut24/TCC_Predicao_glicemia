import os
import pandas as pd
import joblib
from sklearn.ensemble import RandomForestRegressor
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_squared_error, root_mean_squared_error


def get_csv_root():
    try:
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        BASE_DIR = os.getcwd()
    return os.path.join(BASE_DIR, "..", "processado")


# ---- 1. Carregar ----
df_treinamento = pd.read_csv(os.path.join(get_csv_root(), "treinamento_final.csv"))
df_testes = pd.read_csv(os.path.join(get_csv_root(), "testes_final.csv"))

columns_used = ['metodo_medida', 'glucose_level', 'basal',
                'bolus_type', 'bolus_dose', 'meal_type', 'meal_carbs',
                'exercise_intensity', 'doing_exercise', 'target']

df_tr = df_treinamento[columns_used].copy()
df_val = df_testes[columns_used].copy()


# ---- 2. Regra de negócio (igual antes) ----
for df in (df_tr, df_val):
    df['meal_carbs'] = df['meal_carbs'].fillna(0)
    df['exercise_intensity'] = df['exercise_intensity'].fillna(0)
    df.loc[df["meal_carbs"] == 0, "meal_type"] = "Fasting"

# ---- 2.5. Remover linhas sem alvo ----
df_tr = df_tr.dropna(subset=["target"]).reset_index(drop=True)
df_val = df_val.dropna(subset=["target"]).reset_index(drop=True)


# ---- 3. Separar X e y ----
y_tr = df_tr["target"]
X_tr = df_tr.drop(columns=["target"])

y_val = df_val["target"]
X_val = df_val.drop(columns=["target"])


# ---- 4. Identificar colunas numéricas e categóricas ----
num_cols = X_tr.select_dtypes(include=["int64", "float64", "bool"]).columns.tolist()
cat_cols = X_tr.select_dtypes(include=["object", "category"]).columns.tolist()

print("Numéricas:", num_cols)
print("Categóricas:", cat_cols)


# ---- 5. Pipeline ----
preprocessador = ColumnTransformer([
    ("num", SimpleImputer(strategy="median"), num_cols),
    ("cat", Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore")),
    ]), cat_cols),
])

pipeline = Pipeline([
    ("preprocessador", preprocessador),
    ("rf", RandomForestRegressor(
        n_estimators=3000,
        min_samples_leaf=10,
        random_state=0,
        n_jobs=-1,
    )),
])

pipeline.fit(X_tr, y_tr)


# ---- 6. Avaliar ----
p = pipeline.predict(X_val)
mse = mean_squared_error(y_val, p)
rmse = root_mean_squared_error(y_val, p)
print(f"MSE: {mse}")
print(f"RMSE: {rmse}")


# ---- 7. Salvar ----
joblib.dump(pipeline, "modelo_rf.joblib")
print("Modelo salvo em modelo_rf.joblib")