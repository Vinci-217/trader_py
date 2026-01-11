import schwabdev  # import the package
from pprint import pprint  # 用于格式化输出

APP_KEY = "YOUR_APP_KEY"
APP_SECRET = ""

client = schwabdev.Client(APP_KEY, APP_SECRET),

print(client.account_linked().json())  # make api calls

# response = client.quote(symbol_id="AAPL", fields="quote")
#
# # 3. 处理响应（验证状态 + 解析数据）
# if response.ok:
#     # 解析JSON数据
#     apple_quote = response.json()
#     print("=== 苹果（AAPL）股价信息 ===")
#     pprint(apple_quote)
#
#     # 提取核心字段（按需选择）
#     core_data = {
#         "最新价": apple_quote["AAPL"]["lastPrice"],
#         "开盘价": apple_quote["AAPL"]["openPrice"],
#         "最高价": apple_quote["AAPL"]["highPrice"],
#         "最低价": apple_quote["AAPL"]["lowPrice"],
#         "成交量": apple_quote["AAPL"]["volume"],
#         "涨跌幅": f"{apple_quote['AAPL']['netChange']:.2f} ({apple_quote['AAPL']['percentChange']:.2f}%)",
#         "更新时间": apple_quote["AAPL"]["quoteTime"]
#     }
#     print("\n=== 核心股价数据 ===")
#     for key, value in core_data.items():
#         print(f"{key}: {value}")
# else:
#     print(f"获取失败，状态码：{response.status_code}，错误信息：{response.text}")
