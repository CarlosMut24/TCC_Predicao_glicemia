import os
import math
import pandas as pd
import numpy as np
from pathlib import Path
import xml.dom.minidom 
from datetime import datetime, timedelta
import xml.etree.ElementTree as Et

# paga o caminho para a raiz database
def get_xml_root():
    try:
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        BASE_DIR = os.getcwd()
    return os.path.join(BASE_DIR, "..", "OhioT1DM")

# paga o caminho para os arquivos XML
def get_XMLs(root, seletor: str):
    p = Path(root)
    lista_XML = []

    for x in p.iterdir():
        if x.is_dir() :
            lista_XML.extend(get_XMLs(x, seletor))
        elif "testing" in x.name and seletor == "training": 
            continue
        elif "training" in x.name and seletor == "testing": 
            continue
        elif x.suffix == ".xml": 
            lista_XML.append(x)

    return lista_XML

def get_csv_root():
    try:
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        BASE_DIR = os.getcwd()
    return os.path.join(BASE_DIR, "..", "processado")

# estrai as informaçõens dos XMLs
def get_info(file_XML, dados: dict):
    domtree = xml.dom.minidom.parse(str(file_XML))

    patient = domtree.documentElement
    assert patient is not None

    id_patient = int(patient.getAttribute('id'))
    
    if id_patient not in  dados.keys():
        dados[id_patient] = {}

    glucose_level = patient.getElementsByTagName('glucose_level')[0].getElementsByTagName('event')
    for event in glucose_level:
        ts =  binning(event.getAttribute('ts'))
        dados[id_patient][ts] = new_entry(ts, dados.keys(), id_patient)
        dados[id_patient][ts]["metodo_medida"] = "CGM"
        dados[id_patient][ts]["glucose_level"] = int(event.getAttribute('value'))

    finger_stick = patient.getElementsByTagName('finger_stick')[0].getElementsByTagName('event')
    for event in finger_stick:
        ts =  binning(event.getAttribute('ts'))
        dados[id_patient][ts] = new_entry(ts, dados.keys(), id_patient)
        dados[id_patient][ts]["metodo_medida"] = "finger_stick"
        dados[id_patient][ts]["glucose_level"] = int(event.getAttribute('value'))

    bolus = patient.getElementsByTagName('bolus')[0].getElementsByTagName('event')
    for event in bolus:
        ts_begin =  binning(event.getAttribute('ts_begin'))
        ts_end =  binning(event.getAttribute('ts_end'))
        ts_diferenca = (ts_end-ts_begin).total_seconds()

        dados[id_patient][ts_begin] = new_entry(ts_begin, dados.keys(), id_patient)

        if ts_diferenca == 0:
            dados[id_patient][ts_begin]["bolus_type"] = event.getAttribute('type')
            dados[id_patient][ts_begin]["bolus_dose"] += float(event.getAttribute('dose'))
        else:
            ts_between = int(ts_diferenca / 60 / 5)
            dose = float(event.getAttribute('dose'))

            for i in range(0, ts_between+1):
                ts = ts_begin + timedelta(minutes= 5*i)
                dados[id_patient][ts] = new_entry(ts, dados.keys(), id_patient)
                dados[id_patient][ts]["bolus_type"] = event.getAttribute('type')
                dados[id_patient][ts]["bolus_dose"] += dose

    meal = patient.getElementsByTagName('meal')[0].getElementsByTagName('event')
    for event in meal:
        ts =  binning(event.getAttribute('ts'))
        dados[id_patient][ts] = new_entry(ts, dados.keys(), id_patient)
        dados[id_patient][ts]["meal_type"] = event.getAttribute('type')
        dados[id_patient][ts]["meal_carbs"] = int(event.getAttribute('carbs'))
        dados[id_patient][ts]["meal_time"] = 0

    basal = patient.getElementsByTagName('basal')[0].getElementsByTagName('event')
    for event in basal:
        ts =  binning(event.getAttribute('ts'))

        for entry in dados[id_patient]:
            if entry >= ts:
                dados[id_patient][entry]["basal"] = float(event.getAttribute('value'))

    temp_basal = patient.getElementsByTagName('temp_basal')[0].getElementsByTagName('event')
    for event in temp_basal:
        ts_begin =  binning(event.getAttribute('ts_begin'))
        ts_end =  binning(event.getAttribute('ts_end'))

        for entry in dados[id_patient]:
            if entry >= ts_begin and entry <= ts_end:
                dados[id_patient][entry]["basal"] = float(event.getAttribute('value'))


    exercise = patient.getElementsByTagName('exercise')[0].getElementsByTagName('event')
    for event in exercise:
        ts_begin =  binning(event.getAttribute('ts'))
        ts_end = ts_begin + timedelta(minutes= int(event.getAttribute('duration')))

        for entry in dados[id_patient]:
            if entry >= ts_begin and entry <= ts_end:
                dados[id_patient][entry]["doing_exercise"] = True
                dados[id_patient][entry]["exercise_intensity"] = int(event.getAttribute('intensity'))

    for event in dados[id_patient]:
        if dados[id_patient][event]["glucose_level"] is not None:
            ts_target = event - timedelta(minutes= 30)
            if ts_target in dados[id_patient].keys():
                dados[id_patient][ts_target]["target"] = dados[id_patient][event]["glucose_level"]
    
    return dados

