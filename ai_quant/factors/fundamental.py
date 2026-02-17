import pandas as pd
import numpy as np
import yfinance as yf


FUNDAMENTAL_TICKERS = {
    'AAPL': 'AAPL',
    'MSFT': 'MSFT',
    'AMZN': 'AMZN',
    'GOOGL': 'GOOGL',
    'NVDA': 'NVDA',
    'META': 'META',
    'TSLA': 'TSLA'
}


def get_fundamental_data(symbol, period='1y'):
    try:
        ticker = yf.Ticker(FUNDAMENTAL_TICKERS.get(symbol, symbol))
        
        info = ticker.info
        
        fundamentals = {
            'symbol': symbol,
            'pe_ratio': info.get('trailingPE', 0),
            'forward_pe': info.get('forwardPE', 0),
            'peg_ratio': info.get('pegRatio', 0),
            'pb_ratio': info.get('priceToBook', 0),
            'ps_ratio': info.get('priceToSalesTrailing12Months', 0),
            'ev_ebitda': info.get('enterpriseToRevenue', 0),
            'profit_margin': info.get('profitMargins', 0),
            'operating_margin': info.get('operatingMargins', 0),
            'roe': info.get('returnOnEquity', 0),
            'roa': info.get('returnOnAssets', 0),
            'debt_to_equity': info.get('debtToEquity', 0),
            'current_ratio': info.get('currentRatio', 0),
            'quick_ratio': info.get('quickRatio', 0),
            'revenue_growth': info.get('revenueGrowth', 0),
            'earnings_growth': info.get('earningsGrowth', 0),
            'revenue': info.get('revenue', 0),
            'market_cap': info.get('marketCap', 0),
            'dividend_yield': info.get('dividendYield', 0),
            'beta': info.get('beta', 0),
            'fifty_two_week_high': info.get('fiftyTwoWeekHigh', 0),
            'fifty_two_week_low': info.get('fiftyTwoWeekLow', 0),
        }
        
        return fundamentals
    except Exception as e:
        print(f"Error fetching fundamental data for {symbol}: {e}")
        return None


def get_all_fundamentals(symbols=None):
    if symbols is None:
        symbols = list(FUNDAMENTAL_TICKERS.keys())
    
    all_fundamentals = {}
    for symbol in symbols:
        print(f"Fetching fundamentals for {symbol}...")
        data = get_fundamental_data(symbol)
        if data:
            all_fundamentals[symbol] = data
    
    return all_fundamentals


def calculate_fundamental_score(fundamentals):
    if not fundamentals:
        return 0
    
    score = 0
    
    if fundamentals.get('pe_ratio', 0) > 0:
        if fundamentals['pe_ratio'] < 15:
            score += 3
        elif fundamentals['pe_ratio'] < 25:
            score += 1
        elif fundamentals['pe_ratio'] > 50:
            score -= 2
    
    if fundamentals.get('peg_ratio', 0) > 0:
        if fundamentals['peg_ratio'] < 1:
            score += 3
        elif fundamentals['peg_ratio'] < 2:
            score += 1
        elif fundamentals['peg_ratio'] > 3:
            score -= 2
    
    if fundamentals.get('roe', 0) > 0.2:
        score += 3
    elif fundamentals.get('roe', 0) > 0.1:
        score += 1
    elif fundamentals.get('roe', 0) < 0:
        score -= 2
    
    if fundamentals.get('revenue_growth', 0) > 0.2:
        score += 3
    elif fundamentals.get('revenue_growth', 0) > 0.1:
        score += 1
    elif fundamentals.get('revenue_growth', 0) < 0:
        score -= 2
    
    if fundamentals.get('profit_margin', 0) > 0.2:
        score += 2
    elif fundamentals.get('profit_margin', 0) > 0.1:
        score += 1
    elif fundamentals.get('profit_margin', 0) < 0:
        score -= 1
    
    if fundamentals.get('debt_to_equity', 0) < 50:
        score += 2
    elif fundamentals.get('debt_to_equity', 0) > 150:
        score -= 2
    
    if fundamentals.get('dividend_yield', 0) > 0.02:
        score += 1
    
    return score


def rank_stocks_by_fundamentals(symbols=None):
    fundamentals = get_all_fundamentals(symbols)
    
    scores = {}
    for symbol, data in fundamentals.items():
        scores[symbol] = calculate_fundamental_score(data)
    
    sorted_stocks = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    
    return sorted_stocks, fundamentals


if __name__ == "__main__":
    ranks, data = rank_stocks_by_fundamentals()
    print("\nFundamental Rankings:")
    for symbol, score in ranks:
        print(f"  {symbol}: {score}")
