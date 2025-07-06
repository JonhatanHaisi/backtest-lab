"""
Test file for FileDataProvider functionality.
"""
import pytest
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import shutil
from unittest.mock import Mock, patch, mock_open

from backtest_lab.data import FileDataProvider, MarketDataRequest, MarketData, DataFrequency


class TestFileDataProvider:
    """Test FileDataProvider class"""
    
    def setup_method(self):
        """Setup method run before each test method"""
        self.temp_dir = tempfile.mkdtemp()
        self.provider = FileDataProvider(data_directory=self.temp_dir)
        
        # Create sample data for testing
        self.sample_data = pd.DataFrame({
            'open': [100.0, 101.0, 102.0, 103.0, 104.0],
            'high': [105.0, 106.0, 107.0, 108.0, 109.0],
            'low': [95.0, 96.0, 97.0, 98.0, 99.0],
            'close': [102.0, 103.0, 104.0, 105.0, 106.0],
            'volume': [1000, 1100, 1200, 1300, 1400]
        }, index=pd.date_range('2023-01-01', periods=5, freq='D'))
    
    def teardown_method(self):
        """Cleanup after each test method"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
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
    
    def test_initialization_with_string_path(self):
        """Test initialization with string path."""
        provider = FileDataProvider(data_directory="/tmp/test")
        assert provider.data_directory == Path("/tmp/test")
        assert provider.supported_formats == [".parquet", ".csv"]

    def test_initialization_with_path_object(self):
        """Test initialization with Path object."""
        path_obj = Path("/tmp/test")
        provider = FileDataProvider(data_directory=path_obj)
        assert provider.data_directory == path_obj

    def test_initialization_with_none(self):
        """Test initialization with None defaults to current directory."""
        provider = FileDataProvider(data_directory=None)
        assert provider.data_directory == Path.cwd()
    
    def test_get_available_symbols_empty_directory(self):
        """Test get_available_symbols with empty directory"""
        # Use a fresh empty directory for this test
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
    
    def test_initialization_with_string_path(self):
        """Test initialization with string path."""
        provider = FileDataProvider(data_directory="/tmp/test")
        assert provider.data_directory == Path("/tmp/test")
        assert provider.supported_formats == [".parquet", ".csv"]

    def test_initialization_with_path_object(self):
        """Test initialization with Path object."""
        path_obj = Path("/tmp/test")
        provider = FileDataProvider(data_directory=path_obj)
        assert provider.data_directory == path_obj

    def test_initialization_with_none(self):
        """Test initialization with None defaults to current directory."""
        provider = FileDataProvider(data_directory=None)
        assert provider.data_directory == Path.cwd()

    def test_get_data_with_exact_filename_match(self):
        """Test get_data with exact filename match."""
        # Create a parquet file using the correct naming convention
        filename = "aapl_1d.parquet"  # symbol_frequency.extension
        file_path = Path(self.temp_dir) / filename
        self.sample_data.to_parquet(file_path)
        
        request = MarketDataRequest(
            symbol="AAPL",
            frequency=DataFrequency.DAILY,
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 1, 5)
        )
        
        result = self.provider.get_data(request)
        
        assert isinstance(result, MarketData)
        assert result.symbol == "AAPL"
        assert len(result.data) == 5

    def test_get_data_with_case_insensitive_symbol(self):
        """Test get_data with case-insensitive symbol matching."""
        # Create a file with uppercase symbol
        filename = "aapl_1d.parquet"
        file_path = Path(self.temp_dir) / filename
        self.sample_data.to_parquet(file_path)
        
        # Request with lowercase symbol
        request = MarketDataRequest(
            symbol="aapl",
            frequency=DataFrequency.DAILY
        )
        
        result = self.provider.get_data(request)
        # The provider normalizes symbols to uppercase
        assert result.symbol == "AAPL"

    def test_get_data_with_csv_format(self):
        """Test get_data with CSV format."""
        filename = "aapl_1d.csv"
        file_path = Path(self.temp_dir) / filename
        self.sample_data.to_csv(file_path)
        
        request = MarketDataRequest(
            symbol="AAPL",
            frequency=DataFrequency.DAILY
        )
        
        result = self.provider.get_data(request)
        assert isinstance(result, MarketData)
        assert len(result.data) == 5

    def test_get_data_with_date_filtering(self):
        """Test get_data with date filtering."""
        filename = "aapl_1d.parquet"  # Use correct format
        file_path = Path(self.temp_dir) / filename
        
        # Create larger dataset
        large_data = pd.DataFrame({
            'open': [100 + i for i in range(10)],
            'high': [105 + i for i in range(10)],
            'low': [95 + i for i in range(10)],
            'close': [102 + i for i in range(10)],
            'volume': [1000 + i * 100 for i in range(10)]
        }, index=pd.date_range('2023-01-01', periods=10, freq='D'))
        
        large_data.to_parquet(file_path)
        
        request = MarketDataRequest(
            symbol="AAPL",
            frequency=DataFrequency.DAILY,
            start_date=datetime(2023, 1, 3),
            end_date=datetime(2023, 1, 7)
        )
        
        result = self.provider.get_data(request)
        
        # Should be filtered to 5 days
        assert len(result.data) == 5
        assert result.data.index[0] == pd.Timestamp('2023-01-03')
        assert result.data.index[-1] == pd.Timestamp('2023-01-07')

    def test_get_data_file_not_found(self):
        """Test get_data when no file is found."""
        request = MarketDataRequest(
            symbol="NONEXISTENT",
            frequency=DataFrequency.DAILY
        )
        
        with pytest.raises(FileNotFoundError, match="No data file found for symbol"):
            self.provider.get_data(request)

    def test_get_data_unsupported_format(self):
        """Test get_data with unsupported file format."""
        # We can't directly test unsupported format since _find_file_for_symbol 
        # only looks for supported formats. This test verifies that behavior.
        filename = "aapl_1d.txt"
        file_path = Path(self.temp_dir) / filename
        file_path.write_text("dummy content")
        
        request = MarketDataRequest(
            symbol="AAPL",
            frequency=DataFrequency.DAILY
        )
        
        # Should raise FileNotFoundError because .txt is not in supported_formats
        with pytest.raises(FileNotFoundError):
            self.provider.get_data(request)

    def test_get_data_with_corrupted_parquet(self):
        """Test get_data with corrupted parquet file."""
        filename = "AAPL_1d_2023-01-01_2023-01-05.parquet"
        file_path = Path(self.temp_dir) / filename
        
        # Create corrupted parquet file
        with open(file_path, 'w') as f:
            f.write("corrupted content")
        
        request = MarketDataRequest(
            symbol="AAPL",
            frequency=DataFrequency.DAILY
        )
        
        with pytest.raises(Exception):  # Should raise some read error
            self.provider.get_data(request)

    def test_get_data_with_corrupted_csv(self):
        """Test get_data with corrupted CSV file."""
        filename = "AAPL_1d_2023-01-01_2023-01-05.csv"
        file_path = Path(self.temp_dir) / filename
        
        # Create corrupted CSV file
        with open(file_path, 'w') as f:
            f.write("corrupted,csv,content\n1,2")  # Incomplete CSV
        
        request = MarketDataRequest(
            symbol="AAPL",
            frequency=DataFrequency.DAILY
        )
        
        with pytest.raises(Exception):  # Should raise some read error
            self.provider.get_data(request)

    def test_get_available_symbols_with_various_formats(self):
        """Test get_available_symbols with various file formats."""
        # Create files with different formats
        files = [
            "aapl_1d.parquet",
            "googl_1d.csv",
            "msft_1h.parquet",
            "INVALID_FILE.txt",  # Should be ignored
            "tsla_1d.parquet"
        ]
        
        for filename in files:
            file_path = Path(self.temp_dir) / filename
            if filename.endswith('.parquet'):
                self.sample_data.to_parquet(file_path)
            elif filename.endswith('.csv'):
                self.sample_data.to_csv(file_path)
            else:
                file_path.write_text("dummy")
        
        symbols = self.provider.get_available_symbols()
        
        # The parse_filename function will extract symbols correctly from structured filenames
        expected_symbols = {'AAPL', 'GOOGL', 'MSFT', 'TSLA'}
        assert set(symbols) == expected_symbols

    def test_get_available_symbols_empty_directory(self):
        """Test get_available_symbols with empty directory."""
        empty_provider = FileDataProvider(data_directory=tempfile.mkdtemp())
        symbols = empty_provider.get_available_symbols()
        assert symbols == []

    def test_get_available_symbols_nonexistent_directory(self):
        """Test get_available_symbols with non-existent directory."""
        nonexistent_provider = FileDataProvider(data_directory="/nonexistent/path")
        symbols = nonexistent_provider.get_available_symbols()
        assert symbols == []

    def test_validate_symbol_with_exact_match(self):
        """Test validate_symbol with exact filename match."""
        filename = "aapl_1d.parquet"  # Use the correct format that generate_filename creates
        file_path = Path(self.temp_dir) / filename
        self.sample_data.to_parquet(file_path)
        
        is_valid = self.provider.validate_symbol("AAPL")
        assert is_valid is True

    def test_validate_symbol_case_insensitive(self):
        """Test validate_symbol with case-insensitive matching."""
        filename = "aapl_1d.parquet"  # Use the correct format
        file_path = Path(self.temp_dir) / filename
        self.sample_data.to_parquet(file_path)
        
        is_valid = self.provider.validate_symbol("aapl")
        assert is_valid is True

    def test_validate_symbol_nonexistent(self):
        """Test validate_symbol with non-existent symbol."""
        is_valid = self.provider.validate_symbol("NONEXISTENT")
        assert is_valid is False

    def test_validate_symbol_nonexistent_directory(self):
        """Test validate_symbol with non-existent directory."""
        nonexistent_provider = FileDataProvider(data_directory="/nonexistent/path")
        is_valid = nonexistent_provider.validate_symbol("AAPL")
        assert is_valid is False

    def test_find_file_for_symbol_with_frequency_preference(self):
        """Test _find_file_for_symbol with frequency preference."""
        # Create files with different frequencies
        files = [
            "aapl_1d.parquet",
            "aapl_1h.parquet", 
            "aapl_1m.parquet"
        ]
        
        for filename in files:
            file_path = Path(self.temp_dir) / filename
            self.sample_data.to_parquet(file_path)
        
        # Should prefer the exact frequency match
        found_file = self.provider._find_file_for_symbol("AAPL", DataFrequency.HOUR_1)
        assert found_file is not None
        assert "1h" in found_file.name

    def test_find_file_for_symbol_fallback_to_any(self):
        """Test _find_file_for_symbol fallback to any frequency."""
        filename = "aapl_1d.parquet"
        file_path = Path(self.temp_dir) / filename
        self.sample_data.to_parquet(file_path)
        
        # Request different frequency, should fallback to available
        found_file = self.provider._find_file_for_symbol("AAPL", DataFrequency.HOUR_1)
        assert found_file is not None
        assert "1d" in found_file.name

    def test_find_file_for_symbol_prefer_parquet_over_csv(self):
        """Test _find_file_for_symbol prefers parquet over CSV."""
        # Create both CSV and parquet files
        parquet_file = Path(self.temp_dir) / "aapl_1d.parquet"
        csv_file = Path(self.temp_dir) / "aapl_1d.csv"
        
        self.sample_data.to_parquet(parquet_file)
        self.sample_data.to_csv(csv_file)
        
        found_file = self.provider._find_file_for_symbol("AAPL", DataFrequency.DAILY)
        assert found_file is not None
        assert found_file.suffix == ".parquet"

    def test_list_files_with_pattern_matching(self):
        """Test _list_files with pattern matching."""
        files = [
            "aapl_1d.parquet",
            "aapl_1h.parquet",
            "googl_1d.parquet",
            "invalid_file.txt"
        ]
        
        for filename in files:
            file_path = Path(self.temp_dir) / filename
            if filename.endswith('.parquet'):
                self.sample_data.to_parquet(file_path)
            else:
                file_path.write_text("dummy")
        
        # List files for AAPL (case insensitive search)
        aapl_files = [f for f in self.provider.list_files()['.parquet'] if 'aapl' in f.name.lower()]
        assert len(aapl_files) == 2
        assert all("aapl" in f.name.lower() for f in aapl_files)

    def test_list_files_empty_directory(self):
        """Test list_files with empty directory."""
        empty_provider = FileDataProvider(data_directory=tempfile.mkdtemp())
        files = empty_provider.list_files()
        assert files == {'.parquet': [], '.csv': []}

    def test_parquet_file_loading_integration(self):
        """Test parquet file loading with proper file structure."""
        filename = "aapl_1d.parquet"  # Use correct format
        file_path = Path(self.temp_dir) / filename
        
        # Save with reset index to simulate different save formats
        data_with_reset_index = self.sample_data.reset_index()
        data_with_reset_index.to_parquet(file_path)
        
        request = MarketDataRequest(
            symbol="AAPL",
            frequency=DataFrequency.DAILY
        )
        result = self.provider.get_data(request)
        assert result.symbol == "AAPL"
        assert len(result.data) > 0

    def test_csv_file_loading_integration(self):
        """Test CSV file loading with proper file structure."""
        filename = "aapl_1d.csv"  # Use correct format
        file_path = Path(self.temp_dir) / filename
        
        # Save CSV with date column
        data_with_date_col = self.sample_data.reset_index()
        data_with_date_col.to_csv(file_path, index=False)
        
        request = MarketDataRequest(
            symbol="AAPL",
            frequency=DataFrequency.DAILY
        )
        result = self.provider.get_data(request)
        assert result.symbol == "AAPL"
        assert len(result.data) > 0

    def test_date_filtering_integration(self):
        """Test date filtering functionality."""
        filename = "aapl_1d.parquet"  # Use correct format
        file_path = Path(self.temp_dir) / filename
        self.sample_data.to_parquet(file_path)
        
        request = MarketDataRequest(
            symbol="AAPL",
            frequency=DataFrequency.DAILY,
            start_date=datetime(2023, 1, 2),
            end_date=datetime(2023, 1, 4)
        )
        
        result = self.provider.get_data(request)
        assert len(result.data) == 3  # Should include 2nd, 3rd, 4th

    def test_provider_metadata_integration(self):
        """Test provider metadata is properly added."""
        filename = "aapl_1d.parquet"  # Use correct format
        file_path = Path(self.temp_dir) / filename
        self.sample_data.to_parquet(file_path)
        
        request = MarketDataRequest(
            symbol="AAPL",
            frequency=DataFrequency.DAILY
        )
        
        result = self.provider.get_data(request)
        assert result.metadata is not None
        assert result.metadata.get('provider') == 'File Data Provider'
        assert 'source_file' in result.metadata

    def test_multiple_file_formats_integration(self):
        """Test handling of multiple file formats."""
        # Create both CSV and parquet files
        parquet_file = Path(self.temp_dir) / "aapl_1d.parquet"  # Use correct format
        csv_file = Path(self.temp_dir) / "googl_1d.csv"  # Use correct format
        
        self.sample_data.to_parquet(parquet_file)
        self.sample_data.to_csv(csv_file)
        
        # Test parquet loading
        request1 = MarketDataRequest(symbol="AAPL", frequency=DataFrequency.DAILY)
        result1 = self.provider.get_data(request1)
        assert result1.symbol == "AAPL"
        
        # Test CSV loading
        request2 = MarketDataRequest(symbol="GOOGL", frequency=DataFrequency.DAILY)
        result2 = self.provider.get_data(request2)
        assert result2.symbol == "GOOGL"

    def test_provider_with_nested_directories(self):
        """Test provider behavior with nested directories."""
        nested_dir = Path(self.temp_dir) / "nested" / "subdirectory"
        nested_dir.mkdir(parents=True, exist_ok=True)
        
        # Create file in nested directory
        filename = "AAPL_1d_2023-01-01_2023-01-05.parquet"
        file_path = nested_dir / filename
        self.sample_data.to_parquet(file_path)
        
        # Provider should only look in its data directory, not nested
        request = MarketDataRequest(
            symbol="AAPL",
            frequency=DataFrequency.DAILY
        )
        
        with pytest.raises(FileNotFoundError):
            self.provider.get_data(request)
