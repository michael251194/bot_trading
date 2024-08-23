import ccxt
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from keras.models import Sequential
from keras.layers import LSTM, Dense, Dropout
import ta  # Pour les indicateurs techniques

# 1. Collecte des données
def fetch_data(symbol, timeframe):
    exchange = ccxt.bybit()
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    return df

# 2. Prétraitement et ingénierie des features
def preprocess_data(df):
    # Calculer les indicateurs techniques
    df['RSI'] = ta.momentum.rsi(df['close'], window=14)
    df['MACD'] = ta.trend.macd_diff(df['close'])
    df['Bollinger_Upper'], df['Bollinger_Lower'] = ta.volatility.bollinger_hband(df['close']), ta.volatility.bollinger_lband(df['close'])
    df['ATR'] = ta.volatility.average_true_range(df['high'], df['low'], df['close'])

    # Supprimer les lignes contenant des NaN
    df.dropna(inplace=True)

    # Assurez-vous que toutes les colonnes numériques sont de type float
    numeric_columns = df.select_dtypes(include=[np.number]).columns
    df[numeric_columns] = df[numeric_columns].astype(float)

    # Vérifier qu'il ne reste plus de valeurs NaN ou infinies
    if df.isnull().values.any():
        raise ValueError("Le DataFrame contient toujours des NaN après suppression")
    if np.isinf(df[numeric_columns].values).any():
        raise ValueError("Le DataFrame contient des valeurs infinies après suppression des NaN")

    # Normaliser les données
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_data = scaler.fit_transform(df[['close', 'RSI', 'MACD', 'Bollinger_Upper', 'Bollinger_Lower', 'ATR']])
    
    return scaled_data, scaler

# 3. Modélisation avec LSTM
def build_lstm_model(input_shape):
    model = Sequential()
    model.add(LSTM(units=50, return_sequences=True, input_shape=(input_shape[1], input_shape[2])))
    model.add(Dropout(0.2))
    model.add(LSTM(units=50, return_sequences=False))
    model.add(Dropout(0.2))
    model.add(Dense(units=1))  # Prédire le prix de clôture suivant
    model.compile(optimizer='adam', loss='mean_squared_error')
    return model

# 4. Préparation des données pour le modèle LSTM
def prepare_data_for_lstm(scaled_data, time_step=60):
    X, y = [], []
    for i in range(time_step, len(scaled_data)):
        X.append(scaled_data[i-time_step:i, :])
        y.append(scaled_data[i, 0])  # 0 correspond à la colonne 'close'
    X, y = np.array(X), np.array(y)
    return X, y

# 5. Calcul du Stop-Loss et du Take-Profit
def calculate_stop_loss_take_profit(entry_price, atr, decision, stop_loss_multiplier=1.5, take_profit_multiplier=2.0):
    if decision == "Acheter":
        stop_loss = entry_price - (atr * stop_loss_multiplier)
        take_profit = entry_price + (atr * take_profit_multiplier)
    elif decision == "Vendre":
        stop_loss = entry_price + (atr * stop_loss_multiplier)
        take_profit = entry_price - (atr * take_profit_multiplier)
    return stop_loss, take_profit

# 6. Exécution en temps réel avec calcul du prix d'entrée, stop-loss, take-profit
def run_real_time_trading(symbol, timeframe, model, scaler, time_step=60):
    df = fetch_data(symbol, timeframe)
    scaled_data, _ = preprocess_data(df)
    X_real_time = scaled_data[-time_step:]
    X_real_time = np.reshape(X_real_time, (1, X_real_time.shape[0], X_real_time.shape[1]))
    
    # Prédiction du prochain prix de clôture
    prediction = model.predict(X_real_time)
    predicted_price = scaler.inverse_transform(np.concatenate((prediction, np.zeros((1, 5))), axis=1))[:, 0][0]
    
    current_price = df['close'].iloc[-1]
    atr = df['ATR'].iloc[-1]
    
    # Déterminer le prix d'entrée et la décision d'achat/vente
    print(f"{predicted_price}")
    if predicted_price > current_price:
        entry_price = current_price
        decision = "Acheter"
    else:
        entry_price = current_price
        decision = "Vendre"

    # Calculer les niveaux de stop-loss et take-profit en fonction de la décision
    stop_loss, take_profit = calculate_stop_loss_take_profit(entry_price, atr, decision)
    
    return {
        "Décision": decision,
        "Prix entrée": entry_price,
        "Stop-Loss": stop_loss,
        "Take-Profit": take_profit
    }

# 7. Entraînement et exécution
if __name__ == "__main__":
    symbol = 'GMTUSDT'
    timeframe = '15m'
    
    df = fetch_data(symbol, timeframe)
    scaled_data, scaler = preprocess_data(df)
    
    X, y = prepare_data_for_lstm(scaled_data)
    model = build_lstm_model(X.shape)
    
    model.fit(X, y, epochs=50, batch_size=32)
    
    # Exécution en temps réel
    trading_decision = run_real_time_trading(symbol, timeframe, model, scaler)
    print(f"Décision de trading pour {symbol} : {trading_decision['Décision']}")
    print(f"Prix d'entrée : {trading_decision['Prix entrée']:.5f}")
    print(f"Stop-Loss : {trading_decision['Stop-Loss']:.5f}")
    print(f"Take-Profit : {trading_decision['Take-Profit']:.5f}")
