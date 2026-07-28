import os
from pathlib import Path
import xml.dom.minidom 
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

    patient = domtree.documentElement
    assert patient is not None

    print(f"--- Patient {patient.getAttribute('id')} ---")

    parar = 0 #serve para os lupes não imundar o painel de comando, sera remorido depis

    glucose_level = patient.getElementsByTagName('glucose_level')[0].getElementsByTagName('event')
    print("-- Nivel de glicose --")

    for event in glucose_level:
        print (f"tempo: {event.getAttribute('ts')} glicose: {event.getAttribute('value')}")

        parar = parar + 1
        if parar >= 4 :
            parar = 0
            break

lista_XML = get_XMLs(get_xml_root())

for file in lista_XML:
    get_info(file)

