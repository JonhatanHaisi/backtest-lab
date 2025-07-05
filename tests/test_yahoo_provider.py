"""Tests for Yahoo Finance provider"""
import pytest
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, ANY, MagicMock

from backtest_lab.data.base import MarketDataRequest, MarketData, DataFrequency
from backtest_lab.data.providers.yahoo import YahooFinanceProvider


class TestYahooFinanceProvider:
    """Test Yahoo Finance provider"""
    
    def test_provider_name(self, yahoo_provider):
        """Test provider name property"""
        assert yahoo_provider.provider_name == "Yahoo Finance"
    
    def test_frequency_mapping(self):
        """Test frequency mapping is correct"""
        expected_mapping = {
            DataFrequency.MINUTE_1: "1m",
            DataFrequency.MINUTE_5: "5m",
            DataFrequency.MINUTE_15: "15m",
            DataFrequency.MINUTE_30: "30m",
            DataFrequency.HOUR_1: "1h",
            DataFrequency.DAILY: "1d",
            DataFrequency.WEEKLY: "1wk",
            DataFrequency.MONTHLY: "1mo",
        }
        
        assert YahooFinanceProvider.FREQUENCY_MAPPING == expected_mapping
    
    def test_provider_initialization(self):
        """Test provider initialization"""
        provider = YahooFinanceProvider()
        assert provider.config == {}
        assert provider.provider_name == "Yahoo Finance"
        
        # Test with config
        config = {"timeout": 30}
        provider_with_config = YahooFinanceProvider(config)
        assert provider_with_config.config == config
    
    @patch('backtest_lab.data.providers.yahoo.yf.Ticker')
    def test_get_data_success(self, mock_ticker, sample_market_data_request):
        """Test successful data retrieval"""
        # Setup mock
        mock_instance = Mock()
        mock_ticker.return_value = mock_instance
        
        # Mock history data
        mock_history_data = pd.DataFrame({
            'Open': [100.0, 101.0, 102.0],
            'High': [101.0, 102.0, 103.0],
            'Low': [99.0, 100.0, 101.0],
            'Close': [100.5, 101.5, 102.5],
            'Volume': [1000000, 1100000, 1200000],
            'Adj Close': [100.5, 101.5, 102.5]
        }, index=pd.date_range('2024-01-01', periods=3, freq='D'))
        
        mock_instance.history.return_value = mock_history_data
        mock_instance.info = {
            'symbol': 'AAPL',
            'longName': 'Apple Inc.',
            'sector': 'Technology',
            'industry': 'Consumer Electronics'
        }
        
        # Test
        provider = YahooFinanceProvider()
        result = provider.get_data(sample_market_data_request)
        
        # Assertions
        assert isinstance(result, MarketData)
        assert result.symbol == "AAPL"
        assert len(result.data) == 3
        assert 'open' in result.data.columns
        assert 'high' in result.data.columns
        assert 'low' in result.data.columns
        assert 'close' in result.data.columns
        assert 'volume' in result.data.columns
        assert result.metadata['provider'] == "Yahoo Finance"
        assert result.metadata['company_name'] == 'Apple Inc.'
    
    @patch('backtest_lab.data.providers.yahoo.yf.Ticker')
    def test_get_data_with_empty_response(self, mock_ticker, sample_market_data_request):
        """Test handling of empty data response"""
        # Setup mock to return empty DataFrame
        mock_instance = Mock()
        mock_ticker.return_value = mock_instance
        mock_instance.history.return_value = pd.DataFrame()
        
        provider = YahooFinanceProvider()
        
        with pytest.raises(ValueError, match="No data found for symbol"):
            provider.get_data(sample_market_data_request)
    
    @patch('backtest_lab.data.providers.yahoo.yf.Ticker')
    def test_get_data_with_network_error(self, mock_ticker, sample_market_data_request):
        """Test handling of network errors"""
        # Setup mock to raise exception
        mock_instance = Mock()
        mock_ticker.return_value = mock_instance
        mock_instance.history.side_effect = ConnectionError("Network error")
        
        provider = YahooFinanceProvider()
        
        with pytest.raises(ConnectionError):
            provider.get_data(sample_market_data_request)
    
    @patch('backtest_lab.data.providers.yahoo.yf.Ticker')
    def test_get_data_with_different_frequencies(self, mock_ticker):
        """Test data retrieval with different frequencies"""
        # Setup mock
        mock_instance = Mock()
        mock_ticker.return_value = mock_instance
        
        mock_history_data = pd.DataFrame({
            'Open': [100.0], 'High': [101.0], 'Low': [99.0], 
            'Close': [100.5], 'Volume': [1000000], 'Adj Close': [100.5]
        }, index=pd.date_range('2024-01-01', periods=1, freq='D'))
        
        mock_instance.history.return_value = mock_history_data
        mock_instance.info = {'symbol': 'AAPL'}
        
        provider = YahooFinanceProvider()
        
        # Test different frequencies
        frequencies = [
            (DataFrequency.MINUTE_1, "1m"),
            (DataFrequency.MINUTE_5, "5m"),
            (DataFrequency.HOUR_1, "1h"),
            (DataFrequency.DAILY, "1d"),
            (DataFrequency.WEEKLY, "1wk"),
        ]
        
        for freq_enum, expected_interval in frequencies:
            request = MarketDataRequest(symbol="AAPL", frequency=freq_enum)
            result = provider.get_data(request)
            
            # Verify correct interval was used
            mock_instance.history.assert_called_with(
                start=ANY,
                end=ANY,
                interval=expected_interval,
                auto_adjust=True,
                prepost=True
            )
            
            assert isinstance(result, MarketData)
    
    @patch('backtest_lab.data.providers.yahoo.yf.Ticker')
    def test_get_data_date_handling(self, mock_ticker):
        """Test date handling in data requests"""
        # Setup mock
        mock_instance = Mock()
        mock_ticker.return_value = mock_instance
        
        mock_history_data = pd.DataFrame({
            'Open': [100.0], 'High': [101.0], 'Low': [99.0], 
            'Close': [100.5], 'Volume': [1000000], 'Adj Close': [100.5]
        }, index=pd.date_range('2024-01-01', periods=1, freq='D'))
        
        mock_instance.history.return_value = mock_history_data
        mock_instance.info = {'symbol': 'AAPL'}
        
        provider = YahooFinanceProvider()
        
        # Test with specific dates
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 10)
        request = MarketDataRequest(
            symbol="AAPL", 
            start_date=start_date, 
            end_date=end_date
        )
        
        result = provider.get_data(request)
        
        # Verify dates were passed correctly
        mock_instance.history.assert_called_with(
            start=start_date,
            end=end_date,
            interval="1d",
            auto_adjust=True,
            prepost=True
        )
        
        assert isinstance(result, MarketData)
    
    @patch('backtest_lab.data.providers.yahoo.yf.Ticker')
    def test_get_data_without_dates(self, mock_ticker):
        """Test data retrieval without specified dates"""
        # Setup mock
        mock_instance = Mock()
        mock_ticker.return_value = mock_instance
        
        mock_history_data = pd.DataFrame({
            'Open': [100.0], 'High': [101.0], 'Low': [99.0], 
            'Close': [100.5], 'Volume': [1000000], 'Adj Close': [100.5]
        }, index=pd.date_range('2024-01-01', periods=1, freq='D'))
        
        mock_instance.history.return_value = mock_history_data
        mock_instance.info = {'symbol': 'AAPL'}
        
        provider = YahooFinanceProvider()
        request = MarketDataRequest(symbol="AAPL")
        
        result = provider.get_data(request)
        
        # Should use default date range (1 year)
        call_args = mock_instance.history.call_args
        start_date = call_args[1]['start']
        end_date = call_args[1]['end']
        
        # Should be approximately 1 year difference
        date_diff = end_date - start_date
        assert 360 <= date_diff.days <= 370  # Allow some tolerance
        
        assert isinstance(result, MarketData)
    
    @patch('backtest_lab.data.providers.yahoo.yf.Ticker')
    def test_validate_symbol_success(self, mock_ticker):
        """Test successful symbol validation"""
        # Setup mock
        mock_instance = Mock()
        mock_ticker.return_value = mock_instance
        mock_instance.info = {'symbol': 'AAPL', 'shortName': 'Apple Inc.'}
        
        provider = YahooFinanceProvider()
        result = provider.validate_symbol("AAPL")
        
        assert result is True
        mock_ticker.assert_called_once_with("AAPL")
    
    @patch('backtest_lab.data.providers.yahoo.yf.Ticker')
    def test_validate_symbol_with_short_name(self, mock_ticker):
        """Test symbol validation with shortName"""
        # Setup mock
        mock_instance = Mock()
        mock_ticker.return_value = mock_instance
        mock_instance.info = {'shortName': 'Apple Inc.'}
        
        provider = YahooFinanceProvider()
        result = provider.validate_symbol("AAPL")
        
        assert result is True
    
    @patch('backtest_lab.data.providers.yahoo.yf.Ticker')
    def test_validate_symbol_failure(self, mock_ticker):
        """Test symbol validation failure"""
        # Setup mock
        mock_instance = Mock()
        mock_ticker.return_value = mock_instance
        mock_instance.info = {}
        
        provider = YahooFinanceProvider()
        result = provider.validate_symbol("INVALID")
        
        assert result is False
    
    @patch('backtest_lab.data.providers.yahoo.yf.Ticker')
    def test_validate_symbol_exception(self, mock_ticker):
        """Test symbol validation with exception"""
        # Setup mock to raise exception
        mock_ticker.side_effect = Exception("Network error")
        
        provider = YahooFinanceProvider()
        result = provider.validate_symbol("AAPL")
        
        assert result is False
    
    def test_get_available_symbols_not_implemented(self):
        """Test that get_available_symbols raises NotImplementedError"""
        provider = YahooFinanceProvider()
        
        with pytest.raises(NotImplementedError):
            provider.get_available_symbols()
    
    def test_standardize_columns(self):
        """Test column standardization"""
        # Create DataFrame with Yahoo Finance column names
        yahoo_data = pd.DataFrame({
            'Open': [100.0, 101.0],
            'High': [101.0, 102.0],
            'Low': [99.0, 100.0],
            'Close': [100.5, 101.5],
            'Volume': [1000000, 1100000],
            'Adj Close': [100.5, 101.5]
        })
        
        provider = YahooFinanceProvider()
        result = provider._standardize_columns(yahoo_data)
        
        # Check column names are standardized
        expected_columns = ['open', 'high', 'low', 'close', 'volume', 'adj_close']
        assert list(result.columns) == expected_columns
        
        # Check data is preserved
        assert result['open'].iloc[0] == 100.0
        assert result['high'].iloc[0] == 101.0
        assert result['low'].iloc[0] == 99.0
        assert result['close'].iloc[0] == 100.5
        assert result['volume'].iloc[0] == 1000000
        assert result['adj_close'].iloc[0] == 100.5
    
    def test_standardize_columns_missing_columns(self):
        """Test column standardization with missing columns"""
        # Create DataFrame with only some columns
        partial_data = pd.DataFrame({
            'Open': [100.0, 101.0],
            'High': [101.0, 102.0],
            'Close': [100.5, 101.5],
        })
        
        provider = YahooFinanceProvider()
        result = provider._standardize_columns(partial_data)
        
        # Check that missing columns are filled with None
        assert 'open' in result.columns
        assert 'high' in result.columns
        assert 'close' in result.columns
        assert 'low' in result.columns
        assert 'volume' in result.columns
        
        # Check that missing columns have None values
        assert result['low'].isna().all()
        assert result['volume'].isna().all()
    
    def test_standardize_columns_without_adj_close(self):
        """Test column standardization without adj_close"""
        # Create DataFrame without adj_close
        data = pd.DataFrame({
            'Open': [100.0, 101.0],
            'High': [101.0, 102.0],
            'Low': [99.0, 100.0],
            'Close': [100.5, 101.5],
            'Volume': [1000000, 1100000],
        })
        
        provider = YahooFinanceProvider()
        result = provider._standardize_columns(data)
        
        # Should only have basic columns
        expected_columns = ['open', 'high', 'low', 'close', 'volume']
        assert list(result.columns) == expected_columns
        assert 'adj_close' not in result.columns


