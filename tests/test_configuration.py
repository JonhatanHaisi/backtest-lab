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
