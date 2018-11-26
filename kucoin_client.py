import time
from datetime import datetime
import threading
from decimal import Decimal
import random
import api_keys
import Consts
from abstract_client import AbstractClient
from kucoin.client import Client
from kucoin.exceptions import KucoinAPIException, KucoinRequestException

class KucoinClient(AbstractClient):

    def __init__(self, listener):
        self.exchange = 'kucoin'
        self.trade_fee = Decimal(0.001)
        self.client = Client(api_keys.kucoin[0], api_keys.kucoin[1])
        super(KucoinClient, self).__init__(listener)
        self.get_all_balances()

    def _buy(self, symbol, price, amount):
        result = self.client.create_buy_order(symbol, price, amount)
        self.open_orders[symbol] = [str(result['orderOid']), 'BUY', symbol]

    def _sell(self, symbol, price, amount):
        result = self.client.create_sell_order(symbol, price, amount)
        self.open_orders[symbol] = [str(result['orderOid']), 'SELL', symbol]

    def _cancel(self, symbol):
        order = self.open_orders.pop(symbol)
        self.client.cancel_order(order[0], order[1], symbol=order[2])
        time.sleep(1)
        if not self.is_order_fulfilled(order[0]):
            raise Exception("cancelled order not fulfilled!")

    def is_order_fulfilled(self, orderOid):
        try:
            for data in self.client.get_dealt_orders()['datas']:
                if data['orderOid'] == orderOid:
                    return True

        except (KucoinRequestException, KucoinAPIException) as e:
            print datetime.now(), "[Kucoin] is order fulfilled error", str(e).replace('\r\n', '')
            self.errors += 1

        return False

    def get_all_balances(self):
        # Kucoin paginates the coin balances and we can only retrieve 20 coins per page
        page = 1
        while True:
            try:
                result = self.client.get_all_balances_paged(limit=20, page=page)

                for balance in result['datas']:
                    self.coin_balances[str(balance['coinType'])] = Decimal(
                        str(balance['balance']))  # + Decimal(balance['freezeBalance'])

                page = result['currPageNo'] + 1
                if page > result['pageNos']:
                    break

            except (KucoinRequestException, KucoinAPIException) as e:
                print datetime.now(), "[Kucoin] get all balances error:", str(e).replace('\r\n', '')
                self.errors += 1
                break

        return self.coin_balances

    # Gets the buy/sell price and amount for one symbol at a time (inefficient).
    def _market_poll(self):
        result = {'success': False}
        result['client'] = self
        result['timestamp'] = int(time.time() * 1000)
        result['coinpairs'] = {}

        threads = []
        for symbol in self.exchange_symbols:
            thread = threading.Thread(target=self._symbol_poll, args=[symbol, result])
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()

        if len(result['coinpairs']) > 0:
            result['success'] = True

        return result

    def _symbol_poll(self, symbol, result):
        try:
            data = self.client.get_order_book(symbol, limit=1)

            if data['BUY'] is not None and data['SELL'] is not None:
                result['coinpairs'][self._get_arbitrager_coinpair(symbol)] = {
                    'buy': Decimal(str(data['BUY'][0][0])),
                    'buyAmount': Decimal(str(data['BUY'][0][1])),
                    'sell': Decimal(str(data['SELL'][0][0])),
                    'sellAmount': Decimal(str(data['SELL'][0][1]))
                }

        except (KucoinRequestException, KucoinAPIException) as e:
            print datetime.now(), "[Kucoin] market poll error", str(e).replace('\r\n', '')
            self.errors += 1

    # Gets the buy/sell price for all the symbols with one query but does not contain buy/sell amount (useless).
    @DeprecationWarning
    def market_poll_no_amount(self):
        threading.Timer(Consts.POLL_INTERVAL, self.market_poll_no_amount).start()
        timestamp = int(time.time() * 1000)
        try:
            coins = self.client.get_trading_symbols()
            if self.verbose:
                now = int(time.time() * 1000)
                print datetime.now(), "[Kucoin] market_poll took", now - timestamp, "ms."
        except (KucoinRequestException, KucoinAPIException) as e:
            print datetime.now(), "[Kucoin] market poll error", str(e).replace('\r\n', ' ')
            result = {'success': False}
            result['client'] = self
            return result

        result = {'success': True}
        result['client'] = self
        result['timestamp'] = timestamp
        result['coinpairs'] = {}

        for coin in coins:
            symbol = coin['symbol']
            if symbol in self.exchange_symbols:
                result['coinpairs'][self._get_arbitrager_coinpair(symbol)] = {
                    'buy': Decimal(str(coin['buy'])),
                    'sell': Decimal(str(coin['sell']))
                }
                # result['timestamp'] = coin['datetime']

        if self.callback is None:
            print result
        else:
            self.callback(result)


if __name__ == '__main__':
    client = KucoinClient(None)
    client.market_poll()
