import logging
from datetime import datetime
import lightgbm as lgb
import pandas as pd

logger = logging.getLogger("MLFeedbackLoop")

class MLFeedbackService:
    MODEL_PATH = "app/ml/models/risk_v1.txt"

    @staticmethod
    def integrate_verified_incident(lat: float, lon: float, time_of_day_hour: int):
        try:
            logger.info(f"Triggering incremental LightGBM update for Lat {lat}, Lon {lon}")
            
            is_weekend = 1 if datetime.utcnow().weekday() >= 5 else 0
            
            new_data = pd.DataFrame([{
                'latitude': lat, 
                'longitude': lon, 
                'hour_of_day': time_of_day_hour,
                'is_weekend': is_weekend,
                'street_lit': 0,
                'commercial_density': 0.3,
                'recent_incidents_count': 1
            }])
            
            labels = pd.Series([10.0])
            train_data = lgb.Dataset(new_data, label=labels)
            
            updated_model = lgb.train(
                params={
                    'objective': 'regression',
                    'learning_rate': 0.1,
                    'min_data_in_leaf': 1,
                    'min_data_in_bin': 1,
                    'feature_pre_filter': False
                },
                train_set=train_data,
                num_boost_round=5, 
                init_model=MLFeedbackService.MODEL_PATH
            )
            
            updated_model.save_model(MLFeedbackService.MODEL_PATH)
            logger.info("ML Risk Model successfully updated and saved.")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to run incremental ML update: {str(e)}")
            return False