import time
import datetime
from binance.client import Client
from binance.enums import *
import requests
import numpy as np

api_key='YOUR_KEY'
api_secret ='YOUR_KEY'

#current_price = float(input("quel est le prix actuel du token ou quel prix de base veux-tu définir ? "))
symbol = 'GMTUSDT'
pourcentage_trade_balance = 0.5 #pourcentage du capital à trader par position
start_leverage = 20 #levier 
deadband = 0.0013
SP_long = 0.0050 #pourcentage stop loss pour les longs
SP_short = 0.0050 #pourcentage take profit pour les longs
decimal_TP_SP_price = 4

interval = KLINE_INTERVAL_1HOUR
fast_ma_period = 10 #longeur MA
slow_ma_period = 30 #longeur MA

price = 0.0
open_positions = False
first_scan = True
order_type = FUTURE_ORDER_TYPE_MARKET
save_amount = 0
buy = False
sell = False
# levier
leverage = start_leverage

#modifier le time out de connexion
url = "https://fapi.binance.com/fapi/v1/ping"
timeout = 60  # temps limite de 30 secondes
response = requests.get(url, timeout=timeout)

# Fonction de calcul de la moyenne mobile
def calculate_ma(prices, period):
    ma = np.zeros(len(prices) - period + 1)
    for i in range(period - 1, len(prices)):
        ma[i - period + 1] = np.mean(prices[i - period + 1:i + 1])
    return ma

print("start")
# Boucle infinie pour surveiller le marché en temps réel
while True:
    now = datetime.datetime.now()
    client = Client(api_key, api_secret)
    client.futures_change_leverage(symbol=symbol, leverage=leverage)

    #si position ouverte
    positions = client.futures_position_information()
    open_positions = False
    for position in positions:
        # si la quantité de la position est différente de zéro, la position est considérée comme ouverte
        if float(position['positionAmt']) != 0:
            open_positions = True

    # Récupère le ticker du marché 
    ticker = client.futures_symbol_ticker(symbol=symbol)
    
    # Récupère le solde du compte pour la devise USDT
    balance = client.futures_account_balance()
    for asset in balance:
        if asset['asset'] == 'USDT':
           usdt_balance = float(asset['balance'])
       
    price = float(ticker['price'])
    usdt_amount = pourcentage_trade_balance*usdt_balance  
    amount = int(usdt_amount / price*leverage)
    stop_loss_long = round((1-SP_long) * price, decimal_TP_SP_price)
    stop_loss_short = round((1+SP_short) * price, decimal_TP_SP_price)

    # Récupération des données de prix
    klines = client.futures_klines(symbol=symbol, interval=interval, limit=1000)
    prices = np.array([float(kline[4]) for kline in klines])
    # Calcul de la moyenne mobile rapide et lente
    fast_ma = calculate_ma(prices, fast_ma_period)
    slow_ma = calculate_ma(prices, slow_ma_period)
    # Dernières valeurs de la moyenne mobile
    last_fast_ma = fast_ma[-1]
    last_slow_ma = slow_ma[-1]

    buy = False
    sell = False
    if open_positions == False:
        if last_fast_ma > last_slow_ma:
            buy = True
            sell = False
        elif last_fast_ma < last_slow_ma:
            buy = False
            sell = True

    #Long/buy
    if  buy == True:     
        client.futures_cancel_all_open_orders(symbol=symbol)
        # création de l'ordre d'achat
        long_order = client.futures_create_order(
            symbol=symbol,
            side=SIDE_BUY,
            type=order_type,
            quantity=amount
        )
        print(f"take long : {now}. price = {price}. capital : {usdt_balance}")                 
        time.sleep(10)

    #short/sell
    elif sell == True:
        client.futures_cancel_all_open_orders(symbol=symbol)
        # Place un ordre de vente
        short_order = client.futures_create_order(
            symbol=symbol,
            side=SIDE_SELL,
            type=order_type,
            quantity=amount
        )
        print(f"take short : {now}. price = {price}. capital : {usdt_balance}")
        time.sleep(10)
            
    if last_fast_ma < last_slow_ma and open_positions == True:
        for position in positions:
            if float(position['positionAmt']) > 0:
                long_order_sell = client.futures_create_order(
                    symbol=symbol,
                    side=SIDE_SELL,
                    type=order_type,
                    quantity=abs(float(position['positionAmt']))
                )  

    elif last_fast_ma > last_slow_ma and open_positions == True:
        for position in positions:
            if float(position['positionAmt']) < 0:
                short_order_buy = client.futures_create_order(
                    symbol=symbol,
                    side=SIDE_BUY,
                    type=order_type,
                    quantity=abs(float(position['positionAmt']))
                )     
        
    first_scan = False
    #cycle toute les 30 minutes
    time.sleep(1800)
   
