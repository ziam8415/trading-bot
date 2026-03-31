import MetaTrader5 as mt5
import pandas as pd

def connect_mt5():
    if not mt5.initialize(
        path="C:\\Program Files\\MetaTrader 5\\terminal64.exe"
    ):
        print("Error:", mt5.last_error())
        raise Exception("MT5 initialization failed")
    print("MT5 connected")

def ensure_symbol(symbol):
    if not mt5.symbol_select(symbol, True):
        raise Exception(f"{symbol} not available")

def get_xauusd_data():
    connect_mt5()
    ensure_symbol("XAUUSD")

    rates = mt5.copy_rates_from_pos("XAUUSD", mt5.TIMEFRAME_M15, 0, 100)

    if rates is None:
        print("Error:", mt5.last_error())
        mt5.shutdown()
        raise Exception("Failed to fetch data")

    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')

    mt5.shutdown()
    return df


if __name__ == "__main__":
    data = get_xauusd_data()
    print(data.tail())