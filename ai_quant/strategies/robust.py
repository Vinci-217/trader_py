import backtrader as bt
import pandas as pd
import numpy as np
from collections import deque


class RobustGrowthStrategy(bt.Strategy):
    params = (
        ('rebalance_days', 5),
    )
    
    def __init__(self):
        self.last_rebalance = -1
        self.inds = {}
        self.entry_prices = {}
        self.max_prices = {}
        self.market_state = 'neutral'
        
        for i, data in enumerate(self.datas):
            symbol = data._name
            self.inds[symbol] = {}
            self.inds[symbol]['mom5'] = bt.indicators.Momentum(data.close, period=5)
            self.inds[symbol]['mom10'] = bt.indicators.Momentum(data.close, period=10)
            self.inds[symbol]['mom20'] = bt.indicators.Momentum(data.close, period=20)
            self.inds[symbol]['roc10'] = bt.indicators.ROC(data.close, period=10)
            self.inds[symbol]['rsi'] = bt.indicators.RSI(data.close, period=14)
            self.inds[symbol]['sma10'] = bt.indicators.SMA(data.close, period=10)
            self.inds[symbol]['sma20'] = bt.indicators.SMA(data.close, period=20)
            self.inds[symbol]['sma50'] = bt.indicators.SMA(data.close, period=50)
            self.inds[symbol]['highest_10'] = bt.indicators.Highest(data.high, period=10)
            self.inds[symbol]['highest_20'] = bt.indicators.Highest(data.high, period=20)
    
    def get_market_state(self):
        bullish = 0
        bearish = 0
        total = 0
        
        for data in self.datas:
            ind = self.inds[data._name]
            sma20 = ind['sma20'][0]
            sma50 = ind['sma50'][0]
            close = data.close[0]
            mom20 = ind['mom20'][0]
            
            if np.isnan(sma20) or np.isnan(sma50):
                continue
            
            if close > sma20 and sma20 > sma50 and mom20 > 0:
                bullish += 1
            elif close < sma20 and sma20 < sma50:
                bearish += 1
            total += 1
        
        if total == 0:
            return 'neutral'
        
        if bearish >= total * 0.6:
            return 'bear'
        elif bullish >= total * 0.5:
            return 'bull'
        else:
            return 'neutral'
    
    def next(self):
        current_idx = len(self)
        if current_idx < 30:
            return
        
        self.market_state = self.get_market_state()
        
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
                
                sma10 = self.inds[symbol]['sma10'][0]
                mom5 = self.inds[symbol]['mom5'][0]
                
                if self.market_state == 'bear':
                    if drawdown > 0.08:
                        self.close(data)
                        if symbol in self.entry_prices:
                            del self.entry_prices[symbol]
                        if symbol in self.max_prices:
                            del self.max_prices[symbol]
                else:
                    if drawdown > 0.15 and close < sma10 and mom5 < 0:
                        self.close(data)
                        if symbol in self.entry_prices:
                            del self.entry_prices[symbol]
                        if symbol in self.max_prices:
                            del self.max_prices[symbol]
        
        if self.last_rebalance >= 0 and current_idx - self.last_rebalance < self.params.rebalance_days:
            return
        self.last_rebalance = current_idx
        
        if self.market_state == 'bear':
            return
        
        scores = []
        for data in self.datas:
            symbol = data._name
            ind = self.inds[symbol]
            
            mom5 = ind['mom5'][0]
            mom10 = ind['mom10'][0]
            mom20 = ind['mom20'][0]
            roc10 = ind['roc10'][0]
            rsi = ind['rsi'][0]
            sma10 = ind['sma10'][0]
            sma20 = ind['sma20'][0]
            sma50 = ind['sma50'][0]
            highest_10 = ind['highest_10'][0]
            highest_20 = ind['highest_20'][0]
            close = data.close[0]
            
            if any(np.isnan(x) for x in [mom5, mom10, sma10, sma20]):
                continue
            
            if close < sma20:
                continue
            
            score = 0
            
            score += mom5 * 0.25
            score += mom10 * 0.25
            score += mom20 * 0.15
            score += roc10 * 0.002
            
            if close >= highest_10:
                score += 0.12
            elif close >= highest_10 * 0.97:
                score += 0.06
            
            if close >= highest_20:
                score += 0.06
            
            if close > sma10 and sma10 > sma20:
                score += 0.04
            
            if sma20 > sma50:
                score += 0.03
            
            if 45 < rsi < 70:
                score += 0.02
            
            scores.append((symbol, score, data))
        
        if not scores:
            return
        
        scores.sort(key=lambda x: x[1], reverse=True)
        
        if self.market_state == 'bull':
            n_stocks = 3
            cash_pct = 0.95
        else:
            n_stocks = 2
            cash_pct = 0.80
        
        top_stocks = [s[0] for s in scores[:n_stocks]]
        
        for data in self.datas:
            symbol = data._name
            pos = self.getposition(data)
            if pos.size > 0 and symbol not in top_stocks:
                self.close(data)
                if symbol in self.entry_prices:
                    del self.entry_prices[symbol]
                if symbol in self.max_prices:
                    del self.max_prices[symbol]
        
        current_positions = sum(1 for data in self.datas if self.getposition(data).size > 0)
        positions_to_add = n_stocks - current_positions
        
        if positions_to_add > 0:
            available_cash = self.broker.getvalue() * cash_pct
            per_stock_cash = available_cash / n_stocks
            
            for symbol, score, data in scores[:n_stocks]:
                if self.getposition(data).size == 0 and positions_to_add > 0:
                    size = int(per_stock_cash / data.close[0])
                    if size > 0:
                        self.buy(data, size=size)
                        self.entry_prices[symbol] = data.close[0]
                        self.max_prices[symbol] = data.close[0]
                        positions_to_add -= 1
    
    def notify_order(self, order):
        pass


