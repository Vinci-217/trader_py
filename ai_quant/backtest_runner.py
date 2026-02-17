#!/usr/bin/env python3
"""
=======================================================
智能量化交易回测系统
=======================================================

使用方法:
    修改下面的配置参数，然后运行:
    python backtest_runner.py

配置说明:
    - SYMBOLS: 股票代码列表
    - START_DATE/END_DATE: 回测时间范围
    - STRATEGY: 选择的策略
    - INITIAL_CASH: 初始资金
    - REBALANCE_DAYS: 调仓频率(天数)

策略选项:
    - "trend_follow": 趋势跟踪策略 (推荐)
    - "composite": 综合信号策略
    - "momentum": 强势动量策略
    - "dual_momentum": 双周期动量策略

=======================================================
"""

import backtrader as bt
import pandas as pd
import numpy as np
import os
import sys
from datetime import datetime

from ai_quant.data.loader import load_stock_data, get_buy_and_hold_return
from ai_quant.strategies.technical_strategies import (
    CompositeSignalStrategy, 
    TrendFollowStrategy, 
    StrongMomentumStrategy, 
    DualMomentumStrategy
)


# =======================================================
# 配置参数 - 修改这里来定制你的回测
# =======================================================

# 股票代码列表
SYMBOLS = ['AAPL', 'MSFT', 'AMZN', 'GOOGL', 'NVDA', 'META', 'TSLA']

# 回测时间范围 (格式: YYYYMMDD)
START_DATE = "20200101"
END_DATE = "20251231"

# 初始资金
INITIAL_CASH = 100000

# 调仓频率 (天数)
REBALANCE_DAYS = 5

# 策略选择
STRATEGY = "trend_follow"  # 选项: "trend_follow", "composite", "momentum", "dual_momentum"

# 策略参数
STRATEGY_PARAMS = {
    "trend_follow": {"rebalance_days": REBALANCE_DAYS},
    "composite": {"rebalance_days": REBALANCE_DAYS, "top_n": 2},
    "momentum": {"rebalance_days": REBALANCE_DAYS},
    "dual_momentum": {"rebalance_days": REBALANCE_DAYS},
}

# 交易费率 (0 = 无手续费)
COMMISSION = 0

# 仓位管理
POSITION_PERCENT = 95


# =======================================================
# 回测引擎
# =======================================================

