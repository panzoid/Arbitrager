import time
from datetime import datetime
import threading
from decimal import Decimal
from abstract_client import AbstractClient
from binance.client import Client
import api_keys
import Consts
from binance.enums import *
from binance.exceptions import *


class BinanceClient(AbstractClient):

    def __init__(self, listener):
        self.exchange = 'binance'
        self.trade_fee = Decimal(0.0005)
        self.client = Client(api_keys.binance[0], api_keys.binance[1])
        super(BinanceClient, self).__init__(listener)
        self._get_exchange_info()
        self.get_all_balances()

    def _buy(self, symbol, price, amount):
        result = self.client.create_order(
            symbol=symbol,
            quantity=amount,
            price=price,
            side=SIDE_BUY,
            type=ORDER_TYPE_LIMIT,
            timeInForce=TIME_IN_FORCE_GTC
        )
        self.open_orders[symbol] = result['orderId']

    def _sell(self, symbol, price, amount):
        result = self.client.create_order(
            symbol=symbol,
            quantity=amount,
            price=price,
            side=SIDE_SELL,
            type=ORDER_TYPE_LIMIT,
            timeInForce=TIME_IN_FORCE_GTC
        )
        self.open_orders[symbol] = result['orderId']

    def _cancel(self, symbol):
        orderId = self.open_orders.pop(symbol)
        try:
            self.client.cancel_order(
                symbol=symbol,
                orderId=orderId
            )
        # Binance throws API exception if the order is not open so we'll have to check if it's fulfilled here.
        except BinanceAPIException as e:
            time.sleep(1)
            if not self.is_order_fulfilled(symbol, orderId):
                # Order was not fulfilled, re-throw exception
                raise e
        except BinanceRequestException as e:
            self.errors += 1
            raise e

    def is_order_fulfilled(self, symbol, orderId):
        try:
            for data in self.client.get_my_trades(symbol=symbol):
                if data['orderId'] == int(orderId):
                    return True

        except (BinanceRequestException, BinanceAPIException) as e:
            print datetime.now(), "[Binance] is order fulfilled error", e
            self.errors += 1

        return False

    def get_all_balances(self):
        try:
            result = self.client.get_account()

            for balance in result['balances']:
                self.coin_balances[str(balance['asset'])] = Decimal(
                    str(balance['free']))  # + Decimal(balance['locked'])

            return self.coin_balances

        except (BinanceRequestException, BinanceAPIException) as e:
            print datetime.now(), "[Binance] get all balances error:", str(e).replace('\r\n', '')
            self.errors += 1

    def _market_poll(self):
        result = {'success': False}
        result['client'] = self
        result['timestamp'] = int(time.time() * 1000)
        result['coinpairs'] = {}

        try:
            coins = self.client.get_orderbook_tickers()

            for coin in coins:
                symbol = str(coin['symbol'])
                if symbol in self.exchange_symbols:
                    result['coinpairs'][self._get_arbitrager_coinpair(symbol)] = {
                        'buy': Decimal(str(coin['bidPrice'])),
                        'buyAmount': Decimal(str(coin['bidQty'])),
                        'sell': Decimal(str(coin['askPrice'])),
                        'sellAmount': Decimal(str(coin['askQty']))
                    }

        except (BinanceRequestException, BinanceAPIException) as e:
            print datetime.now(), "[Binance] market poll error", str(e).replace('\r\n', '')
            self.errors += 1

        if len(result['coinpairs']) > 0:
            result['success'] = True

        return result

    def _get_exchange_info(self):
        result = self.client.get_exchange_info()
        for symbol in result['symbols']:
            sym = str(symbol['symbol'])
            self.trade_rules[sym] = {}
            trade_rule = self.trade_rules[sym]
            for filter in symbol['filters']:
                if filter['filterType'] == 'PRICE_FILTER':
                    trade_rule['minPrice'] = Decimal(filter['minPrice'])
                    trade_rule['maxPrice'] = Decimal(filter['maxPrice'])
                    trade_rule['stepPrice'] = Decimal(filter['tickSize'])
                elif filter['filterType'] == 'LOT_SIZE':
                    if sym == 'NEOETH':
                        trade_rule['minAmount'] = Decimal(0.1)
                    elif sym == 'LTCETH':
                        trade_rule['minAmount'] = Decimal(0.05)
                    else:
                        trade_rule['minAmount'] = Decimal(filter['minQty'])
                    trade_rule['maxAmount'] = Decimal(filter['maxQty'])
                    trade_rule['stepAmount'] = Decimal(filter['stepSize'])
                elif filter['filterType'] == 'MIN_NOTIONAL':
                    trade_rule['minNotional'] = Decimal(filter['minNotional'])


if __name__ == '__main__':
    client = BinanceClient(None)
    client.market_poll()

