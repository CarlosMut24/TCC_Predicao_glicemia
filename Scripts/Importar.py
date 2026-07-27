import os
import xml.dom.minidom 
import xml.etree.ElementTree as Et

def get_xml_path():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))  
    return os.path.join(BASE_DIR, "..", "OhioT1DM", "2018", "test", "559-ws-testing.xml")

domtree = xml.dom.minidom.parse(get_xml_path())

patient = domtree.documentElement
assert patient is not None
print(f"--- Patient {patient.getAttribute('id')} ---")

glucose_level = patient.getElementsByTagName('glucose_level')[0].getElementsByTagName('event')

parar = 0

print("-- Nivel de glicose --")
for event in glucose_level:

    print (f"tempo: {event.getAttribute('ts')} glicose: {event.getAttribute('value')}")

    parar = parar + 1
    if parar >= 4 :
        parar = 0
        break

