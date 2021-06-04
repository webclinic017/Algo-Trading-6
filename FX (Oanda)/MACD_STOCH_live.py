from modules.oanda_api import get_candlestick_data, market_order, get_balance, get_account
from modules.indicators import Stochastic, MACD
import time
import datetime as dt

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
        self.data = self.update_data()
        self.stoch_trend = 0
        self.sold_half = False

    def run(self):
        print('Starting algorithm')
        while True:
            self.update_data() #Get most current data
            positions = get_account()['openPositionCount']
            print(positions)
            if positions == 0:
                print(f'Looking for position | {dt.datetime.now().strftime("%H:%M:%S")}')
                for instrument in self.instruments:
                    df = self.data[instrument]

                    #####################################################################
                    #####################################################################
                    #Strategy
                    c = df['Close'][-1]
                    prev_macd = df['MACD'][-2]
                    prev_signal = df['Signal'][-2]
                    macd = df['MACD'][-1]
                    signal = df['Signal'][-1]
                    stoch = df['stoch'][-1]

                    #Long signals
                    macd_cross_up = macd >= signal and prev_macd <= prev_signal

                    #Short signals
                    macd_cross_down = macd <= signal and prev_macd >= prev_signal

                    #Update self.stoch_trend
                    if stoch > 80:
                        self.stoch_trend = -100
                    elif stoch < 20:
                        self.stoch_trend = 100

                    if (macd_cross_up and self.stoch_trend>0) and positions == 0:
                        positions += 1
                        stop_loss = df['Low'][-5:].min()
                        take_profit = c + (c-stop_loss)
                        qty = 0.95*get_balance()//c
                        market_order(instrument, qty, stop_loss, take_profit) #1.5 profit/loss
                        self.stoch_trend = 0
                    elif (macd_cross_down and self.stoch_trend<0) and positions == 0:
                        positions += 1
                        stop_loss = df['High'][-5:].max()
                        take_profit = c - (stop_loss-c)
                        qty = -0.95*get_balance()//c
                        market_order(instrument, qty, stop_loss, take_profit) #1.5 profit/loss
                        self.stoch_trend = 0
                    else:
                        print(f'No position found for {instrument}')
                    #####################################################################
                    #####################################################################
                print('sleeping for 1 min')
                time.sleep(56)
            else:
                print('Position waiting for stop_loss or take_profit')
                time.sleep(60)

    def update_data(self):
        """Updates data to most recent candles with indicators"""
        d = {}
        for pair in self.instruments:
            temp = get_candlestick_data(instrument=pair, periods=50, granularity='M1')

            ################################################################
            ################################################################
            #Add indicators to the data
            MACD(temp)
            Stochastic(temp)
            ################################################################
            ################################################################

            d[pair] = temp
        return d

s = Strategy()
s.run()
