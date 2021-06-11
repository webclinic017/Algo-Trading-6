from requests.api import get
from modules.oanda_api import get_candlestick_data
import matplotlib.pyplot as plt

instruments = [
            'USD_CAD','EUR_USD','USD_CHF','GBP_USD','NZD_USD',
            'AUD_USD','USD_JPY','EUR_CAD','EUR_AUD','EUR_JPY',
            'EUR_CHF','EUR_GBP','AUD_CAD','GBP_CHF','GBP_JPY',
            'CHF_JPY','AUD_JPY','AUD_NZD'
        ]

# dic = {}
# for ins in instruments:
#     temp = get_candlestick_data(ins,5000,"M5")
#     temp['EMA 50'] = temp['Close'].ewm(50).mean()
#     temp['EMA 100'] = temp['Close'].ewm(100).mean()
#     temp['EMA 150'] = temp['Close'].ewm(150).mean()
#     dic[ins] = temp

params = {
    "slow_ema_period" : 50,
    "med_ema_period" : 100,
    "long_ema_period" : 150,
    "reward_to_risk_multiplier" : 2,
    "risk_pct" : 2
}

def backtest_sell_half_at_1_to_1(df):
    """
    Strategy: 
    50, 100, and 150 EMA's.
    When all EMA's are in order and at positive angle, wait for price pullback below 50 and/or 100 EMA.
    CANNOT close below 100 EMA during pullback.  Wait for confirmation of bounce when price closes above
    50 EMA, buy at close.  Place stop loss at low of pullback, at 1:1 profit sell half and move stop to 
    break even.

    Ideas
    - Try different ema periods
    - Try different risk managment
    """
    wins, losses = 0, 0
    max_wins, max_losses = 0, 0
    cur_wins, cur_losses = 0, 0
    init_cash = 100_000
    cash = init_cash
    pct_change = [0]*len(df)
    pos = None

    sold_half = False
    for i in range(16,len(df)):
        c = df['Close'][i]
        short_ema = df['EMA 50'][i]
        med_ema = df['EMA 100'][i]
        long_ema = df['EMA 150'][i]

        emas_in_order = (short_ema > med_ema and med_ema > long_ema)
        pullback = False
        below_long = False
        if emas_in_order:
            recent = df.iloc[i-16:]
            above_emas = False
            for i in range(len(recent)):
                if recent['Low'][i] > recent['EMA 50'][i]:
                    above_emas = True
                if above_emas and recent['Close'][i] < recent['EMA 50'][i]:
                    pullback = True
                if recent['Low'][i] < recent['EMA 150'][i]:
                    below_long = True

        if emas_in_order and pullback and not below_long and not pos:
            sl = min([df['Low'][i-di] for di in range(16)])
            tp1 = c + (c - sl) #1:1
            tp2 = c + (2 * (c - sl))
            qty = 1 #TODO: Figure out how to convert difference to USD
            pos = {"buy_price": c,"stop_loss" : sl, "take_profit1" : tp1, "take_profit2" : tp2, "qty" : qty}
        elif pos:
            if c >= pos["take_profit1"] and not sold_half:
                cash += params["risk_pct"]/2
                sold_half = True
                pos["stop_loss"] = pos["buy_price"]
                wins += 1
            elif c >= pos["take_profit2"] and sold_half:
                cash += params['risk_pct']
                sold_half = False
                pos = None
            elif c <= pos["stop_loss"]:
                cash -= params["risk_pct"]
                sold_half = False
                pos = None
                losses += 1
        
        #Update backtest metrics
        pct_change[i] = cash / init_cash

    print(f"Wins:{wins}")
    print(f"Losses:{losses}")

    plt.subplot(2,1,1)
    plt.plot(df['Close'])
    plt.plot(df['EMA 50'])
    plt.plot(df['EMA 100'])
    plt.plot(df['EMA 150'])

    plt.subplot(2,1,2)
    plt.plot(df.index,pct_change)
    plt.show()


EUR_USD = get_candlestick_data("EUR_USD",5000,"M5")
EUR_USD['EMA 50'] = EUR_USD["Close"].ewm(50).mean()
EUR_USD['EMA 100'] = EUR_USD["Close"].ewm(100).mean()
EUR_USD['EMA 150'] = EUR_USD["Close"].ewm(150).mean()
EUR_USD.dropna(inplace=True,axis=0)
print(EUR_USD)
backtest_sell_half_at_1_to_1(EUR_USD)
