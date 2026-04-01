import schedule
import time
import pandas as pd
import os
from datetime import datetime

# Importing your custom collectors
from mt5_collector import get_xauusd_data
from dxy_collector import get_dxy_data
from news_collector import fetch_gold_news

# ✅ Get project root directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def save_market_data(df, filename):
    """
    Saves data ensuring no duplicate timestamps. 
    Grows the file indefinitely (No .tail() cap).
    """
    try:
        path = os.path.join(BASE_DIR, "data", "raw", filename)
        os.makedirs(os.path.dirname(path), exist_ok=True)

        # Ensure the 'time' column is in string format for consistent CSV comparison
        df['time'] = df['time'].astype(str)

        if os.path.exists(path):
            # 1. Load existing data
            try:
                existing_df = pd.read_csv(path)
                existing_df['time'] = existing_df['time'].astype(str)
            except Exception as e:
                print(f"⚠️ Could not read existing {filename}, creating new: {e}")
                existing_df = pd.DataFrame()

            # 2. Merge and remove duplicates
            # 'keep=last' ensures that if a candle was partial before, it gets updated with final data
            combined_df = pd.concat([existing_df, df], ignore_index=True)
            combined_df = combined_df.drop_duplicates(subset=['time'], keep='last')
            
            # 3. Sort by time (Oldest to Newest)
            combined_df = combined_df.sort_values('time')
            
            # 4. Save (Overwrites with the full new history)
            combined_df.to_csv(path, index=False)
            total_rows = len(combined_df)
        else:
            # First time creating the file
            df = df.sort_values('time')
            df.to_csv(path, index=False)
            total_rows = len(df)
            
        print(f"✅ Synced: {filename} | Total History: {total_rows} rows")

    except PermissionError:
        print(f"❌ CRITICAL: Could not save {filename}. Close the file if it's open in Excel!")
    except Exception as e:
        print(f"❌ Error saving {filename}: {e}")

# ==============================
# SCHEDULED JOBS
# ==============================

def job_market_data():
    try:
        print("\n📊 Fetching XAUUSD (M1)...")
        df = get_xauusd_data()
        save_market_data(df, "xauusd.csv")
    except Exception as e:
        print(f"❌ Market data error: {e}")

def job_dxy_data():
    try:
        print("\n💲 Fetching DXY Index...")
        df = get_dxy_data()
        
        # 1. Flatten Multi-Index columns (yfinance 0.2.x+ fix)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # 2. Reset index so 'Datetime' becomes a column
        df = df.reset_index()

        # 3. Clean column names
        df.columns = [str(c).strip().lower() for c in df.columns]
        
        # 4. FIX: Map 'datetime' (from yfinance) to 'time'
        if 'datetime' in df.columns:
            df.rename(columns={'datetime': 'time'}, inplace=True)
        elif 'date' in df.columns:
            df.rename(columns={'date': 'time'}, inplace=True)
        
        # 5. Ensure the 'time' column exists before saving
        if 'time' not in df.columns:
            print(f"⚠️ Columns found: {df.columns.tolist()}")
            raise KeyError("Could not find a time/date column in DXY data")

        # 6. Format time string
        df['time'] = pd.to_datetime(df['time']).dt.strftime('%Y-%m-%d %H:%M:%S')

        save_market_data(df, "dxy.csv")
        
    except Exception as e:
        print(f"❌ DXY error: {e}")
        
def job_news():
    try:
        print("\n📰 Fetching Gold News...")
        news = fetch_gold_news()
        if news:
            df = pd.DataFrame(news)
            path = os.path.join(BASE_DIR, "data", "raw", "news.csv")
            # News doesn't need duplicate checking usually, we just append
            df.to_csv(path, mode='a', header=not os.path.exists(path), index=False)
            print(f"✅ News Headlines Saved ({len(df)} new articles)")
    except Exception as e:
        print(f"❌ News error: {e}")

# ==============================
# RUNNER
# ==============================

if __name__ == "__main__":
    print("="*55)
    print("🚀 GOLD BOT SCHEDULER ACTIVE")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*55)

    # Run immediate first sync
    job_market_data()
    job_dxy_data()
    
    # Define Schedule
    schedule.every(1).minutes.do(job_market_data)
    schedule.every(1).minutes.do(job_dxy_data)
    schedule.every(1).minutes.do(job_news)

    while True:
        try:
            schedule.run_pending()
            time.sleep(1)
        except KeyboardInterrupt:
            print("\n👋 Scheduler stopped by user.")
            break
        except Exception as e:
            print(f"❌ Scheduler crashed: {e}")
            time.sleep(5) # Wait before retry