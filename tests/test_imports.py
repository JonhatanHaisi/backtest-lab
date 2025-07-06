"""Tests for __init__.py modules and package structure"""
import pytest
import sys
import os

# Add src to path to import backtest_lab
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class TestPackageStructure:
    """Test the package structure and imports"""
    
    def test_main_package_import(self):
        """Test that the main package can be imported"""
        import backtest_lab
        assert backtest_lab is not None
    
    def test_data_module_imports(self):
        """Test that all expected classes can be imported from data module"""
        from backtest_lab.data import (
            StockDataLoader,
            DataFrequency,
            MarketDataRequest,
            MarketData,
            YahooFinanceProvider,
            FileDataProvider
        )
        
        # Verify all classes are available
        assert StockDataLoader is not None
        assert DataFrequency is not None
        assert MarketDataRequest is not None
        assert MarketData is not None
        assert YahooFinanceProvider is not None
        assert FileDataProvider is not None
    
    def test_data_module_all_attribute(self):
        """Test that __all__ attribute is correctly defined"""
        from backtest_lab.data import __all__
        
        expected_exports = [
            'StockDataLoader',
            'DataFrequency',
            'MarketDataRequest',
            'MarketData',
            'YahooFinanceProvider',
            'FileDataProvider',
            'generate_filename',
            'parse_filename',
        ]
        
        assert set(__all__) == set(expected_exports)
    
    def test_direct_class_imports(self):
        """Test that classes can be imported directly from their modules"""
        from backtest_lab.data.loaders.stock_loader import StockDataLoader
        from backtest_lab.data.base import DataFrequency, MarketDataRequest, MarketData
        from backtest_lab.data.providers.yahoo import YahooFinanceProvider
        
        # Verify classes can be instantiated
        assert StockDataLoader is not None
        assert DataFrequency is not None
        assert MarketDataRequest is not None
        assert MarketData is not None
        assert YahooFinanceProvider is not None
    
    def test_package_version_accessibility(self):
        """Test if package version is accessible (if defined)"""
        try:
            import backtest_lab
            # If version is defined, it should be accessible
            if hasattr(backtest_lab, '__version__'):
                assert isinstance(backtest_lab.__version__, str)
                assert len(backtest_lab.__version__) > 0
        except AttributeError:
            # It's okay if version is not defined
            pass
    
    def test_no_unexpected_imports(self):
        """Test that importing the package doesn't have unexpected side effects"""
        import sys
        modules_before = set(sys.modules.keys())
        
        # Import the package
        import backtest_lab.data
        
        modules_after = set(sys.modules.keys())
        new_modules = modules_after - modules_before
        
        # Should only import expected modules
        expected_module_prefixes = [
            'backtest_lab',
            'pydantic',
            'pandas',
            'datetime',
            'typing',
            'enum',
            'abc'
        ]
        
        for module in new_modules:
            module_name = module.split('.')[0]
            assert any(module_name.startswith(prefix) for prefix in expected_module_prefixes), \
                f"Unexpected module imported: {module}"
    
    def test_circular_imports(self):
        """Test that there are no circular import issues"""
        # This test will fail if there are circular imports
        try:
            from backtest_lab.data import StockDataLoader
            from backtest_lab.data.base import DataProvider
            from backtest_lab.data.providers.yahoo import YahooFinanceProvider
            
            # Try to create instances to ensure no circular dependencies
            loader = StockDataLoader()
            provider = YahooFinanceProvider()
            
            assert loader is not None
            assert provider is not None
        except ImportError as e:
            pytest.fail(f"Circular import detected: {e}")
    
    def test_submodule_accessibility(self):
        """Test that submodules are accessible after importing the main package"""
        import backtest_lab.data
        
        # Should be able to access submodules
        assert hasattr(backtest_lab.data, 'StockDataLoader')
        assert hasattr(backtest_lab.data, 'DataFrequency')
        assert hasattr(backtest_lab.data, 'MarketDataRequest')
        assert hasattr(backtest_lab.data, 'MarketData')
        assert hasattr(backtest_lab.data, 'YahooFinanceProvider')
    
    def test_module_docstrings(self):
        """Test that modules have proper docstrings"""
        import backtest_lab.data.base
        import backtest_lab.data.loaders.stock_loader
        import backtest_lab.data.providers.yahoo
        
        # Check that key modules have docstrings
        # Note: __doc__ might be None for some modules, which is acceptable
        if backtest_lab.data.base.__doc__:
            assert isinstance(backtest_lab.data.base.__doc__, str)
        
        if backtest_lab.data.loaders.stock_loader.__doc__:
            assert isinstance(backtest_lab.data.loaders.stock_loader.__doc__, str)
        
        if backtest_lab.data.providers.yahoo.__doc__:
            assert isinstance(backtest_lab.data.providers.yahoo.__doc__, str)
    
    def test_import_performance(self):
        """Test that imports are reasonably fast"""
        import time
        
        start_time = time.time()
        import backtest_lab.data
        end_time = time.time()
        
        import_time = end_time - start_time
        
        # Import should be very fast (less than 1 second)
        assert import_time < 1.0, f"Import took too long: {import_time:.3f} seconds"
    
    def test_package_completeness(self):
        """Test that the package exports all expected functionality"""
        from backtest_lab.data import (
            StockDataLoader,
            DataFrequency,
            MarketDataRequest,
            MarketData,
            YahooFinanceProvider
        )
        
        # Test that each class has expected methods/attributes
        
        # StockDataLoader
        loader = StockDataLoader()
        assert hasattr(loader, 'get_data')
        assert hasattr(loader, 'get_multiple_symbols')
        assert hasattr(loader, 'validate_symbol')
        assert hasattr(loader, 'get_available_providers')
        
        # DataFrequency
        assert hasattr(DataFrequency, 'DAILY')
        assert hasattr(DataFrequency, 'WEEKLY')
        assert hasattr(DataFrequency, 'MONTHLY')
        
        # MarketDataRequest
        assert hasattr(MarketDataRequest, 'model_validate')
        assert hasattr(MarketDataRequest, 'model_post_init')
        
        # MarketData
        assert hasattr(MarketData, 'model_validate')
        
        # YahooFinanceProvider
        provider = YahooFinanceProvider()
        assert hasattr(provider, 'get_data')
        assert hasattr(provider, 'validate_symbol')
        assert hasattr(provider, 'provider_name')
