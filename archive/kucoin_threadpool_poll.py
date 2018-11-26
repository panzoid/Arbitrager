import time
import threading
from multiprocessing.dummy import Pool as ThreadPool
from kucoin.client import Client

client = Client("", "")
coinpairs = []

def start(coinpairs_dict, listener):
    global running
    running = True

    global callback
    callback = listener

    global coinpairs
    for coinpair in coinpairs_dict:
        if coinpairs_dict[coinpair]['kucoin'] is not None:
            coinpairs.append(coinpairs_dict[coinpair]['kucoin'])

    global pool
    pool = ThreadPool(len(coinpairs))

    run()

def end():
    global running
    running = False

def get_open_orders(coinpair):
    open_orders = client.get_order_book(coinpair, limit=1)
    timestamp = int(time.time())
    sell = open_orders['SELL'][0][0]
    buy = open_orders['BUY'][0][0]
    result = {'exchange': 'kucoin'}
    result['coin'] = coinpair
    result['buy'] = buy
    result['sell'] = sell
    result['timestamp'] = timestamp

    return result

def run():
    if running:
        threading.Timer(1, run).start()
        results = pool.map(get_open_orders, coinpairs)

        for result in results:
            if callback is None:
                print result
            else:
                callback(result)


if __name__ == '__main__':
    import Consts
    start(Consts.COINPAIRS, None)