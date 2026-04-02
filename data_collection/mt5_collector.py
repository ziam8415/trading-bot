import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timedelta

def connect_mt5():
    # Shutdown to refresh connection state
    mt5.shutdown()
    if not mt5.initialize():
        login = 413604055          
        password = "Ab123456@@"  
        server = "Exness-MT5Trial6" 
        if not mt5.login(login, password=password, server=server):
            print(f"❌ MT5 Login Failed: {mt5.last_error()}")
            return False
    return True

def get_xauusd_data():
    if not connect_mt5():
        return None

    symbol = "XAUUSD"
    mt5.symbol_select(symbol, True)

    # Fetch 500 bars (M1)
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, 500)

    if rates is None or len(rates) == 0:
        mt5.shutdown()
        return None

    df = pd.DataFrame(rates)
    
    # --- FIXED TIME CONVERSION ---
    df['time'] = pd.to_datetime(df['time'], unit='s')

    # Calculate difference between Broker and Local System Time
    broker_time = df['time'].iloc[-1]
    local_time = datetime.now()
    
    # Get total hour difference (e.g., 3)
    hour_diff = round((broker_time - local_time).total_seconds() / 3600)
    
    # SHIFT THE TIME to match your local clock
    df['time'] = df['time'] - timedelta(hours=hour_diff)
    
    # Format as string so it matches the CSV format exactly
    df['time'] = df['time'].dt.strftime('%Y-%m-%d %H:%M:%S')
    # -----------------------------

    df = df[['time', 'open', 'high', 'low', 'close', 'tick_volume', 'spread']]
    df.columns = ['time', 'open', 'high', 'low', 'close', 'volume', 'spread']

    mt5.shutdown()
    return df