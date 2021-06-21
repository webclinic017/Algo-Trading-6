import mysql.connector
import datetime as dt

cnx = mysql.connector.connect(host="localhost", user="root", passwd="Cornellvac62")

def add_stock_sentiments(sentiments):
    cnx = mysql.connector.connect(host="localhost", user="root", passwd="Cornellvac62")
    date = str(dt.date.today())
    cur = cnx.cursor()
    for sector in sentiments:
        for ticker in sentiments[sector]:
            if ticker != 'Sentiment':
                sql = "INSERT INTO backtester.stock_sentiments (Date, Ticker, Sentiment) VALUES (%s,%s,%s)"
                val = (date, ticker, sentiments[sector][ticker])
                cur.execute(sql, val)
    cnx.commit()
    cur.close()
    cnx.close()

def add_sector_sentiments(sentiments):
    cnx = mysql.connector.connect(host="localhost", user="root", passwd="Cornellvac62")
    date = str(dt.date.today())
    cur = cnx.cursor()
    for sector in sentiments:
        sql = "INSERT INTO backtester.sector_sentiments (Date, Sector, Sentiment) VALUES (%s,%s,%s)"
        val = (date, sector, round(sentiments[sector]['Sentiment'], 3))
        cur.execute(sql,val)
    cnx.commit()
    cur.close()
    cnx.close()

def get_stock_sentiments(date):
    cnx = mysql.connector.connect(host="localhost", user="root", passwd="Cornellvac62")
    cur = cnx.cursor()
    cur.execute(f"SELECT*FROM backtester.stock_sentiments WHERE date='{date}';")

    stock_sentiments = []
    for row in cur:
        stock_sentiments.append(row)
    cnx.commit()
    cur.close()
    cnx.close()
    return stock_sentiments

def get_sector_sentiments(date):
    cnx = mysql.connector.connect(host="localhost", user="root", passwd="Cornellvac62")
    cur = cnx.cursor()
    cur.execute(f"SELECT*FROM backtester.sector_sentiments WHERE date='{date}';")

    sector_sentiments = []
    for row in cur:
        sector_sentiments.append(row)

    cnx.commit()
    cur.close()
    cnx.close()
    return sector_sentiments
    

   