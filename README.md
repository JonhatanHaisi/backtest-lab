# Backtest Lab

A Python library for trading strategy development and backtesting, focusing on data loading from multiple providers.

## Features

- **Multi-provider data loading**: Support for Yahoo Finance and extensible for other providers
- **Comprehensive data models**: Type-safe data structures using Pydantic v2
- **Flexible frequency support**: From minute-level to monthly data
- **Robust testing**: Complete test suite with 100+ tests covering all scenarios
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