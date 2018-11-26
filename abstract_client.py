import Consts
import time
import threading
from datetime import datetime

class AbstractClient(object):

    # Set to True to pause all client polling
    pause = False

    def __init__(self, listener):
        self.callback = listener
        self.exchange_symbols = []
        self.coin_balances = {}
        self.trade_rules = {}
        self.open_orders = {}
        self.verbose = False
        self.test_trades = False
        self.test_balances = False
        self.errors = 0
        self._error_monitor()
        for key, value in Consts.COINPAIRS.items():
            if value[self.exchange] is not None:
                self.exchange_symbols.append(value[self.exchange])

    def _resume(self):
        print '{0} [{1}] resuming market poll'.format(datetime.now(), self.exchange)
        AbstractClient.pause = False
        self.market_poll()

    # If we get more than 10 errors in a minute something may be wrong with the exchange
    def _error_monitor(self):
        if self.errors >= 10:
            print '{0} [{1}] too many errors detected'.format(datetime.now(), self.exchange)
            AbstractClient.pause = True

        self.errors = 0
        threading.Timer(60, self._error_monitor).start()

    def market_poll(self):
        if AbstractClient.pause:
            print '{0} [{1}] pausing market poll'.format(datetime.now(), self.exchange)
            threading.Timer(5 * 60, self._resume).start()
            return

        timestamp = int(time.time() * 1000)
        try:
            result = self._market_poll()

        except Exception as e:
            print '{0} [{1}] market poll error: {2}'.format(datetime.now(), self.exchange, str(e).replace('\r\n', ''))

        if self.verbose:
            now = int(time.time() * 1000)
            print '{0} [{1}] market poll took {2} ms'.format(datetime.now(), self.exchange, now - timestamp)

        if result is not None:
            if self.callback is None:
                print result
            else:
                self.callback(result)

        threading.Timer(Consts.POLL_INTERVAL, self.market_poll).start()

    def _get_exchange_symbol(self, coinpair):
        return Consts.COINPAIRS[coinpair][self.exchange]

    def buy(self, coinpair, price, amount, success=None):
        symbol = self._get_exchange_symbol(coinpair)

        if self.test_trades:
            print '{0} [TEST][{1}] buying {2} amount of {3} for price: {4}'.format(
                datetime.now(), self.exchange, amount, symbol, price)
            time.sleep(0.25)  # simulate network
            self.open_orders[symbol] = 1
            if success is not None:
                success.set(True)
            return

        try:
            self._buy(symbol, price, amount)
            print '{0} [{1}] buying {2} amount of {3} for price: {4}'.format(
                datetime.now(), self.exchange, amount, symbol, price)
            if success is not None:
                success.set(True)
        except Exception as e:
            print '{0} [{1}] buy error: {2}'.format(datetime.now(), self.exchange, str(e).replace('\r\n', ''))
            self.errors += 1
            if success is not None:
                success.set(False)

    # Place a sell order. Success will be set to true if order was placed successfully.
    def sell(self, coinpair, price, amount, success=None):
        symbol = self._get_exchange_symbol(coinpair)

        if self.test_trades:
            print '{0} [TEST][{1}] selling {2} amount of {3} for price: {4}'.format(
                datetime.now(), self.exchange, amount, symbol, price)
            time.sleep(0.25)  # simulate network
            self.open_orders[symbol] = 1
            if success is not None:
                success.set(True)
            return

        try:
            self._sell(symbol, price, amount)
            print '{0} [{1}] selling {2} amount of {3} for price: {4}'.format(
                datetime.now(), self.exchange, amount, symbol, price)
            if success is not None:
                success.set(True)
        except Exception as e:
            print '{0} [{1}] buy error: {2}'.format(datetime.now(), self.exchange, str(e).replace('\r\n', ''))
            self.errors += 1
            if success is not None:
                success.set(False)

    # Cancel an order. Success will be set to true if order was fulfilled.
    def cancel(self, coinpair, success=None):
        symbol = self._get_exchange_symbol(coinpair)

        if symbol not in self.open_orders:
            print '{0} [{1}] cancel error: open order does not exist for {2}'.format(datetime.now(), self.exchange, symbol)
            if success is not None:
                success.set(False)
            return

        if self.test_trades:
            self.open_orders.pop(symbol)
            time.sleep(1)  # simulate network
            print '{0} [TEST][{1}] cancelled order for {2}'.format(datetime.now(), self.exchange, symbol)
            if success is not None:
                success.set(True)
            return

        try:
            self._cancel(symbol)
            if success is not None:
                success.set(True)
        except Exception as e:
            print '{0} [{1}] cancel error: {2}'.format(datetime.now(), self.exchange, str(e).replace('\r\n', ''))
            if success is not None:
                success.set(False)

        self.get_all_balances()

    # Gets a cached coin balance. Use get_all_balances to bypass cache.
    def get_balance(self, coin):
        if self.test_balances:
            return 100
        elif coin in self.coin_balances:
            return self.coin_balances[coin]
        else:
            return 0

    # Converts an exchange's symbol to the arbitrager's coinpair
    def _get_arbitrager_coinpair(self, symbol):
        for key, value in Consts.COINPAIRS.items():
            if symbol == value[self.exchange]:
                return key

        return None


    def get_trade_rules(self, coinpair):
        symbol = self._get_exchange_symbol(coinpair)
        if symbol in self.trade_rules:
            return self.trade_rules[symbol]
        else:
            return None

    def has_open_order(self, coinpair):
        symbol = self._get_exchange_symbol(coinpair)
        return symbol in self.open_orders


class MutableBoolean:
    def __init__(self):
        self.value = False

    def __nonzero__(self):
        return self.value

    def set(self, value):
        self.value = value
