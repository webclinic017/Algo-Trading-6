from oanda_api import ClientREST as API

api = API(
    access_token = "7504cc953a3efe6542a1b0181f7a69b0-f5e662a814de4b0d43ea9c206a8e44ce",
    account_id = "101-001-17749174-001"
    )

#Getting data`
df = api.get_candlestick_data("EUR_USD",100,"M5")

#Market order with stoploss and takeprofit
#api.market_order('EUR_USD',100)

#Market order with trailing stop
api.market_order("EUR_USD",100,trailing_stop=0.0005,take_profit=df['Close'][-1]+0.001)


class CipherB:
    def __init__(self,candle_span='M15'):
        self.instrument = 'EUR_USD'
        self.candle_span = candle_span
        self.update_data()
        self.atr_mult = 1
        self.rr_mult = 5
        self.run = False

    def update_data(self):
        data = api.get_candlestick_data(self.instrument,300,self.candle_span)
        #Add indicators to data here
        data['EMA 200'] = data['Close'].ewm(200).mean()
        data['EMA 50'] = data['Close'].ewm(50).mean()
        cipherB(data)
        ATR(data)

        #Condition 1 (Above/Below 200 EMA and 50 EMA above below 200 EMA)
        bull_condition1 = (data['Close'] > data['EMA 200']) & (data['EMA 50'] > data['EMA 200'])
        bear_condition1 = (data['Close'] < data['EMA 200']) & (data['EMA 50'] < data['EMA 200'])

        #Condtion 2 (Pullback to 50 EMA)
        bull_condition2 = np.array([False]*len(data))
        bear_condition2 = np.array([False]*len(data))

        lookback = 10
        for i in range(len(data) - lookback, len(data)):
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
                        api.market_order(self.instrument,qty,trailing_stop=c-stop_loss,take_profit=take_profit)
                        alert("Long Signal","Cipher B Long","8452697031@mms.att.net")
                        print("\tLong Signal Detected")
                    elif len(api.get_orders()['orders']) == 0 and df['Sell'][-1]:
                        stop_loss = c + self.atr_mult * df['ATR'][-1]
                        take_profit = c - self.rr_mult*(stop_loss-c)
                        qty = api.calculate_qty(c,stop_loss,"EUR_USD",balance=api.get_balance())
                        api.market_order(self.instrument,qty,trailing_stop=stop_loss-c,take_profit=take_profit)
                        alert("Short Signal","Cipher B Short","8452697031@mms.att.net")
                        print("Short Signal Detected")
                    else:
                        print('\tNo Signals found')
            print('\nStopping Cipher B Algorithm...')

        except Exception as e:
            print(e)
            print('\nAn error occured, restarting...')
            self.start()
