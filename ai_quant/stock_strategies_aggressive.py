"""激进型牛熊策略 - 争取每年30%+收益"""
import backtrader as bt
import backtrader.indicators as btind


class AggressiveBullBearStrategy(bt.Strategy):
    """激进型牛熊策略
    
    思路：
    - 简化趋势判断
    - 放宽买入条件，增加交易频率
    - 大止盈小止损
    - 只做多，熊市空仓
    """

    params = (
        ('sma_short', 10),
        ('sma_long', 30),
        ('rsi_period', 7),
        ('bb_period', 10),
        ('bb_std', 2),
        ('stop_loss', 0.04),
        ('take_profit', 0.20),
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

    def is_bull_market(self) -> bool:
        """简化判断：价格在均线上方"""
        return self.dataclose[0] > self.sma_short[0]

    def should_buy(self) -> tuple:
        if not self.is_bull_market():
            return False, "非牛市"

        close = self.dataclose[0]
        prev_close = self.dataclose[-1]

        # 多个买入信号
        if self.crossover_short > 0:
            return True, "均线金叉"

        if self.rsi[0] < 50:
            return True, "RSI低位"

        if close > self.bb.lines.bot[0] and prev_close <= self.bb.lines.bot[-1]:
            return True, "布林带下轨"

        return False, ""

    def should_sell(self) -> tuple:
        if not self.position:
            return False, ""

        close = self.dataclose[0]
        entry = self.buyprice

        # 止盈
        if entry and close > entry * (1 + self.params.take_profit):
            return True, "止盈20%"

        # 止损
        if entry and close < entry * (1 - self.params.stop_loss):
            return True, "止损"

        # 趋势反转
        if self.crossover_long > 0:
            return True, "均线死叉"

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


class NVDA_Aggressive(AggressiveBullBearStrategy):
    params = (
        ('sma_short', 10),
        ('sma_long', 25),
        ('rsi_period', 7),
        ('bb_period', 10),
        ('bb_std', 2),
        ('stop_loss', 0.035),
        ('take_profit', 0.18),
    )


class TSLA_Aggressive(AggressiveBullBearStrategy):
    params = (
        ('sma_short', 8),
        ('sma_long', 20),
        ('rsi_period', 7),
        ('bb_period', 8),
        ('bb_std', 2.5),
        ('stop_loss', 0.03),
        ('take_profit', 0.15),
    )


class AAPL_Aggressive(AggressiveBullBearStrategy):
    params = (
        ('sma_short', 12),
        ('sma_long', 30),
        ('rsi_period', 10),
        ('bb_period', 12),
        ('bb_std', 2),
        ('stop_loss', 0.035),
        ('take_profit', 0.15),
    )


class MSFT_Aggressive(AggressiveBullBearStrategy):
    params = (
        ('sma_short', 10),
        ('sma_long', 25),
        ('rsi_period', 7),
        ('bb_period', 10),
        ('bb_std', 2),
        ('stop_loss', 0.035),
        ('take_profit', 0.15),
    )


class AMZN_Aggressive(AggressiveBullBearStrategy):
    params = (
        ('sma_short', 10),
        ('sma_long', 25),
        ('rsi_period', 7),
        ('bb_period', 10),
        ('bb_std', 2.5),
        ('stop_loss', 0.035),
        ('take_profit', 0.15),
    )


class GOOGL_Aggressive(AggressiveBullBearStrategy):
    params = (
        ('sma_short', 10),
        ('sma_long', 25),
        ('rsi_period', 7),
        ('bb_period', 10),
        ('bb_std', 2),
        ('stop_loss', 0.035),
        ('take_profit', 0.15),
    )


class META_Aggressive(AggressiveBullBearStrategy):
    params = (
        ('sma_short', 10),
        ('sma_long', 25),
        ('rsi_period', 7),
        ('bb_period', 10),
        ('bb_std', 2.5),
        ('stop_loss', 0.03),
        ('take_profit', 0.18),
    )


class AMAT_Aggressive(AggressiveBullBearStrategy):
    params = (
        ('sma_short', 10),
        ('sma_long', 25),
        ('rsi_period', 7),
        ('bb_period', 10),
        ('bb_std', 2),
        ('stop_loss', 0.04),
        ('take_profit', 0.15),
    )
