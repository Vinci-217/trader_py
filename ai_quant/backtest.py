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
from ai_quant.stock_strategies_v2 import NVDAStrategyV2, TSLAStrategyV2, AAPLStrategyV2
from ai_quant.stock_strategies_v3 import NVDAStrategyV3, TSLAStrategyV3, AAPLStrategyV3
from ai_quant.stock_strategies_smart import NVDA_Smart, TSLA_Smart, AAPL_Smart
from ai_quant.stock_strategies_bullbear import (
    NVDA_BullBear, TSLA_BullBear, AAPL_BullBear,
    MSFT_BullBear, AMZN_BullBear, GOOGL_BullBear, 
    META_BullBear, AMAT_BullBear
)
from ai_quant.stock_strategies_aggressive import (
    NVDA_Aggressive, TSLA_Aggressive, AAPL_Aggressive,
    MSFT_Aggressive, AMZN_Aggressive, GOOGL_Aggressive,
    META_Aggressive, AMAT_Aggressive
)
from ai_quant.stock_strategies_smartscore import (
    NVDA_SmartScore, TSLA_SmartScore, AAPL_SmartScore,
    MSFT_SmartScore, AMZN_SmartScore, GOOGL_SmartScore,
    META_SmartScore, AMAT_SmartScore
)
from ai_quant.stock_strategies_multi import MultiStrategy
from ai_quant.stock_strategies_ultimate import (
    NVDA_Ultimate, TSLA_Ultimate, AAPL_Ultimate,
    MSFT_Ultimate, AMZN_Ultimate, GOOGL_Ultimate,
    META_Ultimate, AMAT_Ultimate
)
from ai_quant.stock_strategies_ai import (
    NVDA_AI, TSLA_AI, AAPL_AI,
    MSFT_AI, AMZN_AI, GOOGL_AI,
    META_AI, AMAT_AI
)
from quant.data_get import get_us_stock


class BacktestResult:
    """回测结果"""

    def __init__(self):
        self.trades: List[Dict[str, Any]] = []
        self.initial_cash = INITIAL_CASH
        self.final_value = 0
        self.total_return = 0
        self.win_rate = 0
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.avg_win = 0
        self.avg_loss = 0
        self.max_drawdown = 0
        self.sharpe_ratio = 0


def prepare_data(stock_code: str, start_date: str, end_date: str) -> Optional[bt.feeds.PandasData]:
    """准备股票数据"""
    try:
        df = get_us_stock(stock_code, start_date, end_date)

        if df is None or df.empty:
            print(f"无法获取 {stock_code} 的数据")
            return None

        df.rename(columns={
            '日期': 'datetime',
            '开盘': 'open',
            '最高': 'high',
            '最低': 'low',
            '收盘': 'close',
            '成交量': 'volume'
        }, inplace=True)

        df['datetime'] = pd.to_datetime(df['datetime'])
        df.set_index('datetime', inplace=True)

        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        df = df.dropna()

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

        return data

    except Exception as e:
        print(f"数据准备失败: {e}")
        return None


class TradeAnalyzer(bt.Analyzer):
    """交易分析器"""

    def __init__(self):
        self.trades = []
        self.total_pnl = 0

    def notify_trade(self, trade):
        if trade.isclosed:
            self.trades.append({
                'pnl': trade.pnl,
                'pnlcomm': trade.pnlcomm,
                'price': trade.price,
                'size': trade.size
            })
            self.total_pnl += trade.pnlcomm

    def get_analysis(self):
        return {
            'trades': self.trades,
            'total_pnl': self.total_pnl
        }


