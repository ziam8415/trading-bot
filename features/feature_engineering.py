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

EXCLUDE_FROM_FEATURES = [
    'time', 'open', 'high', 'low', 'close', 'volume', 'spread',
    'future_close', 'future_return', 'Signal',
    'high_20', 'low_20', 'BB_middle', 'BB_upper', 'BB_lower',
    'candle_body', 'candle_range', 'EMA20', 'EMA50'
]

# ==============================
# LOAD & CLEAN
# ==============================
def load_data(filename=RAW_DATA_FILE):
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path     = os.path.join(BASE_DIR, "data", "raw", filename)

    if not os.path.exists(path): raise FileNotFoundError(f"Missing: {path}")
    
    df = pd.read_csv(path)
    df.columns = df.columns.str.lower()
    
    # Standardize column names
    if 'tick_volume' in df.columns: df.rename(columns={'tick_volume': 'volume'}, inplace=True)
    
    df['time'] = pd.to_datetime(df['time'], errors='coerce')
    numeric_cols = ['open', 'high', 'low', 'close', 'volume']
    for col in numeric_cols: df[col] = pd.to_numeric(df[col], errors='coerce')

    df.dropna(inplace=True)
    df.drop_duplicates(subset=['time'], inplace=True)
    df.sort_values('time', inplace=True)
    return df.reset_index(drop=True)

# ==============================
# INDICATORS
# ==============================
def calculate_rsi(df, period=14):
    delta = df['close'].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    df['RSI'] = 100 - (100 / (1 + rs))
    return df

def calculate_macd(df):
    ema12 = df['close'].ewm(span=12, adjust=False).mean()
    ema26 = df['close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = ema12 - ema26
    df['MACD_signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_hist'] = df['MACD'] - df['MACD_signal']
    return df

def calculate_atr(df, period=14):
    tr = pd.concat([df['high']-df['low'], abs(df['high']-df['close'].shift()), abs(df['low']-df['close'].shift())], axis=1).max(axis=1)
    df['ATR'] = tr.rolling(period).mean()
    df['ATR_pct'] = df['ATR'] / df['close']
    return df

# ==============================
# STATIONARY FEATURES
# ==============================
def build_features(df):
    # Bollinger
    mid = df['close'].rolling(20).mean()
    std = df['close'].rolling(20).std()
    df['BB_width'] = (4 * std) / mid
    df['BB_position'] = (df['close'] - (mid - 2*std)) / (4 * std)
    
    # Returns & Vol
    df['return_1'] = df['close'].pct_change(1)
    df['return_5'] = df['close'].pct_change(5)
    df['volatility_10'] = df['return_1'].rolling(10).std()
    
    # Structure
    h20, l20 = df['high'].rolling(20).max(), df['low'].rolling(20).min()
    df['price_position'] = (df['close'] - l20) / (h20 - l20)
    df['body_ratio'] = abs(df['close'] - df['open']) / (df['high'] - df['low'])
    df['candle_direction'] = np.where(df['close'] >= df['open'], 1, -1)
    
    # Trend
    e20, e50 = df['close'].ewm(span=20).mean(), df['close'].ewm(span=50).mean()
    df['price_vs_EMA20'] = (df['close'] - e20) / e20
    df['EMA_diff_pct'] = (e20 - e50) / e50
    df['EMA_cross'] = np.sign(e20 - e50).diff()
    
    # Lags
    for lag in range(1, 6):
        df[f'rsi_lag_{lag}'] = df['RSI'].shift(lag)
        df[f'return_lag_{lag}'] = df['return_1'].shift(lag)
        
    return df

def create_signal(df):
    df['future_return'] = (df['close'].shift(-SIGNAL_LOOKAHEAD) - df['close']) / df['close']
    df['Signal'] = 0
    df.loc[df['future_return'] > SIGNAL_THRESHOLD, 'Signal'] = 1
    df.loc[df['future_return'] < -SIGNAL_THRESHOLD, 'Signal'] = -1
    return df

if __name__ == "__main__":
    df = load_data()
    df = calculate_rsi(df)
    df = calculate_macd(df)
    df = calculate_atr(df)
    df = build_features(df)
    df = create_signal(df)
    df.dropna(inplace=True)
    
    # Save
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    p_dir = os.path.join(BASE_DIR, "data", "processed")
    os.makedirs(p_dir, exist_ok=True)
    
    df.to_csv(os.path.join(p_dir, "features.csv"), index=False)
    cols = [c for c in df.columns if c not in EXCLUDE_FROM_FEATURES]
    with open(os.path.join(p_dir, "feature_columns.json"), 'w') as f:
        json.dump(cols, f)
    print(f"✅ Features Saved. Ready to Train.")