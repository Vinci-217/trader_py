"""回测模块"""
import backtrader as bt
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Optional
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from ai_quant.config import STOCKS, INITIAL_CASH, BACKTEST_START_DATE, BACKTEST_END_DATE
from ai_quant.strategy import MultiIndicatorStrategy
from ai_quant.strategy_v2 import ConservativeStrategy, VeryConservativeStrategy
from ai_quant.strategy_v3 import BalancedStrategy
from ai_quant.strategy_v4 import FlexibleStrategy
from ai_quant.stock_strategies import NVDAStrategy, TSLAStrategy, AAPLStrategy
from ai_quant.stock_strategies_ultimate import (
    NVDA_Ultimate, TSLA_Ultimate, AAPL_Ultimate,
    MSFT_Ultimate, AMZN_Ultimate, GOOGL_Ultimate,
    META_Ultimate, AMAT_Ultimate
)
from ai_quant.stock_strategies_hf import (
    NVDA_HF, TSLA_HF, AAPL_HF,
    MSFT_HF, AMZN_HF, GOOGL_HF,
    META_HF, AMAT_HF
)
from ai_quant.stock_strategies_volatile import (
    NVDA_Volatile, TSLA_Volatile, AAPL_Volatile,
    MSFT_Volatile, AMZN_Volatile, GOOGL_Volatile,
    META_Volatile, AMAT_Volatile
)
from quant.data_get import get_us_stock


class BacktestResult:
    """回测结果"""
    def __init__(self):
        self.total_return = 0.0
        self.max_drawdown = 0.0
        self.sharpe_ratio = 0.0
        self.total_trades = 0
        self.win_rate = 0.0
        self.final_value = 0.0
        self.avg_win = 0.0
        self.avg_loss = 0.0


def prepare_data(stock_code: str, start_date: str, end_date: str) -> pd.DataFrame:
    """准备回测数据"""
    try:
        df = get_us_stock(stock_code, start_date.replace('-', ''), end_date.replace('-', ''))
        if df is None or df.empty:
            print(f"获取数据失败: {stock_code}")
            return None
        
        df = df.rename(columns={
            '日期': 'date',
            '开盘': 'open',
            '收盘': 'close',
            '最高': 'high',
            '最低': 'low',
            '成交量': 'volume'
        })
        
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date')
        df = df.sort_index()
        
        return df
    except Exception as e:
        print(f"准备数据失败: {e}")
        return None


