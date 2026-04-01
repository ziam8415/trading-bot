import pandas as pd
import numpy as np
import os
import json
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import accuracy_score
from xgboost import XGBClassifier

# ==============================
# CONFIG
# ==============================
SIGNAL_MAP = {-1: 0, 0: 1, 1: 2} 

XGB_PARAMS = dict(
    n_estimators=1000,
    max_depth=3,
    learning_rate=0.01,
    subsample=0.6,
    colsample_bytree=0.6,
    gamma=5.0,
    reg_alpha=10.0,
    reg_lambda=20.0,
    objective="multi:softprob", # This outputs [Prob_Sell, Prob_Wait, Prob_Buy]
    num_class=3,
    random_state=42,
    n_jobs=-1,
    early_stopping_rounds=25 
)

def main():
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    csv_path = os.path.join(BASE_DIR, "data", "processed", "features.csv")
    cols_path = os.path.join(BASE_DIR, "data", "processed", "feature_columns.json")
    save_dir = os.path.join(BASE_DIR, "models", "saved_models")
    os.makedirs(save_dir, exist_ok=True)

    # 1. Load and Cleaning
    df = pd.read_csv(csv_path)
    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    df.dropna(inplace=True)

    with open(cols_path, 'r') as f:
        feature_cols = json.load(f)

    X = df[feature_cols].copy()
    y = df['Signal'].map(SIGNAL_MAP).astype(int).values

    # 2. Split
    split = int(len(X) * 0.8)
    X_train, X_test = X.iloc[:split], X.iloc[split:]
    y_train, y_test = y[:split], y[split:]

    print(f"\n🔄 Data Cleaned. Training on {len(X_train)} samples...")

    # 3. Cross Validation Loop
    tscv = TimeSeriesSplit(n_splits=5)
    for fold, (tr_idx, val_idx) in enumerate(tscv.split(X_train), 1):
        X_tr, X_val = X_train.iloc[tr_idx], X_train.iloc[val_idx]
        y_tr, y_val = y_train[tr_idx], y_train[val_idx]

        model = XGBClassifier(**XGB_PARAMS)
        model.fit(X_tr, y_tr, eval_set=[(X_val, y_val)], verbose=False)
        
        # --- THE FIX ---
        # 1. Get raw predictions (probabilities)
        preds_raw = model.predict(X_val) 
        
        # 2. Check if output is a probability matrix (Nx3)
        if len(preds_raw.shape) > 1 and preds_raw.shape[1] == 3:
            # Pick the index with the highest probability (0, 1, or 2)
            y_pred = np.argmax(preds_raw, axis=1)
        else:
            # Already a 1D array
            y_pred = preds_raw
            
        y_pred = y_pred.astype(int).flatten()
        y_val  = y_val.astype(int).flatten()
        
        # Now both y_val and y_pred will have length 70
        acc = accuracy_score(y_val, y_pred)
        print(f"   ✅ Fold {fold} Accuracy: {acc:.4f} (Samples: {len(y_val)})")

    # 4. Final Training
    print("\n🤖 Training final model...")
    final_model = XGBClassifier(**XGB_PARAMS)
    final_model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=100)

    # Save
    final_model.save_model(os.path.join(save_dir, "xgb_model.json"))
    print("\n✨ Success! Model saved.")

if __name__ == "__main__":
    main()