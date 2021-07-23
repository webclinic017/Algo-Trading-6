from .modules.oanda_api import ClientREST
from .modules.indicators import cipherB, ATR, half_trend, money_flow, wave_trend, RSI
import time
import datetime as dt
import numpy as np
import os
import matplotlib.pyplot as plt
from . import config

api = ClientREST(access_token = config.access_token, account_id = config.account_id)

class Scalper:
    def __init__(self):
        self.instrument = 'EUR_USD'
        self.update_data()
        self.run = False
        self.rr_mult = 1.5
        self.order = None

    def update_data(self):
        m5 = api.get_candlestick_data(self.instrument,300,"M5")
        h1 = api.get_candlestick_data(self.instrument,300,"H1")
        #Add indicators to data here
        m5['EMA 8'] = m5['Close'].ewm(8).mean()
        m5['EMA 13'] = m5['Close'].ewm(13).mean()
        m5['EMA 21'] = m5['Close'].ewm(21).mean()
        
        h1['EMA 8'] = h1['Close'].ewm(8).mean()
        h1['EMA 21'] = h1['Close'].ewm(8).mean()
        
        self.m5 = m5
        self.h1 = h1

    def save_plot(self):
        print(os.getcwd()+'templates/Scalper.png')
        plt.plot(self.m5['Close'],alpha=0.7,label='Close')
        plt.plot(self.m5['EMA 8'],alpha=0.5)
        plt.plot(self.m5['EMA 13'],alpha=0.5)
        plt.plot(self.m5['EMA 21'],alpha=0.5)
        plt.legend()
        plt.savefig('Scalper.png')

    def start(self):
        self.run = True
        try:
            print('\nStarting Cipher B Algorithm...')
            while self.run:
                if dt.datetime.now().second == 0  and len(api.get_open_positions()['positions']) == 0:
                    self.update_data()
                    print(f'\n---- {time.asctime()}: Looking for Signals ---- \n')
                    m5 = self.m5
                    h1 = self.h1
                    print(f'\t{m5.index[-1]}')
                    c = m5['Close'][-1]
                    
                    #Condition 1: Above/Below 8,21 EMA in hour tf
                    lc1 = h1['Close'][-1] > h1['EMA 8'][-1] and h1['EMA 8'][-1] > h1['EMA 21'][-1]
                    sc1 = h1['Close'][-1] < h1['EMA 8'][-1] and h1['EMA 8'][-1] < h1['EMA 21'][-1]
                    
                    #Condtion 2: Above EMA's in 5 minute timeframe
                    lc2 = m5['Close'][-1] > m5['EMA 8'][-1] and m5['EMA 8'][-1] > m5['EMA 13'][-1] and m5['EMA 13'][-1] > m5['EMA 21'][-1]
                    sc2 = m5['Close'][-1] < m5['EMA 8'][-1] and m5['EMA 8'][-1] < m5['EMA 13'][-1] and m5['EMA 13'][-1] < m5['EMA 21'][-1]
                    
                    #Condition3: Trigger candle (pullback into EMA 8)
                    lc3 = m5['Low'][-2] > m5['EMA 8'][-1] and m5['Low'][-1] <= m5['EMA 8'][-1]
                    sc3 = m5['High'][-2] < m5['EMA 8'][-1] and m5['High'][-1] >= m5['EMA 8'][-1]
                    
                    if len(api.get_orders()['orders']) == 0 and (lc1 and lc2 and lc3):
                        stop_loss = m5['Low'][-1]
                        take_profit = c + self.rr_mult*(c - stop_loss)
                        stop_price = max([m5['High'][-di] for di in range(2,6)])
                        qty = api.calculate_qty(c,stop_loss,self.instrument,balance=api.get_balance())
                        api.stop_order(self.instrument,stop_price,qty,stop_loss,take_profit)
                        self.order = "long"
                        print("\tLong Signal Detected")
                    if len(api.get_orders()['orders']) == 0 and (sc1 and sc2 and sc3):
                        stop_loss = m5['High'][-1]
                        take_profit = c - self.rr_mult*(stop_loss-c)
                        stop_price = min([m5['Low'][-di] for di in range(2,6)])
                        qty = api.calculate_qty(c,stop_loss,self.instrument,balance=api.get_balance())
                        api.stop_order(self.instrument,stop_price,qty,stop_loss,take_profit)
                        self.order = "short"
                        print("\tShort Signal Detected")
                    elif self.order:
                        if self.order == "long":
                            if m5['Close'][-1] < m5['EMA 21'][-1]:
                                api.cancel_order()
                        else:
                            if m5['Close'][-1] > m5['EMA 21'][-1]:
                                api.cancel_order() 
                    else:
                        print('\tNo Signals found')
            print('\nStopping Cipher B Algorithm...')

        except Exception as e:
            print(e)
            print('\nAn error occured, restarting...')
            self.start()

