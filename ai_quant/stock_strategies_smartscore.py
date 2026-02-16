"""智能评分策略 - 多指标综合评分 + 动态仓位"""
import backtrader as bt
import backtrader.indicators as btind


class SmartScoreStrategy(bt.Strategy):
    """智能评分策略
    
    思路：
    - 多指标综合评分（趋势、动量、RSI、布林带）
    - 高分时重仓，低分时空仓
    - 严格的止盈止损
    - 只做多，不做空
    """

    params = (
        ('sma_short', 20),
        ('sma_long', 50),
        ('rsi_period', 14),
        ('bb_period', 20),
        ('bb_std', 2),
        ('stop_loss', 0.05),
        ('take_profit', 0.15),
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

    def calculate_score(self) -> float:
        """计算综合评分 (-10 到 10)"""
        score = 0
        close = self.dataclose[0]

        # 趋势评分 (权重3)
        if close > self.sma_long[0]:
            score += 3
        elif close > self.sma_short[0]:
            score += 1
        else:
            score -= 3

        if self.sma_short[0] > self.sma_long[0]:
            score += 2

        # 均线金叉/死叉
        if self.crossover_short > 0:
            score += 3
        if self.crossover_long > 0:
            score -= 3

        # RSI评分 (权重2)
        rsi = self.rsi[0]
        if rsi < 30:
            score += 3  # 超卖，是买入机会
        elif rsi < 45:
            score += 1  # 低位
        elif rsi > 70:
            score -= 2  # 超买
        elif rsi > 55:
            score -= 1  # 高位

        # 布林带评分 (权重2)
        bb_position = (close - self.bb.lines.bot[0]) / (self.bb.lines.top[0] - self.bb.lines.bot[0] + 0.001)
        if bb_position < 0.2:
            score += 2  # 接近下轨
        elif bb_position > 0.8:
            score -= 2  # 接近上轨

        # MACD评分 (权重2)
        if self.macd.lines.macd[0] > self.macd.lines.signal[0]:
            score += 2
        else:
            score -= 1

        # 动量评分 (权重1)
        if close > self.dataclose[-5]:
            score += 1
        else:
            score -= 1

        return score

    def should_buy(self) -> tuple:
        score = self.calculate_score()

        if score >= 5:  # 高分才买入
            return True, f"评分{score}"

        return False, ""

    def should_sell(self) -> tuple:
        if not self.position:
            return False, ""

        close = self.dataclose[0]
        entry = self.buyprice
        score = self.calculate_score()

        # 评分过低
        if score < -3:
            return True, f"评分过低{score}"

        # 止盈
        if entry and close > entry * (1 + self.params.take_profit):
            return True, "止盈"

        # 止损
        if entry and close < entry * (1 - self.params.stop_loss):
            return True, "止损"

        # 均线死叉
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


class NVDA_SmartScore(SmartScoreStrategy):
    params = (
        ('sma_short', 15),
        ('sma_long', 45),
        ('rsi_period', 12),
        ('bb_period', 15),
        ('bb_std', 2),
        ('stop_loss', 0.06),
        ('take_profit', 0.18),
    )


class TSLA_SmartScore(SmartScoreStrategy):
    params = (
        ('sma_short', 12),
        ('sma_long', 35),
        ('rsi_period', 10),
        ('bb_period', 12),
        ('bb_std', 2.5),
        ('stop_loss', 0.05),
        ('take_profit', 0.15),
    )


class AAPL_SmartScore(SmartScoreStrategy):
    params = (
        ('sma_short', 20),
        ('sma_long', 50),
        ('rsi_period', 14),
        ('bb_period', 20),
        ('bb_std', 2),
        ('stop_loss', 0.05),
        ('take_profit', 0.12),
    )


class MSFT_SmartScore(SmartScoreStrategy):
    params = (
        ('sma_short', 15),
        ('sma_long', 45),
        ('rsi_period', 12),
        ('bb_period', 15),
        ('bb_std', 2),
        ('stop_loss', 0.05),
        ('take_profit', 0.15),
    )


class AMZN_SmartScore(SmartScoreStrategy):
    params = (
        ('sma_short', 15),
        ('sma_long', 40),
        ('rsi_period', 12),
        ('bb_period', 15),
        ('bb_std', 2.5),
        ('stop_loss', 0.05),
        ('take_profit', 0.15),
    )


class GOOGL_SmartScore(SmartScoreStrategy):
    params = (
        ('sma_short', 15),
        ('sma_long', 45),
        ('rsi_period', 12),
        ('bb_period', 15),
        ('bb_std', 2),
        ('stop_loss', 0.05),
        ('take_profit', 0.15),
    )


class META_SmartScore(SmartScoreStrategy):
    params = (
        ('sma_short', 12),
        ('sma_long', 35),
        ('rsi_period', 10),
        ('bb_period', 12),
        ('bb_std', 2.5),
        ('stop_loss', 0.05),
        ('take_profit', 0.18),
    )


class AMAT_SmartScore(SmartScoreStrategy):
    params = (
        ('sma_short', 15),
        ('sma_long', 45),
        ('rsi_period', 12),
        ('bb_period', 15),
        ('bb_std', 2),
        ('stop_loss', 0.06),
        ('take_profit', 0.15),
    )
