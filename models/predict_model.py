import joblib

def predict_signal(df):

    model = joblib.load("models/gold_model.pkl")

    latest = df[["rsi","ma50","ma200"]].iloc[-1:]

    prediction = model.predict(latest)[0]

    return prediction