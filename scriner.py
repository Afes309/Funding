import ccxt
import pandas as pd



exchange = ccxt.gate({'enableRateLimit':True})

timeframe = '1d'
limit = 1


def get_pairs(timeframe,limit):
    markets = exchange.load_markets()
    
    usdt_pairs = [symbol for symbol in markets.keys() if symbol.endswith('/USDT')]

    all_pairs = pd.DataFrame()

    for symbol in usdt_pairs:
        try:
            ticker = exchange.fetch_ohlcv(symbol,timeframe, limit = limit)
            df = pd.DataFrame(ticker,columns = ['timestamp','open','high','low','close','volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit = 'ms')
            df['symbol'] = symbol
            all_pairs = pd.concat([all_pairs,df],ignore_index = True)
            print(df[['timestamp','volume']].tail())
        except Exception as e:
            print('Error')

    print(all_pairs.head())






        


def get_order_book(symbol):
    order_book = exchange.fetch_order_book(symbol)

    print(order_book)



if __name__ == '__main__':
    #get_order_book('BTC/USDT')
    get_pairs(timeframe,limit)
