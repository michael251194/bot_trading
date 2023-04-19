import time
import datetime
from binance.client import Client
from binance.enums import *
import requests

api_key='yV3pMGLeDyflG55jkNPr3tscCG5FBfcWyMXcEHZ2Ub852MAtkdELtDIPfmPLlEf4'
api_secret = 'zpUuQVsyyF0fytC1lDDQgy1BGk6Pv1iAWouAHl7zoTzczajQfqcRd20IG8UfO00W'

#current_price = float(input("quel est le prix actuel du token ou quel prix de base veux-tu définir ? "))
symbol = 'GMTUSDT'
save_price = 0.3810  #forcer avec la valeur actuelle ou une autre valeur 
pourcentage_trade_balance = 0.5 #pourcentage du capital à trader par position
start_leverage = 5 #levier 
start_increase = 0.0125 #prend un long si la valeur augmente de x%
start_decrease = 0.0125 #prend un short si la valeur baisse de x%
SP_long = 0.0150 #pourcentage stop loss pour les longs
TP_long = 0.0150 #pourcentage take profit pour les longs
SP_short = 0.0150 #pourcentage stop loss pour les shorts
TP_short = 0.0150 #pourcentage take profit pour les shorts
minus_TP = 0.0048 #diminue les TP si des positions identiques shortl/ong se suuccédent
decimal_TP_SP_price = 4
timer_update_price = 12*60*60 #en secondes, délai avant de mettre à jour le save_price

price_position = 0
amount_position = 0
counter_long = 0
counter_short = 0
position_opened = False
price = 0.0
timer = 0
open_positions = False
first_scan = True
order_type = FUTURE_ORDER_TYPE_MARKET
# levier
leverage = start_leverage

