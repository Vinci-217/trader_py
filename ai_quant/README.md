# AI Quant - 智能量化交易系统

基于Backtrader框架的量化交易策略库，支持回测和Schwab实盘对接。

## 项目结构

```
ai_quant/
├── __init__.py              # 包入口
├── README.md                # 本文档
├── data/                    # 数据模块
│   ├── __init__.py
│   └── loader.py            # 数据加载器
├── factors/                 # 因子模块
│   ├── __init__.py
│   ├── technical.py         # 技术因子
│   └── fundamental.py       # 基本面因子
├── ml/                      # 机器学习模块
│   ├── __init__.py
│   └── predictor.py         # ML预测器
├── strategies/              # 策略模块
│   ├── __init__.py
│   ├── robust.py            # 稳健策略 (Defensive, Conservative)
│   ├── advanced_defensive.py # 高级策略 (TrendRider, BreakoutDefensive)
│   └── winner_v1.py         # Winner策略系列
├── broker/                  # 券商对接
│   ├── __init__.py
│   ├── schwab_client.py     # Schwab API客户端
│   └── schwab_trader.py     # 交易执行器
├── runner/                  # 策略运行器
│   └── __init__.py          # 回测/实盘运行
└── test_strategies.py       # 策略测试脚本
```

## 策略介绍

### 推荐策略

| 策略名称 | 正收益年数 | 胜率 | 特点 | 适用场景 |
|---------|-----------|------|------|---------|
| **TrendRider** | 6/6 | 33.3% | EMA+SMA趋势追踪 | 每年正收益首选 |
| **BreakoutDefensive** | 6/6 | 33.3% | 新高突破+防御 | 每年正收益首选 |
| **Defensive** | 6/6 | 33.3% | 严格筛选+70%仓位 | 稳健保守 |
| **WinnerV1** | 5/6 | 50.0% | 动量策略 | 牛市高收益 |

### 策略详情

#### 1. TrendRider (推荐)
- **特点**: EMA+SMA组合趋势判断，75%仓位
- **2025收益**: 45.79%
- **核心逻辑**: 
  - 筛选条件: `close > sma20 > sma50` 且 `mom20 > 0`
  - EMA趋势确认加分
  - 12%回撤止损

#### 2. BreakoutDefensive (推荐)
- **特点**: 新高突破加分机制，75%仓位
- **2025收益**: 45.79%
- **核心逻辑**:
  - 接近或创20日新高加分
  - 严格趋势筛选
  - 分散持仓2-3只股票

#### 3. DefensiveStrategy
- **特点**: 70%仓位，严格筛选
- **2025收益**: 42.51%
- **核心逻辑**:
  - 双均线过滤: `close > sma20 > sma50`
  - 动量确认: `mom20 > 0`
  - 12%止损保护

#### 4. WinnerV1
- **特点**: 高胜率(50%)，牛市表现好
- **2020收益**: 164.91%
- **注意**: 2023年可能亏损(-6.45%)

### 年度收益对比

| 年份 | TrendRider | Defensive | WinnerV1 | 平均收益 |
|------|------------|-----------|----------|----------|
| 2020 | 24.78% | 23.18% | **164.91%** | 157.15% |
| 2021 | 30.22% | 28.71% | 29.59% | 52.59% |
| 2022 | **7.67%** | **6.63%** | 5.37% | -47.66% |
| 2023 | **18.74%** | 17.48% | -6.45% | 116.95% |
| 2024 | 11.86% | 10.99% | 37.40% | 63.84% |
| 2025 | **45.79%** | 42.51% | 41.77% | 23.32% |

## 快速开始

### 安装依赖

```bash
pip install backtrader pandas numpy requests
pip install schwab-py  # 实盘交易需要
```

### 回测示例

```python
from ai_quant import TrendRider, load_stock_data
import backtrader as bt

# 准备数据
symbols = ['AAPL', 'MSFT', 'AMZN', 'GOOGL', 'NVDA', 'META', 'TSLA']

# 创建回测引擎
cerebro = bt.Cerebro()
cerebro.addstrategy(TrendRider)
cerebro.broker.setcash(100000)

# 加载数据
for symbol in symbols:
    df = load_stock_data(symbol, '20200101', '20251231')
    data = bt.feeds.PandasData(dataname=df)
    data._name = symbol
    cerebro.adddata(data)

# 运行回测
results = cerebro.run()
print(f"最终价值: ${cerebro.broker.getvalue():,.2f}")
```

