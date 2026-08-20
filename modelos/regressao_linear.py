import os
import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
from sklearn.metrics import mean_absolute_error as MAE
from sklearn import model_selection as ms
from sklearn.linear_model import LinearRegression

def get_csv_root():
    try:
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        BASE_DIR = os.getcwd()
    return os.path.join(BASE_DIR, "..", "processado")

df_paciente = pd.read_csv(os.path.join(get_csv_root(), "paciente.cvs"))
df_final = pd.read_csv(os.path.join(get_csv_root(), "final.cvs"))

df_LRegression = df_final[['glucose_level', 'basal', 'bolus_dose', 'meal_carbs', 'sleeping',
    'sleep_quality', 'exercise_intensity', 'doing_exercise', 'target']]

df_LRegression_dummies = df_final[['metodo_medida', 'glucose_level', 'basal',
       'bolus_type', 'bolus_dose', 'meal_type', 'meal_carbs', 'sleeping',
       'sleep_quality', 'exercise_intensity', 'doing_exercise', 'target']]

zero_columns = ['meal_carbs', 'sleep_quality', 'exercise_intensity']
df_LRegression[zero_columns] = df_LRegression[zero_columns].fillna(0)
df_LRegression_dummies[zero_columns] = df_LRegression_dummies[zero_columns].fillna(0)

df_LRegression_dummies = pd.get_dummies(df_LRegression_dummies)

df_LRegression = df_LRegression.dropna()
df_LRegression_dummies = df_LRegression_dummies.dropna()

X = df_LRegression.drop(columns=['target'])
Y = df_LRegression.loc[:, 'target']

X_dummies = df_LRegression_dummies.drop(columns=['target'])
Y_dummies = df_LRegression_dummies.loc[:, 'target']

X_train, X_test, Y_train, Y_test = ms.train_test_split(X,Y, test_size= 1/3, random_state=2)
X_trainD, X_testD, Y_trainD, Y_testD = ms.train_test_split(X_dummies, Y_dummies,
                                                            test_size= 1/3, random_state=2)

modelo = LinearRegression()
modelo_D = LinearRegression()
modelo.fit(X_train, Y_train)
modelo_D.fit(X_trainD, Y_trainD)

Y_pred = modelo.predict(X_test).ravel()
Y_pred_dummies = modelo_D.predict(X_testD).ravel()

result = pd.DataFrame({
    'Y_pred': np.round(Y_pred, 2),
    'Y_test': Y_test.to_numpy(),
    'miss': abs(np.round(Y_pred, 0) - Y_test.to_numpy())
})

resultD = pd.DataFrame({
    'Y_pred': np.round(Y_pred_dummies, 2),
    'Y_test': Y_testD.to_numpy(),
    'miss': abs(Y_pred_dummies - Y_testD.to_numpy())
})

print(f"techa de erro sem dummies: {np.round(sum(result["miss"])/len(result["miss"]),2)}")
print(f"techa de erro com dummies: {np.round(sum(resultD["miss"])/len(resultD["miss"]),2)}\n")

print(f"MAE sem dummies: {MAE(result["Y_pred"], result["Y_test"])}")
print(f"MAE com dummies: {MAE(resultD["Y_pred"], resultD["Y_test"])}\n")

print(f"Menor techa de erro sem dummies: {np.round(min(result["miss"]),2)}")
print(f"Menor techa de erro com dummies: {np.round(min(resultD["miss"]),2)}\n")

print(f"Maior techa de erro maxima sem dummies: {np.round(max(result["miss"]),2)}")
print(f"Maior techa de erro maxima com dummies: {np.round(max(resultD["miss"]),2)}\n")