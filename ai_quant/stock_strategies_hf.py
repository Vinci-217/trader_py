"""
高频波段策略 - 精准捕捉每一次波动

核心思路：
1. 多因子快速评分：每天计算所有股票评分
2. 智能选最强：选择评分最高的股票
3. 高频交易：每次波段赚取5-15%
4. 动态止盈止损
"""
import backtrader as bt
import backtrader.indicators as btind
import numpy as np
from typing import Dict, Tuple


class HFAnalysis:
    """高频分析器 - 快速计算评分"""
    
    @staticmethod
    def calc_trend(close, sma5, sma10, sma20) -> float:
        score = 50
        if close > sma20: score += 15
        if close > sma10: score += 10
        if close > sma5: score += 10
        if sma5 > sma10: score += 10
        if sma10 > sma20: score += 10
        return min(100, score)
    
    @staticmethod
    def calc_momentum(rsi, macd, macd_sig, price_change) -> float:
        score = 50
        if rsi < 30: score += 25
        elif rsi < 40: score += 15
        elif rsi > 70: score -= 20
        elif rsi > 60: score -= 10
        
        if macd > macd_sig: score += 15
        else: score -= 10
        
        if price_change > 0: score += 10
        else: score -= 5
        
        if 2 < price_change < 8: score += 10
        
        return max(0, min(100, score))
    
    @staticmethod
    def calc_breakout(close, high, low, prev_high, prev_low) -> float:
        score = 50
        if close > prev_high: score += 30
        if close < prev_low: score -= 30
        body = abs(close - (high + low) / 2)
        range_ = high - low
        if range_ > 0 and body / range_ > 0.7:
            score += 10
        return max(0, min(100, score))
    
    @staticmethod
    def calc_volume(vol, vol_ma, vol_ma5) -> float:
        score = 50
        if vol > vol_ma * 1.5: score += 20
        elif vol > vol_ma: score += 10
        if vol > vol_ma5: score += 10
        return min(100, score)


