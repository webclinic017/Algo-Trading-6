from modules.oanda_api import get_candlestick_data
import matplotlib.pyplot as plt
import numpy as np

df = get_candlestick_data("EUR_USD",300,"M5")
df['SMA 5'] = df['Close'].rolling(5).mean()
df['Roll High'] = df['High'].rolling(5).max()
df['Roll Low'] = df['Low'].rolling(5).min()

df['Buy'] = df['Close'] > df['SMA 5']
df['Sell'] = df['Close'] < df['SMA 5']
df['Buy'] = np.where(df['Buy'] == True,df['Close'],np.nan)
df['Sell'] = np.where(df['Sell'] == True,df['Close'],np.nan)
print(df)

wins,losses = 0,0
pos = None
accum = [0]*len(df)
buy,sell = [np.nan]*len(df),[np.nan]*len(df)
for i in range(1,len(df)):
    accum[i] = accum[i-1]

    prev_buy = df['Buy'][i-1]
    b = df['Buy'][i]
    prev_sell = df['Sell'][i-1]
    s = df['Sell'][i]
    c = df['Close'][i]
    roll_high = df['Roll High'][i]
    roll_low = df['Roll Low'][i]

    if not pos and np.isnan(prev_buy) and (not np.isnan(b)):
        pos = {"type": 'long',"stop" : roll_low,"take":(c - roll_low) + c}
        buy[i] = c
        print('Bought')
    elif not pos and np.isnan(prev_sell) and (not np.isnan(s)):
        pos = {"type":"short","stop" : roll_high,"take":c - (-c + roll_low)}
        sell[i] = c
        print('Sold')
    
    elif pos and pos['type'] == 'long':
        if pos and c <= pos['stop']:
            pos = None
            accum[i] = accum[i-1] - .02
            losses += 1
            sell[i] = c
            print('Closed')
        elif pos and c >= pos['take']:
            pos = None
            accum[i] = accum[i-1] + .02
            wins += 1
            sell[i] = c
            print('Closed')
    elif pos and pos['type'] == 'short':
        if pos and c >= pos['stop']:
            pos = None
            accum[i] = accum[i-1] - .02
            losses += 1
            buy[i] = c
            print('Closed')
        elif pos and c <= pos['take']:
            pos = None
            accum[i] = accum[i-1] + .02
            wins += 1
            buy[i] = c
            print('Closed')

df['Buy'] = buy
df['Sell'] = sell

print(f"Wins:{wins}")
print(f"losses:{losses}")
print(f'Win %: {0 if wins + losses == 0 else 100 * wins/(wins+losses)}')

plt.figure(figsize=(16,8))
plt.subplot(2,1,1)
plt.title('Close price with signals')
plt.plot(df["Close"])
plt.plot(df['Buy'],marker='^',color='g')
plt.plot(df['Sell'],marker='v',color='r')

plt.subplot(2,1,2)
plt.title('Returns (%)')
plt.plot(df.index,accum)
plt.show()