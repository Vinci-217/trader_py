import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import warnings
warnings.filterwarnings('ignore')


ML_MODELS = {}
SCALERS = {}
FEATURE_IMPORTANCE = {}


def prepare_features(df):
    features = pd.DataFrame(index=df.index)
    
    close = df['close']
    high = df['high']
    low = df['low']
    volume = df['volume']
    
    features['return_1d'] = close.pct_change(1)
    features['return_5d'] = close.pct_change(5)
    features['return_10d'] = close.pct_change(10)
    features['return_20d'] = close.pct_change(20)
    
    features['volatility_5d'] = close.pct_change().rolling(5).std()
    features['volatility_10d'] = close.pct_change().rolling(10).std()
    features['volatility_20d'] = close.pct_change().rolling(20).std()
    
    features['sma_5'] = close.rolling(5).mean() / close - 1
    features['sma_10'] = close.rolling(10).mean() / close - 1
    features['sma_20'] = close.rolling(20).mean() / close - 1
    features['sma_50'] = close.rolling(50).mean() / close - 1
    
    features['high_low_ratio'] = (high - low) / close
    
    features['volume_ratio'] = volume / volume.rolling(20).mean()
    
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    features['rsi'] = 100 - (100 / (1 + rs))
    
    features['momentum_5'] = close / close.shift(5) - 1
    features['momentum_10'] = close / close.shift(10) - 1
    features['momentum_20'] = close / close.shift(20) - 1
    
    features['highest_20'] = high.rolling(20).max() / close - 1
    features['lowest_20'] = low.rolling(20).min() / close - 1
    
    return features


def prepare_labels(df, forward_days=5, threshold=0.02):
    close = df['close']
    future_return = close.shift(-forward_days) / close - 1
    
    labels = pd.Series(0, index=df.index)
    labels[future_return > threshold] = 1
    labels[future_return < -threshold] = -1
    
    return labels


def train_model(symbol, df):
    features = prepare_features(df)
    labels = prepare_labels(df)
    
    features = features.dropna()
    labels = labels.loc[features.index]
    
    if len(features) < 100:
        return None
    
    X = features.values
    y = labels.values
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        min_samples_split=5,
        random_state=42,
        n_jobs=-1
    )
    
    model.fit(X_scaled, y)
    
    ML_MODELS[symbol] = model
    SCALERS[symbol] = scaler
    FEATURE_IMPORTANCE[symbol] = dict(zip(features.columns, model.feature_importances_))
    
    return model


def predict(symbol, df):
    if symbol not in ML_MODELS:
        train_model(symbol, df)
    
    if symbol not in ML_MODELS:
        return 0, 0.5
    
    features = prepare_features(df)
    last_features = features.iloc[-1:].values
    
    if np.any(np.isnan(last_features)):
        return 0, 0.5
    
    scaler = SCALERS[symbol]
    model = ML_MODELS[symbol]
    
    last_features_scaled = scaler.transform(last_features)
    
    prediction = model.predict(last_features_scaled)[0]
    proba = model.predict_proba(last_features_scaled)[0]
    
    confidence = max(proba)
    
    return prediction, confidence


def get_ml_score(symbol, df):
    prediction, confidence = predict(symbol, df)
    
    score = prediction * confidence * 10
    
    return score


def train_all_models(symbols, data_loader):
    print("训练机器学习模型...")
    for symbol in symbols:
        df = data_loader(symbol)
        if df is not None:
            train_model(symbol, df)
            print(f"  {symbol} 模型训练完成")


if __name__ == "__main__":
    from ai_quant.data.loader import load_stock_data
    
    symbols = ['AAPL', 'MSFT', 'NVDA', 'META', 'GOOGL', 'AMZN', 'TSLA']
    
    print("训练机器学习模型...")
    for symbol in symbols:
        df = load_stock_data(symbol, '20200101', '20241231', use_cache=True)
        if df is not None:
            model = train_model(symbol, df)
            if model:
                print(f"\n{symbol} 模型训练完成")
                
                prediction, confidence = predict(symbol, df)
                print(f"  预测: {prediction}")
                print(f"  置信度: {confidence:.2f}")
                
                importance = FEATURE_IMPORTANCE.get(symbol, {})
                top_features = sorted(importance.items(), key=lambda x: x[1], reverse=True)[:5]
                print(f"  重要特征: {top_features}")
