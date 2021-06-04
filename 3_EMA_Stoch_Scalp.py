from numpy.core.fromnumeric import take
from requests.api import get
from modules.oanda_api import market_order, limit_order, get_candlestick_data, get_balance, get_account
from talib import STOCHRSI, ATR
import time

class Strategy:
    """
    Indicators: 8, 14, 50 EMA, Stochastic
    """
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
            data['EMA 8'] = data['Close'].ewm(8).mean()
            data['EMA 14'] = data['Close'].ewm(14).mean()
            data['EMA 50'] = data['Close'].ewm(50).mean()
            data['Stoch'],data['Stoch_ma'] = STOCHRSI(data['Close'])
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
                        ema8 = row['EMA 8']
                        ema14 = row['EMA 14']
                        ema50 = row['EMA 50']
                        prev_stoch = df['Stoch'][-2]
                        prev_stoch_ma = df['Stoch_ma'][-2]
                        cur_stoch = df['Stoch'][-1]
                        cur_stoch_ma = df['Stoch_ma'][-1]

                        #Long signals
                        bull_cross = prev_stoch <= prev_stoch_ma and cur_stoch >= cur_stoch_ma and prev_stoch < 50
                        emas_in_order = ema8 > ema14 and ema14 > ema50

                        if bull_cross and emas_in_order and c > ema8 and len(get_account()['orders']) == 0:
                            stop_loss = round(c - 3*atr,4)
                            take_profit = round(c + 2*atr,4)
                            max_qty = 2_000_000//c
                            qty = min(int((0.02*get_balance())//(take_profit - c)),max_qty)
                            limit_order(ins,c,qty,stop_loss,take_profit)

                        #Short signals
                        bear_cross = prev_stoch >= prev_stoch_ma and cur_stoch <= cur_stoch_ma and prev_stoch > 50
                        emas_in_order = ema8 < ema14 and ema14 < ema50

                        if bear_cross and emas_in_order and c < ema8 and len(get_account()['orders']) == 0:
                            stop_loss = round(c + 3*atr,4)
                            take_profit = round(c - 2*atr,4)
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