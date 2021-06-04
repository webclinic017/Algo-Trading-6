import alpaca_trade_api as tradeapi
import time
import datetime as dt
import pandas as pd
import numpy as np
from utility.scraper import get_low_float_stocks, get_SANDP_tickers, get_gainers
import matplotlib.pyplot as plt

API_KEY = "PK5QCW9RJ5N5FVPCOP6R"
API_SECRET = "u7aAbggWpAyvVswCK4p3rKE1fj36TcCW1KxV89nx"
APCA_API_BASE_URL = "https://paper-api.alpaca.markets"

class Strategy:
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
            elif self.timeToClose < (6.25*60*60): #after 9:45
                if self.position:
                    #Current price
                    current_price = float(self.alpaca.get_last_quote(self.position['symbol']).bidprice)
                    print(f"{self.position['symbol']} price: ${current_price}")
                    
                    #Sell signals
                    stop_loss = current_price <= self.position['stop_loss']
                    take_profit = current_price >= self.position['take_profit']

                    if stop_loss or take_profit:
                        self.submitOrder(self.position['symbol'], self.position['qty'], 'sell')
                        self.position = None
                    time.sleep(5)

                elif not self.position:
                    self.data = self.getCurrentData()
                    #Every minute check for new entry
                    for stock in self.data:
                        df = self.data[stock]
                        current_price = float(self.alpaca.get_last_quote(self.position['symbol']).bidprice)
                        l = df['Low'][-1]
                        c = df['Close'][-1]
                        ema = df['EMA200'][-1]
                        macd = df['MACD'][-1]
                        atr = df['ATR'][-1]
                        signal = df['Signal'][-1]
                        
                        #Buy signals
                        above_ema = l > ema
                        macd_below_0 = macd < 0
                        macd_above_signal = macd > signal

                        if above_ema and macd_below_0 and macd_above_signal and not self.position:
                            buying_power = float(self.alpaca.get_account().cash)
                            stop_loss = current_price - atr
                            take_profit = current_price + (1.5*atr)
                            qty = (0.01*buying_power)//(c-stop_loss)
                            self.submitOrder(stock, buying_power//df['High'][-1], 'buy')
                            self.position = {'symbol':stock,
                                             'buy_price':c,
                                             'qty':qty,
                                             'stop_loss':stop_loss,
                                             'take_profit':take_profit}
                    if not self.position:
                        print('No stocks to buy')
                        time.sleep(60)
            else:
                time.sleep(60)

    #####################################################################################
    ################################## Indicators #######################################
    #####################################################################################
    def EMA200(self, df):
        df['EMA200'] = df['Close'].ewm(200).mean()
    
    def MACD(self, df,a=12,b=26,c=9):
        """function to calculate MACD
        typical values a = 12; b =26, c =9"""
        df["MA_Fast"]=df["Close"].ewm(span=a,min_periods=a).mean()
        df["MA_Slow"]=df["Close"].ewm(span=b,min_periods=b).mean()
        df["MACD"]=df["MA_Fast"]-df["MA_Slow"]
        df["Signal"]=df["MACD"].ewm(span=c,min_periods=c).mean()

    def ATR(self, df,n=14):
        "function to calculate True Range and Average True Range"
        df['H-L']=abs(df['High']-df['Low'])
        df['H-PC']=abs(df['High']-df['Close'].shift(1))
        df['L-PC']=abs(df['Low']-df['Close'].shift(1))
        df['TR']=df[['H-L','H-PC','L-PC']].max(axis=1,skipna=False)
        df['ATR'] = df['TR'].rolling(n).mean()
        #df['ATR'] = df['TR'].ewm(span=n,adjust=False,min_periods=n).mean()
        df = df.drop(['H-L','H-PC','L-PC'],axis=1)
    ##########################################################################################
    #################################### Helper Functions ####################################
    ##########################################################################################
    def getCurrentData(self):
        print('Updating Data')
        d = {}
        df = self.alpaca.get_barset(self.stocks, "1Min").df
        for stock in self.stocks:
            temp = df[stock].copy()
            temp.columns = ['Open','High','Low','Close','Volume']
            #Add indicators to each df
            self.MACD(temp)
            self.EMA200(temp)
            self.ATR(temp)
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
            self.submitOrder(position.symbol, qty, orderSide)

        print("Sleeping until market close (15 minutes).")
        time.sleep(60 * 15)

    def submitOrder(self, ticker, qty, side):
        if(qty > 0):
            try:
                self.alpaca.submit_order(ticker, qty, side, "market", "day")
                print("\nMarket order of | " + str(qty) + " " + ticker + " " + side + " | completed.")
            except:
                self.submitOrder(ticker, qty, side)
                print("\nOrder of | " + str(qty) + " " + ticker + " " + side + " | did not go through.")
        else:
            print("\nQuantity is 0, order of | " + str(qty) + " " + ticker + " " + side + " | not completed.")

if __name__ == "__main__":
    print('Starting algorithm')
    strat = Strategy()
    strat.run()