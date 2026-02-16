"""AI量化交易主入口"""
import sys
import os
from datetime import datetime, timedelta

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from ai_quant.config import STOCKS, INITIAL_CASH, BACKTEST_START_DATE, BACKTEST_END_DATE
from ai_quant.backtest import run_multi_stock_backtest, run_backtest
from ai_quant.ai_client import AIClient
from ai_quant.trader import SchwabTrader
from quant.data_get import get_us_stock
import pandas as pd
import bt


def prepare_stock_data(symbol: str, days: int = 30) -> dict:
    """准备股票数据用于AI分析"""
    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=days*2)).strftime("%Y%m%d")

    stock_code_map = {
        "NVDA": "105.NVDA",
        "TSLA": "105.TSLA",
        "AAPL": "105.AAPL"
    }

    code = stock_code_map.get(symbol, f"105.{symbol}")

    df = get_us_stock(code, start_date, end_date)

    if df is None or df.empty:
        return None

    df.rename(columns={
        '日期': 'datetime',
        '开盘': 'open',
        '最高': 'high',
        '最低': 'low',
        '收盘': 'close',
        '成交量': 'volume'
    }, inplace=True)

    df['datetime'] = pd.to_datetime(df['datetime'])
    df.set_index('datetime', inplace=True)

    for col in ['open', 'high', 'low', 'close', 'volume']:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    df = df.dropna()

    close = df['close'].iloc[-1]
    sma20 = df['close'].rolling(20).mean().iloc[-1]
    sma50 = df['close'].rolling(50).mean().iloc[-1]

    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs)).iloc[-1]

    exp1 = df['close'].ewm(span=12, adjust=False).mean()
    exp2 = df['close'].ewm(span=26, adjust=False).mean()
    macd = exp1 - exp2
    signal = macd.ewm(span=9, adjust=False).mean()
    macd_value = (macd - signal).iloc[-1]

    bb_mid = df['close'].rolling(20).mean()
    bb_std = df['close'].rolling(20).std()
    bb_upper = bb_mid + 2 * bb_std
    bb_lower = bb_mid - 2 * bb_std

    volume = int(df['volume'].iloc[-1])

    price_data = "\n".join([
        f"{row.name.strftime('%Y-%m-%d')}: 开盘${row['open']:.2f}, 收盘${row['close']:.2f}, 成交量{row['volume']:,.0f}"
        for _, row in df.tail(20).iterrows()
    ])

    return {
        "symbol": symbol,
        "name": STOCKS.get(symbol, symbol),
        "price_data": price_data,
        "close": float(close),
        "sma20": float(sma20) if pd.notna(sma20) else float(close),
        "sma50": float(sma50) if pd.notna(sma50) else float(close),
        "rsi": float(rsi) if pd.notna(rsi) else 50.0,
        "macd": float(macd_value) if pd.notna(macd_value) else 0.0,
        "bb_upper": float(bb_upper.iloc[-1]),
        "bb_mid": float(bb_mid.iloc[-1]),
        "bb_lower": float(bb_lower.iloc[-1]),
        "volume": volume
    }


def run_live_trading():
    """运行实时交易（需要配置Schwab API）"""
    print("\n" + "="*60)
    print("AI量化交易实时模式")
    print("="*60)

    ai_client = AIClient()
    trader = SchwabTrader()

    print(f"\n剩余交易次数: {trader.get_remaining_trades()}")

    for symbol, name in STOCKS.items():
        print(f"\n分析 {name} ({symbol})...")

        data = prepare_stock_data(symbol)
        if data is None:
            print(f"无法获取 {symbol} 数据")
            continue

        ai_result = ai_client.analyze_stock(**data)

        if ai_result:
            print(f"AI分析结果:")
            print(f"  趋势: {ai_result.get('trend')}")
            print(f"  建议: {ai_result.get('recommendation')}")
            print(f"  信心: {ai_result.get('confidence')}")
            print(f"  风险: {ai_result.get('risk_level')}")
            print(f"  原因: {ai_result.get('reason')}")
        else:
            print("AI分析失败")

    print("\n实时交易功能需要配置Schwab API密钥")


def run_backtest_mode():
    """运行回测模式"""
    print("\n" + "="*60)
    print("AI量化交易回测模式")
    print("="*60)
    print(f"回测时间范围: {BACKTEST_START_DATE} - {BACKTEST_END_DATE}")
    print(f"股票列表: {list(STOCKS.values())}")
    print("="*60)

    results = run_multi_stock_backtest()

    return results


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="AI量化交易系统")
    parser.add_argument(
        '--mode',
        choices=['backtest', 'live'],
        default='backtest',
        help='运行模式: backtest(回测) 或 live(实时交易)'
    )

    args = parser.parse_args()

    if args.mode == 'backtest':
        run_backtest_mode()
    else:
        run_live_trading()


if __name__ == "__main__":
    main()
