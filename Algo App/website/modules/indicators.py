import numpy as np
from scipy.signal import argrelmin,argrelmax

def ADX(df,n):
    "function to calculate ADX"
    df['TR'] = ATR(df)['TR'] #the period parameter of ATR function does not matter because period does not influence TR calculation
    df['DMplus']=np.where((df['High']-df['High'].shift(1))>(df['Low'].shift(1)-df['Low']),df['High']-df['High'].shift(1),0)
    df['DMplus']=np.where(df['DMplus']<0,0,df['DMplus'])
    df['DMminus']=np.where((df['Low'].shift(1)-df['Low'])>(df['High']-df['High'].shift(1)),df['Low'].shift(1)-df['Low'],0)
    df['DMminus']=np.where(df['DMminus']<0,0,df['DMminus'])
    TRn = []
    DMplusN = []
    DMminusN = []
    TR = df['TR'].tolist()
    DMplus = df['DMplus'].tolist()
    DMminus = df['DMminus'].tolist()
    for i in range(len(df)):
        if i < n:
            TRn.append(np.NaN)
            DMplusN.append(np.NaN)
            DMminusN.append(np.NaN)
        elif i == n:
            TRn.append(df['TR'].rolling(n).sum().tolist()[n])
            DMplusN.append(df['DMplus'].rolling(n).sum().tolist()[n])
            DMminusN.append(df['DMminus'].rolling(n).sum().tolist()[n])
        elif i > n:
            TRn.append(TRn[i-1] - (TRn[i-1]/14) + TR[i])
            DMplusN.append(DMplusN[i-1] - (DMplusN[i-1]/14) + DMplus[i])
            DMminusN.append(DMminusN[i-1] - (DMminusN[i-1]/14) + DMminus[i])
    df['TRn'] = np.array(TRn)
    df['DMplusN'] = np.array(DMplusN)
    df['DMminusN'] = np.array(DMminusN)
    df['DIplusN']=100*(df['DMplusN']/df['TRn'])
    df['DIminusN']=100*(df['DMminusN']/df['TRn'])
    df['DIdiff']=abs(df['DIplusN']-df['DIminusN'])
    df['DIsum']=df['DIplusN']+df['DIminusN']
    df['DX']=100*(df['DIdiff']/df['DIsum'])
    ADX = []
    DX = df['DX'].tolist()
    for j in range(len(df)):
        if j < 2*n-1:
            ADX.append(np.NaN)
        elif j == 2*n-1:
            ADX.append(df['DX'][j-n+1:j+1].mean())
        elif j > 2*n-1:
            ADX.append(((n-1)*ADX[j-1] + DX[j])/n)
    df['ADX']=np.array(ADX)

def ASH(df,mode='RSI',ma_type='WMA',length=9,smooth=3,alma_offset=0.85,alma_sigma=6):
    "Absolute Strength Histogram (ASH)"
    Price1 = df['Close'].rolling(1).mean()
    Price2 = df['Close'].shift(1).rolling(1).mean()

    #RSI
    Bulls0 = 0.5*(abs(Price1-Price2)+(Price1-Price2))
    Bears0 = 0.5*(abs(Price1-Price2)-(Price1-Price2))

    #STOCHASTIC
    Bulls1 = Price1 - Price1.rolling(length).min()
    Bears1 = Price1.rolling(length).max()- Price1

    #ADX
    Bulls2 = 0.5*(abs(df['High']-df['High'].shift(1))+(df['High']-df['High'].shift(1)))
    Bears2 = 0.5*(abs(df['Low'].shift(1)-df['Low'])+(df['Low'].shift(1)-df['Low']))

    df['Bulls'] = Bulls0 if mode == "RSI"  else (Bulls1 if mode == "STOCHASTIC" else Bulls2)
    df['Bears'] = Bears0 if mode == "RSI" else (Bears1 if mode == "STOCHASTIC" else Bears2)
    if ma_type == 'SMA': #Simple
        df['AvgBulls']=df['Bulls'].rolling(length).mean()
        df['SmthBulls'] = df['AvgBulls'].rolling(smooth).mean()
        df['AvgBears']=df['Bears'].rolling(length).mean()
        df['SmthBears'] = df['AvgBears'].rolling(smooth).mean()
    elif ma_type == 'EMA': #Exponential
        df['AvgBulls']=df['Bulls'].ewm(length,min_periods=length).mean()
        df['SmthBulls']=df['AvgBulls'].ewm(smooth,min_periods=smooth).mean()
        df['AvgBears']=df['Bears'].ewm(length,min_periods=length).mean()
        df['SmthBears']=df['AvgBears'].ewm(smooth,min_periods=smooth).mean()
    elif ma_type == 'WMA': #Weighted
        n = length
        s = smooth
        df['AvgBulls']=df['Bulls'].rolling(n).apply(lambda x: x[::-1].cumsum().sum() * 2 / n / (n + 1))
        df['SmthBulls']=df['AvgBulls'].rolling(s).apply(lambda x: x[::-1].cumsum().sum() * 2 / s / (s + 1))
        df['AvgBears']=df['Bears'].rolling(n).apply(lambda x: x[::-1].cumsum().sum() * 2 / n / (n + 1))
        df['SmthBears']=df['AvgBears'].rolling(s).apply(lambda x: x[::-1].cumsum().sum() * 2 / s / (s + 1))

    df['difference'] = abs(df['SmthBulls'] - df['SmthBears'])

