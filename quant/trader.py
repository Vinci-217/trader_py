import backtrader as bt
import backtrader.sizers as sizers
import pandas as pd

# from plot import plot_data  # 暂时注释掉绘图功能以避免numpy兼容性问题
from data_get import get_zh_a_stock, get_hk_stock, get_us_stock
from quant.plot import plot_data
from quant.strategy.sma import SMAStrategy


def prepare_data(stock_code, start_date, end_date):
    df = get_us_stock(stock_code, start_date, end_date)

    # 重命名列以匹配 backtrader 期望的列名
    df.rename(columns={
        '日期': 'datetime',
        '开盘': 'open',
        '最高': 'high',
        '最低': 'low',
        '收盘': 'close',
        '成交量': 'volume'
    }, inplace=True)

    # 确保日期列为 datetime 类型
    df['datetime'] = pd.to_datetime(df['datetime'])
    df.set_index('datetime', inplace=True)

    # 确保数值列是正确的数据类型
    df['open'] = pd.to_numeric(df['open'], errors='coerce')
    df['high'] = pd.to_numeric(df['high'], errors='coerce')
    df['low'] = pd.to_numeric(df['low'], errors='coerce')
    df['close'] = pd.to_numeric(df['close'], errors='coerce')
    df['volume'] = pd.to_numeric(df['volume'], errors='coerce')

    # 创建 PandasData 对象并传入数据
    data = bt.feeds.PandasData(
        dataname=df,
        datetime=None,  # 使用索引作为 datetime
        open='open',  # open 列的名称
        high='high',  # high 列的名称
        low='low',  # low 列的名称
        close='close',  # close 列的名称
        volume='volume',  # volume 列的名称
        openinterest=-1  # 如果没有 openinterest 列，设为 -1
    )

    # 设置数据名称以便在绘图时显示
    data._name = f'{stock_code}股票数据'  # 设置股票名称用于绘图显示

    return data


if __name__ == '__main__':
    cerebro = bt.Cerebro()
    # 使用数据前处理函数
    data = prepare_data("105.MSFT", "20230101", "20240101")

    # 添加数据到 cerebro
    cerebro.adddata(data)
    cerebro.addstrategy(SMAStrategy)

    # 设置初始资金
    cerebro.broker.setcash(100000.0)
    # 设置佣金
    cerebro.broker.setcommission(commission=0)
    cerebro.addsizer(bt.sizers.PercentSizer, percents=90)  # 使用100%资金进行交易

    # 添加分析器
    cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')

    # 运行策略
    results = cerebro.run()

    # 输出分析器结果
    strat = results[0]
    print("\n=== 策略分析结果 ===")
    print("总收益率:", f"{strat.analyzers.returns.get_analysis()['rtot']:.4f}")
    print("夏普比率:", strat.analyzers.sharpe.get_analysis().get("sharperatio", "N/A"))
    print("最大回撤:", f"{strat.analyzers.drawdown.get_analysis()['max']['drawdown']:.2f}%")

    # 使用绘图函数
    plot_data(cerebro, "MSFT")  # 暂时注释掉绘图功能以避免numpy兼容性问题
