import asyncio
import websockets
import json


async def funding():
    uri = 'wss://contract.mexc.com/edge'

    param = {'symbol':'BTC_USDT'}
    #method = 'sub.funding.rate'
    method = 'sub.ticker'


    try:
        async with websockets.connect(uri,ping_interval = 20, ping_timeout = 10) as websocket:
            print('Connection ok')

            subscribe_message = {'method': method,'param':param}
            
            await websocket.send(json.dumps(subscribe_message))
            
            print('Subscribe ok')

            async for message in websocket:

                data = json.loads(message)
            
                print(data)
    except Exception as e:
        print(f'not ok {e}')


if __name__ == '__main__':
    asyncio.run(funding())