def ATR(df,n=14):
    "function to calculate True Range and Average True Range"
    df['H-L']=abs(df['High']-df['Low'])
    df['H-PC']=abs(df['High']-df['Close'].shift(1))
    df['L-PC']=abs(df['Low']-df['Close'].shift(1))
    df['TR']=df[['H-L','H-PC','L-PC']].max(axis=1,skipna=False)
    df['ATR'] = df['TR'].rolling(n).mean()
    #df['ATR'] = df['TR'].ewm(span=n,adjust=False,min_periods=n).mean()
    df = df.drop(['H-L','H-PC','L-PC'],axis=1)

def BollingerBand(df,n):
    "function to calculate Bollinger Band"
    df["BB_MA"] = df['Adj Close'].rolling(n).mean()
    df["BB_up"] = df["MA"] + 2*df["MA"].rolling(n).std()
    df["BB_dn"] = df["MA"] - 2*df["MA"].rolling(n).std()
    df["BB_width"] = df["BB_up"] - df["BB_dn"]
    df.dropna(inplace=True)

def cipherB(df,multiplier=150,period=60,chlen=9,avg=12,malen=3):
    #Money Flow
    df['temp'] = (((df['Close'] - df['Open']) / (df['High'] - df['Low'])) * multiplier)
    df['temp'] = np.where(np.isnan(df['temp']),0,df['temp'])
    df['Money Flow'] = df['temp'].rolling(period).mean() - 2.5
    df.drop(['temp'],axis=1,inplace = True)
    
    #Wave Trend
    df['hlc3'] = (df['High'] + df['Low'] + df['Close'])/3
    df['esa'] = df['hlc3'].ewm(chlen).mean()
    df['de'] = abs(df['hlc3'] - df['esa']).ewm(chlen).mean()
    df['ci'] = (df['hlc3'] - df['esa']) / (0.015 * df['de'])
    df['ci'] = np.where(np.isnan(df['ci']),0,df['ci'])
    df['wt1'] = df['ci'].ewm(avg).mean()
    df['wt2'] = df['wt1'].rolling(malen).mean()
    df.drop(['hlc3','esa','de','ci'],axis=1,inplace=True)

def CMF(df,n=21):
    """Chaikan Money Flow"""
    df['CMF'] = ((((df['Close']-df['Low']) - (df['High'] - df['Close']))/(df['High'] - df['Low']))*df['Volume'])/df['Volume'].rolling(n).sum()

def EMA(df,n):
    df[f'EMA {n}'] = df['Close'].ewm(n,min_periods=n).mean()

def fractals(df):
    bear_fractals = [np.nan]*len(df)
    bull_fractals = [np.nan]*len(df)
    for i in range(2,len(df)-2):
        high = df['High'][i]
        low = df['Low'][i]

        if high > df['High'][i-1] and high > df['High'][i-2] and high > df['High'][i+1] and high > df['High'][i+2]:
            bear_fractals[i] = df['High'][i]
        if low < df['Low'][i-1] and low < df['Low'][i-2] and low < df['Low'][i+1] and low < df['Low'][i+2]:
            bull_fractals[i] = df['Low'][i]
    df['bull_fractals'] = bull_fractals
    df['bear_fractals'] = bear_fractals

def KijunSen(df,n=26):
    df['Kijun Sen'] = (df['High'].rolling(n).max() + df['High'].rolling(n).min())/2

def MA(df, n):
    df[f'MA {n}'] = df['Close'].rolling(n).mean()

def MACD(df,a=12,b=26,c=9):
    """function to calculate MACD
    typical values a = 12; b =26, c =9"""
    df["MA_Fast"]=df["Close"].ewm(span=a,min_periods=a).mean()
    df["MA_Slow"]=df["Close"].ewm(span=b,min_periods=b).mean()
    df["MACD"]=df["MA_Fast"]-df["MA_Slow"]
    df["Signal"]=df["MACD"].ewm(span=c,min_periods=c).mean()

