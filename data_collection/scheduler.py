import schedule
import time
import pandas as pd
import os
import sys
from datetime import datetime

# ✅ FIX: This allows the script to find the project root regardless of how it's launched
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Now we can import using the full path reliably
try:
    from data_collection.mt5_collector import get_xauusd_data
    from data_collection.dxy_collector import get_dxy_data
    from data_collection.news_collector import fetch_gold_news
except ModuleNotFoundError:
    # Fallback for direct execution
    from mt5_collector import get_xauusd_data
    from dxy_collector import get_dxy_data
    from news_collector import fetch_gold_news

BASE_DIR = PROJECT_ROOT

def save_market_data(df, filename):
    """
    Saves data ensuring no duplicate timestamps. 
    """
    try:
        path = os.path.join(BASE_DIR, "data", "raw", filename)
        os.makedirs(os.path.dirname(path), exist_ok=True)

        # Ensure 'time' column is string for CSV comparison
        df['time'] = df['time'].astype(str)

        if os.path.exists(path):
            try:
                existing_df = pd.read_csv(path)
                existing_df['time'] = existing_df['time'].astype(str)
            except Exception:
                existing_df = pd.DataFrame()

            # Merge and remove duplicates (keeps the newest data)
            combined_df = pd.concat([existing_df, df], ignore_index=True)
            combined_df = combined_df.drop_duplicates(subset=['time'], keep='last')
            
            # Sort and cap size (Keep last 100k rows)
            combined_df = combined_df.sort_values('time').tail(100000)
            
            combined_df.to_csv(path, index=False)
            total_rows = len(combined_df)
        else:
            df.sort_values('time').to_csv(path, index=False)
            total_rows = len(df)
            
        print(f"✅ {filename} Synced | Total History: {total_rows} rows | Last: {df['time'].iloc[-1]}")

    except PermissionError:
        print(f"❌ Close {filename} in Excel! Permission Denied.")
    except Exception as e:
        print(f"❌ Error saving {filename}: {e}")

# ==============================
# JOBS
# ==============================

def job_market_data():
    try:
        df = get_xauusd_data()
        if df is not None and not df.empty:
            save_market_data(df, "xauusd.csv")
    except Exception as e:
        print(f"❌ XAUUSD Sync Error: {e}")

def job_dxy_data():
    try:
        df = get_dxy_data()
        if df is not None and not df.empty:
            # Flatten multi-index if needed
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            
            df = df.reset_index()
            df.columns = [str(c).lower().strip() for c in df.columns]
            
            # Map time columns
            if 'datetime' in df.columns:
                df.rename(columns={'datetime': 'time'}, inplace=True)
            elif 'date' in df.columns:
                df.rename(columns={'date': 'time'}, inplace=True)
            
            df['time'] = pd.to_datetime(df['time']).dt.strftime('%Y-%m-%d %H:%M:%S')
            save_market_data(df, "dxy.csv")
    except Exception as e:
        print(f"❌ DXY Sync Error: {e}")

def job_news():
    try:
        news = fetch_gold_news()
        if news:
            df = pd.DataFrame(news)
            path = os.path.join(BASE_DIR, "data", "raw", "news.csv")
            df.to_csv(path, mode='a', header=not os.path.exists(path), index=False)
            print(f"✅ News Headlines Saved ({len(df)} new articles)")
    except Exception as e:
        print(f"❌ News Error: {e}")

# ==============================
# RUNNER
# ==============================

if __name__ == "__main__":
    print("🚀 Running standalone data sync...")
    job_market_data()
    job_dxy_data()