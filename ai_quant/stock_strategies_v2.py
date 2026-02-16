"""针对不同股票特性的专属策略 - 趋势持有版"""
import backtrader as bt
import backtrader.indicators as btind


class NVDAStrategyV2(bt.Strategy):
    """英伟达专属策略 - 趋势持有版
    
    思路：2020年是单边上涨市，尽量持有更长时间
    只在趋势反转时卖出
    """

    params = (
        ('sma_short', 20),
        ('sma_long', 50),
        ('rsi_period', 14),
        ('bb_period', 20),
        ('bb_std', 2),
        ('stop_loss', 0.10),
        ('take_profit', 0.50),
    )

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.order = None
        self.buyprice = None

        self.sma_short = btind.SimpleMovingAverage(
            self.datas[0], period=self.params.sma_short)
        self.sma_long = btind.SimpleMovingAverage(
            self.datas[0], period=self.params.sma_long)

        self.rsi = btind.RSI(
            self.datas[0].close, period=self.params.rsi_period)

        self.bb = btind.BollingerBands(
            self.datas[0].close,
            period=self.params.bb_period,
            devfactor=self.params.bb_std
        )

        self.crossover_short = btind.CrossOver(
            self.sma_short, self.sma_long)
        self.crossover_long = btind.CrossOver(
            self.sma_long, self.sma_short)

    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        print(f'{dt.isoformat()}, {txt}')

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
        if order.status == order.Completed:
            if order.isbuy():
                self.buyprice = order.executed.price
                self.log(f'买入成交, 价格: {order.executed.price:.2f}')
            else:
                self.log(f'卖出成交, 价格: {order.executed.price:.2f}')
            self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        self.log(f'交易盈亏: {trade.pnlcomm:.2f}')

    def should_buy(self) -> tuple:
        close = self.dataclose[0]

        # 上涨趋势中买入
        if close < self.sma_short[0]:
            return False, "不在上涨趋势"

        if self.crossover_short > 0:
            return True, "均线金叉"

        if self.rsi[0] < 40:
            return True, "RSI回调到位"

        return False, ""

    def should_sell(self) -> tuple:
        if not self.position:
            return False, ""

        close = self.dataclose[0]
        entry = self.buyprice

        # 趋势反转才卖出
        if self.crossover_long > 0:
            return True, "均线死叉"

        # 止盈50%
        if entry and close > entry * (1 + self.params.take_profit):
            return True, "止盈50%"

        # 追踪止损：盈利回落到20%时卖出
        if entry and close > entry * 1.20:
            if close < entry * 1.20:
                return True, "追踪止损"

        # 止损10%
        if entry and close < entry * (1 - self.params.stop_loss):
            return True, "止损"

        return False, ""

    def next(self):
        if self.order:
            return

        if not self.position:
            should_buy, reason = self.should_buy()
            if should_buy:
                self.log(f'买入信号: {reason}')
                self.order = self.buy()
        else:
            should_sell, reason = self.should_sell()
            if should_sell:
                self.log(f'卖出信号: {reason}')
                self.order = self.sell()