def OBV(df):
    """function to calculate On Balance Volume"""
    df['daily_ret'] = df['Adj Close'].pct_change()
    df['direction'] = np.where(df['daily_ret']>=0,1,-1)
    df['direction'][0] = 0
    df['vol_adj'] = df['Volume'] * df['direction']
    df['obv'] = df['vol_adj'].cumsum()

def ParabolicSAR(df):
    pass

def RSI(df,n=14):
    "function to calculate RSI"
    df['delta']=df['Close'] - df['Close'].shift(1)
    df['gain']=np.where(df['delta']>=0,df['delta'],0)
    df['loss']=np.where(df['delta']<0,abs(df['delta']),0)
    avg_gain = []
    avg_loss = []
    gain = df['gain'].tolist()
    loss = df['loss'].tolist()
    for i in range(len(df)):
        if i < n:
            avg_gain.append(np.NaN)
            avg_loss.append(np.NaN)
        elif i == n:
            avg_gain.append(df['gain'].rolling(n).mean().tolist()[n])
            avg_loss.append(df['loss'].rolling(n).mean().tolist()[n])
        elif i > n:
            avg_gain.append(((n-1)*avg_gain[i-1] + gain[i])/n)
            avg_loss.append(((n-1)*avg_loss[i-1] + loss[i])/n)
    df['avg_gain']=np.array(avg_gain)
    df['avg_loss']=np.array(avg_loss)
    df['RS'] = df['avg_gain']/df['avg_loss']
    df['RSI'] = 100 - (100/(1+df['RS']))
    df.drop(columns=['delta', 'gain', 'loss','avg_gain','avg_loss','RS'],inplace=True)

def RSI_Divergence(data, span = 4):
    """
    Bullish Divergence : price makes lower lows, indicator makes higher lows
    Bullish Hidden Divergence : price makes higher low, indicator makes lower low
    Bearish Divergence : Price makes higher high, indicator makes lower high
    Bearish Hidden Divergence : Price makes lower high, indicator makes higher high
    """
    #Get relative minimums of Close price
    rel_min1, = argrelmin(np.array(data['Close'].tolist()),order=span)
    data['swing_low'] = [data['Low'][i] if i in rel_min1 else np.nan for i in range(len(data))]

    #Get relative maximumns of Close price
    rel_max1, = argrelmax(np.array(data['Close'].tolist()),order=span)
    data['swing_high'] = [data['High'][i] if i in rel_max1 else np.nan for i in range(len(data))]

    #Get relative minimums of RSI
    rel_min2, = argrelmin(np.array(data['RSI'].tolist()),order=span)
    data['swing_low_rsi'] = [data['RSI'][i] if i in rel_min2 else np.nan for i in range(len(data))]

    #Get relative maxiumums of RSI
    rel_max2, = argrelmax(np.array(data['RSI'].tolist()),order=span)
    data['swing_high_rsi'] = [data['RSI'][i] if i in rel_max2 else np.nan for i in range(len(data))]

    #Get intersection of mins and maxes for RSI and Close price
    lows = np.intersect1d(rel_min1,rel_min2)
    highs = np.intersect1d(rel_max1,rel_max2)

    #Tuple list (index1, index2)
    bull_div, bull_h_div = [], []
    bear_div, bear_h_div = [], []
    #Compare adjacent highs
    for i in range(1,len(highs)):
        prev_rsi = data['RSI'][highs[i-1]]
        cur_rsi = data['RSI'][highs[i]]
        prev_high = data['High'][highs[i-1]]
        cur_high = data['High'][highs[i]]

        if cur_high > prev_high and cur_rsi < prev_rsi: #Bearish divergence
            bear_div.append((highs[i-1],highs[i]))
        elif cur_high < prev_high and cur_rsi > prev_rsi: #Bearish Hidden Divergence
            bear_h_div.append((highs[i-1],highs[i]))
    #Compare adjacent lows
    for i in range(1,len(lows)):
        prev_rsi = data['RSI'][lows[i-1]]
        cur_rsi = data['RSI'][lows[i]]
        prev_low = data['Low'][lows[i-1]]
        cur_low = data['Low'][lows[i]]

        if cur_low < prev_low and cur_rsi > prev_rsi: #Bullish divergence
            bull_div.append((lows[i-1],lows[i]))
        elif cur_low > prev_low and cur_rsi < prev_rsi: #Bullish hidden divergence
            bull_h_div.append((lows[i-1],lows[i]))
    
    #Add columns to dataframe for plotting
    col_list1 = ['bullish_divergence','bearish_divergence','bullish_hidden_divergence','bearish_hidden_divergence']
    col_list2 = ['bullish_divergence_rsi','bearish_divergence_rsi','bullish_hidden_divergence_rsi','bearish_hidden_divergence_rsi']
    for t1,t2 in zip([bull_div,bear_div,bull_h_div,bear_h_div],col_list1):
        temp = [np.nan]*len(data)
        for pair in t1:
            c = data['Close'][pair[0]]
            c2 = data['Close'][pair[1]]
            slope = (c2 - c)/(pair[1]-pair[0])
            for i in range(pair[0],pair[1]+1):
                temp[i] = c + slope*(i-pair[0])
        data[t2] = temp

    for t1,t2 in zip([bull_div,bear_div,bull_h_div,bear_h_div],col_list2):
        temp = [np.nan]*len(data)
        for pair in t1:
            c = data['RSI'][pair[0]]
            c2 = data['RSI'][pair[1]]
            slope = (c2 - c)/(pair[1]-pair[0])
            for i in range(pair[0],pair[1]+1):
                temp[i] = c + slope*(i-pair[0])
        data[t2] = temp