class DefensiveStrategy(bt.Strategy):
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
            self.inds[symbol]['mom5'] = bt.indicators.Momentum(data.close, period=5)
            self.inds[symbol]['mom10'] = bt.indicators.Momentum(data.close, period=10)
            self.inds[symbol]['mom20'] = bt.indicators.Momentum(data.close, period=20)
            self.inds[symbol]['roc10'] = bt.indicators.ROC(data.close, period=10)
            self.inds[symbol]['rsi'] = bt.indicators.RSI(data.close, period=14)
            self.inds[symbol]['sma10'] = bt.indicators.SMA(data.close, period=10)
            self.inds[symbol]['sma20'] = bt.indicators.SMA(data.close, period=20)
            self.inds[symbol]['sma50'] = bt.indicators.SMA(data.close, period=50)
            self.inds[symbol]['highest_10'] = bt.indicators.Highest(data.high, period=10)
    
    def next(self):
        current_idx = len(self)
        if current_idx < 30:
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
                
                sma10 = self.inds[symbol]['sma10'][0]
                mom5 = self.inds[symbol]['mom5'][0]
                
                if drawdown > 0.12 and close < sma10:
                    self.close(data)
                    if symbol in self.entry_prices:
                        del self.entry_prices[symbol]
                    if symbol in self.max_prices:
                        del self.max_prices[symbol]
        
        if self.last_rebalance >= 0 and current_idx - self.last_rebalance < self.params.rebalance_days:
            return
        self.last_rebalance = current_idx
        
        scores = []
        for data in self.datas:
            symbol = data._name
            ind = self.inds[symbol]
            
            mom5 = ind['mom5'][0]
            mom10 = ind['mom10'][0]
            mom20 = ind['mom20'][0]
            roc10 = ind['roc10'][0]
            rsi = ind['rsi'][0]
            sma10 = ind['sma10'][0]
            sma20 = ind['sma20'][0]
            sma50 = ind['sma50'][0]
            highest_10 = ind['highest_10'][0]
            close = data.close[0]
            
            if any(np.isnan(x) for x in [mom5, mom10, sma10, sma20, sma50]):
                continue
            
            if close < sma20 or close < sma50:
                continue
            
            if mom20 < 0:
                continue
            
            score = 0
            
            score += mom5 * 0.20
            score += mom10 * 0.20
            score += mom20 * 0.15
            score += roc10 * 0.002
            
            if close >= highest_10:
                score += 0.10
            elif close >= highest_10 * 0.97:
                score += 0.05
            
            if close > sma10 and sma10 > sma20 and sma20 > sma50:
                score += 0.06
            
            if 40 < rsi < 65:
                score += 0.02
            
            scores.append((symbol, score, data))
        
        if not scores:
            return
        
        scores.sort(key=lambda x: x[1], reverse=True)
        
        n_stocks = min(3, len(scores))
        top_stocks = [s[0] for s in scores[:n_stocks]]
        
        for data in self.datas:
            symbol = data._name
            pos = self.getposition(data)
            if pos.size > 0 and symbol not in top_stocks:
                self.close(data)
                if symbol in self.entry_prices:
                    del self.entry_prices[symbol]
                if symbol in self.max_prices:
                    del self.max_prices[symbol]
        
        current_positions = sum(1 for data in self.datas if self.getposition(data).size > 0)
        positions_to_add = n_stocks - current_positions
        
        if positions_to_add > 0:
            available_cash = self.broker.getvalue() * 0.70
            per_stock_cash = available_cash / n_stocks
            
            for symbol, score, data in scores[:n_stocks]:
                if self.getposition(data).size == 0 and positions_to_add > 0:
                    size = int(per_stock_cash / data.close[0])
                    if size > 0:
                        self.buy(data, size=size)
                        self.entry_prices[symbol] = data.close[0]
                        self.max_prices[symbol] = data.close[0]
                        positions_to_add -= 1
    
    def notify_order(self, order):
        pass


