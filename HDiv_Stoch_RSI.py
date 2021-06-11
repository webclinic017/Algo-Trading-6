import requests
import json
from modules.oanda_api import get_candlestick_data
from modules.indicators import RSI_Divergence, EMA
from talib import RSI, STOCH, ATR
import matplotlib.pyplot as plt
import numpy as np

#Get data and add necessary indicators
data = get_candlestick_data("EUR_USD",5000,'M1')
data['ATR'] = ATR(data['High'],data['Low'],data['Close'])
data['RSI'] = RSI(data['Close'])
data['stoch'], data['stoch_ma'] = STOCH(data['High'],data['Low'],data['Close'])
RSI_Divergence(data)
EMA(data,50)
EMA(data,200)
data.index = range(len(data))
print(data)

#Plot data 
plt.subplot(2,1,1)
plt.plot(data['Close'])
plt.plot(data['bullish_hidden_divergence'], color='g')
plt.plot(data['bearish_hidden_divergence'], color='r')
plt.plot(data['EMA 50'])
plt.plot(data['EMA 200'])

plt.subplot(2,1,2)
plt.plot(data['RSI'])
plt.plot(data['bullish_hidden_divergence_rsi'],color='g')
plt.plot(data['bearish_hidden_divergence_rsi'],color='r')
plt.show()

#Backtest strategy with data
def backtest(df):
    pos = None
    wins,losses = 0,0
    for i,row in df.iterrows():
        if i > 10:
            o,h,l,c = row['Open'],row['High'],row['Low'],row['Close']
            ema50 = row['EMA 50']
            ema200 = row['EMA 200']
            prev_stoch = df['stoch'][i-1]
            prev_stoch_ma = df['stoch_ma'][i-1]
            stoch = df['stoch'][i]
            stoch_ma = df['stoch_ma'][i]
            atr = row['ATR']

            #long 
            bull_trend = ema50 > ema200
            bull_h_div = False in [np.isnan(df['bullish_hidden_divergence'].iloc[-i]) for i in range(3,10)]
            bull_stoch_cross = prev_stoch <= prev_stoch_ma and stoch > stoch_ma
            above_emas = c > ema50 and c > ema200

            if bull_trend and bull_h_div and bull_stoch_cross and above_emas and not pos:
                stop_loss = c - 2 * atr
                take_profit = c + 4 * atr
                pos = {
                    'stop_loss' : stop_loss,
                    'take_profit' : take_profit
                }

            elif pos:
                if c >= pos['take_profit']:
                    wins += 1
                    pos = None
                elif c <= pos['stop_loss']:
                    losses += 1
                    pos = None
    print(wins, losses)
backtest(data)