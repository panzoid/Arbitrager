from binance_client import BinanceClient
from kucoin_client import KucoinClient
from decimal import Decimal

def get_balances_in_eth():
    kucoin_client = KucoinClient(None)
    binance_client = BinanceClient(None)
    kucoin_balances = kucoin_client.get_all_balances()
    binance_balances = binance_client.get_all_balances()
    rates = kucoin_client.client.get_currencies(['ETH', 'NEO', 'LTC', 'VEN', 'BCH', 'USDT', 'BTC', 'ETC'])['rates']

    ethValue = 0

    kucoinValue = 0
    for key, value in rates.items():
        if key == 'ETH':
            ethValue = Decimal(str(value['USD']))
            print "[Utils] 1 ETH in USD:", '{0:.2f}'.format(ethValue)

        usd_value = kucoin_balances[key] * Decimal(str(value['USD']))
        print "[Utils] Kucoin", key, "USD:", usd_value
        kucoinValue += usd_value

    print "[Utils] Kucoin total USD:", '{0:.2f}'.format(kucoinValue)

    binanceValue = 0
    for key, value in rates.items():
        if key == 'BCH':
            usd_value = binance_balances['BCC'] * Decimal(str(value['USD']))
        else:
            usd_value = binance_balances[key] * Decimal(str(value['USD']))

        print "[Utils] Binance", key, "USD:", usd_value
        binanceValue += usd_value

    print "[Utils] Binance total USD:", '{0:.2f}'.format(binanceValue)
    print "[Utils] Average total USD:", '{0:.2f}'.format(kucoinValue / 2 + binanceValue / 2)

    return (binanceValue / ethValue, kucoinValue / ethValue)

def rebalance():
    kucoin_client = KucoinClient(None)
    binance_client = BinanceClient(None)


if __name__ == '__main__':
    print get_balances_in_eth()