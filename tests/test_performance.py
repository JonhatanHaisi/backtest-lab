"""Performance tests for backtest-lab"""
import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import Mock

from backtest_lab.data import StockDataLoader, DataFrequency, MarketData


class TestPerformance:
    """Performance tests for the package"""
    
    @pytest.mark.slow
    def test_single_symbol_load_performance(self, sample_ohlcv_data):
        """Test performance of loading single symbol"""
        loader = StockDataLoader()
        
        # Mock provider for consistent timing
        mock_provider = Mock()
        mock_provider.get_data.return_value = MarketData(
            symbol="AAPL",
            data=sample_ohlcv_data,
            metadata={"provider": "mock"}
        )
        loader.providers['yahoo'] = mock_provider
        
        # Measure time for single load
        start_time = time.time()
        result = loader.get_data("AAPL")
        end_time = time.time()
        
        load_time = end_time - start_time
        
        # Should be very fast with mock data
        assert load_time < 0.1  # Less than 100ms
        assert isinstance(result, MarketData)
    
    @pytest.mark.slow
    def test_multiple_symbols_load_performance(self, sample_ohlcv_data):
        """Test performance of loading multiple symbols"""
        loader = StockDataLoader()
        
        # Mock provider
        mock_provider = Mock()
        
        def mock_get_data(request):
            # Simulate some processing time
            time.sleep(0.01)  # 10ms per symbol
            return MarketData(
                symbol=request.symbol,
                data=sample_ohlcv_data,
                metadata={"provider": "mock"}
            )
        
        mock_provider.get_data.side_effect = mock_get_data
        loader.providers['yahoo'] = mock_provider
        
        # Test with 10 symbols
        symbols = [f"SYMBOL{i}" for i in range(10)]
        
        start_time = time.time()
        results = loader.get_multiple_symbols(symbols)
        end_time = time.time()
        
        load_time = end_time - start_time
        
        # Should complete all symbols in reasonable time
        # 10 symbols * 10ms + overhead should be < 1 second
        assert load_time < 1.0
        assert len(results) == 10
    
    @pytest.mark.slow
    def test_large_dataset_handling(self):
        """Test handling of large datasets"""
        import pandas as pd
        import numpy as np
        
        # Create large dataset (1 year of minute data)
        dates = pd.date_range(
            start=datetime(2024, 1, 1),
            end=datetime(2024, 12, 31),
            freq='1min'
        )
        
        large_data = pd.DataFrame({
            'open': np.random.uniform(100, 200, len(dates)),
            'high': np.random.uniform(100, 200, len(dates)),
            'low': np.random.uniform(100, 200, len(dates)),
            'close': np.random.uniform(100, 200, len(dates)),
            'volume': np.random.randint(1000, 10000, len(dates))
        }, index=dates)
        
        loader = StockDataLoader()
        
        # Mock provider with large dataset
        mock_provider = Mock()
        mock_provider.get_data.return_value = MarketData(
            symbol="AAPL",
            data=large_data,
            metadata={"provider": "mock", "rows_count": len(large_data)}
        )
        loader.providers['yahoo'] = mock_provider
        
        # Test loading large dataset
        start_time = time.time()
        result = loader.get_data("AAPL")
        end_time = time.time()
        
        load_time = end_time - start_time
        
        # Should handle large dataset efficiently
        assert load_time < 1.0  # Less than 1 second
        assert len(result.data) > 100000  # Should have lots of data
        assert isinstance(result, MarketData)
    
    @pytest.mark.slow
    def test_memory_usage_with_multiple_symbols(self, sample_ohlcv_data):
        """Test memory usage with multiple symbols"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        loader = StockDataLoader()
        
        # Mock provider
        mock_provider = Mock()
        
        def mock_get_data(request):
            return MarketData(
                symbol=request.symbol,
                data=sample_ohlcv_data.copy(),  # Copy to simulate memory usage
                metadata={"provider": "mock"}
            )
        
        mock_provider.get_data.side_effect = mock_get_data
        loader.providers['yahoo'] = mock_provider
        
        # Load many symbols
        symbols = [f"SYMBOL{i}" for i in range(50)]
        results = loader.get_multiple_symbols(symbols)
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable
        # Allow up to 100MB increase for 50 symbols
        assert memory_increase < 100 * 1024 * 1024  # 100MB
        assert len(results) == 50
    
    @pytest.mark.slow
    def test_concurrent_requests_performance(self, sample_ohlcv_data):
        """Test performance with concurrent requests"""
        import threading
        import queue
        
        loader = StockDataLoader()
        
        # Mock provider
        mock_provider = Mock()
        mock_provider.get_data.return_value = MarketData(
            symbol="AAPL",
            data=sample_ohlcv_data,
            metadata={"provider": "mock"}
        )
        loader.providers['yahoo'] = mock_provider
        
        results_queue = queue.Queue()
        
        def load_data():
            try:
                result = loader.get_data("AAPL")
                results_queue.put(("success", result))
            except Exception as e:
                results_queue.put(("error", str(e)))
        
        # Create multiple threads
        threads = []
        start_time = time.time()
        
        for _ in range(10):
            thread = threading.Thread(target=load_data)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Collect results
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())
        
        # Should complete all requests quickly
        assert total_time < 1.0  # Less than 1 second
        assert len(results) == 10
        
        # All should be successful
        success_count = sum(1 for result_type, _ in results if result_type == "success")
        assert success_count == 10
    
    @pytest.mark.slow
    def test_request_creation_performance(self):
        """Test performance of creating many requests"""
        from backtest_lab.data.base import MarketDataRequest
        
        start_time = time.time()
        
        # Create many requests
        requests = []
        for i in range(1000):
            request = MarketDataRequest(
                symbol=f"SYMBOL{i}",
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2024, 1, 31),
                frequency=DataFrequency.DAILY
            )
            requests.append(request)
        
        end_time = time.time()
        creation_time = end_time - start_time
        
        # Should create requests quickly
        assert creation_time < 1.0  # Less than 1 second for 1000 requests
        assert len(requests) == 1000
        
        # Verify all requests are valid
        for i, request in enumerate(requests):
            assert request.symbol == f"SYMBOL{i}"
            assert request.frequency == DataFrequency.DAILY
    
    @pytest.mark.slow
    def test_data_processing_performance(self, sample_ohlcv_data):
        """Test performance of data processing operations"""
        # Create larger dataset for meaningful timing
        large_sample = sample_ohlcv_data
        for _ in range(100):  # Replicate data 100 times
            large_sample = large_sample.append(sample_ohlcv_data, ignore_index=False)
        
        market_data = MarketData(
            symbol="AAPL",
            data=large_sample,
            metadata={"provider": "test"}
        )
        
        start_time = time.time()
        
        # Perform various operations
        df = market_data.data
        
        # Calculate some statistics (common operations)
        mean_close = df['close'].mean()
        max_high = df['high'].max()
        min_low = df['low'].min()
        volume_sum = df['volume'].sum()
        
        # Calculate returns
        returns = df['close'].pct_change()
        
        # Calculate moving averages
        ma_20 = df['close'].rolling(window=20).mean()
        ma_50 = df['close'].rolling(window=50).mean()
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Should process data efficiently
        assert processing_time < 1.0  # Less than 1 second
        assert mean_close > 0
        assert max_high > 0
        assert min_low > 0
        assert volume_sum > 0
        assert len(returns) == len(df)
        assert len(ma_20) == len(df)
        assert len(ma_50) == len(df)


class TestScalability:
    """Test scalability of the package"""
    
    @pytest.mark.slow
    def test_scaling_with_symbol_count(self, sample_ohlcv_data):
        """Test how performance scales with number of symbols"""
        loader = StockDataLoader()
        
        # Mock provider
        mock_provider = Mock()
        
        def mock_get_data(request):
            return MarketData(
                symbol=request.symbol,
                data=sample_ohlcv_data,
                metadata={"provider": "mock"}
            )
        
        mock_provider.get_data.side_effect = mock_get_data
        loader.providers['yahoo'] = mock_provider
        
        # Test with increasing number of symbols
        symbol_counts = [1, 5, 10, 20, 50]
        times = []
        
        for count in symbol_counts:
            symbols = [f"SYMBOL{i}" for i in range(count)]
            
            start_time = time.time()
            results = loader.get_multiple_symbols(symbols)
            end_time = time.time()
            
            load_time = end_time - start_time
            times.append(load_time)
            
            assert len(results) == count
        
        # Performance should scale roughly linearly
        # (allowing for some overhead)
        for i in range(1, len(times)):
            ratio = times[i] / times[i-1]
            symbol_ratio = symbol_counts[i] / symbol_counts[i-1]
            
            # Time ratio shouldn't be much worse than symbol ratio
            assert ratio < symbol_ratio * 2  # Allow 2x overhead
    
    @pytest.mark.slow
    def test_scaling_with_data_size(self):
        """Test how performance scales with data size"""
        import pandas as pd
        import numpy as np
        
        loader = StockDataLoader()
        
        # Test with increasing data sizes
        data_sizes = [100, 500, 1000, 5000]
        times = []
        
        for size in data_sizes:
            # Create dataset of specified size
            dates = pd.date_range(
                start=datetime(2024, 1, 1),
                periods=size,
                freq='D'
            )
            
            data = pd.DataFrame({
                'open': np.random.uniform(100, 200, size),
                'high': np.random.uniform(100, 200, size),
                'low': np.random.uniform(100, 200, size),
                'close': np.random.uniform(100, 200, size),
                'volume': np.random.randint(1000, 10000, size)
            }, index=dates)
            
            # Mock provider
            mock_provider = Mock()
            mock_provider.get_data.return_value = MarketData(
                symbol="AAPL",
                data=data,
                metadata={"provider": "mock"}
            )
            loader.providers['yahoo'] = mock_provider
            
            # Measure load time
            start_time = time.time()
            result = loader.get_data("AAPL")
            end_time = time.time()
            
            load_time = end_time - start_time
            times.append(load_time)
            
            assert len(result.data) == size
        
        # Performance should scale reasonably with data size
        # Allow for some non-linear scaling due to overhead
        for i in range(1, len(times)):
            ratio = times[i] / times[i-1]
            size_ratio = data_sizes[i] / data_sizes[i-1]
            
            # Time ratio shouldn't be much worse than size ratio
            assert ratio < size_ratio * 3  # Allow 3x overhead
    
    @pytest.mark.slow
    def test_memory_efficiency(self, sample_ohlcv_data):
        """Test memory efficiency with large operations"""
        import psutil
        import os
        import gc
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        loader = StockDataLoader()
        
        # Mock provider
        mock_provider = Mock()
        
        def mock_get_data(request):
            return MarketData(
                symbol=request.symbol,
                data=sample_ohlcv_data.copy(),
                metadata={"provider": "mock"}
            )
        
        mock_provider.get_data.side_effect = mock_get_data
        loader.providers['yahoo'] = mock_provider
        
        # Load and release many symbols
        for batch in range(5):  # 5 batches
            symbols = [f"BATCH{batch}_SYMBOL{i}" for i in range(20)]
            results = loader.get_multiple_symbols(symbols)
            
            # Verify results
            assert len(results) == 20
            
            # Clear results to allow garbage collection
            del results
            gc.collect()
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory should not grow excessively
        # Allow up to 50MB increase for all operations
        assert memory_increase < 50 * 1024 * 1024  # 50MB


class TestBenchmarks:
    """Benchmark tests for performance comparison"""
    
    @pytest.mark.slow
    def test_request_creation_benchmark(self):
        """Benchmark request creation"""
        from backtest_lab.data.base import MarketDataRequest
        
        iterations = 10000
        
        start_time = time.time()
        
        for i in range(iterations):
            request = MarketDataRequest(
                symbol=f"SYMBOL{i}",
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2024, 1, 31),
                frequency=DataFrequency.DAILY
            )
        
        end_time = time.time()
        total_time = end_time - start_time
        
        requests_per_second = iterations / total_time
        
        # Should be able to create many requests per second
        assert requests_per_second > 1000  # At least 1000 requests/second
        
        print(f"Request creation benchmark: {requests_per_second:.0f} requests/second")
    
    @pytest.mark.slow
    def test_data_loading_benchmark(self, sample_ohlcv_data):
        """Benchmark data loading"""
        loader = StockDataLoader()
        
        # Mock provider
        mock_provider = Mock()
        mock_provider.get_data.return_value = MarketData(
            symbol="AAPL",
            data=sample_ohlcv_data,
            metadata={"provider": "mock"}
        )
        loader.providers['yahoo'] = mock_provider
        
        iterations = 1000
        
        start_time = time.time()
        
        for i in range(iterations):
            result = loader.get_data(f"SYMBOL{i}")
            assert isinstance(result, MarketData)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        loads_per_second = iterations / total_time
        
        # Should be able to load many symbols per second
        assert loads_per_second > 100  # At least 100 loads/second
        
        print(f"Data loading benchmark: {loads_per_second:.0f} loads/second")
    
    @pytest.mark.slow
    def test_multiple_symbols_benchmark(self, sample_ohlcv_data):
        """Benchmark multiple symbols loading"""
        loader = StockDataLoader()
        
        # Mock provider
        mock_provider = Mock()
        
        def mock_get_data(request):
            return MarketData(
                symbol=request.symbol,
                data=sample_ohlcv_data,
                metadata={"provider": "mock"}
            )
        
        mock_provider.get_data.side_effect = mock_get_data
        loader.providers['yahoo'] = mock_provider
        
        symbols = [f"SYMBOL{i}" for i in range(100)]
        
        start_time = time.time()
        results = loader.get_multiple_symbols(symbols)
        end_time = time.time()
        
        total_time = end_time - start_time
        symbols_per_second = len(symbols) / total_time
        
        assert len(results) == 100
        assert symbols_per_second > 50  # At least 50 symbols/second
        
        print(f"Multiple symbols benchmark: {symbols_per_second:.0f} symbols/second")
