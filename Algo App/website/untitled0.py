#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun 29 22:19:36 2021

@author: vaughncampos
"""
from modules.oanda_api import get_candlestick_data
from talib import ATR
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

def halfTrend(df, amplitude=2, channelDeviation=2):
    #Columns to update
    trend = np.zeros(len(df))
    nextTrend = np.zeros(len(df))
    maxLowPrice = df['Low']
    minHighPrice = df['High']
    
    up = np.zeros(len(df))
    down = np.zeros(len(df))
    atrHigh = np.zeros(len(df))
    atrLow = np.zeros(len(df))
    arrowUp = [np.nan]*len(df)
    arrowDown = [np.nan]*len(df)

    atr2 = ATR(df['High'],df['Low'],df['Close'],timeperiod=100) / 2
    dev = channelDeviation * atr2

    df['highPrice'] = df['High'].rolling(amplitude).max()
    df['lowPrice'] = df['Low'].rolling(amplitude).min()
    df['highma'] = df['High'].rolling(amplitude).mean()
    df['lowma'] = df['Low'].rolling(amplitude).mean()
    
    for i in range(1,len(df)):
        if nextTrend[i-1] == 1:
            maxLowPrice[i] = max(df['lowPrice'][i],maxLowPrice[i])
            
            if df['highma'][i] < maxLowPrice[i] and df['Close'][i] < df['Low'][i-1]:
                trend[i] = 1
                nextTrend[i] = 0
                minHighPrice[i] = df['highPrice'][i]    
        else:
            minHighPrice[i] = min(df['highPrice'][i],minHighPrice[i])
            
            if df['lowma'][i] > minHighPrice[i] and df['Close'][i] > df['High'][i-1]:
                trend[i] = 0
                nextTrend[i] = 1
                maxLowPrice[i] = df['lowPrice'][i]
        
        if trend[i-1] == 0:
        	if trend[i-1] and trend[i-1] != 0:
        		up[i] = down[i-1]
        		arrowUp[i] = up[i] - atr2[i]
        	else:
        		up[i] = max(maxLowPrice[i], up[i-1])
        	atrHigh[i] = up[i] + dev[i]
        	atrLow[i] = up[i] - dev[i]
        else:
        	if trend[i-1] and trend[i-1] != 1:
        		down[i] = up[i-1]
        		arrowDown[i] = down[i] + atr2[i]
        	else:
        		down[i] = min(minHighPrice[i], down[i-1])
        	atrHigh[i] = down[i] + dev[i]
        	atrLow[i] = down[i] - dev[i]
    print(nextTrend)

    ht = np.where(trend == 0, up, down)
    ht = np.where(ht == 0,np.nan,ht)

    atrHigh = np.where(atrHigh == 0, np.nan, atrHigh)
    atrLow = np.where(atrLow == 0, np.nan, atrLow)

    plt.plot(df['Close'])
    plt.plot(df.index,ht)
    plt.plot(df.index,atrHigh,label='atrHigh')
    plt.plot(df.index,atrLow,label='atrLow')
    plt.plot(df.index,arrowUp,color='g',marker='^')
    plt.plot(df.index,arrowDown,color='r',marker='v')
    plt.legend()
    plt.show()
    
instrument = "EUR_USD"
data = get_candlestick_data(instrument, 1000, "M5")
halfTrend(data)

            
        