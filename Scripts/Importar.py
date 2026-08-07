import os
import math
import pandas as pd
import numpy as np
from pathlib import Path
import xml.dom.minidom 
from datetime import datetime
import xml.etree.ElementTree as Et

def get_xml_root():
    try:
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        BASE_DIR = os.getcwd()
    return os.path.join(BASE_DIR, "..", "OhioT1DM")

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

def get_info(file_XML, dados: dict):
    domtree = xml.dom.minidom.parse(str(file_XML))

    patient = domtree.documentElement
    assert patient is not None

    id_patient = int(patient.getAttribute('id'))
        

    parar = 0 #serve para os lupes não imundar o painel de comando, sera remorido depis

    glucose_level = patient.getElementsByTagName('glucose_level')[0].getElementsByTagName('event')
    finger_stick = patient.getElementsByTagName('finger_stick')[0].getElementsByTagName('event')
    basal = patient.getElementsByTagName('basal')[0].getElementsByTagName('event')
    bolus = patient.getElementsByTagName('bolus')[0].getElementsByTagName('event')
    meal = patient.getElementsByTagName('meal')[0].getElementsByTagName('event')
    sleep = patient.getElementsByTagName('sleep')[0].getElementsByTagName('event')
    exercise = patient.getElementsByTagName('exercise')[0].getElementsByTagName('event')


    for event in finger_stick:
        ts =  binning(event.getAttribute('ts'))
        dados[id_patient][ts] = {
                                    "medidor": "paciente", 
                                 "glucose_level": int(event.getAttribute('value')),
                                 "basal": None,
                                 "bolus": None,
                                 "bolus_bwz_carb_input": None,
                                 "meal_type": None, 
                                 "meal_carbs": None,
                                 "sleep": None,
                                 "sleep_quality": None,
                                 "exercise_intensity": None,
                                 "glucose_level": None}

    for event in glucose_level:
        ts =  binning(event.getAttribute('ts'))
        try:
            dados[id_patient][ts]["medidor"] = "CGM"
            dados[id_patient][ts]["glucose_level"] = int(event.getAttribute('value'))           
        except:
            dados[id_patient][ts] = {"medidor": "CGM", 
                                     "glucose_level": int(event.getAttribute('value')),
                                     "basal": None,
                                     "bolus": None,
                                     "bolus_bwz_carb_input": None,
                                     "meal_type": None, 
                                     "meal_carbs": None,
                                     "sleep": None,
                                     "sleep_quality": None,
                                     "exercise_intensity": None,
                                     "glucose_level": None}

    for event in basal:
        ts =  binning(event.getAttribute('ts'))
        try:
            dados[id_patient][ts]["basal"] = float(event.getAttribute('value'))
        except:
            dados[id_patient][ts] = {"medidor": None, 
                                     "glucose_level": None,
                                     "basal": float(event.getAttribute('value')),
                                     "bolus": None,
                                     "bolus_bwz_carb_input": None,
                                     "meal_type": None, 
                                     "meal_carbs": None,
                                     "sleep": None,
                                     "sleep_quality": None,
                                     "exercise_intensity": None,
                                     "glucose_level": None}

    for event in bolus:
        ts =  binning(event.getAttribute('ts_begin'))
        try:
            dados[id_patient][ts]["bolus"] = event.getAttribute('dose')
            dados[id_patient][ts]["bolus_bwz_carb_input"] = event.getAttribute('bwz_carb_input')
        except:
            dados[id_patient][ts] = {"medidor": None, 
                                     "glucose_level": None,
                                     "basal": None,
                                     "bolus": event.getAttribute('dose'),
                                     "bolus_bwz_carb_input": event.getAttribute('bwz_carb_input'),
                                     "meal_type": None, 
                                     "meal_carbs": None,
                                     "sleep": None,
                                     "sleep_quality": None,
                                     "exercise_intensity": None,
                                     "glucose_level": None}

    for event in meal:
        ts =  binning(event.getAttribute('ts'))
        try:
            dados[id_patient][ts]["meal_type"] = event.getAttribute('type')
            dados[id_patient][ts]["meal_carbs"] = event.getAttribute('carbs')
        except:
            dados[id_patient][ts] = {"medidor": None, 
                                     "glucose_level": None,
                                     "basal": None,
                                     "bolus": None,
                                     "bolus_bwz_carb_input": None,
                                     "meal_type": event.getAttribute('type'), 
                                     "meal_carbs": event.getAttribute('carbs'),
                                     "sleep": None,
                                     "sleep_quality": None,
                                     "exercise_intensity": None,
                                     "glucose_level": None}

    for event in sleep:
        ts_begin =  binning(event.getAttribute('ts_begin'))
        ts_end =  binning(event.getAttribute('ts_end'))
        try:
            dados[id_patient][ts_begin]["sleep"] = 'comeso'
            dados[id_patient][ts_begin]["sleep_quality"] = event.getAttribute('quality')
        except:
            dados[id_patient][ts_begin] = {"medidor": None, 
                                             "glucose_level": None,
                                             "basal": None,
                                             "bolus": None,
                                             "bolus_bwz_carb_input": None,
                                             "meal_type": None,
                                             "meal_carbs": None,
                                             "sleep": 'comeso',
                                             "sleep_quality": event.getAttribute('quality'),
                                             "exercise_intensity": None,
                                             "glucose_level": None}
        try:
            dados[id_patient][ts_end]["sleep"] = 'fim'
            dados[id_patient][ts_end]["sleep_quality"] = event.getAttribute('quality')
        except:
            dados[id_patient][ts_end] = {"medidor": None, 
                                             "glucose_level": None,
                                             "basal": None,
                                             "bolus": None,
                                             "bolus_bwz_carb_input": None,
                                             "meal_type": None,
                                             "meal_carbs": None,
                                             "sleep": 'fim',
                                             "sleep_quality": event.getAttribute('quality'),
                                             "exercise_intensity": None,
                                             "glucose_level": None}

    for event in exercise:
        ts =  binning(event.getAttribute('ts'))
        try:
            dados[id_patient][ts]["exercise_intensity"] = event.getAttribute('intensity')
            dados[id_patient][ts]["exercise_duration"] = event.getAttribute('duration')
        except:
            dados[id_patient][ts] = {"medidor": None, 
                                     "glucose_level": None,
                                     "basal": None,
                                     "bolus": None,
                                     "bolus_bwz_carb_input": None,
                                     "meal_type": None,
                                     "meal_carbs": None,
                                     "sleep": None,
                                     "sleep_quality": None,
                                     "exercise_intensity": event.getAttribute('intensity'),
                                     "exercise_duration": event.getAttribute('duration')}

    
    return dados

def binning(ts): 
    data = datetime.strptime(ts, "%d-%m-%Y %H:%M:%S")
    mim = math.floor(data.minute/5)*5
    return data.replace(minute = mim, second = 0)
    
# lista_XML = get_XMLs(get_xml_root())

# dados = {}
# for file in lista_XML:
#     dados = get_info(file, dados)

# for pacientes in dados:
#     print(f"ID Paciente: {pacientes}")
#     for data in dados[pacientes]:
#         print(data)

#         for entrada in dados[pacientes][data]:
#             print(f"{entrada}: {dados[pacientes][data][entrada]}")

root = get_xml_root()

print(root)
print(type(root))



