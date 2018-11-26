import time
import Utils
import datetime
import Consts
import threading
from abstract_client import MutableBoolean
from binance_client import BinanceClient
from kucoin_client import KucoinClient

clients = {}
arbitrages = {}
balances = {}

# daily number of trades
# daily amount earned
# % amount earned
# total and daily % earned
# number of possible trades
template_statistics = {'successful_trades': 0, 'wash_trades': 0, 'failed_trades': 0, 'missed_trades': 0, 'possible_trades': 0}
hourly_statistics = template_statistics.copy()
hour_count = 0

mutex = threading.Lock()

def market_listener(data):
    with mutex:
        if data['success']:
            client = data['client']
            if client not in clients or data['timestamp'] > clients[client]['timestamp']:
                clients[client] = data
                if client.exchange != binance_client.exchange:
                    find_arbitrage_opportunity(data)
        #else:
            # Cancel every arbitrage that involves the un-successful client
            #cancel_every_arbitrage(data['client'])
            # threading.Timer(60, cancel_every_arbitrage, [data['client']]).start()


def find_arbitrage_opportunity(data):
    my_client = data['client']
    for other_client in clients:
        if other_client != my_client:

            is_stale = False
            now = int(time.time() * 1000)
            if now - data['timestamp'] > Consts.TIMESTAMP_THRESHOLD or now - clients[other_client]['timestamp'] > Consts.TIMESTAMP_THRESHOLD:
                is_stale = True
                return

            for coinpair, my_trades in data['coinpairs'].items():
                if coinpair in clients[other_client]['coinpairs']:
                    my_sell_price = my_trades['buy']
                    my_buy_price = my_trades['sell']

                    other_trades = clients[other_client]['coinpairs'][coinpair]
                    other_sell_price = other_trades['buy']
                    other_buy_price = other_trades['sell']

                    trade_fees = my_client.trade_fee + other_client.trade_fee
                    buy_mine_sell_other_profit = (other_sell_price / my_buy_price - 1 - trade_fees) * 100
                    buy_other_sell_mine_profit = (my_sell_price / other_buy_price - 1 - trade_fees) * 100

                    if buy_mine_sell_other_profit >= Consts.TRADE_THRESHOLD:
                        place_arbitrage(coinpair, my_client, other_client)
                    elif buy_other_sell_mine_profit >= Consts.TRADE_THRESHOLD:
                        place_arbitrage(coinpair, other_client, my_client)
                    else:
                        # No arbitrage opportunities found, that means existing arbitrage opportunities are expired and must be cancelled.
                        cancel_arbitrage(coinpair, my_client, other_client)
                        # Wait 3 seconds for existing open orders to fulfill.
                        #threading.Timer(60, cancel_arbitrage, [coinpair, my_client, other_client]).start()


