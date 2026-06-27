import lightgbm as lgb
import pandas as pd
import logging
from datetime import datetime

logger = logging.getLogger("MLFeedbackLoop")

class MLFeedbackService:
    MODEL_PATH = "app/ml/models/risk_v1.txt"

    @staticmethod
    def integrate_verified_incident(lat: float, lon: float, time_of_day_hour: int):
        """
        Takes a verified SOS location and forces the model to increase the risk 
        score for that specific spatial feature profile.
        """
        try:
            logger.info(f"Triggering incremental LightGBM update for Lat {lat}, Lon {lon}")
            
            # 1. Format the new verified danger point
            # In a real scenario, you'd pull the OSM lighting prior for this exact lat/lon here.
            # For the demo, we assume a baseline prior and force a high risk_score target.
            new_data = pd.DataFrame([{
                'lat': lat, 
                'lon': lon, 
                'time_of_day': time_of_day_hour,
                'lighting_prior': 0.5 # Mocked prior
            }])
            
            # The target label is 1.0 (Maximum Risk) because it is a verified SOS incident
            labels = pd.Series([1.0])
            
            train_data = lgb.Dataset(new_data, label=labels)
            
            # 2. Retrain incrementally using the existing model as the baseline
            updated_model = lgb.train(
                params={'objective': 'regression', 'learning_rate': 0.1},
                train_set=train_data,
                num_boost_round=5, 
                init_model=MLFeedbackService.MODEL_PATH
            )
            
            # 3. Overwrite the model with the newly learned weights
            updated_model.save_model(MLFeedbackService.MODEL_PATH)
            logger.info("ML Risk Model successfully updated and saved.")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to run incremental ML update: {str(e)}")
            return False