### 运行测试

```bash
python -m ai_quant.test_strategies
```

## Schwab实盘对接

### 1. 注册Schwab开发者账户

1. 访问 [Schwab Developer Portal](https://developer.schwab.com/)
2. 创建应用，获取 `App Key` 和 `App Secret`
3. 设置回调URL (如 `https://127.0.0.1`)

### 2. 配置环境变量

```bash
# Windows
set SCHWAB_APP_KEY=your_app_key
set SCHWAB_APP_SECRET=your_app_secret
set SCHWAB_CALLBACK_URL=https://127.0.0.1

# Linux/Mac
export SCHWAB_APP_KEY=your_app_key
export SCHWAB_APP_SECRET=your_app_secret
export SCHWAB_CALLBACK_URL=https://127.0.0.1
```

### 3. 实盘交易示例

```python
from ai_quant.broker import SchwabClient, SchwabTrader
from ai_quant.runner import StrategyRunner

# 创建客户端
client = SchwabClient(
    app_key='your_app_key',
    app_secret='your_app_secret',
    callback_url='https://127.0.0.1'
)

# OAuth认证 (首次需要)
client.authenticate()

# 创建交易执行器
trader = SchwabTrader(client, dry_run=True)  # dry_run=True 模拟运行

# 连接账户
trader.connect()

# 同步持仓
positions = trader.sync_positions()
print(f"当前持仓: {positions}")

# 执行交易信号
result = trader.execute_signal('AAPL', 'buy')
print(f"交易结果: {result}")

# 批量执行策略信号
signals = {'AAPL': 'buy', 'MSFT': 'buy', 'GOOGL': 'sell'}
results = trader.execute_strategy_signals(signals)
```

### 4. 使用策略运行器

```python
from ai_quant.runner import StrategyRunner

# 创建运行器
runner = StrategyRunner(
    strategy_name='TrendRider',
    symbols=['AAPL', 'MSFT', 'AMZN', 'GOOGL', 'NVDA', 'META', 'TSLA'],
    mode='live',
    dry_run=True  # 模拟运行，不实际下单
)

# 设置券商
runner.setup_broker(
    app_key='your_app_key',
    app_secret='your_app_secret'
)

# 认证
runner.authenticate()

# 运行
result = runner.run_live()
print(result)
```

## API参考

### SchwabClient

```python
class SchwabClient:
    def __init__(self, app_key, app_secret, callback_url, sandbox=True)
    def authenticate(self) -> bool
    def get_account_info(self) -> Dict
    def get_positions(self, account_hash=None) -> List[Dict]
    def get_quote(self, symbol: str) -> Dict
    def get_price_history(self, symbol, start_date, end_date) -> List[Dict]
    def place_order(self, symbol, quantity, order_type, side, price) -> Dict
    def cancel_order(self, order_id) -> Dict
    def get_order_status(self, order_id) -> Dict
```

### SchwabTrader

```python
class SchwabTrader:
    def __init__(self, client, account_hash=None, dry_run=True)
    def connect(self) -> bool
    def sync_positions(self) -> Dict
    def get_account_balance(self) -> Dict
    def execute_signal(self, symbol, signal, quantity=None, price=None) -> Dict
    def execute_strategy_signals(self, signals: Dict[str, str]) -> List[Dict]
    def rebalance_portfolio(self, target_allocation: Dict[str, float]) -> List[Dict]
```

## 注意事项

1. **风险提示**: 量化交易存在风险，历史表现不代表未来收益
2. **Schwab API限制**: 
   - 每分钟最多120次请求
   - 盘前盘后可能有额外限制
3. **资金管理**: 建议先用模拟模式测试
4. **策略选择**: 
   - 追求稳定正收益: TrendRider / BreakoutDefensive
   - 追求高收益: WinnerV1 (但可能某些年份亏损)

## 版本历史

- **v3.0**: 整合优质策略，添加Schwab实盘对接
- **v2.0**: 添加Defensive系列策略
- **v1.0**: 初始版本，Winner策略

## License

MIT License
