import requests
import json
import datetime as dt
import pandas as pd

class ClientREST:

    BASE_URL = "https://api-fxpractice.oanda.com/"

    def __init__(self, **kwargs):
        self.access_token = kwargs.get('access_token')
        self.account_id = kwargs.get('account_id')
        self.auth_header = {
            'Authorization':f'Bearer {self.access_token}',
            'Accept-Datetime-Format':'UNIX', 
            'Content-type':'application/json'
        }

    #Account Endpoints
    def get_accounts(self):
        response = requests.get(f'{self.BASE_URL}v3/accounts', headers=self.auth_header)
        return json.loads(response.text)
    
    def get_summary(self):
        response = requests.get(f'{self.BASE_URL}v3/summary', headers=self.auth_header)
        return json.loads(response.text)
    
    def get_instruments(self):
        response = requests.get(f'{self.BASE_URL}v3/instruments', headers=self.auth_header)
        return json.loads(response.text)

    #Instrument Endpoints
    def get_candlestick_data(self, instrument,periods,granularity,_from=None,to=None):
        """Returns pandas dataframe of ohlc and volume data"""
        if _from:
            end_point = f"v3/instruments/{instrument}/candles?granularity={granularity}&count={periods}&from={_from}"
        elif to:
            end_point = f"v3/instruments/{instrument}/candles?granularity={granularity}&count={periods}&to={to}"
        else:
            end_point = f"v3/instruments/{instrument}/candles?granularity={granularity}&count={periods}"
        response = requests.get(self.BASE_URL+end_point, headers=self.auth_header)
        data = json.loads(response.content)
        if "errorMessage" in data.keys():
            print('Error retrieving data')
        else:
            candles = data['candles']
            df = pd.DataFrame()
            df['Open'] = [float(candle['mid']['o']) for candle in candles]
            df['High'] = [float(candle['mid']['h']) for candle in candles]
            df['Low'] = [float(candle['mid']['l']) for candle in candles]
            df['Close'] = [float(candle['mid']['c']) for candle in candles]
            df['Volume'] = [float(candle['volume']) for candle in candles]
            df.index = [dt.datetime.fromtimestamp(float(candle['time'])) for candle in candles]
            return df

    def get_order_book(self, symbol):
        response = requests.get(f'{self.BASE_URL}v3/instruments/{symbol}/orderBook',headers=self.auth_header)
        return json.loads(response.content)

    def get_position_book(self, symbol):
        response = requests.get(f'{self.BASE_URL}v3/instruments/{symbol}/positionBook',headers=self.auth_header)
        return json.loads(response.content)

    #Order Endpoints
    def market_order(self, instrument, qty, stop_loss, take_profit):
        """Sends market order, FOK: filled or killed"""
        if stop_loss >= 10:
            stop_loss = round(stop_loss,3)
            take_profit = round(take_profit,3)
        else:
            stop_loss = round(stop_loss,5)
            take_profit = round(take_profit,5)
        end_point = f"v3/accounts/{self.account_id}/orders"
        data =  {
            "order": {
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
                "positionFill": "DEFAULT"
            }
        }
        response = requests.post(self.BASE_URL+end_point, json=data, headers=self.auth_header)
        print(response)
        dic = json.loads(response.text)
        if 'errorMessage' in dic.keys():
            print(f'\tUnable to complete order for | {qty} | {instrument} | stoploss:{stop_loss} | takeprofit:{take_profit}')
        else:
            print(f'\tMarket Order for | {qty} | {instrument} | stoploss:{stop_loss} | takeprofit:{take_profit} | completed')
    
    def limit_order(self, instrument, price, qty, stop_loss, take_profit):
        if price >= 10:
            price = round(price,3)
            stop_loss = round(stop_loss,3)
            take_profit = round(take_profit,3)
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
        end_point = f"v3/accounts/{self.account_id}/orders"
        response = requests.post(self.BASE_URL+end_point, json=data, headers=self.auth_header)
        print(response)
        dic = json.loads(response.text)
        if 'errorMessage' in dic.keys():
            print(f'\tUnable to complete order for | {qty} | {instrument} | stoploss:{stop_loss} | takeprofit:{take_profit}')
        else:
            print(f'\tLimit Order for | {qty} | {instrument} | stoploss:{stop_loss} | takeprofit:{take_profit} | completed')

    def stop_order(self, instrument, price, qty, stop_loss, take_profit):
        if price >= 10:
            price = round(price,3)
            stop_loss = round(stop_loss,3)
            take_profit = round(take_profit,3)
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
                "timeInForce": "GTC",
                "instrument": instrument,
                "units": str(qty),
                "clientExtensions": {
                    "id": "myorder"
                },
                "type": "STOP",
                "positionFill": "DEFAULT"
            }
        }
        end_point = f"v3/accounts/{self.account_id}/orders"
        response = requests.post(self.BASE_URL+end_point, json=data, headers=self.auth_header)
        print(json.loads(response.text))
        dic = json.loads(response.text)
        if 'errorMessage' in dic.keys():
            print(f'\tUnable to complete order for | {qty} | {instrument} | stoploss:{stop_loss} | takeprofit:{take_profit}')
        else:
            print(f'\Stop Order for | {qty} | {instrument} | stoploss:{stop_loss} | takeprofit:{take_profit} | completed')

    def cancel_order(self,orderid='myorder'):
        response = requests.put(f'{self.BASE_URL}v3/accounts/{self.account_id}/orders/@{orderid}/cancel', 
            headers=self.auth_header)
        print(response)

    def get_orders(self):
        response = requests.get(f'{self.BASE_URL}v3/accounts/{self.account_id}/orders', 
            headers=self.auth_header)
        return json.loads(response.text)

    def get_pending_orders(self):
        response = requests.get(f'{self.BASE_URL}v3/accounts/{self.account_id}/pendingOrders', 
            headers=self.auth_header)
        return json.loads(response.text)

    #Trade Endpoints
    def get_trades(self,ins):
        response = requests.get(f'{self.BASE_URL}v3/accounts/{self.account_id}/trades?instrument={ins}', 
            headers=self.auth_header)
        return json.loads(response.text)

    def get_open_trades(self):
        response = requests.get(f'{self.BASE_URL}v3/accounts/{self.account_id}/openTrades', 
            headers=self.auth_header)
        return json.loads(response.text)

    #Position Endpoints
    def get_positions(self):
        response = requests.get(f'{self.BASE_URL}v3/accounts/{self.account_id}/positions', 
            headers=self.auth_header)
        return json.loads(response.text)

    def get_open_positions(self):
        response = requests.get(f'{self.BASE_URL}v3/accounts/{self.account_id}/openPositions', 
            headers=self.auth_header)
        return json.loads(response.text)

    #Helper functions
    def calculate_qty(self,price,stop_loss,instrument,risk_pct=0.01,balance=10_000):
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
    
    def get_balance(self):
        """Returns float representing available cash"""
        end_point = f"v3/accounts/{self.account_id}"
        r = requests.get(self.BASE_URL+end_point, headers=self.auth_header)
        return float(json.loads(r.content)['account']['balance'])