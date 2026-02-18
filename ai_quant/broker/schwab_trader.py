"""
Schwab Trader
=============
将策略信号转换为Schwab交易指令
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Optional, Dict, List, Any, Callable
from enum import Enum

from .schwab_client import SchwabClient


class OrderSide(Enum):
    BUY = "buy"
    SELL = "sell"


class OrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"


class SchwabTrader:
    """
    Schwab交易执行器
    
    将策略信号转换为实际交易指令
    """
    
    def __init__(
        self,
        client: SchwabClient,
        account_hash: Optional[str] = None,
        dry_run: bool = True,
        position_size_pct: float = 0.95,
        max_positions: int = 5
    ):
        """
        初始化交易执行器
        
        Args:
            client: Schwab客户端实例
            account_hash: 账户哈希值
            dry_run: 是否模拟运行 (不实际下单)
            position_size_pct: 单只股票仓位比例
            max_positions: 最大持仓数量
        """
        self.client = client
        self.account_hash = account_hash
        self.dry_run = dry_run
        self.position_size_pct = position_size_pct
        self.max_positions = max_positions
        
        self._pending_orders = []
        self._executed_orders = []
        self._positions = {}
    
    def connect(self) -> bool:
        """
        连接到Schwab并获取账户信息
        
        Returns:
            是否连接成功
        """
        if not self.client.is_authenticated():
            print("错误: 客户端未认证，请先执行认证流程")
            return False
        
        accounts = self.client.get_account_info()
        if not accounts:
            print("错误: 无法获取账户信息")
            return False
        
        if self.account_hash is None:
            self.account_hash = accounts[0].get('hashValue')
        
        print(f"连接成功，账户: {self.account_hash[:8]}...")
        return True
    
    def sync_positions(self) -> Dict[str, Any]:
        """
        同步当前持仓
        
        Returns:
            持仓信息
        """
        positions = self.client.get_positions(self.account_hash)
        
        self._positions = {}
        for pos in positions:
            symbol = pos.get('instrument', {}).get('symbol', '')
            if symbol:
                self._positions[symbol] = {
                    'quantity': pos.get('longQuantity', 0),
                    'avg_price': pos.get('averagePrice', 0),
                    'market_value': pos.get('marketValue', 0),
                }
        
        return self._positions
    
    def get_account_balance(self) -> Dict[str, float]:
        """
        获取账户余额
        
        Returns:
            余额信息
        """
        positions = self.client.get_positions(self.account_hash)
        
        total_value = 0
        cash = 0
        
        for pos in positions:
            if pos.get('instrument', {}).get('assetType') == 'CASH':
                cash = pos.get('marketValue', 0)
            total_value += pos.get('marketValue', 0)
        
        return {
            'total_value': total_value,
            'cash': cash,
            'invested': total_value - cash
        }
    
    def calculate_position_size(self, symbol: str, price: float) -> int:
        """
        计算仓位大小
        
        Args:
            symbol: 股票代码
            price: 当前价格
        
        Returns:
            股票数量
        """
        balance = self.get_account_balance()
        available_cash = balance['total_value'] * self.position_size_pct
        
        position_value = available_cash / self.max_positions
        quantity = int(position_value / price)
        
        return max(1, quantity)
    
    def execute_signal(
        self,
        symbol: str,
        signal: str,
        quantity: Optional[int] = None,
        price: Optional[float] = None,
        order_type: str = 'market'
    ) -> Dict[str, Any]:
        """
        执行交易信号
        
        Args:
            symbol: 股票代码
            signal: 信号 ('buy', 'sell', 'close')
            quantity: 数量 (None则自动计算)
            price: 价格 (限价单需要)
            order_type: 订单类型
        
        Returns:
            执行结果
        """
        if self.dry_run:
            return self._dry_run_order(symbol, signal, quantity, price)
        
        if signal == 'buy':
            if quantity is None:
                current_price = price or self._get_current_price(symbol)
                if current_price is None:
                    return {'success': False, 'error': '无法获取价格'}
                quantity = self.calculate_position_size(symbol, current_price)
            
            return self.client.place_order(
                symbol=symbol,
                quantity=quantity,
                order_type=order_type,
                side='buy',
                price=price,
                account_hash=self.account_hash
            )
        
        elif signal == 'sell':
            if quantity is None:
                pos = self._positions.get(symbol, {})
                quantity = int(pos.get('quantity', 0))
            
            if quantity <= 0:
                return {'success': False, 'error': '没有持仓可卖'}
            
            return self.client.place_order(
                symbol=symbol,
                quantity=quantity,
                order_type=order_type,
                side='sell',
                price=price,
                account_hash=self.account_hash
            )
        
        elif signal == 'close':
            pos = self._positions.get(symbol, {})
            quantity = int(pos.get('quantity', 0))
            
            if quantity <= 0:
                return {'success': True, 'message': '没有持仓'}
            
            return self.client.place_order(
                symbol=symbol,
                quantity=quantity,
                order_type=order_type,
                side='sell',
                price=price,
                account_hash=self.account_hash
            )
        
        else:
            return {'success': False, 'error': f'未知信号: {signal}'}
    
    def _dry_run_order(
        self,
        symbol: str,
        signal: str,
        quantity: Optional[int],
        price: Optional[float]
    ) -> Dict[str, Any]:
        """
        模拟下单
        """
        current_price = price or self._get_current_price(symbol)
        
        if signal == 'buy' and quantity is None:
            quantity = self.calculate_position_size(symbol, current_price or 100)
        elif signal in ['sell', 'close']:
            pos = self._positions.get(symbol, {})
            quantity = quantity or int(pos.get('quantity', 0))
        
        order = {
            'success': True,
            'dry_run': True,
            'symbol': symbol,
            'signal': signal,
            'quantity': quantity,
            'price': current_price,
            'estimated_value': (quantity or 0) * (current_price or 0),
            'timestamp': datetime.now().isoformat()
        }
        
        self._pending_orders.append(order)
        print(f"[模拟] {signal.upper()} {quantity} 股 {symbol} @ ${current_price:.2f}")
        
        return order
    
    def _get_current_price(self, symbol: str) -> Optional[float]:
        """
        获取当前价格
        """
        quote = self.client.get_quote(symbol)
        if quote:
            return quote.get('quote', {}).get('lastPrice')
        return None
    
    def execute_strategy_signals(
        self,
        signals: Dict[str, str],
        prices: Optional[Dict[str, float]] = None
    ) -> List[Dict[str, Any]]:
        """
        批量执行策略信号
        
        Args:
            signals: {symbol: signal} 字典
            prices: {symbol: price} 字典 (可选)
        
        Returns:
            执行结果列表
        """
        results = []
        
        for symbol, signal in signals.items():
            price = prices.get(symbol) if prices else None
            result = self.execute_signal(symbol, signal, price=price)
            results.append({
                'symbol': symbol,
                'signal': signal,
                'result': result
            })
        
        return results
    
    def rebalance_portfolio(
        self,
        target_allocation: Dict[str, float],
        tolerance: float = 0.05
    ) -> List[Dict[str, Any]]:
        """
        重新平衡投资组合
        
        Args:
            target_allocation: 目标配置 {symbol: weight}
            tolerance: 容差比例
        
        Returns:
            交易结果列表
        """
        self.sync_positions()
        balance = self.get_account_balance()
        total_value = balance['total_value']
        
        results = []
        
        current_symbols = set(self._positions.keys())
        target_symbols = set(target_allocation.keys())
        
        for symbol in current_symbols - target_symbols:
            result = self.execute_signal(symbol, 'close')
            results.append({'symbol': symbol, 'action': 'close', 'result': result})
        
        for symbol, weight in target_allocation.items():
            target_value = total_value * weight
            current_value = self._positions.get(symbol, {}).get('market_value', 0)
            
            diff_ratio = abs(current_value - target_value) / total_value if total_value > 0 else 1
            
            if diff_ratio > tolerance:
                if current_value < target_value:
                    result = self.execute_signal(symbol, 'buy')
                    results.append({'symbol': symbol, 'action': 'buy', 'result': result})
                else:
                    result = self.execute_signal(symbol, 'sell')
                    results.append({'symbol': symbol, 'action': 'sell', 'result': result})
        
        return results
    
    def get_pending_orders(self) -> List[Dict[str, Any]]:
        """获取待执行订单"""
        return self._pending_orders
    
    def get_executed_orders(self) -> List[Dict[str, Any]]:
        """获取已执行订单"""
        return self._executed_orders
    
    def clear_pending_orders(self):
        """清空待执行订单"""
        self._pending_orders = []
    
    def get_trading_summary(self) -> Dict[str, Any]:
        """
        获取交易摘要
        
        Returns:
            交易摘要信息
        """
        return {
            'account_hash': self.account_hash,
            'dry_run': self.dry_run,
            'positions': self._positions,
            'pending_orders': len(self._pending_orders),
            'executed_orders': len(self._executed_orders),
            'max_positions': self.max_positions,
            'position_size_pct': self.position_size_pct
        }