def run_backtest(
    stock_code: str,
    stock_name: str,
    start_date: str = None,
    end_date: str = None,
    initial_cash: float = INITIAL_CASH,
    commission: float = 0.001,
    strategy_name: str = "conservative"
) -> BacktestResult:
    """运行单支股票回测

    Args:
        stock_code: 股票代码 (如 105.NVDA)
        stock_name: 股票名称
        start_date: 开始日期
        end_date: 结束日期
        initial_cash: 初始资金
        commission: 佣金比例
        strategy_name: 策略名称 "original"/"conservative"/"very_conservative"

    Returns:
        BacktestResult对象
    """
    start_date = start_date or BACKTEST_START_DATE
    end_date = end_date or BACKTEST_END_DATE

    result = BacktestResult()

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

    cerebro.adddata(data)

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
    elif strategy_name == "nvda_v2":
        cerebro.addstrategy(NVDAStrategyV2)
    elif strategy_name == "tsla_v2":
        cerebro.addstrategy(TSLAStrategyV2)
    elif strategy_name == "aapl_v2":
        cerebro.addstrategy(AAPLStrategyV2)
    elif strategy_name == "nvda_v3":
        cerebro.addstrategy(NVDAStrategyV3)
    elif strategy_name == "tsla_v3":
        cerebro.addstrategy(TSLAStrategyV3)
    elif strategy_name == "aapl_v3":
        cerebro.addstrategy(AAPLStrategyV3)
    elif strategy_name == "nvda_smart":
        cerebro.addstrategy(NVDA_Smart)
    elif strategy_name == "tsla_smart":
        cerebro.addstrategy(TSLA_Smart)
    elif strategy_name == "aapl_smart":
        cerebro.addstrategy(AAPL_Smart)
    elif strategy_name == "nvda_bullbear":
        cerebro.addstrategy(NVDA_BullBear)
    elif strategy_name == "tsla_bullbear":
        cerebro.addstrategy(TSLA_BullBear)
    elif strategy_name == "aapl_bullbear":
        cerebro.addstrategy(AAPL_BullBear)
    elif strategy_name == "msft_bullbear":
        cerebro.addstrategy(MSFT_BullBear)
    elif strategy_name == "amzn_bullbear":
        cerebro.addstrategy(AMZN_BullBear)
    elif strategy_name == "googl_bullbear":
        cerebro.addstrategy(GOOGL_BullBear)
    elif strategy_name == "meta_bullbear":
        cerebro.addstrategy(META_BullBear)
    elif strategy_name == "amat_bullbear":
        cerebro.addstrategy(AMAT_BullBear)
    elif strategy_name == "nvda_aggressive":
        cerebro.addstrategy(NVDA_Aggressive)
    elif strategy_name == "tsla_aggressive":
        cerebro.addstrategy(TSLA_Aggressive)
    elif strategy_name == "aapl_aggressive":
        cerebro.addstrategy(AAPL_Aggressive)
    elif strategy_name == "msft_aggressive":
        cerebro.addstrategy(MSFT_Aggressive)
    elif strategy_name == "amzn_aggressive":
        cerebro.addstrategy(AMZN_Aggressive)
    elif strategy_name == "googl_aggressive":
        cerebro.addstrategy(GOOGL_Aggressive)
    elif strategy_name == "meta_aggressive":
        cerebro.addstrategy(META_Aggressive)
    elif strategy_name == "amat_aggressive":
        cerebro.addstrategy(AMAT_Aggressive)
    elif strategy_name == "nvda_smartscore":
        cerebro.addstrategy(NVDA_SmartScore)
    elif strategy_name == "tsla_smartscore":
        cerebro.addstrategy(TSLA_SmartScore)
    elif strategy_name == "aapl_smartscore":
        cerebro.addstrategy(AAPL_SmartScore)
    elif strategy_name == "msft_smartscore":
        cerebro.addstrategy(MSFT_SmartScore)
    elif strategy_name == "amzn_smartscore":
        cerebro.addstrategy(AMZN_SmartScore)
    elif strategy_name == "googl_smartscore":
        cerebro.addstrategy(GOOGL_SmartScore)
    elif strategy_name == "meta_smartscore":
        cerebro.addstrategy(META_SmartScore)
    elif strategy_name == "amat_smartscore":
        cerebro.addstrategy(AMAT_SmartScore)
    elif strategy_name == "multi":
        cerebro.addstrategy(MultiStrategy)
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
    elif strategy_name == "nvda_ai":
        cerebro.addstrategy(NVDA_AI)
    elif strategy_name == "tsla_ai":
        cerebro.addstrategy(TSLA_AI)
    elif strategy_name == "aapl_ai":
        cerebro.addstrategy(AAPL_AI)
    elif strategy_name == "msft_ai":
        cerebro.addstrategy(MSFT_AI)
    elif strategy_name == "amzn_ai":
        cerebro.addstrategy(AMZN_AI)
    elif strategy_name == "googl_ai":
        cerebro.addstrategy(GOOGL_AI)
    elif strategy_name == "meta_ai":
        cerebro.addstrategy(META_AI)
    elif strategy_name == "amat_ai":
        cerebro.addstrategy(AMAT_AI)
    else:
        cerebro.addstrategy(FlexibleStrategy)

    cerebro.broker.setcash(initial_cash)

    cerebro.broker.setcommission(commission=commission)

    cerebro.addsizer(bt.sizers.PercentSizer, percents=90)

    cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe', riskfreerate=0.02)
    cerebro.addanalyzer(TradeAnalyzer, _name='trades')

    try:
        results = cerebro.run()
        strat = results[0]

        result.final_value = cerebro.broker.getvalue()
        result.total_return = (result.final_value - initial_cash) / initial_cash

        trades_data = strat.analyzers.trades.get_analysis()
        trades = trades_data.get('trades', [])

        result.total_trades = len(trades)
        if result.total_trades > 0:
            winning = [t for t in trades if t['pnlcomm'] > 0]
            losing = [t for t in trades if t['pnlcomm'] <= 0]

            result.winning_trades = len(winning)
            result.losing_trades = len(losing)
            result.win_rate = result.winning_trades / result.total_trades if result.total_trades > 0 else 0

            result.avg_win = np.mean([t['pnlcomm'] for t in winning]) if winning else 0
            result.avg_loss = np.mean([t['pnlcomm'] for t in losing]) if losing else 0

        dd_data = strat.analyzers.drawdown.get_analysis()
        result.max_drawdown = dd_data.get('max', {}).get('drawdown', 0)

        sharpe_data = strat.analyzers.sharpe.get_analysis()
        result.sharpe_ratio = sharpe_data.get('sharperatio', 0)

        print(f"\n{'='*50}")
        print(f"回测结果: {stock_name}")
        print(f"{'='*50}")
        print(f"总交易次数: {result.total_trades}")
        print(f"盈利次数: {result.winning_trades}")
        print(f"亏损次数: {result.losing_trades}")
        print(f"胜率: {result.win_rate*100:.2f}%")
        print(f"平均盈利: ${result.avg_win:.2f}")
        print(f"平均亏损: ${result.avg_loss:.2f}")
        print(f"总收益率: {result.total_return*100:.2f}%")
        print(f"最大回撤: {result.max_drawdown:.2f}%")
        sharpe = result.sharpe_ratio if result.sharpe_ratio else 0
        print(f"夏普比率: {sharpe:.4f}")
        print(f"最终资金: ${result.final_value:,.2f}")
        print(f"{'='*50}\n")

    except Exception as e:
        print(f"回测执行失败: {e}")
        import traceback
        traceback.print_exc()

    return result


