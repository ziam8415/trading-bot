import ta

def add_indicators(df):

    df["rsi"] = ta.momentum.rsi(df["Close"], window=14)

    df["ma50"] = df["Close"].rolling(50).mean()

    df["ma200"] = df["Close"].rolling(200).mean()

    df.dropna(inplace=True)

    return df