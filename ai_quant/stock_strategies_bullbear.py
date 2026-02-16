"""智能牛熊判断策略 - 只做多，熊市空仓"""
import backtrader as bt
import backtrader.indicators as btind


class SmartBullBearStrategy(bt.Strategy):
    """智能牛熊策略
    
    思路：
    - 判断市场趋势：基于大盘均线和RSI
    - 熊市：空仓等待
    - 牛市：积极做多
    - 只做多，不做空
    """

    params = (
        ('sma_short', 15),
        ('sma_long', 50),
        ('rsi_period', 10),
        ('bb_period', 15),
        ('bb_std', 2),
        ('stop_loss', 0.05),
        ('take_profit', 0.12),
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
        """判断牛市：价格在长期均线上方"""
        return self.dataclose[0] > self.sma_long[0] and self.sma_short[0] > self.sma_long[0]

    def is_bear_market(self) -> bool:
        """判断熊市：价格在长期均线下方"""
        return self.dataclose[0] < self.sma_long[0] and self.sma_short[0] < self.sma_long[0]

    def should_buy(self) -> tuple:
        # 只在牛市买入
        if not self.is_bull_market():
            return False, "非牛市"

        close = self.dataclose[0]
        prev_close = self.dataclose[-1]

        # 多个买入条件
        if self.crossover_short > 0:
            return True, "均线金叉"

        if self.rsi[-1] < 35 and self.rsi[0] > 40:
            return True, "RSI回升"

        if close > self.bb.lines.bot[0] and prev_close <= self.bb.lines.bot[-1]:
            return True, "布林带下轨"

        return False, ""

    def should_sell(self) -> tuple:
        if not self.position:
            return False, ""

        close = self.dataclose[0]
        entry = self.buyprice

        # 趋势反转卖出
        if self.is_bear_market():
            return True, "熊市离场"

        if self.crossover_long > 0:
            return True, "均线死叉"

        if entry and close > entry * (1 + self.params.take_profit):
            return True, "止盈"

        if entry and close < entry * (1 - self.params.stop_loss):
            return True, "止损"

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


class NVDA_BullBear(SmartBullBearStrategy):
    """英伟达 - 高波动，高成长"""
    params = (
        ('sma_short', 15),
        ('sma_long', 45),
        ('rsi_period', 10),
        ('bb_period', 15),
        ('bb_std', 2),
        ('stop_loss', 0.06),
        ('take_profit', 0.15),
    )


class TSLA_BullBear(SmartBullBearStrategy):
    """特斯拉 - 极高波动"""
    params = (
        ('sma_short', 12),
        ('sma_long', 40),
        ('rsi_period', 10),
        ('bb_period', 12),
        ('bb_std', 2.5),
        ('stop_loss', 0.05),
        ('take_profit', 0.12),
    )


class AAPL_BullBear(SmartBullBearStrategy):
    """苹果 - 稳健"""
    params = (
        ('sma_short', 20),
        ('sma_long', 50),
        ('rsi_period', 14),
        ('bb_period', 20),
        ('bb_std', 2),
        ('stop_loss', 0.05),
        ('take_profit', 0.10),
    )


class MSFT_BullBear(SmartBullBearStrategy):
    """微软 - 稳健成长"""
    params = (
        ('sma_short', 15),
        ('sma_long', 45),
        ('rsi_period', 12),
        ('bb_period', 15),
        ('bb_std', 2),
        ('stop_loss', 0.05),
        ('take_profit', 0.12),
    )


class AMZN_BullBear(SmartBullBearStrategy):
    """亚马逊 - 高波动"""
    params = (
        ('sma_short', 12),
        ('sma_long', 40),
        ('rsi_period', 10),
        ('bb_period', 12),
        ('bb_std', 2.5),
        ('stop_loss', 0.05),
        ('take_profit', 0.12),
    )


class GOOGL_BullBear(SmartBullBearStrategy):
    """谷歌 - 稳健"""
    params = (
        ('sma_short', 15),
        ('sma_long', 45),
        ('rsi_period', 12),
        ('bb_period', 15),
        ('bb_std', 2),
        ('stop_loss', 0.05),
        ('take_profit', 0.12),
    )


class META_BullBear(SmartBullBearStrategy):
    """Meta - 高波动"""
    params = (
        ('sma_short', 12),
        ('sma_long', 40),
        ('rsi_period', 10),
        ('bb_period', 12),
        ('bb_std', 2.5),
        ('stop_loss', 0.05),
        ('take_profit', 0.12),
    )


class AMAT_BullBear(SmartBullBearStrategy):
    """应用材料 - 半导体周期股"""
    params = (
        ('sma_short', 15),
        ('sma_long', 45),
        ('rsi_period', 10),
        ('bb_period', 15),
        ('bb_std', 2),
        ('stop_loss', 0.06),
        ('take_profit', 0.12),
    )
