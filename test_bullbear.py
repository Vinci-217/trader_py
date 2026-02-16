from ai_quant.backtest import run_backtest

stocks = [
    ('105.NVDA', 'NVDA'),
    ('105.TSLA', 'TSLA'),
    ('105.AAPL', 'AAPL'),
    ('105.MSFT', 'MSFT'),
    ('105.AMZN', 'AMZN'),
    ('105.GOOGL', 'GOOGL'),
    ('105.META', 'META'),
    ('105.AMAT', 'AMAT'),
]

years = ['2020', '2021', '2022', '2023', '2024']

print('='*80)
print('智能牛熊策略 每年回测 (2020-2024)')
print('目标: 年收益30%+, 回撤<10%')
print('='*80)

results = {}

for year in years:
    start = f'{year}-01-01'
    end = f'{year}-12-31'
    print(f'\n========== {year}年 ==========')
    
    for code, name in stocks:
        key = f'{name}_{year}'
        try:
            result = run_backtest(code, name, start, end, strategy_name=f'{name.lower()}_bullbear')
            results[key] = result
            print(f'{name}: 收益={result.total_return:.1f}%, 回撤={result.max_drawdown:.1f}%, 交易={result.total_trades}次')
        except Exception as e:
            print(f'{name}: 错误 - {e}')

print('\n' + '='*80)
print('5年汇总')
print('='*80)

for name in ['NVDA', 'TSLA', 'AAPL', 'MSFT', 'AMZN', 'GOOGL', 'META', 'AMAT']:
    total_return = 1.0
    max_dd = 0
    for year in years:
        key = f'{name}_{year}'
        if key in results:
            r = results[key]
            total_return *= (1 + r.total_return / 100)
            max_dd = max(max_dd, abs(r.max_drawdown))
    
    avg_return = (total_return - 1) * 100 / 5
    print(f'{name}: 5年累计={total_return*100-100:.1f}%, 平均年化≈{avg_return:.1f}%, 最大回撤≈{max_dd:.1f}%')
