import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin

class FeaturesTemporais(BaseEstimator, TransformerMixin):
    # Adiciona features cíclicas e flags temporais a partir de uma coluna timestamp.
    
    def __init__(self, coluna_timestamp="timestamp"):
        self.coluna_timestamp = coluna_timestamp
    
    def fit(self, X, y=None):
        return self
    
    def transform(self, X):
        X = X.copy()
        dt = pd.to_datetime(X[self.coluna_timestamp])
        
        h = dt.dt.hour + dt.dt.minute / 60
        X["hora_sin"] = np.sin(2 * np.pi * h / 24)
        X["hora_cos"] = np.cos(2 * np.pi * h / 24)
        
        d = dt.dt.dayofweek
        X["dia_sin"] = np.sin(2 * np.pi * d / 7)
        X["dia_cos"] = np.cos(2 * np.pi * d / 7)
        
        X["fim_de_semana"] = (d >= 5).astype(int)
        X["madrugada"]     = dt.dt.hour.isin([0,1,2,3,4,5]).astype(int)
        X["pos_cafe"]      = dt.dt.hour.between(7, 10).astype(int)
        X["pos_almoco"]    = dt.dt.hour.between(12, 15).astype(int)
        X["pos_jantar"]    = dt.dt.hour.between(19, 22).astype(int)
        
        # remove a coluna timestamp original (RF não usa)
        X = X.drop(columns=[self.coluna_timestamp])
        return X