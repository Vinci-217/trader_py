"""硅基流动AI客户端模块"""
import json
import requests
from typing import Dict, Any, Optional
from ai_quant.config import SILICON_FLOWS_API_KEY, SILICON_FLOWS_BASE_URL, AI_MODEL


SYSTEM_PROMPT = """你是一位专业的股票分析师，擅长技术分析和量化交易。
请根据提供的股票历史数据和技术指标，分析并给出交易建议。

请严格按照以下JSON格式输出，不要输出其他内容：
{
  "trend": "bullish/bearish/sideways",  // 当前趋势判断
  "support": 数值,  // 关键支撑位
  "resistance": 数值,  // 关键阻力位
  "recommendation": "buy/sell/hold",  // 交易建议
  "confidence": 0.0-1.0之间的浮点数,  // 信心指数
  "risk_level": "low/medium/high",  // 风险等级
  "reason": "简要分析原因，不超过50字"  // 分析原因
}

注意：
1. 只输出JSON，不要有其他文字
2. 所有数值使用浮点数
3. reason字段必须用中文
4. 如果数据不足无法判断，recommendation设为"hold"，confidence设为0.5"""


USER_PROMPT_TEMPLATE = """请分析以下股票数据：

股票代码: {symbol}
股票名称: {name}

最近20个交易日数据:
{price_data}

技术指标:
- 收盘价: {close}
- 20日均线: {sma20}
- 50日均线: {sma50}
- RSI(14): {rsi}
- MACD: {macd}
- 布林带: 上轨={bb_upper}, 中轨={bb_mid}, 下轨={bb_lower}
- 成交量: {volume}

请给出你的分析和建议（只输出JSON）："""


class AIClient:
    """硅基流动AI分析客户端"""

    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or SILICON_FLOWS_API_KEY
        self.model = model or AI_MODEL
        self.base_url = SILICON_FLOWS_BASE_URL

    def _call_api(self, messages: list) -> Optional[Dict[str, Any]]:
        """调用硅基流动API"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": 512,
            "temperature": 0.7
        }

        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                return result.get("choices", [{}])[0].get("message", {}).get("content", "")
            else:
                print(f"API调用失败: {response.status_code}, {response.text}")
                return None

        except Exception as e:
            print(f"API调用异常: {e}")
            return None

    def analyze_stock(
        self,
        symbol: str,
        name: str,
        price_data: str,
        close: float,
        sma20: float,
        sma50: float,
        rsi: float,
        macd: float,
        bb_upper: float,
        bb_mid: float,
        bb_lower: float,
        volume: int
    ) -> Optional[Dict[str, Any]]:
        """分析股票并返回交易建议"""

        user_prompt = USER_PROMPT_TEMPLATE.format(
            symbol=symbol,
            name=name,
            price_data=price_data,
            close=close,
            sma20=sma20,
            sma50=sma50,
            rsi=rsi,
            macd=macd,
            bb_upper=bb_upper,
            bb_mid=bb_mid,
            bb_lower=bb_lower,
            volume=volume
        )

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ]

        response = self._call_api(messages)

        if response:
            return self._parse_response(response)

        return None

    def _parse_response(self, response: str) -> Dict[str, Any]:
        """解析AI响应为JSON"""
        try:
            # 尝试提取JSON
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            elif response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]

            data = json.loads(response.strip())

            # 验证必要字段
            required_fields = ["trend", "support", "resistance", "recommendation",
                            "confidence", "risk_level", "reason"]

            for field in required_fields:
                if field not in data:
                    raise ValueError(f"Missing field: {field}")

            return data

        except Exception as e:
            print(f"解析AI响应失败: {e}")
            print(f"原始响应: {response}")
            return None


def test_ai_client():
    """测试AI客户端"""
    client = AIClient()

    test_data = {
        "symbol": "NVDA",
        "name": "英伟达",
        "price_data": "2024-01-02: 480.00, 2024-01-03: 485.50, ...",
        "close": 495.50,
        "sma20": 488.30,
        "sma50": 475.20,
        "rsi": 62.5,
        "macd": 5.2,
        "bb_upper": 502.0,
        "bb_mid": 488.5,
        "bb_lower": 475.0,
        "volume": 45000000
    }

    result = client.analyze_stock(**test_data)
    print("AI分析结果:")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    test_ai_client()
