import backtrader as bt


# SMA均线策略类
class SMAStrategy(bt.Strategy):
    # 策略参数：可外部传入修改均线周期
    params = (
        ('maperiod', 15),
    )

    def next(self):
        self.log(f'收盘价: {self.dataclose[0]:.2f}, SMA({self.params.maperiod}): {self.sma[0]:.2f}')

        if self.order:
            self.log('当前有未完成的订单')
            return

        # 3. 核心策略逻辑：无持仓 → 判断买入；有持仓 → 判断卖出
        if not self.position:
            # 策略规则：【当期收盘价 上穿 SMA均线】 → 买入信号
            # 双重判断：前一期收盘价在均线下方，当期收盘价在均线上方 → 有效上穿，杜绝假突破
            self.log(
                f'当前无持仓，检查买入信号: 前期收盘价{self.dataclose[-1]:.2f}, 前期SMA{self.sma[-1]:.2f}, 当期收盘价{self.dataclose[0]:.2f}, 当期SMA{self.sma[0]:.2f}')
            if self.dataclose[-1] < self.sma[-1] and self.dataclose[0] > self.sma[0]:
                self.log(f'发出买入委托, 委托价: {self.dataclose[0]:.2f}')
                # 执行买入：默认全仓买入，也可以用 size=xxx 指定手数
                self.order = self.buy()
            else:
                self.log('未满足买入条件')

        # ========== 有持仓，满足条件则卖出 ==========
        else:
            # 策略规则：【当期收盘价 下穿 SMA均线】 → 卖出信号
            # 双重判断：前一期收盘价在均线上方，当期收盘价在均线下方 → 有效下穿
            self.log(
                f'当前有持仓，检查卖出信号: 前期收盘价{self.dataclose[-1]:.2f}, 前期SMA{self.sma[-1]:.2f}, 当期收盘价{self.dataclose[0]:.2f}, 当期SMA{self.sma[0]:.2f}')
            if self.dataclose[-1] > self.sma[-1] and self.dataclose[0] < self.sma[0]:
                self.log(f'发出卖出委托, 委托价: {self.dataclose[0]:.2f}')
                self.order = self.sell()
                self.log('已卖出平仓')
            else:
                self.log('不卖出')

    def __init__(self):
        # 保存数据源的收盘价序列
        self.dataclose = self.datas[0].close

        # 订单状态：记录是否有未成交订单，防止重复下单
        self.order = None
        # 成交价格/手续费 记录
        self.buyprice = None
        self.buycomm = None

        # 定义核心指标：SMA简单移动平均线
        self.sma = bt.indicators.SimpleMovingAverage(
            self.datas[0], period=self.params.maperiod)

        # 绘制辅助指标（用于图表展示，不影响策略逻辑）
        bt.indicators.ExponentialMovingAverage(self.datas[0], period=25)
        bt.indicators.WeightedMovingAverage(self.datas[0], period=25, subplot=True)
        bt.indicators.StochasticSlow(self.datas[0])
        bt.indicators.MACDHisto(self.datas[0])
        rsi = bt.indicators.RSI(self.datas[0])
        bt.indicators.SmoothedMovingAverage(rsi, period=10)
        bt.indicators.ATR(self.datas[0], plot=False)

    def log(self, txt, dt=None):
        # 取当期时间，默认用数据源的当期日期
        dt = dt or self.datas[0].datetime.date(0)
        # 格式：日期, 日志内容
        print(f'{dt.isoformat()}, {txt}')

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status == order.Completed:
            if order.isbuy():
                self.log(
                    f'买入成交, 成交价: {order.executed.price:.2f}, 成交金额: {order.executed.value:.2f}, 手续费: {order.executed.comm:.2f}'
                )
                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # 卖出成交
                self.log(
                    f'卖出成交, 成交价: {order.executed.price:.2f}, 成交金额: {order.executed.value:.2f}, 手续费: {order.executed.comm:.2f}'
                )
            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('订单状态：已撤销/保证金不足/被拒绝')
        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        self.log(f'本次交易盈亏, 毛利润: {trade.pnl:.2f}, 净利润: {trade.pnlcomm:.2f}')
