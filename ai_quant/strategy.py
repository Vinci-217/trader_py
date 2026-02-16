"""多指标综合策略 - 可用于回测"""
import backtrader as bt
import backtrader.indicators as btind
from typing import Optional, Dict, Any


class MultiIndicatorStrategy(bt.Strategy):
    """多指标综合策略

    买入条件（满足任一即可）:
    1. SMA金叉 + RSI超卖 + 成交量放大
    2. 布林带下轨反弹 + RSI未超买
    3. MACD金叉 + 站上20日均线

    卖出条件（满足任一即可）:
    1. SMA死叉
    2. RSI超买 (>70)
    3. 触及止盈点 (+10%)
    4. 触及止损点 (-5%)
    """

    params = (
        ('sma_short', 20),      # 短期均线周期
        ('sma_long', 50),       # 长期均线周期
        ('rsi_period', 14),     # RSI周期
        ('rsi_oversold', 30),  # RSI超卖阈值
        ('rsi_overbought', 70), # RSI超买阈值
        ('bb_period', 20),      # 布林带周期
        ('bb_std', 2),          # 布林带标准差倍数
        ('stop_loss', 0.05),    # 止损比例
        ('take_profit', 0.10),  # 止盈比例
        ('volume_ratio', 1.5),  # 成交量放大倍数
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

        # 均线指标
        self.sma_short = btind.SimpleMovingAverage(
            self.datas[0], period=self.params.sma_short)
        self.sma_long = btind.SimpleMovingAverage(
            self.datas[0], period=self.params.sma_long)

        # RSI指标
        self.rsi = btind.RSI(
            self.datas[0].close, period=self.params.rsi_period)

        # MACD指标
        self.macd = btind.MACD(
            self.datas[0].close,
            period_me1=12,
            period_me2=26,
            period_signal=9
        )

        # 布林带指标
        self.bb = btind.BollingerBands(
            self.datas[0].close,
            period=self.params.bb_period,
            devfactor=self.params.bb_std
        )

        # 成交量均线
        self.volume_sma = btind.SimpleMovingAverage(
            self.datas[0].volume, period=20)

        # 交叉信号
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

    def should_buy(self) -> tuple:
        """判断是否应该买入，返回(是否买入, 原因)"""
        close = self.dataclose[0]
        prev_close = self.dataclose[-1]

        # 条件1: SMA金叉 + RSI未超买 + 成交量放大
        if (self.crossover_short > 0 and
            self.rsi[0] < self.params.rsi_overbought and
            self.datavolume[0] > self.volume_sma[0] * self.params.volume_ratio):
            return True, "SMA金叉+成交量放大"

        # 条件2: 价格触及布林下轨且反弹
        if (close > self.bb.lines.bot[0] and
            prev_close <= self.bb.lines.bot[-1] and
            self.rsi[0] < self.params.rsi_overbought):
            return True, "布林带下轨反弹"

        # 条件3: MACD金叉 + 站上20日均线
        if (self.macd.lines.macd[0] > self.macd.lines.signal[0] and
            self.macd.lines.macd[-1] <= self.macd.lines.signal[-1] and
            close > self.sma_short[0]):
            return True, "MACD金叉"

        # 条件4: RSI超卖后回升
        if (self.rsi[-1] < self.params.rsi_oversold and
            self.rsi[0] > self.params.rsi_oversold and
            close > self.sma_short[0]):
            return True, "RSI超卖回升"

        return False, ""

    def should_sell(self) -> tuple:
        """判断是否应该卖出，返回(是否卖出, 原因)"""
        if not self.position:
            return False, ""

        close = self.dataclose[0]
        entry_price = self.buyprice

        # 条件1: SMA死叉
        if self.crossover_long > 0:
            return True, "SMA死叉"

        # 条件2: RSI超买
        if self.rsi[0] > self.params.rsi_overbought:
            return True, "RSI超买"

        # 条件3: 触及止盈点
        if entry_price and close > entry_price * (1 + self.params.take_profit):
            return True, "触及止盈点"

        # 条件4: 触及止损点
        if entry_price and close < entry_price * (1 - self.params.stop_loss):
            return True, "触及止损点"

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


class AwareMultiIndicatorStrategy(bt.Strategy):
    """带AI分析的多指标策略（用于实时交易）"""

    params = (
        ('sma_short', 20),
        ('sma_long', 50),
        ('rsi_period', 14),
        ('rsi_oversold', 30),
        ('rsi_overbought', 70),
        ('bb_period', 20),
        ('bb_std', 2),
        ('stop_loss', 0.05),
        ('take_profit', 0.10),
        ('volume_ratio', 1.5),
        ('ai_confidence_threshold', 0.6),  # AI信心阈值
    )

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.datavolume = self.datas[0].volume

        self.order = None
        self.buyprice = None

        # 指标
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
            self.order = None

    def set_ai_signal(self, ai_result: Dict[str, Any]):
        """设置AI分析结果"""
        self.ai_signal = ai_result

    def should_buy(self) -> tuple:
        """带AI信号的买入判断"""
        close = self.dataclose[0]
        prev_close = self.dataclose[-1]

        indicator_signal = False
        indicator_reason = ""

        # 指标信号判断
        if (self.crossover_short > 0 and
            self.rsi[0] < self.params.rsi_overbought and
            self.datavolume[0] > self.volume_sma[0] * self.params.volume_ratio):
            indicator_signal = True
            indicator_reason = "SMA金叉+放量"
        elif (close > self.bb.lines.bot[0] and
              prev_close <= self.bb.lines.bot[-1]):
            indicator_signal = True
            indicator_reason = "布林下轨反弹"
        elif (self.macd.lines.macd[0] > self.macd.lines.signal[0] and
              self.macd.lines.macd[-1] <= self.macd.lines.signal[-1]):
            indicator_signal = True
            indicator_reason = "MACD金叉"

        # AI信号判断
        ai_signal = False
        ai_reason = ""
        if hasattr(self, 'ai_signal') and self.ai_signal:
            rec = self.ai_signal.get('recommendation', '')
            conf = self.ai_signal.get('confidence', 0)
            if rec == 'buy' and conf >= self.params.ai_confidence_threshold:
                ai_signal = True
                ai_reason = f"AI建议(conf={conf:.2f})"

        # 综合判断: 指标信号+AI信号都满足，或者指标信号+AI推荐hold但信心低
        if indicator_signal and ai_signal:
            return True, f"{indicator_reason}+{ai_reason}"
        elif indicator_signal and not ai_signal:
            return True, indicator_reason

        return False, ""

    def should_sell(self) -> tuple:
        if not self.position:
            return False, ""

        close = self.dataclose[0]

        if self.crossover_long > 0:
            return True, "SMA死叉"
        if self.rsi[0] > self.params.rsi_overbought:
            return True, "RSI超买"
        if self.buyprice and close > self.buyprice * (1 + self.params.take_profit):
            return True, "止盈"
        if self.buyprice and close < self.buyprice * (1 - self.params.stop_loss):
            return True, "止损"

        # AI卖出信号
        if hasattr(self, 'ai_signal') and self.ai_signal:
            rec = self.ai_signal.get('recommendation', '')
            conf = self.ai_signal.get('confidence', 0)
            if rec == 'sell' and conf >= self.params.ai_confidence_threshold:
                return True, f"AI卖出(conf={conf:.2f})"

        return False, ""

    def next(self):
        if self.order:
            return

        if not self.position:
            should_buy, reason = self.should_buy()
            if should_buy:
                self.log(f'买入: {reason}')
                self.order = self.buy()
        else:
            should_sell, reason = self.should_sell()
            if should_sell:
                self.log(f'卖出: {reason}')
                self.order = self.sell()
