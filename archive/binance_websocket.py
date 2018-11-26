from binance.client import Client
from binance.websockets import BinanceSocketManager

def process_m_message(msg):
    timestamp = msg['data']['T']
    price = msg['data']['p']
    s, ms = divmod(timestamp, 1000)

    coinpair = msg['data']['s']
    result = {'exchange': 'binance'}
    result['coinpair'] = str(coinpair)
    result['buy'] = float(str(price))
    result['sell'] = float(str(price))
    result['timestamp'] = int(s)

    if callback is None:
        print(result)
    else:
        callback(result)

def start(coinpairs, listener):
    global callback
    callback = listener
    client = Client("", "")
    global bm
    bm = BinanceSocketManager(client)
    # pass a list of stream names
    streams = []
    for coinpair in coinpairs:
        if coinpairs[coinpair]['binance'] is not None:
            streams.append(coinpairs[coinpair]['binance'].lower() + '@aggTrade')

    conn_key = bm.start_multiplex_socket(streams, process_m_message)
    # then start the socket manager
    bm.start()

def end():
    global bm
    bm.end()

if __name__ == '__main__':
    import arbitrager
    start(arbitrager.coinpairs, None)




