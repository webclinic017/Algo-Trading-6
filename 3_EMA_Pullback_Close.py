from modules.oanda_api import limit_order, get_candlestick_data, get_balance, get_account
from talib import ATR
import time
import numpy as np

class Strategy:
    def __init__(self,candle_span='M5'):
        self.instruments = [
            'USD_CAD','EUR_USD','USD_CHF','GBP_USD','NZD_USD',
            'AUD_USD','EUR_CAD','EUR_AUD','EUR_CHF','EUR_GBP',
            'AUD_CAD','GBP_CHF','AUD_NZD'
        ]
        self.candle_span = candle_span
        self.update_data()
        
    def update_data(self):
        d = {}
        for ins in self.instruments:
            data = get_candlestick_data(ins,1000,self.candle_span)
            #Add indicators to data here
            data['EMA 50'] = data['Close'].ewm(50).mean()
            data['EMA 100'] = data['Close'].ewm(100).mean()
            data['EMA 150'] = data['Close'].ewm(150).mean()
            #data['ATR'] = ATR(data['High'],data['Low'],data['Close'])
            d[ins] = data
        self.data = d

    def live(self):
        try:
            print('Starting Algorithm')
            while True:
                self.update_data()
                if get_account()['openPositionCount'] == 0 and len(get_account()['orders']) == 0:
                    print('Looking for position')
                    for ins in self.instruments:
                        df = self.data[ins]
                        #Latest candle data
                        c = df['Close'][-1]
                        #Rest of latest data
                        short_ema = df['EMA 50'][-1]
                        med_ema = df['EMA 100'][-1]
                        long_ema = df['EMA 150'][-1]

                        #Long signals
                        emas_in_order = short_ema > med_ema and med_ema > long_ema
                        pullback_short = False
                        pullback_med = False
                        pullback_long = False
                        if emas_in_order:
                            recent = df.iloc[-16:]
                            above_emas = False
                            for i in range(len(recent)):
                                if recent['Low'][i] > recent['EMA 50'][i]:
                                    above_emas = True
                                if above_emas and recent['Close'][i] < recent['EMA 50'][i]:
                                    pullback_short = True
                                if above_emas and recent['Low'][i] < recent['EMA 100'][i]:
                                    pullback_med = True
                                if recent['Low'][i] < recent['EMA 150'][i]:
                                    pullback_long = True

                        if (pullback_short or pullback_med) and not pullback_long and emas_in_order and c > short_ema and len(get_account()['orders']) == 0:
                            stop_loss1 = min([df['Low'][-i] for i in range(16)])
                            stop_loss2 = c
                            take_profit1 = c + (c - stop_loss1)
                            take_profit2 = c + (2 * (c - stop_loss1))
                            qty = int((0.02*get_balance())//(take_profit2 - c))
                            limit_order(ins,c,qty,stop_loss1,take_profit2)
                            #TODO: At 1:1 Risk:Reward, move stop to c, and sell half
                
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