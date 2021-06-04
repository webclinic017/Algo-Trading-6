import alpaca_trade_api as tradeapi
import threading
import time
import datetime as dt
import os
import pandas as pd
import talib
from scraper import get_low_float_stocks, get_SANDP_tickers, get_gainers

API_KEY = "PKUHDJD7RS8U7NMJYZIY"
API_SECRET = "zROM0AON6XowrC1XSRuwSUyvkET6pWtkp9Mwrs7Z"
APCA_API_BASE_URL = "https://paper-api.alpaca.markets"

class Strategy:
    """Day Trading Strategy using candle sticks patterns and  10 period vwap"""
    def __init__(self):
        self.alpaca = tradeapi.REST(API_KEY, API_SECRET, APCA_API_BASE_URL)
        self.stocks = get_gainers()
        self.timeToClose = None
        self.position = None

    def run(self):
        self.awaitMarketOpen()
        self.onMarketOpen()
        while True:
            self.updateClock()
            if self.timeToClose < (15*60): #After 3:45
                self.onMarketClose()
            elif (self.timeToClose < (6.25*60*60) and self.timeToClose > (4.5*60*60)) or (self.timeToClose < (3*60*60)): #9:45-11:30, and 1-3:45
                current_barset = self.alpaca.get_barset(self.stocks,'1Min')
                if self.position:
                    print('\nLooking to sell')
                    alpaca_pos = self.alpaca.list_positions()[0]
                    pos_barset = current_barset[self.position['symbol']]
                    price = pos_barset[-1].c #lastest close price
                    vwap = self.get_vwap(pos_barset, 10) #Get 10 day vwap somehow using barset data
                    signal = self.get_engulfing_pattern_signals(pos_barset)
                    pl = float(alpaca_pos.unrealized_pl)

                    #Sell indicators
                    cross_vwap = price >= vwap
                    take_profit = pl >= 200
                    bear_signal = signal < 0
                    stop_loss = pl <= 100

                    if cross_vwap or take_profit or bear_signal or stop_loss:
                        self.submitOrder(self.position['symbol'], self.position['qty'],'sell')
                        self.position = None
                else:
                    print('\nLooking to Buy')
                    current_barset = self.alpaca.get_barset(self.stocks,'1Min')
                    for ticker in self.stocks:
                        tick_barset = current_barset[ticker]
                        if len(tick_barset) > 0:
                            candle = tick_barset[-1]
                            price = (candle.c + candle.o +candle.h + candle.l)/4 #Average price
                            vwap = self.get_vwap(tick_barset, 10)
                            signal = self.get_engulfing_pattern_signals(tick_barset)

                            #Buy Signals
                            bull_signal = signal > 0
                            below_vwap = price < vwap

                            if (bull_signal and below_vwap) and not self.position:
                                buying_power = float(self.alpaca.get_account().cash)
                                qty = buying_power//price
                                self.submitOrder(ticker, qty, 'buy')
                                self.position = {'symbol':ticker, 'qty':qty, 'buy_price':price}
            time.sleep(60)

    def get_vwap(self, bars, span):
        sum_volume = 0
        sum_vol_times_price = 0
        for i in range(span):
            sum_volume += bars[-1-i].v
            sum_vol_times_price += bars[-1-i].v * bars[-1-i].c
        return sum_vol_times_price/sum_volume
    
    def get_engulfing_pattern_signals(self, bars):
        Open = []
        High = []
        Low = []
        Close = []
        for bar in bars:
            Open.append(bar.o)
            High.append(bar.h)
            Low.append(bar.l)
            Close.append(bar.c)
        
        df = pd.DataFrame()
        df['Open'] = Open
        df['High'] = High
        df['Low'] = Low
        df['Close'] = Close
        df['Engullfing Pattern'] = talib.CDLENGULFING(df['Open'], df['High'], df['Low'], df['Close'])

        return df['Engullfing Pattern'][len(df)-1]

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
        #update barset data
        self.previous_barset = self.alpaca.get_barset(self.stocks,'1Min').df[:-1]
    
    def updateClock(self):
        # Figure out when the market will close so we can prepare to sell beforehand.
        clock = self.alpaca.get_clock()
        closingTime = clock.next_close.replace(tzinfo=dt.timezone.utc).timestamp()
        currTime = clock.timestamp.replace(tzinfo=dt.timezone.utc).timestamp()
        self.timeToClose = closingTime - currTime
    
    def onMarketClose(self):
        # Close all positions when 15 minutes til market close.
        print("Market closing soon.  Closing positions.")
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
                print("Market order of | " + str(qty) + " " + ticker + " " + side + " | completed.")
            except:
                print("Order of | " + str(qty) + " " + ticker + " " + side + " | did not go through.")
        else:
            print("Quantity is 0, order of | " + str(qty) + " " + ticker + " " + side + " | not completed.")
                
strat = Strategy()
strat.run()