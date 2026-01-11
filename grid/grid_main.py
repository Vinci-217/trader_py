"""
网格交易主程序
"""

from grid_strategy import GridStrategy
from grid_plot import plot_grid_lines, plot_grid_trading_results
from grid_backtest import GridBacktest
import akshare as ak


def get_etf_list():
    """
    获取ETF列表
    """
    try:
        etf_list = ak.fund_etf_category_sina()
        hsi_related = etf_list[
            etf_list['名称'].str.contains('恒生|H股|国企', case=False, na=False)
        ]
        return hsi_related if not hsi_related.empty else etf_list.head(10)
    except:
        # 如果获取失败，返回一些常见的ETF代码
        return [
            {'代码': '510900', '名称': 'H股ETF'},
            {'代码': '159920', '名称': '恒生ETF'},
            {'代码': '513600', '名称': '恒生医疗'}
        ]


def run_live_trading():
    """
    运行实时网格交易
    """
    print("=== 实时网格交易 ===")
    
    # 显示ETF列表
    print("恒生相关ETF列表:")
    try:
        etf_list = get_etf_list()
        if hasattr(etf_list, 'iloc'):
            print(etf_list[['代码', '名称', '最新价', '涨跌幅']].head().to_string(index=False))
        else:
            for etf in etf_list[:5]:
                print(f"代码: {etf['代码']}, 名称: {etf['名称']}")
    except:
        print("510900 (H股ETF)")
        print("159920 (恒生ETF)")
        print("513600 (恒生医疗)")
    
    # 获取用户输入
    symbol = input("请输入ETF代码 (例如 510900): ").strip()
    if not symbol:
        symbol = "510900"
    
    current_price = None
    try:
        fund_etf_spot_em_df = ak.fund_etf_spot_em()
        stock_data = fund_etf_spot_em_df[fund_etf_spot_em_df['代码'] == symbol]
        if not stock_data.empty:
            current_price = float(stock_data.iloc[0]['最新价'])
    except:
        pass
    
    if current_price is None:
        print("无法获取实时价格，使用默认价格1.0")
        current_price = 1.0
    
    upper_percent = float(input(f"请输入网格上轨相对于当前价格的涨幅百分比 (默认3%, 当前价格{current_price:.3f}): ") or "3") / 100
    lower_percent = float(input(f"请输入网格下轨相对于当前价格的跌幅百分比 (默认3%): ") or "3") / 100
    
    upper_price = current_price * (1 + upper_percent)
    lower_price = current_price * (1 - lower_percent)
    
    grid_count = int(input("请输入网格数量 (默认10): ") or "10")
    position_per_grid = int(input("请输入每格持仓量 (默认100): ") or "100")
    
    print(f"\n网格参数设置:")
    print(f"  ETF代码: {symbol}")
    print(f"  当前价格: {current_price:.3f}")
    print(f"  网格范围: {lower_price:.3f} - {upper_price:.3f}")
    print(f"  网格数量: {grid_count}")
    print(f"  每格持仓: {position_per_grid}")
    
    # 显示网格线
    plot_grid_lines(current_price, upper_price, lower_price, grid_count)
    
    # 创建策略实例
    strategy = GridStrategy(
        symbol=symbol,
        upper_price=upper_price,
        lower_price=lower_price,
        grid_count=grid_count,
        position_per_grid=position_per_grid
    )
    
    print("\n开始实时网格交易，按 Ctrl+C 停止...")
    try:
        import time
        while True:
            current_price = strategy.get_current_price()
            if current_price:
                print(f"当前价格: {current_price:.3f}")
                strategy.execute_trading_logic(current_price)
                strategy.total_value = strategy.cash + strategy.position * current_price
                print(f"现金: {strategy.cash:.2f}, 持仓: {strategy.position}, 总资产: {strategy.total_value:.2f}")
            
            time.sleep(10)  # 每10秒检查一次
    except KeyboardInterrupt:
        print("\n停止实时交易")
        
        # 显示交易结果
        metrics = strategy.get_performance_metrics()
        print(f"\n交易结果:")
        for key, value in metrics.items():
            print(f"{key}: {value}")
        
        # 绘制交易结果
        plot_grid_trading_results(strategy)


def run_backtest():
    """
    运行回测
    """
    print("=== 网格交易回测 ===")
    
    # 显示ETF列表
    print("恒生相关ETF列表:")
    try:
        etf_list = get_etf_list()
        if hasattr(etf_list, 'iloc'):
            print(etf_list[['代码', '名称', '最新价', '涨跌幅']].head().to_string(index=False))
        else:
            for etf in etf_list[:5]:
                print(f"代码: {etf['代码']}, 名称: {etf['名称']}")
    except:
        print("510900 (H股ETF)")
        print("159920 (恒生ETF)")
        print("513600 (恒生医疗)")
    
    # 获取用户输入
    symbol = input("请输入ETF代码 (例如 510900): ").strip()
    if not symbol:
        symbol = "510900"
    
    start_date = input("请输入回测开始日期 (YYYY-MM-DD, 默认30天前): ").strip()
    if not start_date:
        from datetime import datetime, timedelta
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    
    end_date = input("请输入回测结束日期 (YYYY-MM-DD, 默认今天): ").strip()
    if not end_date:
        from datetime import datetime
        end_date = datetime.now().strftime('%Y-%m-%d')
    
    current_price = None
    try:
        fund_etf_hist_sina_df = ak.fund_etf_hist_sina(symbol=symbol)
        current_price = float(fund_etf_hist_sina_df.iloc[-1]['收盘'])
    except:
        pass
    
    if current_price is None:
        print("无法获取价格，使用默认价格1.0")
        current_price = 1.0
    
    upper_percent = float(input(f"请输入网格上轨相对于当前价格的涨幅百分比 (默认3%): ") or "3") / 100
    lower_percent = float(input(f"请输入网格下轨相对于当前价格的跌幅百分比 (默认3%): ") or "3") / 100
    
    upper_price = current_price * (1 + upper_percent)
    lower_price = current_price * (1 - lower_percent)
    
    grid_count = int(input("请输入网格数量 (默认10): ") or "10")
    position_per_grid = int(input("请输入每格持仓量 (默认100): ") or "100")
    initial_capital = float(input("请输入初始资金 (默认100000): ") or "100000")
    
    print(f"\n回测参数设置:")
    print(f"  ETF代码: {symbol}")
    print(f"  回测期间: {start_date} - {end_date}")
    print(f"  网格范围: {lower_price:.3f} - {upper_price:.3f}")
    print(f"  网格数量: {grid_count}")
    print(f"  每格持仓: {position_per_grid}")
    print(f"  初始资金: {initial_capital}")
    
    # 创建回测实例
    backtest = GridBacktest(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        upper_price=upper_price,
        lower_price=lower_price,
        grid_count=grid_count,
        position_per_grid=position_per_grid,
        initial_capital=initial_capital
    )
    
    # 运行回测
    backtest.run_backtest()
    
    # 打印报告
    backtest.print_report()
    
    # 绘制结果
    from grid_plot import plot_backtest_results
    plot_backtest_results(backtest)


def main():
    """
    主函数
    """
    print("恒生指数ETF网格交易系统")
    print("="*40)
    
    while True:
        print("\n请选择功能:")
        print("1. 实时网格交易")
        print("2. 历史数据回测")
        print("3. 退出")
        
        choice = input("请输入选择 (1-3): ").strip()
        
        if choice == '1':
            run_live_trading()
        elif choice == '2':
            run_backtest()
        elif choice == '3':
            print("退出系统")
            break
        else:
            print("无效选择，请重新输入")


if __name__ == "__main__":
    main()