class HighFrequencyStrategy(bt.Strategy):
    """高频波段策略
    
    交易规则：
    1. 每天计算综合评分
    2. 评分>=65买入
    3. 止盈8-15%或止损5%
    4. 可反复交易
    """
    
    params = (
        ('buy_threshold', 65),
        ('sell_threshold', 35),
        ('stop_loss', 0.05),
        ('take_profit', 0.12),
    )
    
    def __init__(self):
        self.dataclose = self.datas[0].close
        self.datahigh = self.datas[0].high
        self.datalow = self.datas[0].low
        self.datavolume = self.datas[0].volume
        
        self.order = None
        self.buyprice = None
        self.entry_score = None
        
        self.sma5 = btind.SimpleMovingAverage(self.datas[0], period=5)
        self.sma10 = btind.SimpleMovingAverage(self.datas[0], period=10)
        self.sma20 = btind.SimpleMovingAverage(self.datas[0], period=20)
        
        self.rsi = btind.RSI(self.datas[0].close, period=7)
        
        self.macd = btind.MACD(self.datas[0].close, period_me1=5, period_me2=13, period_signal=4)
        
        self.atr = btind.ATR(self.datas[0], period=7)
        
        self.volume_ma = btind.SimpleMovingAverage(self.datas[0].volume, period=10)
        self.volume_ma5 = btind.SimpleMovingAverage(self.datas[0].volume, period=5)
        
        self.analysis = HFAnalysis()
        
        self.days_held = 0
    
    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        print(f'{dt.isoformat()}, {txt}')
    
    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
        if order.status == order.Completed:
            if order.isbuy():
                self.buyprice = order.executed.price
                self.days_held = 0
                self.log(f'买入: {order.executed.price:.2f}, 评分={self.entry_score:.0f}')
            else:
                self.log(f'卖出: {order.executed.price:.2f}')
            self.order = None
    
    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        pnl = trade.pnlcomm
        self.log(f'交易结束: 盈亏={pnl:.2f}')
    
    def calculate_score(self) -> float:
        close = float(self.dataclose[0])
        high = float(self.datahigh[0])
        low = float(self.datalow[0])
        vol = float(self.datavolume[0])
        
        prev_close = float(self.dataclose[-1]) if len(self.dataclose) > 1 else close
        prev_high = float(self.datahigh[-1]) if len(self.datahigh) > 1 else high
        prev_low = float(self.datalow[-1]) if len(self.datalow) > 1 else low
        
        price_change = (close - prev_close) / prev_close * 100
        
        trend = self.analysis.calc_trend(
            close, 
            float(self.sma5[0]), 
            float(self.sma10[0]), 
            float(self.sma20[0])
        )
        
        momentum = self.analysis.calc_momentum(
            float(self.rsi[0]),
            float(self.macd.lines.macd[0]),
            float(self.macd.lines.signal[0]),
            price_change
        )
        
        breakout = self.analysis.calc_breakout(close, high, low, prev_high, prev_low)
        
        volume = self.analysis.calc_volume(
            vol,
            float(self.volume_ma[0]),
            float(self.volume_ma5[0])
        )
        
        score = trend * 0.30 + momentum * 0.30 + breakout * 0.25 + volume * 0.15
        
        return score
    
    def should_buy(self) -> Tuple[bool, str]:
        if self.position:
            return False, ""
        
        score = self.calculate_score()
        
        if score >= self.params.buy_threshold:
            self.entry_score = score
            return True, f"评分{score:.0f}"
        
        return False, ""
    
    def should_sell(self) -> Tuple[bool, str]:
        if not self.position:
            return False, ""
        
        close = float(self.dataclose[0])
        entry = self.buyprice
        score = self.calculate_score()
        
        self.days_held += 1
        
        pnl_pct = (close - entry) / entry
        
        if pnl_pct >= self.params.take_profit:
            return True, f"止盈({pnl_pct*100:.1f}%)"
        
        if pnl_pct <= -self.params.stop_loss:
            return True, f"止损({pnl_pct*100:.1f}%)"
        
        if score < self.params.sell_threshold:
            return True, f"评分过低({score:.0f})"
        
        if self.rsi[0] > 80:
            return True, "RSI超买"
        
        if self.days_held >= 3 and pnl_pct > 0.02 and score < 55:
            return True, "短线止盈"
        
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


class NVDA_HF(HighFrequencyStrategy):
    params = (
        ('buy_threshold', 62),
        ('sell_threshold', 38),
        ('stop_loss', 0.06),
        ('take_profit', 0.15),
    )


class TSLA_HF(HighFrequencyStrategy):
    params = (
        ('buy_threshold', 60),
        ('sell_threshold', 40),
        ('stop_loss', 0.07),
        ('take_profit', 0.18),
    )


class AAPL_HF(HighFrequencyStrategy):
    params = (
        ('buy_threshold', 65),
        ('sell_threshold', 35),
        ('stop_loss', 0.05),
        ('take_profit', 0.12),
    )


class MSFT_HF(HighFrequencyStrategy):
    params = (
        ('buy_threshold', 65),
        ('sell_threshold', 35),
        ('stop_loss', 0.05),
        ('take_profit', 0.12),
    )


class AMZN_HF(HighFrequencyStrategy):
    params = (
        ('buy_threshold', 63),
        ('sell_threshold', 37),
        ('stop_loss', 0.06),
        ('take_profit', 0.15),
    )


class GOOGL_HF(HighFrequencyStrategy):
    params = (
        ('buy_threshold', 63),
        ('sell_threshold', 37),
        ('stop_loss', 0.05),
        ('take_profit', 0.14),
    )


class META_HF(HighFrequencyStrategy):
    params = (
        ('buy_threshold', 62),
        ('sell_threshold', 38),
        ('stop_loss', 0.06),
        ('take_profit', 0.15),
    )


class AMAT_HF(HighFrequencyStrategy):
    params = (
        ('buy_threshold', 62),
        ('sell_threshold', 38),
        ('stop_loss', 0.06),
        ('take_profit', 0.15),
    )
