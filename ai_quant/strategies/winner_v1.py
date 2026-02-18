import backtrader as bt
import pandas as pd
import numpy as np


class WinnerV1Strategy(bt.Strategy):
    params = (
        ('rebalance_days', 5),
    )
    
    def __init__(self):
        self.last_rebalance = -1
        self.inds = {}
        
        for i, data in enumerate(self.datas):
            symbol = data._name
            self.inds[symbol] = {}
            self.inds[symbol]['mom10'] = bt.indicators.Momentum(data.close, period=10)
            self.inds[symbol]['mom20'] = bt.indicators.Momentum(data.close, period=20)
            self.inds[symbol]['mom60'] = bt.indicators.Momentum(data.close, period=60)
            self.inds[symbol]['sma20'] = bt.indicators.SMA(data.close, period=20)
            self.inds[symbol]['sma50'] = bt.indicators.SMA(data.close, period=50)
            self.inds[symbol]['rsi'] = bt.indicators.RSI(data.close, period=14)
            self.inds[symbol]['highest_20'] = bt.indicators.Highest(data.high, period=20)
    
    def next(self):
        current_idx = len(self)
        if current_idx < 65:
            return
        if self.last_rebalance >= 0 and current_idx - self.last_rebalance < self.params.rebalance_days:
            return
        self.last_rebalance = current_idx
        
        momentum_list = []
        for i, data in enumerate(self.datas):
            symbol = data._name
            ind = self.inds[symbol]
            mom10, mom20, mom60 = ind['mom10'][0], ind['mom20'][0], ind['mom60'][0]
            sma20, sma50 = ind['sma20'][0], ind['sma50'][0]
            rsi = ind['rsi'][0]
            highest_20 = ind['highest_20'][0]
            close = data.close[0]
            
            if any(np.isnan(x) for x in [mom10, mom20, mom60, sma20]):
                continue
            
            score = mom10 * 0.3 + mom20 * 0.3 + mom60 * 0.4
            if close >= highest_20 * 0.98:
                score += 0.03
            if close > sma20:
                score += 0.02
            if close > sma50:
                score += 0.02
            if rsi < 45:
                score += 0.01
            
            momentum_list.append((symbol, score, data))
        
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


class WinnerV2Strategy(bt.Strategy):
    params = (
        ('rebalance_days', 10),
    )
    
    def __init__(self):
        self.last_rebalance = -1
        self.inds = {}
        self.entry_prices = {}
        self.max_prices = {}
        
        for i, data in enumerate(self.datas):
            symbol = data._name
            self.inds[symbol] = {}
            self.inds[symbol]['mom10'] = bt.indicators.Momentum(data.close, period=10)
            self.inds[symbol]['mom20'] = bt.indicators.Momentum(data.close, period=20)
            self.inds[symbol]['mom60'] = bt.indicators.Momentum(data.close, period=60)
            self.inds[symbol]['sma20'] = bt.indicators.SMA(data.close, period=20)
            self.inds[symbol]['sma50'] = bt.indicators.SMA(data.close, period=50)
            self.inds[symbol]['highest_20'] = bt.indicators.Highest(data.high, period=20)
    
    def next(self):
        current_idx = len(self)
        if current_idx < 65:
            return
        
        for data in self.datas:
            symbol = data._name
            pos = self.getposition(data)
            
            if pos.size > 0:
                close = data.close[0]
                if symbol in self.max_prices:
                    self.max_prices[symbol] = max(self.max_prices[symbol], close)
                else:
                    self.max_prices[symbol] = close
                
                max_price = self.max_prices.get(symbol, close)
                drawdown = (max_price - close) / max_price if max_price > 0 else 0
                
                sma20 = self.inds[symbol]['sma20'][0]
                
                if drawdown > 0.20 and close < sma20:
                    self.close(data)
                    if symbol in self.entry_prices:
                        del self.entry_prices[symbol]
                    if symbol in self.max_prices:
                        del self.max_prices[symbol]
        
        if self.last_rebalance >= 0 and current_idx - self.last_rebalance < self.params.rebalance_days:
            return
        self.last_rebalance = current_idx
        
        has_position = any(self.getposition(data).size > 0 for data in self.datas)
        if has_position:
            return
        
        momentum_list = []
        for i, data in enumerate(self.datas):
            symbol = data._name
            ind = self.inds[symbol]
            mom10, mom20, mom60 = ind['mom10'][0], ind['mom20'][0], ind['mom60'][0]
            sma20, sma50 = ind['sma20'][0], ind['sma50'][0]
            highest_20 = ind['highest_20'][0]
            close = data.close[0]
            
            if any(np.isnan(x) for x in [mom10, mom20, mom60, sma20]):
                continue
            
            score = mom10 * 0.3 + mom20 * 0.3 + mom60 * 0.4
            if close >= highest_20:
                score += 0.05
            elif close >= highest_20 * 0.95:
                score += 0.03
            if close > sma20:
                score += 0.02
            if close > sma50:
                score += 0.02
            
            momentum_list.append((symbol, score, data))
        
        if not momentum_list:
            return
        
        momentum_list.sort(key=lambda x: x[1], reverse=True)
        best_stock = momentum_list[0][0]
        
        for data in self.datas:
            if data._name == best_stock:
                if self.getposition(data).size == 0:
                    size = int(self.broker.getvalue() * 0.98 / data.close[0])
                    if size > 0:
                        self.buy(data, size=size)
                        self.entry_prices[best_stock] = data.close[0]
                        self.max_prices[best_stock] = data.close[0]
                break
    
    def notify_order(self, order):
        pass


