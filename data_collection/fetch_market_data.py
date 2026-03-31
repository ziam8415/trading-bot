import yfinance as yf
import pandas as pd

def get_gold_data():
    data = yf.download("GC=F", period="1mo", interval="1h")
    data = data[['Open','High','Low','Close','Volume']]
    data.dropna(inplace=True)
    return data


data = get_gold_data()

print(data.head())