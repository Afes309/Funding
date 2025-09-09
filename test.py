
data_1 = [
    {'symbol': 'BTC/USDT', 'spot_price': 118925.89, 'futures_price': 118920.1, 'fundingRate': 0.0071920000000000005, 'fundingTime': '2025-08-15 19:00:00', 'exchange': 'binance', 'interval': None},
    {'symbol': 'BTC/USDT', 'spot_price': 118934.9, 'futures_price': 118916.5, 'fundingRate': 0.01, 'fundingTime': '2025-08-15 19:00:00', 'exchange': 'bybit', 'interval': '8h'},
    {'symbol': 'BTC/USDT', 'spot_price': 118934.9, 'futures_price': 118899.9, 'fundingRate': -0.01, 'fundingTime': '2025-08-15 19:00:00', 'exchange': 'okx', 'interval': None},
    {'symbol': 'BTC/USDT', 'spot_price': 118934.41, 'futures_price': 118870.8, 'fundingRate': 9.999999999999999e-05, 'fundingTime': '2025-08-15 19:00:00', 'exchange': 'bitget', 'interval': '8h'},
    {'symbol': 'BTC/USDT', 'spot_price': 118983.0, 'futures_price': 118923.4, 'fundingRate': 0.01, 'fundingTime': '2025-08-15 19:00:00', 'exchange': 'gate', 'interval': '8h'},
    {'symbol': 'BTC/USDT', 'spot_price': 118921.25, 'futures_price': 118865.2, 'fundingRate': -0.0072, 'fundingTime': '2025-08-15 19:00:00', 'exchange': 'mexc', 'interval': '8h'},
        ]

fee_1 = {'spot':0.1,'futures':0.05}
fee_2 = {'spot':0.1,'futures':0.06}

def swap_exchange(pair):
    if ':' in pair:
        pair_1, pair_2 = pair.split(':')
        swap_exchange = f"{pair_2}:{pair_1}"
        return(swap_exchange)
    print('не удалось свапнуть биржи')
    

def exchange_arbitrage(exchange_data_1,exchange_data_2,fee_1,fee_2):
    
    exchange_1 = exchange_data_1['exchange']
    futures_price_ask_1 = exchange_data_1['futures_price_ask']
    futures_price_bid_1 = exchange_data_1['futures_price_bid']
    fundingRate_1 = exchange_data_1['fundingRate']
    interval_1 = exchange_data_1['interval']

    exchange_2 = exchange_data_2['exchange']
    futures_price_ask_2 = exchange_data_2['futures_price_ask']
    futures_price_bid_2 = exchange_data_2['futures_price_bid']
    fundingRate_2 = exchange_data_2['fundingRate'] 
    interval_2 = exchange_data_2['interval'] 

    # Вариант 1
    try:
        if futures_price_ask_1 and futures_price_ask_2 != None:
            profit_1 = (futures_price_bid_1/futures_price_ask_2*100-100)+fundingRate_1-fundingRate_2-fee_1*2-fee_2*2
            profit_2 = (futures_price_bid_2/futures_price_ask_1*100-100)+fundingRate_2-fundingRate_1-fee_1*2-fee_2*2


            #print(profit_1)
            #print(profit_2)

            if profit_1 > profit_2:
                #print(f"result {profit_1}")
                return profit_1
            elif profit_1 < profit_2:
                #print(f"result {profit_2}")
                return profit_2

        else:
            print('Some else wrong')
    except Exception as e:
        print(e)

def rass(data):
    best_profit = {}
    for i in data:
        for b in data:
            if i==b:
                continue
            
            print(f"{i['exchange']}:{b['exchange']}")

            profit = exchange_arbitrage(i,b,fee_1['futures'],fee_2['futures'])
            
            best_profit[f"{i['exchange']}:{b['exchange']}"] = profit

    print(best_profit)




if __name__ == '__main__':
    

    for i in data_1:
        for b in data:
            if i==b:
                continue
            print(f"{i['exchange']}:{b['exchange']}")

            exchange_arbitrage(i,b,fee_1['futures'],fee_2['futures'])



