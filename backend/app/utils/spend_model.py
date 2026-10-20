"""Positive spend forecast features, including recent arithmetic spending levels."""
import numpy as np
from sklearn.base import BaseEstimator,RegressorMixin
class RecentSpendRegressor(RegressorMixin,BaseEstimator):
    def __init__(self,feature='lag1'):self.feature=feature
    def fit(self,X,y):return self
    def predict(self,X):return X[self.feature].to_numpy()
