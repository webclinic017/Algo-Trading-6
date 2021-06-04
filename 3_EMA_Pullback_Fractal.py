from numpy.core.fromnumeric import take
from requests.api import get
from modules.oanda_api import market_order, limit_order, get_candlestick_data, get_balance, get_account
from talib import ATR
from modules.indicators import fractals
import time
import numpy as np

class Strategy:
    def __init__(self,candle_span='M5'):
        self.instruments = [
            'USD_CAD','EUR_USD','USD_CHF','GBP_USD','NZD_USD',
            'AUD_USD','USD_JPY','EUR_CAD','EUR_AUD','EUR_JPY',
            'EUR_CHF','EUR_GBP','AUD_CAD','GBP_CHF','GBP_JPY',
            'CHF_JPY','AUD_JPY','AUD_NZD'
        ]
        self.candle_span = candle_span
        self.update_data()
        

    def update_data(self):
        d = {}
        for ins in self.instruments:
            data = get_candlestick_data(ins,1000,self.candle_span)
            #Add indicators to data here
            data['EMA 20'] = data['Close'].ewm(8).mean()
            data['EMA 50'] = data['Close'].ewm(14).mean()
            data['EMA 100'] = data['Close'].ewm(50).mean()
            fractals(data)
            data['ATR'] = ATR(data['High'],data['Low'],data['Close'])
            d[ins] = data
        self.data = d

    def live(self):
        try:
            print('Starting Algorithm')
            while True:
                self.update_data()
                if get_account()['openPositionCount'] == 0 and len(get_account()['orders']) == 0:
                    #Look for position
                    print('Looking for position')
                    for ins in self.instruments:
                        df = self.data[ins]
                        #Latest candle data
                        row = df.iloc[-1]
                        o,h,l,c = row['Open'],row['High'],row['Low'],row['Close']
                        #Rest of latest data
                        atr = row['ATR']
                        ema20 = row['EMA 20']
                        ema50 = row['EMA 50']
                        ema100 = row['EMA 100']
                        bull_fractal = df['bull_fractals'][-3]
                        bear_fractal = df['bear_fractals'][-3]

                        #Long signals
                        emas_in_order = ema20 > ema50 and ema50 > ema100
                        bull_pullback_20 = False
                        bull_pullback_50 = False
                        below100 = False
                        if emas_in_order:
                            recent = df.iloc[-16:]
                            aboveemas = False
                            for i in range(len(recent)):
                                if recent['Low'][i] > recent['EMA 20'][i]:
                                    aboveemas = True
                                if aboveemas and recent['Low'][i] < recent['EMA 20'][i]:
                                    bull_pullback_20 = True
                                if aboveemas and recent['Low'][i] < recent['EMA 50'][i]:
                                    bull_pullback_50 = True
                                if recent['Low'][i] < recent['EMA 100'][i]:
                                    below100 = True

                        if (bull_pullback_20 or bull_pullback_50) and not below100 and emas_in_order and not np.isnan(bull_fractal) and len(get_account()['orders']) == 0:
                            stop_loss = round(c - 3*atr,4) #TODO
                            take_profit = round(c + 2*atr,4) #TODO
                            max_qty = 2_000_000//c
                            qty = min(int((0.02*get_balance())//(take_profit - c)),max_qty)
                            limit_order(ins,c,qty,stop_loss,take_profit)

                        #Long signals
                        emas_in_order = ema20 < ema50 and ema50 < ema100
                        bear_pullback_20 = False
                        bear_pullback_50 = False
                        above100 = False
                        if emas_in_order:
                            recent = df.iloc[-16:]
                            belowemas = False
                            for i in range(len(recent)):
                                if recent['High'][i] < recent['EMA 20'][i]:
                                    belowemas = True
                                if belowemas and recent['High'][i] > recent['EMA 20'][i]:
                                    bear_pullback_20 = True
                                if belowemas and recent['High'][i] > recent['EMA 50'][i]:
                                    bear_pullback_50 = True
                                if recent['High'][i] > recent['EMA 100'][i]:
                                    above100 = True

                        if (bear_pullback_20 or bear_pullback_50) and not above100 and emas_in_order and not np.isnan(bear_fractal) and len(get_account()['orders']) == 0:
                            stop_loss = round(c + 3*atr,4) #TODO
                            take_profit = round(c - 2*atr,4) #TODO
                            max_qty = 2_000_000//c
                            qty = min(int((0.02*get_balance())//(take_profit - c)),max_qty)
                            limit_order(ins,c,qty,stop_loss,take_profit)
                
                print(f'{time.asctime()}')
                time.sleep(2.5*60)

        except Exception as e:
            print(e)
            response = input('\nAn error occured, restart? (y/n): ')
            if response == 'y':
                self.live()

if __name__ == "__main__":
    strat = Strategy()
    strat.live()