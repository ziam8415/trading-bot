import time
import datetime
import os
import subprocess
from colorama import Fore, Style, init

# Initialize colors for the terminal
init(autoreset=True)

# ==============================
# CONFIG
# ==============================
# Set this to match your timeframe (e.g., 3600 for 1H, 900 for 15M)
CHECK_INTERVAL_SECONDS = 60  # Check every minute for data updates
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PREDICT_SCRIPT = os.path.join(SCRIPT_DIR, "predict_model.py")

def run_bot_cycle():
    print(Fore.CYAN + "="*55)
    print(Fore.CYAN + "       GOLD AI LIVE MONITORING STARTING...")
    print(Fore.CYAN + f"       Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(Fore.CYAN + "="*55)

    try:
        while True:
            current_time = datetime.datetime.now().strftime("%H:%M:%S")
            
            # 1. Execute the prediction script
            # We use subprocess to keep the memory clean for each run
            result = subprocess.run(
                ["python", PREDICT_SCRIPT], 
                capture_output=True, 
                text=True
            )

            # 2. Parse the output for signals
            output = result.stdout
            
            if "🔥 ACTIVE SIGNAL" in output:
                print(Fore.GREEN + f"[{current_time}] 🎯 SIGNAL DETECTED!")
                print(output)
                # OPTIONAL: Add your notify_phone() function here
            elif "❌" in output:
                print(Fore.RED + f"[{current_time}] ERROR IN PREDICTION:")
                print(output)
            else:
                # Silent mode for "Wait" signals to keep terminal clean
                print(Fore.YELLOW + f"[{current_time}] Market Scanned: No high-confidence setup found.")

            # 3. Wait for the next check
            time.sleep(CHECK_INTERVAL_SECONDS)

    except KeyboardInterrupt:
        print(Fore.WHITE + "\n[!] Live Monitoring Stopped by User.")

if __name__ == "__main__":
    run_bot_cycle()