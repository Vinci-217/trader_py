#!/usr/bin/env python3
"""
=======================================================
AI Quant 策略回测测试
=======================================================
测试所有优质策略的年度收益和回撤
=======================================================
"""

import backtrader as bt
import pandas as pd
import numpy as np

from ai_quant.data.loader import load_stock_data, get_buy_and_hold_return
from ai_quant.strategies import (
    DefensiveStrategy,
    ConservativeStrategy,
    RobustGrowthStrategy,
    BalancedGrowthStrategy,
    TrendRider,
    BreakoutDefensive,
    MomentumFocus,
    SmartDefensive,
    AdaptiveDefensive,
    WinnerV1Strategy,
)


SYMBOLS = ['AAPL', 'MSFT', 'AMZN', 'GOOGL', 'NVDA', 'META', 'TSLA']
START_DATE = "20200101"
END_DATE = "20251231"
INITIAL_CASH = 100000
COMMISSION = 0

RECOMMENDED_STRATEGIES = {
    "TrendRider": {"class": TrendRider, "params": {}, "desc": "趋势追踪(推荐)", "recommended": True},
    "BreakoutDefensive": {"class": BreakoutDefensive, "params": {}, "desc": "突破防御(推荐)", "recommended": True},
    "Defensive": {"class": DefensiveStrategy, "params": {}, "desc": "防御型(稳健)", "recommended": True},
    "Conservative": {"class": ConservativeStrategy, "params": {}, "desc": "保守型(低风险)"},
    "WinnerV1": {"class": WinnerV1Strategy, "params": {}, "desc": "动量策略(高收益)", "recommended": True},
    "MomentumFocus": {"class": MomentumFocus, "params": {}, "desc": "动量聚焦"},
    "SmartDefensive": {"class": SmartDefensive, "params": {}, "desc": "智能防御"},
    "RobustGrowth": {"class": RobustGrowthStrategy, "params": {}, "desc": "稳健增长"},
    "BalancedGrowth": {"class": BalancedGrowthStrategy, "params": {}, "desc": "平衡增长"},
    "AdaptiveDefensive": {"class": AdaptiveDefensive, "params": {}, "desc": "自适应防御"},
}


class BacktestEngine:
    def __init__(self, symbols, start_date, end_date, initial_cash):
        self.symbols = symbols
        self.start_date = start_date
        self.end_date = end_date
        self.initial_cash = initial_cash
    
    def prepare_data(self, symbol):
        df = load_stock_data(symbol, self.start_date, self.end_date, use_cache=True)
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
        cerebro = bt.Cerebro()
        
        all_data = {}
        for symbol in self.symbols:
            data = self.prepare_data(symbol)
            if data is not None:
                cerebro.adddata(data)
                all_data[symbol] = load_stock_data(symbol, self.start_date, self.end_date)
        
        if not all_data:
            return None
        
        cerebro.addstrategy(strategy_class, **strategy_params)
        cerebro.broker.setcash(self.initial_cash)
        cerebro.broker.setcommission(commission=COMMISSION)
        
        cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
        
        results = cerebro.run()
        
        portfolio_value = cerebro.broker.getvalue()
        strategy_return = (portfolio_value - self.initial_cash) / self.initial_cash
        
        buy_hold_returns = {}
        for symbol, df in all_data.items():
            if df is not None:
                buy_hold_returns[symbol] = get_buy_and_hold_return(df)
        
        avg_buy_hold = np.mean(list(buy_hold_returns.values())) if buy_hold_returns else 0
        
        strat = results[0]
        dd_analyzer = strat.analyzers.drawdown.get_analysis()
        max_dd = dd_analyzer.get('max', {}).get('drawdown', 0)
        
        return {
            'strategy_return': strategy_return,
            'avg_buy_hold_return': avg_buy_hold,
            'buy_hold_returns': buy_hold_returns,
            'final_value': portfolio_value,
            'max_drawdown': max_dd,
        }


def run_yearly_backtest(symbols, strategy_class, strategy_params, initial_cash=100000):
    years = ['2020', '2021', '2022', '2023', '2024', '2025']
    
    total_win = 0
    total_years = 0
    yearly_results = []
    positive_years = 0
    
    for year in years:
        start_date = f"{year}0101"
        end_date = f"{year}1231"
        
        engine = BacktestEngine(
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            initial_cash=initial_cash
        )
        
        result = engine.run(strategy_class, **strategy_params)
        
        if result:
            strat_ret = result['strategy_return']
            avg_bh = result['avg_buy_hold_return']
            max_dd = result['max_drawdown']
            beat_avg = strat_ret > avg_bh
            
            yearly_results.append({
                'year': year,
                'return': strat_ret,
                'avg': avg_bh,
                'beat': beat_avg,
                'max_dd': max_dd,
            })
            
            if beat_avg:
                total_win += 1
            if strat_ret > 0:
                positive_years += 1
            total_years += 1
    
    win_rate = total_win / total_years if total_years > 0 else 0
    positive_rate = positive_years / total_years if total_years > 0 else 0
    
    return win_rate, total_win, total_years, yearly_results, positive_years, positive_rate


