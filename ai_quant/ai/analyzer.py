import requests
import json
import os
from datetime import datetime


SILICONFLOW_API_KEY = "sk-jphazurlkjtttzdreijixmllsoybabuwnkwvjwmwoyxsbqoy"
SILICONFLOW_BASE_URL = "https://api.siliconflow.cn/v1/chat/completions"


def analyze_stock_with_ai(symbol, price_data, technical_indicators, fundamentals):
    prompt = f"""你是一个专业的股票分析师。请分析以下股票数据，并给出投资建议。

股票代码: {symbol}

最近价格数据:
{price_data}

技术指标:
{technical_indicators}

基本面数据:
{fundamentals}

请按照以下JSON格式返回分析结果（只返回JSON，不要其他内容）:
{{
    "score": <1-10的评分，10表示最值得买入>,
    "recommendation": "<buy/sell/hold>",
    "reason": "<简短理由，50字以内>",
    "confidence": <0.0-1.0的置信度>
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
                {"role": "system", "content": "你是一个专业的股票分析师，擅长技术分析和基本面分析。"},
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
                    return json.loads(json_str)
            except:
                pass
            
            return {"score": 5, "recommendation": "hold", "reason": "AI分析失败", "confidence": 0.5}
        
        return {"score": 5, "recommendation": "hold", "reason": "API调用失败", "confidence": 0.5}
    
    except Exception as e:
        return {"score": 5, "recommendation": "hold", "reason": f"错误: {str(e)}", "confidence": 0.5}


def batch_analyze_stocks(stocks_data):
    results = {}
    
    for symbol, data in stocks_data.items():
        price_data = data.get('price_data', '')
        technical_indicators = data.get('technical_indicators', '')
        fundamentals = data.get('fundamentals', '')
        
        result = analyze_stock_with_ai(symbol, price_data, technical_indicators, fundamentals)
        results[symbol] = result
        
        print(f"  {symbol}: 评分={result.get('score', 5)}, 建议={result.get('recommendation', 'hold')}")
    
    return results


def get_ai_ranking(stocks_data):
    print("\n正在进行AI分析...")
    results = batch_analyze_stocks(stocks_data)
    
    sorted_results = sorted(results.items(), key=lambda x: x[1].get('score', 5), reverse=True)
    
    print("\nAI分析排名:")
    for i, (symbol, result) in enumerate(sorted_results, 1):
        print(f"  {i}. {symbol}: {result.get('score', 5)}分 - {result.get('reason', '')}")
    
    return sorted_results


if __name__ == "__main__":
    test_data = {
        'NVDA': {
            'price_data': '最新价格: $120, 5日涨幅: +5%',
            'technical_indicators': 'RSI: 65, MACD: 金叉',
            'fundamentals': 'PE: 65, 营收增长: 122%'
        },
        'AAPL': {
            'price_data': '最新价格: $200, 5日涨幅: +2%',
            'technical_indicators': 'RSI: 55, MACD: 死叉',
            'fundamentals': 'PE: 28, 营收增长: 8%'
        }
    }
    
    get_ai_ranking(test_data)
