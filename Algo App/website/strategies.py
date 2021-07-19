from .modules.oanda_api import calculate_qty,market_order,limit_order, get_candlestick_data, get_balance, get_account
from talib import STOCHRSI, ATR
from .modules.indicators import cipherB, ATR
import time
import datetime as dt
import numpy as np

class CipherB:
    def __init__(self,candle_span='M5'):
        self.instrument = 'EUR_USD'
        self.candle_span = candle_span
        self.update_data()
        self.atr_mult = 1
        self.rr_mult = 3
        self.run = False

    def update_data(self):
        data = get_candlestick_data(self.instrument,300,self.candle_span)
        #Add indicators to data here
        data['EMA 200'] = data['Close'].ewm(200).mean()
        data['EMA 50'] = data['Close'].ewm(50).mean()
        cipherB(data)
        ATR(data)

        #Condition 1 (Above/Below 200 EMA)
        bull_condition1 = data['Close'] > data['EMA 200']
        bear_condition1 = data['Close'] < data['EMA 200']

        #Condtion 2 (Pullback to 50 EMA)
        bull_condition2 = np.array([False]*len(data))
        bear_condition2 = np.array([False]*len(data))

        lookback = 20
        for i in range(lookback, len(data)):
            above_50 = False
            below_50 = False
            for di in range(lookback):
                if data['Close'][i-lookback+di] > data['EMA 50'][i-lookback+di] and data['EMA 50'][i-lookback+di] > data['EMA 200'][i-lookback+di]: 
                    above_50 = True
                if data['Close'][i-lookback+di] < data['EMA 50'][i-lookback+di] and data['EMA 50'][i-lookback+di] < data['EMA 200'][i-lookback+di]: 
                    below_50 = True

                if above_50 and data['Close'][i-lookback+di] < data['EMA 50'][i-lookback+di]:
                    bull_condition2[i] = True
                if below_50 and data['Close'][i-lookback+di] > data['EMA 50'][i-lookback+di]:
                    bear_condition2[i] = True
                    
        #Condition 3: Money Flow above/below 0
        bull_condition3 = data['Money Flow'] > 0
        bear_condition3 = data['Money Flow'] < 0
        
        #Condition 4: Wave Trend Cross above/below 0
        bull_condition4 = ((data['wt1'] > data['wt2']) & (data['wt1'].shift(1) <= data['wt2'].shift(1)) & (data['wt1'] < 0)) 
        bear_condition4 = ((data['wt1'] < data['wt2']) & (data['wt1'].shift(1) >= data['wt2'].shift(1)) & (data['wt1'] > 0)) 

        #Buy/Sell signals (All conditions)
        data['Buy'] = (bull_condition1 & bull_condition2 & bull_condition3 & bull_condition4)
        data['Sell'] = (bear_condition1 & bear_condition2 & bear_condition3 & bear_condition4)
        
        self.data = data

    def start(self):
        self.run = True
        try:
            print('\nStarting Cipher B Algorithm...')
            while self.run:
                if dt.datetime.now().second == 0  and get_account()['openPositionCount'] == 0 and len(get_account()['orders']) == 0:
                    self.update_data()
                    print(f'\n---- {time.asctime()}: Looking for Signals ---- \n')
                    df = self.data
                    print(f'\t{df.index[-1]}')
                    c = df['Close'][-1]

                    if len(get_account()['orders']) == 0 and df['Buy'][-1]:
                        stop_loss = c - self.atr_mult * df['ATR'][-1]
                        take_profit = c + self.rr_mult*(c-stop_loss)
                        qty = calculate_qty(c,stop_loss,"EUR_USD",balance=get_balance())
                        market_order(self.instrument,qty,stop_loss,take_profit)
                        print("\tLong Signal Detected")
                    elif len(get_account()['orders']) == 0 and df['Sell'][-1]:
                        stop_loss = c + self.atr_mult * df['ATR'][-1]
                        take_profit = c - self.rr_mult*(stop_loss-c)
                        qty = calculate_qty(c,stop_loss,"EUR_USD",balance=get_balance())
                        market_order(self.instrument,qty,stop_loss,take_profit)
                        print("Short Signal Detected")
                    else:
                        print('\tNo Signals found')
            print('\nStopping Cipher B Algorithm...')

        except Exception as e:
            print(e)
            print('\nAn error occured, restarting...')
            self.start()