def run_multi_stock_backtest(
    stocks: Dict[str, str] = None,
    start_date: str = None,
    end_date: str = None
) -> Dict[str, BacktestResult]:
    """多支股票回测

    Args:
        stocks: 股票字典 {代码: 名称}
        start_date: 开始日期
        end_date: 结束日期

    Returns:
        各股票回测结果字典
    """
    stocks = stocks or STOCKS

    stock_code_map = {
        "NVDA": "105.NVDA",
        "TSLA": "105.TSLA",
        "AAPL": "105.AAPL"
    }

    results = {}

    for symbol, name in stocks.items():
        stock_code = stock_code_map.get(symbol, f"105.{symbol}")
        result = run_backtest(stock_code, name, start_date, end_date)
        results[symbol] = result

    print_summary(results)

    return results


def print_summary(results: Dict[str, BacktestResult]):
    """打印汇总结果"""
    print("\n" + "="*60)
    print("多股票回测汇总")
    print("="*60)

    total_return = 0
    total_trades = 0
    total_wins = 0
    total_loss = 0

    for symbol, result in results.items():
        total_return += result.total_return
        total_trades += result.total_trades
        total_wins += result.winning_trades
        total_loss += result.losing_trades

    avg_win_rate = (total_wins / total_trades * 100) if total_trades > 0 else 0

    print(f"总交易次数: {total_trades}")
    print(f"总盈利次数: {total_wins}")
    print(f"总亏损次数: {total_loss}")
    print(f"综合胜率: {avg_win_rate:.2f}%")
    print(f"平均收益率: {total_return/len(results)*100:.2f}%")
    print("="*60)


if __name__ == "__main__":
    results = run_multi_stock_backtest()
