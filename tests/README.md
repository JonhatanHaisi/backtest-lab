# Testing Guide for Backtest Lab

This directory contains comprehensive tests for the backtest-lab package.

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures and test configuration
├── test_base.py             # Tests for base classes (DataFrequency, MarketDataRequest, MarketData, DataProvider)
├── test_yahoo_provider.py   # Tests for Yahoo Finance provider
├── test_stock_loader.py     # Tests for StockDataLoader
├── test_integration.py      # Integration tests across components
├── test_end_to_end.py       # End-to-end workflow tests
├── test_performance.py      # Performance and scalability tests
├── test_examples.py         # Tests for example scripts in docs/examples/
├── test_imports.py          # Tests for package structure and imports
├── test_edge_cases.py       # Tests for edge cases and error scenarios
├── test_configuration.py    # Tests for test configuration and setup
└── README.md               # This file
```

## Test Categories

### Unit Tests
- **test_base.py**: Tests for core data models and abstract classes
- **test_yahoo_provider.py**: Tests for Yahoo Finance provider implementation
- **test_stock_loader.py**: Tests for the main data loader class
- **test_imports.py**: Tests for package structure and import functionality
- **test_edge_cases.py**: Tests for edge cases, error scenarios, and boundary conditions

### Integration Tests
- **test_integration.py**: Tests component interaction and package-level functionality
- **test_end_to_end.py**: Real-world usage scenarios and workflows
- **test_examples.py**: Tests for example scripts to ensure they work correctly

### Performance Tests
- **test_performance.py**: Performance benchmarks and scalability tests

### Configuration Tests
- **test_configuration.py**: Tests for test setup, configuration files, and project structure

## Test Markers

The tests use pytest markers to categorize different types of tests:

- `unit`: Unit tests (default)
- `integration`: Integration tests
- `network`: Tests that require network access
- `slow`: Long-running tests
- `performance`: Performance benchmark tests

## Running Tests

### Prerequisites

Install test dependencies:
```bash
pip install pytest pytest-cov pytest-mock pytest-asyncio freezegun responses
```

Or using poetry:
```bash
poetry install --with dev
```

### Quick Start

Run all tests (excluding network and slow tests):
```bash
python run_tests.py --type quick
```

### Different Test Types

```bash
# Run only unit tests
python run_tests.py --type unit

# Run integration tests
python run_tests.py --type integration

# Run performance tests
python run_tests.py --type performance

# Run all tests with coverage
python run_tests.py --type coverage

# Run all tests
python run_tests.py --type all
```

### Direct pytest Commands

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/backtest_lab --cov-report=html

# Run specific test file
pytest tests/test_base.py

# Run tests with specific marker
pytest -m "not network"

# Run with verbose output
pytest -v

# Stop on first failure
pytest -x

# Run in parallel (requires pytest-xdist)
pytest -n auto
```

### Network Tests

Some tests require network access to test real data providers. These are marked with `@pytest.mark.network`:

```bash
# Include network tests
pytest -m "network"

# Exclude network tests (default)
pytest -m "not network"
```

## Test Configuration

### pytest.ini
Configuration file with default settings:
- Test paths
- Coverage settings
- Marker definitions
- Default options

### conftest.py
Shared fixtures including:
- Sample OHLCV data
- Mock providers
- Test configurations
- Common test utilities

## Writing New Tests

### Test File Naming
- Test files: `test_*.py`
- Test classes: `Test*`
- Test functions: `test_*`

### Example Test Structure

```python
import pytest
from backtest_lab.data import StockDataLoader

class TestMyFeature:
    """Test my new feature"""
    
    def test_basic_functionality(self):
        """Test basic functionality"""
        # Arrange
        loader = StockDataLoader()
        
        # Act
        result = loader.some_method()
        
        # Assert
        assert result is not None
    
    @pytest.mark.network
    def test_with_real_data(self):
        """Test with real network data"""
        # This test requires network access
        pass
    
    @pytest.mark.slow
    def test_performance(self):
        """Test performance characteristics"""
        # This test may take longer to run
        pass
```

### Using Fixtures

```python
def test_with_sample_data(self, sample_ohlcv_data, sample_market_data_request):
    """Test using shared fixtures"""
    # Use fixtures from conftest.py
    assert len(sample_ohlcv_data) > 0
    assert sample_market_data_request.symbol == "AAPL"
```

### Mocking External Services

```python
from unittest.mock import Mock, patch

@patch('backtest_lab.data.providers.yahoo.yf.Ticker')
def test_with_mock_yahoo(self, mock_ticker):
    """Test with mocked Yahoo Finance"""
    # Setup mock
    mock_instance = Mock()
    mock_ticker.return_value = mock_instance
    mock_instance.history.return_value = sample_data
    
    # Test code here
```

## Test Data

### Fixtures
- `sample_ohlcv_data`: Standard OHLCV DataFrame for testing
- `sample_market_data_request`: Pre-configured market data request
- `sample_market_data`: Complete MarketData object
- `mock_yahoo_ticker`: Mocked Yahoo Finance ticker

### Test Symbols
- Use `AAPL`, `GOOGL`, `MSFT` for US stocks
- Use `PETR4.SA`, `VALE3.SA` for Brazilian stocks
- Use `BTC-USD`, `ETH-USD` for crypto
- Use `INVALID_SYMBOL_123` for invalid symbols

## Coverage Requirements

The project aims for:
- **Minimum 80% code coverage**
- **100% coverage for critical paths**
- **All public APIs tested**

View coverage report:
```bash
python run_tests.py --type coverage
open htmlcov/index.html  # View in browser
```

## Performance Benchmarks

Performance tests verify:
- **Request creation**: > 1000 requests/second
- **Data loading**: > 100 loads/second
- **Multiple symbols**: > 50 symbols/second
- **Memory usage**: < 100MB for 50 symbols
- **Large datasets**: < 1 second for 100k+ rows

Run performance tests:
```bash
python run_tests.py --type performance
```

## Troubleshooting

### Common Issues

1. **Import errors**: Ensure package is installed in development mode
   ```bash
   pip install -e .
   ```

2. **Network test failures**: Check internet connection or skip network tests
   ```bash
   pytest -m "not network"
   ```

3. **Slow test timeouts**: Increase timeout or skip slow tests
   ```bash
   pytest -m "not slow"
   ```

4. **Mock issues**: Verify mock paths match actual import paths

### Debug Mode

Run tests with debug output:
```bash
pytest -v -s --tb=long
```

### Test Specific Function

```bash
pytest tests/test_base.py::TestMarketDataRequest::test_symbol_normalization -v
```

## Continuous Integration

For CI/CD pipelines, use:
```bash
# Fast CI tests (no network, no slow tests)
pytest tests/ -m "not network and not slow" --cov=src/backtest_lab --cov-fail-under=80

# Full test suite
python run_tests.py --type all
```

## Contributing

When adding new features:

1. **Write tests first** (TDD approach)
2. **Add appropriate markers** (`@pytest.mark.network`, etc.)
3. **Update fixtures** if needed
4. **Maintain coverage** above 80%
5. **Add performance tests** for critical paths
6. **Document test scenarios** in docstrings

## Test Environment

Recommended test environment:
- Python 3.8+
- pytest 7.0+
- All dev dependencies installed
- Stable internet connection (for network tests)

## Getting Help

- Check existing test files for examples
- Review pytest documentation: https://docs.pytest.org/
- Ask questions in project issues
- Follow established patterns in the codebase
