# Backtest Lab

A Python library for trading strategy development and backtesting, focusing on data loading from multiple providers.

## Features

- **Multi-provider data loading**: Support for Yahoo Finance and file-based data providers
- **Data persistence**: Save and load market data in Parquet and CSV formats
- **Flexible file management**: Load data from local files with automatic symbol detection
- **Stepwise analysis**: Advanced framework for step-by-step OHLC data analysis with signals
- **Signal system**: Built-in and custom technical indicators with caching support
- **Immutable steps**: Frozen snapshots of analysis state for reproducible results
- **Flexible plotting**: Multiple backend support (matplotlib, plotly) for visualizations
- **Comprehensive data models**: Type-safe data structures using Pydantic v2
- **Flexible frequency support**: From minute-level to monthly data
- **Robust testing**: Complete test suite with 200+ tests covering all scenarios
- **Modern Python**: Built for Python 3.13+ with modern tooling

## Quick Start

### Data Loading

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

### Stepwise Analysis

```python
from backtest_lab.analysis import (
    StepwiseAnalyzer,
    TopBottomSignal,
    create_sma_signal,
    create_rsi_signal,
    PlotManager
)

# Create signals
signals = [
    TopBottomSignal("top_bottom", window=10),
    create_sma_signal("sma_20", 20),
    create_rsi_signal("rsi_14", 14)
]

# Initialize stepwise analyzer
analyzer = StepwiseAnalyzer(
    ohlc=data.data,  # OHLC DataFrame
    signals=signals,
    initial_window=100,
    step_size=20
)

# Progress through steps
for i in range(5):
    if analyzer.can_advance:
        step = analyzer.next_step()
        print(f"Step {step.step_index}: {step.current_date}")
        
        # Get current signal values
        rsi = step.get_latest_signal_values('rsi_14', 1)
        print(f"Current RSI: {rsi.iloc[-1]:.2f}")

# Plot analysis
plot_manager = PlotManager()
fig = plot_manager.plot_step(
    analyzer.current_step,
    signals=['sma_20', 'rsi_14'],
    title="Current Analysis"
)
plot_manager.save_plot(fig, "analysis.png")
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
- **`stepwise_analysis.py`**: Complete stepwise analysis workflow with signals and plotting
- **`multiple_timeframes.py`**: Working with multiple timeframes and data management

Run the examples:
```bash
python docs/examples/data_loading.py
python docs/examples/stepwise_analysis.py
python docs/examples/multiple_timeframes.py
```

## Documentation

- **[Stepwise Analysis Guide](docs/STEPWISE_ANALYSIS.md)**: Complete guide to the stepwise analysis system
- **[Examples README](docs/examples/README.md)**: Detailed explanation of all examples
- **[Tests README](tests/README.md)**: Testing documentation and best practices

## Installation

```bash
# Install with Poetry (recommended)
poetry install

# Alternatively, install with pip
pip install -e .

## Development

```bash
# Install development dependencies with Poetry
poetry install --with dev

# Alternatively, install with pip
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
│   ├── data/                   # Data loading modules
│   │   ├── providers/          # Data providers (Yahoo, file)
│   │   └── loaders/            # Data loaders
│   └── analysis/               # Stepwise analysis system
│       ├── signals.py          # Signal implementations
│       ├── step.py             # Immutable step class
│       ├── wrapper.py          # Main analyzer class
│       ├── plotting.py         # Plotting system
│       └── exceptions.py       # Custom exceptions
├── tests/                      # Comprehensive test suite
├── docs/                       # Documentation
│   ├── examples/               # Usage examples
│   └── STEPWISE_ANALYSIS.md    # Complete analysis guide
└── README.md                   # This file
```