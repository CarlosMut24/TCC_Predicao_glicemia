import os
import xml.etree.ElementTree as Et

class Read_xml():
    def __init__(self, directoty) -> None:
        self.directoty = directoty

    def all_files(self):
        return [ os.path.join(self.directoty, arq) for arq in os.listdir(self.directoty)
        if arq.lower().endswith(".xml")]

    def nfe_data(self, xml):
        root = Et.parse(xml).getroot()
        ns = {"ns": "patient"}

    def check_none(self, var):
        pass