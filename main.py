import sys
import io
import time
import datetime
import os
import subprocess
from colorama import Fore, init

# Import the Telegram notifier
try:
    from notifications.telegram_alert import notifier 
except ImportError:
    print(Fore.RED + "⚠️ Telegram notifier not found. Continuing without alerts.")
    notifier = None

# ✅ IMPORT JOBS DIRECTLY
# Note: Ensure you have an empty __init__.py in the data_collection folder
try:
    from data_collection.scheduler import job_market_data, job_dxy_data
except ImportError as e:
    print(Fore.RED + f"❌ Import Error: {e}")
    print(Fore.YELLOW + "Make sure 'data_collection' has an __init__.py file.")
    sys.exit(1)

# Force UTF-8 for Emojis in Windows Terminal
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
init(autoreset=True)

# CONFIGURATION
CHECK_INTERVAL_SECONDS = 60  
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# SCRIPT PATHS
FEATURE_SCRIPT = os.path.join(BASE_DIR, "features", "feature_engineering.py")
PREDICT_SCRIPT = os.path.join(BASE_DIR, "models", "predict_model.py")

def run_bot_cycle():
    print(Fore.CYAN + "=======================================================")
    print(Fore.CYAN + " 🚀 GOLD AI BOT: FULL PIPELINE ACTIVE")
    print(Fore.CYAN + f" 📅 Start Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(Fore.CYAN + "=======================================================")
    
    if notifier:
        notifier.send_sync_message("✅ *Gold AI Bot Started*\nPipeline active: Syncing every 60s.")

    try:
        while True:
            start_time = time.time()
            current_time = datetime.datetime.now().strftime("%H:%M:%S")
            
            print(Fore.WHITE + f"\n🔔 [Cycle Start: {current_time}]")

            # --- STEP 1: FETCH DATA ---
            print(Fore.BLUE + "📥 Step 1: Syncing Raw Market Data...")
            try:
                job_market_data()
                job_dxy_data()
            except Exception as e:
                print(Fore.RED + f"❌ Data Sync Failed: {e}")

            # --- STEP 2: GENERATE FEATURES ---
            print(Fore.BLUE + "⚙️  Step 2: Recalculating Features...")
            # We run this as a subprocess to ensure fresh pandas memory
            subprocess.run([sys.executable, FEATURE_SCRIPT], capture_output=False)

            # --- STEP 3: RUN PREDICTION ---
            print(Fore.BLUE + "🤖 Step 3: Running AI Prediction...")
            result = subprocess.run(
                [sys.executable, PREDICT_SCRIPT], 
                capture_output=True, 
                text=True,
                encoding='utf-8'
            )

            output = result.stdout.strip()
            
            # --- STEP 4: OUTPUT & NOTIFY ---
            if output:
                # Print prediction terminal to local console
                print(output)
                
                # Send to Telegram
                if notifier:
                    # Wrap in triple backticks for fixed-width formatting in Telegram
                    notifier.send_sync_message(f"```\n{output}\n```")
            
            if result.stderr:
                print(Fore.RED + f"⚠️ Prediction Script Error:\n{result.stderr}")

            # --- STEP 5: DYNAMIC SLEEP ---
            # This ensures we run exactly every 60 seconds, 
            # accounting for the time the scripts took to run.
            elapsed = time.time() - start_time
            sleep_time = max(1, CHECK_INTERVAL_SECONDS - elapsed)
            
            print(Fore.MAGENTA + f"😴 Cycle complete. Waiting {round(sleep_time)}s...")
            time.sleep(sleep_time)

    except KeyboardInterrupt:
        print(Fore.YELLOW + "\n👋 Shutdown signal received. Stopping Bot...")
        if notifier:
            notifier.send_sync_message("🛑 *Gold AI Bot Offline*")

if __name__ == "__main__":
    run_bot_cycle()