# # PARAMS = {
# #     'bull_stoch_cross' : 40,
# #     'bear_stoch_cross' : 60,
# #     'EMA_gap' : 0.0001, # 1 pip
# #     'risk_pct' : 0.02, # 2%
# #     'sleep' : 30 # 1 minute
# # }

# class SimpleMACD:
#     def __init__(self,candle_span='M5'):
#         self.instruments = [
#             'USD_CAD','EUR_USD','USD_CHF','GBP_USD','NZD_USD',
#             'AUD_USD'
#         ]
#         self.candle_span = candle_span
#         self.update_data()

#     def update_data(self):
#         d = {}
#         for ins in self.instruments:
#             data = get_candlestick_data(ins,300,self.candle_span)
#             #Add indicators to data here
#             data['EMA 200'] = data['Close'].ewm(200).mean()
#             MACD(data)

#             #Condition 1 (Above/Below 200 EMA)
#             data['Long Condition 1'] = data['Close'] > data['EMA 200']
#             data['Short Condition 1'] = data['Close'] < data['EMA 200']

#             #Condtion 2 (MACD cross below/above 0)
#             data['Long Condition 2'] = (data['MACD'] < 0) & (data['MACD'] > data['Signal']) & (data['MACD'].shift(1) <= data['Signal'].shift(1))
#             data['Short Condition 2'] = (data['MACD'] > 0) & (data['MACD'] < data['Signal']) & (data['MACD'].shift(1) >= data['Signal'].shift(1))

#             #Buy/Sell signals (All conditions)
#             buy = (data['Long Condition 1'] & data['Long Condition 2'])
#             data['Buy'] = buy
#             data['Buy Plot'] = np.where(buy == True,data['Close'],np.nan)
#             sell = (data['Short Condition 1'] & data['Short Condition 2'])
#             data['Sell'] = sell
#             data['Sell Plot'] = np.where(sell == True,data['Close'],np.nan)
#             d[ins] = data
#         self.data = d

#     def start(self):
#         try:
#             print('\nStarting Simple MACD Algorithm...')
#             while True:
#                 if dt.datetime.now().minute % 5 == 0 and dt.datetime.now().second < 10 and get_account()['openPositionCount'] == 0 and len(get_account()['orders']) == 0:
#                     self.update_data()
#                     print(f'\n---- {time.asctime()}: Looking for Signals ---- \n')
#                     for ins in self.instruments:
#                         df = self.data[ins]
#                         c = df['Close'][-1]

#                         if len(get_account()['orders']) == 0 and df['Buy'][-1]:
#                             stop_loss = min([df['Low'][-1-di] for di in range(5)])
#                             take_profit = c + 2*(c-stop_loss)
#                             qty = int((PARAMS['risk_pct']*get_balance())//(take_profit - c))
#                             limit_order(ins,c,qty,stop_loss,take_profit)
#                             print("\tLong Signal Detected")
#                             break
#                         elif len(get_account()['orders']) == 0 and df['Sell'][-1]:
#                             stop_loss = max([df['High'][-1-di] for di in range(5)])
#                             take_profit = c - 2*(stop_loss-c)
#                             qty = int((PARAMS['risk_pct']*get_balance())//(take_profit - c))
#                             limit_order(ins,c,qty,stop_loss,take_profit)
#                             print("Short Signal Detected")
#                             break
#                     else:
#                         print('\tNo Signals found')

#         except Exception as e:
#             print(e)
#             print('\nAn error occured, restarting...')
#             self.start()

