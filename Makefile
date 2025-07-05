# Makefile for backtest-lab project
.PHONY: help install test test-unit test-integration test-performance test-quick test-coverage test-all clean lint format docs

# Default target
help:
	@echo "Backtest Lab - Available commands:"
	@echo ""
	@echo "Setup:"
	@echo "  install         Install package and dependencies"
	@echo "  install-dev     Install with development dependencies"
	@echo ""
	@echo "Testing:"
	@echo "  test           Run quick tests (no network/slow tests)"
	@echo "  test-unit      Run unit tests only"
	@echo "  test-integration  Run integration tests"
	@echo "  test-performance  Run performance tests"
	@echo "  test-coverage  Run tests with coverage report"
	@echo "  test-all       Run all tests"
	@echo "  test-network   Run tests including network tests"
	@echo ""
	@echo "Code Quality:"
	@echo "  lint           Run linting checks"
	@echo "  format         Format code with black"
	@echo "  type-check     Run type checking with mypy"
	@echo ""
	@echo "Documentation:"
	@echo "  docs           Build documentation"
	@echo "  docs-serve     Serve documentation locally"
	@echo ""
	@echo "Utilities:"
	@echo "  clean          Clean up build artifacts"
	@echo "  example        Run example data loading script"

# Installation
install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"
	# Or using poetry: poetry install --with dev

# Testing targets
test:
	python run_tests.py --type quick

test-unit:
	python run_tests.py --type unit

test-integration:
	python run_tests.py --type integration

test-performance:
	python run_tests.py --type performance

test-coverage:
	python run_tests.py --type coverage

test-all:
	python run_tests.py --type all

test-network:
	pytest tests/ -m "network" -v

# Alternative pytest commands
pytest-unit:
	pytest tests/test_base.py tests/test_yahoo_provider.py tests/test_stock_loader.py tests/test_imports.py tests/test_edge_cases.py tests/test_configuration.py -m "not network and not slow" -v

pytest-integration:
	pytest tests/test_integration.py tests/test_end_to_end.py tests/test_examples.py -m "not network" -v

pytest-quick:
	pytest tests/ -m "not network and not slow" --tb=short

pytest-coverage:
	pytest tests/ --cov=src/backtest_lab --cov-report=html --cov-report=term-missing --cov-fail-under=80 -m "not network and not slow"

pytest-all:
	pytest tests/ -v

# New test categories
test-examples:
	pytest tests/test_examples.py -v

test-imports:
	pytest tests/test_imports.py -v

test-edge-cases:
	pytest tests/test_edge_cases.py -v

test-configuration:
	pytest tests/test_configuration.py -v

test-new:
	pytest tests/test_examples.py tests/test_imports.py tests/test_edge_cases.py tests/test_configuration.py -v

# Code quality
lint:
	@echo "Running flake8..."
	flake8 src/backtest_lab tests/ --max-line-length=120 --extend-ignore=E203,W503
	@echo "Running pylint..."
	pylint src/backtest_lab --disable=C0111,R0903,R0913

format:
	@echo "Formatting with black..."
	black src/backtest_lab tests/ docs/examples/ --line-length=120
	@echo "Sorting imports with isort..."
	isort src/backtest_lab tests/ docs/examples/ --profile black

type-check:
	@echo "Running mypy type checking..."
	mypy src/backtest_lab --ignore-missing-imports

# Documentation
docs:
	@echo "Building documentation..."
	mkdocs build

docs-serve:
	@echo "Serving documentation at http://localhost:8000"
	mkdocs serve

# Examples
example:
	@echo "Running data loading example..."
	python docs/examples/data_loading.py

example-verbose:
	@echo "Running data loading example with verbose output..."
	python -u docs/examples/data_loading.py

# Utilities
clean:
	@echo "Cleaning up build artifacts..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .mypy_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Development workflow
dev-setup: install-dev
	@echo "Development environment setup complete!"
	@echo "Run 'make test' to verify installation"

dev-test: format lint type-check test-coverage
	@echo "Development testing complete!"

# Release preparation
pre-release: clean format lint type-check test-all docs
	@echo "Pre-release checks complete!"

# CI/CD targets
ci-test:
	pytest tests/ -m "not network and not slow" --cov=src/backtest_lab --cov-report=xml --cov-fail-under=80

ci-full:
	python run_tests.py --type all --verbose

# Package building
build:
	python -m build

