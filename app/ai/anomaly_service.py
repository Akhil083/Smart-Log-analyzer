from __future__ import annotations

import numpy as np
from sklearn.ensemble import IsolationForest


class AnomalyService:
    """Detect anomaly in the time series log data"""

    def __init__(self):
        self.model = IsolationForest(
            contamination=0.1,
            random_state=42,
        )

    def detect(self, values: list[int]) ->list:
        """
        Detect anomaly points
        Returns:
        listprediction(-1 = anomaly , 1 = normal)
        """

        if not values:
            return []
        
        if len(values) < 5:
            return [1] * len(values)
        
        data = np.array(values).reshape(-1, 1)
        self.model.fit(data)
        
        return self.model.predict(data)
    