"""
恒生指数ETF网格交易策略
"""

import akshare as ak
import pandas as pd
import numpy as np
import time
from datetime import datetime


class GridStrategy:
    """
    网格交易策略类
    """
    
    def __init__(self, symbol, upper_price, lower_price, grid_count, position_per_grid, initial_capital=100000, fee_rate=0.001):
        """
        初始化网格交易参数
        
        :param symbol: 交易标的代码
        :param upper_price: 网格上轨价格
        :param lower_price: 网格下轨价格
        :param grid_count: 网格数量
        :param position_per_grid: 每格持仓量
        :param initial_capital: 初始资金
        :param fee_rate: 手续费率
        """
        self.symbol = symbol
        self.upper_price = upper_price
        self.lower_price = lower_price
        self.grid_count = grid_count
        self.position_per_grid = position_per_grid
        self.initial_capital = initial_capital
        self.fee_rate = fee_rate
        
        # 计算网格间距
        self.grid_step = (upper_price - lower_price) / grid_count
        
        # 初始化账户信息
        self.cash = initial_capital
        self.position = 0   # 当前持仓数量
        self.total_value = self.cash  # 总资产
        self.trade_log = []  # 交易日志
        
        # 创建网格价格点
        self.grid_prices = []
        for i in range(grid_count + 1):
            price = lower_price + i * self.grid_step
            self.grid_prices.append(round(price, 3))
    
    def get_current_price(self):
        """
        获取当前市场价格
        """
        try:
            # 获取ETF实时行情
            fund_etf_spot_em_df = ak.fund_etf_spot_em()
            current_data = fund_etf_spot_em_df[fund_etf_spot_em_df['代码'] == self.symbol]
            
            if current_data.empty:
                # 如果未找到ETF数据，尝试其他接口
                try:
                    fund_etf_hist_sina_df = ak.fund_etf_hist_sina(symbol=self.symbol)
                    current_price = fund_etf_hist_sina_df.iloc[-1]['close']
                    return current_price
                except:
                    return None
            else:
                current_price = float(current_data.iloc[0]['最新价'])
                return current_price
                
        except Exception as e:
            print(f"获取价格失败: {e}")
            return None
    
    def buy(self, price, quantity):
        """
        买入操作
        """
        cost = price * quantity * (1 + self.fee_rate)
        if self.cash >= cost:
            self.cash -= cost
            self.position += quantity
            self.total_value = self.cash + self.position * price
            
            trade_record = {
                'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'action': 'BUY',
                'price': price,
                'quantity': quantity,
                'total_cost': cost,
                'cash': self.cash,
                'position': self.position,
                'total_value': self.total_value
            }
            
            self.trade_log.append(trade_record)
            print(f"买入: 价格={price}, 数量={quantity}, 成本={cost:.2f}")
            return True
        else:
            print("资金不足，无法买入")
            return False
    
    def sell(self, price, quantity):
        """
        卖出操作
        """
        if self.position >= quantity:
            revenue = price * quantity * (1 - self.fee_rate)
            self.cash += revenue
            self.position -= quantity
            self.total_value = self.cash + self.position * price
            
            trade_record = {
                'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'action': 'SELL',
                'price': price,
                'quantity': quantity,
                'total_revenue': revenue,
                'cash': self.cash,
                'position': self.position,
                'total_value': self.total_value
            }
            
            self.trade_log.append(trade_record)
            print(f"卖出: 价格={price}, 数量={quantity}, 收入={revenue:.2f}")
            return True
        else:
            print("持仓不足，无法卖出")
            return False
    
    def execute_trading_logic(self, current_price):
        """
        执行网格交易逻辑
        """
        if current_price is None:
            return
            
        # 遍历网格价格，判断是否触发买卖信号
        for i, grid_price in enumerate(self.grid_prices):
            # 计算与网格价格的差距
            diff = abs(current_price - grid_price)
            
            # 如果价格触及网格点（考虑一定容错）
            if diff <= self.grid_step * 0.5:  # 使用一半网格步长作为触发阈值
                # 判断是上涨穿越还是下跌穿越
                if current_price > grid_price:
                    # 价格上涨穿越网格点，应卖出
                    if self.position >= self.position_per_grid:
                        self.sell(grid_price, self.position_per_grid)
                else:
                    # 价格下跌穿越网格点，应买入
                    if self.cash >= grid_price * self.position_per_grid * (1 + self.fee_rate):
                        self.buy(grid_price, self.position_per_grid)
                        
                # 只处理一个网格点的信号，避免重复交易
                break
    
    def run_strategy(self, duration_minutes=60, interval_seconds=10):
        """
        运行网格交易策略
        
        :param duration_minutes: 策略运行时长（分钟）
        :param interval_seconds: 数据获取间隔（秒）
        """
        start_time = time.time()
        end_time = start_time + duration_minutes * 60
        
        print(f"开始网格交易策略，预计运行 {duration_minutes} 分钟")
        print(f"交易标的: {self.symbol}")
        print(f"网格范围: {self.lower_price} - {self.upper_price}")
        print(f"网格数量: {self.grid_count}")
        print(f"每格仓位: {self.position_per_grid}")
        
        trade_count = 0
        last_price = None
        
        while time.time() < end_time:
            current_price = self.get_current_price()
            if current_price:
                # 仅当价格发生显著变化时才打印
                if last_price is None or abs(current_price - last_price) / last_price > 0.001:
                    print(f"当前价格: {current_price:.3f}")
                    last_price = current_price
                
                # 执行交易逻辑
                self.execute_trading_logic(current_price)
                
                # 更新总资产
                self.total_value = self.cash + self.position * current_price
                print(f"现金: {self.cash:.2f}, 持仓: {self.position}, 总资产: {self.total_value:.2f}")
            
            # 等待下次查询
            time.sleep(interval_seconds)
        
        print(f"策略运行结束，总交易次数: {len(self.trade_log)}")
    
    def get_performance_metrics(self):
        """
        获取策略绩效指标
        """
        if not self.trade_log:
            return {
                '总交易次数': 0,
                '买入次数': 0,
                '卖出次数': 0,
                '最终现金': self.cash,
                '最终持仓': self.position,
                '最终总资产': self.total_value,
                '盈亏': 0,
                '收益率': '0.00%'
            }
        
        buy_count = len([t for t in self.trade_log if t['action'] == 'BUY'])
        sell_count = len([t for t in self.trade_log if t['action'] == 'SELL'])
        profit = self.total_value - self.initial_capital
        return_rate = (profit / self.initial_capital) * 100 if self.initial_capital > 0 else 0
        
        return {
            '总交易次数': len(self.trade_log),
            '买入次数': buy_count,
            '卖出次数': sell_count,
            '最终现金': self.cash,
            '最终持仓': self.position,
            '最终总资产': self.total_value,
            '盈亏': profit,
            '收益率': f'{return_rate:.2f}%'
        }