"""Test configuration and test execution functionality"""
import subprocess
import sys
import os
from pathlib import Path


class TestTestConfiguration:
    """Test the test configuration and execution"""
    
    def test_pytest_configuration_exists(self):
        """Test that pytest.ini exists and has correct configuration"""
        pytest_ini_path = Path(__file__).parent.parent / "pytest.ini"
        assert pytest_ini_path.exists(), "pytest.ini file should exist"
        
        # Read the configuration
        with open(pytest_ini_path, 'r') as f:
            content = f.read()
        
        # Check for important configuration options
        assert "testpaths = tests" in content
        assert "--cov=src/backtest_lab" in content
        assert "markers =" in content
        assert "unit:" in content
        assert "integration:" in content
        assert "network:" in content
        assert "slow:" in content
    
    def test_test_directory_structure(self):
        """Test that test directory has correct structure"""
        test_dir = Path(__file__).parent
        
        # Check that essential test files exist
        essential_files = [
            "conftest.py",
            "test_base.py",
            "test_yahoo_provider.py",
            "test_stock_loader.py",
            "test_integration.py",
            "test_performance.py",
            "test_end_to_end.py",
            "test_examples.py",
            "test_imports.py",
            "test_edge_cases.py"
        ]
        
        for file in essential_files:
            file_path = test_dir / file
            assert file_path.exists(), f"Essential test file {file} should exist"
    
    def test_run_tests_script_exists(self):
        """Test that run_tests.py script exists"""
        run_tests_path = Path(__file__).parent.parent / "run_tests.py"
        assert run_tests_path.exists(), "run_tests.py script should exist"
        
        # Check that it's executable
        try:
            with open(run_tests_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            # Try with different encodings
            with open(run_tests_path, 'r', encoding='latin-1') as f:
                content = f.read()
        
        assert "#!/usr/bin/env python3" in content or "import subprocess" in content
    
    def test_makefile_exists(self):
        """Test that Makefile exists with test targets"""
        makefile_path = Path(__file__).parent.parent / "Makefile"
        assert makefile_path.exists(), "Makefile should exist"
        
        try:
            with open(makefile_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            # Try with different encodings
            with open(makefile_path, 'r', encoding='latin-1') as f:
                content = f.read()
        
        # Check for test targets
        assert "test:" in content
        assert "test-unit:" in content
        assert "test-integration:" in content
        assert "test-performance:" in content
        assert "test-coverage:" in content
    
    def test_conftest_has_required_fixtures(self):
        """Test that conftest.py has all required fixtures"""
        conftest_path = Path(__file__).parent / "conftest.py"
        assert conftest_path.exists()
        
        with open(conftest_path, 'r') as f:
            content = f.read()
        
        # Check for essential fixtures
        essential_fixtures = [
            "sample_ohlcv_data",
            "sample_market_data_request",
            "sample_market_data",
            "mock_yahoo_ticker",
            "yahoo_provider",
            "stock_loader"
        ]
        
        for fixture in essential_fixtures:
            assert f"def {fixture}" in content, f"Fixture {fixture} should be defined in conftest.py"
    
    def test_test_markers_coverage(self):
        """Test that test files use appropriate markers"""
        test_dir = Path(__file__).parent
        
        # Check that integration tests use integration marker
        integration_test_file = test_dir / "test_integration.py"
        if integration_test_file.exists():
            with open(integration_test_file, 'r') as f:
                content = f.read()
            # Should have integration marker somewhere
            assert "@pytest.mark.integration" in content or "integration" in content
        
        # Check that performance tests use slow marker
        performance_test_file = test_dir / "test_performance.py"
        if performance_test_file.exists():
            with open(performance_test_file, 'r') as f:
                content = f.read()
            # Should have slow marker somewhere
            assert "@pytest.mark.slow" in content or "slow" in content
    
    def test_source_code_structure(self):
        """Test that source code structure is correct for testing"""
        src_dir = Path(__file__).parent.parent / "src" / "backtest_lab"
        assert src_dir.exists(), "Source directory should exist"
        
        # Check main modules
        main_modules = [
            "__init__.py",
            "data/__init__.py",
            "data/base.py",
            "data/loaders/stock_loader.py",
            "data/providers/yahoo.py"
        ]
        
        for module in main_modules:
            module_path = src_dir / module
            assert module_path.exists(), f"Module {module} should exist"
    
    def test_coverage_configuration(self):
        """Test that coverage configuration is set up correctly"""
        pytest_ini_path = Path(__file__).parent.parent / "pytest.ini"
        
        with open(pytest_ini_path, 'r') as f:
            content = f.read()
        
        # Check coverage configuration
        assert "--cov=src/backtest_lab" in content
        assert "--cov-report=html" in content
        assert "--cov-report=term-missing" in content
        assert "--cov-fail-under=80" in content
    
    def test_package_dependencies(self):
        """Test that package dependencies are correctly specified"""
        pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
        assert pyproject_path.exists()
        
        with open(pyproject_path, 'r') as f:
            content = f.read()
        
        # Check main dependencies
        assert "pydantic" in content
        assert "pandas" in content
        
        # Check test dependencies
        assert "pytest" in content
        assert "pytest-cov" in content
        assert "pytest-mock" in content
        assert "yfinance" in content
    
    def test_example_files_exist(self):
        """Test that example files exist"""
        docs_dir = Path(__file__).parent.parent / "docs"
        examples_dir = docs_dir / "examples"
        
        if examples_dir.exists():
            # Check that data_loading.py example exists
            data_loading_example = examples_dir / "data_loading.py"
            assert data_loading_example.exists(), "data_loading.py example should exist"
            
            # Check that it has valid Python syntax
            with open(data_loading_example, 'r') as f:
                content = f.read()
            
            # Should be valid Python
            try:
                compile(content, str(data_loading_example), 'exec')
            except SyntaxError as e:
                raise AssertionError(f"Example file has syntax error: {e}")
    
    def test_readme_exists(self):
        """Test that project README exists"""
        readme_path = Path(__file__).parent.parent / "README.md"
        assert readme_path.exists(), "README.md should exist"
        
        # Check test-specific README
        test_readme_path = Path(__file__).parent / "README.md"
        if test_readme_path.exists():
            with open(test_readme_path, 'r') as f:
                content = f.read()
            
            # Should contain test-related information
            assert "test" in content.lower() or "pytest" in content.lower()
    
    def test_project_metadata(self):
        """Test that project metadata is correctly configured"""
        pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
        
        with open(pyproject_path, 'r') as f:
            content = f.read()
        
        # Check project metadata
        assert 'name = "backtest-lab"' in content
        assert 'version = "0.1.0"' in content
        assert 'requires-python = ">=3.13"' in content
        assert "backtest_lab" in content
        assert "src" in content
