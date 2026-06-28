import os
import logging
import random
from datetime import datetime
import lightgbm as lgb
import pandas as pd
from app.services.risk_engine import reload_model

logger = logging.getLogger("MLFeedbackLoop")

class MLFeedbackService:
    MODEL_PATH = "app/ml/models/risk_v1.txt"
    BATCH_FILE = "app/ml/data/verified_batch.csv"
    BATCH_SIZE = 5

    @staticmethod
    def integrate_verified_incident(lat: float, lon: float, time_of_day_hour: int):
        try:
            logger.info(f"Logging verified incident for Lat {lat}, Lon {lon}")
            is_weekend = 1 if datetime.utcnow().weekday() >= 5 else 0
            
            # 🔥 FIX: Dynamic target score. 
            # verified incidents are bad, but a flat 9.0 destroys the model's nuance.
            base_score = 8.5 if (time_of_day_hour >= 22 or time_of_day_hour <= 4) else 7.0
            noise = random.uniform(-0.5, 0.5)
            target_score = round(base_score + noise, 2)
            
            new_data = pd.DataFrame([{
                'latitude': lat, 
                'longitude': lon, 
                'hour_of_day': time_of_day_hour,
                'is_weekend': is_weekend,
                'street_lit': 0, # Assume unlit if an incident occurred (pessimistic prior)
                'commercial_density': 0.5,
                'recent_incidents_count': 1,
                'target_risk_score': target_score
            }])
            
            # 1. Append to Batch File
            os.makedirs(os.path.dirname(MLFeedbackService.BATCH_FILE), exist_ok=True)
            new_data.to_csv(
                MLFeedbackService.BATCH_FILE, 
                mode='a', 
                header=not os.path.exists(MLFeedbackService.BATCH_FILE), 
                index=False
            )
            
            df = pd.read_csv(MLFeedbackService.BATCH_FILE)
            if len(df) < MLFeedbackService.BATCH_SIZE:
                logger.info(f"Batch size at {len(df)}/{MLFeedbackService.BATCH_SIZE}. Deferring retrain.")
                return True
                
            # 2. We hit the batch size, incrementally retrain safely!
            logger.info("Batch threshold met. Triggering incremental retrain.")
            X_train = df.drop(columns=['target_risk_score'])
            y_train = df['target_risk_score']
            train_data = lgb.Dataset(X_train, label=y_train)
            
            updated_model = lgb.train(
                params={
                    'objective': 'regression',
                    'learning_rate': 0.01, # 🔥 FIX: Very low learning rate to prevent catastrophic forgetting
                    'min_data_in_leaf': 1,
                    'min_data_in_bin': 1,
                    'feature_pre_filter': False
                },
                train_set=train_data,
                num_boost_round=2, # 🔥 FIX: Add only 2 trees to gently nudge the model, not 10
                init_model=MLFeedbackService.MODEL_PATH
            )
            
            # 3. Save model and clear batch
            updated_model.save_model(MLFeedbackService.MODEL_PATH)
            df.iloc[0:0].to_csv(MLFeedbackService.BATCH_FILE, index=False)
            logger.info("ML Risk Model successfully updated.")
            
            # 4. Tell the server to reload its brain!
            reload_model()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to integrate ML feedback: {e}")
            return False