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

    basal = patient.getElementsByTagName('basal')[0].getElementsByTagName('event')
    for event in basal:
        ts =  binning(event.getAttribute('ts'))
        dados = new_entry(ts, dados, id_patient)
        dados[id_patient][ts]["basal"] = float(event.getAttribute('value'))

    bolus = patient.getElementsByTagName('bolus')[0].getElementsByTagName('event')
    for event in bolus:
        ts =  binning(event.getAttribute('ts_begin'))
        dados = new_entry(ts, dados, id_patient)
        dados[id_patient][ts]["bolus"] = event.getAttribute('dose')
        dados[id_patient][ts]["bolus_bwz_carb_input"] = event.getAttribute('bwz_carb_input')
        
    meal = patient.getElementsByTagName('meal')[0].getElementsByTagName('event')
    for event in meal:
        ts =  binning(event.getAttribute('ts'))
        dados = new_entry(ts, dados, id_patient)
        dados[id_patient][ts]["meal_type"] = event.getAttribute('type')
        dados[id_patient][ts]["meal_carbs"] = event.getAttribute('carbs')

    sleep = patient.getElementsByTagName('sleep')[0].getElementsByTagName('event')
    for event in sleep:
        ts_begin =  binning(event.getAttribute('ts_begin'))
        ts_end =  binning(event.getAttribute('ts_end'))
        dados = new_entry(ts_begin, dados, id_patient)
        dados = new_entry(ts_end, dados, id_patient)

        dados[id_patient][ts_begin]["sleep"] = 'comeso'
        dados[id_patient][ts_begin]["sleep_quality"] = event.getAttribute('quality')

        dados[id_patient][ts_end]["sleep"] = 'fim'
        dados[id_patient][ts_end]["sleep_quality"] = event.getAttribute('quality')

    exercise = patient.getElementsByTagName('exercise')[0].getElementsByTagName('event')
    for event in exercise:
        ts =  binning(event.getAttribute('ts'))
        dados = new_entry(ts, dados, id_patient)
        dados[id_patient][ts]["exercise_intensity"] = event.getAttribute('intensity')
        dados[id_patient][ts]["exercise_duration"] = event.getAttribute('duration')

    
    return dados

# cria uma nova entrada caso ela não existir
def new_entry(ts, dados: dict, id_patient):
    if ts not in dados[id_patient].keys():
        dados[id_patient][ts] = {"metodo_medida": None, 
                                 "glucose_level": None,
                                 "basal": None,
                                 "bolus": None,
                                 "bolus_bwz_carb_input": None,
                                 "meal_type": None, 
                                 "meal_carbs": None,
                                 "sleeping": False,
                                 "sleep_quality": None,
                                 "exercise_intensity": None,
                                 "doing_exercise": False}
    return dados

# aredonda o horario para o 5 muinutos enterior 
def binning(ts): 
    data = datetime.strptime(ts, "%d-%m-%Y %H:%M:%S")
    i = 5
    mim = data.minute//i*i
    return data.replace(minute = mim, second = 0)
    
    
lista_XML = get_XMLs(get_xml_root())

dados = {}
for file in lista_XML:
    dados = get_info(file, dados)

for pacientes in dados:
    print(f"ID Paciente: {pacientes}")
    for data in dados[pacientes]:
        print(data)

        for entrada in dados[pacientes][data]:
            print(f"{entrada}: {dados[pacientes][data][entrada]}")




