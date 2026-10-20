"""Reusable interval wrapper; point and interval predictions share the fitted estimator."""
import numpy as np
class OffsetRegressor:
    def __init__(self, model, offset):
        self.model, self.offset = model, offset
    def predict(self, X):
        return np.clip(self.model.predict(X) + self.offset, 0, 125)
