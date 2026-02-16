"""优化后的保守型多指标策略 - 可用于回测"""
import backtrader as bt
import backtrader.indicators as btind
from typing import Optional, Dict, Any


class ConservativeStrategy(bt.Strategy):
    """保守型多指标策略 - 减少回撤

    改进点：
    1. 增加趋势过滤 - 只在上涨趋势中买入
    2. 收紧止损到3%
    3. 放宽止盈到15%
    4. 增加更多确认条件，避免假信号
    5. 增加持仓时间限制

    买入条件（必须全部满足）:
    1. 价格处于上涨趋势（收盘价 > 50日均线）
    2. RSI在合理区间（30-60）
    3. MACD金叉或布林带下轨反弹
    4. 成交量放大确认

    卖出条件（满足任一即可）:
    1. SMA死叉
    2. RSI超买 (>75)
    3. 触及止盈点 (+15%)
    4. 触及止损点 (-3%)
    5. 持仓超过20天且RSI高于65
    6. 跌破20日均线
    """

    params = (
        ('sma_short', 20),       # 短期均线周期
        ('sma_long', 50),        # 长期均线周期
        ('rsi_period', 14),      # RSI周期
        ('rsi_oversold', 30),    # RSI超卖阈值
        ('rsi_overbought', 75),  # RSI超买阈值 (提高)
        ('rsi_safe_zone', 60),   # RSI安全买入区间上限
        ('bb_period', 20),       # 布林带周期
        ('bb_std', 2),           # 布林带标准差倍数
        ('stop_loss', 0.03),     # 止损比例 (收紧到3%)
        ('take_profit', 0.15),   # 止盈比例 (提高到15%)
        ('volume_ratio', 1.3),   # 成交量放大倍数
        ('max_hold_days', 20),   # 最大持仓天数
    )

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.dataopen = self.datas[0].open
        self.datahigh = self.datas[0].high
        self.datalow = self.datas[0].low
        self.datavolume = self.datas[0].volume

        self.order = None
        self.buyprice = None
        self.buycomm = None
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
                self.log(f'买入成交, 价格: {order.executed.price:.2f}')
                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
                self.buy_date = len(self)
            else:
                self.log(f'卖出成交, 价格: {order.executed.price:.2f}')
            self.bar_executed = len(self)
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('订单失败')
        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        self.log(f'交易盈亏: {trade.pnlcomm:.2f}')

    def is_uptrend(self) -> bool:
        """判断是否处于上涨趋势"""
        return self.dataclose[0] > self.sma_long[0]

    def should_buy(self) -> tuple:
        """判断是否应该买入（所有条件必须满足）"""
        close = self.dataclose[0]
        prev_close = self.dataclose[-1]

        if not self.is_uptrend():
            return False, "下跌趋势"

        if self.rsi[0] > self.params.rsi_safe_zone:
            return False, "RSI过高"

        if self.datavolume[0] < self.volume_sma[0] * self.params.volume_ratio:
            return False, "成交量不足"

        # MACD金叉 + 站上短期均线
        macd_cross = (self.macd.lines.macd[0] > self.macd.lines.signal[0] and
                      self.macd.lines.macd[-1] <= self.macd.lines.signal[-1])
        price_above_short = close > self.sma_short[0]

        # 布林带下轨反弹
        bb_bounce = (close > self.bb.lines.bot[0] and
                     prev_close <= self.bb.lines.bot[-1])

        if macd_cross and price_above_short:
            return True, "MACD金叉+上涨趋势"

        if bb_bounce and self.rsi[0] < self.params.rsi_overbought:
            return True, "布林带下轨反弹+上涨趋势"

        if self.crossover_short > 0 and self.rsi[0] < self.params.rsi_safe_zone:
            return True, "SMA金叉+上涨趋势"

        return False, ""

    def should_sell(self) -> tuple:
        """判断是否应该卖出"""
        if not self.position:
            return False, ""

        close = self.dataclose[0]
        entry_price = self.buyprice
        hold_days = len(self) - self.buy_date if self.buy_date else 0

        if self.crossover_long > 0:
            return True, "SMA死叉"

        if self.rsi[0] > self.params.rsi_overbought:
            return True, "RSI超买"

        if entry_price and close > entry_price * (1 + self.params.take_profit):
            return True, "触及止盈点"

        if entry_price and close < entry_price * (1 - self.params.stop_loss):
            return True, "触及止损点"

        if hold_days > self.params.max_hold_days and self.rsi[0] > 65:
            return True, "持仓过久+RSI高"

        if close < self.sma_short[0] and hold_days > 5:
            return True, "跌破短期均线"

        return False, ""

    def next(self):
        if self.order:
            return

        if not self.position:
            should_buy, reason = self.should_buy()
            if should_buy:
                self.log(f'买入信号: {reason}, 价格: {self.dataclose[0]:.2f}')
                self.order = self.buy()
        else:
            should_sell, reason = self.should_sell()
            if should_sell:
                self.log(f'卖出信号: {reason}, 价格: {self.dataclose[0]:.2f}')
                self.order = self.sell()


class VeryConservativeStrategy(bt.Strategy):
    """极度保守型策略 - 最小化回撤

    特点：
    1. 只做确定性高的信号
    2. 2%止损
    3. 需要多个指标同时确认
    4. 更严格的趋势过滤
    """

    params = (
        ('sma_short', 20),
        ('sma_long', 60),
        ('rsi_period', 14),
        ('rsi_oversold', 25),
        ('rsi_overbought', 80),
        ('rsi_buy_max', 55),
        ('bb_period', 20),
        ('bb_std', 2),
        ('stop_loss', 0.02),
        ('take_profit', 0.20),
        ('volume_ratio', 1.5),
        ('max_hold_days', 30),
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

        if close < self.sma_long[0]:
            return False, "价格低于长期均线"

        if self.rsi[0] > self.params.rsi_buy_max:
            return False, "RSI过高"

        if self.rsi[0] < self.params.rsi_oversold:
            return False, "RSI超卖（可能还有更低）"

        if self.datavolume[0] < self.volume_sma[0] * self.params.volume_ratio:
            return False, "成交量不足"

        macd_gold = (self.macd.lines.macd[0] > self.macd.lines.signal[0] and
                     self.macd.lines.macd[-1] <= self.macd.lines.signal[-1])

        bb_touch = close <= self.bb.lines.bot[0] * 1.02

        if (macd_gold and close > self.sma_short[0] and
            self.crossover_short > 0 and
            close > self.sma_long[0]):
            return True, "MACD金叉+SMA金叉+趋势确认"

        if (bb_touch and close > self.sma_long[0] and
            self.rsi[0] > 35):
            return True, "布林带触及+趋势确认"

        return False, ""

    def should_sell(self) -> tuple:
        if not self.position:
            return False, ""

        close = self.dataclose[0]
        entry_price = self.buyprice
        hold_days = len(self) - self.buy_date if self.buy_date else 0

        if self.crossover_long > 0:
            return True, "SMA死叉"

        if self.rsi[0] > self.params.rsi_overbought:
            return True, "RSI超买"

        if entry_price and close > entry_price * (1 + self.params.take_profit):
            return True, "触及止盈点"

        if entry_price and close < entry_price * (1 - self.params.stop_loss):
            return True, "触及止损点"

        if hold_days > self.params.max_hold_days:
            return True, "持仓超时"

        if close < self.sma_long[0]:
            return True, "跌破长期均线"

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
