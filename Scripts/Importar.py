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
    
    if id_patient not in dados.keys():
        dados[id_patient] = {}

    finger_stick = patient.getElementsByTagName('finger_stick')[0].getElementsByTagName('event')
    for event in finger_stick:
        ts =  binning(event.getAttribute('ts'))
        dados = new_entry(ts, dados, id_patient)
        dados[id_patient][ts]["metodo_medida"] = "finger_stick"
        dados[id_patient][ts]["glucose_level"] = int(event.getAttribute('value'))

    glucose_level = patient.getElementsByTagName('glucose_level')[0].getElementsByTagName('event')
    for event in glucose_level:
        ts =  binning(event.getAttribute('ts'))
        dados = new_entry(ts, dados, id_patient)
        dados[id_patient][ts]["metodo_medida"] = "CGM"
        dados[id_patient][ts]["glucose_level"] = int(event.getAttribute('value'))

    bolus = patient.getElementsByTagName('bolus')[0].getElementsByTagName('event')
    for event in bolus:
        ts_begin =  binning(event.getAttribute('ts_begin'))
        ts_end =  binning(event.getAttribute('ts_end'))
        ts_diferenca = (ts_end-ts_begin).total_seconds()

        dados = new_entry(ts_begin, dados, id_patient)

        dados[id_patient][ts_begin]["bolus_type"] = event.getAttribute('type')

        if ts_diferenca == 0:
            dados[id_patient][ts_begin]["bolus_dose"] = float(event.getAttribute('dose'))
        else:
            ts_between = int(ts_diferenca / 60 / 5)
            dose = float(event.getAttribute('dose'))/ts_between

            for i in range(0, ts_between+1):
                ts = ts_begin + timedelta(minutes= 5*i)
                dados = new_entry(ts, dados, id_patient)
                dados[id_patient][ts]["bolus_dose"] = dose

    meal = patient.getElementsByTagName('meal')[0].getElementsByTagName('event')
    for event in meal:
        ts =  binning(event.getAttribute('ts'))
        dados = new_entry(ts, dados, id_patient)
        dados[id_patient][ts]["meal_type"] = event.getAttribute('type')
        dados[id_patient][ts]["meal_carbs"] = event.getAttribute('carbs')

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

    sleep = patient.getElementsByTagName('sleep')[0].getElementsByTagName('event')
    for event in sleep:
        ts_begin =  binning(event.getAttribute('ts_begin'))
        ts_end =  binning(event.getAttribute('ts_end'))

        for entry in dados[id_patient]:
            if entry >= ts_begin and entry <= ts_end:
                dados[id_patient][entry]["sleeping"] = True
                dados[id_patient][entry]["sleep_quality"] = event.getAttribute('quality')

    exercise = patient.getElementsByTagName('exercise')[0].getElementsByTagName('event')
    for event in exercise:
        ts_begin =  binning(event.getAttribute('ts'))
        ts_end = ts_begin + timedelta(minutes= int(event.getAttribute('duration')))

        for entry in dados[id_patient]:
            if entry >= ts and entry <= ts_end:
                dados[id_patient][entry]["doing_exercise"] = True
                dados[id_patient][entry]["exercise_intensity"] = event.getAttribute('intensity')

    for event in dados[id_patient]:
        if dados[id_patient][event]["glucose_level"] is not None:
            ts_target = event - timedelta(hours= 1)
            if ts_target in dados[id_patient].keys():
                dados[id_patient][ts_target]["target"] = dados[id_patient][event]["glucose_level"]
    
    return dados

# cria uma nova entrada caso ela não existir
def new_entry(ts, dados: dict, id_patient):
    if ts not in dados[id_patient].keys():
        dados[id_patient][ts] = {"id_patient": id_patient,
                                 "ts": ts,
                                 "metodo_medida": None, 
                                 "glucose_level": None,
                                 "basal": None,
                                 "bolus_type": None,
                                 "bolus_dose": None,
                                 "meal_type": None, 
                                 "meal_carbs": None,
                                 "sleeping": False,
                                 "sleep_quality": None,
                                 "exercise_intensity": None,
                                 "doing_exercise": False,
                                 "target": None}
    return dados

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
# df_paciente = pd.DataFrame(dados_individual)
print(df_paciente)




