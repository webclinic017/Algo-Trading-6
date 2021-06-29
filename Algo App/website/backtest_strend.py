from modules.oanda_api import get_candlestick_data, limit_order
import datetime as dt
import matplotlib.pyplot as plt
import numpy as np
from talib import STOCHRSI
import pandas as pd
"""
Strategy:
C1: Below/Above 200
C2: Stochastic RSI cross above/below 80/20
C3: At least 2 supertrends agree with direction (at least two above/below price)
Stop Loss: stop loss at second supertrend, target 1:1.5 Risk:Reward
Special case: If Stochastic RSI goes overbought/oversold, and not 2 strends above/below, wait until two strends
go above/below as long as stochastic rsi still above/below 50 line
"""


def get_supertrend(high, low, close, lookback, multiplier):
    # ATR
    tr1 = pd.DataFrame(high - low)
    tr2 = pd.DataFrame(abs(high - close.shift(1)))
    tr3 = pd.DataFrame(abs(low - close.shift(1)))
    frames = [tr1, tr2, tr3]
    tr = pd.concat(frames, axis = 1, join = 'inner').max(axis = 1)
    atr = tr.ewm(lookback).mean()
    # H/L AVG AND BASIC UPPER & LOWER BAND
    hl_avg = (high + low) / 2
    upper_band = (hl_avg + multiplier * atr).dropna()
    lower_band = (hl_avg - multiplier * atr).dropna()
    # FINAL UPPER BAND
    final_bands = pd.DataFrame(columns = ['upper', 'lower'])
    final_bands.iloc[:,0] = [x for x in upper_band - upper_band]
    final_bands.iloc[:,1] = final_bands.iloc[:,0]
    for i in range(len(final_bands)):
        if i == 0:
            final_bands.iloc[i,0] = 0
        else:
            if (upper_band[i] < final_bands.iloc[i-1,0]) | (close[i-1] > final_bands.iloc[i-1,0]):
                final_bands.iloc[i,0] = upper_band[i]
            else:
                final_bands.iloc[i,0] = final_bands.iloc[i-1,0]
    # FINAL LOWER BAND
    for i in range(len(final_bands)):
        if i == 0:
            final_bands.iloc[i, 1] = 0
        else:
            if (lower_band[i] > final_bands.iloc[i-1,1]) | (close[i-1] < final_bands.iloc[i-1,1]):
                final_bands.iloc[i,1] = lower_band[i]
            else:
                final_bands.iloc[i,1] = final_bands.iloc[i-1,1]
    # SUPERTREND
    supertrend = pd.DataFrame(columns = [f'supertrend_{lookback}'])
    supertrend.iloc[:,0] = [x for x in final_bands['upper'] - final_bands['upper']]
    
    for i in range(len(supertrend)):
        if i == 0:
            supertrend.iloc[i, 0] = 0
        elif supertrend.iloc[i-1, 0] == final_bands.iloc[i-1, 0] and close[i] < final_bands.iloc[i, 0]:
            supertrend.iloc[i, 0] = final_bands.iloc[i, 0]
        elif supertrend.iloc[i-1, 0] == final_bands.iloc[i-1, 0] and close[i] > final_bands.iloc[i, 0]:
            supertrend.iloc[i, 0] = final_bands.iloc[i, 1]
        elif supertrend.iloc[i-1, 0] == final_bands.iloc[i-1, 1] and close[i] > final_bands.iloc[i, 1]:
            supertrend.iloc[i, 0] = final_bands.iloc[i, 1]
        elif supertrend.iloc[i-1, 0] == final_bands.iloc[i-1, 1] and close[i] < final_bands.iloc[i, 1]:
            supertrend.iloc[i, 0] = final_bands.iloc[i, 0]
    supertrend = supertrend.set_index(upper_band.index)
    supertrend = supertrend.dropna()[1:]
    # ST UPTREND/DOWNTREND
    upt = []
    dt = []
    close = close.iloc[len(close) - len(supertrend):]
    for i in range(len(supertrend)):
        if close[i] > supertrend.iloc[i, 0]:
            upt.append(supertrend.iloc[i, 0])
            dt.append(np.nan)
        elif close[i] < supertrend.iloc[i, 0]:
            upt.append(np.nan)
            dt.append(supertrend.iloc[i, 0])
        else:
            upt.append(np.nan)
            dt.append(np.nan)    
    st, upt, dt = pd.Series(supertrend.iloc[:, 0]), pd.Series(upt), pd.Series(dt)
    upt.index, dt.index = supertrend.index, supertrend.index
    
    return st, upt, dt

