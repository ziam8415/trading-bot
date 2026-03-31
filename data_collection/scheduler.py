import schedule
import time
import pandas as pd

from mt5_collector import get_xauusd_data
from dxy_collector import get_dxy_data
from news_collector import fetch_gold_news


def save_to_csv(df, path):
    df.to_csv(path, mode='a', header=not pd.io.common.file_exists(path), index=False)


def job_market_data():
    print("Fetching XAUUSD data...")
    df = get_xauusd_data()
    save_to_csv(df, "../data/raw/xauusd.csv")


def job_dxy_data():
    print("Fetching DXY data...")
    df = get_dxy_data()
    save_to_csv(df, "../data/raw/dxy.csv")


def job_news():
    print("Fetching news...")
    news = fetch_gold_news()

    df = pd.DataFrame(news)
    save_to_csv(df, "../data/raw/news.csv")


# Schedule jobs
schedule.every(15).minutes.do(job_market_data)
schedule.every(30).minutes.do(job_dxy_data)
schedule.every(1).hours.do(job_news)


if __name__ == "__main__":
    print("Scheduler started...")

    while True:
        schedule.run_pending()
        time.sleep(1)