class HalfTrend:
    def __init__(self,candle_span='M5'):
        self.instrument = 'EUR_USD'
        self.candle_span = candle_span
        self.update_data()
        self.rr_mult = 2.5
        self.atr_mult = 1
        self.run = False

    def update_data(self):
        df = api.get_candlestick_data(self.instrument,300,self.candle_span)
        df['EMA 200'] = df['Close'].ewm(200,min_periods=200).mean()
        money_flow(df)
        wave_trend(df)
        RSI(df,n=2)
        ATR(df,n=100)
        df.dropna(axis=0,inplace=True)
        half_trend(df)

        #Half Trend Crosses
        bull_cross = np.isnan(df.shift(1)['up']) & ~(np.isnan(df['up']))
        bear_cross = np.isnan(df.shift(1)['dn']) & ~(np.isnan(df['dn']))

        #Above/Below 200 EMA
        above_200_ema = df['Close'] > df['EMA 200']
        below_200_ema = df['Close'] < df['EMA 200']

        #Money Flow above/below 0
        mf_above_0 = df['Money Flow'] > 0
        mf_below_0 = df['Money Flow'] < 0

        #Time not within 5:00pm to 8:00pm EST
        def get_hour(date):
            col_index = date.find(':')
            hour = int(date[col_index-2:col_index])
            return hour

        df['Hour'] = [get_hour(str(date)) for date in df.index]
        good_time = ~((df['Hour'] >= 17) & (df['Hour'] < 20))

        #Buy and Sell Signals
        df['Buy'] = bull_cross & above_200_ema & mf_above_0 & good_time
        df['Sell'] = bear_cross & below_200_ema & mf_below_0 & good_time
        
        self.data = df
    
    def save_plot(self):
        plt.subplot(2,1,1)
        plt.plot(self.data['Close'],alpha=0.7,label='Close')
        plt.plot(self.data['EMA 200'],alpha=0.5)
        plt.plot(self.data.index,np.where(self.data['Buy']==True,self.data['Close'],np.nan),marker='^',color='g')
        plt.plot(self.data.index,np.where(self.data['Sell']==True,self.data['Close'],np.nan),marker='v',color='r')
        plt.legend()

        plt.subplot(2,1,2)
        plt.plot(self.data['Money Flow'])
        plt.plot(self.data['wt1'])
        plt.plot(self.data['wt2'])
        plt.savefig('HalfTrend.png')

    def start(self):
        self.run = True
        try:
            print('\nStarting HalfTrend Algorithm...')
            while self.run:
                if dt.datetime.now().second == 30 and len(api.get_open_positions()['positions']) == 0 and len(api.get_orders()['orders']) == 0:
                    self.update_data()
                    print(f'\n---- {time.asctime()}: Looking for Signals ---- \n')
                    df = self.data
                    c = df['Close'][-1]

                    if len(api.get_orders()['orders']) == 0 and df['Buy'][-1]:
                        stop_loss = c - self.atr_mult * df['ATR'][-1]
                        take_profit = c + self.rr_mult*(c-stop_loss)
                        qty = api.calculate_qty(c,stop_loss,self.instrument,balance=api.get_balance())
                        api.market_order(self.instrument,qty,stop_loss,take_profit)
                        print("\tLong Signal Detected")
                    elif len(api.get_orders()['orders']) == 0 and df['Sell'][-1]:
                        stop_loss = c + self.atr_mult * df['ATR'][-1]
                        take_profit = c - self.rr_mult*(stop_loss-c)
                        qty = api.calculate_qty(c,stop_loss,self.instrument,balance=api.get_balance())
                        api.market_order(self.instrument,qty,stop_loss,take_profit)
                        print("Short Signal Detected")
                    else:
                        print('\tNo Signals found')
            print('\nStopping HalfTrend Algorithm...')

        except Exception as e:
            print(e)
            print('\nAn error occured, restarting...')
            self.start()

class CipherB:
    def __init__(self,candle_span='M5'):
        self.instrument = 'EUR_USD'
        self.candle_span = candle_span
        self.update_data()
        self.atr_mult = 1
        self.rr_mult = 3
        self.run = False

    def update_data(self):
        data = api.get_candlestick_data(self.instrument,300,self.candle_span)
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

    def save_plot(self):
        plt.subplot(2,1,1)
        plt.plot(self.data['Close'],alpha=0.7,label='Close')
        plt.plot(self.data['EMA 200'],alpha=0.5)
        plt.plot(self.data['EMA 50'],alpha=0.5)
        plt.plot(self.data.index,np.where(self.data['Buy']==True,self.data['Close'],np.nan),marker='^',color='g')
        plt.plot(self.data.index,np.where(self.data['Sell']==True,self.data['Close'],np.nan),marker='v',color='r')
        plt.legend()

        plt.subplot(2,1,2)
        plt.plot(self.data['Money Flow'])
        plt.plot(self.data['wt1'])
        plt.plot(self.data['wt2'])
        plt.savefig('CipherB.png')

    def start(self):
        self.run = True
        try:
            print('\nStarting Cipher B Algorithm...')
            while self.run:
                if dt.datetime.now().second == 30 and len(api.get_open_positions()['positions']) == 0 and len(api.get_orders()['orders']) == 0:
                    self.update_data()
                    print(f'\n---- {time.asctime()}: Looking for Signals ---- \n')
                    df = self.data
                    print(f'\t{df.index[-1]}')
                    c = df['Close'][-1]

                    if len(api.get_orders()['orders']) == 0 and df['Buy'][-1]:
                        stop_loss = c - self.atr_mult * df['ATR'][-1]
                        take_profit = c + self.rr_mult*(c-stop_loss)
                        qty = api.calculate_qty(c,stop_loss,"EUR_USD",balance=api.get_balance())
                        api.market_order(self.instrument,qty,stop_loss,take_profit)
                        print("\tLong Signal Detected")
                    elif len(api.get_orders()['orders']) == 0 and df['Sell'][-1]:
                        stop_loss = c + self.atr_mult * df['ATR'][-1]
                        take_profit = c - self.rr_mult*(stop_loss-c)
                        qty = api.calculate_qty(c,stop_loss,"EUR_USD",balance=api.get_balance())
                        api.market_order(self.instrument,qty,stop_loss,take_profit)
                        print("Short Signal Detected")
                    else:
                        print('\tNo Signals found')
            print('\nStopping Cipher B Algorithm...')

        except Exception as e:
            print(e)
            print('\nAn error occured, restarting...')
            self.start()