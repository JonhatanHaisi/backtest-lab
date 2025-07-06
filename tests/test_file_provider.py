"""
Test file for FileDataProvider functionality.
"""
import pytest
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import json
from unittest.mock import Mock

from backtest_lab.data import FileDataProvider, MarketDataRequest, MarketData, DataFrequency


class TestFileDataProvider:
    """Test FileDataProvider class"""
    
    def test_provider_initialization(self):
        """Test FileDataProvider initialization"""
        provider = FileDataProvider()
        assert provider.provider_name == "File Data Provider"
        assert provider.data_directory == Path.cwd()
        assert provider.supported_formats == ['.parquet', '.csv']
    
    def test_provider_initialization_with_directory(self):
        """Test FileDataProvider initialization with custom directory"""
        test_dir = Path("test_data")
        provider = FileDataProvider(test_dir)
        assert provider.data_directory == test_dir
    
    def test_provider_name(self):
        """Test provider name property"""
        provider = FileDataProvider()
        assert provider.provider_name == "File Data Provider"
    
    def test_get_available_symbols_empty_directory(self):
        """Test get_available_symbols with empty directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            provider = FileDataProvider(temp_dir)
            symbols = provider.get_available_symbols()
            assert symbols == []
    
    def test_get_available_symbols_with_files(self):
        """Test get_available_symbols with data files"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test files
            (temp_path / "aapl.parquet").touch()
            (temp_path / "googl.csv").touch()
            (temp_path / "msft.parquet").touch()
            
            provider = FileDataProvider(temp_dir)
            symbols = provider.get_available_symbols()
            
            assert set(symbols) == {'AAPL', 'GOOGL', 'MSFT'}
    
    def test_validate_symbol_existing_file(self):
        """Test validate_symbol with existing file"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            (temp_path / "aapl.parquet").touch()
            
            provider = FileDataProvider(temp_dir)
            assert provider.validate_symbol("AAPL") is True
            assert provider.validate_symbol("aapl") is True
            assert provider.validate_symbol("GOOGL") is False
    
    def test_validate_symbol_nonexistent_directory(self):
        """Test validate_symbol with nonexistent directory"""
        provider = FileDataProvider("nonexistent_directory")
        assert provider.validate_symbol("AAPL") is False
    
    def test_list_files_empty_directory(self):
        """Test list_files with empty directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            provider = FileDataProvider(temp_dir)
            files = provider.list_files()
            
            assert files == {'.parquet': [], '.csv': []}
    
    def test_list_files_with_data(self):
        """Test list_files with data files"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test files
            parquet_file = temp_path / "aapl.parquet"
            csv_file = temp_path / "googl.csv"
            parquet_file.touch()
            csv_file.touch()
            
            provider = FileDataProvider(temp_dir)
            files = provider.list_files()
            
            assert len(files['.parquet']) == 1
            assert len(files['.csv']) == 1
            assert parquet_file in files['.parquet']
            assert csv_file in files['.csv']
    
    def test_get_data_file_not_found(self):
        """Test get_data with nonexistent file"""
        with tempfile.TemporaryDirectory() as temp_dir:
            provider = FileDataProvider(temp_dir)
            request = MarketDataRequest(symbol="AAPL")
            
            with pytest.raises(FileNotFoundError):
                provider.get_data(request)
    
    def test_get_data_with_parquet_file(self):
        """Test get_data with Parquet file"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create sample data
            data = {
                'open': [100.0, 101.0],
                'high': [102.0, 103.0],
                'low': [99.0, 100.0],
                'close': [101.0, 102.0],
                'volume': [1000000, 1100000]
            }
            df = pd.DataFrame(data, index=pd.date_range('2024-01-01', periods=2))
            
            # Save to parquet
            parquet_file = temp_path / "aapl.parquet"
            df.to_parquet(parquet_file)
            
            provider = FileDataProvider(temp_dir)
            request = MarketDataRequest(symbol="AAPL")
            
            market_data = provider.get_data(request)
            
            assert market_data.symbol == "AAPL"
            assert len(market_data.data) == 2
            assert list(market_data.data.columns) == ['open', 'high', 'low', 'close', 'volume']
            assert market_data.metadata['provider'] == "File Data Provider"
    
    def test_get_data_with_csv_file(self):
        """Test get_data with CSV file"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create sample data
            data = {
                'open': [100.0, 101.0],
                'high': [102.0, 103.0],
                'low': [99.0, 100.0],
                'close': [101.0, 102.0],
                'volume': [1000000, 1100000]
            }
            df = pd.DataFrame(data, index=pd.date_range('2024-01-01', periods=2))
            
            # Save to CSV
            csv_file = temp_path / "googl.csv"
            df.to_csv(csv_file)
            
            provider = FileDataProvider(temp_dir)
            request = MarketDataRequest(symbol="GOOGL")
            
            market_data = provider.get_data(request)
            
            assert market_data.symbol == "GOOGL"
            assert len(market_data.data) == 2
            assert list(market_data.data.columns) == ['open', 'high', 'low', 'close', 'volume']
            assert market_data.metadata['provider'] == "File Data Provider"
    
    def test_get_data_with_date_filtering(self):
        """Test get_data with date range filtering"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create sample data with more dates
            data = {
                'open': [100.0, 101.0, 102.0, 103.0, 104.0],
                'high': [102.0, 103.0, 104.0, 105.0, 106.0],
                'low': [99.0, 100.0, 101.0, 102.0, 103.0],
                'close': [101.0, 102.0, 103.0, 104.0, 105.0],
                'volume': [1000000, 1100000, 1200000, 1300000, 1400000]
            }
            df = pd.DataFrame(data, index=pd.date_range('2024-01-01', periods=5))
            
            # Save to parquet
            parquet_file = temp_path / "aapl.parquet"
            df.to_parquet(parquet_file)
            
            provider = FileDataProvider(temp_dir)
            request = MarketDataRequest(
                symbol="AAPL",
                start_date=datetime(2024, 1, 2),
                end_date=datetime(2024, 1, 4)
            )
            
            market_data = provider.get_data(request)
            
            assert len(market_data.data) == 3  # 2024-01-02 to 2024-01-04
            assert market_data.metadata['filtered'] is True
            assert market_data.metadata['original_rows'] == 5
            assert market_data.metadata['filtered_rows'] == 3
    
    def test_get_data_unsupported_format(self):
        """Test get_data with unsupported file format"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create a file with unsupported extension but manually set the path
            # to bypass the _find_file_for_symbol filtering
            unsupported_file = temp_path / "aapl.txt"
            unsupported_file.write_text("test data")
            
            provider = FileDataProvider(temp_dir)
            
            # Manually mock the file finding to return the unsupported file
            provider._find_file_for_symbol = lambda x, y=None: unsupported_file
            
            request = MarketDataRequest(symbol="AAPL")
            
            with pytest.raises(ValueError, match="Unsupported file format"):
                provider.get_data(request)
    
    def test_find_file_for_symbol_case_insensitive(self):
        """Test _find_file_for_symbol with different case variations"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create file with lowercase name
            (temp_path / "aapl.parquet").touch()
            
            provider = FileDataProvider(temp_dir)
            
            # Test finding file with different case variations
            assert provider._find_file_for_symbol("AAPL") is not None
            assert provider._find_file_for_symbol("aapl") is not None
            assert provider._find_file_for_symbol("Aapl") is not None
    
    def test_find_file_for_symbol_different_formats(self):
        """Test _find_file_for_symbol prioritizes Parquet over CSV"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create both parquet and CSV files
            (temp_path / "aapl.parquet").touch()
            (temp_path / "aapl.csv").touch()
            
            provider = FileDataProvider(temp_dir)
            found_file = provider._find_file_for_symbol("AAPL")
            
            # Should prioritize parquet (first in supported_formats list)
            assert found_file.suffix == '.parquet'