def place_arbitrage(coinpair, lower_price_client, higher_price_client):
    data = (coinpair, lower_price_client, higher_price_client)
    if data not in arbitrages:
        arbitrages[data] = 0

    arbitrages[data] += 1
    if arbitrages[data] == 1:  # Use a higher number if we want to wait for more market ticks before performing trade.
        (sell_coin, buy_coin) = coinpair.split('-')
        lower_price_balance = lower_price_client.get_balance(buy_coin)
        higher_price_balance = higher_price_client.get_balance(sell_coin)

        lower_buy_price = clients[lower_price_client]['coinpairs'][coinpair]['sell']
        lower_buy_amount = clients[lower_price_client]['coinpairs'][coinpair]['sellAmount']
        higher_sell_price = clients[higher_price_client]['coinpairs'][coinpair]['buy']
        higher_sell_amount = clients[higher_price_client]['coinpairs'][coinpair]['buyAmount']


        lower_price_rules = lower_price_client.get_trade_rules(coinpair)
        higher_price_rules = higher_price_client.get_trade_rules(coinpair)

        # First, verify that the trade volume adheres to the exchange's rules.
        amount = min(lower_buy_amount, higher_sell_amount)
        amount = apply_exchange_rules(amount, lower_price_rules, lower_buy_price, higher_price_rules, higher_sell_price)
        if amount <= 0:
            # This trade does not follow the exchange rules, disregard and do not add this trade to statistics.
            return

        # Second, adjust the trade volume so that we have enough balance to cover it.
        amount = min(amount, lower_price_balance / lower_buy_price * Consts.BUY_TRADE_AMOUNT,
                     higher_price_balance * Consts.SELL_TRADE_AMOUNT)
        amount = apply_exchange_rules(amount, lower_price_rules, lower_buy_price, higher_price_rules, higher_sell_price)
        hourly_statistics['possible_trades'] += 1
        profit = higher_sell_price / lower_buy_price - lower_price_client.trade_fee - higher_price_client.trade_fee

        if amount <= 0:
            hourly_statistics['missed_trades'] += 1
            print datetime.datetime.now(), '[Arbitrager] missed estimated profit of {0:.3f}% for {1} between {2} (buy) and {3} (sell) due to lack of funds.' \
                .format((profit - 1) * 100, coinpair, lower_price_client.exchange, higher_price_client.exchange)
        else:
            print datetime.datetime.now(),\
                '[Arbitrager] buy {0} on {1} and sell on {2} for estimated {3:.3f}% profit. Estimated nominal gain of {4:.8f} {5}.'\
                    .format(coinpair, lower_price_client.exchange, higher_price_client.exchange,
                            (profit - 1) * 100, (profit - 1) * amount, sell_coin)

            # We only want 8 decimal places for prices and amount
            lower_buy_price = "{:.8f}".format(lower_buy_price)
            higher_sell_price = "{:.8f}".format(higher_sell_price)
            amount = "{:.8f}".format(amount)

            buy_result = MutableBoolean()
            sell_result = MutableBoolean()
            buy_thread = threading.Thread(target=lower_price_client.buy, args=(coinpair, lower_buy_price, amount, buy_result))
            sell_thread = threading.Thread(target=higher_price_client.sell, args=(coinpair, higher_sell_price, amount, sell_result))
            buy_thread.start()
            sell_thread.start()
            buy_thread.join()
            sell_thread.join()

            if buy_result and not sell_result:
                print datetime.datetime.now(), "[Arbitrager] failed to place sell order"
                lower_price_client.cancel(coinpair)
            elif not buy_result and sell_result:
                print datetime.datetime.now(), "[Arbitrager] failed to place buy order"
                higher_price_client.cancel(coinpair)
            elif not buy_result and not sell_result:
                print datetime.datetime.now(), "[Arbitrager] failed to place both orders"


def apply_exchange_rules(amount, lower_price_rules, lower_buy_price, higher_price_rules, higher_sell_price):

    if lower_price_rules is not None and higher_price_rules is not None:
        if amount % lower_price_rules['stepAmount'] != 0 or amount % higher_price_rules['stepAmount'] != 0:
            amount -= amount % lcm(lower_price_rules['stepAmount'], higher_price_rules['stepAmount'])

    if lower_price_rules is not None:
        if amount % lower_price_rules['stepAmount'] != 0:
            amount -= amount % lower_price_rules['stepAmount']
        if amount < lower_price_rules['minAmount'] or amount > lower_price_rules[
            'maxAmount'] or amount * lower_buy_price < lower_price_rules['minNotional']:
            amount = -1

    if higher_price_rules is not None:
        if amount % higher_price_rules['stepAmount'] != 0:
            amount -= amount % higher_price_rules['stepAmount']
        if amount < higher_price_rules['minAmount'] or amount > higher_price_rules[
            'maxAmount'] or amount * higher_sell_price < higher_price_rules['minNotional']:
            amount = -1

    return amount

# Cancels arbitrages for the specified coinpair between two exchanges
def cancel_arbitrage(coinpair, client1, client2):
    for arbitrage in arbitrages:
        if client1 in arbitrage and client2 in arbitrage and coinpair == arbitrage[0]:
            _cancel_trade_(arbitrage, coinpair, client1, client2)


# Cancels all arbitrage orders between two exchanges
def cancel_all_arbitrage(client1, client2):
    for arbitrage in arbitrages:
        if client1 in arbitrage and client2 in arbitrage:
            _cancel_trade_(arbitrage, arbitrage[0], client1, client2)


