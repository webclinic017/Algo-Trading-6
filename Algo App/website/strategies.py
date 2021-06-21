from .modules.oanda_api import limit_order, get_candlestick_data, get_balance, get_account
from talib import STOCHRSI, ATR
import time
import datetime as dt
import numpy as np

class SMA5_Cross:
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
            data['SMA 5'] = data['Close'].rolling(5).mean()
            data['Roll High'] = data['High'].rolling(10).max()
            data['Roll Low'] = data['Low'].rolling(10).min()
            data['Buy'] = data['Close'] < data['SMA 5']
            data['Sell'] = data['Close'] > data['SMA 5']
            data['Buy'] = np.where(data['Buy'] == True,data['Close'],np.nan)
            data['Sell'] = np.where(data['Sell'] == True,data['Close'],np.nan)
            d[ins] = data
        self.data = d

    def start(self):
        try:
            print('\nStarting SMA cross algorithm...')
            while True:
                if dt.datetime.now().minute % 5 == 0 and dt.datetime.now().second < 10 and get_account()['openPositionCount'] == 0 and len(get_account()['orders']) == 0:
                    self.update_data()
                    print(f'\n---- {time.asctime()}: Looking for Signals ---- \n')
                    for ins in self.instruments:
                        df = self.data[ins]
                        #Latest candle data
                        prev_buy = df['Buy'][-2]
                        b = df['Buy'][-1]
                        prev_sell = df['Sell'][-1]
                        s = df['Sell'][-1]
                        c = df['Close'][-1]
                        roll_high = df['Roll High'][-1]
                        roll_low = df['Roll Low'][-1]

                        if len(get_account()['orders']) == 0 and np.isnan(prev_buy) and (not np.isnan(b)):
                            take_profit = (c - roll_low) + c
                            qty = int((PARAMS['risk_pct']*get_balance())//(take_profit - c))
                            limit_order(ins,c,qty,roll_low,take_profit)
                            print("\tLong Signal Detected")
                            break
                        elif len(get_account()['orders']) == 0 and np.isnan(prev_sell) and (not np.isnan(s)):
                            take_profit = c - (-c + roll_low)
                            qty = int((PARAMS['risk_pct']*get_balance())//(take_profit - c))
                            limit_order(ins,c,qty,roll_high,take_profit)
                            print("Short Signal Detected")
                            break
                    else:
                        print('\tNo Signals found')

        except Exception as e:
            print(e)
            response = input('\nAn error occured, restart? (y/n): ')
            if response == 'y':
                self.srart()

PARAMS = {
    'bull_stoch_cross' : 40,
    'bear_stoch_cross' : 60,
    'EMA_gap' : 0.0001, # 1 pip
    'risk_pct' : 0.02, # 2%
    'sleep' : 30 # 1 minute
}

class Stoch_Scalp:
    """
    Indicators: 8, 14, 50 EMA, Stochastic

    """
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
            data['EMA 8'] = data['Close'].ewm(8).mean()
            data['EMA 14'] = data['Close'].ewm(14).mean()
            data['EMA 50'] = data['Close'].ewm(50).mean()
            data['Stoch'],data['Stoch_ma'] = STOCHRSI(data['Close'])
            data['ATR'] = ATR(data['High'],data['Low'],data['Close'])
            data['Roll High'] = data['High'].rolling(10).max()
            data['Roll Low'] = data['Low'].rolling(10).min()
            d[ins] = data
        self.data = d

    def start(self):
        try:
            print('\nStarting Stochastic Scalping Algorithm...')
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
                            stop_loss = df['Roll Low'][-1]
                            take_profit = c + (c-stop_loss)
                            qty = int((PARAMS['risk_pct']*get_balance())//(take_profit - c))
                            limit_order(ins,c,qty,stop_loss,take_profit)
                            print("\tLong Signal Detected")
                            break
                        elif bear_cross and emas_in_order and c < ema8 and len(get_account()['orders']) == 0:
                            stop_loss = df['Roll High'][-1]
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
