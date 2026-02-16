"""多策略组合 - 智能选股"""
import backtrader as bt
import backtrader.indicators as btind


class MultiStrategy(bt.Strategy):
    """多策略组合 - 同时监控所有股票，根据评分选择最强的"""

    params = (
        ('stocks', ['NVDA', 'TSLA', 'AAPL', 'MSFT', 'AMZN', 'GOOGL', 'META', 'AMAT']),
        ('sma_short', 15),
        ('sma_long', 45),
        ('rsi_period', 12),
        ('stop_loss', 0.05),
        ('take_profit', 0.15),
    )

    def __init__(self):
        self.orders = {}
        for data in self.datas:
            name = data._name
            self.orders[name] = {
                'order': None,
                'buyprice': None,
                'sma_short': btind.SimpleMovingAverage(data, period=self.params.sma_short),
                'sma_long': btind.SimpleMovingAverage(data, period=self.params.sma_long),
                'rsi': btind.RSI(data.close, period=self.params.rsi_period),
                'macd': btind.MACD(data.close, period_me1=12, period_me2=26, period_signal=9),
                'crossover': btind.CrossOver(
                    btind.SimpleMovingAverage(data, period=self.params.sma_short),
                    btind.SimpleMovingAverage(data, period=self.params.sma_long)
                ),
            }

    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        print(f'{dt.isoformat()}, {txt}')

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
        if order.status == order.Completed:
            name = order.data._name
            if order.isbuy():
                self.orders[name]['buyprice'] = order.executed.price
                self.log(f'{name}买入成交, 价格: {order.executed.price:.2f}')
            else:
                self.log(f'{name}卖出成交, 价格: {order.executed.price:.2f}')
            self.orders[name]['order'] = None

    def calculate_score(self, data, state) -> float:
        """计算单只股票评分"""
        score = 0
        close = data.close[0]
        s = state

        # 趋势
        if close > s['sma_long'][0]:
            score += 3
        elif close > s['sma_short'][0]:
            score += 1

        if s['sma_short'][0] > s['sma_long'][0]:
            score += 2

        if s['crossover'] > 0:
            score += 3
        if s['crossover'] < 0:
            score -= 3

        # RSI
        rsi = s['rsi'][0]
        if rsi < 30:
            score += 3
        elif rsi < 45:
            score += 1
        elif rsi > 70:
            score -= 2

        # MACD
        if s['macd'].lines.macd[0] > s['macd'].lines.signal[0]:
            score += 2
        else:
            score -= 1

        return score

    def next(self):
        # 找出评分最高的股票
        scores = {}
        for data in self.datas:
            name = data._name
            state = self.orders[name]
            if state['order'] is None:  # 没有pending订单
                scores[name] = self.calculate_score(data, state)

        if not scores:
            return

        best_stock = max(scores, key=scores.get)
        best_score = scores[best_stock]

        # 如果最高分>=5，买入
        if best_score >= 5:
            state = self.orders[best_stock]
            if not self.getposition(data=self.getdatabyname(best_stock)):
                self.log(f'买入信号: {best_stock}, 评分: {best_score}')
                self.orders[best_stock]['order'] = self.buy(data=self.getdatabyname(best_stock))

        # 检查持仓股票是否需要卖出
        for data in self.datas:
            name = data._name
            state = self.orders[name]
            pos = self.getposition(data=data)

            if pos and pos.size > 0:
                close = data.close[0]
                entry = state['buyprice']

                # 止盈
                if entry and close > entry * (1 + self.params.take_profit):
                    self.log(f'卖出信号: {name}, 止盈')
                    state['order'] = self.sell(data=data)
                    continue

                # 止损
                if entry and close < entry * (1 - self.params.stop_loss):
                    self.log(f'卖出信号: {name}, 止损')
                    state['order'] = self.sell(data=data)
                    continue

                # 均线死叉
                if state['crossover'] < 0:
                    self.log(f'卖出信号: {name}, 均线死叉')
                    state['order'] = self.sell(data=data)
                    continue

                # RSI超买
                if state['rsi'][0] > 75:
                    self.log(f'卖出信号: {name}, RSI超买')
                    state['order'] = self.sell(data=data)
                    continue