class WinnerV3Strategy(bt.Strategy):
    params = (
        ('rebalance_days', 5),
    )
    
    def __init__(self):
        self.last_rebalance = -1
        self.inds = {}
        
        for i, data in enumerate(self.datas):
            symbol = data._name
            self.inds[symbol] = {}
            self.inds[symbol]['mom10'] = bt.indicators.Momentum(data.close, period=10)
            self.inds[symbol]['mom20'] = bt.indicators.Momentum(data.close, period=20)
            self.inds[symbol]['sma20'] = bt.indicators.SMA(data.close, period=20)
            self.inds[symbol]['highest_20'] = bt.indicators.Highest(data.high, period=20)
    
    def next(self):
        current_idx = len(self)
        if current_idx < 25:
            return
        if self.last_rebalance >= 0 and current_idx - self.last_rebalance < self.params.rebalance_days:
            return
        self.last_rebalance = current_idx
        
        momentum_list = []
        for i, data in enumerate(self.datas):
            symbol = data._name
            ind = self.inds[symbol]
            mom10 = ind['mom10'][0]
            mom20 = ind['mom20'][0]
            sma20 = ind['sma20'][0]
            highest_20 = ind['highest_20'][0]
            close = data.close[0]
            
            if any(np.isnan(x) for x in [mom10, mom20, sma20]):
                continue
            
            score = mom10 * 0.5 + mom20 * 0.5
            if close >= highest_20:
                score += 0.05
            elif close >= highest_20 * 0.95:
                score += 0.03
            if close > sma20:
                score += 0.02
            
            momentum_list.append((symbol, score, data))
        
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


class WinnerV4Strategy(bt.Strategy):
    params = (
        ('rebalance_days', 5),
    )
    
    def __init__(self):
        self.last_rebalance = -1
        self.inds = {}
        self.entry_prices = {}
        self.max_prices = {}
        
        for i, data in enumerate(self.datas):
            symbol = data._name
            self.inds[symbol] = {}
            self.inds[symbol]['mom10'] = bt.indicators.Momentum(data.close, period=10)
            self.inds[symbol]['mom20'] = bt.indicators.Momentum(data.close, period=20)
            self.inds[symbol]['sma20'] = bt.indicators.SMA(data.close, period=20)
            self.inds[symbol]['highest_20'] = bt.indicators.Highest(data.high, period=20)
    
    def next(self):
        current_idx = len(self)
        if current_idx < 25:
            return
        
        for data in self.datas:
            symbol = data._name
            pos = self.getposition(data)
            
            if pos.size > 0:
                close = data.close[0]
                if symbol in self.max_prices:
                    self.max_prices[symbol] = max(self.max_prices[symbol], close)
                else:
                    self.max_prices[symbol] = close
                
                max_price = self.max_prices.get(symbol, close)
                drawdown = (max_price - close) / max_price if max_price > 0 else 0
                
                sma20 = self.inds[symbol]['sma20'][0]
                
                if drawdown > 0.15 and close < sma20:
                    self.close(data)
                    if symbol in self.entry_prices:
                        del self.entry_prices[symbol]
                    if symbol in self.max_prices:
                        del self.max_prices[symbol]
        
        if self.last_rebalance >= 0 and current_idx - self.last_rebalance < self.params.rebalance_days:
            return
        self.last_rebalance = current_idx
        
        has_position = any(self.getposition(data).size > 0 for data in self.datas)
        if has_position:
            return
        
        momentum_list = []
        for i, data in enumerate(self.datas):
            symbol = data._name
            ind = self.inds[symbol]
            mom10 = ind['mom10'][0]
            mom20 = ind['mom20'][0]
            sma20 = ind['sma20'][0]
            highest_20 = ind['highest_20'][0]
            close = data.close[0]
            
            if any(np.isnan(x) for x in [mom10, mom20, sma20]):
                continue
            
            score = mom10 * 0.5 + mom20 * 0.5
            if close >= highest_20:
                score += 0.05
            elif close >= highest_20 * 0.95:
                score += 0.03
            if close > sma20:
                score += 0.02
            
            momentum_list.append((symbol, score, data))
        
        if not momentum_list:
            return
        
        momentum_list.sort(key=lambda x: x[1], reverse=True)
        best_stock = momentum_list[0][0]
        
        for data in self.datas:
            if data._name == best_stock:
                if self.getposition(data).size == 0:
                    size = int(self.broker.getvalue() * 0.98 / data.close[0])
                    if size > 0:
                        self.buy(data, size=size)
                        self.entry_prices[best_stock] = data.close[0]
                        self.max_prices[best_stock] = data.close[0]
                break
    
    def notify_order(self, order):
        pass


