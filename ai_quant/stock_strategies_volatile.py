"""
震荡市高频策略 - 精准捕捉每一次波动

核心思路：
1. 极短周期分析：5分钟级别指标应用到日线
2. 突破买入：价格突破短期高点/低点
3. 超短止盈：3-8%即止盈
4. 严格止损：3-5%
"""
import backtrader as bt
import backtrader.indicators as btind
import numpy as np
from typing import Dict, Tuple


class VolatileStrategy(bt.Strategy):
    """震荡市高频策略
    
    交易规则：
    1. 评分>=55买入（更敏感）
    2. 止盈5-10%或止损3-5%
    3. RSI超买超卖反向交易
    4. 反复交易
    """
    
    params = (
        ('buy_threshold', 55),
        ('sell_threshold', 45),
        ('stop_loss', 0.035),
        ('take_profit', 0.08),
    )
    
    def __init__(self):
        self.dataclose = self.datas[0].close
        self.datahigh = self.datas[0].high
        self.datalow = self.datas[0].low
        self.dataopen = self.datas[0].open
        self.datavolume = self.datas[0].volume
        
        self.order = None
        self.buyprice = None
        self.entry_score = None
        
        self.sma5 = btind.SimpleMovingAverage(self.datas[0], period=5)
        self.sma10 = btind.SimpleMovingAverage(self.datas[0], period=10)
        
        self.rsi = btind.RSI(self.datas[0].close, period=7)
        
        self.macd = btind.MACD(self.datas[0].close, period_me1=5, period_me2=13, period_signal=4)
        
        self.atr = btind.ATR(self.datas[0], period=7)
        
        self.highest = btind.Highest(self.datas[0].high, period=10)
        self.lowest = btind.Lowest(self.datas[0].low, period=10)
        
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
        self.log(f'交易结束: 盈亏={trade.pnlcomm:.2f}')
    
    def calculate_score(self) -> float:
        close = float(self.dataclose[0])
        high = float(self.datahigh[0])
        low = float(self.datalow[0])
        
        prev_close = float(self.dataclose[-1]) if len(self.dataclose) > 1 else close
        prev_high = float(self.datahigh[-1]) if len(self.datahigh) > 1 else high
        
        score = 50
        
        if close > float(self.sma5[0]):
            score += 10
        else:
            score -= 5
        
        if close > float(self.sma10[0]):
            score += 5
        
        rsi = float(self.rsi[0])
        if rsi < 25:
            score += 25
        elif rsi < 35:
            score += 15
        elif rsi > 75:
            score -= 20
        elif rsi > 65:
            score -= 10
        
        macd = float(self.macd.lines.macd[0])
        macd_sig = float(self.macd.lines.signal[0])
        if macd > macd_sig:
            score += 10
        else:
            score -= 5
        
        price_change = (close - prev_close) / prev_close * 100
        if 1 < price_change < 5:
            score += 10
        elif -5 < price_change < -1:
            score += 5
        
        if close > float(self.highest[-1]) * 0.98:
            score += 10
        
        return max(0, min(100, score))
    
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
        
        self.days_held += 1
        
        pnl_pct = (close - entry) / entry
        
        if pnl_pct >= self.params.take_profit:
            return True, f"止盈({pnl_pct*100:.1f}%)"
        
        if pnl_pct <= -self.params.stop_loss:
            return True, f"止损({pnl_pct*100:.1f}%)"
        
        rsi = float(self.rsi[0])
        if rsi > 75:
            return True, "RSI超买"
        
        if rsi > 65 and pnl_pct > 0.02:
            return True, "RSI高位止盈"
        
        if self.days_held >= 2 and pnl_pct > 0.03:
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


class NVDA_Volatile(VolatileStrategy):
    params = (
        ('buy_threshold', 52),
        ('stop_loss', 0.04),
        ('take_profit', 0.10),
    )


class TSLA_Volatile(VolatileStrategy):
    params = (
        ('buy_threshold', 50),
        ('stop_loss', 0.05),
        ('take_profit', 0.12),
    )


class AAPL_Volatile(VolatileStrategy):
    params = (
        ('buy_threshold', 55),
        ('stop_loss', 0.03),
        ('take_profit', 0.07),
    )


class MSFT_Volatile(VolatileStrategy):
    params = (
        ('buy_threshold', 55),
        ('stop_loss', 0.03),
        ('take_profit', 0.07),
    )


class AMZN_Volatile(VolatileStrategy):
    params = (
        ('buy_threshold', 52),
        ('stop_loss', 0.04),
        ('take_profit', 0.10),
    )


class GOOGL_Volatile(VolatileStrategy):
    params = (
        ('buy_threshold', 53),
        ('stop_loss', 0.035),
        ('take_profit', 0.08),
    )


class META_Volatile(VolatileStrategy):
    params = (
        ('buy_threshold', 52),
        ('stop_loss', 0.04),
        ('take_profit', 0.10),
    )


class AMAT_Volatile(VolatileStrategy):
    params = (
        ('buy_threshold', 52),
        ('stop_loss', 0.045),
        ('take_profit', 0.10),
    )