upload-test:
	python -m twine upload --repository testpypi dist/*

upload:
	python -m twine upload dist/*

# Database/cache management (if needed in future)
clean-cache:
	@echo "Cleaning cache directories..."
	rm -rf .cache/
	rm -rf cache/
	rm -rf data/cache/

# Performance profiling
profile-tests:
	pytest tests/test_performance.py --profile-svg

# Security checks
security-check:
	bandit -r src/backtest_lab/ -f json -o security-report.json
	safety check

# Dependency management
update-deps:
	pip-review --local --interactive

freeze-deps:
	pip freeze > requirements-frozen.txt

# Git hooks setup
setup-hooks:
	pre-commit install
	@echo "Git hooks installed!"

# Advanced testing scenarios
test-scenarios:
	@echo "Running specific test scenarios..."
	pytest tests/test_end_to_end.py::TestEndToEndScenarios::test_basic_stock_analysis_workflow -v
	pytest tests/test_end_to_end.py::TestEndToEndScenarios::test_portfolio_analysis_workflow -v
	pytest tests/test_end_to_end.py::TestEndToEndScenarios::test_international_trading_workflow -v

# Stress testing
stress-test:
	pytest tests/test_performance.py::TestScalability -v --tb=short

# Memory leak detection
memory-test:
	pytest tests/test_performance.py::TestPerformance::test_memory_usage_with_multiple_symbols -v

# Load testing with real data (requires network)
load-test:
	pytest tests/test_integration.py::TestRealDataIntegration -v -m "network"

# Generate test report
test-report:
	pytest tests/ --html=test-report.html --self-contained-html -m "not network and not slow"
	@echo "Test report generated: test-report.html"

# Continuous testing (watch for changes)
test-watch:
	ptw tests/ -- -m "not network and not slow" --tb=short

# Benchmark comparison
benchmark:
	pytest tests/test_performance.py::TestBenchmarks -v --benchmark-only

# Debug specific test
debug-test:
	pytest tests/test_base.py::TestMarketDataRequest::test_symbol_normalization -v -s --pdb

# Test with different Python versions (if available)
test-py38:
	python3.8 -m pytest tests/ -m "not network and not slow"

test-py39:
	python3.9 -m pytest tests/ -m "not network and not slow"

test-py310:
	python3.10 -m pytest tests/ -m "not network and not slow"

test-py311:
	python3.11 -m pytest tests/ -m "not network and not slow"

# Export test data for analysis
export-test-data:
	pytest tests/ --collect-only --quiet | grep "test_" > test-inventory.txt
	@echo "Test inventory exported to test-inventory.txt"

# Parallel testing with different configurations
test-parallel:
	pytest tests/ -n auto --dist worksteal -m "not network and not slow"

# Integration with GitHub Actions
github-test:
	pytest tests/ -m "not network and not slow" --cov=src/backtest_lab --cov-report=xml --junit-xml=test-results.xml

# Docker testing (if Docker is set up)
docker-test:
	docker build -t backtest-lab-test .
	docker run --rm backtest-lab-test make test

# Performance monitoring
perf-monitor:
	pytest tests/test_performance.py --profile --profile-svg -v

# Test data validation
validate-test-data:
	python -c "import tests.conftest as conf; print('Test fixtures loaded successfully')"

# Check test coverage by module
coverage-by-module:
	pytest tests/ --cov=src/backtest_lab --cov-report=term-missing --cov-report=html -m "not network and not slow"
	@echo "Detailed coverage by module available in htmlcov/"

# Mutation testing (if mutmut is installed)
mutation-test:
	mutmut run --paths-to-mutate src/backtest_lab/

# Property-based testing (if hypothesis is added)
property-test:
	pytest tests/ -k "hypothesis" -v

# Integration test with specific providers
test-yahoo:
	pytest tests/test_yahoo_provider.py -v -m "not network"

test-yahoo-live:
	pytest tests/test_yahoo_provider.py -v -m "network"

# Generate badges (if needed)
generate-badges:
	@echo "Generating coverage badge..."
	coverage-badge -o coverage.svg

# All-in-one development check
dev-check: clean format lint type-check test-coverage docs
	@echo "✅ All development checks passed!"
	@echo "📊 Coverage report: htmlcov/index.html"
	@echo "📚 Documentation: site/index.html"

# Quick health check
health-check:
	@echo "🔍 Running health check..."
	python -c "import backtest_lab; print(f'✅ Package imports successfully')"
	python -c "from backtest_lab.data import StockDataLoader; loader = StockDataLoader(); print(f'✅ StockDataLoader creates successfully')"
	python -c "from backtest_lab.data.base import MarketDataRequest; req = MarketDataRequest(symbol='TEST'); print(f'✅ MarketDataRequest creates successfully: {req.symbol}')"
	@echo "✅ Health check passed!"
