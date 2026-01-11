import matplotlib.pyplot as plt


def plot_data(cerebro, stock_code):
    # 设置中文字体以支持中文显示
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans', 'Arial Unicode MS']
    plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

    # 绘图，设置红涨绿跌样式
    cerebro.plot(
        style='candle',  # 使用蜡烛图样式
        title=f'{stock_code} K线图',  # 图表标题
        figsize=(15, 10),  # 图表大小
        barup='red',  # 上涨K线颜色（红色）
        bardown='black',  # 下跌K线颜色（绿色）
        grid=True,  # 显示网格
        numfigs=1,  # 图表数量
        plotvaluetags=True,  # 在图上显示价格标签
        plotlinelabels=True  # 显示线标签
    )
