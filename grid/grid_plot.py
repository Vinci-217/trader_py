"""
网格交易绘图模块
"""

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np


def plot_grid_lines(base_price, upper_price, lower_price, grid_count):
    """
    绘制网格线图
    
    :param base_price: 基准价格
    :param upper_price: 上轨价格
    :param lower_price: 下轨价格
    :param grid_count: 网格数量
    """
    plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
    plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号
    
    grid_step = (upper_price - lower_price) / grid_count
    grid_prices = [lower_price + i * grid_step for i in range(grid_count + 1)]
    
    plt.figure(figsize=(10, 6))
    for i, price in enumerate(grid_prices):
        plt.axhline(y=price, color='blue', linestyle='-', alpha=0.3, linewidth=0.8)
        plt.text(0.5, price, f'{price:.3f}', fontsize=8, ha='center', va='bottom')
    
    plt.title(f'网格价格线 - {upper_price:.3f} ~ {lower_price:.3f}')
    plt.xlabel('网格编号')
    plt.ylabel('价格')
    plt.grid(True, alpha=0.3)
    plt.show()


def plot_grid_trading_results(strategy_instance):
    """
    绘制网格交易结果
    
    :param strategy_instance: 策略实例
    """
    plt.rcParams['font.sans-serif'] = ['SimHei']
    plt.rcParams['axes.unicode_minus'] = False
    
    if not strategy_instance.trade_log:
        print("没有交易记录，无法绘图")
        return
    
    # 准备数据
    df = pd.DataFrame(strategy_instance.trade_log)
    df['time'] = pd.to_datetime(df['time'])
    df = df.sort_values('time')
    
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 10))
    
    # 子图1：价格和交易点
    if 'price' in df.columns:
        buy_data = df[df['action'] == 'BUY']
        sell_data = df[df['action'] == 'SELL']
        
        if not buy_data.empty:
            ax1.scatter(buy_data['time'], buy_data['price'], 
                       c='red', label='买入', marker='^', s=100)
        if not sell_data.empty:
            ax1.scatter(sell_data['time'], sell_data['price'], 
                       c='green', label='卖出', marker='v', s=100)
        
        ax1.plot(df['time'], df['price'], 'b-', alpha=0.3, label='价格轨迹')
    
    # 绘制网格线
    for grid_price in strategy_instance.grid_prices[::2]:  # 每隔一条显示，避免太密
        ax1.axhline(y=grid_price, color='gray', linestyle='--', alpha=0.5)
    
    ax1.set_title(f'{strategy_instance.symbol} 网格交易 - 价格与交易点')
    ax1.set_ylabel('价格')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 子图2：总资产变化
    if 'total_value' in df.columns:
        ax2.plot(df['time'], df['total_value'], 'purple', linewidth=2, label='总资产')
        ax2.axhline(y=strategy_instance.initial_capital, color='red', linestyle='--', label='初始资金')
        ax2.set_title('总资产变化')
        ax2.set_ylabel('总资产 (元)')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
    
    # 子图3：持仓变化
    if 'position' in df.columns:
        ax3.plot(df['time'], df['position'], 'orange', linewidth=2, label='持仓数量')
        ax3.set_title('持仓变化')
        ax3.set_xlabel('时间')
        ax3.set_ylabel('持仓数量')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()


def plot_backtest_results(backtest_instance):
    """
    绘制回测结果
    
    :param backtest_instance: 回测实例
    """
    plt.rcParams['font.sans-serif'] = ['SimHei']
    plt.rcParams['axes.unicode_minus'] = False
    
    if not backtest_instance.trade_log:
        print("没有交易记录，无法绘图")
        return
    
    # 准备数据
    df = pd.DataFrame(backtest_instance.trade_log)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 10))
    
    # 子图1：交易点分布
    if 'price' in df.columns:
        buy_data = df[df['action'] == 'BUY']
        sell_data = df[df['action'] == 'SELL']
        
        if not buy_data.empty:
            ax1.scatter(buy_data['date'], buy_data['price'], 
                       c='red', label='买入', marker='^', s=100)
        if not sell_data.empty:
            ax1.scatter(sell_data['date'], sell_data['price'], 
                       c='green', label='卖出', marker='v', s=100)
    
    ax1.set_title(f'{backtest_instance.symbol} 回测交易 - 价格与交易点')
    ax1.set_ylabel('价格')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 子图2：总资产变化
    if 'total_value' in df.columns:
        ax2.plot(df['date'], df['total_value'], 'purple', linewidth=2, label='总资产')
        ax2.axhline(y=backtest_instance.initial_capital, color='red', linestyle='--', label='初始资金')
        ax2.set_title('回测总资产变化')
        ax2.set_ylabel('总资产 (元)')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
    
    # 子图3：持仓变化
    if 'position' in df.columns:
        ax3.plot(df['date'], df['position'], 'orange', linewidth=2, label='持仓数量')
        ax3.set_title('回测持仓变化')
        ax3.set_xlabel('时间')
        ax3.set_ylabel('持仓数量')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()