def test_all_strategies():
    print("="*100)
    print("AI Quant 策略回测测试")
    print("="*100)
    print(f"标的: {SYMBOLS}")
    print(f"日期: {START_DATE} - {END_DATE}")
    print(f"初始资金: ${INITIAL_CASH:,}")
    print("="*100)
    
    results = []
    
    for name, config in RECOMMENDED_STRATEGIES.items():
        strategy_class = config["class"]
        params = config["params"]
        desc = config["desc"]
        recommended = config.get("recommended", False)
        
        marker = "★ " if recommended else "  "
        print(f"{marker}测试 {name} ({desc})...")
        
        win_rate, wins, total, yearly, pos_years, pos_rate = run_yearly_backtest(
            SYMBOLS, strategy_class, params, INITIAL_CASH
        )
        
        results.append({
            'name': name,
            'desc': desc,
            'win_rate': win_rate,
            'wins': wins,
            'total': total,
            'yearly': yearly,
            'positive_years': pos_years,
            'positive_rate': pos_rate,
            'recommended': recommended
        })
    
    results.sort(key=lambda x: (x['positive_rate'], x['win_rate']), reverse=True)
    
    print("\n" + "="*100)
    print("策略排名 (按正收益年数)")
    print("="*100)
    print(f"{'排名':<4} {'策略名称':<20} {'描述':<20} {'正收益年':<10} {'胜率':<10} {'推荐'}")
    print("-"*100)
    
    for i, r in enumerate(results, 1):
        rec = "★" if r['recommended'] else ""
        print(f"{i:<4} {r['name']:<20} {r['desc']:<20} {r['positive_years']}/6       {r['win_rate']*100:.1f}%      {rec}")
    
    print("\n" + "="*100)
    print("推荐策略年度收益详情")
    print("="*100)
    
    for r in results:
        if r['recommended']:
            print(f"\n【{r['name']}】({r['desc']})")
            print(f"正收益年数: {r['positive_years']}/6, 胜率: {r['win_rate']*100:.1f}%")
            print(f"{'年份':<6} {'策略收益':<12} {'平均收益':<12} {'最大回撤':<12} {'结果':<10} {'正收益'}")
            print("-"*70)
            
            for y in r['yearly']:
                status = "✓ 跑赢" if y['beat'] else "✗ 跑输"
                pos_status = "✓ 正" if y['return'] > 0 else "✗ 负"
                print(f"{y['year']:<6} {y['return']*100:>8.2f}%     {y['avg']*100:>8.2f}%     {y['max_dd']:>8.2f}%     {status:<10} {pos_status}")
    
    print("\n" + "="*100)
    print("年度收益对比表")
    print("="*100)
    
    years = ['2020', '2021', '2022', '2023', '2024', '2025']
    
    header = f"{'策略':<20}"
    for year in years:
        header += f" {year:<10}"
    header += f" {'正收益年':<10}"
    print(header)
    print("-"*100)
    
    for r in results[:6]:
        row = f"{r['name']:<20}"
        for y in r['yearly']:
            ret_str = f"{y['return']*100:>6.2f}%"
            row += f" {ret_str:<10}"
        row += f" {r['positive_years']}/6"
        print(row)
    
    print("\n" + "="*100)
    print("年度回撤对比表")
    print("="*100)
    
    header = f"{'策略':<20}"
    for year in years:
        header += f" {year:<10}"
    print(header)
    print("-"*100)
    
    for r in results[:6]:
        row = f"{r['name']:<20}"
        for y in r['yearly']:
            dd_str = f"{y['max_dd']:>6.2f}%"
            row += f" {dd_str:<10}"
        print(row)
    
    best = results[0]
    print(f"\n{'='*100}")
    print(f"最佳策略: {best['name']} ({best['desc']})")
    print(f"正收益年数: {best['positive_years']}/6, 胜率: {best['win_rate']*100:.1f}%")
    print(f"{'='*100}")
    
    return results


def main():
    test_all_strategies()


if __name__ == "__main__":
    main()