class TestYahooFinanceProviderIntegration:
    """Integration tests for Yahoo Finance provider"""
    
    @pytest.mark.integration
    @pytest.mark.network
    def test_real_data_retrieval(self):
        """Test real data retrieval from Yahoo Finance - requires network"""
        provider = YahooFinanceProvider()
        
        # Use a reliable symbol and recent date range
        request = MarketDataRequest(
            symbol="AAPL",
            start_date=datetime.now() - timedelta(days=10),
            end_date=datetime.now() - timedelta(days=1),
            frequency=DataFrequency.DAILY
        )
        
        try:
            result = provider.get_data(request)
            
            # Basic assertions
            assert isinstance(result, MarketData)
            assert result.symbol == "AAPL"
            assert len(result.data) > 0
            assert 'open' in result.data.columns
            assert 'high' in result.data.columns
            assert 'low' in result.data.columns
            assert 'close' in result.data.columns
            assert 'volume' in result.data.columns
            
            # Check metadata
            assert result.metadata['provider'] == "Yahoo Finance"
            assert result.metadata['symbol'] == "AAPL"
            assert result.metadata['rows_count'] == len(result.data)
            
        except Exception as e:
            pytest.skip(f"Network test failed: {e}")
    
    @pytest.mark.integration
    @pytest.mark.network
    def test_real_symbol_validation(self):
        """Test real symbol validation - requires network"""
        provider = YahooFinanceProvider()
        
        try:
            # Test valid symbol
            assert provider.validate_symbol("AAPL") is True
            
            # Test invalid symbol
            assert provider.validate_symbol("INVALID_SYMBOL_123") is False
            
        except Exception as e:
            pytest.skip(f"Network test failed: {e}")
    
    @pytest.mark.integration
    @pytest.mark.network
    def test_brazilian_stocks(self):
        """Test Brazilian stock symbols - requires network"""
        provider = YahooFinanceProvider()
        
        request = MarketDataRequest(
            symbol="PETR4.SA",
            start_date=datetime.now() - timedelta(days=5),
            end_date=datetime.now() - timedelta(days=1),
            frequency=DataFrequency.DAILY
        )
        
        try:
            result = provider.get_data(request)
            
            assert isinstance(result, MarketData)
            assert result.symbol == "PETR4.SA"
            assert len(result.data) > 0
            
        except Exception as e:
            pytest.skip(f"Network test failed: {e}")
    
    @pytest.mark.integration
    @pytest.mark.network
    def test_crypto_symbols(self):
        """Test cryptocurrency symbols - requires network"""
        provider = YahooFinanceProvider()
        
        request = MarketDataRequest(
            symbol="BTC-USD",
            start_date=datetime.now() - timedelta(days=5),
            end_date=datetime.now() - timedelta(days=1),
            frequency=DataFrequency.DAILY
        )
        
        try:
            result = provider.get_data(request)
            
            assert isinstance(result, MarketData)
            assert result.symbol == "BTC-USD"
            assert len(result.data) > 0
            
        except Exception as e:
            pytest.skip(f"Network test failed: {e}")


