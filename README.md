# Backtest Lab

A Python library for trading strategy development and backtesting, focusing on data loading from multiple providers.

## Features

- **Multi-provider data loading**: Support for Yahoo Finance and file-based data providers
- **Data persistence**: Save and load market data in Parquet and CSV formats
- **Flexible file management**: Load data from local files with automatic symbol detection
- **Comprehensive data models**: Type-safe data structures using Pydantic v2
- **Flexible frequency support**: From minute-level to monthly data
- **Robust testing**: Complete test suite with 170+ tests covering all scenarios
- **Modern Python**: Built for Python 3.13+ with modern tooling

## Quick Start

```python
from datetime import datetime, timedelta
from backtest_lab.data import StockDataLoader, DataFrequency

# Create a data loader
loader = StockDataLoader()

# Load data for a single symbol
data = loader.get_data(
    symbol="AAPL",
    start_date=datetime.now() - timedelta(days=30),
    end_date=datetime.now(),
    frequency=DataFrequency.DAILY
)

print(f"Loaded {len(data.data)} rows for {data.symbol}")
```

## Data Persistence

The library supports saving and loading market data in popular formats:

```python
# Save data to files
loader.save_data(data, "aapl.parquet", format='parquet')  # Recommended
loader.save_data(data, "aapl.csv", format='csv')          # For compatibility

# Load data from files
loaded_data = loader.load_from_file("aapl.parquet")

# Use file provider for directory-based loading
loader.add_file_provider("./data")
file_data = loader.get_data(symbol="AAPL", provider="file")
```

### Supported Features

- **Parquet format**: Fast, efficient storage with metadata preservation
- **CSV format**: Human-readable, compatible with spreadsheet applications
- **Automatic datetime indexing**: Ensures proper time-series formatting
- **OHLCV column validation**: Guarantees required columns (open, high, low, close, volume)
- **Metadata preservation**: Saves additional information alongside market data
- **Date filtering**: Load data within specific date ranges from files

## Examples

The `docs/examples/` directory contains comprehensive examples:

- **`data_loading.py`**: Basic example showing data loading, saving, and file provider usage
- **`enhanced_data_loading.py`**: Advanced example with full workflow, file management, and performance comparison

Run the examples:
```bash
python docs/examples/data_loading.py
python docs/examples/enhanced_data_loading.py
```

## Installation

```bash
pip install -e .
```

## Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
make test

# Run with coverage
make test-coverage

# Format code
make format

# Lint code
make lint
```

## Testing

The project includes a comprehensive test suite with:
- Unit tests for all components
- Integration tests for real-world scenarios
- Performance benchmarks
- Edge case handling
- Example validation

See [tests/README.md](tests/README.md) for detailed testing documentation.

## Project Structure

```
backtest-lab/
├── src/backtest_lab/           # Main library code
│   └── data/                   # Data loading modules
├── tests/                      # Comprehensive test suite
├── docs/examples/              # Usage examples
└── docs/                       # Documentation
```