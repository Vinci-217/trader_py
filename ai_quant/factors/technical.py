import pandas as pd
import numpy as np


def calculate_technical_features(df):
    features = pd.DataFrame(index=df.index)
    features['close'] = df['close']
    features['open'] = df['open']
    features['high'] = df['high']
    features['low'] = df['low']
    features['volume'] = df['volume']
    
    close = df['close']
    high = df['high']
    low = df['low']
    volume = df['volume']
    
    features['return_1d'] = close.pct_change(1)
    features['return_5d'] = close.pct_change(5)
    features['return_10d'] = close.pct_change(10)
    features['return_20d'] = close.pct_change(20)
    
    for period in [5, 10, 20, 30, 50]:
        features[f'ma{period}'] = close.rolling(period).mean()
        features[f'ema{period}'] = close.ewm(span=period, adjust=False).mean()
        features[f'close_ma{period}_ratio'] = close / features[f'ma{period}']
        features[f'volume_ma{period}'] = volume / volume.rolling(period).mean()
    
    for period in [5, 10, 20]:
        features[f'volatility_{period}d'] = close.pct_change().rolling(period).std()
    
    delta = close.diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    features['rsi_14'] = 100 - (100 / (1 + rs))
    
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    features['macd'] = ema12 - ema26
    features['macd_signal'] = features['macd'].ewm(span=9, adjust=False).mean()
    features['macd_hist'] = features['macd'] - features['macd_signal']
    
    k = 100 * (close - low.rolling(14).min()) / (high.rolling(14).max() - low.rolling(14).min())
    features['kdj_k'] = k
    features['kdj_d'] = k.rolling(3).mean()
    features['kdj_j'] = 3 * k - 2 * features['kdj_d']
    
    bb_mid = close.rolling(20).mean()
    bb_std = close.rolling(20).std()
    features['bb_upper'] = bb_mid + 2 * bb_std
    features['bb_lower'] = bb_mid - 2 * bb_std
    features['bb_width'] = (features['bb_upper'] - features['bb_lower']) / bb_mid
    features['bb_position'] = (close - features['bb_lower']) / (features['bb_upper'] - features['bb_lower'])
    
    features['atr'] = (high - low).rolling(14).mean()
    features['atr_ratio'] = features['atr'] / close
    
    features['obv'] = (np.sign(close.diff()) * volume).cumsum()
    features['obv_ma5'] = features['obv'] / features['obv'].rolling(5).mean()
    
    features['high_low_ratio'] = (high - low) / close
    features['close_open_ratio'] = (close - df['open']) / df['open']
    
    features['price_momentum'] = (close - close.shift(10)) / close.shift(10)
    features['volume_momentum'] = (volume - volume.shift(10)) / volume.shift(10).replace(0, 1)
    
    for i in range(1, 6):
        features[f'close_lag_{i}'] = close.shift(i)
        features[f'return_lag_{i}'] = features['return_1d'].shift(i)
    
    features = features.fillna(0)
    features = features.replace([np.inf, -np.inf], 0)
    
    return features


def detect_candlestick_patterns(df):
    patterns = pd.DataFrame(index=df.index)
    
    close = df['close']
    open_price = df['open']
    high = df['high']
    low = df['low']
    
    body = close - open_price
    upper_shadow = high - np.maximum(close, open_price)
    lower_shadow = np.minimum(close, open_price) - low
    body_size = abs(body)
    
    patterns['doji'] = (body_size / (high - low + 0.0001)) < 0.1
    
    patterns['hammer'] = (
        (lower_shadow > 2 * body_size) & 
        (upper_shadow < body_size * 0.5) &
        (body > 0)
    )
    
    patterns['shooting_star'] = (
        (upper_shadow > 2 * body_size) & 
        (lower_shadow < body_size * 0.5) &
        (body < 0)
    )
    
    patterns['engulfing_bullish'] = (
        (body.shift(1) < 0) & 
        (body > 0) &
        (close > open_price.shift(1)) &
        (open_price < close.shift(1))
    )
    
    patterns['engulfing_bearish'] = (
        (body.shift(1) > 0) & 
        (body < 0) &
        (close < open_price.shift(1)) &
        (open_price > close.shift(1))
    )
    
    patterns['morning_star'] = (
        (body.shift(2) < 0) &
        (abs(body.shift(1)) / (high.shift(2) - low.shift(2) + 0.0001) < 0.1) &
        (body > 0) &
        (close > (open_price.shift(2) + close.shift(2)) / 2)
    )
    
    patterns['evening_star'] = (
        (body.shift(2) > 0) &
        (abs(body.shift(1)) / (high.shift(2) - low.shift(2) + 0.0001) < 0.1) &
        (body < 0) &
        (close < (open_price.shift(2) + close.shift(2)) / 2)
    )
    
    patterns['three_white_soldiers'] = (
        (body > 0) & 
        (body.shift(1) > 0) &
        (body.shift(2) > 0) &
        (close > close.shift(1)) &
        (close.shift(1) > close.shift(2))
    )
    
    patterns['three_black_crows'] = (
        (body < 0) & 
        (body.shift(1) < 0) &
        (body.shift(2) < 0) &
        (close < close.shift(1)) &
        (close.shift(1) < close.shift(2))
    )
    
    patterns = patterns.fillna(0).astype(int)
    return patterns


def calculate_all_features(df):
    features = calculate_technical_features(df)
    patterns = detect_candlestick_patterns(df)
    features = features.join(patterns)
    return features
