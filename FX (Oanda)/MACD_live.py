from api import get_candlestick_data, market_order, get_balance, get_positions
import time
import datetime as dt

class Strategy():
    def __init__(self):
        self.instruments = ['EUR_USD',
                            'USD_JPY',
                            'GBP_USD',
                            'USD_CAD',
                            'AUD_USD',
                            'NZD_USD',
                            'USD_CHF',
                            'EUR_JPY',
                            'EUR_GBP',
                            'EUR_CHF',
                            'EUR_SEK',
                            'EUR_NOK',
                            'GBP_JPY']
        self.data = self.update_data()

    def run(self):
        print('Starting algorithm')
        while True:
            self.update_data() #Get most current data
            if len(get_positions()) == 0:
                print(f'Looking for position | {dt.datetime.now().strftime("%H:%M:%S")}')
                for instrument in self.instruments:
                    df = self.data[instrument]
                    #Data necessary for signals
                    c = df['Close'][-1]
                    prev_macd = df['MACD'][-2]
                    prev_signal = df['Signal'][-2]
                    macd = df['MACD'][-1]
                    signal = df['Signal'][-1]
                    ema = df['EMA200'][-1]
                    atr = df['ATR'][-1]

                    #Long signals
                    above_ema = c > ema
                    macd_below_zero = macd < 0
                    macd_cross_up = macd >= signal and prev_macd <= prev_signal

                    #Short signals
                    below_ema = c < ema
                    macd_above_zero = macd > 0
                    macd_cross_down = macd <= signal and prev_macd >= prev_signal

                    if above_ema and macd_below_zero and macd_cross_up and len(get_positions()) == 0:
                        stop_loss = c - 2*atr
                        take_profit = c + 3*atr
                        qty = 0.75*get_balance()//c
                        market_order(instrument, qty, stop_loss, take_profit) #1.5 profit/loss
                    elif below_ema and macd_above_zero and macd_cross_down and len(get_positions()) == 0:
                        stop_loss = c + 2*atr
                        take_profit = c - 3*atr
                        qty = -0.75*get_balance()//c
                        market_order(instrument, qty, stop_loss, take_profit) #1.5 profit/loss

            print('sleeping for 1 min')
            time.sleep(56)
        else:
            print('Position waiting for stop_loss or take_profit')
            time.sleep(60)


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

    def update_data(self):
        """Updates data to most recent candles with indicators"""
        d = {}
        for pair in self.instruments:
            temp = get_candlestick_data(instrument=pair)
            #Add indicators to the data
            self.MACD(temp)
            self.EMA200(temp)
            self.ATR(temp)
            d[pair] = temp
        return d

s = Strategy()
s.run()
