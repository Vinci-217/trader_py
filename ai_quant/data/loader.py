import akshare as ak
import pandas as pd
import os


MAGIFICENT_7 = {
    'AAPL': '105.AAPL',
    'MSFT': '105.MSFT',
    'AMZN': '105.AMZN',
    'GOOGL': '105.GOOGL',
    'NVDA': '105.NVDA',
    'META': '105.META',
    'TSLA': '105.TSLA'
}

STOCK_NAMES = {
    'AAPL': 'Apple',
    'MSFT': 'Microsoft',
    'AMZN': 'Amazon',
    'GOOGL': 'Alphabet',
    'NVDA': 'Nvidia',
    'META': 'Meta',
    'TSLA': 'Tesla'
}


def get_us_stock(stock_code, start_date, end_date):
    try:
        data = ak.stock_us_hist(
            symbol=stock_code,
            period="daily",
            start_date=start_date,
            end_date=end_date,
            adjust="qfq"
        )
        return data
    except Exception as e:
        print(f"Error fetching {stock_code}: {e}")
        return None


def prepare_data(df):
    if df is None or df.empty:
        return None
    
    df = df.copy()
    df.rename(columns={
        '日期': 'datetime',
        '开盘': 'open',
        '最高': 'high',
        '最低': 'low',
        '收盘': 'close',
        '成交量': 'volume'
    }, inplace=True)
    
    df['datetime'] = pd.to_datetime(df['datetime'])
    df.set_index('datetime', inplace=True)
    
    for col in ['open', 'high', 'low', 'close', 'volume']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    df = df.dropna()
    return df


def load_stock_data(symbol, start_date, end_date, use_cache=False, cache_dir='data_cache'):
    os.makedirs(cache_dir, exist_ok=True)
    cache_file = os.path.join(cache_dir, f"{symbol}_{start_date}_{end_date}.csv")
    
    if use_cache and os.path.exists(cache_file):
        df = pd.read_csv(cache_file, index_col='datetime', parse_dates=True)
        return df
    
    stock_code = MAGIFICENT_7.get(symbol, f"105.{symbol}")
    df = get_us_stock(stock_code, start_date, end_date)
    
    if df is not None and not df.empty:
        df = prepare_data(df)
        if use_cache and df is not None and not df.empty:
            df.to_csv(cache_file)
    
    return df


def load_all_stocks(start_date, end_date, symbols=None):
    if symbols is None:
        symbols = list(MAGIFICENT_7.keys())
    
    all_data = {}
    for symbol in symbols:
        print(f"Loading {symbol}...")
        df = load_stock_data(symbol, start_date, end_date)
        if df is not None and not df.empty:
            all_data[symbol] = df
            print(f"  Loaded {len(df)} rows for {symbol}")
        else:
            print(f"  Failed to load {symbol}")
    return all_data


def get_buy_and_hold_return(df):
    if df is None or len(df) < 2:
        return 0.0
    start_price = df['close'].iloc[0]
    end_price = df['close'].iloc[-1]
    return (end_price - start_price) / start_price
