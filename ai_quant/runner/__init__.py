"""
Strategy Runner
===============
策略运行器 - 将回测策略与实盘交易对接
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any, Type
import importlib

from ..broker.schwab_client import SchwabClient
from ..broker.schwab_trader import SchwabTrader
from ..data.loader import load_stock_data


class StrategyRunner:
    """
    策略运行器
    
    支持回测和实盘两种模式
    """
    
    def __init__(
        self,
        strategy_name: str,
        symbols: List[str],
        mode: str = 'backtest',
        dry_run: bool = True
    ):
        """
        初始化策略运行器
        
        Args:
            strategy_name: 策略名称 (如 'TrendRider', 'Defensive', 'WinnerV1')
            symbols: 交易标的列表
            mode: 运行模式 ('backtest' 或 'live')
            dry_run: 实盘模式下是否模拟运行
        """
        self.strategy_name = strategy_name
        self.symbols = symbols
        self.mode = mode
        self.dry_run = dry_run
        
        self._strategy_class = None
        self._trader = None
        self._client = None
    
    def load_strategy(self) -> bool:
        """
        加载策略类
        
        Returns:
            是否加载成功
        """
        strategy_map = {
            'TrendRider': ('advanced_defensive', 'TrendRider'),
            'BreakoutDefensive': ('advanced_defensive', 'BreakoutDefensive'),
            'MomentumFocus': ('advanced_defensive', 'MomentumFocus'),
            'SmartDefensive': ('advanced_defensive', 'SmartDefensive'),
            'Defensive': ('robust', 'DefensiveStrategy'),
            'Conservative': ('robust', 'ConservativeStrategy'),
            'RobustGrowth': ('robust', 'RobustGrowthStrategy'),
            'WinnerV1': ('winner_v1', 'WinnerV1Strategy'),
        }
        
        if self.strategy_name not in strategy_map:
            print(f"未知策略: {self.strategy_name}")
            print(f"可用策略: {list(strategy_map.keys())}")
            return False
        
        module_name, class_name = strategy_map[self.strategy_name]
        
        try:
            module = importlib.import_module(f'ai_quant.strategies.{module_name}')
            self._strategy_class = getattr(module, class_name)
            print(f"已加载策略: {self.strategy_name}")
            return True
        except Exception as e:
            print(f"加载策略失败: {e}")
            return False
    
    def setup_broker(self, app_key: str, app_secret: str, callback_url: str = 'https://127.0.0.1'):
        """
        设置券商连接
        
        Args:
            app_key: Schwab App Key
            app_secret: Schwab App Secret
            callback_url: OAuth回调URL
        """
        self._client = SchwabClient(
            app_key=app_key,
            app_secret=app_secret,
            callback_url=callback_url
        )
        
        self._trader = SchwabTrader(
            client=self._client,
            dry_run=self.dry_run
        )
    
    def authenticate(self) -> bool:
        """
        执行OAuth认证
        
        Returns:
            是否认证成功
        """
        if self._client is None:
            print("请先调用 setup_broker() 设置券商连接")
            return False
        
        return self._client.authenticate()
    
    def run_backtest(
        self,
        start_date: str = '20200101',
        end_date: str = '20251231',
        initial_cash: float = 100000
    ) -> Dict[str, Any]:
        """
        运行回测
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            initial_cash: 初始资金
        
        Returns:
            回测结果
        """
        if self._strategy_class is None:
            if not self.load_strategy():
                return {}
        
        import backtrader as bt
        
        cerebro = bt.Cerebro()
        cerebro.addstrategy(self._strategy_class)
        cerebro.broker.setcash(initial_cash)
        
        all_data = {}
        for symbol in self.symbols:
            df = load_stock_data(symbol, start_date, end_date, use_cache=True)
            if df is not None and not df.empty:
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
                cerebro.adddata(data)
                all_data[symbol] = df
        
        cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
        cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
        
        print(f"运行回测: {self.strategy_name}")
        print(f"标的: {self.symbols}")
        print(f"日期: {start_date} - {end_date}")
        
        results = cerebro.run()
        
        strat = results[0]
        final_value = cerebro.broker.getvalue()
        total_return = (final_value - initial_cash) / initial_cash
        
        dd_analysis = strat.analyzers.drawdown.get_analysis()
        max_dd = dd_analysis.get('max', {}).get('drawdown', 0)
        
        return {
            'strategy': self.strategy_name,
            'start_date': start_date,
            'end_date': end_date,
            'initial_cash': initial_cash,
            'final_value': final_value,
            'total_return': total_return,
            'max_drawdown': max_dd,
            'symbols': self.symbols
        }
    
    def run_live(self) -> Dict[str, Any]:
        """
        运行实盘
        
        Returns:
            执行结果
        """
        if self._trader is None:
            print("请先调用 setup_broker() 和 authenticate()")
            return {'success': False, 'error': '未连接券商'}
        
        if not self._trader.connect():
            return {'success': False, 'error': '连接失败'}
        
        self._trader.sync_positions()
        
        signals = self._generate_signals()
        
        if not signals:
            return {'success': True, 'message': '无交易信号'}
        
        results = self._trader.execute_strategy_signals(signals)
        
        return {
            'success': True,
            'signals': signals,
            'results': results
        }
    
    def _generate_signals(self) -> Dict[str, str]:
        """
        生成交易信号
        
        Returns:
            {symbol: signal} 字典
        """
        signals = {}
        
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
        
        for symbol in self.symbols:
            df = load_stock_data(symbol, start_date, end_date, use_cache=True)
            if df is None or df.empty:
                continue
            
            df = df.copy()
            df['sma20'] = df['close'].rolling(20).mean()
            df['sma50'] = df['close'].rolling(50).mean()
            df['mom20'] = df['close'].pct_change(20) * 100
            
            latest = df.iloc[-1]
            
            close = latest['close']
            sma20 = latest['sma20']
            sma50 = latest['sma50']
            mom20 = latest['mom20']
            
            if pd.notna(sma20) and pd.notna(sma50) and pd.notna(mom20):
                if close > sma20 and close > sma50 and mom20 > 0:
                    signals[symbol] = 'buy'
                elif close < sma20:
                    signals[symbol] = 'sell'
        
        return signals
    
    def get_status(self) -> Dict[str, Any]:
        """
        获取运行状态
        
        Returns:
            状态信息
        """
        return {
            'strategy': self.strategy_name,
            'symbols': self.symbols,
            'mode': self.mode,
            'dry_run': self.dry_run,
            'strategy_loaded': self._strategy_class is not None,
            'broker_connected': self._client is not None and self._client.is_authenticated()
        }


def run_strategy(
    strategy_name: str,
    symbols: List[str] = None,
    mode: str = 'backtest',
    **kwargs
) -> Dict[str, Any]:
    """
    便捷函数：运行策略
    
    Args:
        strategy_name: 策略名称
        symbols: 交易标的 (默认7巨头)
        mode: 运行模式
        **kwargs: 其他参数
    
    Returns:
        运行结果
    """
    if symbols is None:
        symbols = ['AAPL', 'MSFT', 'AMZN', 'GOOGL', 'NVDA', 'META', 'TSLA']
    
    runner = StrategyRunner(strategy_name, symbols, mode)
    
    if mode == 'backtest':
        return runner.run_backtest(**kwargs)
    elif mode == 'live':
        return runner.run_live()
    else:
        return {'error': f'未知模式: {mode}'}