class WinnerV5Strategy(bt.Strategy):
    params = (
        ('rebalance_days', 5),
    )
    
    def __init__(self):
        self.last_rebalance = -1
        self.inds = {}
        self.entry_prices = {}
        self.max_prices = {}
        self.hold_days = {}
        
        for i, data in enumerate(self.datas):
            symbol = data._name
            self.inds[symbol] = {}
            self.inds[symbol]['mom10'] = bt.indicators.Momentum(data.close, period=10)
            self.inds[symbol]['mom20'] = bt.indicators.Momentum(data.close, period=20)
            self.inds[symbol]['sma20'] = bt.indicators.SMA(data.close, period=20)
            self.inds[symbol]['highest_20'] = bt.indicators.Highest(data.high, period=20)
            self.inds[symbol]['highest_60'] = bt.indicators.Highest(data.high, period=60)
    
    def next(self):
        current_idx = len(self)
        if current_idx < 65:
            return
        
        for data in self.datas:
            symbol = data._name
            pos = self.getposition(data)
            
            if pos.size > 0:
                self.hold_days[symbol] = self.hold_days.get(symbol, 0) + 1
                
                close = data.close[0]
                if symbol in self.max_prices:
                    self.max_prices[symbol] = max(self.max_prices[symbol], close)
                else:
                    self.max_prices[symbol] = close
                
                max_price = self.max_prices.get(symbol, close)
                drawdown = (max_price - close) / max_price if max_price > 0 else 0
                
                sma20 = self.inds[symbol]['sma20'][0]
                mom10 = self.inds[symbol]['mom10'][0]
                
                if drawdown > 0.12 and close < sma20 and mom10 < 0:
                    self.close(data)
                    if symbol in self.entry_prices:
                        del self.entry_prices[symbol]
                    if symbol in self.max_prices:
                        del self.max_prices[symbol]
                    if symbol in self.hold_days:
                        del self.hold_days[symbol]
        
        if self.last_rebalance >= 0 and current_idx - self.last_rebalance < self.params.rebalance_days:
            return
        self.last_rebalance = current_idx
        
        has_position = any(self.getposition(data).size > 0 for data in self.datas)
        if has_position:
            return
        
        momentum_list = []
        for i, data in enumerate(self.datas):
            symbol = data._name
            ind = self.inds[symbol]
            mom10 = ind['mom10'][0]
            mom20 = ind['mom20'][0]
            sma20 = ind['sma20'][0]
            highest_20 = ind['highest_20'][0]
            highest_60 = ind['highest_60'][0]
            close = data.close[0]
            
            if any(np.isnan(x) for x in [mom10, mom20, sma20]):
                continue
            
            score = mom10 * 0.4 + mom20 * 0.6
            
            if close >= highest_20:
                score += 0.08
            elif close >= highest_20 * 0.95:
                score += 0.04
            
            if close >= highest_60:
                score += 0.05
            
            if close > sma20:
                score += 0.02
            
            momentum_list.append((symbol, score, data))
        
        if not momentum_list:
            return
        
        momentum_list.sort(key=lambda x: x[1], reverse=True)
        best_stock = momentum_list[0][0]
        
        for data in self.datas:
            if data._name == best_stock:
                if self.getposition(data).size == 0:
                    size = int(self.broker.getvalue() * 0.98 / data.close[0])
                    if size > 0:
                        self.buy(data, size=size)
                        self.entry_prices[best_stock] = data.close[0]
                        self.max_prices[best_stock] = data.close[0]
                        self.hold_days[best_stock] = 0
                break
    
    def notify_order(self, order):
        pass
