import akshare as ak
import pandas as pd
import backtrader as bt


def get_zh_a_stock(stock_code, start_date, end_date) -> pd.DataFrame:
    data = ak.stock_zh_a_hist(
        symbol=stock_code,
        period="daily",
        start_date=start_date,
        end_date=end_date,
        adjust="qfq"
    )
    return data


def get_hk_stock(stock_code, start_date, end_date) -> pd.DataFrame:
    data = ak.stock_hk_hist(
        symbol=stock_code,
        period="daily",
        start_date=start_date,
        end_date=end_date,
        adjust="qfq"
    )
    return data


def get_us_stock(stock_code, start_date, end_date) -> pd.DataFrame:
    data = ak.stock_us_hist(
        symbol=stock_code,
        period="daily",
        start_date=start_date,
        end_date=end_date,
        adjust="qfq"
    )
    return data


if __name__ == "__main__":
    df = get_us_stock("105.MSFT", "20200101", "20230101")
    df.rename(
        columns={
            '日期': 'datetime',
            '开盘': 'open',
            '最高': 'high',
            '最低': 'low',
            '收盘': 'close',
            '成交量': 'volume'
        }, inplace=True
    )
    df['datetime'] = pd.to_datetime(df['datetime'])
    print(df)