class BalancedGrowthStrategy(bt.Strategy):
    params = (
        ('rebalance_days', 5),
    )
    
    def __init__(self):
        self.last_rebalance = -1
        self.inds = {}
        self.entry_prices = {}
        self.max_prices = {}
        self.bear_count = 0
        
        for i, data in enumerate(self.datas):
            symbol = data._name
            self.inds[symbol] = {}
            self.inds[symbol]['mom5'] = bt.indicators.Momentum(data.close, period=5)
            self.inds[symbol]['mom10'] = bt.indicators.Momentum(data.close, period=10)
            self.inds[symbol]['mom20'] = bt.indicators.Momentum(data.close, period=20)
            self.inds[symbol]['roc10'] = bt.indicators.ROC(data.close, period=10)
            self.inds[symbol]['rsi'] = bt.indicators.RSI(data.close, period=14)
            self.inds[symbol]['sma10'] = bt.indicators.SMA(data.close, period=10)
            self.inds[symbol]['sma20'] = bt.indicators.SMA(data.close, period=20)
            self.inds[symbol]['sma50'] = bt.indicators.SMA(data.close, period=50)
            self.inds[symbol]['highest_10'] = bt.indicators.Highest(data.high, period=10)
            self.inds[symbol]['highest_20'] = bt.indicators.Highest(data.high, period=20)
    
    def next(self):
        current_idx = len(self)
        if current_idx < 30:
            return
        
        bear_signals = 0
        total_signals = 0
        
        for data in self.datas:
            ind = self.inds[data._name]
            sma20 = ind['sma20'][0]
            sma50 = ind['sma50'][0]
            close = data.close[0]
            mom20 = ind['mom20'][0]
            
            if not np.isnan(sma20) and not np.isnan(sma50):
                if close < sma20 and sma20 < sma50:
                    bear_signals += 1
                total_signals += 1
        
        bear_ratio = bear_signals / total_signals if total_signals > 0 else 0
        
        if bear_ratio >= 0.5:
            self.bear_count += 1
        else:
            self.bear_count = max(0, self.bear_count - 1)
        
        in_bear_market = self.bear_count >= 3
        
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
                
                sma10 = self.inds[symbol]['sma10'][0]
                mom5 = self.inds[symbol]['mom5'][0]
                
                if in_bear_market:
                    if drawdown > 0.08:
                        self.close(data)
                        if symbol in self.entry_prices:
                            del self.entry_prices[symbol]
                        if symbol in self.max_prices:
                            del self.max_prices[symbol]
                else:
                    if drawdown > 0.15 and close < sma10:
                        self.close(data)
                        if symbol in self.entry_prices:
                            del self.entry_prices[symbol]
                        if symbol in self.max_prices:
                            del self.max_prices[symbol]
        
        if self.last_rebalance >= 0 and current_idx - self.last_rebalance < self.params.rebalance_days:
            return
        self.last_rebalance = current_idx
        
        if in_bear_market:
            return
        
        scores = []
        for data in self.datas:
            symbol = data._name
            ind = self.inds[symbol]
            
            mom5 = ind['mom5'][0]
            mom10 = ind['mom10'][0]
            mom20 = ind['mom20'][0]
            roc10 = ind['roc10'][0]
            rsi = ind['rsi'][0]
            sma10 = ind['sma10'][0]
            sma20 = ind['sma20'][0]
            sma50 = ind['sma50'][0]
            highest_10 = ind['highest_10'][0]
            highest_20 = ind['highest_20'][0]
            close = data.close[0]
            
            if any(np.isnan(x) for x in [mom5, mom10, sma10]):
                continue
            
            score = 0
            
            score += mom5 * 0.25
            score += mom10 * 0.25
            score += mom20 * 0.15
            score += roc10 * 0.002
            
            if close >= highest_10:
                score += 0.12
            elif close >= highest_10 * 0.97:
                score += 0.06
            
            if close >= highest_20:
                score += 0.06
            
            if close > sma10 and sma10 > sma20:
                score += 0.04
            
            if sma20 > sma50:
                score += 0.03
            
            if 45 < rsi < 70:
                score += 0.02
            
            scores.append((symbol, score, data))
        
        if not scores:
            return
        
        scores.sort(key=lambda x: x[1], reverse=True)
        
        n_stocks = 3
        top_stocks = [s[0] for s in scores[:n_stocks]]
        
        for data in self.datas:
            symbol = data._name
            pos = self.getposition(data)
            if pos.size > 0 and symbol not in top_stocks:
                self.close(data)
                if symbol in self.entry_prices:
                    del self.entry_prices[symbol]
                if symbol in self.max_prices:
                    del self.max_prices[symbol]
        
        current_positions = sum(1 for data in self.datas if self.getposition(data).size > 0)
        positions_to_add = n_stocks - current_positions
        
        if positions_to_add > 0:
            available_cash = self.broker.getvalue() * 0.85
            per_stock_cash = available_cash / n_stocks
            
            for symbol, score, data in scores[:n_stocks]:
                if self.getposition(data).size == 0 and positions_to_add > 0:
                    size = int(per_stock_cash / data.close[0])
                    if size > 0:
                        self.buy(data, size=size)
                        self.entry_prices[symbol] = data.close[0]
                        self.max_prices[symbol] = data.close[0]
                        positions_to_add -= 1
    
    def notify_order(self, order):
        pass


