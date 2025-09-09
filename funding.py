import ccxt.async_support as ccxt
import asyncio
import ccxt as ccxt_s
from datetime import datetime,timedelta

from test import rass

#______________________________________Для каждой монеты

def time_msk(timestamp):
    utc_time = datetime.utcfromtimestamp(int(timestamp/1000))
    msk_time = utc_time + timedelta(hours = 3)

    return msk_time.strftime('%Y-%m-%d %H:%M:%S')

async def coin_data(exchange_id,symbol):
    try:
        exchange = getattr(ccxt, exchange_id)({'enableRateLimit': True}) 

        data = []

        spot_symbol = symbol.split(':')[0]

        funding_data = await exchange.fetch_funding_rate(symbol)
        spot_price_data = await exchange.fetch_ticker(spot_symbol)
        futures_price_data = await exchange.fetch_ticker(symbol)


        print(exchange_id)


        #data.append({'1':funding_data,'2':spot_price_data,'3':futures_price_data})
        data.append({'symbol':spot_symbol,'futures_price_ask':futures_price_data['ask'],'futures_price_bid':futures_price_data['bid'],
                     'fundingRate':round(funding_data['fundingRate']*100,5),
                     'fundingTime':time_msk(funding_data['fundingTimestamp']),
                     'exchange':exchange_id,'interval':funding_data['interval']})
        
        return data
    
    except Exception as e:
        print('pizdec')
        print(e)
        return []

    finally:
        await exchange.close()




async def all_exchange_coin_data():
    exchanges = ['bybit','okx','bitget','gate','mexc','bingx','hyperliquid'] 
    #exchanges = ['bingx']

    tasks = []

    for exchange in exchanges:
        tasks.append(coin_data(exchange,'IDEX/USDT:USDT'))

    results = await asyncio.gather(*tasks)

    all_rates = []

    for result in results:
        all_rates.extend(result)

    return all_rates

async def main_1():
    data = await all_exchange_coin_data()
    print(data)
    rass(data)
    #for i in data:
    #print(i)



#______________________________________

async def get_funding_rates_v2(exchange_id):

    exchange = getattr(ccxt, exchange_id)({'enableRateLimit': True})
    
    try:
        # Получаем все доступные фьючерсные пары
        markets = await exchange.load_markets()
        
        futures_symbols = [symbol for symbol, market in markets.items() if symbol.endswith(':USDT') and market['active']]

                
        # Запрашиваем фандинг для каждой пары отдельно
        results = []
        for symbol in futures_symbols:
            try:
                rate = await exchange.fetch_funding_rate(symbol)
                results.append({'exchange':exchange_id,'symbol': symbol,'price':rate.items()['markPrice'],
                                'funding_rate': rate.items()['fundingRate']})
    
            except Exception as e:
                print(f"Ошибка для {symbol}: {e}")

                return []
        return results
                            

                        
    finally:
        await exchange.close()


#,'next_funding': rate['nextFundingTime']

async def get_funding_rates(exchange_id):
    try:

        exchange = getattr(ccxt,exchange_id)({'enableRateLimit':True})

        funding_rates = await exchange.fetch_funding_rates()

        results = []

        for symbol,rate in funding_rates.items():
            results.append({'exchange':exchange_id,'symbol': symbol,'price':rate['markPrice'],
                            'funding_rate': rate['fundingRate']})
        
        return results
    except Exception as e:
        print(f'Error in {exchange_id}:{str(e)}')
        return []
    finally:
        await exchange.close()
    




async def all_funding_data():
    exchanges = ['binance','bybit','okx']
    
    tasks = []
    for exchange_id in exchanges:
        exchange = getattr(ccxt,exchange_id)({'enableRateLimit':True})
        if not exchange.has.get('fetchFundingRates', False):
            tasks.append(get_funding_rates_v2(exchange_id))
        else:
            tasks.append(get_funding_rates(exchange_id))

    results = await asyncio.gather(*tasks)

    all_rates = []
    for exchange_rates in results:
        all_rates.extend(exchange_rates)

    return all_rates

    

async def main():
    funding_data = await all_funding_data()
    

    for rate in funding_data:
        print(rate)
        #print(rate['exchange'])
        #print(f"symbol {rate['symbol']}, price {rate['markPrice']}, funding {rate['fundingRate']}")


def test(exchange_id):
        
    exchange = getattr(ccxt_s,exchange_id)()

    funding = exchange.fetch_funding_rate(symbol = 'M/USDT:USDT')
    futures = exchange.fetch_ticker(symbol = 'M/USDT:USDT') 
    #funding = exchange.fetch_funding_rates()

    #markets = exchange.load_markets()


    

    print(funding)
    print(futures)

    

    '''   
    print(funding)
    print('___________')
    print(funding['symbol'])
    print(funding['markPrice'])
    print(funding['fundingRate'])
    print(funding['fundingTimestamp'])
    '''


if __name__ == '__main__':
    #asyncio.run(main())
    #test('bingx')
    asyncio.run(main_1())

    

