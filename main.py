from data_collection.fetch_market_data import get_gold_data
from features.feature_engineering import add_indicators
from models.train_model import train_model
from models.predict_model import predict_signal
from strategy.trading_strategy import generate_signal
from notifications.telegram_alert import send_alert

def run_bot():

    data = get_gold_data()

    data = add_indicators(data)

    train_model(data)

    prediction = predict_signal(data)

    signal = generate_signal(prediction)

    message = f"Gold Trading Signal: {signal}"

    print(message)

    send_alert(message)

if __name__ == "__main__":

    run_bot()