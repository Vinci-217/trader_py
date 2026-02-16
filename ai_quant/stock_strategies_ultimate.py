"""
终极综合策略 - 多因子 + 机器学习 + 技术指标

核心思路：
1. 多因子评分：趋势、动量、波动率、成交量等
2. 机器学习预测：基于历史数据预测涨跌概率
3. 综合评分 > 阈值时买入，设置止盈止损
"""
import backtrader as bt
import backtrader.indicators as btind
import numpy as np
from collections import deque
from typing import Dict, Tuple


class MultiFactorAnalyzer:
    """多因子分析器"""
    
    def __init__(self):
        self.price_history = deque(maxlen=100)
        
    def update(self, close: float):
        self.price_history.append(close)
    
    def calculate_trend_factor(self, close, sma_short, sma_long, sma_trend) -> float:
        """趋势因子 (0-100)"""
        score = 50
        if close > sma_long:
            score += 15
        if close > sma_short:
            score += 10
        if sma_short > sma_long:
            score += 15
        if sma_trend > 0:
            score += 10
        return min(100, score)
    
    def calculate_momentum_factor(self, rsi, macd, macd_signal, macd_hist) -> float:
        """动量因子 (0-100)"""
        score = 50
        if 30 < rsi < 50:
            score += 20
        elif rsi < 30:
            score += 25
        elif 50 < rsi < 70:
            score += 10
        elif rsi > 70:
            score -= 20
        if macd > macd_signal:
            score += 10
        if macd_hist > 0:
            score += 5
        return max(0, min(100, score))
    
    def calculate_volatility_factor(self, close, bb_upper, bb_lower, atr, atr_ma) -> float:
        """波动率因子 (0-100)"""
        score = 50
        bb_width = (bb_upper - bb_lower) / (close + 0.001)
        if bb_width < 0.05:
            score += 15
        elif bb_width < 0.10:
            score += 8
        bb_position = (close - bb_lower) / (bb_upper - bb_lower + 0.001)
        if bb_position < 0.25:
            score += 20
        elif bb_position < 0.40:
            score += 10
        elif bb_position > 0.80:
            score -= 15
        if atr < atr_ma:
            score += 5
        return max(0, min(100, score))
    
    def calculate_volume_factor(self, volume, volume_ma) -> float:
        """成交量因子 (0-100)"""
        score = 50
        if volume > volume_ma * 1.5:
            score += 15
        elif volume > volume_ma:
            score += 8
        return min(100, score)
    
    def calculate_price_pattern_factor(self, close, high, low, prev_close) -> float:
        """价格形态因子 (0-100)"""
        score = 50
        change = (close - prev_close) / (prev_close + 0.001) * 100
        if 0 < change < 2:
            score += 15
        elif -2 < change < 0:
            score += 8
        elif change > 3:
            score -= 5
        body = abs(close - prev_close)
        range_hl = high - low
        if range_hl > 0:
            body_ratio = body / range_hl
            if body_ratio > 0.6:
                score += 5
        return max(0, min(100, score))


class MLPredictor:
    """机器学习预测器 - 简化版"""
    
    def __init__(self, lookback=20):
        self.lookback = lookback
    
    def predict(self, features: Dict) -> float:
        """预测上涨概率 (0-100)"""
        score = 50
        
        if features['price_above_sma20']:
            score += 8
        if features['price_above_sma50']:
            score += 8
        if features['sma20_above_sma50']:
            score += 7
        if features['sma_trend'] > 0:
            score += 5
        
        rsi = features['rsi']
        if rsi < 25:
            score += 20
        elif rsi < 35:
            score += 15
        elif rsi < 45:
            score += 8
        elif rsi > 75:
            score -= 20
        elif rsi > 65:
            score -= 10
        
        if features['macd_above_signal']:
            score += 8
        if features['macd_hist_increasing']:
            score += 5
        
        bb_pos = features['bb_position']
        if bb_pos < 0.2:
            score += 12
        elif bb_pos < 0.35:
            score += 6
        elif bb_pos > 0.85:
            score -= 12
        
        if features['volume_above_avg']:
            score += 5
        
        if features['atr_below_avg']:
            score += 3
        
        return max(0, min(100, score))


