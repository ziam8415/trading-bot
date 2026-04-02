import sys
import io
import pandas as pd
import numpy as np
import os
import json
from xgboost import XGBClassifier

# Force UTF-8 for Emojis
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Adjusted threshold for higher precision
CONFIDENCE_THRESHOLD = 0.55  
SIGNAL_NAMES = {0: "SELL", 1: "WAIT", 2: "BUY"}

def _get_dirs():
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return {
        "model_json": os.path.join(BASE_DIR, "models", "saved_models", "xgb_model.json"),
        "features_csv": os.path.join(BASE_DIR, "data", "processed", "features.csv"),
    }

def run_prediction():
    dirs = _get_dirs()
    output_msg = []
    output_msg.append("=======================================================")
    output_msg.append("    GOLD AI BOT — PREDICTION TERMINAL")
    output_msg.append("=======================================================")

    # 1. Check Model Path
    if not os.path.exists(dirs["model_json"]):
        print(f"❌ Error: Model file missing at {dirs['model_json']}")
        return

    # 2. Load Model
    try:
        model = XGBClassifier()
        model.load_model(dirs["model_json"])
        # Get exactly what the model was trained on
        expected_features = model.get_booster().feature_names
        output_msg.append(f"✅ Model loaded. Expecting {len(expected_features)} features.")
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        return

    # 3. Load Features
    if not os.path.exists(dirs["features_csv"]):
        print("❌ Error: features.csv missing.")
        return

    df = pd.read_csv(dirs["features_csv"])
    if df.empty:
        print("❌ Error: features.csv is empty.")
        return

    # --- CRITICAL FIX: COLUMN NAME SYNC ---
    # Convert CSV columns to lowercase to match our new feature_engineering.py
    df.columns = [c.lower() for c in df.columns]
    
    # Also ensure the 'expected_features' list is lowercase to match the DF
    # XGBoost saves feature names exactly as they were during training.
    # If your model was trained on 'RSI', but CSV has 'rsi', this bridge is required.
    clean_expected = [f.lower() for f in expected_features]
    # --------------------------------------

    # 4. Extract Latest Row
    latest_row_raw = df.iloc[-1:]
    
    try:
        # Select only the features the model needs
        X_latest = latest_row_raw[clean_expected]
        
        # XGBoost requires the actual feature names to match its internal booster
        # We rename the columns of our snapshot to match the model's expected names exactly
        X_latest.columns = expected_features 
        
        # 5. Predict
        probs = model.predict_proba(X_latest)[0]  
        pred_class = np.argmax(probs)
        confidence = probs[pred_class]

        output_msg.append(f"\n📈 MARKET SNAPSHOT:")
        # Use .iloc[0] to get the value from the 1-row dataframe
        output_msg.append(f"   Time:  {latest_row_raw['time'].iloc[0]}")
        output_msg.append(f"   Price: ${latest_row_raw['close'].iloc[0]:,.2f}")
        output_msg.append("-" * 30)
        output_msg.append(f"🤖 AI PROBABILITIES:")
        output_msg.append(f"   [SELL]: {probs[0]:.2%}")
        output_msg.append(f"   [WAIT]: {probs[1]:.2%}")
        output_msg.append(f"   [BUY ]: {probs[2]:.2%}")
        output_msg.append("-" * 30)

        if confidence >= CONFIDENCE_THRESHOLD and pred_class != 1:
            output_msg.append(f"📢 SIGNAL: {SIGNAL_NAMES[pred_class]} (Active)")
            output_msg.append(f"✅ ACTION: Execute {SIGNAL_NAMES[pred_class]} trade.")
        else:
            output_msg.append(f"📢 SIGNAL: WAIT (Neutral)")
            reason = "Low Confidence" if pred_class != 1 else "Market Ranging"
            output_msg.append(f"ℹ️  REASON: {reason}")

    except KeyError as e:
        output_msg.append(f"❌ Feature Mismatch Error: {e}")
        output_msg.append("💡 Try deleting data/processed/features.csv and restarting.")
    except Exception as e:
        output_msg.append(f"❌ Prediction Error: {e}")

    # Print output for main.py logs
    print("\n".join(output_msg))

if __name__ == "__main__":
    run_prediction()