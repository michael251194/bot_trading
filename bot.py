import ccxt

# Initialise l'exchange Binance
exchange = ccxt.binance({
    'rateLimit': 2000,
    'enableRateLimit': True,
    'options': {
        'adjustForTimeDifference': True,
        'defaultType': 'future',
        'timeframes': {
            '1m': '1m',
            '3m': '3m',
            '1h': '1h',
            '1d': '1d',
            '1w': '1w',
            '1M': '1M',
        },
    },
    'apiKey': 'YOUR_API_KEY',
    'secret': 'YOUR_SECRET',
    'enableRateLimit': True,
    'rateLimit': 2000,
})

# Récupère les données de prix en temps réel pour le Bitcoin
ticker = exchange.fetch_ticker('GMT/USDT')

# Définir les paramètres de la stratégie de scalping
take_profit = 0.5 # En pourcentage
stop_loss = 1 # En pourcentage
lot_size = 0.01 # Taille de la position

# Boucle infinie pour surveiller le marché en temps réel
while True:
    # Récupère les données de prix en temps réel
    ticker = exchange.fetch_ticker('GMT/USDT')
    last_price = ticker['last']
    bid_price = ticker['bid']
    ask_price = ticker['ask']

    # Vérifie si le prix a augmenté de plus de X%
    if last_price >= (1 + take_profit/100) * bid_price:
        # Place un ordre de vente
        order = exchange.create_order('GMT/USDT', 'limit', 'sell', lot_size, last_price)

    # Vérifie si le prix a diminué de plus de X%
    elif last_price <= (1 - stop_loss/100) * ask_price:
        # Place un ordre d'achat
        order = exchange.create_order('GMT/USDT', 'limit', 'buy', lot_size, last_price)
