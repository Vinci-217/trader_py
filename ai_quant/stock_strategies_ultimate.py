"""终极优化策略 - 大止盈小止损"""
import backtrader as bt
import backtrader.indicators as btind


class UltimateStrategy(bt.Strategy):
    """终极优化策略
    
    核心改进：
    - 更大止盈 (25%)
    - 更小止损 (3%)
    - 更高买入评分门槛 (6分)
    - RSI超买才卖出
    """

    params = (
        ('sma_short', 15),
        ('sma_long', 40),
        ('rsi_period', 12),
        ('stop_loss', 0.03),
        ('take_profit', 0.25),
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

        self.macd = btind.MACD(
            self.datas[0].close,
            period_me1=12,
            period_me2=26,
            period_signal=9
        )

        self.crossover = btind.CrossOver(
            self.sma_short, self.sma_long)

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

    def calculate_score(self) -> float:
        score = 0
        close = self.dataclose[0]

        # 趋势
        if close > self.sma_long[0]:
            score += 3
        if self.sma_short[0] > self.sma_long[0]:
            score += 2

        if self.crossover > 0:
            score += 3
        if self.crossover < 0:
            score -= 3

        # RSI
        rsi = self.rsi[0]
        if rsi < 30:
            score += 3
        elif rsi < 45:
            score += 1
        elif rsi > 70:
            score -= 2

        # MACD
        if self.macd.lines.macd[0] > self.macd.lines.signal[0]:
            score += 2

        return score

    def should_buy(self) -> tuple:
        score = self.calculate_score()
        if score >= 6:  # 提高门槛
            return True, f"评分{score}"
        return False, ""

    def should_sell(self) -> tuple:
        if not self.position:
            return False, ""

        close = self.dataclose[0]
        entry = self.buyprice
        score = self.calculate_score()

        # 评分过低
        if score < -5:
            return True, f"评分过低{score}"

        # 止盈25%
        if entry and close > entry * (1 + self.params.take_profit):
            return True, "止盈25%"

        # 止损3%
        if entry and close < entry * (1 - self.params.stop_loss):
            return True, "止损"

        # RSI超买
        if self.rsi[0] > 75:
            return True, "RSI超买"

        # 均线死叉
        if self.crossover < 0:
            return True, "均线死叉"

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


class NVDA_Ultimate(UltimateStrategy):
    params = (
        ('sma_short', 12),
        ('sma_long', 35),
        ('rsi_period', 10),
        ('stop_loss', 0.025),
        ('take_profit', 0.25),
    )


class TSLA_Ultimate(UltimateStrategy):
    params = (
        ('sma_short', 10),
        ('sma_long', 30),
        ('rsi_period', 10),
        ('stop_loss', 0.025),
        ('take_profit', 0.20),
    )


class AAPL_Ultimate(UltimateStrategy):
    params = (
        ('sma_short', 15),
        ('sma_long', 45),
        ('rsi_period', 14),
        ('stop_loss', 0.03),
        ('take_profit', 0.20),
    )


class MSFT_Ultimate(UltimateStrategy):
    pass


class AMZN_Ultimate(UltimateStrategy):
    params = (
        ('sma_short', 12),
        ('sma_long', 40),
        ('rsi_period', 10),
        ('stop_loss', 0.025),
        ('take_profit', 0.22),
    )


class GOOGL_Ultimate(UltimateStrategy):
    params = (
        ('sma_short', 12),
        ('sma_long', 35),
        ('rsi_period', 10),
        ('stop_loss', 0.025),
        ('take_profit', 0.25),
    )


class META_Ultimate(UltimateStrategy):
    params = (
        ('sma_short', 10),
        ('sma_long', 30),
        ('rsi_period', 10),
        ('stop_loss', 0.025),
        ('take_profit', 0.25),
    )


class AMAT_Ultimate(UltimateStrategy):
    params = (
        ('sma_short', 12),
        ('sma_long', 35),
        ('rsi_period', 10),
        ('stop_loss', 0.03),
        ('take_profit', 0.20),
    )
