import os
import math
from pathlib import Path
import xml.dom.minidom 
from datetime import datetime
import xml.etree.ElementTree as Et

def get_xml_root():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))  
    return os.path.join(BASE_DIR, "..", "OhioT1DM")

def get_XMLs(root):
    p = Path(root)
    lista_XML = []

    for x in p.iterdir():
        if x.is_dir() :
            lista_XML.extend(get_XMLs(x))
        elif x.suffix == ".xml": 
            lista_XML.append(x)

    return lista_XML

def get_info(file_XML):
    domtree = xml.dom.minidom.parse(str(file_XML))
    dados = {}
    dados_paciente = {}

    patient = domtree.documentElement
    assert patient is not None

    # parar = 0 #serve para os lupes não imundar o painel de comando, sera remorido depis

    glucose_level = patient.getElementsByTagName('glucose_level')[0].getElementsByTagName('event')
    basal = patient.getElementsByTagName('basal')[0].getElementsByTagName('event')
    temp_basal = patient.getElementsByTagName('temp_basal')[0].getElementsByTagName('event')
    bolus = patient.getElementsByTagName('bolus')[0].getElementsByTagName('event')
    meal = patient.getElementsByTagName('meal')[0].getElementsByTagName('event')
    sleep = patient.getElementsByTagName('sleep')[0].getElementsByTagName('event')
    exercise = patient.getElementsByTagName('exercise')[0].getElementsByTagName('event')

    print("-- Nivel de glicose --")

    for event in glucose_level:
        ts = datetime.strptime(event.getAttribute('ts'), "%d-%m-%Y %H:%M:%S")
        print (f"tempo: {ts} glicose: {event.getAttribute('value')}")

        parar = parar + 1
        if parar >= 4 :
            parar = 0
            break

    return dados

def binning(ts): 
    data = datetime.strptime(ts, "%d-%m-%Y %H:%M:%S")


data = datetime.strptime("18-01-2022 00:05:00", "%d-%m-%Y %H:%M:%S")
mim = math.floor(data.minute/5)*5
print(mim)
print(data.replace(minute = mim))

# lista_XML = get_XMLs(get_xml_root())

# for file in lista_XML:
#     dados = get_info(file)

