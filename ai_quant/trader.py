"""Schwab交易执行模块"""
import schwabdev
from typing import Dict, Any, Optional, List
from datetime import datetime, time
import time as time_module
from ai_quant.config import SCHWAB_APP_KEY, SCHWAB_APP_SECRET, STOCKS, MAX_DAY_TRADES


class SchwabTrader:
    """Schwab交易执行类"""

    def __init__(self, app_key: str = None, app_secret: str = None):
        self.app_key = app_key or SCHWAB_APP_KEY
        self.app_secret = app_secret or SCHWAB_APP_SECRET
        self.client = None
        self._day_trades = 0
        self._last_reset_date = None
        self._init_client()

    def _init_client(self):
        """初始化Schwab客户端"""
        if not self.app_key or not self.app_secret:
            print("警告: Schwabb API密钥未配置，将以模拟模式运行")
            self.client = None
            return

        try:
            self.client = schwabdev.Client(self.app_key, self.app_secret)
            print("Schwab API连接成功")
        except Exception as e:
            print(f"Schwab API连接失败: {e}")
            self.client = None

    def _reset_day_trades(self):
        """重置每日交易次数"""
        today = datetime.now().date()
        if self._last_reset_date != today:
            self._day_trades = 0
            self._last_reset_date = today
            print(f"新的一天({today})，重置日内交易次数")

    def can_trade(self) -> bool:
        """检查是否可以交易"""
        self._reset_day_trades()
        return self._day_trades < MAX_DAY_TRADES

    def get_remaining_trades(self) -> int:
        """获取剩余交易次数"""
        self._reset_day_trades()
        return MAX_DAY_TRADES - self._day_trades

    def get_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """获取股票报价"""
        if not self.client:
            return self._simulate_quote(symbol)

        try:
            response = self.client.quote(symbol_id=symbol, fields="quote")
            if response.ok:
                return response.json().get(symbol, {})
            else:
                print(f"获取报价失败: {response.status_code}")
                return None
        except Exception as e:
            print(f"获取报价异常: {e}")
            return None

    def _simulate_quote(self, symbol: str) -> Dict[str, Any]:
        """模拟报价（API未配置时使用）"""
        import random
        base_prices = {
            "NVDA": 500.0,
            "TSLA": 250.0,
            "AAPL": 180.0
        }
        base = base_prices.get(symbol, 100.0)
        return {
            "symbol": symbol,
            "lastPrice": base * random.uniform(0.95, 1.05),
            "openPrice": base,
            "highPrice": base * 1.02,
            "lowPrice": base * 0.98,
            "volume": random.randint(1000000, 10000000)
        }

    def get_account_info(self) -> Optional[Dict[str, Any]]:
        """获取账户信息"""
        if not self.client:
            return {"cashBalance": 100000.0, "buyingPower": 100000.0}

        try:
            response = self.client.account_linked()
            if response.ok:
                accounts = response.json()
                if accounts:
                    return accounts[0]
            return None
        except Exception as e:
            print(f"获取账户信息异常: {e}")
            return None

    def place_order(
        self,
        symbol: str,
        quantity: int,
        side: str = "buy",
        order_type: str = "market",
        limit_price: float = None
    ) -> Optional[Dict[str, Any]]:
        """下单

        Args:
            symbol: 股票代码 (如 NVDA)
            quantity: 数量
            side: buy 或 sell
            order_type: market 或 limit
            limit_price: 限价（仅限价单需要）

        Returns:
            订单结果
        """
        if not self.can_trade():
            print(f"已达到今日最大交易次数({MAX_DAY_TRADES})")
            return None

        if not self.client:
            print(f"[模拟] {'买入' if side == 'buy' else '卖出'} {symbol} x {quantity}")
            self._day_trades += 1
            return {"status": "simulated", "symbol": symbol, "side": side}

        try:
            order = {
                "symbol": symbol,
                "quantity": quantity,
                "side": side,
                "type": order_type
            }

            if order_type == "limit" and limit_price:
                order["limitPrice"] = limit_price

            response = self.client.place_order(account_number=None, order=order)

            if response.ok:
                self._day_trades += 1
                print(f"下单成功: {side} {symbol} x {quantity}")
                return response.json()
            else:
                print(f"下单失败: {response.status_code}")
                return None

        except Exception as e:
            print(f"下单异常: {e}")
            return None

    def buy_market(self, symbol: str, quantity: int) -> Optional[Dict[str, Any]]:
        """市价买入"""
        return self.place_order(symbol, quantity, side="buy", order_type="market")

    def sell_market(self, symbol: str, quantity: int) -> Optional[Dict[str, Any]]:
        """市价卖出"""
        return self.place_order(symbol, quantity, side="sell", order_type="market")

    def buy_limit(self, symbol: str, quantity: int, limit_price: float) -> Optional[Dict[str, Any]]:
        """限价买入"""
        return self.place_order(symbol, quantity, side="buy", order_type="limit", limit_price=limit_price)

    def get_positions(self) -> List[Dict[str, Any]]:
        """获取当前持仓"""
        if not self.client:
            return []

        try:
            response = self.client.account_linked()
            if response.ok:
                accounts = response.json()
                if accounts and "positions" in accounts[0]:
                    return accounts[0]["positions"]
            return []
        except Exception as e:
            print(f"获取持仓异常: {e}")
            return []

    def get_position(self, symbol: str) -> Optional[Dict[str, Any]]:
        """获取指定股票持仓"""
        positions = self.get_positions()
        for pos in positions:
            if pos.get("symbol") == symbol:
                return pos
        return None


def test_schwab_trader():
    """测试Schwab交易"""
    trader = SchwabTrader()

    print("\n=== 账户信息 ===")
    account = trader.get_account_info()
    print(account)

    print("\n=== 报价查询 ===")
    for symbol in STOCKS.keys():
        quote = trader.get_quote(symbol)
        print(f"{symbol}: ${quote.get('lastPrice', 'N/A')}")

    print(f"\n=== 交易次数 ===")
    print(f"剩余交易次数: {trader.get_remaining_trades()}")


if __name__ == "__main__":
    test_schwab_trader()
