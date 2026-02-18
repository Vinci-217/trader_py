import requests
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


SILICONFLOW_API_KEY = "sk-jphazurlkjtttzdreijixmllsoybabuwnkwvjwmwoyxsbqoy"
SILICONFLOW_BASE_URL = "https://api.siliconflow.cn/v1/chat/completions"


SENTIMENT_CACHE = {}


def get_stock_sentiment(symbol, force_refresh=False):
    if symbol in SENTIMENT_CACHE and not force_refresh:
        return SENTIMENT_CACHE[symbol]
    
    prompt = f"""分析股票 {symbol} 的投资情绪。

请基于以下方面进行评估：
1. 公司基本面（盈利能力、成长性、估值）
2. 行业前景（AI、云计算、电商等）
3. 市场情绪（机构持仓、分析师评级）

请严格按照以下JSON格式返回（只返回JSON）：
{{
    "sentiment_score": <1-10分，10分最看好>,
    "growth_potential": <1-10分，成长潜力>,
    "risk_level": <1-10分，风险等级，10分最高风险>,
    "recommendation": "<buy/hold/sell>",
    "key_factors": ["因素1", "因素2", "因素3"]
}}
"""
    
    try:
        headers = {
            "Authorization": f"Bearer {SILICONFLOW_API_KEY}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "Qwen/Qwen2.5-7B-Instruct",
            "messages": [
                {"role": "system", "content": "你是一个专业的股票分析师，擅长基本面分析和市场情绪判断。"},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 500
        }
        
        response = requests.post(SILICONFLOW_BASE_URL, headers=headers, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
            
            try:
                start = content.find('{')
                end = content.rfind('}') + 1
                if start != -1 and end > start:
                    json_str = content[start:end]
                    sentiment_data = json.loads(json_str)
                    SENTIMENT_CACHE[symbol] = sentiment_data
                    return sentiment_data
            except:
                pass
        
        default = {
            "sentiment_score": 5,
            "growth_potential": 5,
            "risk_level": 5,
            "recommendation": "hold",
            "key_factors": []
        }
        SENTIMENT_CACHE[symbol] = default
        return default
    
    except Exception as e:
        default = {
            "sentiment_score": 5,
            "growth_potential": 5,
            "risk_level": 5,
            "recommendation": "hold",
            "key_factors": []
        }
        return default


def get_all_sentiments(symbols):
    results = {}
    for symbol in symbols:
        results[symbol] = get_stock_sentiment(symbol)
    return results


def calculate_sentiment_score(sentiment_data):
    if not sentiment_data:
        return 0
    
    sentiment = sentiment_data.get('sentiment_score', 5)
    growth = sentiment_data.get('growth_potential', 5)
    risk = sentiment_data.get('risk_level', 5)
    
    score = sentiment * 0.4 + growth * 0.4 + (10 - risk) * 0.2
    
    return score


if __name__ == "__main__":
    symbols = ['AAPL', 'MSFT', 'NVDA', 'META', 'GOOGL', 'AMZN', 'TSLA']
    
    print("获取股票情绪分析...")
    for symbol in symbols:
        data = get_stock_sentiment(symbol)
        score = calculate_sentiment_score(data)
        print(f"\n{symbol}:")
        print(f"  情绪评分: {data.get('sentiment_score', 5)}")
        print(f"  成长潜力: {data.get('growth_potential', 5)}")
        print(f"  风险等级: {data.get('risk_level', 5)}")
        print(f"  建议: {data.get('recommendation', 'hold')}")
        print(f"  综合得分: {score:.2f}")
