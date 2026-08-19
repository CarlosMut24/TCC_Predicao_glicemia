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

def get_csv_root():
    try:
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        BASE_DIR = os.getcwd()
    return os.path.join(BASE_DIR, "..", "processado")

# paga o caminho para os arquivos XML
def get_XMLs(root):
    p = Path(root)
    lista_XML = []

    for x in p.iterdir():
        if x.is_dir() :
            lista_XML.extend(get_XMLs(x))
        # elif "testing" in x.name: 
        #     continue
        # elif "training" in x.name: 
        #     continue
        elif x.suffix == ".xml": 
            lista_XML.append(x)

    return lista_XML

# estrai as informaçõens dos XMLs
def get_info(file_XML, dados: dict):
    domtree = xml.dom.minidom.parse(str(file_XML))

    patient = domtree.documentElement
    assert patient is not None

    id_patient = int(patient.getAttribute('id'))
    
    if id_patient not in  dados.keys():
        dados[id_patient] = {}

    finger_stick = patient.getElementsByTagName('finger_stick')[0].getElementsByTagName('event')
    for event in finger_stick:
        ts =  binning(event.getAttribute('ts'))
        dados[id_patient][ts] = new_entry(ts, dados.keys(), id_patient)
        dados[id_patient][ts]["metodo_medida"] = "finger_stick"
        dados[id_patient][ts]["glucose_level"] = int(event.getAttribute('value'))

    glucose_level = patient.getElementsByTagName('glucose_level')[0].getElementsByTagName('event')
    for event in glucose_level:
        ts =  binning(event.getAttribute('ts'))
        dados[id_patient][ts] = new_entry(ts, dados.keys(), id_patient)
        dados[id_patient][ts]["metodo_medida"] = "CGM"
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
            dose = float(event.getAttribute('dose'))/ts_between

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

    sleep = patient.getElementsByTagName('basis_sleep')[0].getElementsByTagName('event')
    for event in sleep:
        ts_begin =  binning(event.getAttribute('tbegin'))
        ts_end =  binning(event.getAttribute('tend'))

        for entry in dados[id_patient]:
            if ts_begin <= entry and entry <= ts_end: 
                # print(id_patient)
                # print(entry)
                # print(dados[id_patient][entry])
                dados[id_patient][entry]["sleeping"] = True
                dados[id_patient][entry]["sleep_quality"] = int(event.getAttribute('quality'))

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
            ts_target = event - timedelta(hours= 1)
            if ts_target in dados[id_patient].keys():
                dados[id_patient][ts_target]["target"] = dados[id_patient][event]["glucose_level"]
    
    return dados

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
                    "sleeping": False,
                    "sleep_quality": None,
                    "exercise_intensity": None,
                    "doing_exercise": False,
                    "target": None}
    return Nentry

# aredonda o horario para o 5 muinutos enterior 
def binning(ts): 
    data = datetime.strptime(ts, "%d-%m-%Y %H:%M:%S")
    i = 5
    mim = data.minute//i*i
    return data.replace(minute = mim, second = 0)
    
lista_XML = get_XMLs(get_xml_root())

para = 0
dados_individual = {}
dados_geral = []
for file in lista_XML:
    # if para > 0:
    #     break 
    dados_individual = get_info(file, dados_individual)
    # para +=1


for pacient in dados_individual:
    for ts in dados_individual[pacient]:
        dados_geral.append(dados_individual[pacient][ts])

df_paciente = pd.DataFrame(dados_geral)
df_paciente_individual = pd.DataFrame(dados_individual)

df_final = df_paciente.sort_values(by=["id_patient", "ts"]).reset_index(drop=True)

for idx, event in df_final.iterrows():
    if pd.isna(event["glucose_level"]):
        back = 5
        past_glucose = None
        future_glucose = None
        past_weight = None
        future_weight = None

        while ((past_glucose is None) or (future_glucose is None)) and (back <= 150):
            ts_past_glucose = event["ts"] - timedelta(minutes= back)
            ts_future_glucose = event["ts"] + timedelta(minutes= back)

            if (past_glucose is None):
                result_past = df_final.loc[
                    (df_final["ts"] == ts_past_glucose) &
                    (df_final["id_patient"] == event["id_patient"]) &
                    (df_final["glucose_level"].notna()),
                    ["glucose_level", "metodo_medida"]
                ]
                
                if not result_past.empty:
                    past_glucose = result_past.iloc[0]
                    past_weight = 1 / (back / 5)

            if (future_glucose is None):
                result_future = df_final.loc[
                    (df_final["ts"] == ts_future_glucose) &
                    (df_final["id_patient"] == event["id_patient"]) &
                    (df_final["glucose_level"].notna()),
                    ["glucose_level", "metodo_medida"]
                ]
                
                if not result_future.empty:
                    future_glucose = result_future.iloc[0]
                    future_weight = 1 / (back / 5)

            if past_glucose is None or future_glucose is None:
                back += 5
        
        if past_glucose is not None and future_glucose is not None:
            assert past_weight is not None
            assert future_weight is not None

            glucose_level = (
                past_glucose["glucose_level"] * past_weight +
                future_glucose["glucose_level"] * future_weight
            ) / (past_weight + future_weight)

            df_final.loc[idx, "glucose_level"] = glucose_level
            df_final.loc[idx, "metodo_medida"] = "interpolado"

        elif (past_glucose is not None):
            df_final.loc[idx, "glucose_level"] = past_glucose["glucose_level"]
            df_final.loc[idx, "metodo_medida"] = past_glucose["metodo_medida"]
            
        elif (future_glucose is not None):
            df_final.loc[idx, "glucose_level"] = future_glucose["glucose_level"]
            df_final.loc[idx, "metodo_medida"] = future_glucose["metodo_medida"]

processado_path = get_csv_root()
df_paciente.to_csv(os.path.join(processado_path, "paciente.cvs"), index=False, encoding='utf-8')
df_final.to_csv(os.path.join(processado_path, "final.cvs"), index=False, encoding='utf-8')
