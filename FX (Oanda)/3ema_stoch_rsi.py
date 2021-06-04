from modules.oanda_api import get_candlestick_data
from modules.indicators import EMA, ATR, STOCH_RSI
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def backtest(df,instrument):
    """
    Creates two columns, 'buy' and 'sell', in df, indicating buy and sell signals of algorithm.
    Assumes df contains necessary columns for algorithm
    """
    #Backtest metrics
    buy, sell = [np.nan]*len(df),[np.nan]*len(df) #Buy sell signals to plot
    wins, losses = 0,0 #Number of wining/losing trades
    consec_wins, consec_losses = 0,0 #Used for max_wins and max_losses
    max_wins, max_losses = 0,0 #Most wins/losses in a row
    cash = 100000 #Initial starting cash
    profit_history = np.zeros(len(df))
    
    #Backtest loop
    pos = None
    for i,row in df.iterrows():
        #Candle data
        o,h,l,c = row['Open'],row['High'],row['Low'],row['Close']
        
        #Strategy
        ###########################################################
        ema8,ema14,ema50 = row['EMA 8'],row['EMA 14'],row['EMA 50']
        prev_srsi = row['stoch_rsi']
        prev_srsi_slow = row['stoch_rsi_ma']
        cur_srsi = row['stoch_rsi']
        cur_srsi_slow = row['stoch_rsi_ma']
        atr = row['ATR']

        #Long conditions
        l1 = ema8 > ema14 and ema14 > ema50 #Uptrend
        l2 = c > ema8 #Candle closes above shortest ema
        l3 = prev_srsi_slow <= prev_srsi and cur_srsi_slow >= cur_srsi #Stochastic cross up

        if l1 and l2 and l3 and not pos:
            stop_loss = c - 3*atr
            take_profit = c + 2*atr
            qty = (c - stop_loss)/(0.02*cash)
            pos = {
                'type' : 'LONG',
                'take_profit' : take_profit,
                'stop_loss' : stop_loss,
                'qty' : qty
            }
            buy[i] = c

        #Short conditions
        s1 = ema8 < ema14 and ema14 < ema50 #Downtrend
        s2 = c < ema8 #Candle closes below shortest ema
        s3 = prev_srsi_slow >= prev_srsi and cur_srsi_slow <= cur_srsi #Stochastic cross down

        if s1 and s2 and s3 and not pos:
            stop_loss = c + 3*atr
            take_profit = c - 2*atr
            qty = (stop_loss - c)/(0.02*cash)
            pos = {
                'type' : 'SHORT',
                'take_profit' : take_profit,
                'stop_loss' : stop_loss,
                'qty' : qty
            }
            sell[i] = c

        elif pos:
            if pos['type'] == 'LONG':
                if h >= pos['take_profit']:
                    wins += 1
                    consec_wins += 1
                    consec_losses = 0
                    if consec_wins > max_wins: max_wins = consec_wins
                    pos = None
                    sell[i] = c
                    cash += round(0.02*(2/3),2)*cash 
                elif l <= pos['stop_loss']:
                    losses += 1
                    consec_losses += 1
                    consec_wins = 0
                    if consec_losses > max_losses: max_losses = consec_losses
                    pos = None
                    sell[i] = c
                    cash -= 0.02*cash

            elif pos['type'] == 'SHORT':
                if l <= pos['take_profit']:
                    wins += 1
                    consec_wins += 1
                    consec_losses = 0
                    if consec_wins > max_wins: max_wins = consec_wins
                    pos = None
                    buy[i] = c
                    cash += round(0.02*(2/3),2)*cash 
                elif h >= pos['stop_loss']:
                    losses += 1
                    consec_losses += 1
                    consec_wins = 0
                    if consec_losses > max_losses: max_losses = consec_losses
                    pos = None
                    buy[i] = c
                    cash -= 0.02*cash
        profit_history[i] = cash

    print(f'Wins: {wins}')
    print(f'Losses: {losses}')
    print(f'Win percentage: {round(100*(wins/(wins+losses))) if wins+losses > 0 else 0}%')
    print(f'Wins in a row: {max_wins}')
    print(f'Losses in a row: {max_losses}')
    print(f'Gain on account: {round((2*(2/3)*wins)-(2*losses),2)}%')

    plt.plot(df['Close'])
    plt.plot(df['EMA 8'])
    plt.plot(df['EMA 14'])
    plt.plot(df['EMA 50'])
    plt.plot(df.index,buy,marker='^',color='g')
    plt.plot(df.index,sell,marker='v',color='r')
    plt.title(f'Buy and Sell signals : {instrument}')
    plt.xlabel('Date')
    plt.ylabel('Close Price')
    plt.show()

    plt.plot(df.index,profit_history)
    plt.show()

if __name__ == "__main__":
    for instrument in ['EUR_USD',"AUD_USD",'GBP_USD','USD_JPY','EUR_JPY']:
        data = get_candlestick_data(instrument,5000,'M1')
        EMA(data, 8)
        EMA(data, 14)
        EMA(data, 50)
        ATR(data)
        STOCH_RSI(data)
        data.reset_index(inplace=True)
        backtest(data,instrument)

