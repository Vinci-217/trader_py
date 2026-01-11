"""
网格交易回测模块
"""

import akshare as ak
import pandas as pd
import numpy as np
from datetime import datetime
from grid_strategy import GridStrategy


class GridBacktest:
    """
    网格交易回测类
    """
    
    def __init__(self, symbol, start_date, end_date, upper_price, lower_price, 
                 grid_count, position_per_grid, initial_capital=100000, fee_rate=0.001):
        """
        初始化回测参数
        
        :param symbol: 交易标的代码
        :param start_date: 回测开始日期 (YYYY-MM-DD)
        :param end_date: 回测结束日期 (YYYY-MM-DD)
        :param upper_price: 网格上轨价格
        :param lower_price: 网格下轨价格
        :param grid_count: 网格数量
        :param position_per_grid: 每格持仓量
        :param initial_capital: 初始资金
        :param fee_rate: 手续费率
        """
        self.symbol = symbol
        self.start_date = start_date
        self.end_date = end_date
        self.upper_price = upper_price
        self.lower_price = lower_price
        self.grid_count = grid_count
        self.position_per_grid = position_per_grid
        self.initial_capital = initial_capital
        self.fee_rate = fee_rate
        
        # 获取历史数据
        self.data = self._get_historical_data()
        
        # 初始化账户信息
        self.cash = initial_capital
        self.position = 0
        self.total_value = initial_capital
        self.trade_log = []
        
        # 计算网格参数
        self.grid_step = (upper_price - lower_price) / grid_count
        self.grid_prices = []
        for i in range(grid_count + 1):
            price = lower_price + i * self.grid_step
            self.grid_prices.append(round(price, 3))
    
    def _get_historical_data(self):
        """
        获取历史数据
        """
        try:
            # 获取ETF历史数据
            data = ak.fund_etf_hist_sina(symbol=self.symbol)
            data['日期'] = pd.to_datetime(data['日期'])
            mask = (data['日期'] >= self.start_date) & (data['日期'] <= self.end_date)
            filtered_data = data.loc[mask].copy()
            return filtered_data
        except Exception as e:
            print(f"获取历史数据失败: {e}")
            return pd.DataFrame()
    
    def _execute_buy(self, price, quantity, date):
        """
        执行买入操作
        """
        cost = price * quantity * (1 + self.fee_rate)
        if self.cash >= cost:
            self.cash -= cost
            self.position += quantity
            self.total_value = self.cash + self.position * price
            
            trade_record = {
                'date': date,
                'action': 'BUY',
                'price': price,
                'quantity': quantity,
                'amount': round(cost, 2),
                'cash': round(self.cash, 2),
                'position': self.position,
                'total_value': round(self.total_value, 2)
            }
            
            self.trade_log.append(trade_record)
            print(f"回测买入: 价格={price}, 数量={quantity}, 成本={cost:.2f}")
            return True
        return False
    
    def _execute_sell(self, price, quantity, date):
        """
        执行卖出操作
        """
        if self.position >= quantity:
            revenue = price * quantity * (1 - self.fee_rate)
            self.cash += revenue
            self.position -= quantity
            self.total_value = self.cash + self.position * price
            
            trade_record = {
                'date': date,
                'action': 'SELL',
                'price': price,
                'quantity': quantity,
                'amount': round(revenue, 2),
                'cash': round(self.cash, 2),
                'position': self.position,
                'total_value': round(self.total_value, 2)
            }
            
            self.trade_log.append(trade_record)
            print(f"回测卖出: 价格={price}, 数量={quantity}, 收入={revenue:.2f}")
            return True
        return False
    
    def _find_nearest_grid_level(self, current_price):
        """
        找到最接近当前价格的网格层级
        """
        min_diff = float('inf')
        nearest_price = self.grid_prices[0]
        nearest_idx = 0
        
        for idx, grid_price in enumerate(self.grid_prices):
            diff = abs(current_price - grid_price)
            if diff < min_diff:
                min_diff = diff
                nearest_price = grid_price
                nearest_idx = idx
                
        return nearest_price, nearest_idx
    
    def _execute_trading_logic(self, current_price, date):
        """
        执行网格交易逻辑
        """
        if current_price is None:
            return False
            
        nearest_price, current_level = self._find_nearest_grid_level(current_price)
        
        # 计算价格变化方向
        price_diff = current_price - nearest_price
        
        # 如果价格偏离网格点超过半个网格步长，则触发交易
        if abs(price_diff) > self.grid_step / 2:
            if price_diff > 0:  # 价格高于网格点，执行卖出
                if self.position >= self.position_per_grid:
                    self._execute_sell(nearest_price, self.position_per_grid, date)
            else:  # 价格低于网格点，执行买入
                cost = nearest_price * self.position_per_grid * (1 + self.fee_rate)
                if self.cash >= cost:
                    self._execute_buy(nearest_price, self.position_per_grid, date)
    
    def run_backtest(self):
        """
        运行回测
        """
        if self.data.empty:
            print("没有历史数据，无法进行回测")
            return
        
        print(f"开始回测 {self.symbol} 从 {self.start_date} 到 {self.end_date}")
        print(f"网格范围: {self.lower_price:.3f} - {self.upper_price:.3f}")
        print(f"网格数量: {self.grid_count}")
        print(f"每格仓位: {self.position_per_grid}")
        
        for idx, row in self.data.iterrows():
            current_price = row['收盘']
            date = row['日期']
            
            # 执行交易逻辑
            self._execute_trading_logic(current_price, date)
            
            # 更新总资产
            self.total_value = self.cash + self.position * current_price
        
        print(f"回测完成! 总交易次数: {len(self.trade_log)}")
    
    def get_performance_metrics(self):
        """
        获取回测绩效指标
        """
        if not self.trade_log:
            print("没有交易记录，无法计算绩效指标")
            return {}
        
        final_value = self.cash + self.position * self.data.iloc[-1]['收盘'] if not self.data.empty else self.initial_capital
        total_return = (final_value - self.initial_capital) / self.initial_capital
        total_profit = final_value - self.initial_capital
        
        buy_count = len([t for t in self.trade_log if t['action'] == 'BUY'])
        sell_count = len([t for t in self.trade_log if t['action'] == 'SELL'])
        
        metrics = {
            '回测期间': f"{self.start_date} 至 {self.end_date}",
            '初始资金': f"{self.initial_capital:.2f}",
            '最终资金': f"{self.cash:.2f}",
            '最终持仓': self.position,
            '最终总资产': f"{final_value:.2f}",
            '总盈亏': f"{total_profit:.2f}",
            '总收益率': f"{total_return * 100:.2f}%",
            '买入次数': buy_count,
            '卖出次数': sell_count
        }
        
        return metrics
    
    def print_report(self):
        """
        打印回测报告
        """
        print("\n" + "="*50)
        print("网格交易回测报告".center(40))
        print("="*50)
        print(f"交易标的: {self.symbol}")
        
        metrics = self.get_performance_metrics()
        for key, value in metrics.items():
            print(f"{key}: {value}")
        
        if self.trade_log:
            print(f"\n最近10笔交易记录:")
            recent_trades = self.trade_log[-10:]
            df = pd.DataFrame(recent_trades)
            if 'date' in df.columns and 'price' in df.columns:
                print(df[['date', 'action', 'price', 'quantity', 'amount', 'total_value']].to_string(index=False))
        
        print("="*50)