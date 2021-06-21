import requests
from bs4 import BeautifulSoup
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import pandas as pd

def get_gainers():
    url = 'https://finance.yahoo.com/gainers/?offset=0&count=100'
    page = requests.get(url=url,headers={'user-agent': 'my-app/0.0.1'})
    soup = BeautifulSoup(page.content, 'html.parser')

    rows = soup.findAll('td')
    
    tickers = []
    for row in rows:
        a = row.find('a')
        if a:
            tickers.append(a.text)
    
    return tickers

def get_sentiment_dict(ticker):
    url = f'https://finviz.com/quote.ashx?t={ticker}' #Must have 3.6 or up
    page = requests.get(url=url,headers={'user-agent': 'my-app/0.0.1'})
    soup = BeautifulSoup(page.content, 'html.parser')
    news_headlines = soup.findAll("a", {'class':'tab-link-news'})
    #List of Headlines
    headlines = []
    for h in news_headlines:
        headlines.append(h.text)
    df = pd.DataFrame(headlines, columns=['Headlines'])
    # Instantiate the sentiment intensity analyzer
    vader = SentimentIntensityAnalyzer()
    # Iterate through the headlines and get the polarity scores using vader
    scores = df['Headlines'].apply(vader.polarity_scores).tolist()

    temp = {}
    comp = 0
    neu = 0
    pos = 0
    neg = 0
    for i in range(len(headlines)):
        temp[headlines[i]] = scores[i]
        comp += scores[i]['compound']
        pos += scores[i]['pos']
        neg += scores[i]['neg']
        neu += scores[i]['neu']
    
    averages = {'compound': round(comp/len(scores),3),
                'pos': round(pos/len(scores),3),
                'neg': round(neg/len(scores),3),
                'neu': round(neu/len(scores),3)}
    
    return temp, averages
    

def get_current_price(ticker):
    """
    type ticker: string, uppercase, length < 5
    rtype: float
    """
    url = f'https://www.marketwatch.com/investing/stock/{ticker}' #Must have 3.6 or up
    page = requests.get(url=url)
    soup = BeautifulSoup(page.content, 'html.parser')
    price = soup.find('bg-quote', {'field':'Last'})
    if price:
        string = price.text
        index = string.find(',')
        if index > 0:
            string = string[:index] + string[index+1:]
        return float(string)
    return 0

def get_sentiment(ticker):
    """
    Returns float of sentiment for given ticker, calculated by averaging sentiment
    of scraped news headlines
    -1 <= sentiment <= 1
    """
    url = f'https://finviz.com/quote.ashx?t={ticker}' #Must have 3.6 or up
    page = requests.get(url=url,headers={'user-agent': 'my-app/0.0.1'})
    soup = BeautifulSoup(page.content, 'html.parser')
    news_headlines = soup.findAll("a", {'class':'tab-link-news'})
    
    #List of Headlines
    headlines = []
    for h in news_headlines:
        headlines.append(h.text)
    
    df = pd.DataFrame(headlines, columns=['Headlines'])

    # Instantiate the sentiment intensity analyzer
    vader = SentimentIntensityAnalyzer()
    # Iterate through the headlines and get the polarity scores using vader
    scores = df['Headlines'].apply(vader.polarity_scores).tolist()
    
    total = 0
    for i in range(len(scores)):
        total = total + scores[i]['compound']
    if len(scores)>0:
        return round(total/len(scores), 3)
    else:
        return 0

def get_sector_sentiments():
    """
    Returns a dataframe of sentiments by sector and ticker
    """
    sectors = {'Consumer Cyclical' : ['AMZN', 'HD','NKE','MCD','SBUX','GM','F', 'LVS'],
               'Communication Services' : ['GOOGL','FB','VZ','T','EA','DIS','NFLX', 'TMUS', 'CMCSA'],
               'Consumer Defense' : ['WMT','PG','COST','EL','KMB','CL','TGT','KHC', 'PEP'],
               'Technology' : ['MSFT','AAPL','INTC','CSCO','CRM','IBM'],
               'Financial' : ['V','MA','JPM','GS','BLK'],
               'Healthcare' : ['PFE','ABBV','AGN','JNJ','MRK','CVS','ABT'],
               'Industrials' : ['GE','UPS','MMM','AMT','NEE','RTX','BA'],
               'Energy' : ['XOM','CVX','COP','PSX','KMI']}
    sentiments = {}
    for sector in sectors:
        sector_sum = 0
        num_ticks = 0
        sector_sentiments = {}
        for t in sectors[sector]:
            t_s = get_sentiment(t)
            sector_sentiments[t] = t_s
            sector_sum += t_s
            num_ticks += 1
        sector_sentiments['Sentiment'] = round(sector_sum/num_ticks, 3)
        sentiments[sector] = sector_sentiments
    return sentiments

def get_SANDP_tickers():
    """
    Function that will web scrape S and P 500 ticker symbols
    """
    url='https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    page = requests.get(url)
    page_content = page.content
    soup = BeautifulSoup(page_content,'html.parser')
    tickers = soup.findAll('a', {'class':'external text'})
    
    tickers_text = ['SPY']
    for ticker in tickers:
        text = ticker.text
        if len(text) < 5:
            tickers_text.append(text)
    
    return tickers_text

def get_low_float_stocks():
    urls = ["https://www.highshortinterest.com/", "https://www.highshortinterest.com/all/2"]
    stocks = []
    for url in urls:
        page = requests.get(url)
        page_content = page.content
        soup = BeautifulSoup(page_content,'html.parser')

        rows = soup.findAll("tr")
        for i in range(6,len(rows)):
            tds = rows[i].findAll("td")
            if len(tds) > 4:
                ticker = tds[0].find('a').text
                flt = tds[4].text
                flt = float(flt[:-1])
                if flt < 100.0: #in millions
                    stocks.append(ticker)
    return stocks