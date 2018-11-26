TRADE_THRESHOLD = 0.3 # percentage

sim_BTC = 1 # BTC
sim_ETH = 1 # BTC
sim_USDT = 1 # BTC

# Breakout Percentages
breakPerc = {
# BTC Base
'ETH-BTC': 0.3,
'NEO-BTC': 0.125,
'LTC-BTC': 0.2,
'VEN-BTC': 0.125,
'BCH-BTC': 0.125,
'ETC-BTC': 0.125,

# ETH Base
'NEO-ETH': 0.1875,
'LTC-ETH': 0.25,
'VEN-ETH': 0.1875,
'BCH-ETH': 0.1875,
'ETC-ETH': 0.1875,

# USDT Base
'ETH-USDT': 0.2,
'NEO-USDT': 0.115,
'BTC-USDT': 0.3,
'LTC-USDT': 0.15,
'BCH-USDT': 0.12,
'ETC-USDT': 0.115
}


COINPAIRS = {
    # BTC Base
    'ETH-BTC': {'binance': {'ETHBTC': breakPerc['ETH-BTC']/2 *sim_BTC}, 'kucoin': {'ETH-BTC':breakPerc['ETH-BTC']/2 *sim_BTC }},
    'NEO-BTC': {'binance': {'NEOBTC': breakPerc['NEO-BTC']/2 *sim_BTC}, 'kucoin': {'NEO-BTC':breakPerc['NEO-BTC']/2 *sim_BTC }},
    'LTC-BTC': {'binance': {'LTCBTC': breakPerc['LTC-BTC']/2 *sim_BTC}, 'kucoin': {'LTC-BTC':breakPerc['LTC-BTC']/2 *sim_BTC }},
    'VEN-BTC': {'binance': {'VENBTC': breakPerc['VEN-BTC']/2 *sim_BTC}, 'kucoin': {'VEN-BTC':breakPerc['VEN-BTC']/2 *sim_BTC }},
    'BCH-BTC': {'binance': {'BCCBTC': breakPerc['BCH-BTC']/2 *sim_BTC}, 'kucoin': {'BCH-BTC':breakPerc['BCH-BTC']/2 *sim_BTC }},
    'ETC-BTC': {'binance': {'ETCBTC': breakPerc['ETC-BTC']/2 *sim_BTC}, 'kucoin': {'ETC-BTC':breakPerc['ETC-BTC']/2 *sim_BTC }},

    # ETH Base
    'NEO-ETH': {'binance': {'NEOETH': breakPerc['NEO-ETH']/2 *sim_BTC}, 'kucoin': {'NEO-ETH': breakPerc['NEO-ETH']/2 *sim_BTC}},
    'LTC-ETH': {'binance': {'LTCETH': breakPerc['LTC-ETH']/2 *sim_BTC}, 'kucoin': {'LTC-ETH': breakPerc['LTC-ETH']/2 *sim_BTC}},
    'VEN-ETH': {'binance': {'VENETH': breakPerc['VEN-ETH']/2 *sim_BTC}, 'kucoin': {'VEN-ETH': breakPerc['VEN-ETH']/2 *sim_BTC}},
    'BCH-ETH': {'binance': {'BCCETH': breakPerc['BCH-ETH']/2 *sim_BTC}, 'kucoin': {'BCH-ETH': breakPerc['BCH-ETH']/2 *sim_BTC}},
    'ETC-ETH': {'binance': {'ETCETH': breakPerc['ETC-ETH']/2 *sim_BTC}, 'kucoin': {'ETC-ETH': breakPerc['ETC-ETH']/2 *sim_BTC}},

    # USDT Base
    'ETH-USDT': {'binance': {'ETHUSDT': breakPerc['ETH-USDT']/2 *sim_BTC}, 'kucoin': {'ETH-USDT': breakPerc['ETH-USDT']/2 *sim_BTC}},
    'NEO-USDT': {'binance': {'NEOUSDT': breakPerc['NEO-USDT']/2 *sim_BTC}, 'kucoin': {'NEO-USDT': breakPerc['NEO-USDT']/2 *sim_BTC}},
    'BTC-USDT': {'binance': {'BTCUSDT': breakPerc['BTC-USDT']/2 *sim_BTC}, 'kucoin': {'BTC-USDT': breakPerc['BTC-USDT']/2 *sim_BTC}},
    'LTC-USDT': {'binance': {'LTCUSDT': breakPerc['LTC-USDT']/2 *sim_BTC}, 'kucoin': {'LTC-USDT': breakPerc['LTC-USDT']/2 *sim_BTC}},
    'BCH-USDT': {'binance': {'BCCUSDT': breakPerc['BCH-USDT']/2 *sim_BTC}, 'kucoin': {'BCH-USDT': breakPerc['BCH-USDT']/2 *sim_BTC}},
    'ETC-USDT': {'binance': {'ETCUSDT': breakPerc['ETC-USDT']/2 *sim_BTC}, 'kucoin': {'ETC-USDT': breakPerc['ETC-USDT']/2 *sim_BTC}}
}

EXCHANGES = ['binance', 'kucoin']