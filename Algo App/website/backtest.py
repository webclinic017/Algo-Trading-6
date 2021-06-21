from modules.oanda_api import limit_order, get_candlestick_data, get_balance, get_account
from talib import STOCHRSI, ATR
import datetime as dt
import matplotlib.pyplot as plt
import numpy as np

def bull_emas(df,short=8,med=14,long=50):
    """
    [bull_ema] creates columns "Bull_EMAs" and "Bear_EMAs" in [df].  Bull_EMAs 
    is a list of highs when EMA of length [short] is greater than EMA of length 
    [med] and EMA of length [med] is greater than EMA of length [long] and 
    np.nan if that condition is not true.  Bear_EMAs is a list of lows when 
    EMA of length [short] is less than EMA of length [med] and EMA of length 
    [med] is less than EMA of length [long] and np.nan if that condition is 
    not true.

    Note: assumes the columns "EMA {short}", "EMA {med}", and "EMA {long}" are
    in [df]
    """
    bull = [np.nan]*len(df)
    bear = [np.nan]*len(df)
    for i in range(len(df)):
        if df[f'EMA {short}'][i] > df[f'EMA {med}'][i] and df[f'EMA {med}'][i] > df[f'EMA {long}'][i]:
            bull[i] = df['High'][i]
        elif df[f'EMA {short}'][i] < df[f'EMA {med}'][i] and df[f'EMA {med}'][i] < df[f'EMA {long}'][i]:
            bear[i] = df['Low'][i]

    df['Bull_EMAs'] = bull
    df['Bear_EMAs'] = bear

def stochastic_cross_thresh(df,bull_thresh=30,bear_thresh=70):
    """
    [stochastic_cross] creates columns "Bull_cross" and "Bear_cross" in [df].  
    Bull_cross is a list of highs when the stochastic crosses below [bull_thresh]
    in the upwards direction and Bear_cross is a list of lows when the stochastic 
    cross above [bear_thresh] and in the downwards direction.

    Note: assumes the columns "Stoch" and "Stoch_ma are in [df]
    """
    bull = [np.nan]*len(df)
    bear = [np.nan]*len(df)
    for i in range(1,len(df)):
        if df['Stoch'][i-1] <= df['Stoch_ma'][i-1] and df['Stoch'][i] > df['Stoch_ma'][i] and df['Stoch'][i] < bull_thresh:
            bull[i] = df['High'][i]
        elif df['Stoch'][i-1] >= df['Stoch_ma'][i-1] and df['Stoch'][i] < df['Stoch_ma'][i] and df['Stoch'][i] > bear_thresh:
            bear[i] = df['Low'][i]

    df['Bull_cross'] = bull
    df['Bear_cross'] = bear

def rolling_high_low(df,period=10):
    """
    [rolling_high_low] creates columns "Roll High" and "Roll Low" which 
    indicate the highs and lows of the past [period] candles.
    """
    df['Roll High'] = df['High'].rolling(period).max()
    df['Roll Low'] = df['Low'].rolling(period).min()

def buy_sell(df):
    """
    [buy_sell] creates columns "buy" and "sell" which 
    """
    buy, sell = [np.nan]*len(df),[np.nan]*len(df)
    for i in range(len(df)):
        if (not np.isnan(df['Bull_EMAs'][i])) and (not np.isnan(df['Bull_cross'][i])):
            buy[i] = df['High'][i]
        if (not np.isnan(df['Bear_EMAs'][i])) and (not np.isnan(df['Bear_cross'][i])):
            sell[i] = df['High'][i]
    df['Buy'] = buy
    df['Sell'] = sell

###################################################################################
###################################### tests ######################################
###################################################################################
test = get_candlestick_data('EUR_USD',400,"M5")
test['EMA 8'] = test['Close'].ewm(8).mean()
test['EMA 14'] = test['Close'].ewm(14).mean()
test['EMA 50'] = test['Close'].ewm(50).mean()
test['Stoch'],test['Stoch_ma'] = STOCHRSI(test['Close'])
#Conditions
bull_emas(test)
stochastic_cross_thresh(test)
rolling_high_low(test)
buy_sell(test)

# #Test of bull_emas
# plt.plot(test['Close'])
# plt.plot(test['EMA 8'],alpha=0.5)
# plt.plot(test['EMA 14'],alpha=0.5)
# plt.plot(test['EMA 50'],alpha=0.5)
# plt.plot(test['Bull_EMAs'],color='g')
# plt.plot(test['Bear_EMAs'],color='r')
# plt.show()

# #Test of stochastic_cross_thresh
# plt.subplot(2,1,1)
# plt.plot(test['Close'])
# plt.plot(test['EMA 8'],alpha=0.5)
# plt.plot(test['EMA 14'],alpha=0.5)
# plt.plot(test['EMA 50'],alpha=0.5)
# plt.plot(test['Bull_cross'],marker='^',color='g')
# plt.plot(test['Bear_cross'],marker='v',color='r')
# plt.subplot(2,1,2)
# plt.plot(test['Stoch'])
# plt.plot(test['Stoch_ma'])
# plt.plot(test.index,[70]*len(test),'--',color='grey',alpha=0.5)
# plt.plot(test.index,[30]*len(test),'--',color='grey',alpha=0.5)
# plt.show()

# #Test of rolling_high_low
# plt.plot(test['Close'])
# plt.plot(test['Roll High'],color='g')
# plt.plot(test['Roll Low'],color='r')
# plt.show()

#Testv buy and sell
plt.plot(test['Close'])
plt.plot(test.index,test['Buy'],marker='^',color='g')
plt.plot(test.index,test['Sell'],marker='v',color='r')
plt.show()