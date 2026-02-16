"""针对不同股票特性的专属策略 - 做空高频版"""
import backtrader as bt
import backtrader.indicators as btind


class NVDAStrategyV3(bt.Strategy):
    """英伟达专属策略 - 做空高频版
    
    目标：每年30%+收益，回撤<10%
    方法：增加交易频率 + 双向交易（做多做空）
    """

    params = (
        ('sma_short', 10),
        ('sma_long', 25),
        ('rsi_period', 7),
        ('bb_period', 10),
        ('bb_std', 2),
        ('stop_loss', 0.03),
        ('take_profit', 0.05),
    )

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.order = None
        self.buyprice = None
        self.sellprice = None

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

        self.macd = btind.MACD(
            self.datas[0].close,
            period_me1=6,
            period_me2=13,
            period_signal=5
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
            elif order.issell():
                self.sellprice = order.executed.price
                self.log(f'做空成交, 价格: {order.executed.price:.2f}')
            else:
                self.log(f'卖出/平空成交, 价格: {order.executed.price:.2f}')
            self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        self.log(f'交易盈亏: {trade.pnlcomm:.2f}')

    def should_buy(self) -> tuple:
        close = self.dataclose[0]
        prev_close = self.dataclose[-1]

        # 上涨趋势
        if close > self.sma_short[0]:
            if self.crossover_short > 0:
                return True, "均线金叉"
            if self.rsi[-1] < 40 and self.rsi[0] > 45:
                return True, "RSI回升"
            if close > self.bb.lines.bot[0] and prev_close <= self.bb.lines.bot[-1]:
                return True, "布林带下轨"
            if self.macd.lines.macd[0] > self.macd.lines.signal[0]:
                if self.macd.lines.macd[-1] <= self.macd.lines.signal[-1]:
                    return True, "MACD金叉"

        return False, ""

    def should_sell(self) -> tuple:
        if not self.position:
            return False, ""

        close = self.dataclose[0]
        entry = self.buyprice

        if self.crossover_long > 0:
            return True, "均线死叉"

        if entry and close > entry * (1 + self.params.take_profit):
            return True, "止盈"

        if entry and close < entry * (1 - self.params.stop_loss):
            return True, "止损"

        if self.rsi[0] > 75:
            return True, "RSI超买"

        return False, ""

    def should_short(self) -> tuple:
        close = self.dataclose[0]
        prev_close = self.dataclose[-1]

        # 下跌趋势
        if close < self.sma_short[0]:
            if self.crossover_long > 0:
                return True, "均线死叉做空"
            if self.rsi[-1] > 60 and self.rsi[0] < 55:
                return True, "RSI回落做空"
            if close < self.bb.lines.top[0] and prev_close >= self.bb.lines.top[-1]:
                return True, "布林带上轨做空"
            if self.macd.lines.macd[0] < self.macd.lines.signal[0]:
                if self.macd.lines.macd[-1] >= self.macd.lines.signal[-1]:
                    return True, "MACD死叉做空"

        return False, ""

    def should_cover(self) -> tuple:
        if not self.position:
            return False, ""

        close = self.dataclose[0]
        entry = self.sellprice

        # 做空持仓
        if self.buyprice is None and self.sellprice is not None:
            if self.crossover_short > 0:
                return True, "均线金叉平空"

            if entry and close < entry * (1 - self.params.take_profit):
                return True, "做空止盈"

            if entry and close > entry * (1 + self.params.stop_loss):
                return True, "做空止损"

            if self.rsi[0] < 30:
                return True, "RSI超卖平空"

        return False, ""

    def next(self):
        if self.order:
            return

        # 有持仓时检查是否卖出/平空
        if self.position:
            if self.position.size > 0:  # 多头持仓
                should_sell, reason = self.should_sell()
                if should_sell:
                    self.log(f'卖出信号: {reason}')
                    self.order = self.sell()
            else:  # 空头持仓
                should_cover, reason = self.should_cover()
                if should_cover:
                    self.log(f'平空信号: {reason}')
                    self.order = self.buy()
        else:
            # 无持仓时检查是否买入或做空
            should_buy, reason = self.should_buy()
            if should_buy:
                self.log(f'买入信号: {reason}')
                self.order = self.buy()
                return

            should_short, reason = self.should_short()
            if should_short:
                self.log(f'做空信号: {reason}')
                self.order = self.sell()


class TSLAStrategyV3(bt.Strategy):
    """特斯拉专属策略 - 做空高频版
    
    高波动股票，更频繁的交易
    """

    params = (
        ('sma_short', 8),
        ('sma_long', 20),
        ('rsi_period', 7),
        ('bb_period', 10),
        ('bb_std', 2.5),
        ('stop_loss', 0.025),
        ('take_profit', 0.04),
    )

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.order = None
        self.buyprice = None
        self.sellprice = None

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
            elif order.issell():
                self.sellprice = order.executed.price
                self.log(f'做空成交, 价格: {order.executed.price:.2f}')
            else:
                self.log(f'卖出/平空成交, 价格: {order.executed.price:.2f}')
            self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        self.log(f'交易盈亏: {trade.pnlcomm:.2f}')

    def should_buy(self) -> tuple:
        close = self.dataclose[0]
        prev_close = self.dataclose[-1]

        if close > self.sma_short[0]:
            if self.crossover_short > 0:
                return True, "均线金叉"
            if self.rsi[0] < 45:
                return True, "RSI低位"
            if close > self.bb.lines.bot[0] and prev_close <= self.bb.lines.bot[-1]:
                return True, "布林带下轨"

        return False, ""

    def should_sell(self) -> tuple:
        if not self.position or self.position.size <= 0:
            return False, ""

        close = self.dataclose[0]
        entry = self.buyprice

        if self.crossover_long > 0:
            return True, "均线死叉"

        if entry and close > entry * (1 + self.params.take_profit):
            return True, "止盈"

        if entry and close < entry * (1 - self.params.stop_loss):
            return True, "止损"

        if self.rsi[0] > 70:
            return True, "RSI超买"

        return False, ""

    def should_short(self) -> tuple:
        close = self.dataclose[0]
        prev_close = self.dataclose[-1]

        if close < self.sma_short[0]:
            if self.crossover_long > 0:
                return True, "均线死叉做空"
            if self.rsi[0] > 55:
                return True, "RSI高位做空"
            if close < self.bb.lines.top[0] and prev_close >= self.bb.lines.top[-1]:
                return True, "布林带上轨做空"

        return False, ""

    def should_cover(self) -> tuple:
        if not self.position or self.position.size >= 0:
            return False, ""

        close = self.dataclose[0]
        entry = self.sellprice

        if self.crossover_short > 0:
            return True, "均线金叉平空"

        if entry and close < entry * (1 - self.params.take_profit):
            return True, "做空止盈"

        if entry and close > entry * (1 + self.params.stop_loss):
            return True, "做空止损"

        if self.rsi[0] < 35:
            return True, "RSI超卖平空"

        return False, ""

    def next(self):
        if self.order:
            return

        if self.position:
            if self.position.size > 0:
                should_sell, reason = self.should_sell()
                if should_sell:
                    self.log(f'卖出信号: {reason}')
                    self.order = self.sell()
            else:
                should_cover, reason = self.should_cover()
                if should_cover:
                    self.log(f'平空信号: {reason}')
                    self.order = self.buy()
        else:
            should_buy, reason = self.should_buy()
            if should_buy:
                self.log(f'买入信号: {reason}')
                self.order = self.buy()
                return

            should_short, reason = self.should_short()
            if should_short:
                self.log(f'做空信号: {reason}')
                self.order = self.sell()


class AAPLStrategyV3(bt.Strategy):
    """苹果专属策略 - 做空高频版"""

    params = (
        ('sma_short', 10),
        ('sma_long', 25),
        ('rsi_period', 7),
        ('bb_period', 10),
        ('bb_std', 2),
        ('stop_loss', 0.025),
        ('take_profit', 0.04),
    )

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.order = None
        self.buyprice = None
        self.sellprice = None

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
            elif order.issell():
                self.sellprice = order.executed.price
                self.log(f'做空成交, 价格: {order.executed.price:.2f}')
            else:
                self.log(f'卖出/平空成交, 价格: {order.executed.price:.2f}')
            self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        self.log(f'交易盈亏: {trade.pnlcomm:.2f}')

    def should_buy(self) -> tuple:
        close = self.dataclose[0]
        prev_close = self.dataclose[-1]

        if close > self.sma_short[0]:
            if self.crossover_short > 0:
                return True, "均线金叉"
            if self.rsi[-1] < 40 and self.rsi[0] > 45:
                return True, "RSI回升"
            if close > self.bb.lines.bot[0] and prev_close <= self.bb.lines.bot[-1]:
                return True, "布林带下轨"

        return False, ""

    def should_sell(self) -> tuple:
        if not self.position or self.position.size <= 0:
            return False, ""

        close = self.dataclose[0]
        entry = self.buyprice

        if self.crossover_long > 0:
            return True, "均线死叉"

        if entry and close > entry * (1 + self.params.take_profit):
            return True, "止盈"

        if entry and close < entry * (1 - self.params.stop_loss):
            return True, "止损"

        if self.rsi[0] > 70:
            return True, "RSI超买"

        return False, ""

    def should_short(self) -> tuple:
        close = self.dataclose[0]
        prev_close = self.dataclose[-1]

        if close < self.sma_short[0]:
            if self.crossover_long > 0:
                return True, "均线死叉做空"
            if self.rsi[-1] > 60 and self.rsi[0] < 55:
                return True, "RSI回落做空"
            if close < self.bb.lines.top[0] and prev_close >= self.bb.lines.top[-1]:
                return True, "布林带上轨做空"

        return False, ""

    def should_cover(self) -> tuple:
        if not self.position or self.position.size >= 0:
            return False, ""

        close = self.dataclose[0]
        entry = self.sellprice

        if self.crossover_short > 0:
            return True, "均线金叉平空"

        if entry and close < entry * (1 - self.params.take_profit):
            return True, "做空止盈"

        if entry and close > entry * (1 + self.params.stop_loss):
            return True, "做空止损"

        if self.rsi[0] < 35:
            return True, "RSI超卖平空"

        return False, ""

    def next(self):
        if self.order:
            return

        if self.position:
            if self.position.size > 0:
                should_sell, reason = self.should_sell()
                if should_sell:
                    self.log(f'卖出信号: {reason}')
                    self.order = self.sell()
            else:
                should_cover, reason = self.should_cover()
                if should_cover:
                    self.log(f'平空信号: {reason}')
                    self.order = self.buy()
        else:
            should_buy, reason = self.should_buy()
            if should_buy:
                self.log(f'买入信号: {reason}')
                self.order = self.buy()
                return

            should_short, reason = self.should_short()
            if should_short:
                self.log(f'做空信号: {reason}')
                self.order = self.sell()
