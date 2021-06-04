import alpaca_trade_api as tradeapi
import time
import datetime as dt
import pandas as pd
import numpy as np
from scraper import get_low_float_stocks, get_SANDP_tickers, get_gainers

API_KEY = "PKBDCJT24OXR196CNG33"
API_SECRET = "kKzy7MzxyPn9VZmVP146sbo6P3mtZvJkAb3HMk22"
APCA_API_BASE_URL = "https://paper-api.alpaca.markets"

class RSI_HA:
    """Day Trading Strategy using RSI and Heikan Ashi candles"""
    def __init__(self):
        self.alpaca = tradeapi.REST(API_KEY, API_SECRET, APCA_API_BASE_URL)
        self.stocks = get_gainers()
        self.data = self.getCurrentData()
        self.timeToClose = None
        self.position = None

    def run(self):
        self.awaitMarketOpen()
        self.onMarketOpen()
        while True:
            #Figure out when the market will close so we can prepare to sell beforehand.
            clock = self.alpaca.get_clock()
            closingTime = clock.next_close.replace(tzinfo=dt.timezone.utc).timestamp()
            currTime = clock.timestamp.replace(tzinfo=dt.timezone.utc).timestamp()
            self.timeToClose = closingTime - currTime
            if self.timeToClose <= (15*60):
                self.onMarketClose()
            else:
                self.data = self.getCurrentData()
                if self.position:
                    #Heikan Ashi candle
                    stock = self.position['symbol']
                    c = self.data[stock]['HA_Close'][-1]
                    o = self.data[stock]['HA_Open'][-1]
                    h = self.data[stock]['HA_High'][-1]
                    l = self.data[stock]['HA_Low'][-1]
                    prev_c = self.data[stock]['HA_Close'][-2]
                    prev_o = self.data[stock]['HA_Open'][-2]
                    rsi = self.data[stock]['RSI'][-1]

                    #Sell Indicators
                    red = c < o
                    small_body = h-l >= 5*(abs(c-o))
                    sell = rsi < 50 or red or small_body

                    if sell:
                        self.submitOrder(self.position['symbol'],self.position['qty'], 'sell',None, None)
                        self.position = None
                else:
                    for stock in self.data:
                        #Heikan Ashi candle
                        c = self.data[stock]['HA_Close'][-1]
                        o = self.data[stock]['HA_Open'][-1]
                        h = self.data[stock]['HA_High'][-1]
                        l = self.data[stock]['HA_Low'][-1]
                        prev_c = self.data[stock]['HA_Close'][-2]
                        prev_o = self.data[stock]['HA_Open'][-2]
                        rsi = self.data[stock]['RSI'][-1]
                        if stock == 'SRNE':
                            periods = self.consolidation_period(self.data[stock])
                            print(periods)

                        #Buy indicators
                        prev_red = prev_c < prev_o
                        green = c > o
                        buy = not self.position and (prev_red and green and rsi > 50 and rsi < 60)
                        print(stock, f'buy={buy} prev_red={prev_red} green={green} rsi={rsi}')

                        if buy:
                            buying_power = float(self.alpaca.get_account().cash)
                            qty = buying_power//h
                            stop_loss = l - 100/qty
                            take_profit=h+200/qty
                            self.position = {'symbol':stock,'qty':qty}
                            self.submitOrder(stock, qty, 'buy',take_profit, stop_loss)

            print('Sleeping for 5 minutes')
            #time.sleep(60*5)

    #####################################################################################
    ############################## Technical Indicators #################################
    #####################################################################################
    def HA(self, df):
        df['HA_Close'] = (df['close']+df['open']+df['high']+df['low'])/4
        df['HA_Open'] = (df['close']+df['open']).shift(1)/2
        high = []
        low = []
        for i in range(len(df)):
            high.append(max(df['high'][i], df['HA_Open'][i], df['HA_Close'][i] ))
            low.append(min(df['low'][i], df['HA_Open'][i], df['HA_Close'][i] ))
        df['HA_High'] = high
        df['HA_Low'] = low

    def RSI(self, df,n=14):
        "function to calculate RSI"
        df['delta']=df['close'] - df['close'].shift(1)
        df['gain']=np.where(df['delta']>=0,df['delta'],0)
        df['loss']=np.where(df['delta']<0,abs(df['delta']),0)
        avg_gain = []
        avg_loss = []
        gain = df['gain'].tolist()
        loss = df['loss'].tolist()
        for i in range(len(df)):
            if i < n:
                avg_gain.append(np.NaN)
                avg_loss.append(np.NaN)
            elif i == n:
                avg_gain.append(df['gain'].rolling(n).mean().tolist()[n])
                avg_loss.append(df['loss'].rolling(n).mean().tolist()[n])
            elif i > n:
                avg_gain.append(((n-1)*avg_gain[i-1] + gain[i])/n)
                avg_loss.append(((n-1)*avg_loss[i-1] + loss[i])/n)
        df['avg_gain']=np.array(avg_gain)
        df['avg_loss']=np.array(avg_loss)
        df['RS'] = df['avg_gain']/df['avg_loss']
        df['RSI'] = 100 - (100/(1+df['RS']))
        df.drop(columns=['delta', 'gain', 'loss','avg_gain','avg_loss','RS'])
    
    def is_consolidating(sel, df, percentage=2):
        recent_candlesticks = df[-15:]
        max_close = recent_candlesticks['close'].max()
        min_close = recent_candlesticks['close'].min()
        threshold = 1 - (percentage / 100)
        if min_close > (max_close * threshold):
            return True
        return False
    def consolidation_period(self, df):
        start = None
        end = None
        ranges = []
        for i in range(16, len(df)):
            temp = df[i-16:i]
            if self.is_consolidating(temp) and not start: #Update start and end date
                start = df.index[i-16]
                end = df.index[i-1]
            elif self.is_consolidating(temp) and start: #Update end date
                end = df.index[i-1]
            elif start and end:
                end = df.index[i-1]
                ranges.append([start, end])
                start = None
                end = None
        return ranges

    ##########################################################################################
    #################################### Helper Functions ####################################
    ##########################################################################################
    def getCurrentData(self):
        print('Gathering Data')
        d = {}
        df = self.alpaca.get_barset(self.stocks, "5Min").df
        for stock in self.stocks:
            print(stock)
            temp = df[stock].copy()
            self.HA(temp)
            self.RSI(temp)
            d[stock] = temp
        return d

    def awaitMarketOpen(self):
        print("Waiting for market to open...")
        isOpen = self.alpaca.get_clock().is_open
        while not isOpen:
            clock = self.alpaca.get_clock()
            openingTime = clock.next_open.replace(tzinfo=dt.timezone.utc).timestamp()
            currTime = clock.timestamp.replace(tzinfo=dt.timezone.utc).timestamp()
            timeToOpen = int((openingTime - currTime) / 60)
            print(str(timeToOpen) + " minutes til market open.")
            time.sleep(60)
            isOpen = self.alpaca.get_clock().is_open
        print("Market opened.")

    def onMarketOpen(self):
        #Cancel any existing orders
        orders = self.alpaca.list_orders(status="open")
        for order in orders:
            self.alpaca.cancel_order(order.id)
    
    def onMarketClose(self):
        # Close all positions when 15 minutes til market close.
        print("Market closing soon, Closing positions.")
        positions = self.alpaca.list_positions()
        for position in positions:
            if position.side == 'long':
                orderSide = 'sell'
            else:
                orderSide = 'buy'
            qty = abs(int(float(position.qty)))
            self.submitOrder(position.symbol, qty, orderSide, None, None)

        print("Sleeping until market close (15 minutes).")
        time.sleep(60 * 15)

    def submitOrder(self, ticker, qty, side, take_profit, stop_loss):
        if(qty > 0):
            try:
                self.alpaca.submit_order(ticker, qty, side, "market", "day", take_profit=dict(limit_price=take_profit),stop_loss=dict(limit_price=stop_loss))
                print("\nMarket order of | " + str(qty) + " " + ticker + " " + side + " | completed.")
            except:
                self.submitOrder(ticker, qty, side, take_profit, stop_loss)
                print("\nOrder of | " + str(qty) + " " + ticker + " " + side + " | did not go through.")
        else:
            print("\nQuantity is 0, order of | " + str(qty) + " " + ticker + " " + side + " | not completed.")
                
strat = RSI_HA()
strat.run()