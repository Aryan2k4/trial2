"""Supervised synthetic-pattern scorer with the existing anomaly scoring interface."""
import numpy as np
class PatternScorer:
    def __init__(self,classifier,threshold=.5):self.classifier,self.threshold=classifier,threshold
    def score_samples(self,X):return -self.classifier.predict_proba(X)[:,1]
    def predict(self,X):return np.where(-self.score_samples(X)>=self.threshold,-1,1)
