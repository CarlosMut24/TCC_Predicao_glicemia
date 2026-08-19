import os
import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
from sklearn.datasets import make_regression
from sklearn.linear_model import LinearRegression


def get_csv_root():
    try:
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        BASE_DIR = os.getcwd()
    return os.path.join(BASE_DIR, "..", "processado")

df_paciente = pd.read_csv(os.path.join(get_csv_root(), "paciente.cvs"))
df_final = pd.read_csv(os.path.join(get_csv_root(), "final.cvs"))
