import lightgbm as lgb
import pandas as pd
import logging
from datetime import datetime

logger = logging.getLogger("MLFeedbackLoop")

class MLFeedbackService:
    # Ensure this matches exactly where your script saves the model
    MODEL_PATH = "app/ml/models/risk_v1.txt"

    @staticmethod
    def integrate_verified_incident(lat: float, lon: float, time_of_day_hour: int):
        """
        Takes a verified SOS location and feeds it into the 7-feature LightGBM model.
        """
        try:
            logger.info(f"Triggering incremental LightGBM update for Lat {lat}, Lon {lon}")
            
            # 1. Format the new verified danger point matching the NEW 7-feature schema
            is_weekend = 1 if datetime.utcnow().weekday() >= 5 else 0
            
            # In production, we'd query OSM/PostGIS for these. For now, we assume
            # a verified SOS implies low lighting and high recent incidents.
            new_data = pd.DataFrame([{
                'latitude': lat, 
                'longitude': lon, 
                'hour_of_day': time_of_day_hour,
                'is_weekend': is_weekend,
                'street_lit': 0,                # Assuming unlit due to incident
                'commercial_density': 0.3,      # Default mid-low density
                'recent_incidents_count': 1     # It's a verified incident!
            }])
            
            # Target risk score is maximum (10.0) based on your generation logic
            labels = pd.Series([10.0])
            
            train_data = lgb.Dataset(new_data, label=labels)
            
            # 2. Retrain incrementally
            updated_model = lgb.train(
                params={'objective': 'regression', 'learning_rate': 0.1},
                train_set=train_data,
                num_boost_round=5, 
                init_model=MLFeedbackService.MODEL_PATH
            )
            
            # 3. Overwrite the model
            updated_model.save_model(MLFeedbackService.MODEL_PATH)
            logger.info("ML Risk Model successfully updated and saved.")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to run incremental ML update: {str(e)}")
            return False