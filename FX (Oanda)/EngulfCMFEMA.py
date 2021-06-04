from modules.oanda_api import get_candlestick_data, market_order, get_account, get_balance
from modules.indicators import EMA, Engulfing, CMF, ATR
import time
import datetime as dt

get_account()

class Strategy():
    def __init__(self):
        self.instruments = ['EUR_USD','USD_JPY','GBP_USD','USD_CAD',
                            'AUD_USD','NZD_USD','USD_CHF','EUR_JPY',
                            'EUR_GBP','EUR_CHF','EUR_SEK','EUR_NOK',
                            'GBP_JPY']
        self.data = self.update_data()

    def run(self):
        print('Starting algorithm')
        while True:
            self.update_data() #Get most current data
            if get_account()['openPositionCount'] == 0:
                print(f'Looking for position | {dt.datetime.now().strftime("%H:%M:%S")}')
                
                for instrument in self.instruments:
                    df = self.data[instrument]
                    #Data most recent period necessary for signals
                    cmf = df['CMF'][-1]
                    ema = df['EMA 200'][-1]
                    close  = df['Close'][-1]
                    low = df['Low'][-1]
                    high = df['High'][-1]
                    engulf = df['Engulfing'][-1]
                    atr = df['ATR'][-1]

                    if cmf > 0 and close > ema and engulf > 0 and get_account()['openPositionCount'] == 0:
                        gap = max(close-low, 4*atr)
                        qty = int(0.01*get_balance()//gap)
                        market_order(instrument, qty, close - gap, close + 2*gap) #Risk 1% 1:2 risk/reward
                    elif cmf < 0 and close < ema and engulf < 0 and get_account()['openPositionCount'] == 0:
                        gap = max(high-close, 4*atr)
                        qty = int(-0.01*get_balance()//gap) #Risk 2% 1:2 risk/reward
                        market_order(instrument, qty, close + gap, close - 2*gap)

            print('sleeping for 1 min')
            time.sleep(56)
        else:
            print('Position waiting for stop_loss or take_profit')
            time.sleep(60)

    def update_data(self):
        """Updates data to most recent candles with indicators"""
        d = {}
        for pair in self.instruments:
            temp = get_candlestick_data(instrument=pair, periods=250, granularity='M1')
            #Add indicators to the data
            CMF(temp)
            EMA(temp, 200)
            Engulfing(temp)
            ATR(temp)
            d[pair] = temp
        return d

s = Strategy()
s.run()
