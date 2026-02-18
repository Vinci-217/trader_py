"""
AI Quant - 智能量化交易系统
============================

包结构:
- data: 数据加载模块
- factors: 因子模块 (技术因子、基本面因子)
- ml: 机器学习模块
- strategies: 交易策略
- broker: Schwab券商对接
- runner: 策略运行器

快速开始:
    # 回测
    python -m ai_quant.test_strategies
    
    # 实盘 (需要Schwab账户)
    python -m ai_quant.runner
"""

from .data.loader import load_stock_data, load_all_stocks, get_buy_and_hold_return
from .factors.technical import calculate_technical_features, detect_candlestick_patterns
from .factors.fundamental import get_fundamental_data, calculate_fundamental_score
from .ml.predictor import MLStockPredictor, train_all_models
from .strategies import (
    DefensiveStrategy,
    ConservativeStrategy,
    TrendRider,
    BreakoutDefensive,
    WinnerV1Strategy,
)

__version__ = "3.0"
__all__ = [
    'load_stock_data',
    'load_all_stocks',
    'get_buy_and_hold_return',
    'calculate_technical_features',
    'detect_candlestick_patterns',
    'get_fundamental_data',
    'calculate_fundamental_score',
    'MLStockPredictor',
    'train_all_models',
    'DefensiveStrategy',
    'ConservativeStrategy',
    'TrendRider',
    'BreakoutDefensive',
    'WinnerV1Strategy',
]
