from requests.api import get
from modules.oanda_api import get_candlestick_data
from modules.indicators import CMF,RSI,EMA, WaveTrend,supertrend
from talib import RSI as RSI2
import matplotlib.pyplot as plt

df = get_candlestick_data("EUR_USD",400,"M5")
EMA(df,200)
EMA(df,50)
RSI(df)
CMF(df)
WaveTrend(df) #tci, wt2
df['RSI2'] = RSI2(df['Close'])
df['strend1'],_,_ = supertrend(df['High'],df['Low'],df['Close'],12,3)
df['strend2'],_,_ = supertrend(df['High'],df['Low'],df['Close'],11,2)
df['strend3'],_,_ = supertrend(df['High'],df['Low'],df['Close'],10,1)


plt.subplot(3,1,1)
plt.plot(df['Close'])
plt.plot(df['EMA 200'],color='grey',alpha=0.5)
plt.plot(df['EMA 50'],color='yellow',alpha=0.5)
plt.plot(df['strend1'],color='grey',alpha=0.5)
plt.plot(df['strend2'],color='grey',alpha=0.5)
plt.plot(df['strend3'],color='grey',alpha=0.5)

plt.subplot(3,1,2)
plt.plot(df['tci'])
plt.plot(df['wt2'])

plt.subplot(3,1,3)
plt.title('RSI')
plt.plot(df['RSI'])

plt.show()