def run_backtest(
    stock_code: str,
    stock_name: str,
    start_date: str = None,
    end_date: str = None,
    initial_cash: float = INITIAL_CASH,
    commission: float = 0,  # 手续费默认为0
    strategy_name: str = "conservative"
) -> BacktestResult:
    """运行单支股票回测"""
    
    result = BacktestResult()
    
    start_date = start_date or BACKTEST_START_DATE
    end_date = end_date or BACKTEST_END_DATE
    
    print(f"\n{'='*50}")
    print(f"开始回测: {stock_name} ({stock_code})")
    print(f"策略: {strategy_name}")
    print(f"时间范围: {start_date} - {end_date}")
    print(f"初始资金: ${initial_cash}")
    print(f"{'='*50}\n")
    
    data = prepare_data(stock_code, start_date, end_date)
    if data is None:
        return result
    
    cerebro = bt.Cerebro()
    
    data_feed = bt.feeds.PandasData(
        dataname=data,
        name=stock_name
    )
    cerebro.adddata(data_feed)
    
    if strategy_name == "original":
        cerebro.addstrategy(MultiIndicatorStrategy)
    elif strategy_name == "conservative":
        cerebro.addstrategy(ConservativeStrategy)
    elif strategy_name == "very_conservative":
        cerebro.addstrategy(VeryConservativeStrategy)
    elif strategy_name == "balanced":
        cerebro.addstrategy(BalancedStrategy)
    elif strategy_name == "flexible":
        cerebro.addstrategy(FlexibleStrategy)
    elif strategy_name == "nvda":
        cerebro.addstrategy(NVDAStrategy)
    elif strategy_name == "tsla":
        cerebro.addstrategy(TSLAStrategy)
    elif strategy_name == "aapl":
        cerebro.addstrategy(AAPLStrategy)
    elif strategy_name == "nvda_ultimate":
        cerebro.addstrategy(NVDA_Ultimate)
    elif strategy_name == "tsla_ultimate":
        cerebro.addstrategy(TSLA_Ultimate)
    elif strategy_name == "aapl_ultimate":
        cerebro.addstrategy(AAPL_Ultimate)
    elif strategy_name == "msft_ultimate":
        cerebro.addstrategy(MSFT_Ultimate)
    elif strategy_name == "amzn_ultimate":
        cerebro.addstrategy(AMZN_Ultimate)
    elif strategy_name == "googl_ultimate":
        cerebro.addstrategy(GOOGL_Ultimate)
    elif strategy_name == "meta_ultimate":
        cerebro.addstrategy(META_Ultimate)
    elif strategy_name == "amat_ultimate":
        cerebro.addstrategy(AMAT_Ultimate)
    elif strategy_name == "nvda_hf":
        cerebro.addstrategy(NVDA_HF)
    elif strategy_name == "tsla_hf":
        cerebro.addstrategy(TSLA_HF)
    elif strategy_name == "aapl_hf":
        cerebro.addstrategy(AAPL_HF)
    elif strategy_name == "msft_hf":
        cerebro.addstrategy(MSFT_HF)
    elif strategy_name == "amzn_hf":
        cerebro.addstrategy(AMZN_HF)
    elif strategy_name == "googl_hf":
        cerebro.addstrategy(GOOGL_HF)
    elif strategy_name == "meta_hf":
        cerebro.addstrategy(META_HF)
    elif strategy_name == "amat_hf":
        cerebro.addstrategy(AMAT_HF)
    elif strategy_name == "nvda_volatile":
        cerebro.addstrategy(NVDA_Volatile)
    elif strategy_name == "tsla_volatile":
        cerebro.addstrategy(TSLA_Volatile)
    elif strategy_name == "aapl_volatile":
        cerebro.addstrategy(AAPL_Volatile)
    elif strategy_name == "msft_volatile":
        cerebro.addstrategy(MSFT_Volatile)
    elif strategy_name == "amzn_volatile":
        cerebro.addstrategy(AMZN_Volatile)
    elif strategy_name == "googl_volatile":
        cerebro.addstrategy(GOOGL_Volatile)
    elif strategy_name == "meta_volatile":
        cerebro.addstrategy(META_Volatile)
    elif strategy_name == "amat_volatile":
        cerebro.addstrategy(AMAT_Volatile)
    else:
        cerebro.addstrategy(FlexibleStrategy)
    
    cerebro.broker.setcash(initial_cash)
    cerebro.broker.setcommission(commission=commission)
    cerebro.addsizer(bt.sizers.PercentSizer, percents=90)
    
    cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
    
    try:
        results = cerebro.run()
        strat = results[0]
        
        final_value = cerebro.broker.getvalue()
        result.total_return = (final_value / initial_cash - 1) * 100
        result.final_value = final_value
        
        dd = strat.analyzers.drawdown.get_analysis()
        result.max_drawdown = abs(dd.get('max', {}).get('drawdown', 0))
        
        sharpe = strat.analyzers.sharpe.get_analysis()
        result.sharpe_ratio = sharpe.get('sharperatio', 0) or 0
        
        trades = strat.analyzers.trades.get_analysis()
        total_trades = trades.get('total', {}).get('total', 0)
        won_trades = trades.get('won', {}).get('total', 0)
        lost_trades = trades.get('lost', {}).get('total', 0)
        
        result.total_trades = total_trades
        result.win_rate = (won_trades / total_trades * 100) if total_trades > 0 else 0
        
        if won_trades > 0:
            result.avg_win = trades.get('won', {}).get('pnl', {}).get('average', 0)
        if lost_trades > 0:
            result.avg_loss = trades.get('lost', {}).get('pnl', {}).get('average', 0)
        
        print(f"\n{'='*50}")
        print(f"回测结果: {stock_name}")
        print(f"{'='*50}")
        print(f"总交易次数: {total_trades}")
        print(f"盈利次数: {won_trades}")
        print(f"亏损次数: {lost_trades}")
        print(f"胜率: {result.win_rate:.2f}%")
        print(f"平均盈利: ${result.avg_win:.2f}")
        print(f"平均亏损: ${result.avg_loss:.2f}")
        print(f"总收益率: {result.total_return:.2f}%")
        print(f"最大回撤: {result.max_drawdown:.2f}%")
        print(f"夏普比率: {result.sharpe_ratio:.4f}")
        print(f"最终资金: ${final_value:,.2f}")
        print(f"{'='*50}\n")
        
    except Exception as e:
        print(f"回测执行失败: {e}")
        import traceback
        traceback.print_exc()
    
    return result


def run_backtest_all(
    stocks: List[Dict[str, str]] = None,
    start_date: str = None,
    end_date: str = None,
    strategy_name: str = "conservative"
) -> Dict[str, BacktestResult]:
    """运行所有股票回测"""
    
    stocks = stocks or STOCKS
    results = {}
    
    for stock in stocks:
        code = stock.get('code')
        name = stock.get('name')
        result = run_backtest(code, name, start_date, end_date, strategy_name=strategy_name)
        results[name] = result
    
    return results


if __name__ == "__main__":
    run_backtest("105.NVDA", "NVDA", "2020-01-01", "2024-12-31", strategy_name="nvda_ultimate")
