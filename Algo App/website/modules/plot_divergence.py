import pandas as pd
from talib import RSI, STOCH, ATR
import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import argrelmin,argrelmax
import yfinance as yf
import requests
import json
import datetime as dt

def RSI_Divergence(data, span = 4):
    """
    Bullish Divergence : price makes lower lows, indicator makes higher lows
    Bullish Hidden Divergence : price makes higher low, indicator makes lower low
    Bearish Divergence : Price makes higher high, indicator makes lower high
    Bearish Hidden Divergence : Price makes lower high, indicator makes higher high
    """
    #Get relative minimums of Close price
    rel_min1, = argrelmin(np.array(data['Close'].tolist()),order=span)
    data['swing_low'] = [data['Low'][i] if i in rel_min1 else np.nan for i in range(len(data))]

    #Get relative maximumns of Close price
    rel_max1, = argrelmax(np.array(data['Close'].tolist()),order=span)
    data['swing_high'] = [data['High'][i] if i in rel_max1 else np.nan for i in range(len(data))]

    #Get relative minimums of RSI
    rel_min2, = argrelmin(np.array(data['RSI'].tolist()),order=span)
    data['swing_low_rsi'] = [data['RSI'][i] if i in rel_min2 else np.nan for i in range(len(data))]

    #Get relative maxiumums of RSI
    rel_max2, = argrelmax(np.array(data['RSI'].tolist()),order=span)
    data['swing_high_rsi'] = [data['RSI'][i] if i in rel_max2 else np.nan for i in range(len(data))]

    #Get intersection of mins and maxes for RSI and Close price
    lows = np.intersect1d(rel_min1,rel_min2)
    highs = np.intersect1d(rel_max1,rel_max2)

    #Tuple list (index1, index2)
    bull_div, bull_h_div = [], []
    bear_div, bear_h_div = [], []
    #Compare adjacent highs
    for i in range(1,len(highs)):
        prev_rsi = data['RSI'][highs[i-1]]
        cur_rsi = data['RSI'][highs[i]]
        prev_high = data['High'][highs[i-1]]
        cur_high = data['High'][highs[i]]

        if cur_high > prev_high and cur_rsi < prev_rsi: #Bearish divergence
            bear_div.append((highs[i-1],highs[i]))
        elif cur_high < prev_high and cur_rsi > prev_rsi: #Bearish Hidden Divergence
            bear_h_div.append((highs[i-1],highs[i]))
    #Compare adjacent lows
    for i in range(1,len(lows)):
        prev_rsi = data['RSI'][lows[i-1]]
        cur_rsi = data['RSI'][lows[i]]
        prev_low = data['Low'][lows[i-1]]
        cur_low = data['Low'][lows[i]]

        if cur_low < prev_low and cur_rsi > prev_rsi: #Bullish divergence
            bull_div.append((lows[i-1],lows[i]))
        elif cur_low > prev_low and cur_rsi < prev_rsi: #Bullish hidden divergence
            bull_h_div.append((lows[i-1],lows[i]))
    
    #Add columns to dataframe for plotting
    col_list1 = ['bullish_divergence','bearish_divergence','bullish_hidden_divergence','bearish_hidden_divergence']
    col_list2 = ['bullish_divergence_rsi','bearish_divergence_rsi','bullish_hidden_divergence_rsi','bearish_hidden_divergence_rsi']
    for t1,t2 in zip([bull_div,bear_div,bull_h_div,bear_h_div],col_list1):
        temp = [np.nan]*len(data)
        for pair in t1:
            c = data['Close'][pair[0]]
            c2 = data['Close'][pair[1]]
            slope = (c2 - c)/(pair[1]-pair[0])
            for i in range(pair[0],pair[1]+1):
                temp[i] = c + slope*(i-pair[0])
        data[t2] = temp

    for t1,t2 in zip([bull_div,bear_div,bull_h_div,bear_h_div],col_list2):
        temp = [np.nan]*len(data)
        for pair in t1:
            c = data['RSI'][pair[0]]
            c2 = data['RSI'][pair[1]]
            slope = (c2 - c)/(pair[1]-pair[0])
            for i in range(pair[0],pair[1]+1):
                temp[i] = c + slope*(i-pair[0])
        data[t2] = temp


