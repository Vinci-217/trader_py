"""
Schwab API Client
==================
对接Charles Schwab交易API的客户端模块

使用schwab-py库: https://github.com/alexgolec/schwab-py

安装: pip install schwab-py
"""

import os
import json
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from pathlib import Path


class SchwabClient:
    """
    Schwab API客户端
    
    使用前需要:
    1. 在Schwab Developer Portal注册应用: https://developer.schwab.com/
    2. 获取App Key和Secret
    3. 设置回调URL
    4. 完成OAuth认证流程
    """
    
    def __init__(
        self,
        app_key: Optional[str] = None,
        app_secret: Optional[str] = None,
        callback_url: Optional[str] = None,
        token_path: Optional[str] = None,
        sandbox: bool = True
    ):
        """
        初始化Schwab客户端
        
        Args:
            app_key: Schwab应用Key (也可通过SCHWAB_APP_KEY环境变量设置)
            app_secret: Schwab应用Secret (也可通过SCHWAB_APP_SECRET环境变量设置)
            callback_url: OAuth回调URL (也可通过SCHWAB_CALLBACK_URL环境变量设置)
            token_path: Token存储路径
            sandbox: 是否使用沙盒环境
        """
        self.app_key = app_key or os.environ.get('SCHWAB_APP_KEY')
        self.app_secret = app_secret or os.environ.get('SCHWAB_APP_SECRET')
        self.callback_url = callback_url or os.environ.get('SCHWAB_CALLBACK_URL', 'https://127.0.0.1')
        self.sandbox = sandbox
        self.token_path = token_path or str(Path.home() / '.schwab' / 'token.json')
        
        self._client = None
        self._authenticated = False
    
    def _get_client(self):
        """获取或创建Schwab客户端实例"""
        if self._client is not None:
            return self._client
        
        try:
            from schwab.auth import client_from_token_file
            from schwab.auth import client_from_login_flow
            
            token_path = Path(self.token_path)
            token_path.parent.mkdir(parents=True, exist_ok=True)
            
            if token_path.exists():
                self._client = client_from_token_file(
                    token_path,
                    self.app_key,
                    self.app_secret,
                    sandbox=self.sandbox
                )
                self._authenticated = True
            else:
                print(f"Token文件不存在: {token_path}")
                print("请先运行认证流程: client.authenticate()")
            
            return self._client
            
        except ImportError:
            raise ImportError(
                "请安装schwab库: pip install schwab-py\n"
                "文档: https://github.com/alexgolec/schwab-py"
            )
    
    def authenticate(self, timeout: int = 300):
        """
        执行OAuth认证流程
        
        Args:
            timeout: 认证超时时间(秒)
        """
        try:
            from schwab.auth import client_from_login_flow
            
            print("=" * 60)
            print("Schwab OAuth认证流程")
            print("=" * 60)
            print(f"1. 将在浏览器中打开Schwab登录页面")
            print(f"2. 请登录您的Schwab账户")
            print(f"3. 授权应用访问")
            print(f"4. 认证成功后将自动返回")
            print("=" * 60)
            
            token_path = Path(self.token_path)
            token_path.parent.mkdir(parents=True, exist_ok=True)
            
            self._client = client_from_login_flow(
                self.app_key,
                self.app_secret,
                self.callback_url,
                token_path,
                sandbox=self.sandbox
            )
            
            self._authenticated = True
            print("认证成功!")
            return True
            
        except Exception as e:
            print(f"认证失败: {e}")
            return False
    
    def is_authenticated(self) -> bool:
        """检查是否已认证"""
        return self._authenticated
    
    def get_account_info(self) -> Dict[str, Any]:
        """
        获取账户信息
        
        Returns:
            账户信息字典
        """
        client = self._get_client()
        if client is None:
            return {}
        
        try:
            response = client.get_account_numbers()
            if response.status_code == 200:
                return response.json()
            else:
                print(f"获取账户信息失败: {response.status_code}")
                return {}
        except Exception as e:
            print(f"获取账户信息异常: {e}")
            return {}
    
    def get_positions(self, account_hash: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取持仓信息
        
        Args:
            account_hash: 账户哈希值 (可选，默认获取第一个账户)
        
        Returns:
            持仓列表
        """
        client = self._get_client()
        if client is None:
            return []
        
        try:
            if account_hash is None:
                accounts = self.get_account_info()
                if accounts:
                    account_hash = accounts[0].get('hashValue')
            
            if account_hash is None:
                print("无法获取账户哈希值")
                return []
            
            response = client.get_account_positions(account_hash)
            if response.status_code == 200:
                data = response.json()
                return data.get('securitiesAccount', {}).get('positions', [])
            else:
                print(f"获取持仓失败: {response.status_code}")
                return []
        except Exception as e:
            print(f"获取持仓异常: {e}")
            return []
    
    def get_quote(self, symbol: str) -> Dict[str, Any]:
        """
        获取股票报价
        
        Args:
            symbol: 股票代码
        
        Returns:
            报价信息
        """
        client = self._get_client()
        if client is None:
            return {}
        
        try:
            response = client.get_quote(symbol)
            if response.status_code == 200:
                data = response.json()
                return data.get(symbol, {})
            else:
                print(f"获取报价失败: {response.status_code}")
                return {}
        except Exception as e:
            print(f"获取报价异常: {e}")
            return {}
    
    def get_price_history(
        self,
        symbol: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        period_type: str = 'year',
        frequency_type: str = 'daily',
        frequency: int = 1
    ) -> List[Dict[str, Any]]:
        """
        获取历史价格数据
        
        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            period_type: 周期类型 ('day', 'month', 'year', 'ytd')
            frequency_type: 频率类型 ('minute', 'daily', 'weekly', 'monthly')
            frequency: 频率
        
        Returns:
            历史价格列表
        """
        client = self._get_client()
        if client is None:
            return []
        
        try:
            from schwab.orders.common import Duration
            from schwab.orders.common import Instrument
            
            params = {
                'periodType': period_type,
                'frequencyType': frequency_type,
                'frequency': frequency,
            }
            
            if start_date:
                params['startDate'] = int(start_date.timestamp() * 1000)
            if end_date:
                params['endDate'] = int(end_date.timestamp() * 1000)
            
            response = client.get_price_history(symbol, **params)
            if response.status_code == 200:
                data = response.json()
                return data.get('candles', [])
            else:
                print(f"获取历史数据失败: {response.status_code}")
                return []
        except Exception as e:
            print(f"获取历史数据异常: {e}")
            return []
    
    def place_order(
        self,
        symbol: str,
        quantity: int,
        order_type: str = 'market',
        side: str = 'buy',
        price: Optional[float] = None,
        account_hash: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        下单
        
        Args:
            symbol: 股票代码
            quantity: 数量
            order_type: 订单类型 ('market', 'limit', 'stop')
            side: 方向 ('buy', 'sell')
            price: 价格 (限价单/止损单需要)
            account_hash: 账户哈希值
        
        Returns:
            订单结果
        """
        client = self._get_client()
        if client is None:
            return {'success': False, 'error': '客户端未初始化'}
        
        try:
            from schwab.orders.orders import (
                equity_buy_market,
                equity_sell_market,
                equity_buy_limit,
                equity_sell_limit,
                equity_buy_stop,
                equity_sell_stop
            )
            
            if account_hash is None:
                accounts = self.get_account_info()
                if accounts:
                    account_hash = accounts[0].get('hashValue')
            
            if account_hash is None:
                return {'success': False, 'error': '无法获取账户哈希值'}
            
            if order_type == 'market':
                if side == 'buy':
                    order = equity_buy_market(symbol, quantity)
                else:
                    order = equity_sell_market(symbol, quantity)
            elif order_type == 'limit' and price:
                if side == 'buy':
                    order = equity_buy_limit(symbol, quantity, price)
                else:
                    order = equity_sell_limit(symbol, quantity, price)
            elif order_type == 'stop' and price:
                if side == 'buy':
                    order = equity_buy_stop(symbol, quantity, price)
                else:
                    order = equity_sell_stop(symbol, quantity, price)
            else:
                return {'success': False, 'error': '不支持的订单类型'}
            
            response = client.place_order(account_hash, order)
            
            if response.status_code in [200, 201]:
                return {
                    'success': True,
                    'order_id': response.headers.get('Location', '').split('/')[-1],
                    'status_code': response.status_code
                }
            else:
                return {
                    'success': False,
                    'status_code': response.status_code,
                    'error': response.text
                }
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def cancel_order(self, order_id: str, account_hash: Optional[str] = None) -> Dict[str, Any]:
        """
        取消订单
        
        Args:
            order_id: 订单ID
            account_hash: 账户哈希值
        
        Returns:
            取消结果
        """
        client = self._get_client()
        if client is None:
            return {'success': False, 'error': '客户端未初始化'}
        
        try:
            if account_hash is None:
                accounts = self.get_account_info()
                if accounts:
                    account_hash = accounts[0].get('hashValue')
            
            response = client.cancel_order(account_hash, order_id)
            
            return {
                'success': response.status_code == 200,
                'status_code': response.status_code
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_order_status(self, order_id: str, account_hash: Optional[str] = None) -> Dict[str, Any]:
        """
        获取订单状态
        
        Args:
            order_id: 订单ID
            account_hash: 账户哈希值
        
        Returns:
            订单状态
        """
        client = self._get_client()
        if client is None:
            return {}
        
        try:
            if account_hash is None:
                accounts = self.get_account_info()
                if accounts:
                    account_hash = accounts[0].get('hashValue')
            
            response = client.get_order(account_hash, order_id)
            
            if response.status_code == 200:
                return response.json()
            else:
                return {}
        except Exception as e:
            print(f"获取订单状态异常: {e}")
            return {}
