import alpaca_trade_api as tradeapi
import time
import datetime as dt
import pandas as pd
import numpy as np
from modules.scraper import get_low_float_stocks, get_SANDP_tickers, get_gainers
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
                    #Check as mush as possible for stop loss and take_profit
                    last_quote = self.alpaca.get_last_quote(self.position['symbol'])
                    current_price = float(last_quote.bidprice)
                    print(f"{self.position['symbol']} price: ${current_price} Stoploss price: ${stop_loss} Takeprofit price: ${take_profit}")
                    stop_loss = self.position['stop_loss']
                    take_profit = self.position['take_profit']

                    if current_price <= stop_loss or current_price >= take_profit:
                        self.submitOrder(self.position['symbol'], self.position['qty'], 'sell')
                        self.position = None
                    time.sleep(5)

                elif not self.position:
                    self.data = self.getCurrentData()
                    #Every minute check for new entry
                    for stock in self.data:
                        df = self.data[stock]
                        above_ema = df['Close'][-1] > df['EMA200'][-1]
                        rsi_over50 = df['RSI'][-1] > 50
                        atr = df['ATR'][-1]
                        bull_pattern = df['Engulfing'][-1] > 0

                        if (above_ema and rsi_over50 and bull_pattern) and not self.position:
                            buying_power = float(self.alpaca.get_account().cash)
                            last_quote = self.alpaca.get_last_quote(stock)
                            current_price = float(last_quote.bidprice)
                            stop_loss = current_price - atr
                            take_profit = current_price + (1.5*atr)
                            qty = abs((0.01*buying_power)//(current_price-stop_loss))#1% risk per trade
                            self.position = {'symbol':stock,
                                             'qty':qty,
                                             'stop_loss':stop_loss,
                                             'take_profit':take_profit}
                            self.submitOrder(stock, qty, 'buy')
                    if not self.position:
                        print('Sleeping for a minute')
                        time.sleep(60)

    #####################################################################################
    ################################## Indicators #######################################
    #####################################################################################
    def RSI(self, df,n=14):
        "function to calculate RSI"
        df['delta']=df['Close'] - df['Close'].shift(1)
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
    
    def EMA200(self, df):
        df['EMA200'] = df['Close'].ewm(200).mean()
    
    def BullEngulf(self, df):
        signals = [np.nan]
        for i in range(len(df)):
            if i > 0:
                prev_red = df['Close'][i-1] < df['Open'][i-1]
                cur_green = df['Close'][i] > df['Open'][i]
                if prev_red and cur_green:
                    prev_width = abs(df['Close'][i-1]-df['Open'][i-1])
                    cur_width = abs(df['Close'][i] - df['Open'][i])
                    if prev_width < cur_width:
                        signals.append(df['Close'][i]) #Bullish signal at price
                    else:
                        signals.append(np.nan) #no signal
                else:
                    signals.append(np.nan)
        df['Engulfing'] = signals
    
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
            self.RSI(temp)
            self.EMA200(temp)
            self.BullEngulf(temp)
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
                print("\nOrder of | " + str(qty) + " " + ticker + " " + side + " | did not go through.")
                self.position = None
        else:
            print("\nQuantity is 0, order of | " + str(qty) + " " + ticker + " " + side + " | not completed.")
            self.position = None

if __name__ == "__main__":
    print('Starting algorithm')
    strat = Strategy()
    strat.run()