#modifier le time out de connexion
url = "https://fapi.binance.com/fapi/v1/ping"
timeout = 60  # temps limite de 30 secondes
response = requests.get(url, timeout=timeout)

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
            if position_opened == False:
                position_opened = True

    #logic to follow if a position is currently open
    if open_positions == False: 
        timer += 1
        price_position = 0
        amount_position = 0
        change_SP_long_1 = False
        change_SP_long_2 = False
        change_SP_long_3 = False
        change_SP_short_1 = False
        change_SP_short_2 = False
        change_SP_short_3 = False
        if position_opened == True: 
            client.futures_cancel_all_open_orders(symbol=symbol) #ferme toute les ordres si aucune positions ouvertes
            time.sleep(1)
            position_opened = False

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


    #change TP/SP en fonction de l'évolution du prix 
    if counter_long != 0 and open_positions == True:
        if price/price_position -1 > 0.0075 and change_SP_long_1 == False:
            stop_loss_long = round((1-0.0050) * price_position, decimal_TP_SP_price)
            change_SP_long_1 = True
            long_order_SP = client.futures_create_order(
                symbol=symbol,
                side=SIDE_SELL,
                type=FUTURE_ORDER_TYPE_STOP_MARKET,
                timeInForce=TIME_IN_FORCE_GTC,
                quantity=amount_position,
                stopPrice=stop_loss_long,
                closePosition=True
            )
        elif price/price_position -1 > 0.01 and change_SP_long_2 == False:
            stop_loss_long = round((1-0.0010) * price_position, decimal_TP_SP_price)
            change_SP_long_2 = True
            long_order_SP = client.futures_create_order(
                symbol=symbol,
                side=SIDE_SELL,
                type=FUTURE_ORDER_TYPE_STOP_MARKET,
                timeInForce=TIME_IN_FORCE_GTC,
                quantity=amount_position,
                stopPrice=stop_loss_long,
                closePosition=True
            )
        elif price/price_position -1 > 0.012 and change_SP_long_3 == False:
            stop_loss_long = round((1+0.0015) * price_position, decimal_TP_SP_price)
            change_SP_long_3 = True
            long_order_SP = client.futures_create_order(
                symbol=symbol,
                side=SIDE_SELL,
                type=FUTURE_ORDER_TYPE_STOP_MARKET,
                timeInForce=TIME_IN_FORCE_GTC,
                quantity=amount_position,
                stopPrice=stop_loss_long,
                closePosition=True
            )
    else:
        stop_loss_long = round((1-SP_long) * price, decimal_TP_SP_price)
        
    if counter_long == 1: 
        take_profit_long = round((1 + TP_long - minus_TP) * price, decimal_TP_SP_price)
    elif counter_long >= 2: 
        take_profit_long = round((1 + TP_long - minus_TP - minus_TP) * price, decimal_TP_SP_price)
    else:
        take_profit_long = round((1+TP_long) * price, decimal_TP_SP_price)
    #change TP/SP en fonction de l'évolution du prix          
    if counter_short != 0 and open_positions == True: 
        if -(price/price_position -1) > 0.0075 and change_SP_short_1 == False:
            stop_loss_short = round((1+0.0050) * price_position, decimal_TP_SP_price)
            change_SP_short_1 = True
            short_order_SP = client.futures_create_order(
                symbol=symbol,
                side=SIDE_BUY,
                type=FUTURE_ORDER_TYPE_STOP_MARKET,
                timeInForce=TIME_IN_FORCE_GTC,
                quantity=amount_position,
                stopPrice=stop_loss_short,
                closePosition=True
            )
        elif -(price/price_position -1) > 0.0100 and change_SP_short_2 == False:
            stop_loss_short = round((1+0.0010) * price_position, decimal_TP_SP_price)
            change_SP_short_2 = True
            short_order_SP = client.futures_create_order(
                symbol=symbol,
                side=SIDE_BUY,
                type=FUTURE_ORDER_TYPE_STOP_MARKET,
                timeInForce=TIME_IN_FORCE_GTC,
                quantity=amount_position,
                stopPrice=stop_loss_short,
                closePosition=True
            )
        elif -(price/price_position -1) > 0.0120 and change_SP_short_3 == False:
            stop_loss_short = round((1-0.0015) * price_position, decimal_TP_SP_price)
            change_SP_short_3 = True
            short_order_SP = client.futures_create_order(
                symbol=symbol,
                side=SIDE_BUY,
                type=FUTURE_ORDER_TYPE_STOP_MARKET,
                timeInForce=TIME_IN_FORCE_GTC,
                quantity=amount_position,
                stopPrice=stop_loss_short,
                closePosition=True
            )
    else:
        stop_loss_short = round((1+SP_short) * price, decimal_TP_SP_price)

    if counter_short == 1: 
        take_profit_short = round((1-TP_short + minus_TP) * price, decimal_TP_SP_price)
    elif counter_short >= 2: 
        take_profit_short = round((1-TP_short + minus_TP + minus_TP) * price, decimal_TP_SP_price)
    else: 
        take_profit_short = round((1-TP_short) * price, decimal_TP_SP_price)


    if timer >= timer_update_price or open_positions == True or first_scan == True: 
        save_price = price
        timer = 0
        
    increase = price / save_price - 1
    decrease = -(price / save_price - 1)

    #Long/buy
    if increase >= start_increase and open_positions == False: 
        save_price = price
        price_position = price
        amount_position = amount
        counter_long += 1
        counter_short = 0
        #client.futures_cancel_all_open_orders(symbol=symbol)
        
        # création de l'ordre d'achat
        long_order = client.futures_create_order(
            symbol=symbol,
            side=SIDE_BUY,
            type=order_type,
            quantity=amount
        )
        long_order_tp = client.futures_create_order(
            symbol=symbol,
            side=SIDE_SELL,
            type=FUTURE_ORDER_TYPE_TAKE_PROFIT_MARKET,
            timeInForce=TIME_IN_FORCE_GTC,
            quantity=amount,
            stopPrice=take_profit_long,
            closePosition=True
        )
        #creation de l'ordre stop loss
        long_order_SP = client.futures_create_order(
            symbol=symbol,
            side=SIDE_SELL,
            type=FUTURE_ORDER_TYPE_STOP_MARKET,
            timeInForce=TIME_IN_FORCE_GTC,
            quantity=amount,
            stopPrice=stop_loss_long,
            closePosition=True
        )
        print(f"take long : {now}. price = {price}. capital : {usdt_balance}")
        time.sleep(0.5)

    #short/sell
    elif decrease >= start_decrease and open_positions == False:
        save_price = price
        price_position = price
        amount_position = amount
        counter_short += 1
        counter_long = 0
        #client.futures_cancel_all_open_orders(symbol=symbol)
        
        # Place un ordre de vente
        short_order = client.futures_create_order(
            symbol=symbol,
            side=SIDE_SELL,
            type=order_type,
            quantity=amount
        )
        #creation de l'ordre take profit 
        short_order_tp = client.futures_create_order(
            symbol=symbol,
            side=SIDE_BUY,
            type=FUTURE_ORDER_TYPE_TAKE_PROFIT_MARKET,
            timeInForce=TIME_IN_FORCE_GTC,
            quantity=amount,
            stopPrice=take_profit_short,
            closePosition=True
        )
        #creation de l'ordre stop loss
        short_order_SP = client.futures_create_order(
            symbol=symbol,
            side=SIDE_BUY,
            type=FUTURE_ORDER_TYPE_STOP_MARKET,
            timeInForce=TIME_IN_FORCE_GTC,
            quantity=amount,
            stopPrice=stop_loss_short,
            closePosition=True
        )
        print(f"take short : {now}. price = {price}. capital : {usdt_balance}")
        time.sleep(0.5)
    first_scan = False
    time.sleep(1)
   