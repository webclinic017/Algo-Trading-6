import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from modules.oanda_api import get_candlestick_data
from modules.indicators import ATR, MACD, EMA

def backtest(df):
    pos = None
    cash = 100000

    profit_loss = 1.5

    wins = 0
    losses = 0

    buy = [np.nan]*len(df)
    sell = [np.nan]*len(df)

    profit = 0
    for i in range(len(df)):
        atr = df['ATR'][i]
        macd = df['MACD'][i]
        prev_macd = df['MACD'][i-1]
        sig = df['Signal'][i]
        prev_sig = df['Signal'][i-1]
        ema = df['EMA 200'][i]

        o = df['Open'][i]
        h = df['High'][i]
        l = df['Low'][i]
        c = df['Close'][i]

        above_ema = [df['Close'][t] > df['EMA 200'][t] for t in range(i-7,i+1)]

        if not pos: #Look for position
            #Long
            if not False in above_ema and macd < 0 and macd >= sig and prev_macd <= prev_sig:
                pos = {
                    'type' : 'long',
                    'buy_price' : c,
                    'stop_loss' : min(l, c-3*atr),
                    'take_profit' : c + profit_loss*(c - min(l, c-3*atr)),
                    'qty' : (0.01*cash)// (c - min(l, c-3*atr))
                }
                print(f'Long buy price: ${pos["buy_price"]}')
                buy[i] = c
            #Short
            if not True in above_ema and macd > 0 and macd <= sig and prev_macd >= prev_sig:
                pos = {
                    'type' : 'short',
                    'sell_price' : c,
                    'stop_loss' : max(h, c+3*atr),
                    'take_profit' : c - profit_loss*(max(h, c+3*atr)-c),
                    'qty' : (0.01*cash)// (max(h, c+3*atr)-c)
                }
                print(f'Short sell price: ${pos["sell_price"]}')
                sell[i] = c
        else: #Look to close position
            if pos['type'] == 'long':
                if c >= pos['take_profit'] or c <= pos['stop_loss'] or i == len(df)-1:
                    prof = pos["qty"]*(c-pos["buy_price"])
                    print(f'Closed long position at ${c} for profit of ${prof}')
                    profit += prof
                    if prof <= 0: 
                        losses += 1
                    else:
                        wins += 1
                    pos = None
                    sell[i] = c
            elif pos['type'] == 'short':
                if c <= pos['take_profit'] or c >= pos['stop_loss'] or i == len(df)-1:
                    prof = pos["qty"]*(pos["sell_price"]-c)
                    print(f'Closed short position at ${c} for profit of ${prof}')
                    profit += prof
                    if prof <= 0: 
                        losses += 1
                    else:
                        wins += 1
                    pos = None
                    buy[i] = c
    
    print(f'\nTotal profit: ${profit}')
    print(f'Winners: {wins}')
    print(f'Losers: {losses}')
    print(f'Time span: {df.index[-1] - df.index[0]}')

    fig, (ax1, ax2) = plt.subplots(2,1,sharex=True)
    ax1.plot(data['Close'],alpha=0.6,color='grey')
    ax1.plot(data['EMA 200'], alpha=0.6, color='yellow')
    ax1.scatter(data.index, buy,marker='^',color='green')
    ax1.scatter(data.index, sell,marker='v',color='red')
    
    ax2.plot(data['MACD'])
    ax2.plot(data['Signal'])
    
    plt.show()

data = get_candlestick_data("EUR_USD", granularity="M5", periods=5000)
data = data.dropna()
MACD(data)
ATR(data)
EMA(data, 200)
backtest(data)