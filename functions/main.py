
# --- Imports from psx_data_reader.py ---
from concurrent.futures import ThreadPoolExecutor, as_completed
from dateutil.relativedelta import relativedelta
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
from collections import defaultdict
from datetime import datetime, date, timedelta
from typing import Union
import requests
import time

# --- Helper functions from psx_data_reader.py ---
def moving_average(data, window=30):
    return data['Close'].rolling(window=window).mean()

def rsi(data, window=14):
    delta = data['Close'].diff()
    gain = delta.where(delta > 0, 0).rolling(window=window).mean()
    loss = -delta.where(delta < 0, 0).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# --- DataReader class from psx_data_reader.py ---
class DataReader:
    def daterange(self, start: date, end: date) -> list:
        return [start + timedelta(days=x) for x in range((end - start).days + 1)]

    def daterange_months(self, start: date, end: date) -> list:
        months = []
        current = start.replace(day=1)
        while current <= end:
            months.append(current)
            if current.month == 12:
                current = current.replace(year=current.year + 1, month=1)
            else:
                current = current.replace(month=current.month + 1)
        return months

    def daterange_daily(self, start: date, end: date) -> list:
        return [start + timedelta(days=x) for x in range((end - start).days + 1)]

    def stocks_daily(self, tickers: Union[str, list], start: date, end: date) -> pd.DataFrame:
        tickers = [tickers] if isinstance(tickers, str) else tickers
        months = self.daterange_months(start, end)
        data = [self.get_psx_data(ticker, months) for ticker in tickers]
        if len(data) == 1:
            df = data[0]
        else:
            df = pd.concat(data, keys=tickers, names=["Ticker", "Date"])
        df = df.loc[(df.index >= pd.to_datetime(start)) & (df.index <= pd.to_datetime(end))]
        df = df[~df.index.duplicated(keep='first')]
        return df

    def preprocess(self, data: list) -> pd.DataFrame:
        data = pd.concat(data)
        data = data.sort_index()
        data = data.rename(columns=str.title)
        data.index.name = "Date"
        data.Volume = data.Volume.str.replace(",", "")
        for column in data.columns:
            data[column] = data[column].str.replace(",", "").astype(np.float64)
        if 'Close' in data.columns:
            data['SMA_30'] = moving_average(data)
            data['RSI'] = rsi(data)
            data['Price_Change_Pct'] = data['Close'].pct_change()
        else:
            print("Error: 'Close' column not found in the data.")
        data.dropna(inplace=True)
        return data

    def get_psx_data(self, ticker, months):
        # Placeholder: implement your data fetching logic here
        # Should return a DataFrame with a DateTime index and columns including 'Close', 'Volume', etc.
        return pd.DataFrame()  # Replace with actual implementation

# Create a single instance for import
data_reader = DataReader()

# --- Firebase and scheduler logic from genie_scheduler.py ---
import firebase_admin
from firebase_admin import credentials, firestore

cred = credentials.Certificate("./stock_genie.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

def load_symbols_from_file(filepath="./psx_symbols.txt"):
    with open(filepath, "r") as f:
        symbols = [line.strip() for line in f if line.strip()]
    return symbols

def safe_get_psx_data(symbol, start_date, end_date, retries=3, delay=2):
    for attempt in range(retries):
        try:
            return data_reader.stocks_daily(symbol, start_date, end_date)
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data for {symbol}: {e}. Retrying ({attempt+1}/{retries})...")
            time.sleep(delay)
    print(f"Failed to fetch data for {symbol} after {retries} attempts.")
    return pd.DataFrame()

def get_last_n_trading_days(symbol, n_days=5):
    end_date = date.today()
    start_date = end_date - relativedelta(months=2)
    data = safe_get_psx_data(symbol, start_date, end_date)
    if data.empty:
        print(f"No data for {symbol} in the last two months.")
        return data
    data = data.sort_index()
    last_n = data.tail(n_days)
    return last_n

def fetch_all_stocks_last_n_days(symbols, n_days=5):
    stock_data = {}
    for symbol in symbols:
        data = get_last_n_trading_days(symbol, n_days)
        if not data.empty:
            stock_data[symbol] = data
            print(f"Fetched last {n_days} trading days for {symbol}")
        else:
            print(f"No data for {symbol}")
    return stock_data

def store_all_stocks_last_n_days_to_firebase(all_stocks_data):
    for symbol, df in all_stocks_data.items():
        records = df.reset_index().to_dict(orient="records")
        db.collection("stocks").document(symbol).set({"recent_days": records})
        print(f"Stored {symbol} last 5 days in Firebase.")

def update_stock_recent_days(symbol):
    today = date.today()
    yesterday = today - timedelta(days=7)
    df = safe_get_psx_data(symbol, yesterday, today)
    if df.empty:
        print(f"No new data for {symbol}")
        return
    latest_row = df.sort_index().iloc[-1]
    new_day_data = latest_row.to_dict()
    new_day_data['Date'] = str(latest_row.name)
    doc_ref = db.collection("stocks").document(symbol)
    doc = doc_ref.get()
    if doc.exists:
        recent_days = doc.to_dict().get("recent_days", [])
    else:
        recent_days = []
    if any(day.get("Date") == new_day_data["Date"] for day in recent_days):
        print(f"Data for {symbol} on {new_day_data['Date']} already exists.")
        return
    recent_days.append(new_day_data)
    if len(recent_days) > 5:
        recent_days = recent_days[-5:]
    doc_ref.set({"recent_days": recent_days})
    print(f"Updated {symbol} with latest day. Total days stored: {len(recent_days)}")

def get_all_stocks_from_firebase():
    stocks_ref = db.collection("stocks")
    docs = stocks_ref.stream()
    stocks_data = {}
    for doc in docs:
        stocks_data[doc.id] = doc.to_dict().get("recent_days", [])
    return stocks_data

def get_gainers_losers(stocks_data):
    gainers = []
    losers = []
    for symbol, days in stocks_data.items():
        if len(days) >= 2:
            prev_close = days[-2]['Close']
            last_close = days[-1]['Close']
            change_pct = ((last_close - prev_close) / prev_close) * 100 if prev_close else 0
            entry = {
                "symbol": symbol,
                "last_close": last_close,
                "change_pct": change_pct
            }
            if change_pct > 0:
                gainers.append(entry)
            elif change_pct < 0:
                losers.append(entry)
    gainers = sorted(gainers, key=lambda x: x['change_pct'], reverse=True)
    losers = sorted(losers, key=lambda x: x['change_pct'])
    return gainers, losers

# --- Firebase Cloud Function Scheduler Example ---
from firebase_functions import scheduler_fn

@scheduler_fn.on_schedule(schedule="every 5 minutes")
def scheduled_stock_update(event):
    symbols = load_symbols_from_file("./psx_symbols.txt")
    for symbol in symbols:
        update_stock_recent_days(symbol)
    return "Stock data updated for all symbols."