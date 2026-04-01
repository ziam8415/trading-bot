import pandas as pd
import numpy as np
import os
import json
from xgboost import XGBClassifier

# ==============================
# CONFIG
# ==============================
CONFIDENCE_THRESHOLD = 0.55  
SIGNAL_NAMES = {0: "SELL", 1: "WAIT", 2: "BUY"}

# ==============================
# PATHS
# ==============================
def _get_dirs():
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return {
        "model_json":    os.path.join(BASE_DIR, "models", "saved_models", "xgb_model.json"),
        "metadata":      os.path.join(BASE_DIR, "models", "saved_models", "model_metadata.json"),
        "features_csv":  os.path.join(BASE_DIR, "data", "processed", "features.csv"),
    }

def run_prediction():
    dirs = _get_dirs()

    print("=" * 55)
    print("   GOLD AI BOT — PREDICTION TERMINAL")
    print("=" * 55)

    # 1. Load the Model First
    model = XGBClassifier()
    model.load_model(dirs["model_json"])
    
    # 2. Extract the EXACT feature names the model is expecting
    # This is the most reliable way to avoid 'feature_names mismatch'
    expected_features = model.get_booster().feature_names
    print(f"✅ Model loaded. Expecting {len(expected_features)} features.")

    # 3. Load your latest data
    df = pd.read_csv(dirs["features_csv"])
    if df.empty:
        print("❌ features.csv is empty.")
        return

    latest_row_full = df.iloc[-1:]
    
    # 4. HARD ALIGNMENT
    # This creates a DataFrame with ONLY the columns the model wants, 
    # in the EXACT order it wants them.
    try:
        X_latest = latest_row_full[expected_features]
    except KeyError as e:
        print(f"❌ Critical Error: The model wants features not found in your CSV: {e}")
        print("💡 Solution: Re-run feature_engineering.py and train_model.py in order.")
        return

    # 5. Predict
    probs = model.predict_proba(X_latest)[0]  
    pred_class = np.argmax(probs)
    confidence = probs[pred_class]

    # 6. Display Results
    print(f"\n📈 MARKET SNAPSHOT:")
    print(f"   Time:  {latest_row_full['time'].values[0]}")
    print(f"   Price: ${latest_row_full['close'].values[0]:,.2f}")
    print("-" * 30)
    
    print(f"🤖 AI PROBABILITIES:")
    print(f"   [SELL]: {probs[0]:.2%}")
    print(f"   [WAIT]: {probs[1]:.2%}")
    print(f"   [BUY ]: {probs[2]:.2%}")
    print("-" * 30)

    if confidence >= CONFIDENCE_THRESHOLD and pred_class != 1:
        print(f"📢 SIGNAL: {SIGNAL_NAMES[pred_class]} (Confidence: {confidence:.2%})")
        print(f"✅ ACTION: Execute {SIGNAL_NAMES[pred_class]} trade.")
    else:
        print(f"📢 SIGNAL: WAIT (Neutral)")
        print(f"ℹ️  REASON: {'Low Confidence' if pred_class != 1 else 'Market Ranging'}")

if __name__ == "__main__":
    try:
        run_prediction()
    except Exception as e:
        print(f"\n❌ Prediction Error: {e}")