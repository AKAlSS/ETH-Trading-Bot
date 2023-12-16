import pandas as pd
import ta
import cryptocompare
from datetime import datetime

SMA_SHORT = 5
SMA_LONG = 62
RSI_PERIOD = 14
TRANSACTION_FEE = 0.0026
RISK_REWARD_RATIO = 1.5
CRYPTOCOMPARE_API_KEY = '9f99d2443bfb4ee51f98bd1a89cb6c20fc3ca6c01a2aa3d3628b890251fe1c6a'

cryptocompare.cryptocompare._set_api_key_parameter(CRYPTOCOMPARE_API_KEY)

def fetch_price_data(crypto, currency="USD", limit=500):
    data = cryptocompare.get_historical_price_day(crypto, currency, limit=limit, toTs=datetime.now())
    df = pd.DataFrame(data)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df.set_index('time', inplace=True)
    df = df[['open', 'high', 'low', 'close', 'volumefrom']].rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volumefrom': 'Volume'})
    return df

def calculate_indicators(df):
    df['SMA_Short'] = ta.trend.sma_indicator(df['Close'], window=SMA_SHORT)
    df['SMA_Long'] = ta.trend.sma_indicator(df['Close'], window=SMA_LONG)
    df['RSI'] = ta.momentum.rsi(df['Close'], window=RSI_PERIOD)
    df['Buy_Signal'] = (df['SMA_Short'].shift(1) < df['SMA_Long'].shift(1)) & (df['SMA_Short'] > df['SMA_Long'])
    df['Sell_Signal'] = (df['SMA_Short'].shift(1) > df['SMA_Long'].shift(1)) & (df['SMA_Short'] < df['SMA_Long'])
    return df

def backtest_strategy(df):
    holding = False
    buy_price = 0
    sell_price = 0
    trades = 0
    profits = 0

    for i in range(len(df)):
        if df['Buy_Signal'].iloc[i] and not holding:
            buy_price = df['Close'].iloc[i] * (1 + TRANSACTION_FEE)  # adjust for transaction fee
            holding = True
        elif holding and ((df['Sell_Signal'].iloc[i]) or ((df['Close'].iloc[i] / buy_price - 1) >= RISK_REWARD_RATIO)):
            sell_price = df['Close'].iloc[i] * (1 - TRANSACTION_FEE)  # adjust for transaction fee
            trades += 1
            profits += (sell_price - buy_price)
            holding = False

    return trades, profits

def run_trading_strategy():
    # Define the initial capital
    initial_capital = 1000
    capital = initial_capital

    # Create a DataFrame to store the backtest results
    backtest_results = pd.DataFrame(columns=['Ticker', 'Total_Profits'])

    # Define the cryptocurrency to backtest
    ticker = 'ETH'

    # Fetch the price data
    df = fetch_price_data(ticker)
    calculate_indicators(df)

    # Create a DataFrame to store the details of each trade
    trade_log = pd.DataFrame(columns=['Date', 'Action', 'Price', 'Amount', 'Capital'])

    trades = 0
    profits = 0
    position = 0

    for i in range(2, df.shape[0]):
        if df['Buy_Signal'].iloc[i] and capital > 0:
            position = capital / df['Close'].iloc[i] * (1 - TRANSACTION_FEE)  # Buy as much as we can
            capital = 0  # All money is now in the position
            new_row = pd.DataFrame({'Date': df.index[i], 'Action': 'Buy', 'Price': df['Close'].iloc[i], 'Amount': position, 'Capital': capital}, index=[i])
            trade_log = pd.concat([trade_log, new_row])
            trades += 1

        if df['Sell_Signal'].iloc[i] and position > 0:
            capital = position * df['Close'].iloc[i] * (1 - TRANSACTION_FEE)  # Sell the position
            profits += capital - initial_capital
            position = 0  # We're now out of the position
            new_row = pd.DataFrame({'Date': df.index[i], 'Action': 'Sell', 'Price': df['Close'].iloc[i], 'Amount': position, 'Capital': capital}, index=[i])
            trade_log = pd.concat([trade_log, new_row])
            trades += 1

    print("Trades executed:", trades)
    print("Total profits:", profits)
    print(ticker)
    print("\nTrade Log:")
    print(trade_log)

    backtest_results.loc[backtest_results['Ticker'] == ticker, 'Total_Profits'] = profits

    print("Backtest complete.")
    return backtest_results

if __name__ == "__main__":
    run_trading_strategy()