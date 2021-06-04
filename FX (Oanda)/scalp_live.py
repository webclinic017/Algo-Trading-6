from modules.oanda_api import get_candlestick_data, market_order, get_balance, get_account
from modules.indicators import EMA, fractals
import time
import datetime as dt
import numpy as np

class Strategy():
    def __init__(self):
        self.instruments = ['EUR_USD',
                            'USD_JPY',
                            'GBP_USD',
                            'USD_CAD',
                            'AUD_USD',
                            'NZD_USD',
                            'USD_CHF',
                            'EUR_JPY',
                            'EUR_GBP',
                            'EUR_CHF',
                            'EUR_SEK',
                            'EUR_NOK',
                            'GBP_JPY']
        self.update_data()

    def run(self):
        print('Starting algorithm')
        while True:
            self.update_data() #Get most current data
            positions = get_account()['openPositionCount']
            if positions == 0:
                print(f'Looking for position | {dt.datetime.now().strftime("%H:%M:%S")}')
                for instrument in self.instruments:
                    df = self.data[instrument]
                    print(df.index[-1])
                    #Data necessary for signals
                    c = df['Close'][-1]
                    ema20 = df['EMA 20'][-1]
                    ema50 = df['EMA 50'][-1]
                    ema100 = df['EMA 100'][-1]
                    bull_fractal = not np.isnan(df['bull_fractals'][-3])

                    pullback20 = False
                    pullback50 = False
                    for i in range(10):
                        if df['Close'][-10+i-1] >= df['EMA 20'][-10+i-1] and df['Close'][-10+i] <= df['EMA 20'][-10+i]:
                            pullback20 = True
                        if df['Close'][-10+i-1] >= df['EMA 50'][-10+i-1] and df['Close'][-10+i] <= df['EMA 50'][-10+i]:
                            pullback50 = True


                    if (pullback20 or pullback50) and ema20>ema50 and ema50>ema100 and bull_fractal  and c > ema100 and get_account()['openPositionCount'] == 0:
                        stop_loss = ema100 if pullback50 else ema50
                        take_profit = c + 1.5*(c - stop_loss)
                        qty = 0.05*get_balance()//c
                        market_order(instrument, int(qty), round(stop_loss,5), round(take_profit,5)) #1.5 profit/loss

            print('sleeping for 30 seconds')
            time.sleep(30)

    def update_data(self):
        """Updates data to most recent candles with indicators"""
        d = {}
        for pair in self.instruments:
            temp = get_candlestick_data(pair,400,'M1')
            #Add indicators to the data
            EMA(temp, 20)
            EMA(temp, 50)
            EMA(temp, 100)
            fractals(temp)
            d[pair] = temp
        self.data = d

s = Strategy()
s.run()