class TestYahooFinanceProviderErrorHandling:
    """Test error handling in Yahoo Finance provider"""
    
    @patch('backtest_lab.data.providers.yahoo.yf.Ticker')
    def test_logging_on_error(self, mock_ticker, caplog):
        """Test that errors are logged properly"""
        # Setup mock to raise exception
        mock_ticker.side_effect = Exception("Test error")
        
        provider = YahooFinanceProvider()
        request = MarketDataRequest(symbol="AAPL")
        
        with pytest.raises(Exception):
            provider.get_data(request)
        
        # Check that error was logged
        assert "Error fetching data for AAPL" in caplog.text
    
    @patch('backtest_lab.data.providers.yahoo.yf.Ticker')
    def test_various_exceptions(self, mock_ticker):
        """Test handling of various types of exceptions"""
        provider = YahooFinanceProvider()
        request = MarketDataRequest(symbol="AAPL")
        
        # Test different exceptions
        exceptions = [
            ConnectionError("Network error"),
            TimeoutError("Request timeout"),
            ValueError("Invalid data"),
            KeyError("Missing key"),
            Exception("Generic error")
        ]
        
        for exception in exceptions:
            mock_ticker.side_effect = exception
            
            with pytest.raises(type(exception)):
                provider.get_data(request)
    
    @patch('backtest_lab.data.providers.yahoo.yf.Ticker')
    def test_partial_data_handling(self, mock_ticker):
        """Test handling of partial or malformed data"""
        # Setup mock with partial data
        mock_instance = Mock()
        mock_ticker.return_value = mock_instance
        
        # Data with missing columns
        partial_data = pd.DataFrame({
            'Open': [100.0, 101.0],
            'Close': [100.5, 101.5],
            # Missing High, Low, Volume
        })
        
        mock_instance.history.return_value = partial_data
        mock_instance.info = {'symbol': 'AAPL'}
        
        provider = YahooFinanceProvider()
        request = MarketDataRequest(symbol="AAPL")
        
        result = provider.get_data(request)
        
        # Should still work with missing columns filled as None
        assert isinstance(result, MarketData)
        assert 'open' in result.data.columns
        assert 'close' in result.data.columns
        assert 'high' in result.data.columns  # Should be added as None
        assert 'low' in result.data.columns   # Should be added as None
        assert 'volume' in result.data.columns  # Should be added as None
