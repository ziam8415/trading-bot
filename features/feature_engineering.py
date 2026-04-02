import pandas as pd
import numpy as np
import os
import json

# ==============================
# CONFIG
# ==============================
RAW_DATA_FILE    = "xauusd.csv"
SIGNAL_THRESHOLD = 0.0015  
SIGNAL_LOOKAHEAD = 5       

# Columns that are NOT used as input features for the AI model
EXCLUDE_FROM_FEATURES = [
    'time', 'open', 'high', 'low', 'close', 'volume', 'spread',
    'future_close', 'future_return', 'signal',
    'high_20', 'low_20', 'bb_middle', 'bb_upper', 'bb_lower',
    'candle_body', 'candle_range', 'ema20', 'ema50'
]

# ==============================
# LOAD & CLEAN
# ==============================
def load_data(filename=RAW_DATA_FILE):
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path     = os.path.join(BASE_DIR, "data", "raw", filename)

    if not os.path.exists(path): 
        raise FileNotFoundError(f"❌ Missing raw data file: {path}")
    
    df = pd.read_csv(path)
    df.columns = df.columns.str.lower()
    
    if 'tick_volume' in df.columns: 
        df.rename(columns={'tick_volume': 'volume'}, inplace=True)
    
    df['time'] = pd.to_datetime(df['time'], errors='coerce')
    numeric_cols = ['open', 'high', 'low', 'close', 'volume']
    for col in numeric_cols: 
        df[col] = pd.to_numeric(df[col], errors='coerce')

    df.dropna(subset=['time', 'close'], inplace=True)
    df.drop_duplicates(subset=['time'], inplace=True)
    df.sort_values('time', inplace=True)
    return df.reset_index(drop=True)

# ==============================
# INDICATORS
# ==============================
def calculate_indicators(df):
    # RSI
    period = 14
    delta = df['close'].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    df['rsi'] = 100 - (100 / (1 + rs))

    # MACD
    ema12 = df['close'].ewm(span=12, adjust=False).mean()
    ema26 = df['close'].ewm(span=26, adjust=False).mean()
    df['macd'] = ema12 - ema26
    df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
    df['macd_hist'] = df['macd'] - df['macd_signal']

    # ATR
    tr = pd.concat([df['high']-df['low'], abs(df['high']-df['close'].shift()), abs(df['low']-df['close'].shift())], axis=1).max(axis=1)
    df['atr'] = tr.rolling(14).mean()
    df['atr_pct'] = df['atr'] / df['close']
    
    return df

# ==============================
# STATIONARY FEATURES
# ==============================
def build_features(df):
    # Bollinger
    mid = df['close'].rolling(20).mean()
    std = df['close'].rolling(20).std()
    df['bb_width'] = (4 * std) / mid
    df['bb_position'] = (df['close'] - (mid - 2*std)) / (4 * std)
    
    # Returns & Vol
    df['return_1'] = df['close'].pct_change(1)
    df['return_5'] = df['close'].pct_change(5)
    df['volatility_10'] = df['return_1'].rolling(10).std()
    
    # Structure
    h20, l20 = df['high'].rolling(20).max(), df['low'].rolling(20).min()
    df['price_position'] = (df['close'] - l20) / (h20 - l20 + 1e-9)
    df['body_ratio'] = abs(df['close'] - df['open']) / (df['high'] - df['low'] + 1e-9)
    df['candle_direction'] = np.where(df['close'] >= df['open'], 1, -1)
    
    # Trend
    e20, e50 = df['close'].ewm(span=20).mean(), df['close'].ewm(span=50).mean()
    df['price_vs_ema20'] = (df['close'] - e20) / e20
    df['ema_diff_pct'] = (e20 - e50) / e50
    df['ema_cross'] = np.sign(e20 - e50).diff()
    
    # Lags (Historical context for the AI)
    for lag in range(1, 6):
        df[f'rsi_lag_{lag}'] = df['rsi'].shift(lag)
        df[f'return_lag_{lag}'] = df['return_1'].shift(lag)
        
    return df

def create_signal(df):
    """
    Calculates the target 'Signal' for training. 
    Note: Last 5 rows will be NaN because the future hasn't happened yet.
    """
    df['future_return'] = (df['close'].shift(-SIGNAL_LOOKAHEAD) - df['close']) / df['close']
    df['signal'] = 0
    df.loc[df['future_return'] > SIGNAL_THRESHOLD, 'signal'] = 1
    df.loc[df['future_return'] < -SIGNAL_THRESHOLD, 'signal'] = -1
    return df

# ==============================
# MAIN EXECUTION
# ==============================
if __name__ == "__main__":
    df = load_data()
    df = calculate_indicators(df)
    df = build_features(df)
    df = create_signal(df)
    
    # ✅ FIX: DO NOT drop the entire row if 'signal' is NaN.
    # Only drop rows where indicators (RSI/ATR) are NaN (the first 20-30 rows).
    critical_indicators = ['rsi', 'atr', 'bb_width', 'volatility_10']
    df.dropna(subset=critical_indicators, inplace=True)
    
    # Save the processed features
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    p_dir = os.path.join(BASE_DIR, "data", "processed")
    os.makedirs(p_dir, exist_ok=True)
    
    feature_path = os.path.join(p_dir, "features.csv")
    df.to_csv(feature_path, index=False)
    
    # Save the JSON list of feature columns for the prediction model
    cols = [c for c in df.columns if c not in EXCLUDE_FROM_FEATURES]
    with open(os.path.join(p_dir, "feature_columns.json"), 'w') as f:
        json.dump(cols, f)
        
    last_time = df['time'].iloc[-1]
    print(f"✅ Features Saved. Latest Time in Features: {last_time}")