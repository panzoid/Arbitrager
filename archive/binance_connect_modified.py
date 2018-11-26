#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Binance api connection and data aggregation.

"""
__all__ = ['process_message', 'BN_Connect', 'CryptoCoin']


import sys
import os
#sys.path.append(r'C:\Users\Tony\Desktop\Coding Software\Python Resources\python_packages')
from binance.client import Client
#from binance.depthcache import DepthCacheManager
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import math
import networkx as nx
import datetime


from binance.websockets import BinanceSocketManager


# start aggregated trade websocket for BNBBTC
def process_message(msg):
    print("message type: {}".format(msg['e']))
    print(msg)
    

def unix_time_millis(dt):
    '''This is the time that the server operates on.
        Ensure that the passed datetime is in UTC.'''
    
    epoch = datetime.datetime.utcfromtimestamp(0)
    
    if type(dt) == datetime.date:
        dt = datetime.datetime.combine(dt, datetime.datetime.min.time())
    
    return int((dt - epoch).total_seconds() * 1000.0)

def millis_to_datetime(milliseconds):
    
    epoch = datetime.datetime.utcfromtimestamp(0)
    
    return epoch + datetime.timedelta(milliseconds = milliseconds)


def BN_Connect(key_file):
    '''Takes a filepath to a text file with your api key and api secret on the 
        first 2 lines. Returns a binance client.'''
    
    with open(key_file, 'r') as f:
        
        api_key = f.readline().strip()
        api_secret = f.readline().strip()
        
    client = Client(api_key, api_secret)
    
    return client

def process_depth(dcm):
    '''Gets the current bids and asks for a particular coin pair.'''
    
    
    depth_cache = dcm.get_depth_cache()
    
    
    print("symbol {}".format(depth_cache.symbol))
    print("top 5 bids")
    print(depth_cache.get_bids()[:5])
    print("top 5 asks")
    print(depth_cache.get_asks()[:5])
    

class CryptoCoin(object):
    '''This will hold a reference to a single crypto coin.'''
    
    def __init__(self, symbol):
        
        self.symbol = symbol
        
        
class BN_CoinPair(object):
    '''Holds pairs of crypto coins.

    '''
    
    def __init__(self, base, quote, client):
        
        self.base = base
        self.quote = quote
        self.client = client # Reference to the API client
        
    def get_price(self, coin_to_buy):
        '''This is the amount of coins you must pay to buy the coin_to_buy.
        
            The price is calculated as the average between the bid and ask in the order book.
        '''
        
        # get the proper symbol for the buy
        sym = self.quote.symbol + self.base.symbol            
        
        # get the order book for this symbol
        book = self.client.get_orderbook_ticker(symbol = sym)
        
        # get the latest bid and asks
        bid = float(book['bidPrice'])
        ask = float(book['askPrice'])
        
        price = (bid + ask)/2
        
        if coin_to_buy == self.base:
            price = 1/price
            
        return price
    
    def get_price_from_list(self, coin_to_buy, price_list):
        
        _d = next((x for x in price_list if x['symbol'] == self.get_symbol()))
        
        if coin_to_buy == self.base:
            return float(_d['price'])
        else:
            return 1/float(_d['price'])
        

    def get_symbol(self):
        return self.quote.symbol + self.base.symbol
        
        
class BN_Exchange(object):
    '''This will hold access to all of the coin pairs available in the market'''
    
    def __init__(self, coin_pairs, client):
        
        self.coin_pairs = coin_pairs
        self.client = client

        # create the buy/sell newtork
        self.create_buy_sell_network()

    @classmethod
    def from_symbols(cls, symbols, client):
        # Convert a list of symbols into coins and coin pairs.
        
        lst_coins = []
        for sym in symbols:
            coin = CryptoCoin(sym)
            lst_coins.append(coin)
            
        # base assets
        baseAssets = [x for x in lst_coins if x.symbol in ['BTC', 'ETH', 'BNB', 'USDT']]
            
        lst_tickers = client.get_all_tickers()
        lst_tickers = [x['symbol'] for x in lst_tickers]
        
        lst_coin_pairs = []
        for base in baseAssets:
            for quote in [x for x in lst_coins if x != base]:
            
                # first test to see if this is a valid coin pair on the exchange
                # this returns none if this is not valid
#                print('Querying symbol %s' % quote.symbol+base.symbol)
#                info = client.get_symbol_info(quote.symbol+base.symbol)
                
                if quote.symbol+base.symbol in lst_tickers:
                    print('Added symbol %s' % quote.symbol+base.symbol)
                    coin_pair = BN_CoinPair(base, quote, client)
                    lst_coin_pairs.append(coin_pair)
                
        return cls(lst_coin_pairs, client)
    
    def get_coin_from_symbol(self, symbol):
        
        coins = self.get_all_coins()
        
        if symbol in [x.symbol for x in coins]:
            return next((x for x in coins if x.symbol == symbol))
        
    
    def get_all_coins(self):
        
        lst_coins = []
        
        for pair in self.coin_pairs:
            lst_coins.append(pair.base)
            lst_coins.append(pair.quote)
            
        return list(set(lst_coins))
    
    def get_coin_pair(self, base_sym, quote_sym):
        
        if type(base_sym) != str:
            base_sym = base_sym.symbol
        if type(quote_sym) != str:
            quote_sym = quote_sym.symbol
        
        try:
            return next((x for x in self.coin_pairs if x.base.symbol == base_sym and x.quote.symbol == quote_sym))
        except:
            print('%s%s is not a valid coin pair.' % (base_sym, quote_sym))
        
        
    def get_history_from_coin_pair(self, pair, start_date, 
                                   end_date = datetime.datetime.utcnow(), interval = '5m'):
        
        return self.get_history(pair.base, pair.quote, start_date, end_date, interval)
    
    
    def get_history(self, base, quote,
                        start_date, end_date = datetime.datetime.utcnow(),
                        interval = '5m'):
        '''This will return the history of a base/quote pair from the 
            start to the end time.'''
        
        # get the referenced pair
        pair = self.get_coin_pair(base, quote)
        
        lst_klines = []
        
        at_end = False
        start = unix_time_millis(start_date)
        end = unix_time_millis(end_date)
        
        if end > unix_time_millis(datetime.datetime.utcnow()):
            end = unix_time_millis(datetime.datetime.utcnow())
        
        count = 0
        
        while not at_end and count < 1000:
        
        
            klines = self.client.get_klines(symbol = pair.get_symbol(), interval = interval,
                                           startTime = start, endTime = end)
            klines = self.kline_to_dict(klines)

            # check if we were able to get all of the range that we wanted
            if klines[-1]['close_time'] >= end:
                klines = [x for x in klines if x['close_time'] <= end]
                at_end = True
            else:
                start = klines[-1]['close_time']
        
        
            lst_klines.extend(klines)
            count += 1 # don't get stuck in a very long loop
            
        df = self.dict_list_to_dataframe(lst_klines)
        
        df['open_datetime'] = df['open_time'].apply(lambda x: millis_to_datetime(x))
        df['close_datetime'] = df['close_time'].apply(lambda x: millis_to_datetime(x))
            
        return df
        
    def kline_to_dict(self, kline_list):
        
        keys = ['open_time', 'open', 'high', 'low', 'close', 'volume', 'close_time',
                    'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume',
                    'taker_buy_quote_asset_volume', 'ignore']
        
        lst_ret = []
        
        for kline in kline_list:
            d_ret = dict()
            
            for key, value in zip(keys, kline):
                d_ret[key] = value
            lst_ret.append(d_ret)
            
        return lst_ret
        
    def dict_list_to_dataframe(self, lst):
        '''Takes a list of individual dictionaries with the same keys and returns 
            a data frame.'''
            
        keys = [x for x in lst[0].keys()]
        
        _d = dict()
        for key in keys:
            _d[key] = []
            
        for d_entry in lst:
            for key in keys:
                _d[key].append(d_entry[key])
                
                
        df = pd.DataFrame.from_dict(_d)
        
        # try to convert all to numerics
        for col in df.columns:
            df.loc[:, col] = pd.to_numeric(df.loc[:, col], errors='ignore')
        
        
        return df
        
    
            
    def create_buy_sell_network(self):
        '''Use networkx to create a graph to find the best path to buy coins.
        
            The network will allow you to explore all of the paths between coins to find that which 
            returns the most of the target coin.'''
        
        # create a directed graph
        g = nx.DiGraph()
        
        print('Creating nodes...')
        # each coin will be a node
        for coin in self.get_all_coins():
            
            g.add_node(coin)        
        
        price_list = self.client.get_all_tickers()
        
        print('Creating links...')
        # links should tell how much of the target coin you would get for 1 source coin
        for base, quote, pair in [(x.base, x.quote, x) for x in self.coin_pairs]:
            
            g.add_edge(base, quote, price_fxn = lambda: pair.get_price_from_list(base, price_list), price = pair.get_price_from_list(base, price_list))
            g.add_edge(quote, base, price_fxn = lambda : pair.get_price_from_list(quote, price_list), price = pair.get_price_from_list(quote, price_list))
            
            print('Added link from %s to %s' % (base.symbol, quote.symbol))
            
        self.buy_sell_graph = g
        
#    def update_buy_sell_network(self):
#        '''Updates the current price of all coins in the buy sell graph.
#        
#            This is slow as it needs to query the exchange for every pair.
#            Could benefit from parallelization.'''
#        
#        g = self.buy_sell_graph
#        
#        for node1, node2 in self.buy_sell_graph.edges:
#            
#            g[node1][node2]['price'] = g[node1][node2]['price_fxn']()
            
            
    def get_price_from_graph(self, coin1, coin2):
        
        if type(coin1) == str:
            coin1 = self.get_coin_from_symbol(coin1)
            
        if type(coin2) == str:
            coin2 = self.get_coin_from_symbol(coin2)
        
        
        return self.buy_sell_graph[coin1][coin2]['price']
    
    
            
    def get_price_from_coin_chain(self, coin_chain, qty_to_sell = 1,
                                  trade_fee = .0005):
        '''Follows a chain of coins to find the amount of the final coin you can get from
            selling the qty_to_sell of the first coin in the chain through this sequence.
            
            Essentially you want to see if going through different coins can get you more 
            of the final coin.
            
            When using BNB for the fees, the trading fee is .05% of the transaction, so this 
            is multiplied through every trade.
            '''
        
        qty = qty_to_sell
        
        for coin1, coin2 in zip(coin_chain[:-1], coin_chain[1:]):
            
            qty = qty * self.get_price_from_graph(coin1, coin2) * (1 - trade_fee)
            
        return qty
    
    def get_best_trade_chain(self, coin_to_sell, coin_to_buy, max_steps = 4):
        '''Uses the buy sell graph to identify the best way to buy the coin_to_buy using the coin_to_sell.
            The optional max_steps limits the number of transaction steps you can take.'''
            
        chains = self.get_potential_trade_chains(coin_to_sell, coin_to_buy, max_steps)
        
        best_res = max((x['coins_bought'] for x in chains))
        
        best_path = next((x for x in chains if x['coins_bought'] == best_res))
        
        print('Best path from %s to %s is: %s' % (coin_to_sell.symbol, coin_to_buy.symbol, '->'.join([x.symbol for x in best_path['path']])))
        print('1 %s will yield %6.4f %s' % (coin_to_sell.symbol, best_path['coins_bought'], coin_to_buy.symbol))
        
        try:
            std_result = self.get_price_from_coin_chain([coin_to_sell, coin_to_buy])
            print('The simple %s->%s would yield %6.4f' % (coin_to_sell.symbol, coin_to_buy.symbol, std_result))
        except:
            pass # you cannot make a straight trade between the coins
            
        return best_path['path'], best_path['coins_bought']
        
        
        
    def get_potential_trade_chains(self, coin_to_sell, coin_to_buy, max_steps = 4):
        '''Using the buy/sell graph, gets all possible routes between the coins.'''
        
        # create a  dict to hold the results
        lst_res = []
        
        # get the graph
        g = self.buy_sell_graph
        
        # find all of the paths between the coins
        paths = nx.all_simple_paths(g, coin_to_sell, coin_to_buy, cutoff = 4)
        
        # add all of the final prices to the dict
        for path in paths:
            _d = dict()
            _d['path'] = path
            _d['coins_bought'] = self.get_price_from_coin_chain(path)
            lst_res.append(_d)
            
        return lst_res
        
    def check_trade_chain(self, chain):
        '''Check the current prices on the trade chain.'''
        
        g = self.buy_sell_graph
        
        for node1, node2 in zip(chain[:-1], chain[1:]):
            
            g[node1][node2]['price'] = g[node1][node2]['price_fxn']()
            
        current_rate = self.get_price_from_coin_chain(chain)
        print('%s will yield %6.4f' % ('->'.join([x.symbol for x in chain]), current_rate ))
        
        return current_rate
        
    def find_best_cycle(self):
        '''Find the best trade cycle based on the current network.'''
        
        d_results = dict()
        
        best = 0
        
        for coin in self.get_all_coins():
            
            path, coins_bought = self.get_best_trade_chain(coin, coin)
            
            d_results[coin] = {
                    'path' : path,
                    'coins_bought' : coins_bought
                    }
            
            if coins_bought > best:
                best = coins_bought
                best_dict = d_results[coin]
               
        current_rate = self.check_trade_chain(best_dict['path'])
        
        
def obtain_trade_history(symbols):
    ''' Obtain the entire trade history '''
    
    trades_prices = {}
    
    for symbol in symbols:
        try:
            trades = client.get_my_trades(symbol=symbol)
            trades_prices[symbol] = trades
        except: continue
    return trades_prices


def evaluate_performance(recent_trades, exchange, BTC_price, volume):  
    ''' Evaluate Current Performance '''          
    performance = {'BTC':{}, 'USDT':{}, 'Current_Amount(USDT)':0}
    
    for coinpair, buy_cost in recent_trades.items():
        try:
            if coinpair[-3:] in ['BTC', 'LTC', 'ETH', 'BNB']:
                price = float(exchange.get_price_from_graph(str(coinpair[-3:]),str(coinpair[:-3])))
                performance['Current_Amount(USDT)'] = performance['Current_Amount(USDT)'] + (float(volume[str(coinpair[:-3])])  * price * BTC_price)
            elif coinpair[-4:] == 'USDT':
                price = float(exchange.get_price_from_graph(str(coinpair[-4:]),str(coinpair[:-4])))
                performance['Current_Amount(USDT)'] = performance['Current_Amount(USDT)'] + (float(volume[str(coinpair[:-4])]) * price * BTC_price)
            performance['BTC'][coinpair] = {'Quantity':buy_cost['Qty'],'Buy Price':buy_cost['Price'], 'Current Price':price, 'Performance':((price - buy_cost['Price'])/buy_cost['Price'])*100.}
            if coinpair[-3:] in ['BTC', 'LTC', 'ETH', 'BNB']:
                performance['USDT'][coinpair] = {'Quantity':volume[str(coinpair[:-3])],'Buy Price':buy_cost['Price']*BTC_price, 'Current Price':price*BTC_price, 'Performance':((price - buy_cost['Price'])/buy_cost['Price'])*100., 'Dollar_Amount':(float(volume[str(coinpair[:-3])]) * price * BTC_price)}
            elif coinpair[-4:] == 'USDT':
                performance['USDT'][coinpair] = {'Quantity':volume[str(coinpair[:-4])],'Buy Price':buy_cost['Price']*BTC_price, 'Current Price':price*BTC_price, 'Performance':((price - buy_cost['Price'])/buy_cost['Price'])*100., 'Dollar_Amount':(float(volume[str(coinpair[:-3])]) * price * BTC_price)}
        except KeyError: continue
        
    return performance    
            
                                                                                                                                                                                                                        
def get_trade_prices(symbols, volume):
    ''' Get my most up-to-date trade cost '''
    
    trades_prices = {}
    
    for symbol in symbols:
        try:
            trades = client.get_my_trades(symbol=symbol)
            trades_prices[symbol] = trades
        except: continue
    
    recent_trades = {}
    for coinpair, v in trades_prices.items():
        if v:
            if v[-1]['isBuyer']: 
                recent_trades[coinpair] = {'Price':float(v[-1]['price']),'Qty':float(v[-1]['qty'])}    
                
    return recent_trades    
    
def process_trade_history(symbols):
    ''' Process Trades History to Obtain total quantity and average price paid '''
    
    trades_prices = {}
    
    for symbol in symbols:
        try:
            trades = client.get_my_trades(symbol=symbol)
            avg_price = 0; quantity = 0
            keep_track_price = 0; keep_track_quantity = 0
            keep_track = False
            print symbol
            for trade in trades:
                isBuyer = trade['isBuyer']
                if isBuyer:
                    quantity = quantity + trade['qty']
                else:
                    quantity = quantity - trade['qty']
                price = trade['price']
                if quantity == 0: keep_track = True
                if keep_track:
                    if isBuyer:
                        keep_track_price = keep_track_price + price * trade['qty']
                        keep_track_quantity = keep_track_quantity + trade['qty']
                    else:
                        keep_track_price = keep_track_price - price * trade['qty']
                        keep_track_quantity = keep_track_quantity - trade['qty']
                        
            avg_price = keep_track_price / keep_track_quantity
            print keep_track_quantity, quantity
            
            trades_prices[symbol] = {'avg_price':avg_price, 'quantity':quantity}
        except Exception as e: print e
        
    return trades_prices
        


def display_performance(performance):
    
    for k, v in performance.items():
        print k
        
        for k1, v1 in performance.items():
            if k1 != 'Current_Amount(USDT)':
                print '   ', k1
            
                for k2, v2 in v1.items():
                    print '        ', k2
                    for k3, v3 in v2.items():
                        print '              ', k3, v3
            else: print k1, v1
    

'''
Trading Functions

    limit_buy_coin(symbol, quantity, price)
    
        order = client.order_limit_buy(symbol=symbol,quantity=quantity,price=price)


    limit_sell_coin(symbol, quantity, price)
    
        order = client.order_limit_sell(symbol=symbol,quantity=quantity,price=price)
       
       
    market_buy_coin(symbol, quantity)
    
        order = client.order_market_buy(symbol=symbol,quantity=quantity)


    market_sell_coin(symbol, quantity)
    
        order = client.order_market_sell(symbol=symbol,quantity=quantity)
                                       
                                                                             
    check_order_status(symbol, orderId)
    
        order = client.get_order(symbol=symbol,orderId=orderId)                                                                                                                                                                                                                  
                                        
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        
    cancel_order(symbol, orderId)
    
        order = client.cancel_order(symbol=symbol,orderId=orderId)
        
        
    get_coin_balance(coin)
    
        balance = client.get_asset_balance(asset=coin) 
  
'''    


if __name__ == '__main__':
     
    most_stable_coins = ['USDT','XMR','ETC','LTC']
    stable_coins = ['ETH','XRP','XLM','ADA','NEO','IOTA','DASH','ZEC','ZRX','BNB','ICX', 'VEN']
    coins = most_stable_coins + stable_coins
          
    client = BN_Connect(r'C:\Users\Tony\Desktop\Crypto-scripts\api_key.txt')
    
    binance_limits = {'Request_per_min':1200, 'Orders_per_sec':10, 'Orders_per_24h':100000}    
    
    i = 0

    # get all symbol prices
    info = client.get_exchange_info()
    symbols = info['symbols']
    symbols = [x['baseAsset'] for x in symbols]
    symbols = list(set(symbols))
    symbols.append('USDT')
    
    #use stable coins
    #symbols = coins
    
    coinbases = ['BTC']#,'ETH','BNB','USDT']
    coinpairs = []
    
    # Create all the coin pairs
    for symbol in symbols:
        for coinbase in coinbases:
            coinpairs.append(symbol+coinbase)
    
    #volume = {}
    #for symbol in symbols: 
    #    balance = client.get_asset_balance(asset=symbol)
    #    if float(balance['free']): volume[symbol] = balance['free']
    #    
    #recent_trades = get_trade_prices(coinpairs, volume)
    
    #trades_prices = process_trade_history(symbols)

    
    # Open a trade websocket for BNBBTC
    #bm = BinanceSocketManager(client)
    #bm.start_aggtrade_socket('BNBBTC', process_message)
    #bm.start()
    
    #start_multiplex_socket(streams, callback)
    #def process_m_message(msg):
    #    print("stream: {} data: {}".format(msg['stream'], msg['data']))
    #
    ## pass a list of stream names
    #conn_key = bm.start_multiplex_socket(['bnbbtc@aggTrade', 'neobtc@ticker'], process_m_message)    
    #
    #
    
#    while i == 0:
#        
#        exchange = BN_Exchange.from_symbols(symbols=symbols, client = client)
#            
#        BTC_price =  exchange.get_price_from_graph('USDT','BTC')
#        
#        performance = evaluate_performance(recent_trades, exchange, BTC_price, volume)
#        
#        # Get ticker (24 h)
#        tickers = client.get_ticker()
#        
##        for j in tickers:
##
##            print 'symbol', j['symbol']
##            print 'volume', j['volume']
##            print 'lastPrice', j['lastPrice']
##            print 'priceChangePercent', j['priceChangePercent']
##            print ' '
#        
#        display_performance(performance)                        
#        i = i + 1

    #