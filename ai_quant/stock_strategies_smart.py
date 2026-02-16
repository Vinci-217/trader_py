"""智能多空策略 - 根据市场环境自动切换"""
import backtrader as bt
import backtrader.indicators as btind


class SmartStrategy(bt.Strategy):
    """智能策略 - 只在明确趋势中交易
    
    思路：
    - 上涨趋势：只做多
    - 下跌趋势：只做空
    - 震荡市：减少交易
    - 更宽松的止盈止损
    """

    params = (
        ('sma_short', 15),
        ('sma_long', 40),
        ('rsi_period', 10),
        ('bb_period', 15),
        ('bb_std', 2),
        ('stop_loss', 0.05),
        ('take_profit', 0.10),
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
            elif order.issell():
                self.buyprice = None
                self.log(f'做空成交, 价格: {order.executed.price:.2f}')
            else:
                self.log(f'卖出/平空成交, 价格: {order.executed.price:.2f}')
            self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        self.log(f'交易盈亏: {trade.pnlcomm:.2f}')

    def is_uptrend(self) -> bool:
        """判断上涨趋势"""
        return self.dataclose[0] > self.sma_long[0] and self.sma_short[0] > self.sma_long[0]

    def is_downtrend(self) -> bool:
        """判断下跌趋势"""
        return self.dataclose[0] < self.sma_long[0] and self.sma_short[0] < self.sma_long[0]

    def should_buy(self) -> tuple:
        if not self.is_uptrend():
            return False, "不在上涨趋势"

        close = self.dataclose[0]
        prev_close = self.dataclose[-1]

        if self.crossover_short > 0:
            return True, "均线金叉"

        if self.rsi[-1] < 35 and self.rsi[0] > 40:
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

        if self.rsi[0] > 75:
            return True, "RSI超买"

        return False, ""

    def should_short(self) -> tuple:
        if not self.is_downtrend():
            return False, "不在下跌趋势"

        close = self.dataclose[0]
        prev_close = self.dataclose[-1]

        if self.crossover_long > 0:
            return True, "均线死叉做空"

        if self.rsi[-1] > 65 and self.rsi[0] < 60:
            return True, "RSI回落做空"

        if close < self.bb.lines.top[0] and prev_close >= self.bb.lines.top[-1]:
            return True, "布林带上轨做空"

        return False, ""

    def should_cover(self) -> tuple:
        if not self.position or self.position.size >= 0:
            return False, ""

        close = self.dataclose[0]
        entry = self.buyprice

        if self.is_uptrend():
            return True, "趋势转多平空"

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


class NVDA_Smart(SmartStrategy):
    pass


class TSLA_Smart(SmartStrategy):
    params = (
        ('sma_short', 12),
        ('sma_long', 30),
        ('rsi_period', 10),
        ('bb_period', 15),
        ('bb_std', 2.5),
        ('stop_loss', 0.04),
        ('take_profit', 0.08),
    )


class AAPL_Smart(SmartStrategy):
    pass
