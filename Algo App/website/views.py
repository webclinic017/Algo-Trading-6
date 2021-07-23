from flask import Blueprint, render_template, redirect
from flask.globals import request
from flask.helpers import url_for
from flask_login import login_required, current_user
from .chartlib import consolidating_stocks, breakout_stocks
from .scraper import get_tickers, get_SANDP_tickers, get_sentiment
from .strategies import CipherB, HalfTrend,Scalper
from .modules.patterns import patterns
import talib
import threading
import os
import pandas as pd
import yfinance as yf
import datetime as dt

views = Blueprint('views', __name__)

#TODO: Make this more robust, refactor into different files
##########################################
#Only Hardcoded part of website
strats = {}
strats['Scalper'] = Scalper, Scalper()
strats['CipherB'] = CipherB, CipherB()
strats['HalfTrend'] = HalfTrend, HalfTrend()
##########################################

threads = []
for strat in strats:
    instance = strats[strat][1]
    t = threading.Thread(target=instance.start)
    threads.append(t)

@views.route('/algorithms', methods=['GET','POST'])
@login_required
def algorithms():
    if request.method == "POST":
        strategy_id = request.form.get('strategy')

        for i,strat in enumerate(strats.keys()):
            thread = threads[i]
            if strategy_id == strat:
                if thread.isAlive():
                    strats[strat][1].run = False
                    strats[strat] = strats[strat][0],strats[strat][0]()
                    threads[i] = threading.Thread(target=strats[strat][1].start)
                else:
                    thread.start()
                break
        
        return redirect(url_for('views.algorithms'))
    
    # for strat in strats:
    #     strats[strat][1].save_plot()
    return render_template("algorithms.html", user=current_user, strats=[(s,strats[s],threads[i].isAlive()) for i,s in enumerate(strats)])

@views.route('/updateData')
@login_required
def updateData():
    tickers = get_SANDP_tickers()
    for symbol in tickers:
        data = yf.download(symbol, start="2020-01-01", end=str(dt.date.today()))
        if len(data) > 0:
            data.to_csv(f'website/datasets/daily/{symbol}.csv')

    return {
        "code": "success"
    }

@views.route('/sentiment', methods=["GET", "POST"])
@login_required
def sentiment():
    if request.method == 'POST':
        ticker = request.form['ticker']
        sentiment = get_sentiment(ticker)
    else:
        ticker = None
        sentiment = None

    print(ticker, sentiment)
    return render_template('sentiment.html', user=current_user, sentiment=sentiment, ticker = ticker)

@views.route('/breakout')
@login_required
def breakout():
    pattern = request.args.get('pattern', False)
    if pattern == 'Consolidating':
        stocks = consolidating_stocks()
    elif pattern == 'Breakout':
        stocks = breakout_stocks()
    else:
        stocks = None

    return render_template('breakout.html', user=current_user, pattern = pattern, stocks=stocks)

@views.route('/candle')
@login_required
def candle():
    pattern  = request.args.get('pattern', False)
    stocks = {}

    tickers = get_tickers()
    for symbol in tickers:
        stocks[symbol] = {'company': symbol}

    if pattern:
        for filename in os.listdir(os.getcwd() + '/website/datasets/daily'):
            df = pd.read_csv(os.getcwd() + '/website/datasets/daily/{}'.format(filename))
            pattern_function = getattr(talib, pattern)
            symbol = filename.split('.')[0]

            try:
                results = pattern_function(df['Open'], df['High'], df['Low'], df['Close'])
                last = results.tail(1).values[0]

                if last > 0:
                    stocks[symbol][pattern] = 'bullish'
                elif last < 0:
                    stocks[symbol][pattern] = 'bearish'
                else:
                    stocks[symbol][pattern] = None
            except Exception as e:
                print('failed on filename: ', filename)

    return render_template('candle.html', user=current_user, candlestick_patterns=patterns, stocks=stocks, pattern=pattern)

@views.route('/')
@login_required
def home():
    return render_template("home.html", user=current_user)