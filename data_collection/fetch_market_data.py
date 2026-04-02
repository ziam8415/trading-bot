import pandas as pd
import os
from datetime import datetime
# Ensure these imports work based on your file names
from data_collection.mt5_collector import get_xauusd_data
from data_collection.dxy_collector import get_dxy_data
# from data_collection.news_collector import fetch_gold_news # Uncomment if using news

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def save_market_data(df, filename):
    try:
        path = os.path.join(BASE_DIR, "data", "raw", filename)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        df['time'] = df['time'].astype(str)

        if os.path.exists(path):
            existing_df = pd.read_csv(path)
            existing_df['time'] = existing_df['time'].astype(str)
            combined_df = pd.concat([existing_df, df], ignore_index=True)
            combined_df = combined_df.drop_duplicates(subset=['time'], keep='last')
            combined_df = combined_df.sort_values('time')
            combined_df.to_csv(path, index=False)
            total_rows = len(combined_df)
        else:
            df = df.sort_values('time')
            df.to_csv(path, index=False)
            total_rows = len(df)
        print(f"✅ Synced: {filename} | Total History: {total_rows} rows")
    except Exception as e:
        print(f"❌ Error saving {filename}: {e}")

def run_all_collections():
    """This function is what main.py will call"""
    print(f"\n--- Data Sync Start: {datetime.now().strftime('%H:%M:%S')} ---")
    
    # 1. Gold Data
    try:
        df_gold = get_xauusd_data()
        save_market_data(df_gold, "xauusd.csv")
    except Exception as e: print(f"Gold Error: {e}")

    # 2. DXY Data
    try:
        df_dxy = get_dxy_data()
        # Clean DXY columns as per your original logic
        if isinstance(df_dxy.columns, pd.MultiIndex):
            df_dxy.columns = df_dxy.columns.get_level_values(0)
        df_dxy = df_dxy.reset_index()
        df_dxy.columns = [str(c).strip().lower() for c in df_dxy.columns]
        if 'datetime' in df_dxy.columns: df_dxy.rename(columns={'datetime': 'time'}, inplace=True)
        df_dxy['time'] = pd.to_datetime(df_dxy['time']).dt.strftime('%Y-%m-%d %H:%M:%S')
        save_market_data(df_dxy, "dxy.csv")
    except Exception as e: print(f"DXY Error: {e}")

# This part allows it to still run if you double-click THIS file manually
if __name__ == "__main__":
    run_all_collections()