"""灵活型多指标策略 - 适用于各种市场环境"""
import backtrader as bt
import backtrader.indicators as btind
from typing import Optional, Dict, Any


class FlexibleStrategy(bt.Strategy):
    """灵活型多指标策略 - 放宽条件，提高交易频率

    买入条件（满足任一即可）:
    1. MACD金叉 + 成交量放大
    2. 布林带下轨反弹
    3. SMA金叉
    4. RSI从超卖区域回升

    卖出条件（满足任一即可）:
    1. MACD死叉
    2. RSI超买 (>75)
    3. 触及止盈点 (+12%)
    4. 触及止损点 (-4%)
    """

    params = (
        ('sma_short', 15),
        ('sma_long', 40),
        ('rsi_period', 14),
        ('rsi_oversold', 30),
        ('rsi_overbought', 75),
        ('bb_period', 20),
        ('bb_std', 2),
        ('stop_loss', 0.04),
        ('take_profit', 0.12),
        ('volume_ratio', 1.2),
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

        self.macd = btind.MACD(
            self.datas[0].close,
            period_me1=12,
            period_me2=26,
            period_signal=9
        )

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

        if self.rsi[0] > 70:
            return False, "RSI已超买"

        vol_ok = self.datavolume[0] > self.volume_sma[0] * self.params.volume_ratio

        macd_cross = (self.macd.lines.macd[0] > self.macd.lines.signal[0] and
                      self.macd.lines.macd[-1] <= self.macd.lines.signal[-1])

        if macd_cross and vol_ok:
            return True, "MACD金叉+放量"

        bb_bounce = (close > self.bb.lines.bot[0] and
                     prev_close <= self.bb.lines.bot[-1])

        if bb_bounce:
            return True, "布林带下轨反弹"

        if self.crossover_short > 0 and vol_ok:
            return True, "SMA金叉+放量"

        if self.rsi[-1] < self.params.rsi_oversold and self.rsi[0] > self.params.rsi_oversold + 5:
            return True, "RSI超卖回升"

        return False, ""

    def should_sell(self) -> tuple:
        if not self.position:
            return False, ""

        close = self.dataclose[0]
        entry_price = self.buyprice

        if self.crossover_long > 0:
            return True, "SMA死叉"

        if self.rsi[0] > self.params.rsi_overbought:
            return True, "RSI超买"

        if entry_price and close > entry_price * (1 + self.params.take_profit):
            return True, "触及止盈点"

        if entry_price and close < entry_price * (1 - self.params.stop_loss):
            return True, "触及止损点"

        macd_death = (self.macd.lines.macd[0] < self.macd.lines.signal[0] and
                      self.macd.lines.macd[-1] >= self.macd.lines.signal[-1])

        if macd_death:
            return True, "MACD死叉"

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
