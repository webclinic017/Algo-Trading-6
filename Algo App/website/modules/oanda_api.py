import requests
import json
import pandas as pd
import datetime as dt

rest_url = "https://api-fxpractice.oanda.com/"
stream_url = "https://stream-fxpractice.oanda.com/"
access_token = "7504cc953a3efe6542a1b0181f7a69b0-f5e662a814de4b0d43ea9c206a8e44ce"
account_id = "101-001-17749174-001"
authorization_header = {'Authorization':f'Bearer {access_token}','Accept-Datetime-Format':'UNIX', 'Content-type':'application/json'}

def calculate_qty(price,stop_loss,instrument,risk_pct=0.01,balance=10_000):
    if instrument[:3] == "USD": #Then USD value is 
        risk_amt = balance * risk_pct
        per_share_risk = price-stop_loss
        return risk_amt//(per_share_risk/price)
    elif instrument[-3:] == "USD": #Then price 
        risk_amt = balance * risk_pct
        per_share_risk = price-stop_loss
        return risk_amt//per_share_risk
    else:
        print('Pair does not contain USD')
        return 0

def get_candlestick_data(instrument,periods,granularity):
    """Returns pandas dataframe of ohlc and volume data"""
    end_point = f"v3/instruments/{instrument}/candles?granularity={granularity}&count={periods}"
    r = requests.get(rest_url+end_point, headers=authorization_header)
    if "errorMessage" in json.loads(r.text).keys():
        print('Error retrieving data')
    else:
        dic = json.loads(r.content)
        candles = dic['candles']
        df = pd.DataFrame()
        df['Open'] = [float(candle['mid']['o']) for candle in candles]
        df['High'] = [float(candle['mid']['h']) for candle in candles]
        df['Low'] = [float(candle['mid']['l']) for candle in candles]
        df['Close'] = [float(candle['mid']['c']) for candle in candles]
        df['Volume'] = [float(candle['volume']) for candle in candles]
        df.index = [dt.datetime.fromtimestamp(float(candle['time'])) for candle in candles]
        return df

def get_balance():
    """Returns float representing available cash"""
    end_point = f"v3/accounts/{account_id}"
    r = requests.get(rest_url+end_point, headers=authorization_header)
    return float(json.loads(r.content)['account']['balance'])

def get_account():
    end_point = f"v3/accounts/{account_id}"
    r = requests.get(rest_url+end_point, headers=authorization_header)
    return json.loads(r.content)['account']

def get_positions():
    get_account()['openPositionCount']

def limit_order(instrument, price, qty, stop_loss, take_profit):
    end_point = f"v3/accounts/{account_id}/orders"
    if price >= 10:
        price = round(price,3)
        stop_loss = round(stop_loss,3)
        take_profit = round(take_profit,3)
        qty = qty * 100
    else:
        price = round(price,5)
        stop_loss = round(stop_loss,5)
        take_profit = round(take_profit,5)
    data = {
        "order": {
            "price": str(price),
            "stopLossOnFill": {
                "timeInForce": "GTC",
                "price": str(stop_loss)
            },
            "takeProfitOnFill": {
                "price": str(take_profit)
            },
            "timeInForce": "GTD",
            "gtdTime" : str(dt.datetime.now() + dt.timedelta(minutes=5)),
            "instrument": instrument,
            "units": str(qty),
            "type": "LIMIT",
            "positionFill": "DEFAULT"
        }
    }
    r = requests.post(rest_url+end_point, json=data, headers=authorization_header)
    print(r)
    dic = json.loads(r.text)
    if 'errorMessage' in dic.keys():
        print(f'\tUnable to complete order for | {qty} | {instrument} | stoploss:{stop_loss} | takeprofit:{take_profit}')
    else:
        print(f'\tLimit Order for | {qty} | {instrument} | stoploss:{stop_loss} | takeprofit:{take_profit} | completed')

def market_order(instrument, qty, stop_loss, take_profit):
    """Sends market order, FOK: filled or killed"""
    if stop_loss >= 10:
        stop_loss = round(stop_loss,3)
        take_profit = round(take_profit,3)
        qty = qty * 100
    else:
        stop_loss = round(stop_loss,5)
        take_profit = round(take_profit,5)
    end_point = f"v3/accounts/{account_id}/orders"
    data =  {"order": {
                "stopLossOnFill": {
                  "timeInForce": "GTC",
                  "price": str(stop_loss)
                },
                "takeProfitOnFill": {
                  "price": str(take_profit)
                },
                "units": str(qty),
                "instrument": instrument,
                "timeInForce": "FOK",
                "type": "MARKET",
                "positionFill": "DEFAULT"}
            }
    r = requests.post(rest_url+end_point, json=data, headers=authorization_header)
    print(r)
    dic = json.loads(r.text)
    if 'errorMessage' in dic.keys():
        print(f'\tUnable to complete order for | {qty} | {instrument} | stoploss:{stop_loss} | takeprofit:{take_profit}')
    else:
        print(f'\tMarket Order for | {qty} | {instrument} | stoploss:{stop_loss} | takeprofit:{take_profit} | completed')
