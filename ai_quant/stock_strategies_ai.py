"""AI综合分析策略 - 结合AI分析和技术指标"""
import backtrader as bt
import backtrader.indicators as btind
import json
from ai_quant.ai_client import AIClient


class AIStrategy(bt.Strategy):
    """AI综合分析策略
    
    核心思路：
    - 每天调用AI分析股票
    - 结合AI建议和技术指标
    - 只做多，不做空
    - 严格止损
    """

    params = (
        ('ai_enabled', True),  # 是否启用AI分析
        ('stop_loss', 0.05),   # 止损5%
        ('take_profit', 0.20), # 止盈20%
    )

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.order = None
        self.buyprice = None

        self.sma_short = btind.SimpleMovingAverage(
            self.datas[0], period=20)
        self.sma_long = btind.SimpleMovingAverage(
            self.datas[0], period=50)

        self.rsi = btind.RSI(
            self.datas[0].close, period=14)

        self.bb = btind.BollingerBands(
            self.datas[0].close,
            period=20,
            devfactor=2
        )

        self.ai_client = AIClient()
        self.ai_signal = None
        self.last_ai_update = None

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

    def get_ai_signal(self):
        """获取AI分析信号，每5个交易日更新一次"""
        current_date = self.datas[0].datetime.date(0)

        if self.last_ai_update == current_date:
            return self.ai_signal

        try:
            close = float(self.dataclose[0])
            sma20 = float(self.sma_short[0])
            sma50 = float(self.sma_long[0])
            rsi = float(self.rsi[0])
            bb_upper = float(self.bb.lines.top[0])
            bb_mid = float(self.bb.lines.mid[0])
            bb_lower = float(self.bb.lines.bot[0])
            volume = int(self.datas[0].volume[0])

            price_data = ""
            for i in range(min(20, len(self.dataclose))):
                d = self.datas[0].datetime.date(-i)
                price_data += f"{d}: {self.dataclose[-i]:.2f}, "

            result = self.ai_client.analyze_stock(
                symbol=self.datas[0]._name,
                name=self.datas[0]._name,
                price_data=price_data,
                close=close,
                sma20=sma20,
                sma50=sma50,
                rsi=rsi,
                macd=0,
                bb_upper=bb_upper,
                bb_mid=bb_mid,
                bb_lower=bb_lower,
                volume=volume
            )

            if result:
                self.ai_signal = result
                self.last_ai_update = current_date
                self.log(f'AI分析: {result.get("recommendation")}, 信心:{result.get("confidence")}, 原因:{result.get("reason")}')

        except Exception as e:
            self.log(f'AI分析失败: {e}')

        return self.ai_signal

    def should_buy(self) -> tuple:
        ai = self.get_ai_signal()

        if not ai:
            return False, "无AI信号"

        recommendation = ai.get('recommendation', 'hold')
        confidence = ai.get('confidence', 0.5)
        trend = ai.get('trend', 'sideways')

        if recommendation == 'buy' and confidence >= 0.6:
            if trend in ['bullish', 'sideways']:
                return True, f"AI买入:{trend},信心:{confidence}"

        return False, ""

    def should_sell(self) -> tuple:
        if not self.position:
            return False, ""

        close = float(self.dataclose[0])
        entry = self.buyprice

        ai = self.get_ai_signal()

        if ai:
            recommendation = ai.get('recommendation', 'hold')
            if recommendation == 'sell':
                return True, "AI建议卖出"

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


class NVDA_AI(AIStrategy):
    pass


class TSLA_AI(AIStrategy):
    params = (
        ('ai_enabled', True),
        ('stop_loss', 0.06),
        ('take_profit', 0.25),
    )


class AAPL_AI(AIStrategy):
    params = (
        ('ai_enabled', True),
        ('stop_loss', 0.05),
        ('take_profit', 0.18),
    )


class MSFT_AI(AIStrategy):
    pass


class AMZN_AI(AIStrategy):
    params = (
        ('ai_enabled', True),
        ('stop_loss', 0.05),
        ('take_profit', 0.20),
    )


class GOOGL_AI(AIStrategy):
    pass


class META_AI(AIStrategy):
    params = (
        ('ai_enabled', True),
        ('stop_loss', 0.06),
        ('take_profit', 0.22),
    )


class AMAT_AI(AIStrategy):
    pass
