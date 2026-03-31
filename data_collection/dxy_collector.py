import yfinance as yf
import pandas as pd

def get_dxy_data():
    data = yf.download("DX-Y.NYB", period="5d", interval="15m")

    if data.empty:
        raise Exception("Failed to fetch DXY data")

    data = data[['Open', 'High', 'Low', 'Close', 'Volume']]
    data.dropna(inplace=True)

    data.reset_index(inplace=True)

    return data


if __name__ == "__main__":
    dxy = get_dxy_data()
    print(dxy.tail())