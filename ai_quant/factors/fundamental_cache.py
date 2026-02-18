FUNDAMENTAL_DATA_CACHE = {
    'AAPL': {
        'pe_ratio': 28.5,
        'forward_pe': 26.2,
        'peg_ratio': 2.1,
        'pb_ratio': 45.3,
        'ps_ratio': 7.2,
        'profit_margin': 0.253,
        'operating_margin': 0.298,
        'roe': 1.47,
        'roa': 0.283,
        'debt_to_equity': 1.87,
        'current_ratio': 0.99,
        'revenue_growth': 0.079,
        'earnings_growth': 0.11,
        'dividend_yield': 0.0052,
        'beta': 1.28,
    },
    'MSFT': {
        'pe_ratio': 32.1,
        'forward_pe': 28.5,
        'peg_ratio': 1.8,
        'pb_ratio': 12.1,
        'ps_ratio': 11.8,
        'profit_margin': 0.364,
        'operating_margin': 0.444,
        'roe': 0.372,
        'roa': 0.189,
        'debt_to_equity': 37.74,
        'current_ratio': 1.24,
        'revenue_growth': 0.156,
        'earnings_growth': 0.22,
        'dividend_yield': 0.0074,
        'beta': 0.89,
    },
    'AMZN': {
        'pe_ratio': 42.5,
        'forward_pe': 35.2,
        'peg_ratio': 1.5,
        'pb_ratio': 8.2,
        'ps_ratio': 3.1,
        'profit_margin': 0.068,
        'operating_margin': 0.094,
        'roe': 0.182,
        'roa': 0.078,
        'debt_to_equity': 58.95,
        'current_ratio': 1.07,
        'revenue_growth': 0.122,
        'earnings_growth': 0.85,
        'dividend_yield': 0,
        'beta': 1.16,
    },
    'GOOGL': {
        'pe_ratio': 24.8,
        'forward_pe': 19.5,
        'peg_ratio': 1.2,
        'pb_ratio': 6.1,
        'ps_ratio': 5.8,
        'profit_margin': 0.256,
        'operating_margin': 0.305,
        'roe': 0.279,
        'roa': 0.187,
        'debt_to_equity': 11.52,
        'current_ratio': 1.84,
        'revenue_growth': 0.155,
        'earnings_growth': 0.37,
        'dividend_yield': 0,
        'beta': 1.05,
    },
    'NVDA': {
        'pe_ratio': 65.2,
        'forward_pe': 45.8,
        'peg_ratio': 1.3,
        'pb_ratio': 52.8,
        'ps_ratio': 35.2,
        'profit_margin': 0.551,
        'operating_margin': 0.623,
        'roe': 1.23,
        'roa': 0.422,
        'debt_to_equity': 42.85,
        'current_ratio': 4.27,
        'revenue_growth': 1.22,
        'earnings_growth': 2.85,
        'dividend_yield': 0.0003,
        'beta': 1.67,
    },
    'META': {
        'pe_ratio': 28.5,
        'forward_pe': 22.1,
        'peg_ratio': 0.9,
        'pb_ratio': 8.5,
        'ps_ratio': 7.8,
        'profit_margin': 0.345,
        'operating_margin': 0.412,
        'roe': 0.348,
        'roa': 0.228,
        'debt_to_equity': 12.45,
        'current_ratio': 2.67,
        'revenue_growth': 0.227,
        'earnings_growth': 0.73,
        'dividend_yield': 0,
        'beta': 1.22,
    },
    'TSLA': {
        'pe_ratio': 58.5,
        'forward_pe': 85.2,
        'peg_ratio': 3.2,
        'pb_ratio': 11.8,
        'ps_ratio': 8.5,
        'profit_margin': 0.073,
        'operating_margin': 0.082,
        'roe': 0.105,
        'roa': 0.065,
        'debt_to_equity': 19.72,
        'current_ratio': 1.72,
        'revenue_growth': 0.03,
        'earnings_growth': -0.52,
        'dividend_yield': 0,
        'beta': 2.04,
    },
}


def get_cached_fundamental_data(symbol):
    return FUNDAMENTAL_DATA_CACHE.get(symbol, {})


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


def get_all_fundamental_scores(symbols):
    scores = {}
    for symbol in symbols:
        data = get_cached_fundamental_data(symbol)
        scores[symbol] = calculate_fundamental_score(data)
    return scores


if __name__ == "__main__":
    symbols = ['AAPL', 'MSFT', 'AMZN', 'GOOGL', 'NVDA', 'META', 'TSLA']
    scores = get_all_fundamental_scores(symbols)
    
    print("基本面评分:")
    for symbol, score in sorted(scores.items(), key=lambda x: x[1], reverse=True):
        print(f"  {symbol}: {score}")