def get_fx_data(instrument,periods,granularity):
    """Returns pandas dataframe of ohlc and volume data"""
    rest_url = "https://api-fxpractice.oanda.com/"
    stream_url = "https://stream-fxpractice.oanda.com/"
    access_token = "7504cc953a3efe6542a1b0181f7a69b0-f5e662a814de4b0d43ea9c206a8e44ce"
    account_id = "101-001-17749174-001"
    authorization_header = {'Authorization':f'Bearer {access_token}','Accept-Datetime-Format':'UNIX', 'Content-type':'application/json'}
    end_point = f"v3/instruments/{instrument}/candles?granularity={granularity}&count={periods}"
    r = requests.get(rest_url+end_point, headers=authorization_header)
    if "errorMessage" in json.loads(r.text).keys():
        print('Error retrieving data')
    else:
        dic = json.loads(r.content)
        candles = dic['candles']
        df = pd.DataFrame()
        df['Open'] = [float(candle['mid']['o']) for candle in candles]
        df['High'] = [float(candle['mid']['h']) for candle in candles]
        df['Low'] = [float(candle['mid']['l']) for candle in candles]
        df['Close'] = [float(candle['mid']['c']) for candle in candles]
        df['Volume'] = [float(candle['volume']) for candle in candles]
        df.index = [dt.datetime.fromtimestamp(float(candle['time'])) for candle in candles]
        return df


#data = yf.download('GOLD','2019-01-01','2021-06-01')
data = get_fx_data('EUR_USD',1000,'M1')
data['RSI'] = RSI(data['Close'])
data['stochf'],data['stochs'] = STOCH(data['High'],data['Low'],data['Close'])
data['EMA 50'] = data['Close'].ewm(50,min_periods=50).mean()
data['EMA 200'] = data['Close'].ewm(200,min_periods=200).mean()
data['ATR'] = ATR(data['High'],data['Low'],data['Close'])
data.dropna(inplace=True)

RSI_Divergence(data)

plt.figure(figsize=(18,9))
plt.subplot(3,1,1)
plt.plot(data['Close'],label='Close Price',alpha=0.5)
plt.plot(data["EMA 50"],label='EMA 50',alpha=0.5)
plt.plot(data["EMA 200"],label='EMA 200',alpha=0.5)
plt.plot(data['swing_low'],marker='^',color='g')
plt.plot(data['swing_high'],marker='v',color='r')
plt.plot(data['bullish_divergence'],label='Bull Divergence')
plt.plot(data['bearish_divergence'],label='Bear Divergence')
#plt.plot(data['bullish_hidden_divergence'],label='Bull Hidden Divergence')
#plt.plot(data['bearish_hidden_divergence'],label='Bear Hidden Divergence')
#plt.legend()

plt.subplot(3,1,2)
plt.plot(data['RSI'],alpha=0.5,label='rsi')
plt.plot(data['swing_low_rsi'],marker='^',color='g')
plt.plot(data['swing_high_rsi'],marker='v',color='r')
plt.plot(data['bullish_divergence_rsi'],label='Bull Divergence')
plt.plot(data['bearish_divergence_rsi'],label='Bear Divergence')
#plt.plot(data['bullish_hidden_divergence_rsi'],label='Bull Hidden Divergence')
#plt.plot(data['bearish_hidden_divergence_rsi'],label='Bear Hidden Divergence')

plt.subplot(3,1,3)
plt.plot(data['stochf'],alpha=0.5)
plt.plot(data['stochs'])
plt.show()