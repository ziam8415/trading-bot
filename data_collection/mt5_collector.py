import MetaTrader5 as mt5
import pandas as pd

def connect_mt5():
    # Attempt to connect to an ALREADY OPEN terminal first
    if not mt5.initialize():
        # If that fails, try to login explicitly
        # Replace the numbers below with your actual account info
        login = 413604055          # Your MT5 Account Number
        password = "Ab123456@@"  # Your Trading Password
        server = "Exness-MT5Trial6" # e.g., "Exness-MT5-Trial" or "ICMarkets-Demo"
        path = "C:\\Program Files\\MetaTrader 5\\terminal64.exe"

        if not mt5.login(login, password=password, server=server):
            print(f"❌ Failed to login to account {login}: {mt5.last_error()}")
            return False
            
    print("✅ MT5 Authorized and Connected")
    return True

def get_xauusd_data():
    if not connect_mt5():
        raise Exception("MT5 initialization failed")

    symbol = "XAUUSD"
    # Ensure symbol is visible in Market Watch
    if not mt5.symbol_select(symbol, True):
        mt5.shutdown()
        raise Exception(f"{symbol} not available. Check your broker's symbol name.")

    # FIXED: Reduced count from 100,000 to 500 to avoid 'Invalid params' error
    # For a live bot, you only need enough bars for your indicators (e.g., RSI 14, EMA 200)
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, 50000)

    if rates is None:
        err = mt5.last_error()
        mt5.shutdown()
        raise Exception(f"Failed to fetch data: {err}")

    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    
    # Standardize column names for your pipeline
    df = df[['time', 'open', 'high', 'low', 'close', 'tick_volume', 'spread']]
    df.columns = ['time', 'open', 'high', 'low', 'close', 'volume', 'spread']

    mt5.shutdown()
    return df

if __name__ == "__main__":
    try:
        data = get_xauusd_data()
        print("✅ Latest Data:\n", data.tail())
    except Exception as e:
        print(e)