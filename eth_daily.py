import pandas as pd
import streamlit as st
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import warnings
from datetime import datetime
from datetime import timedelta
import yfinance as yf
import lxml as xml
from money import Money

st.title("Ethereum Daily Analysis")

select_currency = st.sidebar.selectbox('Currency?', ('ETH-GBP','ETH-USD'))
select_period = st.sidebar.selectbox('Select period?', ('10d','5d','1d'))
#select_interval = st.sidebar.selectbox('Select interval?', ('90m','60m','30m','15m','5m','2m','1m'))
select_interval = st.sidebar.selectbox('Interval?', ('90m','60m','30m','15m','5m'))
select_window = st.sidebar.slider('Bollinger window', min_value=10, max_value=50, value=20, step=5)
select_short = st.sidebar.slider('Short MA', min_value=1, max_value=20, value=10, step=1)
select_long = st.sidebar.slider('Long MA', min_value=1, max_value=100, value=40, step=1)
select_vol_short = st.sidebar.slider('Volume short window', min_value=1, max_value=20, value=10, step=1)
select_vol_long = st.sidebar.slider('Volume long window', min_value=1, max_value=100, value=40, step=1)
select_signals = st.sidebar.checkbox('Show signals?')
select_close = st.sidebar.checkbox('Show closing tracker?')
select_bollinger = st.sidebar.checkbox('Show Bollinger bands?')
select_sma = st.sidebar.checkbox('Show Exponential Moving Averages?')


btc_df = yf.download(tickers=select_currency, period=select_period, interval=select_interval)

btc_df = btc_df.reset_index()
for i in ['Open', 'High', 'Close', 'Low']: 
      btc_df[i]  =  btc_df[i].astype('float64')

#SET TRADING SIGNAL 1 - BOLLINGER BANDS
btc_df['bollinger_mid_band'] = btc_df['Close'].rolling(window=select_window).mean()
btc_df['bollinger_std'] = btc_df['Close'].rolling(window=select_window).std()
btc_df['bollinger_upper_band']  = btc_df['bollinger_mid_band'] + (btc_df['bollinger_std'] * 1)
btc_df['bollinger_lower_band']  = btc_df['bollinger_mid_band'] - (btc_df['bollinger_std'] * 1)
btc_df['bollinger_long'] = np.where(btc_df['Close'] < btc_df['bollinger_lower_band'], 1.0, 0.0)
btc_df['bollinger_short'] = np.where(btc_df['Close'] > btc_df['bollinger_upper_band'], -1.0, 0.0)
btc_df['bollinger_signal'] = np.where(btc_df['bollinger_long'] + btc_df['bollinger_short'] > 0, btc_df['Close'], None)

#SET TRADING SIGNAL 2 - EMA
# Set short and long windows
short_window = select_short
long_window = select_long
# Construct a `Fast` and `Slow` Exponential Moving Average from short and long windows, respectively
btc_df['fast_close'] = btc_df['Close'].ewm(halflife=select_short).mean()
btc_df['slow_close'] = btc_df['Close'].ewm(halflife=select_long).mean()
#btc_df['ema_signal'] = np.where(btc_df['fast_close'] == btc_df['slow_close'], btc_df['Close'], None)

# Construct a crossover trading signal
btc_df['crossover_long'] = np.where(btc_df['fast_close'] > btc_df['slow_close'], 1.0, 0.0)
btc_df['crossover_short'] = np.where(btc_df['fast_close'] < btc_df['slow_close'], -1.0, 0.0)
btc_df['crossover_signal'] = btc_df['crossover_long'] + btc_df['crossover_short']

#SET TRADING SIGNAL 3 - EMA
# Construct a `Fast` and `Slow` Exponential Moving Average from short and long windows, respectively

# Drop NAs and calculate daily percent return
btc_df['daily_return'] = btc_df['Close'].dropna().pct_change()

btc_df['fast_vol'] = btc_df['daily_return'].ewm(halflife=select_vol_short).std()
btc_df['slow_vol'] = btc_df['daily_return'].ewm(halflife=select_vol_long).std()
# Construct a crossover trading signal
btc_df['vol_trend_long'] = np.where(btc_df['fast_vol'] < btc_df['slow_vol'], 1.0, 0.0)
btc_df['vol_trend_short'] = np.where(btc_df['fast_vol'] > btc_df['slow_vol'], -1.0, 0.0) 
btc_df['vol_trend_signal'] = btc_df['vol_trend_long'] + btc_df['vol_trend_short']


mc = yf.Ticker(select_currency)
cur = select_currency
cur = cur[-3:]
st.write("Market capitalisation: " + str(Money(mc.info["marketCap"], cur)))
st.write("Bollinger band window:" + str(select_window))
st.write("Short Moving Average:" + str(select_short))
st.write("Long Moving Average:" + str(select_long))


fig = go.Figure(data=[go.Candlestick(x=btc_df['Datetime'],
            open=btc_df['Open'],
            high=btc_df['High'],
            low=btc_df['Low'],
            close=btc_df['Close'])
#              go.Scatter(x=btc_df.Datetime, y=btc_df.bollinger_mid_band, line=dict(color='orange', width=1), name='Mid'),
#              go.Scatter(x=btc_df.Datetime, y=btc_df.bollinger_upper_band, line=dict(color='red', width=1), name='Upper'),
#              go.Scatter(x=btc_df.Datetime, y=btc_df.bollinger_lower_band, line=dict(color='blue', width=1), name='Lower')
                     ])

if select_bollinger:
      fig.add_trace(go.Scatter(x=btc_df.Datetime, y=btc_df.bollinger_mid_band, line=dict(color='orange', width=1), name='Mid'))
      fig.add_trace(go.Scatter(x=btc_df.Datetime, y=btc_df.bollinger_upper_band, line=dict(color='red', width=1), name='Upper'))
      fig.add_trace(go.Scatter(x=btc_df.Datetime, y=btc_df.bollinger_lower_band, line=dict(color='blue', width=1), name='Lower'))

if select_sma:
      fig.add_trace(go.Scatter(x=btc_df.Datetime, y=btc_df.fast_close,
                  mode='lines',
                  name='Short = ' + str(select_short)))
      fig.add_trace(go.Scatter(x=btc_df.Datetime, y=btc_df.slow_close,
                  mode='lines',
                  name='Long = ' + str(select_long)))
#      if btc_df['ema_signal'] is not None:
#            fig.add_trace(go.Scatter(x=btc_df.Datetime, y=btc_df['Close'],
#                  mode='markers',
#                  name='Signal'))
      

if select_signals:
      fig.add_trace(go.Scatter(x=btc_df.Datetime, y=btc_df.bollinger_signal, mode='markers', line=dict(color='black', width=1), name='Signal'))

if select_close:
      fig.add_trace(go.Scatter(x=btc_df.Datetime, y=btc_df.Close, line=dict(color='grey', width=1), name='Close'))
                    
fig

            
fig = px.bar(btc_df, x="Datetime", y="Volume")

fig

btc_df
