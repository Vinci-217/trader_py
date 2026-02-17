import backtrader as bt
import pandas as pd
import numpy as np


class CompositeSignalStrategy(bt.Strategy):
    params = (
        ('rebalance_days', 5),
        ('top_n', 2),
    )
    
    def __init__(self):
        self.last_rebalance = -1
        self.inds = {}
        
        for i, data in enumerate(self.datas):
            symbol = data._name
            
            self.inds[symbol] = {}
            
            self.inds[symbol]['sma5'] = bt.indicators.SMA(data.close, period=5)
            self.inds[symbol]['sma10'] = bt.indicators.SMA(data.close, period=10)
            self.inds[symbol]['sma20'] = bt.indicators.SMA(data.close, period=20)
            
            self.inds[symbol]['rsi'] = bt.indicators.RSI(data.close, period=14)
            
            ema12 = bt.indicators.EMA(data.close, period=12)
            ema26 = bt.indicators.EMA(data.close, period=26)
            self.inds[symbol]['macd'] = ema12 - ema26
            self.inds[symbol]['macd_signal'] = bt.indicators.EMA(self.inds[symbol]['macd'], period=9)
            
            self.inds[symbol]['stoch'] = bt.indicators.StochasticSlow(data, period=14)
            
            bb_mid = bt.indicators.SMA(data.close, period=20)
            bb_std = bt.indicators.StdDev(data.close, period=20)
            self.inds[symbol]['bb_upper'] = bb_mid + 2 * bb_std
            self.inds[symbol]['bb_lower'] = bb_mid - 2 * bb_std
            
            self.inds[symbol]['mom5'] = bt.indicators.Momentum(data.close, period=5)
            self.inds[symbol]['mom10'] = bt.indicators.Momentum(data.close, period=10)
            self.inds[symbol]['mom20'] = bt.indicators.Momentum(data.close, period=20)
    
    def get_stoch_k(self, stoch):
        try:
            return stoch.lines.k[0]
        except:
            return 50
    
    def calculate_score(self, data):
        symbol = data._name
        ind = self.inds[symbol]
        
        close = data.close[0]
        
        rsi = ind['rsi'][0]
        macd = ind['macd'][0]
        macd_signal = ind['macd_signal'][0]
        macd_hist = macd - macd_signal
        stoch = ind['stoch']
        kdj_k = self.get_stoch_k(stoch)
        bb_upper = ind['bb_upper'][0]
        bb_lower = ind['bb_lower'][0]
        sma5 = ind['sma5'][0]
        sma10 = ind['sma10'][0]
        sma20 = ind['sma20'][0]
        mom5 = ind['mom5'][0]
        mom10 = ind['mom10'][0]
        mom20 = ind['mom20'][0]
        
        if np.isnan(rsi) or np.isnan(macd) or np.isnan(kdj_k):
            return -999
        
        score = 0.0
        
        if 30 < rsi < 70:
            score += (50 - abs(rsi - 50)) * 0.3
        elif rsi < 30:
            score += (30 - rsi) * 0.5
        elif rsi > 70:
            score -= (rsi - 70) * 0.5
        
        if macd > macd_signal:
            score += 3
        else:
            score -= 3
        
        if macd_hist > 0:
            score += 2
        else:
            score -= 2
        
        if kdj_k < 20:
            score += 3
        elif kdj_k > 80:
            score -= 3
        
        if close > sma5:
            score += 2
        if close > sma10:
            score += 2
        if close > sma20:
            score += 3
        if sma5 > sma10:
            score += 2
        if sma10 > sma20:
            score += 2
        
        if close > bb_upper:
            score -= 2
        elif close < bb_lower:
            score += 3
        
        score += mom5 * 10 + mom10 * 5 + mom20 * 3
        
        return score
    
    def next(self):
        current_idx = len(self)
        
        if self.last_rebalance >= 0 and current_idx - self.last_rebalance < self.params.rebalance_days:
            return
        
        if current_idx < 30:
            return
        
        self.last_rebalance = current_idx
        
        scores = {}
        for i, data in enumerate(self.datas):
            symbol = data._name
            score = self.calculate_score(data)
            scores[symbol] = score
        
        if not scores:
            return
        
        sorted_stocks = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        top_stocks = [s[0] for s in sorted_stocks[:self.params.top_n]]
        
        for i, data in enumerate(self.datas):
            symbol = data._name
            pos = self.getposition(data)
            if pos.size > 0 and symbol not in top_stocks:
                self.close(data)
        
        target_value = self.broker.getvalue() / len(top_stocks) if top_stocks else 0
        
        for symbol in top_stocks:
            for data in self.datas:
                if data._name == symbol:
                    pos = self.getposition(data)
                    current_value = pos.size * pos.price if pos.size > 0 else 0
                    if current_value < target_value * 0.9:
                        size = int((target_value - current_value) / data.close[0])
                        if size > 0:
                            self.buy(data, size=size)
                    break
    
    def notify_order(self, order):
        pass