# aredonda o horario para o 5 muinutos enterior 
def binning(ts): 
    data = datetime.strptime(ts, "%d-%m-%Y %H:%M:%S")
    i = 5
    mim = data.minute//i*i
    return data.replace(minute = mim, second = 0)

# cria uma nova entrada caso ela não existir
def new_entry(ts, keys, id_patient):
    if ts not in keys:
        Nentry = {"id_patient": id_patient,
                    "ts": ts,
                    "metodo_medida": None, 
                    "glucose_level": None,
                    "basal": None,
                    "bolus_type": None,
                    "bolus_dose": 0,
                    "meal_type": None, 
                    "meal_carbs": None,
                    "meal_time": None,
                    "sleeping": False,
                    "sleep_quality": None,
                    "exercise_intensity": None,
                    "doing_exercise": False,
                    "target": None}
    return Nentry

# adiciona informasoens de medidas de glucose anteriores para ser posivel de ver a tentencia
def leg_glucose(df):
    df = df.sort_values(["id_patient", "ts"]).reset_index(drop=True)

    for k in [1, 2, 3, 4, 5, 6]:   # 5, 10, 15, 20, 25, 30 min atrás
        df[f"glucose_lag_{k*5}"] = df.groupby("id_patient")["glucose_level"].shift(k)

    # glucose_delta_X é a diferença entre a glucose atual e da glucose a X minutos
    df["glucose_delta_5"]  = df["glucose_level"] - df["glucose_lag_5"]
    df["glucose_delta_15"] = df["glucose_level"] - df["glucose_lag_15"]
    df["glucose_delta_30"] = df["glucose_level"] - df["glucose_lag_30"]

    # glucose_ma_X é a media entre os valores da a glucose atual até da glucose X minutos atrais
    df["glucose_ma_15"]  = df.groupby("id_patient")["glucose_level"].transform(lambda s: s.rolling(3).mean())
    df["glucose_ma_30"]  = df.groupby("id_patient")["glucose_level"].transform(lambda s: s.rolling(6).mean())

    # glucose_std_X é o desvio padrão entre os valores da a glucose atual até da glucose X minutos atrais
    df["glucose_std_30"] = df.groupby("id_patient")["glucose_level"].transform(lambda s: s.rolling(6).std())

    df = df.dropna(subset=["target"])   
    return df

# adiciona informasoens de refeições anteriores para ser posivel de ver a tentencia - não foi usado no trenamento ainda
def leg_meal(df):
    for idx, event in df.iterrows():
        shift = 1
        while pd.notna(event["meal_carbs"]) and shift < 6:
            ts_past_meal = event["ts"] - timedelta(minutes= shift*5)
            result_past = df.loc[
                (df["ts"] == ts_past_meal) &
                (df["id_patient"] == event["id_patient"]) &
                (df["glucose_level"].notna()),
                ["meal_type", "meal_carbs", "meal_time"]
            ]
            if not result_past.empty and result_past["meal_time"] == 0:
                df.loc[idx, "meal_carbs"] = result_past["meal_carbs"]
                df.loc[idx, "meal_type"] = result_past["meal_type"]
                df.loc[idx, "meal_time"] = shift * 5
            else:
                shift += 1       

    return df

lista_XML_training = get_XMLs(get_xml_root(), "training")
lista_XML_testing = get_XMLs(get_xml_root(), "testing")

dados_treinamento = []
for file in lista_XML_training:
    dados = {}
    dados = get_info(file, dados)

    for pacient in dados:
        for ts in dados[pacient]:
            dados_treinamento.append(dados[pacient][ts])

dados_testes = []
for file in lista_XML_testing:

    dados = {}
    dados = get_info(file, dados)

    for pacient in dados:
        for ts in dados[pacient]:
            dados_testes.append(dados[pacient][ts])

df_treinamento = pd.DataFrame(dados_treinamento)
df_testes = pd.DataFrame(dados_testes)

df_treinamento = leg_glucose(df_treinamento)
df_testes = leg_glucose(df_testes)

df_treinamento_final = df_treinamento.sort_values(by=["id_patient", "ts"]).reset_index(drop=True)
df_testes_final = df_testes.sort_values(by=["id_patient", "ts"]).reset_index(drop=True)

processado_path = get_csv_root()
df_treinamento_final.to_csv(os.path.join(processado_path, "treinamento_final.csv"), index=False, encoding='utf-8')
df_testes_final.to_csv(os.path.join(processado_path, "testes_final.csv"), index=False, encoding='utf-8')