# class Triple_STrend:
#     def __init__(self,candle_span='M5'):
#         self.instruments = [
#             'USD_CAD','EUR_USD','USD_CHF','GBP_USD','NZD_USD',
#             'AUD_USD','EUR_CAD','EUR_AUD','EUR_CHF','EUR_GBP',
#             'AUD_CAD','GBP_CHF','AUD_NZD'
#         ]
#         self.candle_span = candle_span
#         self.update_data()
        
#     def update_data(self):
#         d = {}
#         for ins in self.instruments:
#             data = get_candlestick_data(ins,300,self.candle_span)
#             #Add indicators to data here
#             data['EMA 200'] = data['Close'].ewm(200).mean()
#             data['Stoch RSI'], data['Stoch RSI MA'] = STOCHRSI(data['Close'],fastk_period=3)
#             data['strend 3'],data['s_up_3'],data['s_down_3'] = supertrend(data['High'],data['Low'],data['Close'],12,3)
#             data['strend 2'],data['s_up_2'],data['s_down_2'] = supertrend(data['High'],data['Low'],data['Close'],11,2)
#             data['strend 1'],data['s_up_1'],data['s_down_1'] = supertrend(data['High'],data['Low'],data['Close'],10,1)

#             #Condition 1 (Above/Below 200 EMA)
#             data['Long Condition 1'] = data['Close'] > data['EMA 200']
#             data['Short Condition 1'] = data['Close'] < data['EMA 200']

#             #Condtion 2 (Stochastic RSI cross aboe threshold)
#             data['Long Condition 2'] = (data['Stoch RSI'] < 20) & (data['Stoch RSI'] > data['Stoch RSI MA']) & (data['Stoch RSI'].shift(1) <= data['Stoch RSI MA'].shift(1))
#             data['Short Condition 2'] = (data['Stoch RSI'] > 80) & (data['Stoch RSI'] < data['Stoch RSI MA']) & (data['Stoch RSI'].shift(1) >= data['Stoch RSI MA'].shift(1))

#             #Condtion 3 (At least two supertrends are above/below price)
#             strend1_long = data['strend 1'] < data['Close']
#             strend2_long = data['strend 2'] < data['Close']
#             strend3_long = data['strend 3'] < data['Close']
#             data['Long Condition 3'] = (strend1_long & strend2_long) | (strend2_long & strend3_long) | (strend1_long & strend3_long) | (strend1_long & strend2_long & strend3_long)
#             strend1_short = data['strend 1'] > data['Close']
#             strend2_short = data['strend 2'] > data['Close']
#             strend3_short = data['strend 3'] > data['Close']
#             data['Short Condition 3'] = (strend1_short & strend2_short) | (strend2_short & strend3_short) | (strend1_short & strend3_short) | (strend1_short & strend2_short & strend3_short)

#             #Buy/Sell signals (All three conditions)
#             buy = (data['Long Condition 1'] & data['Long Condition 2'] & data['Long Condition 3'])
#             data['Buy'] = buy
#             data['Buy Plot'] = np.where(buy == True,data['Close'],np.nan)
#             sell = (data['Short Condition 1'] & data['Short Condition 2'] & data['Short Condition 3'])
#             data['Sell'] = sell
#             data['Sell Plot'] = np.where(sell == True,data['Close'],np.nan)
#             d[ins] = data
#         self.data = d

#     def start(self):
#         try:
#             print('\nStarting Triple SuperTrend Algorithm...')
#             while True:
#                 if dt.datetime.now().minute % 5 == 0 and dt.datetime.now().second < 10 and get_account()['openPositionCount'] == 0 and len(get_account()['orders']) == 0:
#                     self.update_data()
#                     print(f'\n---- {time.asctime()}: Looking for Signals ---- \n')
#                     for ins in self.instruments:
#                         df = self.data[ins]
#                         c = df['Close'][-1]

