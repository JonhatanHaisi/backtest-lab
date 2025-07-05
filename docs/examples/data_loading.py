from datetime import datetime, timedelta
from backtest_lab.data import StockDataLoader, DataFrequency

# Create an instance of StockDataLoader
loader = StockDataLoader()

# Load data for a single symbol
data = loader.get_data(
    symbol="PETR3.SA",
    start_date=datetime.now() - timedelta(days=30),
    end_date=datetime.now(),
    frequency=DataFrequency.DAILY
)

print(f"Loaded {len(data.data)} rows for {data.symbol}")
print(data.data.head())

# Load data for multiple symbols
symbols = ["AAPL", "GOOGL", "MSFT"]
multi_data = loader.get_multiple_symbols(
    symbols=symbols,
    start_date=datetime.now() - timedelta(days=30),
    frequency=DataFrequency.DAILY
)

for symbol, market_data in multi_data.items():
    print(f"{symbol}: {len(market_data.data)} rows")