class UltimateStrategy(bt.Strategy):
    """终极综合策略
    
    交易规则：
    1. 计算多因子评分
    2. 计算ML预测概率
    3. 综合评分 = 多因子*0.6 + ML*0.4
    4. 评分 >= 阈值时买入
    5. 设置动态止盈止损
    """
    
    params = (
        ('score_threshold', 70),
        ('stop_loss_pct', 0.08),
        ('take_profit_pct', 0.20),
    )
    
    def __init__(self):
        self.dataclose = self.datas[0].close
        self.datahigh = self.datas[0].high
        self.datalow = self.datas[0].low
        self.datavolume = self.datas[0].volume
        self.order = None
        self.buyprice = None
        self.entry_score = None
        
        self.sma_short = btind.SimpleMovingAverage(self.datas[0], period=20)
        self.sma_long = btind.SimpleMovingAverage(self.datas[0], period=50)
        self.sma_trend = btind.SimpleMovingAverage(self.datas[0], period=10)
        
        self.rsi = btind.RSI(self.datas[0].close, period=14)
        
        self.bb = btind.BollingerBands(self.datas[0].close, period=20, devfactor=2)
        
        self.macd = btind.MACD(self.datas[0].close, period_me1=12, period_me2=26, period_signal=9)
        self.macd_hist = self.macd.lines.macd - self.macd.lines.signal
        
        self.atr = btind.ATR(self.datas[0], period=14)
        self.atr_ma = btind.SimpleMovingAverage(self.atr, period=20)
        
        self.volume_ma = btind.SimpleMovingAverage(self.datas[0].volume, period=20)
        
        self.multi_factor = MultiFactorAnalyzer()
        self.ml_predictor = MLPredictor()
    
    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        print(f'{dt.isoformat()}, {txt}')
    
    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
        if order.status == order.Completed:
            if order.isbuy():
                self.buyprice = order.executed.price
                self.log(f'买入成交: 价格={order.executed.price:.2f}, 评分={self.entry_score:.0f}')
            else:
                self.log(f'卖出成交: 价格={order.executed.price:.2f}')
            self.order = None
    
    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        pnl = trade.pnlcomm
        if self.buyprice and trade.size:
            pnl_pct = pnl / (self.buyprice * abs(trade.size)) * 100
            self.log(f'交易结束: 盈亏={pnl:.2f}, 收益率={pnl_pct:.1f}%')
        else:
            self.log(f'交易结束: 盈亏={pnl:.2f}')
    
    def extract_features(self) -> Dict:
        """提取特征"""
        close = float(self.dataclose[0])
        prev_close = float(self.dataclose[-1]) if len(self.dataclose) > 1 else close
        
        return {
            'price_above_sma20': close > float(self.sma_short[0]),
            'price_above_sma50': close > float(self.sma_long[0]),
            'sma20_above_sma50': float(self.sma_short[0]) > float(self.sma_long[0]),
            'sma_trend': float(self.sma_trend[0]) - float(self.sma_trend[-1]) if len(self.sma_trend) > 1 else 0,
            'rsi': float(self.rsi[0]),
            'macd_above_signal': float(self.macd.lines.macd[0]) > float(self.macd.lines.signal[0]),
            'macd_hist_increasing': float(self.macd_hist[0]) > float(self.macd_hist[-1]) if len(self.macd_hist) > 1 else False,
            'bb_position': (close - float(self.bb.lines.bot[0])) / (float(self.bb.lines.top[0]) - float(self.bb.lines.bot[0]) + 0.001),
            'volume_above_avg': float(self.datavolume[0]) > float(self.volume_ma[0]),
            'atr_below_avg': float(self.atr[0]) < float(self.atr_ma[0]),
        }
    
    def calculate_comprehensive_score(self) -> Tuple[float, Dict[str, float]]:
        """计算综合评分"""
        close = float(self.dataclose[0])
        high = float(self.datahigh[0])
        low = float(self.datalow[0])
        prev_close = float(self.dataclose[-1]) if len(self.dataclose) > 1 else close
        
        self.multi_factor.update(close)
        
        trend_score = self.multi_factor.calculate_trend_factor(
            close, float(self.sma_short[0]), float(self.sma_long[0]), 
            float(self.sma_trend[0]) - float(self.sma_trend[-1]) if len(self.sma_trend) > 1 else 0
        )
        
        momentum_score = self.multi_factor.calculate_momentum_factor(
            float(self.rsi[0]), 
            float(self.macd.lines.macd[0]), 
            float(self.macd.lines.signal[0]),
            float(self.macd_hist[0])
        )
        
        volatility_score = self.multi_factor.calculate_volatility_factor(
            close, 
            float(self.bb.lines.top[0]), 
            float(self.bb.lines.bot[0]),
            float(self.atr[0]),
            float(self.atr_ma[0])
        )
        
        volume_score = self.multi_factor.calculate_volume_factor(
            float(self.datavolume[0]), 
            float(self.volume_ma[0])
        )
        
        pattern_score = self.multi_factor.calculate_price_pattern_factor(
            close, high, low, prev_close
        )
        
        factor_score = (
            trend_score * 0.30 + 
            momentum_score * 0.25 + 
            volatility_score * 0.20 + 
            volume_score * 0.15 + 
            pattern_score * 0.10
        )
        
        features = self.extract_features()
        ml_score = self.ml_predictor.predict(features)
        
        comprehensive_score = factor_score * 0.6 + ml_score * 0.4
        
        scores = {
            'factor': factor_score,
            'ml': ml_score,
            'comprehensive': comprehensive_score,
            'trend': trend_score,
            'momentum': momentum_score,
            'volatility': volatility_score,
            'volume': volume_score,
        }
        
        return comprehensive_score, scores
    
    def calculate_dynamic_stop_loss(self) -> float:
        """计算动态止损比例"""
        atr = float(self.atr[0])
        close = float(self.dataclose[0])
        
        atr_pct = atr / (close + 0.001)
        
        if atr_pct < 0.02:
            return 0.05
        elif atr_pct < 0.03:
            return 0.07
        elif atr_pct < 0.05:
            return 0.10
        else:
            return 0.12
    
    def calculate_dynamic_take_profit(self, score: float) -> float:
        """计算动态止盈比例"""
        if score >= 80:
            return 0.28
        elif score >= 75:
            return 0.24
        elif score >= 70:
            return 0.20
        else:
            return 0.18
    
    def should_buy(self) -> Tuple[bool, str, float]:
        """判断是否买入"""
        score, scores = self.calculate_comprehensive_score()
        
        if score >= self.params.score_threshold:
            reasons = []
            if scores['trend'] >= 60:
                reasons.append("趋势↑")
            if scores['momentum'] >= 60:
                reasons.append("动量↑")
            if scores['ml'] >= 60:
                reasons.append("ML↑")
            
            return True, f"评分{score:.0f}({','.join(reasons)})", score
        
        return False, f"评分{score:.0f}未达标", score
    
    def should_sell(self) -> Tuple[bool, str]:
        """判断是否卖出"""
        if not self.position:
            return False, ""
        
        close = float(self.dataclose[0])
        entry = self.buyprice
        
        score, scores = self.calculate_comprehensive_score()
        
        if score < 35:
            return True, f"评分过低({score:.0f})"
        
        if entry:
            pnl_pct = (close - entry) / entry
            
            take_profit = self.calculate_dynamic_take_profit(self.entry_score)
            if pnl_pct >= take_profit:
                return True, f"止盈({pnl_pct*100:.1f}%)"
            
            stop_loss = self.calculate_dynamic_stop_loss()
            if pnl_pct <= -stop_loss:
                return True, f"止损({pnl_pct*100:.1f}%)"
            
            if pnl_pct > 0.12 and scores['momentum'] < 40:
                return True, f"动量衰减止盈"
        
        if self.rsi[0] > 78:
            return True, "RSI严重超买"
        
        if close < self.sma_long[0] and self.entry_score and self.entry_score >= 75:
            return True, "趋势反转"
        
        return False, ""
    
    def next(self):
        if self.order:
            return
        
        if not self.position:
            should_buy, reason, score = self.should_buy()
            if should_buy:
                self.entry_score = score
                self.log(f'买入信号: {reason}')
                self.order = self.buy()
        else:
            should_sell, reason = self.should_sell()
            if should_sell:
                self.log(f'卖出信号: {reason}')
                self.order = self.sell()


