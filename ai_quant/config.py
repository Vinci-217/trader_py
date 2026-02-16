"""AI量化交易配置文件"""
import os

# 硅基流动API配置
SILICON_FLOWS_API_KEY = "sk-jphazurlkjtttzdreijixmllsoybabuwnkwvjwmwoyxsbqoy"
SILICON_FLOWS_BASE_URL = "https://api.siliconflow.cn/v1"

# AI模型选择 - DeepSeek-V3 是高性能模型，适合金融分析
AI_MODEL = "deepseek-ai/DeepSeek-V3"

# 股票配置
STOCKS = {
    "NVDA": "英伟达",
    "TSLA": "特斯拉",
    "AAPL": "苹果"
}

# 交易配置
INITIAL_CASH = 100000.0  # 初始资金
MAX_DAY_TRADES = 3  # 每日最大日内交易次数
STOP_LOSS_PCT = 0.05  # 止损比例 (5%)
TAKE_PROFIT_PCT = 0.10  # 止盈比例 (10%)

# 回测配置
BACKTEST_START_DATE = "2020-01-01"
BACKTEST_END_DATE = "2025-12-31"

# Schwab API配置 (需要用户自行填写)
SCHWAB_APP_KEY = ""
SCHWAB_APP_SECRET = ""