class ConservativeStrategy(bt.Strategy):
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
            self.inds[symbol]['roc10'] = bt.indicators.ROC(data.close, period=10)
            self.inds[symbol]['rsi'] = bt.indicators.RSI(data.close, period=14)
            self.inds[symbol]['sma20'] = bt.indicators.SMA(data.close, period=20)
            self.inds[symbol]['sma50'] = bt.indicators.SMA(data.close, period=50)
            self.inds[symbol]['highest_20'] = bt.indicators.Highest(data.high, period=20)
    
    def next(self):
        current_idx = len(self)
        if current_idx < 50:
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
                mom10 = self.inds[symbol]['mom10'][0]
                
                if drawdown > 0.10 and close < sma20:
                    self.close(data)
                    if symbol in self.entry_prices:
                        del self.entry_prices[symbol]
                    if symbol in self.max_prices:
                        del self.max_prices[symbol]
        
        if self.last_rebalance >= 0 and current_idx - self.last_rebalance < self.params.rebalance_days:
            return
        self.last_rebalance = current_idx
        
        scores = []
        for data in self.datas:
            symbol = data._name
            ind = self.inds[symbol]
            
            mom10 = ind['mom10'][0]
            mom20 = ind['mom20'][0]
            roc10 = ind['roc10'][0]
            rsi = ind['rsi'][0]
            sma20 = ind['sma20'][0]
            sma50 = ind['sma50'][0]
            highest_20 = ind['highest_20'][0]
            close = data.close[0]
            
            if any(np.isnan(x) for x in [mom10, mom20, sma20, sma50]):
                continue
            
            if close < sma20 or close < sma50:
                continue
            
            if mom20 < 0:
                continue
            
            score = 0
            
            score += mom10 * 0.25
            score += mom20 * 0.25
            score += roc10 * 0.002
            
            if close >= highest_20:
                score += 0.10
            elif close >= highest_20 * 0.95:
                score += 0.05
            
            if sma20 > sma50:
                score += 0.05
            
            if 40 < rsi < 60:
                score += 0.02
            
            scores.append((symbol, score, data))
        
        if not scores:
            return
        
        scores.sort(key=lambda x: x[1], reverse=True)
        
        n_stocks = min(2, len(scores))
        top_stocks = [s[0] for s in scores[:n_stocks]]
        
        for data in self.datas:
            symbol = data._name
            pos = self.getposition(data)
            if pos.size > 0 and symbol not in top_stocks:
                self.close(data)
                if symbol in self.entry_prices:
                    del self.entry_prices[symbol]
                if symbol in self.max_prices:
                    del self.max_prices[symbol]
        
        current_positions = sum(1 for data in self.datas if self.getposition(data).size > 0)
        positions_to_add = n_stocks - current_positions
        
        if positions_to_add > 0:
            available_cash = self.broker.getvalue() * 0.60
            per_stock_cash = available_cash / n_stocks
            
            for symbol, score, data in scores[:n_stocks]:
                if self.getposition(data).size == 0 and positions_to_add > 0:
                    size = int(per_stock_cash / data.close[0])
                    if size > 0:
                        self.buy(data, size=size)
                        self.entry_prices[symbol] = data.close[0]
                        self.max_prices[symbol] = data.close[0]
                        positions_to_add -= 1
    
    def notify_order(self, order):
        pass
