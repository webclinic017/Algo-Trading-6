from modules.oanda_api import limit_order, get_candlestick_data, get_balance, get_account
from talib import STOCHRSI, ATR
import time
import datetime as dt

PARAMS = {
    'bull_stoch_cross' : 40,
    'bear_stoch_cross' : 60,
    'EMA_gap' : 0.0001, # 1 pip
    'risk_pct' : 0.02, # 2%
    'sleep' : 30 # 1 minute
}

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
            print('\nStarting Algorithm...')
            while True:
                if dt.datetime.now().minute % 5 == 0 and dt.datetime.now().second < 10 and get_account()['openPositionCount'] == 0 and len(get_account()['orders']) == 0:
                    self.update_data()
                    print(f'\n---- {time.asctime()}: Looking for Signals ---- \n')
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
                        bull_cross = prev_stoch <= prev_stoch_ma and cur_stoch > cur_stoch_ma and prev_stoch < PARAMS['bull_stoch_cross']
                        emas_in_order = ema8 > ema14 + PARAMS['EMA_gap'] and ema14 > ema50 + PARAMS['EMA_gap']
                        #Short signals
                        bear_cross = prev_stoch >= prev_stoch_ma and cur_stoch < cur_stoch_ma and prev_stoch > PARAMS['bear_stoch_cross']
                        emas_in_order = ema8 + PARAMS['EMA_gap'] < ema14 and ema14 + PARAMS['EMA_gap'] < ema50

                        if bull_cross and emas_in_order and c > ema8 and len(get_account()['orders']) == 0:
                            # stop_loss = round(c - PARAMS['stop_loss_atr_factor']*atr,5)
                            stop_loss = min([df['Low'][-di] for di in range(16)])
                            # take_profit = round(c + PARAMS['take_profit_atr_factor']*atr,5)
                            take_profit = c + (c-stop_loss)
                            qty = int((PARAMS['risk_pct']*get_balance())//(take_profit - c))
                            limit_order(ins,c,qty,stop_loss,take_profit)
                            print("\tLong Signal Detected")
                            break
                        elif bear_cross and emas_in_order and c < ema8 and len(get_account()['orders']) == 0:
                            # stop_loss = round(c - PARAMS['stop_loss_atr_factor']*atr,5)
                            stop_loss = max([df['High'][-di] for di in range(16)])
                            # take_profit = round(c + PARAMS['take_profit_atr_factor']*atr,5)
                            take_profit = c - (-c+stop_loss)
                            qty = int((PARAMS['risk_pct']*get_balance())//(take_profit - c))
                            limit_order(ins,c,qty,stop_loss,take_profit)
                            print("\tShort Signal Detected")
                            break
                    else:
                        print('\tNo Signals found')

        except Exception as e:
            print(e)
            response = input('\nAn error occured, restart? (y/n): ')
            if response == 'y':
                self.live()

if __name__ == "__main__":
    strat = Strategy()
    strat.live()