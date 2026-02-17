import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import warnings
warnings.filterwarnings('ignore')


def create_ml_features(df, target_horizon=5):
    features = pd.DataFrame(index=df.index)
    
    close = df['close']
    volume = df['volume']
    high = df['high']
    low = df['low']
    
    for period in [5, 10, 20]:
        features[f'return_{period}d'] = close.pct_change(period)
    
    for period in [5, 10, 20, 50]:
        features[f'ma{period}'] = close.rolling(period).mean()
        features[f'close_ma{period}_ratio'] = close / features[f'ma{period}']
    
    delta = close.diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    features['rsi_14'] = 100 - (100 / (1 + rs))
    
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    features['macd'] = ema12 - ema26
    features['macd_signal'] = features['macd'].ewm(span=9, adjust=False).mean()
    
    k = 100 * (close - low.rolling(14).min()) / (high.rolling(14).max() - low.rolling(14).min())
    features['kdj_k'] = k
    
    bb_mid = close.rolling(20).mean()
    bb_std = close.rolling(20).std()
    features['bb_position'] = (close - (bb_mid - 2 * bb_std)) / (4 * bb_std + 0.0001)
    
    features['atr'] = (high - low).rolling(14).mean()
    
    for i in range(1, 6):
        features[f'return_lag_{i}'] = features[f'return_5d'].shift(i)
    
    features['target'] = (close.shift(-target_horizon) / close - 1) > 0.01
    
    features = features.fillna(0)
    features = features.replace([np.inf, -np.inf], 0)
    
    return features


def train_model(df, model_type='random_forest'):
    ml_data = create_ml_features(df)
    
    feature_cols = [col for col in ml_data.columns if col not in ['target']]
    X = ml_data[feature_cols]
    y = ml_data['target']
    
    valid_idx = ~(X.isna().any(axis=1) | y.isna())
    X = X[valid_idx]
    y = y[valid_idx]
    
    if len(X) < 100:
        return None, None
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    if model_type == 'random_forest':
        model = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
    else:
        model = GradientBoostingClassifier(n_estimators=100, max_depth=5, random_state=42)
    
    model.fit(X_scaled, y)
    
    return model, scaler


def predict_next_day(df, model, scaler):
    ml_data = create_ml_features(df)
    
    feature_cols = [col for col in ml_data.columns if col not in ['target']]
    X = ml_data[feature_cols]
    
    X_last = X.iloc[-1:].fillna(0).replace([np.inf, -np.inf], 0)
    X_scaled = scaler.transform(X_last)
    
    prob = model.predict_proba(X_scaled)[0]
    
    return prob[1] if len(prob) > 1 else 0.5


def calculate_prediction_score(df, model, scaler):
    prob = predict_next_day(df, model, scaler)
    score = (prob - 0.5) * 10
    return score


class MLStockPredictor:
    def __init__(self):
        self.models = {}
        self.scalers = {}
    
    def train(self, symbol, df, model_type='random_forest'):
        model, scaler = train_model(df, model_type)
        if model and scaler:
            self.models[symbol] = model
            self.scalers[symbol] = scaler
            return True
        return False
    
    def predict(self, symbol, df):
        if symbol not in self.models:
            return 0
        return calculate_prediction_score(df, self.models[symbol], self.scalers[symbol])
    
    def rank_stocks(self, stock_data):
        scores = {}
        for symbol, df in stock_data.items():
            score = self.predict(symbol, df)
            scores[symbol] = score
        
        sorted_stocks = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_stocks


def train_all_models(stock_data, model_type='random_forest'):
    predictor = MLStockPredictor()
    
    for symbol, df in stock_data.items():
        print(f"Training model for {symbol}...")
        predictor.train(symbol, df, model_type)
    
    return predictor
