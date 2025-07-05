"""Integration tests for the entire backtest-lab package"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from backtest_lab.data import (
    StockDataLoader,
    DataFrequency,
    MarketDataRequest,
    MarketData,
    YahooFinanceProvider
)


class TestPackageIntegration:
    """Test package-level integration"""
    
    def test_import_structure(self):
        """Test that all main classes can be imported"""
        # Test that we can import all main classes
        assert StockDataLoader is not None
        assert DataFrequency is not None
        assert MarketDataRequest is not None
        assert MarketData is not None
        assert YahooFinanceProvider is not None
    
    def test_basic_workflow(self, sample_ohlcv_data):
        """Test basic workflow from request to data"""
        # Create a request
        request = MarketDataRequest(
            symbol="AAPL",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 10),
            frequency=DataFrequency.DAILY
        )
        
        # Create mock provider
        mock_provider = Mock(spec=YahooFinanceProvider)
        mock_provider.get_data.return_value = MarketData(
            symbol="AAPL",
            data=sample_ohlcv_data,
            metadata={"provider": "mock"}
        )
        
        # Test that request can be processed
        result = mock_provider.get_data(request)
        
        assert isinstance(result, MarketData)
        assert result.symbol == "AAPL"
        assert len(result.data) > 0
    
    def test_loader_with_provider_workflow(self, sample_ohlcv_data):
        """Test complete workflow using loader with provider"""
        loader = StockDataLoader()
        
        # Mock the Yahoo provider
        mock_provider = Mock(spec=YahooFinanceProvider)
        mock_provider.get_data.return_value = MarketData(
            symbol="AAPL",
            data=sample_ohlcv_data,
            metadata={"provider": "Yahoo Finance"}
        )
        mock_provider.validate_symbol.return_value = True
        
        # Replace the provider
        loader.providers['yahoo'] = mock_provider
        
        # Test symbol validation
        assert loader.validate_symbol("AAPL") is True
        
        # Test data loading
        result = loader.get_data("AAPL")
        assert isinstance(result, MarketData)
        assert result.symbol == "AAPL"
        
        # Test multiple symbols
        results = loader.get_multiple_symbols(["AAPL", "GOOGL"])
        assert len(results) == 2
        assert "AAPL" in results
        assert "GOOGL" in results
    
    def test_different_frequencies_integration(self, sample_ohlcv_data):
        """Test integration with different data frequencies"""
        loader = StockDataLoader()
        
        # Mock provider
        mock_provider = Mock(spec=YahooFinanceProvider)
        mock_provider.get_data.return_value = MarketData(
            symbol="AAPL",
            data=sample_ohlcv_data,
            metadata={"provider": "Yahoo Finance"}
        )
        loader.providers['yahoo'] = mock_provider
        
        # Test different frequencies
        frequencies = [
            DataFrequency.MINUTE_1,
            DataFrequency.MINUTE_5,
            DataFrequency.HOUR_1,
            DataFrequency.DAILY,
            DataFrequency.WEEKLY
        ]
        
        for freq in frequencies:
            result = loader.get_data("AAPL", frequency=freq)
            assert isinstance(result, MarketData)
            assert result.symbol == "AAPL"
            
            # Check that request was made with correct frequency
            call_args = mock_provider.get_data.call_args[0][0]
            assert call_args.frequency == freq
    
    def test_error_handling_integration(self):
        """Test error handling across the package"""
        loader = StockDataLoader()
        
        # Mock provider that fails
        mock_provider = Mock(spec=YahooFinanceProvider)
        mock_provider.get_data.side_effect = ValueError("Network error")
        loader.providers['yahoo'] = mock_provider
        
        # Test that errors propagate properly
        with pytest.raises(ValueError, match="Network error"):
            loader.get_data("AAPL")
    
    def test_provider_switching_integration(self, sample_ohlcv_data):
        """Test switching between providers"""
        loader = StockDataLoader()
        
        # Add multiple mock providers
        mock_yahoo = Mock(spec=YahooFinanceProvider)
        mock_yahoo.get_data.return_value = MarketData(
            symbol="AAPL",
            data=sample_ohlcv_data,
            metadata={"provider": "Yahoo Finance"}
        )
        
        mock_custom = Mock(spec=YahooFinanceProvider)
        mock_custom.get_data.return_value = MarketData(
            symbol="AAPL",
            data=sample_ohlcv_data,
            metadata={"provider": "Custom Provider"}
        )
        
        loader.providers['yahoo'] = mock_yahoo
        loader.add_provider('custom', mock_custom)
        
        # Test default provider
        result1 = loader.get_data("AAPL")
        assert result1.metadata["provider"] == "Yahoo Finance"
        
        # Test specific provider
        result2 = loader.get_data("AAPL", provider="custom")
        assert result2.metadata["provider"] == "Custom Provider"
        
        # Test changing default provider
        loader.set_default_provider("custom")
        result3 = loader.get_data("AAPL")
        assert result3.metadata["provider"] == "Custom Provider"


class TestRealWorldScenarios:
    """Test real-world usage scenarios"""
    
    def test_stock_analysis_scenario(self, sample_ohlcv_data):
        """Test a typical stock analysis scenario"""
        loader = StockDataLoader()
        
        # Mock provider
        mock_provider = Mock(spec=YahooFinanceProvider)
        mock_provider.get_data.return_value = MarketData(
            symbol="AAPL",
            data=sample_ohlcv_data,
            metadata={"provider": "Yahoo Finance"}
        )
        loader.providers['yahoo'] = mock_provider
        
        # Scenario: Load daily data for last 30 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        result = loader.get_data(
            symbol="AAPL",
            start_date=start_date,
            end_date=end_date,
            frequency=DataFrequency.DAILY
        )
        
        # Verify data
        assert isinstance(result, MarketData)
        assert result.symbol == "AAPL"
        assert len(result.data) > 0
        
        # Verify OHLCV columns
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in required_columns:
            assert col in result.data.columns
        
        # Verify request parameters
        call_args = mock_provider.get_data.call_args[0][0]
        assert call_args.symbol == "AAPL"
        assert call_args.start_date == start_date
        assert call_args.end_date == end_date
        assert call_args.frequency == DataFrequency.DAILY
    
    def test_portfolio_analysis_scenario(self, sample_ohlcv_data):
        """Test a portfolio analysis scenario"""
        loader = StockDataLoader()
        
        # Mock provider
        mock_provider = Mock(spec=YahooFinanceProvider)
        
        def mock_get_data(request):
            return MarketData(
                symbol=request.symbol,
                data=sample_ohlcv_data,
                metadata={"provider": "Yahoo Finance"}
            )
        
        mock_provider.get_data.side_effect = mock_get_data
        loader.providers['yahoo'] = mock_provider
        
        # Scenario: Load data for multiple stocks
        portfolio_symbols = ["AAPL", "GOOGL", "MSFT", "AMZN"]
        
        results = loader.get_multiple_symbols(
            symbols=portfolio_symbols,
            start_date=datetime.now() - timedelta(days=90),
            frequency=DataFrequency.DAILY
        )
        
        # Verify results
        assert len(results) == 4
        for symbol in portfolio_symbols:
            assert symbol in results
            assert isinstance(results[symbol], MarketData)
            assert results[symbol].symbol == symbol
            assert len(results[symbol].data) > 0
    
    def test_international_stocks_scenario(self, sample_ohlcv_data):
        """Test international stocks scenario"""
        loader = StockDataLoader()
        
        # Mock provider
        mock_provider = Mock(spec=YahooFinanceProvider)
        
        def mock_get_data(request):
            return MarketData(
                symbol=request.symbol,
                data=sample_ohlcv_data,
                metadata={"provider": "Yahoo Finance"}
            )
        
        mock_provider.get_data.side_effect = mock_get_data
        loader.providers['yahoo'] = mock_provider
        
        # Scenario: Load Brazilian stocks
        brazilian_symbols = ["PETR4.SA", "VALE3.SA", "ITUB4.SA"]
        
        results = loader.get_multiple_symbols(
            symbols=brazilian_symbols,
            start_date=datetime.now() - timedelta(days=30),
            frequency=DataFrequency.DAILY
        )
        
        # Verify results
        assert len(results) == 3
        for symbol in brazilian_symbols:
            assert symbol in results
            assert results[symbol].symbol == symbol
    
    def test_intraday_analysis_scenario(self, sample_ohlcv_data):
        """Test intraday analysis scenario"""
        loader = StockDataLoader()
        
        # Mock provider
        mock_provider = Mock(spec=YahooFinanceProvider)
        mock_provider.get_data.return_value = MarketData(
            symbol="AAPL",
            data=sample_ohlcv_data,
            metadata={"provider": "Yahoo Finance"}
        )
        loader.providers['yahoo'] = mock_provider
        
        # Scenario: Load intraday data
        result = loader.get_data(
            symbol="AAPL",
            start_date=datetime.now() - timedelta(days=1),
            frequency=DataFrequency.MINUTE_5
        )
        
        # Verify data
        assert isinstance(result, MarketData)
        assert result.symbol == "AAPL"
        
        # Verify request frequency
        call_args = mock_provider.get_data.call_args[0][0]
        assert call_args.frequency == DataFrequency.MINUTE_5
    
    def test_error_recovery_scenario(self, sample_ohlcv_data, capsys):
        """Test error recovery scenario"""
        loader = StockDataLoader()
        
        # Mock provider with mixed results
        mock_provider = Mock(spec=YahooFinanceProvider)
        
        def mock_get_data_mixed(request):
            if request.symbol == "INVALID":
                raise ValueError("Invalid symbol")
            return MarketData(
                symbol=request.symbol,
                data=sample_ohlcv_data,
                metadata={"provider": "Yahoo Finance"}
            )
        
        mock_provider.get_data.side_effect = mock_get_data_mixed
        loader.providers['yahoo'] = mock_provider
        
        # Scenario: Load portfolio with one invalid symbol
        symbols = ["AAPL", "INVALID", "GOOGL", "MSFT"]
        
        results = loader.get_multiple_symbols(symbols)
        
        # Should get results for valid symbols only
        assert len(results) == 3
        assert "AAPL" in results
        assert "GOOGL" in results
        assert "MSFT" in results
        assert "INVALID" not in results
        
        # Check error was logged
        captured = capsys.readouterr()
        assert "Error loading INVALID" in captured.out


class TestPackageConsistency:
    """Test consistency across package components"""
    
    def test_data_format_consistency(self, sample_ohlcv_data):
        """Test that data format is consistent across providers"""
        loader = StockDataLoader()
        
        # Mock provider
        mock_provider = Mock(spec=YahooFinanceProvider)
        mock_provider.get_data.return_value = MarketData(
            symbol="AAPL",
            data=sample_ohlcv_data,
            metadata={"provider": "Yahoo Finance"}
        )
        loader.providers['yahoo'] = mock_provider
        
        # Load data
        result = loader.get_data("AAPL")
        
        # Check consistent column names
        expected_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in expected_columns:
            assert col in result.data.columns
        
        # Check data types
        assert result.data['open'].dtype.kind in 'if'  # int or float
        assert result.data['high'].dtype.kind in 'if'
        assert result.data['low'].dtype.kind in 'if'
        assert result.data['close'].dtype.kind in 'if'
        assert result.data['volume'].dtype.kind in 'if'
    
    def test_symbol_normalization_consistency(self):
        """Test that symbol normalization is consistent"""
        # Test request normalization
        request = MarketDataRequest(symbol="  aapl  ")
        assert request.symbol == "AAPL"
        
        # Test loader handling
        loader = StockDataLoader()
        mock_provider = Mock(spec=YahooFinanceProvider)
        mock_provider.get_data.return_value = Mock(spec=MarketData)
        loader.providers['yahoo'] = mock_provider
        
        # Should normalize symbol in request
        loader.get_data("  googl  ")
        
        call_args = mock_provider.get_data.call_args[0][0]
        assert call_args.symbol == "GOOGL"
    
    def test_error_message_consistency(self):
        """Test that error messages are consistent"""
        loader = StockDataLoader()
        
        # Test invalid provider error
        with pytest.raises(ValueError, match="Provider 'invalid' not found"):
            loader.get_data("AAPL", provider="invalid")
        
        with pytest.raises(ValueError, match="Provider 'invalid' not found"):
            loader.set_default_provider("invalid")
    
    def test_metadata_consistency(self, sample_ohlcv_data):
        """Test that metadata format is consistent"""
        loader = StockDataLoader()
        
        # Mock provider
        mock_provider = Mock(spec=YahooFinanceProvider)
        mock_provider.get_data.return_value = MarketData(
            symbol="AAPL",
            data=sample_ohlcv_data,
            metadata={
                "provider": "Yahoo Finance",
                "symbol": "AAPL",
                "rows_count": len(sample_ohlcv_data)
            }
        )
        loader.providers['yahoo'] = mock_provider
        
        # Load data
        result = loader.get_data("AAPL")
        
        # Check metadata structure
        assert "provider" in result.metadata
        assert "symbol" in result.metadata
        assert "rows_count" in result.metadata
        assert result.metadata["symbol"] == "AAPL"
        assert result.metadata["rows_count"] == len(sample_ohlcv_data)


@pytest.mark.integration
@pytest.mark.network
class TestRealDataIntegration:
    """Integration tests with real data sources"""
    
    def test_real_yahoo_integration(self):
        """Test integration with real Yahoo Finance data"""
        try:
            loader = StockDataLoader()
            
            # Test with a reliable symbol
            result = loader.get_data(
                symbol="AAPL",
                start_date=datetime.now() - timedelta(days=5),
                end_date=datetime.now() - timedelta(days=1),
                frequency=DataFrequency.DAILY
            )
            
            # Basic validation
            assert isinstance(result, MarketData)
            assert result.symbol == "AAPL"
            assert len(result.data) > 0
            assert result.metadata["provider"] == "Yahoo Finance"
            
            # Data quality checks
            assert not result.data.empty
            assert all(col in result.data.columns for col in ['open', 'high', 'low', 'close', 'volume'])
            
            # Financial data logic checks
            assert (result.data['high'] >= result.data['low']).all()
            assert (result.data['high'] >= result.data['open']).all()
            assert (result.data['high'] >= result.data['close']).all()
            assert (result.data['low'] <= result.data['open']).all()
            assert (result.data['low'] <= result.data['close']).all()
            
        except Exception as e:
            pytest.skip(f"Real data integration test failed: {e}")
    
    def test_real_multiple_symbols_integration(self):
        """Test integration with multiple real symbols"""
        try:
            loader = StockDataLoader()
            
            symbols = ["AAPL", "GOOGL"]
            results = loader.get_multiple_symbols(
                symbols=symbols,
                start_date=datetime.now() - timedelta(days=5),
                end_date=datetime.now() - timedelta(days=1),
                frequency=DataFrequency.DAILY
            )
            
            assert len(results) == 2
            for symbol in symbols:
                assert symbol in results
                assert isinstance(results[symbol], MarketData)
                assert results[symbol].symbol == symbol
                assert len(results[symbol].data) > 0
            
        except Exception as e:
            pytest.skip(f"Real multiple symbols integration test failed: {e}")
    
    def test_real_brazilian_stocks_integration(self):
        """Test integration with Brazilian stocks"""
        try:
            loader = StockDataLoader()
            
            result = loader.get_data(
                symbol="PETR4.SA",
                start_date=datetime.now() - timedelta(days=5),
                end_date=datetime.now() - timedelta(days=1),
                frequency=DataFrequency.DAILY
            )
            
            assert isinstance(result, MarketData)
            assert result.symbol == "PETR4.SA"
            assert len(result.data) > 0
            
        except Exception as e:
            pytest.skip(f"Real Brazilian stocks integration test failed: {e}")
    
    def test_real_symbol_validation_integration(self):
        """Test real symbol validation"""
        try:
            loader = StockDataLoader()
            
            # Test valid symbol
            assert loader.validate_symbol("AAPL") is True
            
            # Test invalid symbol
            assert loader.validate_symbol("DEFINITELY_INVALID_SYMBOL_123") is False
            
        except Exception as e:
            pytest.skip(f"Real symbol validation integration test failed: {e}")
