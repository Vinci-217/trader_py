import requests
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time


SILICONFLOW_API_KEY = "sk-jphazurlkjtttzdreijixmllsoybabuwnkwvjwmwoyxsbqoy"
SILICONFLOW_BASE_URL = "https://api.siliconflow.cn/v1/chat/completions"


HISTORICAL_FUNDAMENTALS_CACHE = {}


def get_historical_fundamentals(symbol, year):
    cache_key = f"{symbol}_{year}"
    if cache_key in HISTORICAL_FUNDAMENTALS_CACHE:
        return HISTORICAL_FUNDAMENTALS_CACHE[cache_key]
    
    prompt = f"""你是一个专业的股票分析师。请分析 {symbol} 在 {year} 年的基本面情况。

请基于 {year} 年的实际历史情况，分析以下内容：

1. **营收增长**: {year}年的营收增长率
2. **盈利能力**: 净利润率、毛利率
3. **估值水平**: PE、PB估值
4. **行业地位**: 在行业中的竞争地位
5. **重大事件**: {year}年的重大事件（如产品发布、收购等）

请严格按照以下JSON格式返回（只返回JSON）：
{{
    "year": {year},
    "revenue_growth": <营收增长率，如0.2表示20%>,
    "profit_margin": <净利润率，如0.15表示15%>,
    "pe_ratio": <市盈率>,
    "industry_position": "<行业地位: leader/challenger/follower>",
    "key_events": ["事件1", "事件2"],
    "growth_potential": <成长潜力评分1-10>,
    "risk_level": <风险等级1-10>,
    "overall_score": <综合评分1-10>,
    "investment_thesis": "<投资逻辑简述>"
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
                {"role": "system", "content": "你是一个专业的股票分析师，擅长历史基本面分析。请基于真实历史数据回答。"},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 800
        }
        
        response = requests.post(SILICONFLOW_BASE_URL, headers=headers, json=data, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
            
            try:
                start = content.find('{')
                end = content.rfind('}') + 1
                if start != -1 and end > start:
                    json_str = content[start:end]
                    fund_data = json.loads(json_str)
                    HISTORICAL_FUNDAMENTALS_CACHE[cache_key] = fund_data
                    return fund_data
            except:
                pass
        
        default = {
            "year": year,
            "revenue_growth": 0.1,
            "profit_margin": 0.15,
            "pe_ratio": 25,
            "industry_position": "challenger",
            "key_events": [],
            "growth_potential": 5,
            "risk_level": 5,
            "overall_score": 5,
            "investment_thesis": "中性"
        }
        HISTORICAL_FUNDAMENTALS_CACHE[cache_key] = default
        return default
    
    except Exception as e:
        default = {
            "year": year,
            "revenue_growth": 0.1,
            "profit_margin": 0.15,
            "pe_ratio": 25,
            "industry_position": "challenger",
            "key_events": [],
            "growth_potential": 5,
            "risk_level": 5,
            "overall_score": 5,
            "investment_thesis": "中性"
        }
        return default


def get_historical_sentiment(symbol, year):
    cache_key = f"sentiment_{symbol}_{year}"
    if cache_key in HISTORICAL_FUNDAMENTALS_CACHE:
        return HISTORICAL_FUNDAMENTALS_CACHE[cache_key]
    
    prompt = f"""你是一个专业的股票分析师。请分析 {symbol} 在 {year} 年的市场情绪和投资氛围。

请基于 {year} 年的实际历史情况，分析以下内容：

1. **市场热度**: 投资者关注度
2. **机构态度**: 机构投资者的持仓变化
3. **分析师评级**: 华尔街分析师的评级
4. **新闻情绪**: 媒体报道的整体情绪
5. **行业趋势**: 所处行业的整体趋势

