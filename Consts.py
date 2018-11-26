from decimal import Decimal

TRADE_THRESHOLD = Decimal(0.15)  # Minimum estimated percent profit (after exchange fees) to perform a trade.
BUY_TRADE_AMOUNT = Decimal(0.25)  # Percent of the balance to spend on a buy order.
SELL_TRADE_AMOUNT = Decimal(0.5)  # Percent of the balance to spend on a sell order.
TIMESTAMP_THRESHOLD = 1000     # ignore data older than half second
POLL_INTERVAL = 0.25  # Poll every quarter second.

COINPAIRS = {
    # BTC Base
    'ETH-BTC': {'binance': 'ETHBTC', 'kucoin': 'ETH-BTC'},
    'NEO-BTC': {'binance': 'NEOBTC', 'kucoin': 'NEO-BTC'},
    'LTC-BTC': {'binance': 'LTCBTC', 'kucoin': 'LTC-BTC'},
    'VEN-BTC': {'binance': 'VENBTC', 'kucoin': 'VEN-BTC'},
    'BCH-BTC': {'binance': 'BCCBTC', 'kucoin': 'BCH-BTC'},
    'ETC-BTC': {'binance': 'ETCBTC', 'kucoin': 'ETC-BTC'},

    # ETH Base
    'NEO-ETH': {'binance': 'NEOETH', 'kucoin': 'NEO-ETH'},
    'LTC-ETH': {'binance': 'LTCETH', 'kucoin': 'LTC-ETH'},
    'VEN-ETH': {'binance': 'VENETH', 'kucoin': 'VEN-ETH'},
    'BCH-ETH': {'binance': 'BCCETH', 'kucoin': 'BCH-ETH'},
    'ETC-ETH': {'binance': 'ETCETH', 'kucoin': 'ETC-ETH'},

    # USDT Base
    'ETH-USDT': {'binance': 'ETHUSDT', 'kucoin': 'ETH-USDT'},
    'NEO-USDT': {'binance': 'NEOUSDT', 'kucoin': 'NEO-USDT'},
    'BTC-USDT': {'binance': 'BTCUSDT', 'kucoin': 'BTC-USDT'},
    'LTC-USDT': {'binance': 'LTCUSDT', 'kucoin': 'LTC-USDT'},
    'BCH-USDT': {'binance': 'BCCUSDT', 'kucoin': 'BCH-USDT'}
}