###################################################################################
###################################### tests ######################################
###################################################################################
def backtest(ins,plot=True):
    test = get_candlestick_data(ins,5000,"M5")
    test['EMA 200'] = test['Close'].ewm(200).mean()
    test['Stoch RSI'], test['Stoch RSI MA'] = STOCHRSI(test['Close'])
    test['strend 3'],test['s_up_3'],test['s_down_3'] = get_supertrend(test['High'],test['Low'],test['Close'],12,3)
    test['strend 2'],test['s_up_2'],test['s_down_2'] = get_supertrend(test['High'],test['Low'],test['Close'],11,2)
    test['strend 1'],test['s_up_1'],test['s_down_1'] = get_supertrend(test['High'],test['Low'],test['Close'],10,1)

    #Condition 1 (Above/Below 200 EMA)
    test['Long Condition 1'] = test['Close'] > test['EMA 200']
    test['Short Condition 1'] = test['Close'] < test['EMA 200']

    #Condtion 2 (Stochastic RSI cross aboe threshold)
    test['Long Condition 2'] = (test['Stoch RSI'] < 20) & (test['Stoch RSI'] > test['Stoch RSI MA']) & (test['Stoch RSI'].shift(1) <= test['Stoch RSI MA'].shift(1))
    test['Short Condition 2'] = (test['Stoch RSI'] > 80) & (test['Stoch RSI'] < test['Stoch RSI MA']) & (test['Stoch RSI'].shift(1) >= test['Stoch RSI MA'].shift(1))

    #Condtion 3 (At least two supertrends are above/below price)
    strend1_long = test['strend 1'] > test['Close']
    strend2_long = test['strend 2'] > test['Close']
    strend3_long = test['strend 3'] > test['Close']
    test['Long Condition 3'] = (strend1_long & strend2_long) | (strend2_long & strend3_long) | (strend1_long & strend3_long) | (strend1_long & strend2_long & strend3_long)
    strend1_short = test['strend 1'] < test['Close']
    strend2_short = test['strend 2'] < test['Close']
    strend3_short = test['strend 3'] < test['Close']
    test['Short Condition 3'] = (strend1_short & strend2_short) | (strend2_short & strend3_short) | (strend1_short & strend3_short) | (strend1_short & strend2_short & strend3_short)

    #Buy/Sell signals (All three conditions)
    buy = (test['Long Condition 1'] & test['Long Condition 2'] & test['Long Condition 3'])
    test['Buy'] = buy
    test['Buy Plot'] = np.where(buy == True,test['Close'],np.nan)
    sell = (test['Short Condition 1'] & test['Short Condition 2'] & test['Short Condition 3'])
    test['Sell'] = sell
    test['Sell Plot'] = np.where(sell == True,test['Close'],np.nan)

    #Backtest
    risk_pct = 0.01
    pos = None
    wins,losses = 0,0
    cur_wins, cur_losses = 0,0
    max_wins,max_losses = 0,0
    performance = [0]*len(test)
    for i in range(1,len(test)):
        o = test['Open'][i]
        h = test['High'][i]
        l = test['Low'][i]
        c = test['Close'][i]
        buy = test['Buy'][i]
        sell = test['Sell'][i]
        st1 = test['strend 1'][i]
        st2 = test['strend 2'][i]
        st3 = test['strend 3'][i]

        if not pos:
            if buy:
                stop = min([st1,st2,st3])
                pos = {
                    'Stop Loss' : stop,
                    'Take Profit' : c + 1.5*(c - stop),
                    'Type' : 'long'
                }
            elif sell:
                stop = max([st1,st2,st3])
                pos = {
                    'Stop Loss' : stop,
                    'Take Profit' : c - 1.5*(stop - c),
                    'Type' : 'short'
                }

            performance[i] = performance[i-1] 
        
        elif pos['Type'] == 'long':
            if h >= pos['Take Profit']:
                wins += 1
                cur_wins += 1
                if cur_losses > max_losses:
                    max_losses = cur_losses
                cur_losses = 0
                pos = None
                performance[i] = performance[i-1] + risk_pct*1.5
            elif l <= pos['Stop Loss']:
                losses += 1
                cur_losses += 1
                if cur_wins > max_wins:
                    max_wins = cur_wins
                cur_wins = 0
                pos = None
                performance[i] = performance[i-1] - risk_pct
            else:
                performance[i] = performance[i-1]
            
        elif pos['Type'] == 'short':
            if l <= pos['Take Profit']:
                wins += 1
                cur_wins += 1
                if cur_losses > max_losses:
                    max_losses = cur_losses
                cur_losses = 0
                pos = None
                performance[i] = performance[i-1] + risk_pct*1.5
            elif h >= pos['Stop Loss']:
                losses += 1
                cur_losses += 1
                if cur_wins > max_wins:
                    max_wins = cur_wins
                cur_wins = 0
                pos = None
                performance[i] = performance[i-1] - risk_pct
            else:
                performance[i] = performance[i-1]

    #Display performance
    test['Performance'] = performance
    print(f'\n--------{ins} backtest--------\n')
    print(f'Wins : {wins}')
    print(f'Losses : {losses}')
    print(f'Win % : {0 if wins + losses == 0 else wins/(wins+losses)}')
    print(f'Max Wins : {max_wins}')
    print(f'Max Losses : {max_losses}')

    if plot:
        ax1 = plt.subplot(2,1,1)
        plt.plot(test['Close'])
        plt.plot(test['Buy Plot'],color='g',marker='^')
        plt.plot(test['Sell Plot'],color='r',marker='v')
        plt.subplot(2,1,2,sharex=ax1)
        plt.plot(test['Performance'])
        plt.show()

if __name__ == "__main__":  
    instruments = [
        'USD_CAD','EUR_USD','USD_CHF','GBP_USD','NZD_USD',
        'AUD_USD','EUR_CAD','EUR_AUD','EUR_CHF','EUR_GBP',
        'AUD_CAD','GBP_CHF','AUD_NZD'
    ]
    for ins in instruments:
        backtest(ins,plot=True)