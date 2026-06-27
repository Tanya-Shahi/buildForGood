import lightgbm as lgb
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split

df = pd.read_csv("synthetic_risk_data.csv") 

X = df.drop(columns=['target_risk_score'])
y = df['target_risk_score']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 2. Configure LightGBM (Regression task since we want a 0-10 score)
params = {
    'objective': 'regression',
    'metric': 'rmse',
    'boosting_type': 'gbdt',
    'learning_rate': 0.05,
    'num_leaves': 31,
    'max_depth': -1,
    'feature_fraction': 0.8
}

train_data = lgb.Dataset(X_train, label=y_train)
valid_data = lgb.Dataset(X_test, label=y_test, reference=train_data)

# 3. Train the model
model = lgb.train(
    params,
    train_data,
    num_boost_round=500,
    valid_sets=[train_data, valid_data],
    callbacks=[lgb.early_stopping(stopping_rounds=50)]
)

# 4. Save the compiled model to your services folder
model_dir = "../app/ml/models"
os.makedirs(model_dir, exist_ok=True)
model_path = f"{model_dir}/risk_v1.txt"

model.save_model(model_path)
print(f"Model trained and saved natively for incremental learning to {model_path}.")