# Cancels every arbitrage order that contains this exchange
def cancel_every_arbitrage(client):
    for arbitrage in arbitrages:
        if client in arbitrage:
            _cancel_trade_(arbitrage, arbitrage[0], arbitrage[1], arbitrage[2])


def _cancel_trade_(arbitrage, coinpair, client1, client2):
    arbitrages[arbitrage] = 0

    if client1.has_open_order(coinpair) and client2.has_open_order(coinpair):
        result1 = MutableBoolean()
        result2 = MutableBoolean()
        thread1 = threading.Thread(target=client1.cancel, args=(coinpair, result1))
        thread2 = threading.Thread(target=client2.cancel, args=(coinpair, result2))
        thread1.start()
        thread2.start()
        thread1.join()
        thread2.join()

        if result1 and result2:
            # Both trades were fulfilled when we cancelled.
            # We gained the estimated arbitrage profit for a net gain.
            print datetime.datetime.now(), "[Arbitrager]", coinpair, "arbitrage was a SUCCESS!"
            hourly_statistics['successful_trades'] += 1
        elif not result1 and not result2:
            # Both were cancelled with neither being fulfilled.
            # There is no arbitrage profit and no exchange fees were taken so we did not gain or lose.
            print datetime.datetime.now(), "[Arbitrager]", coinpair, "arbitrage was a WASH..."
            hourly_statistics['wash_trades'] += 1
        else:
            # One trade was fulfilled while the other was cancelled.
            # There is no arbitrage profit but we lost one of the exchange's fee for a net loss.
            print datetime.datetime.now(), "[Arbitrager]", coinpair, "arbitrage was a FAILURE..."
            hourly_statistics['failed_trades'] += 1


# Find greatest common divisor of a and b
def gcd(a, b):
    while b > 0:
        a, b = b, a % b
    return a

# Find lowest common multiple of a and b
def lcm(a, b):
    return a * b / gcd(a, b)


def one_hour_timer():
    global hour_count
    global hourly_statistics
    global daily_statistics
    global kucoin_starting_balance
    global binance_starting_balance

    hour_count += 1
    (binance_balance, kucoin_balance) = Utils.get_balances_in_eth()

    print datetime.datetime.now(), "[Arbitrager] -----", hour_count, "hour statistics begin -----"
    for key, value in hourly_statistics.items():
        print datetime.datetime.now(), "[Arbitrager]", key, "=", value
    print datetime.datetime.now(),"[Arbitrager] Binance gain in ETH: {0:.8f} ({1:.3f}%)".format(
        binance_balance - binance_starting_balance, (binance_balance / binance_starting_balance - 1 ) * 100)
    print datetime.datetime.now(), "[Arbitrager] Kucoin gain in ETH: {0:.8f} ({1:.3f}%)".format(
        kucoin_balance - kucoin_starting_balance, (kucoin_balance / kucoin_starting_balance - 1) * 100)
    print datetime.datetime.now(), "[Arbitrager] Total gain in ETH: {0:.8f} ({1:.3f}%)".format(
        kucoin_balance - kucoin_starting_balance + binance_balance - binance_starting_balance,
        ((kucoin_balance + binance_balance) / (kucoin_starting_balance + binance_starting_balance) - 1) * 100)
    print datetime.datetime.now(), "[Arbitrager] -----", hour_count, "hour statistics end -------"

    if hour_count == 24:
        hour_count = 0
        hourly_statistics = template_statistics.copy()
        binance_starting_balance = binance_balance
        kucoin_starting_balance = kucoin_balance

    threading.Timer(60*60, one_hour_timer).start()


if __name__ == '__main__':
    threading.Timer(60*60, one_hour_timer).start()

    global binance_starting_balance
    global kucoin_starting_balance

    (binance_starting_balance, kucoin_starting_balance) = Utils.get_balances_in_eth()

    binance_client = BinanceClient(market_listener)
    kucoin_client = KucoinClient(market_listener)

    kucoin_client.market_poll()
    binance_client.market_poll()