class BacktestEngine:
    def __init__(self, symbols, start_date, end_date, initial_cash):
        self.symbols = symbols
        self.start_date = start_date
        self.end_date = end_date
        self.initial_cash = initial_cash
        self.results = None
    
    def prepare_data(self, symbol):
        df = load_stock_data(symbol, self.start_date, self.end_date)
        if df is None or df.empty:
            return None
        
        df = df.copy()
        df.index = pd.to_datetime(df.index)
        
        data = bt.feeds.PandasData(
            dataname=df,
            datetime=None,
            open='open',
            high='high',
            low='low',
            close='close',
            volume='volume',
            openinterest=-1
        )
        data._name = symbol
        return data
    
    def run(self, strategy_class, **strategy_params):
        print(f"\n{'='*60}")
        print(f"开始回测")
        print(f"{'='*60}")
        print(f"股票: {', '.join(self.symbols)}")
        print(f"时间: {self.start_date} - {self.end_date}")
        print(f"策略: {strategy_class.__name__}")
        print(f"初始资金: ${self.initial_cash:,.2f}")
        print(f"调仓频率: {strategy_params.get('rebalance_days', 'N/A')}天")
        print(f"{'='*60}\n")
        
        cerebro = bt.Cerebro()
        
        all_data = {}
        for symbol in self.symbols:
            data = self.prepare_data(symbol)
            if data is not None:
                cerebro.adddata(data)
                all_data[symbol] = load_stock_data(symbol, self.start_date, self.end_date)
        
        if not all_data:
            print("错误: 没有加载到任何数据!")
            return None
        
        cerebro.addstrategy(strategy_class, **strategy_params)
        
        cerebro.broker.setcash(self.initial_cash)
        cerebro.broker.setcommission(commission=COMMISSION)
        cerebro.addsizer(bt.sizers.PercentSizer, percents=POSITION_PERCENT)
        
        cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
        cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
        cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
        cerebro.addanalyzer(bt.analyzers.TimeReturn, _name='time_return')
        
        results = cerebro.run()
        
        portfolio_value = cerebro.broker.getvalue()
        strategy_return = (portfolio_value - self.initial_cash) / self.initial_cash
        
        buy_hold_returns = {}
        for symbol, df in all_data.items():
            if df is not None:
                buy_hold_returns[symbol] = get_buy_and_hold_return(df)
        
        avg_buy_hold = np.mean(list(buy_hold_returns.values())) if buy_hold_returns else 0
        max_return = max(buy_hold_returns.values()) if buy_hold_returns else 0
        
        strat = results[0]
        
        self.results = {
            'strategy_return': strategy_return,
            'avg_buy_hold_return': avg_buy_hold,
            'max_buy_hold_return': max_return,
            'buy_hold_returns': buy_hold_returns,
            'outperformance': strategy_return - avg_buy_hold,
            'final_value': portfolio_value,
            'analyzers': strat.analyzers,
        }
        
        return self.results
    
    def print_results(self):
        if not self.results:
            print("没有结果可显示")
            return
        
        r = self.results
        
        print(f"\n{'='*60}")
        print(f"回测结果")
        print(f"{'='*60}")
        
        print(f"\n【收益统计】")
        print(f"  策略总收益: {r['strategy_return']*100:>8.2f}%")
        print(f"  平均买入持有收益: {r['avg_buy_hold_return']*100:>8.2f}%")
        print(f"  最高买入持有收益: {r['max_buy_hold_return']*100:>8.2f}%")
        print(f"  超额收益(vs平均): {(r['strategy_return'] - r['avg_buy_hold_return'])*100:>8.2f}%")
        
        try:
            returns_analyzer = r['analyzers'].returns.get_analysis()
            print(f"\n【年化统计】")
            print(f"  年化收益率: {returns_analyzer.get('rnorm100', 0):>8.2f}%")
        except:
            pass
        
        try:
            sharpe_analyzer = r['analyzers'].sharpe.get_analysis()
            sharpe_ratio = sharpe_analyzer.get('sharperatio', 0)
            if sharpe_ratio and not np.isnan(sharpe_ratio):
                print(f"  夏普比率: {sharpe_ratio:>8.2f}")
        except:
            pass
        
        try:
            dd_analyzer = r['analyzers'].drawdown.get_analysis()
            max_dd = dd_analyzer.get('max', {}).get('drawdown', 0)
            print(f"  最大回撤: {max_dd:>8.2f}%")
        except:
            pass
        
        print(f"\n【各股票买入持有收益】")
        for symbol, ret in sorted(r['buy_hold_returns'].items(), key=lambda x: x[1], reverse=True):
            print(f"  {symbol:>6}: {ret*100:>8.2f}%")
        
        outperformance_vs_all = []
        for symbol, ret in r['buy_hold_returns'].items():
            beat = r['strategy_return'] > ret
            outperformance_vs_all.append(beat)
        
        beat_count = sum(outperformance_vs_all)
        total_count = len(outperformance_vs_all)
        
        print(f"\n【策略表现】")
        print(f"  跑赢股票数: {beat_count}/{total_count}")
        
        if r['strategy_return'] > r['avg_buy_hold_return']:
            print(f"  ✓ 跑赢平均买入持有")
        else:
            print(f"  ✗ 未跑赢平均买入持有")
        
        if r['strategy_return'] > r['max_buy_hold_return']:
            print(f"  ✓ 跑赢最强股票")
        else:
            print(f"  ✗ 未跑赢最强股票")
        
        print(f"\n{'='*60}")
    
    def get_results(self):
        return self.results


# =======================================================
# 主程序
# =======================================================

STRATEGY_MAP = {
    "trend_follow": TrendFollowStrategy,
    "composite": CompositeSignalStrategy,
    "momentum": StrongMomentumStrategy,
    "dual_momentum": DualMomentumStrategy,
}

def main():
    print("="*60)
    print("智能量化交易回测系统 v2.0")
    print("="*60)
    
    if STRATEGY not in STRATEGY_MAP:
        print(f"错误: 未知的策略 '{STRATEGY}'")
        print(f"可用策略: {list(STRATEGY_MAP.keys())}")
        sys.exit(1)
    
    strategy_class = STRATEGY_MAP[STRATEGY]
    strategy_params = STRATEGY_PARAMS.get(STRATEGY, {})
    
    engine = BacktestEngine(
        symbols=SYMBOLS,
        start_date=START_DATE,
        end_date=END_DATE,
        initial_cash=INITIAL_CASH
    )
    
    engine.run(strategy_class, **strategy_params)
    engine.print_results()


if __name__ == "__main__":
    main()