class NVDA_Ultimate(UltimateStrategy):
    params = (
        ('score_threshold', 68),
        ('stop_loss_pct', 0.08),
        ('take_profit_pct', 0.25),
    )


class TSLA_Ultimate(UltimateStrategy):
    params = (
        ('score_threshold', 72),
        ('stop_loss_pct', 0.10),
        ('take_profit_pct', 0.28),
    )


class AAPL_Ultimate(UltimateStrategy):
    params = (
        ('score_threshold', 70),
        ('stop_loss_pct', 0.07),
        ('take_profit_pct', 0.22),
    )


class MSFT_Ultimate(UltimateStrategy):
    params = (
        ('score_threshold', 70),
        ('stop_loss_pct', 0.07),
        ('take_profit_pct', 0.22),
    )


class AMZN_Ultimate(UltimateStrategy):
    params = (
        ('score_threshold', 70),
        ('stop_loss_pct', 0.08),
        ('take_profit_pct', 0.24),
    )


class GOOGL_Ultimate(UltimateStrategy):
    params = (
        ('score_threshold', 68),
        ('stop_loss_pct', 0.07),
        ('take_profit_pct', 0.24),
    )


class META_Ultimate(UltimateStrategy):
    params = (
        ('score_threshold', 72),
        ('stop_loss_pct', 0.10),
        ('take_profit_pct', 0.26),
    )


class AMAT_Ultimate(UltimateStrategy):
    params = (
        ('score_threshold', 70),
        ('stop_loss_pct', 0.09),
        ('take_profit_pct', 0.24),
    )