#                         if len(get_account()['orders']) == 0 and df['Buy'][-1]:
#                             stop_loss = min([df['strend 1'][-1],df['strend 2'][-1],df['strend 3'][-1]])
#                             take_profit = c + 1.5*(c-stop_loss)
#                             qty = int((PARAMS['risk_pct']*get_balance())//(take_profit - c))
#                             limit_order(ins,c,qty,stop_loss,take_profit)
#                             print("\tLong Signal Detected")
#                             break
#                         elif len(get_account()['orders']) == 0 and df['Sell'][-1]:
#                             stop_loss = max([df['strend 1'][-1],df['strend 2'][-1],df['strend 3'][-1]])
#                             take_profit = c - 1.5*(stop_loss-c)
#                             qty = int((PARAMS['risk_pct']*get_balance())//(take_profit - c))
#                             limit_order(ins,c,qty,stop_loss,take_profit)
#                             print("Short Signal Detected")
#                             break
#                     else:
#                         print('\tNo Signals found')

#         except Exception as e:
#             print(e)
#             print('\nAn error occured, restarting...')
#             self.start()

# class SMA5_Cross:
#     def __init__(self,candle_span='M5'):
#         self.instruments = [
#             'USD_CAD','EUR_USD','USD_CHF','GBP_USD','NZD_USD',
#             'AUD_USD','EUR_CAD','EUR_AUD','EUR_CHF','EUR_GBP',
#             'AUD_CAD','GBP_CHF','AUD_NZD'
#         ]
#         self.candle_span = candle_span
#         self.update_data()
        
#     def update_data(self):
#         d = {}
#         for ins in self.instruments:
#             data = get_candlestick_data(ins,1000,self.candle_span)
#             #Add indicators to data here
#             data['SMA 5'] = data['Close'].rolling(5).mean()
#             data['Roll High'] = data['High'].rolling(10).max()
#             data['Roll Low'] = data['Low'].rolling(10).min()
#             data['Buy'] = data['Close'] < data['SMA 5']
#             data['Sell'] = data['Close'] > data['SMA 5']
#             data['Buy'] = np.where(data['Buy'] == True,data['Close'],np.nan)
#             data['Sell'] = np.where(data['Sell'] == True,data['Close'],np.nan)
#             d[ins] = data
#         self.data = d

#     def start(self):
#         try:
#             print('\nStarting SMA cross algorithm...')
#             while True:
#                 if dt.datetime.now().minute % 5 == 0 and dt.datetime.now().second < 10 and get_account()['openPositionCount'] == 0 and len(get_account()['orders']) == 0:
#                     self.update_data()
#                     print(f'\n---- {time.asctime()}: Looking for Signals ---- \n')
#                     for ins in self.instruments:
#                         df = self.data[ins]
#                         #Ladata candle data
#                         prev_buy = df['Buy'][-2]
#                         b = df['Buy'][-1]
#                         prev_sell = df['Sell'][-1]
#                         s = df['Sell'][-1]
#                         c = df['Close'][-1]
#                         roll_high = df['Roll High'][-1]
#                         roll_low = df['Roll Low'][-1]

#                         if len(get_account()['orders']) == 0 and np.isnan(prev_buy) and (not np.isnan(b)):
#                             take_profit = (c - roll_low) + c
#                             qty = int((PARAMS['risk_pct']*get_balance())//(take_profit - c))
#                             limit_order(ins,c,qty,roll_low,take_profit)
#                             print("\tLong Signal Detected")
#                             break
#                         elif len(get_account()['orders']) == 0 and np.isnan(prev_sell) and (not np.isnan(s)):
#                             take_profit = c - (-c + roll_low)
#                             qty = int((PARAMS['risk_pct']*get_balance())//(take_profit - c))
#                             limit_order(ins,c,qty,roll_high,take_profit)
#                             print("Short Signal Detected")
#                             break
#                     else:
#                         print('\tNo Signals found')

#         except Exception as e:
#             print(e)
#             print('\nAn error occured, restarting...')
#             self.start()

# class Stoch_Scalp:
#     """
#     Indicators: 8, 14, 50 EMA, Stochastic

