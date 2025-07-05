"""Common fixtures for tests"""
import pytest
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from backtest_lab.data.base import MarketDataRequest, MarketData, DataFrequency
from backtest_lab.data.providers.yahoo import YahooFinanceProvider
from backtest_lab.data.loaders.stock_loader import StockDataLoader


@pytest.fixture
def sample_ohlcv_data():
    """Sample OHLCV data for testing"""
    dates = pd.date_range(start='2024-01-01', end='2024-01-10', freq='D')
    data = pd.DataFrame({
        'open': [100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 106.0, 107.0, 108.0, 109.0],
        'high': [101.0, 102.0, 103.0, 104.0, 105.0, 106.0, 107.0, 108.0, 109.0, 110.0],
        'low': [99.0, 100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 106.0, 107.0, 108.0],
        'close': [100.5, 101.5, 102.5, 103.5, 104.5, 105.5, 106.5, 107.5, 108.5, 109.5],
        'volume': [1000000, 1100000, 1200000, 1300000, 1400000, 1500000, 1600000, 1700000, 1800000, 1900000],
        'adj_close': [100.5, 101.5, 102.5, 103.5, 104.5, 105.5, 106.5, 107.5, 108.5, 109.5]
    }, index=dates)
    return data


@pytest.fixture
def sample_market_data_request():
    """Sample MarketDataRequest for testing"""
    return MarketDataRequest(
        symbol="AAPL",
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 1, 10),
        frequency=DataFrequency.DAILY
    )


@pytest.fixture
def sample_market_data(sample_ohlcv_data):
    """Sample MarketData for testing"""
    return MarketData(
        symbol="AAPL",
        data=sample_ohlcv_data,
        metadata={
            'provider': 'test_provider',
            'rows_count': len(sample_ohlcv_data),
            'start_date': '2024-01-01',
            'end_date': '2024-01-10'
        }
    )


@pytest.fixture
def mock_yahoo_ticker():
    """Mock Yahoo Finance ticker for testing"""
    with patch('yfinance.Ticker') as mock_ticker:
        mock_instance = Mock()
        mock_ticker.return_value = mock_instance
        
        # Mock history method
        mock_instance.history.return_value = pd.DataFrame({
            'Open': [100.0, 101.0, 102.0],
            'High': [101.0, 102.0, 103.0],
            'Low': [99.0, 100.0, 101.0],
            'Close': [100.5, 101.5, 102.5],
            'Volume': [1000000, 1100000, 1200000],
            'Adj Close': [100.5, 101.5, 102.5]
        }, index=pd.date_range('2024-01-01', periods=3, freq='D'))
        
        # Mock info method
        mock_instance.info = {
            'symbol': 'AAPL',
            'shortName': 'Apple Inc.',
            'longName': 'Apple Inc.',
            'sector': 'Technology',
            'industry': 'Consumer Electronics'
        }
        
        yield mock_instance


@pytest.fixture
def yahoo_provider():
    """Yahoo Finance provider instance for testing"""
    return YahooFinanceProvider()


@pytest.fixture
def stock_loader():
    """Stock data loader instance for testing"""
    return StockDataLoader()


@pytest.fixture
def empty_dataframe():
    """Empty pandas DataFrame for testing error scenarios"""
    return pd.DataFrame()


@pytest.fixture
def invalid_symbol():
    """Invalid symbol for testing error scenarios"""
    return "INVALID_SYMBOL_123"


@pytest.fixture
def date_range_last_30_days():
    """Date range for last 30 days"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    return start_date, end_date


@pytest.fixture
def mock_network_error():
    """Mock network error for testing error handling"""
    def _mock_network_error():
        raise ConnectionError("Network error")
    return _mock_network_error


@pytest.fixture
def mock_timeout_error():
    """Mock timeout error for testing error handling"""
    def _mock_timeout_error():
        raise TimeoutError("Request timeout")
    return _mock_timeout_error


@pytest.fixture
def sample_symbols():
    """Sample list of symbols for testing"""
    return ["AAPL", "GOOGL", "MSFT", "AMZN"]


@pytest.fixture
def sample_brazilian_symbols():
    """Sample list of Brazilian symbols for testing"""
    return ["PETR4.SA", "VALE3.SA", "ITUB4.SA", "BBDC4.SA"]


@pytest.fixture
def sample_crypto_symbols():
    """Sample list of crypto symbols for testing"""
    return ["BTC-USD", "ETH-USD", "ADA-USD"]


@pytest.fixture
def mock_successful_provider_response(sample_ohlcv_data):
    """Mock successful provider response"""
    return MarketData(
        symbol="TEST",
        data=sample_ohlcv_data,
        metadata={'provider': 'mock', 'rows_count': len(sample_ohlcv_data)}
    )


@pytest.fixture
def mock_failed_provider_response():
    """Mock failed provider response"""
    def _mock_failed_response():
        raise ValueError("Provider error")
    return _mock_failed_response


@pytest.fixture
def temp_directory(tmp_path):
    """Temporary directory for file operations"""
    return tmp_path


@pytest.fixture
def sample_config():
    """Sample configuration for providers"""
    return {
        'timeout': 30,
        'retries': 3,
        'cache_enabled': True
    }