class TrendFollowStrategy(bt.Strategy):
    params = (
        ('rebalance_days', 5),
    )
    
    def __init__(self):
        self.last_rebalance = -1
        self.inds = {}
        
        for i, data in enumerate(self.datas):
            symbol = data._name
            
            self.inds[symbol] = {}
            self.inds[symbol]['ema12'] = bt.indicators.EMA(data.close, period=12)
            self.inds[symbol]['ema26'] = bt.indicators.EMA(data.close, period=26)
            self.inds[symbol]['sma20'] = bt.indicators.SMA(data.close, period=20)
            self.inds[symbol]['sma50'] = bt.indicators.SMA(data.close, period=50)
            self.inds[symbol]['mom20'] = bt.indicators.Momentum(data.close, period=20)
    
    def next(self):
        current_idx = len(self)
        
        if self.last_rebalance >= 0 and current_idx - self.last_rebalance < self.params.rebalance_days:
            return
        
        if current_idx < 55:
            return
        
        self.last_rebalance = current_idx
        
        scores = {}
        for i, data in enumerate(self.datas):
            symbol = data._name
            ind = self.inds[symbol]
            
            ema12 = ind['ema12'][0]
            ema26 = ind['ema26'][0]
            sma20 = ind['sma20'][0]
            close = data.close[0]
            mom20 = ind['mom20'][0]
            
            if np.isnan(ema12) or np.isnan(sma20):
                continue
            
            score = 0
            
            if ema12 > ema26:
                score += 3
            
            if close > sma20:
                score += 3
            
            if mom20 > 0:
                score += 4
            
            scores[symbol] = score
        
        if not scores:
            return
        
        sorted_stocks = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        best_stock = sorted_stocks[0][0]
        
        if scores[best_stock] >= 5:
            for data in self.datas:
                if self.getposition(data).size > 0 and data._name != best_stock:
                    self.close(data)
            
            for data in self.datas:
                if data._name == best_stock:
                    if self.getposition(data).size == 0:
                        size = int(self.broker.getvalue() * 0.98 / data.close[0])
                        if size > 0:
                            self.buy(data, size=size)
                    break
    
    def notify_order(self, order):
        pass


class StrongMomentumStrategy(bt.Strategy):
    params = (
        ('rebalance_days', 10),
    )
    
    def __init__(self):
        self.last_rebalance = -1
        self.inds = {}
        
        for i, data in enumerate(self.datas):
            symbol = data._name
            
            self.inds[symbol] = {}
            self.inds[symbol]['mom30'] = bt.indicators.Momentum(data.close, period=30)
            self.inds[symbol]['mom60'] = bt.indicators.Momentum(data.close, period=60)
            self.inds[symbol]['sma30'] = bt.indicators.SMA(data.close, period=30)
    
    def next(self):
        current_idx = len(self)
        
        if self.last_rebalance >= 0 and current_idx - self.last_rebalance < self.params.rebalance_days:
            return
        
        if current_idx < 65:
            return
        
        self.last_rebalance = current_idx
        
        momentum_list = []
        for i, data in enumerate(self.datas):
            symbol = data._name
            ind = self.inds[symbol]
            
            mom30 = ind['mom30'][0]
            mom60 = ind['mom60'][0]
            sma30 = ind['sma30'][0]
            close = data.close[0]
            
            if np.isnan(mom30) or np.isnan(mom60):
                continue
            
            combined_mom = mom30 * 0.4 + mom60 * 0.6
            
            if close > sma30:
                combined_mom += 0.02
            
            momentum_list.append((symbol, combined_mom, data))
        
        if not momentum_list:
            return
        
        momentum_list.sort(key=lambda x: x[1], reverse=True)
        best_stock = momentum_list[0][0]
        
        for data in self.datas:
            if self.getposition(data).size > 0 and data._name != best_stock:
                self.close(data)
        
        for data in self.datas:
            if data._name == best_stock:
                if self.getposition(data).size == 0:
                    size = int(self.broker.getvalue() * 0.98 / data.close[0])
                    if size > 0:
                        self.buy(data, size=size)
                break
    
    def notify_order(self, order):
        pass


class DualMomentumStrategy(bt.Strategy):
    params = (
        ('short_period', 20),
        ('long_period', 60),
        ('rebalance_days', 10),
    )
    
    def __init__(self):
        self.last_rebalance = -1
        self.inds = {}
        
        for i, data in enumerate(self.datas):
            symbol = data._name
            
            self.inds[symbol] = {}
            self.inds[symbol]['mom_short'] = bt.indicators.Momentum(data.close, period=self.params.short_period)
            self.inds[symbol]['mom_long'] = bt.indicators.Momentum(data.close, period=self.params.long_period)
            self.inds[symbol]['sma50'] = bt.indicators.SMA(data.close, period=50)
    
    def next(self):
        current_idx = len(self)
        
        if self.last_rebalance >= 0 and current_idx - self.last_rebalance < self.params.rebalance_days:
            return
        
        if current_idx < self.params.long_period + 5:
            return
        
        self.last_rebalance = current_idx
        
        momentum_list = []
        for i, data in enumerate(self.datas):
            symbol = data._name
            ind = self.inds[symbol]
            
            mom_short = ind['mom_short'][0]
            mom_long = ind['mom_long'][0]
            sma50 = ind['sma50'][0]
            close = data.close[0]
            
            if np.isnan(mom_short) or np.isnan(mom_long):
                continue
            
            dual_score = mom_short + mom_long
            
            if close > sma50:
                dual_score += 0.03
            
            momentum_list.append((symbol, dual_score, data))
        
        if not momentum_list:
            return
        
        momentum_list.sort(key=lambda x: x[1], reverse=True)
        best_stock = momentum_list[0][0]
        
        for data in self.datas:
            if self.getposition(data).size > 0 and data._name != best_stock:
                self.close(data)
        
        for data in self.datas:
            if data._name == best_stock:
                if self.getposition(data).size == 0:
                    size = int(self.broker.getvalue() * 0.98 / data.close[0])
                    if size > 0:
                        self.buy(data, size=size)
                break
    
    def notify_order(self, order):
        pass
