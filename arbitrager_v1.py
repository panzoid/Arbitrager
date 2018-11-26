import datetime
import Consts
import testdata
import binance_client
import kucoin_client

database = {}

def listener(data):
    my_exchange = data['exchange']
    my_sell_price = data['buy']
    my_buy_price = data['sell']
    coinpair = lookup_coinpair(my_exchange, data['coinpair'])

    if coinpair is None:
        return

    update_database(my_exchange, coinpair, data)
    find_arbitrage_opportunity(my_exchange, coinpair, my_sell_price, my_buy_price)


def find_arbitrage_opportunity(my_exchange, coinpair, my_sell_price, my_buy_price):
    '''
        Look at each exchange and find opportunities for arbitrage trades (profit margin >= threshold)
        for the specified coinpairs
    
    ''' 
    for other_exchange in Consts.EXCHANGES:
        if other_exchange != my_exchange:
            if other_exchange in database and coinpair in database[other_exchange]:
                other_sell_price = database[other_exchange][coinpair]['buy']
                other_buy_price = database[other_exchange][coinpair]['sell']

                buy_mine_sell_other_profit = other_sell_price / my_buy_price * 100 - 100
                buy_other_sell_mine_profit = my_sell_price / other_buy_price * 100 - 100
                
                print 'My: ', my_exchange, coinpair, my_sell_price, my_buy_price
                                
                print 'Other: ', other_exchange, coinpair, other_sell_price, other_buy_price
                
                buy_sell_message = 'Buy {0} on {1} and sell on {2} for {3:.3f}% profit'
                
                if buy_mine_sell_other_profit >= Consts.TRADE_THRESHOLD:
                    print datetime.datetime.now(), buy_sell_message.format(coinpair, my_exchange, other_exchange, buy_mine_sell_other_profit)
                if buy_other_sell_mine_profit >= Consts.TRADE_THRESHOLD:
                    print datetime.datetime.now(), buy_sell_message.format(coinpair, other_exchange, my_exchange, buy_other_sell_mine_profit)


def lookup_coinpair(exchange, exchange_coinpair):
    '''
        Lookup all coinpairs we are interested in trading as specified in Consts.py 
    '''    
    for key, value in Consts.COINPAIRS.items():
        if exchange_coinpair == value[exchange]:
            return key
    return None


def update_database(exchange, coinpair, data):
    '''
        Updates the database with all coinpairs for each exchange we are trading on
    '''   
    if exchange not in database:
        database[exchange] = {}

    if coinpair not in database[exchange] or database[exchange][coinpair]['timestamp'] <= data['timestamp']:
        database[exchange][coinpair] = data

def gen_test_data():
    '''
        Generate trade opportunity data to benchmark possible performance
    '''
    
    
    

if __name__ == '__main__':
    binance_client.start_poll(listener)
    kucoin_client.start_poll(listener)