#     """
#     def __init__(self,candle_span='M5'):
#         self.instruments = [
#             'USD_CAD','EUR_USD','USD_CHF','GBP_USD','NZD_USD',
#             'AUD_USD','EUR_CAD','EUR_AUD','EUR_CHF','EUR_GBP',
#             'AUD_CAD','GBP_CHF','AUD_NZD'
#         ]
#         self.candle_span = candle_span
#         self.update_data()
        

#     def update_data(self):
#         d = {}
#         for ins in self.instruments:
#             data = get_candlestick_data(ins,1000,self.candle_span)
#             #Add indicators to data here
#             data['EMA 8'] = data['Close'].ewm(8).mean()
#             data['EMA 14'] = data['Close'].ewm(14).mean()
#             data['EMA 50'] = data['Close'].ewm(50).mean()
#             data['Stoch'],data['Stoch_ma'] = STOCHRSI(data['Close'])
#             data['ATR'] = ATR(data['High'],data['Low'],data['Close'])
#             data['Roll High'] = data['High'].rolling(10).max()
#             data['Roll Low'] = data['Low'].rolling(10).min()
#             d[ins] = data
#         self.data = d

#     def start(self):
#         try:
#             print('\nStarting Stochastic Scalping Algorithm...')
#             while True:
#                 if dt.datetime.now().minute % 5 == 0 and dt.datetime.now().second < 10 and get_account()['openPositionCount'] == 0 and len(get_account()['orders']) == 0:
#                     self.update_data()
#                     print(f'\n---- {time.asctime()}: Looking for Signals ---- \n')
#                     for ins in self.instruments:
#                         df = self.data[ins]
#                         #Ladata candle data
#                         row = df.iloc[-1]
#                         o,h,l,c = row['Open'],row['High'],row['Low'],row['Close']
#                         #Rest of ladata data
#                         atr = row['ATR']
#                         ema8 = row['EMA 8']
#                         ema14 = row['EMA 14']
#                         ema50 = row['EMA 50']
#                         prev_stoch = df['Stoch'][-2]
#                         prev_stoch_ma = df['Stoch_ma'][-2]
#                         cur_stoch = df['Stoch'][-1]
#                         cur_stoch_ma = df['Stoch_ma'][-1]

#                         #Long signals
#                         bull_cross = prev_stoch <= prev_stoch_ma and cur_stoch > cur_stoch_ma and prev_stoch < PARAMS['bull_stoch_cross']
#                         emas_in_order = ema8 > ema14 + PARAMS['EMA_gap'] and ema14 > ema50 + PARAMS['EMA_gap']
#                         #Short signals
#                         bear_cross = prev_stoch >= prev_stoch_ma and cur_stoch < cur_stoch_ma and prev_stoch > PARAMS['bear_stoch_cross']
#                         emas_in_order = ema8 + PARAMS['EMA_gap'] < ema14 and ema14 + PARAMS['EMA_gap'] < ema50

#                         if bull_cross and emas_in_order and c > ema8 and len(get_account()['orders']) == 0:
#                             stop_loss = df['Roll Low'][-1]
#                             take_profit = c + (c-stop_loss)
#                             qty = int((PARAMS['risk_pct']*get_balance())//(take_profit - c))
#                             limit_order(ins,c,qty,stop_loss,take_profit)
#                             print("\tLong Signal Detected")
#                             break
#                         elif bear_cross and emas_in_order and c < ema8 and len(get_account()['orders']) == 0:
#                             stop_loss = df['Roll High'][-1]
#                             take_profit = c - (-c+stop_loss)
#                             qty = int((PARAMS['risk_pct']*get_balance())//(take_profit - c))
#                             limit_order(ins,c,qty,stop_loss,take_profit)
#                             print("\tShort Signal Detected")
#                             break
#                     else:
#                         print('\tNo Signals found')

#         except Exception as e:
#             print(e)
#             print('\nAn error occured, restarting...')
#             self.start()