请严格按照以下JSON格式返回（只返回JSON）：
{{
    "year": {year},
    "market_heat": <市场热度1-10>,
    "institutional_sentiment": <机构态度: bullish/neutral/bearish>,
    "analyst_rating": <分析师平均评级: buy/hold/sell>,
    "news_sentiment": <新闻情绪1-10>,
    "industry_trend": <行业趋势: growing/stable/declining>,
    "sentiment_score": <综合情绪评分1-10>,
    "key_themes": ["主题1", "主题2"],
    "investment_recommendation": "<投资建议>"
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
                {"role": "system", "content": "你是一个专业的股票分析师，擅长市场情绪分析。请基于真实历史数据回答。"},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 600
        }
        
        response = requests.post(SILICONFLOW_BASE_URL, headers=headers, json=data, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
            
            try:
                start = content.find('{')
                end = content.rfind('}') + 1
                if start != -1 and end > start:
                    json_str = content[start:end]
                    sent_data = json.loads(json_str)
                    HISTORICAL_FUNDAMENTALS_CACHE[cache_key] = sent_data
                    return sent_data
            except:
                pass
        
        default = {
            "year": year,
            "market_heat": 5,
            "institutional_sentiment": "neutral",
            "analyst_rating": "hold",
            "news_sentiment": 5,
            "industry_trend": "stable",
            "sentiment_score": 5,
            "key_themes": [],
            "investment_recommendation": "持有"
        }
        HISTORICAL_FUNDAMENTALS_CACHE[cache_key] = default
        return default
    
    except Exception as e:
        default = {
            "year": year,
            "market_heat": 5,
            "institutional_sentiment": "neutral",
            "analyst_rating": "hold",
            "news_sentiment": 5,
            "industry_trend": "stable",
            "sentiment_score": 5,
            "key_themes": [],
            "investment_recommendation": "持有"
        }
        return default


def calculate_historical_score(fund_data, sent_data):
    if not fund_data or not sent_data:
        return 5
    
    growth = fund_data.get('growth_potential', 5)
    risk = fund_data.get('risk_level', 5)
    overall = fund_data.get('overall_score', 5)
    revenue_growth = fund_data.get('revenue_growth', 0)
    
    market_heat = sent_data.get('market_heat', 5)
    news_sentiment = sent_data.get('news_sentiment', 5)
    sentiment_score = sent_data.get('sentiment_score', 5)
    
    fund_score = growth * 0.3 + (10 - risk) * 0.2 + overall * 0.3 + min(10, revenue_growth * 20) * 0.2
    
    sent_score = market_heat * 0.3 + news_sentiment * 0.3 + sentiment_score * 0.4
    
    combined_score = fund_score * 0.6 + sent_score * 0.4
    
    return combined_score


def get_all_historical_data(symbols, year):
    print(f"\n获取 {year} 年历史数据...")
    results = {}
    
    for symbol in symbols:
        print(f"  获取 {symbol} 数据...")
        fund_data = get_historical_fundamentals(symbol, year)
        sent_data = get_historical_sentiment(symbol, year)
        score = calculate_historical_score(fund_data, sent_data)
        
        results[symbol] = {
            'fundamentals': fund_data,
            'sentiment': sent_data,
            'score': score
        }
        
        time.sleep(0.5)
    
    return results


if __name__ == "__main__":
    symbols = ['AAPL', 'MSFT', 'NVDA', 'META', 'GOOGL', 'AMZN', 'TSLA']
    
    for year in ['2022', '2023']:
        print(f"\n{'='*60}")
        print(f"{year}年数据分析")
        print(f"{'='*60}")
        
        data = get_all_historical_data(symbols, year)
        
        sorted_data = sorted(data.items(), key=lambda x: x[1]['score'], reverse=True)
        
        print(f"\n排名:")
        for i, (symbol, d) in enumerate(sorted_data, 1):
            fund = d['fundamentals']
            sent = d['sentiment']
            print(f"{i}. {symbol}: 综合得分 {d['score']:.2f}")
            print(f"   基本面: 成长{fund.get('growth_potential', 5)}/10, 风险{fund.get('risk_level', 5)}/10")
            print(f"   情绪: 热度{sent.get('market_heat', 5)}/10, 情绪{sent.get('sentiment_score', 5)}/10")
