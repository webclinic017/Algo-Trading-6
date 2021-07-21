import requests
from bs4 import BeautifulSoup as bs
import pandas as pd
from nltk.sentiment.vader import SentimentIntensityAnalyzer

def get_SANDP_tickers():
    """
    Function that will web scrape S and P 500 ticker symbols
    """
    url='https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    page = requests.get(url)
    page_content = page.content
    soup = bs(page_content,'html.parser')
    tickers = soup.findAll('a', {'class':'external text'})

    tickers_text = ['SPY']
    for ticker in tickers:
        text = ticker.text
        if len(text) < 5:
            tickers_text.append(text)

    return tickers_text

def get_tickers():
    url = 'https://stockanalysis.com/stocks/'
    page = requests.get(url)
    soup = bs(page.content,'html.parser')
    lis = soup.findAll('li')

    tickers = []
    for li in lis:
        a = li.find('a')
        text = a.text.split(' ')[0]
        if text.isupper():
            tickers.append(text)

    return tickers

def get_sentiment(ticker):
    """
    Returns float of sentiment for given ticker, calculated by averaging sentiment
    of scraped news headlines
    -1 <= sentiment <= 1
    """
    url = f'https://finviz.com/quote.ashx?t={ticker}' #Must have 3.6 or up
    page = requests.get(url=url,headers={'user-agent': 'my-app/0.0.1'})
    soup = bs(page.content, 'html.parser')
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
