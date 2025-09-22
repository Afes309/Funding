import ccxt.async_support as ccxt
import asyncio
import ccxt as ccxt_s
from datetime import datetime,timedelta


enter_data = {'symbol':'OMNI/USDT:USDT','short_enter_price':3.817, 'long_enter_price':3.785,
                          'short_exchange': 'gate', 'long_exchange':'mexc', 'short_time':155, 'long_time':455
                          }

#current_data = {'symbol':'NMR/USDT:USDT','short_current_price':50.600,'long_current_price':51.300,
#                'funding_short':-0.754,'funding_long':-2.5
#                }

mexc = 0.03
gate = 0.06

def save_enter_data(enter_data):

    pass

def get_current_data(short_exchange, long_exchange,symbol):
    
    try:
        exchange_short = getattr(ccxt_s, short_exchange)({'enableRateLimit': True}) 
        exchange_long = getattr(ccxt_s, long_exchange)({'enableRateLimit': True}) 

        data = {}

        short_data = exchange_short.fetch_ticker(symbol)
        long_data = exchange_long.fetch_ticker(symbol)

        funding_short = exchange_short.fetch_funding_rate(symbol)
        funding_long = exchange_long.fetch_funding_rate(symbol)
        '''
        print(short_data)
        print('**********************************')
        print(long_data)
        print('*********************************')
        print(funding_short)
        print('**********************************')
        print(funding_long)
        print('________________________')
        print(funding_long['fundingRate'])
        '''
        

        data.update({'symbol':symbol,'short_current_price':short_data['bid'],'long_current_price':long_data['ask'],
                     'funding_short':round(funding_short['fundingRate']*100,5),
                     'funding_long':round(funding_long['fundingRate']*100,5)
                     })
        
        #print(f'current data {data}')
        
        return data
    
    except Exception as e:
        print('pizdec')
        print(e)
        return []


def get_profit_data(enter_data,current_data,fee_short,fee_long):
    
    short_profit = (enter_data['short_enter_price']/current_data['short_current_price']*100-100)+current_data['funding_short']-fee_short*2
    long_profit = (enter_data['long_enter_price']/current_data['long_current_price']*100-100)*-1-current_data['funding_long']-fee_long*2

    result_profit = short_profit+long_profit

    print(f"Short exchange price {current_data['short_current_price']}")
    print(f"Long excenge price {current_data['long_current_price']}")
    print(f"Short funding {current_data['funding_short']}")
    print(f"Long funding {current_data['funding_long']}")

    print(short_profit)
    print(long_profit)

    print(f'result profit {result_profit}')


if __name__ == '__main__':
    current_data = get_current_data('gate','mexc','OMNI/USDT:USDT')
    get_profit_data(enter_data,current_data,mexc,gate)
