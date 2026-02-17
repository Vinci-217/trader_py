"""
AI Quant - 智能量化交易系统

包结构:
- data: 数据加载模块
- factors: 因子模块 (技术因子、基本面因子)
- ml: 机器学习模块
- strategies: 交易策略
- backtest_runner.py: 回测运行器

快速开始:
    python -m ai_quant.backtest_runner
"""

from .data.loader import load_stock_data, load_all_stocks, get_buy_and_hold_return
from .factors.technical import calculate_technical_features, detect_candlestick_patterns
from .factors.fundamental import get_fundamental_data, calculate_fundamental_score
from .ml.predictor import MLStockPredictor, train_all_models
from .strategies.technical_strategies import (
    CompositeSignalStrategy,
    TrendFollowStrategy, 
    StrongMomentumStrategy,
    DualMomentumStrategy
)

__version__ = "2.0"
