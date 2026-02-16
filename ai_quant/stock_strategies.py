"""针对不同股票特性的专属策略"""
import backtrader as bt
import backtrader.indicators as btind


class NVDAStrategy(bt.Strategy):
    """英伟达专属策略 - 稳健增长型
    
    特性分析：
    - 波动率中等，适合中长线
    - 上涨趋势强，回调后容易继续上涨
    - 需要更严格的止损控制
    
    策略：趋势确认 + 布林带回调买入
    - 止损4%
    - 止盈12%
    """

    params = (
        ('sma_short', 15),
        ('sma_long', 40),
        ('rsi_period', 14),
        ('bb_period', 20),
        ('bb_std', 2),
        ('stop_loss', 0.04),
        ('take_profit', 0.12),
    )

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.datavolume = self.datas[0].volume

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
        prev_close = self.dataclose[-1]

        # 布林带下轨反弹
        if (close > self.bb.lines.bot[0] and 
            prev_close <= self.bb.lines.bot[-1]):
            return True, "布林带下轨反弹"

        # 均线金叉
        if self.crossover_short > 0:
            return True, "均线金叉"

        # RSI从超卖回升
        if self.rsi[-1] < 35 and self.rsi[0] > 40:
            return True, "RSI回升"

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


class TSLAStrategy(bt.Strategy):
    """特斯拉专属策略 - 高波动型
    
    特性分析：
    - 波动率极高
    - 经常出现极端行情
    - 反弹后上涨空间大
    
    策略：超跌反弹 + 趋势确认
    - 止损3.5%
    - 止盈10%
    - 持仓不超过15天
    """

    params = (
        ('sma_short', 15),
        ('sma_long', 40),
        ('rsi_period', 14),
        ('bb_period', 20),
        ('bb_std', 2),
        ('stop_loss', 0.035),
        ('take_profit', 0.10),
        ('max_hold_days', 15),
    )

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.datavolume = self.datas[0].volume

        self.order = None
        self.buyprice = None
        self.buy_date = None

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

        self.volume_sma = btind.SimpleMovingAverage(
            self.datas[0].volume, period=20)

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
                self.buy_date = len(self)
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
        prev_close = self.dataclose[-1]

        # 布林带下轨反弹
        bb_lower = self.bb.lines.bot[0]
        if close > bb_lower and prev_close <= bb_lower:
            return True, "布林带下轨反弹"

        # RSI超卖回升
        if self.rsi[-1] < 30 and self.rsi[0] > 35:
            return True, "RSI超卖回升"

        # 均线金叉
        if self.crossover_short > 0:
            return True, "均线金叉"

        return False, ""

    def should_sell(self) -> tuple:
        if not self.position:
            return False, ""

        close = self.dataclose[0]
        entry = self.buyprice
        hold_days = len(self) - self.buy_date if self.buy_date else 0

        # 止盈
        if entry and close > entry * (1 + self.params.take_profit):
            return True, "止盈"

        # 止损
        if entry and close < entry * (1 - self.params.stop_loss):
            return True, "止损"

        # 持仓超时
        if hold_days > self.params.max_hold_days:
            return True, "持仓超时"

        # RSI超买
        if self.rsi[0] > 75:
            return True, "RSI超买"

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


class AAPLStrategy(bt.Strategy):
    """苹果专属策略 - 稳健型
    
    特性分析：
    - 波动率低，走势稳定
    - 趋势性强，一旦启动持续时间长
    - 可以承受稍大的回调
    
    策略：趋势跟踪 + 均线回踩买入
    - 只在上涨趋势中买入
    - 止损4%
    - 止盈12%
    - 等待回踩均线时买入
    """

    params = (
        ('sma_short', 20),
        ('sma_long', 50),
        ('rsi_period', 14),
        ('bb_period', 20),
        ('bb_std', 2),
        ('stop_loss', 0.02),
        ('take_profit', 0.15),
    )

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.datavolume = self.datas[0].volume

        self.order = None
        self.buyprice = None

        self.sma_short = btind.SimpleMovingAverage(
            self.datas[0], period=self.params.sma_short)
        self.sma_long = btind.SimpleMovingAverage(
            self.datas[0], period=self.params.sma_long)

        self.rsi = btind.RSI(
            self.datas[0].close, period=self.params.rsi_period)

        self.macd = btind.MACD(
            self.datas[0].close,
            period_me1=12,
            period_me2=26,
            period_signal=9
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
        prev_close = self.dataclose[-1]

        # 上涨趋势
        if close < self.sma_short[0]:
            return False, "不在上涨趋势"

        # MACD金叉
        if (self.macd.lines.macd[0] > self.macd.lines.signal[0] and
            self.macd.lines.macd[-1] <= self.macd.lines.signal[-1]):
            return True, "MACD金叉"

        # 均线金叉
        if self.crossover_short > 0:
            return True, "均线金叉"

        # 回踩均线后反弹
        if (close > self.sma_short[0] and 
            prev_close < self.sma_short[0]):
            return True, "回踩均线反弹"

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

        # 追踪止损：当盈利超过5%时，将止损点提高到成本价
        if entry and close > entry * 1.05:
            if close < entry * 1.02:  # 盈利回落到2%以内
                return True, "追踪止损"

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
