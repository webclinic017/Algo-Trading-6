from modules.oanda_api import get_candlestick_data
import matplotlib.pyplot as plt
import numpy as np

df = get_candlestick_data("EUR_USD",500,"M5")

# Entry #1: Momentum and Big Range
# Idea: Go with momentum after big range bars
# - range = high - low
# - if range > 2 * std(range,period) + avg(range, period) AND
# close > close_bars_ago THEN long
# - if range > 2 * std(range,period) + avg(range, period) AND
# close < close_bars_ago THEN short
# - 2 Variables: period and daysback

def momentum_big_range(df,period=2,daysback=2):
    """
    [momentum_big_range] creates a [buy] and [sell] column in [df]
    """
    df['Range'] = df['High'] - df['Low']
    df['Roll Mean'] = df['Range'].rolling(period).mean()
    df['Roll STD'] = df['Range'].rolling(period).std()

    buy,sell = [np.nan]*len(df), [np.nan]*len(df)
    for i in range(period, len(df)):
        rang = df['Range'][i]
        std = df['Roll Mean'][i]
        avg = df['Roll STD'][i]

        if (rang > (2 * std + avg)) and df['Close'][i] > df['Close'][i-daysback] and not ((rang > (2 * std + avg)) and df['Close'][i-1] > df['Close'][i-1-daysback]):
            buy[i] = df['Close'][i]
        if (rang > (2 * std + avg)) and df['Close'][i] < df['Close'][i-daysback] and not ((rang > (2 * std + avg)) and df['Close'][i-1] < df['Close'][i-1-daysback]):
            sell[i] = df['Close'][i]
    
    df['Buy'], df['Sell'] = buy,sell

momentum_big_range(df,15,3)
plt.title("Momentum entry")
plt.plot(df['Close'])
plt.plot(df['Buy'],color='g',marker='^')
plt.plot(df['Sell'],color='r',marker='v')
plt.show()

# Entry #2: Breakout - Report Play
# Idea: Go with trend after a regular report
# - Definition: Report - Reaction after news that is significant, go with trend
# - if time == XXX then make two orders buy and sell +- 0.01
# - the above line is executed sometime before event
# If time == XXX then buy if price goes above the buy price from line above, and sell at sell price above
# - 1 variable: XXX
# - Hard part is determining reports
# - Natural Gas, weekly crude oil report, ag reports, c report

def breakout_report(df,time1,time2):
    pass

# Entry #3: Mean Reversion (stock market)
# - stock market tends to mean revert more often
# Idea: Look for low volume on reversal points
# - if volume < SMA5_volume then
# 	if close = lowest(close,len) then buy
# 	if close = highest(close, Len) then short
# - 1 variable: len

def mean_reversion(df,length=10):
    df['Roll Min'] = df['Close'].rolling(length).min()
    df['Roll Max'] = df['Close'].rolling(length).max()
    df['Volume SMA'] = df['Volume'].rolling(5).mean()
    buy,sell = [np.nan]*len(df), [np.nan]*len(df)
    for i in range(5,len(df)):
        volume = df['Volume'][i]
        mean_volume = df['Volume SMA'][i]
        close = df['Close'][i]

        if volume < mean_volume:
            if close  == df['Roll Min'][i] and not (df['Close'][i-1] == df['Roll Min'][i-1]):
                buy[i] = close
            if close == df['Roll Max'][i] and not (df['Close'][i-1] == df['Roll Max'][i-1]):
                sell[i] = close
    
    df['Buy'], df['Sell'] = buy,sell

mean_reversion(df)
plt.title('Mean reversion entry')
plt.subplot(2,1,1)
plt.plot(df['Close'])
plt.plot(df['Close'].ewm(200).mean())
plt.plot(df['Buy'],color='g',marker='^')
plt.plot(df['Sell'],color='r',marker='v')

plt.subplot(2,1,2)
plt.bar(df.index,df['Volume'])
plt.plot(df['Volume SMA'])
plt.show()


# Entry #4: Simple Breakout 
# - works well with trending stocks (FOREX)
# - if close = Highest(close,len) then buy
# - if close = Lowest(close,len) then short
# - 1 variable: Length

def breakout(df,length=20):
    df['Roll Min'] = df['Close'].rolling(length).min()
    df['Roll Max'] = df['Close'].rolling(length).max()
    buy,sell = [np.nan]*len(df), [np.nan]*len(df)
    for i in range(len(df)):
        if df['Close'][i] == df['Roll Min'][i] and not (df['Close'][i-1] == df['Roll Min'][i-1]):
            buy[i] = df['Close'][i]
        if df['Close'][i] == df['Roll Max'][i] and not (df['Close'][i-1] == df['Roll Max'][i-1]):
            sell[i] = df['Close'][i]

    df['Buy'], df['Sell'] = buy,sell

breakout(df)
plt.title('Breakout Entry')
plt.plot(df['Close'])
plt.plot(df['Buy'],color='g',marker='^')
plt.plot(df['Sell'],color='r',marker='v')
plt.show()

# Entry #5: Dueling Momentum
# Idea: Go with short momentum, against long momentum
# - if close>short_momentum and c < long_momentum then buy
# - if close < short momentum and c > long_momentum then short
# - 2 variables: short and long periods