def STC(df):
    """Shaff Trend Cycle"""
    pass

def Stochastic(df, n=14, m=3):
    df['stoch'] = (df['Close'] - df['Low'].rolling(n).min())/(df['High'].rolling(14).max() - df['Low'].rolling(n).min())*100
    df['stoch_ma'] = df['stoch'].rolling(m).mean()

def STOCH_RSI(df):
    RSI(df)
    df['min_rsi'] = df['RSI'].rolling(14).min()
    df['max_rsi'] = df['RSI'].rolling(14).max()
    df['stoch_rsi'] = (df['RSI'] - df['min_rsi'])/(df['max_rsi']-df['RSI'])
    df['stoch_rsi_ma'] = df['stoch_rsi'].rolling(3).mean()


def SSL_Channel(df, n=14):
    up = [np.nan]*n
    dn = [np.nan]*n
    trend = None
    for i in range(n,len(df)):
        highs = [df['High'][k] for k in range(i-n, i)]
        high_avg = sum(highs)/len(highs)
        lows = [df['Low'][k] for k in range(i-n, i)]
        low_avg = sum(lows)/len(lows)

        close = df['Close'][i]
        if close > high_avg:
            up.append(high_avg)
            dn.append(low_avg)
            trend = 'up'
        elif close < low_avg:
            up.append(low_avg)
            dn.append(high_avg)
            trend = 'dn'
        else:
            if trend == 'up':
                up.append(high_avg)
                dn.append(low_avg)
            elif trend == 'dn':
                up.append(low_avg)
                dn.append(high_avg)

    df['SSL_up'] = up
    df['SSL_dn'] = dn

def SuperTrend(df,m=1,n=10):
    """function to calculate Supertrend given historical candle data
        m = multiplier
        n = n day ATR"""
    ATR(df,n=5) # Usually ATR_5 is used for the calculation
    df["B-U"]=((df['High']+df['Low'])/2) + m*df['ATR']
    df["B-L"]=((df['High']+df['Low'])/2) - m*df['ATR']
    df["temp1"] = df["B-U"]
    df["temp2"] = df["B-L"]
    df["F-U"]= np.where((df["B-U"]<df["temp1"].shift(1))|(df["Close"].shift(1)>df["temp1"].shift(1)),df["B-U"],df["temp1"].shift(1))
    df["F-L"]= np.where((df["B-L"]>df["temp2"].shift(1))|(df["Close"].shift(1)<df["temp2"].shift(1)),df["B-L"],df["temp2"].shift(1))
    df["Strend"] = np.where(df["Close"]<=df["F-U"],df["F-U"],df["F-L"])

def TDI(df, m=1.6185):
    """Traders Dynamic Index"""
    RSI(df, n=13)
    df['VB up'] = df['RSI'].rolling(34).mean() + m*df['RSI'].rolling(34).std()
    df['VB dn'] = df['RSI'].rolling(34).mean() - m*df['RSI'].rolling(34).std()
    df['RSI MA Fast'] = df['RSI'].rolling(2).mean()
    df['RSI MA Slow'] = df['RSI'].rolling(7).mean()

def WaveTrend(df, n1=10, n2=21):
    df['Avg Price'] = (df['Close']+df['High']+df['Low'])/3
    df['esa'] = df['Avg Price'].ewm(n1).mean()
    df['d'] = abs(df['Avg Price']-df['esa']).ewm(n1).mean()
    df['ci'] = (df['Avg Price']-df['esa'])/(0.015*df['d'])
    #Plot these vvvv
    df['tci'] = df['ci'].ewm(n2).mean()
    df['wt2'] = df['tci'].rolling(4).mean()

def WilliamsAlligator(df):
    """Alligator indicator"""
    pass

def WMA(df,n):
    df[f'WMA {n}'] = df.rolling(n).apply(lambda x: x[::-1].cumsum().sum() * 2 / n / (n + 1))

