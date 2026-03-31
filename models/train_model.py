from sklearn.ensemble import RandomForestClassifier
import joblib

def train_model(df):

    df["future"] = df["Close"].shift(-1)

    df["target"] = (df["future"] > df["Close"]).astype(int)

    df.dropna(inplace=True)

    X = df[["rsi","ma50","ma200"]]

    y = df["target"]

    model = RandomForestClassifier()

    model.fit(X,y)

    joblib.dump(model,"models/gold_model.pkl")

    return model