class TSLAStrategyV2(bt.Strategy):
    """特斯拉专属策略 - 趋势持有版
    
    目标：跑赢720%的买入持有
    """

    params = (
        ('sma_short', 20),
        ('sma_long', 50),
        ('rsi_period', 14),
        ('bb_period', 20),
        ('bb_std', 2.5),
        ('stop_loss', 0.10),
        ('take_profit', 1.00),
    )

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.order = None
        self.buyprice = None

        self.sma_short = btind.SimpleMovingAverage(
            self.datas[0], period=self.params.sma_short)
        self.sma_long = btind.SimpleMovingAverage(
            self.datas[0], period=self.params.sma_long)

        self.rsi = btind.RSI(
            self.datas[0].close, period=self.params.rsi_period)

        self.bb = btind.BollingerBands(
            self.datas[0].close,
            period=self.params.bb_period,
            devfactor=self.params.bb_std
        )

        self.crossover_short = btind.CrossOver(
            self.sma_short, self.sma_long)
        self.crossover_long = btind.CrossOver(
            self.sma_long, self.sma_short)

    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        print(f'{dt.isoformat()}, {txt}')

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
        if order.status == order.Completed:
            if order.isbuy():
                self.buyprice = order.executed.price
                self.log(f'买入成交, 价格: {order.executed.price:.2f}')
            else:
                self.log(f'卖出成交, 价格: {order.executed.price:.2f}')
            self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        self.log(f'交易盈亏: {trade.pnlcomm:.2f}')

    def should_buy(self) -> tuple:
        close = self.dataclose[0]

        if close < self.sma_short[0]:
            return False, "不在上涨趋势"

        if self.crossover_short > 0:
            return True, "均线金叉"

        if self.rsi[0] < 40:
            return True, "RSI回调"

        return False, ""

    def should_sell(self) -> tuple:
        if not self.position:
            return False, ""

        close = self.dataclose[0]
        entry = self.buyprice

        if self.crossover_long > 0:
            return True, "均线死叉"

        # 止盈100%
        if entry and close > entry * (1 + self.params.take_profit):
            return True, "止盈100%"

        # 追踪止损
        if entry and close > entry * 1.50:
            if close < entry * 1.40:
                return True, "追踪止损"

        if entry and close < entry * (1 - self.params.stop_loss):
            return True, "止损"

        return False, ""

    def next(self):
        if self.order:
            return

        if not self.position:
            should_buy, reason = self.should_buy()
            if should_buy:
                self.log(f'买入信号: {reason}')
                self.order = self.buy()
        else:
            should_sell, reason = self.should_sell()
            if should_sell:
                self.log(f'卖出信号: {reason}')
                self.order = self.sell()


class AAPLStrategyV2(bt.Strategy):
    """苹果专属策略 - 趋势持有版
    
    目标：跑赢84%的买入持有
    """

    params = (
        ('sma_short', 20),
        ('sma_long', 50),
        ('rsi_period', 14),
        ('bb_period', 20),
        ('bb_std', 2),
        ('stop_loss', 0.08),
        ('take_profit', 0.60),
    )

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.order = None
        self.buyprice = None

        self.sma_short = btind.SimpleMovingAverage(
            self.datas[0], period=self.params.sma_short)
        self.sma_long = btind.SimpleMovingAverage(
            self.datas[0], period=self.params.sma_long)

        self.rsi = btind.RSI(
            self.datas[0].close, period=self.params.rsi_period)

        self.bb = btind.BollingerBands(
            self.datas[0].close,
            period=self.params.bb_period,
            devfactor=self.params.bb_std
        )

        self.crossover_short = btind.CrossOver(
            self.sma_short, self.sma_long)
        self.crossover_long = btind.CrossOver(
            self.sma_long, self.sma_short)

    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        print(f'{dt.isoformat()}, {txt}')

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
        if order.status == order.Completed:
            if order.isbuy():
                self.buyprice = order.executed.price
                self.log(f'买入成交, 价格: {order.executed.price:.2f}')
            else:
                self.log(f'卖出成交, 价格: {order.executed.price:.2f}')
            self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        self.log(f'交易盈亏: {trade.pnlcomm:.2f}')

    def should_buy(self) -> tuple:
        close = self.dataclose[0]

        if close < self.sma_short[0]:
            return False, "不在上涨趋势"

        if self.crossover_short > 0:
            return True, "均线金叉"

        if self.rsi[0] < 40:
            return True, "RSI回调"

        return False, ""

    def should_sell(self) -> tuple:
        if not self.position:
            return False, ""

        close = self.dataclose[0]
        entry = self.buyprice

        if self.crossover_long > 0:
            return True, "均线死叉"

        if entry and close > entry * (1 + self.params.take_profit):
            return True, "止盈60%"

        if entry and close > entry * 1.30:
            if close < entry * 1.25:
                return True, "追踪止损"

        if entry and close < entry * (1 - self.params.stop_loss):
            return True, "止损"

        return False, ""

    def next(self):
        if self.order:
            return

        if not self.position:
            should_buy, reason = self.should_buy()
            if should_buy:
                self.log(f'买入信号: {reason}')
                self.order = self.buy()
        else:
            should_sell, reason = self.should_sell()
            if should_sell:
                self.log(f'卖出信号: {reason}')
                self.order = self.sell()
