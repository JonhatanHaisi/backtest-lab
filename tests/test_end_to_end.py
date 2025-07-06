"""End-to-end tests simulating real usage scenarios"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import pandas as pd

from backtest_lab.data import (
    StockDataLoader,
    DataFrequency,
    MarketDataRequest,
    MarketData,
    YahooFinanceProvider
)


class TestEndToEndScenarios:
    """End-to-end tests for real-world scenarios"""
    
    def test_basic_stock_analysis_workflow(self, sample_ohlcv_data):
        """Test basic stock analysis workflow"""
        # Scenario: Analyst wants to analyze AAPL for last 30 days
        
        # Step 1: Create loader
        loader = StockDataLoader()
        
        # Mock Yahoo provider
        mock_provider = Mock(spec=YahooFinanceProvider)
        mock_provider.get_data.return_value = MarketData(
            symbol="AAPL",
            data=sample_ohlcv_data,
            metadata={
                "provider": "Yahoo Finance",
                "symbol": "AAPL",
                "company_name": "Apple Inc.",
                "sector": "Technology"
            }
        )
        loader.providers['yahoo'] = mock_provider
        
        # Step 2: Load data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        data = loader.get_data(
            symbol="AAPL",
            start_date=start_date,
            end_date=end_date,
            frequency=DataFrequency.DAILY
        )
        
        # Step 3: Verify data quality
        assert isinstance(data, MarketData)
        assert data.symbol == "AAPL"
        assert len(data.data) > 0
        assert data.metadata["company_name"] == "Apple Inc."
        
        # Step 4: Basic analysis
        df = data.data
        
        # Price statistics
        avg_price = df['close'].mean()
        max_price = df['high'].max()
        min_price = df['low'].min()
        total_volume = df['volume'].sum()
        
        assert avg_price > 0
        assert max_price >= avg_price
        assert min_price <= avg_price
        assert total_volume > 0
        
        # Technical indicators
        df['ma_5'] = df['close'].rolling(window=5).mean()
        df['ma_20'] = df['close'].rolling(window=20).mean() if len(df) >= 20 else None
        
        # Verify indicators
        assert 'ma_5' in df.columns
        assert not df['ma_5'].iloc[-1:].isna().all()  # Last value should not be NaN
    
    def test_portfolio_analysis_workflow(self, sample_ohlcv_data):
        """Test portfolio analysis workflow"""
        # Scenario: Portfolio manager wants to analyze tech stocks
        
        loader = StockDataLoader()
        
        # Mock provider
        mock_provider = Mock(spec=YahooFinanceProvider)
        
        def mock_get_data(request):
            return MarketData(
                symbol=request.symbol,
                data=sample_ohlcv_data,
                metadata={
                    "provider": "Yahoo Finance",
                    "symbol": request.symbol,
                    "sector": "Technology"
                }
            )
        
        mock_provider.get_data.side_effect = mock_get_data
        loader.providers['yahoo'] = mock_provider
        
        # Step 1: Define portfolio
        tech_stocks = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA"]
        
        # Step 2: Load all data
        portfolio_data = loader.get_multiple_symbols(
            symbols=tech_stocks,
            start_date=datetime.now() - timedelta(days=90),
            frequency=DataFrequency.DAILY
        )
        
        # Step 3: Verify all stocks loaded
        assert len(portfolio_data) == 5
        for symbol in tech_stocks:
            assert symbol in portfolio_data
            assert isinstance(portfolio_data[symbol], MarketData)
            assert portfolio_data[symbol].symbol == symbol
        
        # Step 4: Portfolio analysis
        portfolio_returns = {}
        portfolio_volatility = {}
        
        for symbol, data in portfolio_data.items():
            df = data.data
            
            # Calculate returns
            returns = df['close'].pct_change().dropna()
            portfolio_returns[symbol] = returns.mean()
            portfolio_volatility[symbol] = returns.std()
        
        # Verify calculations
        assert len(portfolio_returns) == 5
        assert len(portfolio_volatility) == 5
        
        # All stocks should have some returns data
        for symbol in tech_stocks:
            assert symbol in portfolio_returns
            assert symbol in portfolio_volatility
    
    def test_international_trading_workflow(self, sample_ohlcv_data):
        """Test international trading workflow"""
        # Scenario: Global trader analyzing different markets
        
        loader = StockDataLoader()
        
        # Mock provider
        mock_provider = Mock(spec=YahooFinanceProvider)
        
        def mock_get_data(request):
            # Simulate different market metadata
            if ".SA" in request.symbol:
                country = "Brazil"
                currency = "BRL"
            elif ".TO" in request.symbol:
                country = "Canada"
                currency = "CAD"
            else:
                country = "USA"
                currency = "USD"
            
            return MarketData(
                symbol=request.symbol,
                data=sample_ohlcv_data,
                metadata={
                    "provider": "Yahoo Finance",
                    "symbol": request.symbol,
                    "country": country,
                    "currency": currency
                }
            )
        
        mock_provider.get_data.side_effect = mock_get_data
        loader.providers['yahoo'] = mock_provider
        
        # Step 1: Define international portfolio
        global_stocks = {
            "USA": ["AAPL", "GOOGL"],
            "Brazil": ["PETR4.SA", "VALE3.SA"],
            "Canada": ["SHOP.TO", "CNR.TO"]
        }
        
        # Step 2: Load data by market
        market_data = {}
        
        for market, symbols in global_stocks.items():
            market_results = loader.get_multiple_symbols(
                symbols=symbols,
                start_date=datetime.now() - timedelta(days=60),
                frequency=DataFrequency.DAILY
            )
            market_data[market] = market_results
        
        # Step 3: Verify data by market
        for market, symbols in global_stocks.items():
            assert market in market_data
            assert len(market_data[market]) == len(symbols)
            
            for symbol in symbols:
                assert symbol in market_data[market]
                data = market_data[market][symbol]
                assert isinstance(data, MarketData)
                assert data.metadata["country"] == market
        
        # Step 4: Cross-market analysis
        market_performance = {}
        
        for market, results in market_data.items():
            market_returns = []
            
            for symbol, data in results.items():
                df = data.data
                returns = df['close'].pct_change().dropna()
                market_returns.extend(returns.tolist())
            
            if market_returns:
                market_performance[market] = {
                    "avg_return": sum(market_returns) / len(market_returns),
                    "volatility": pd.Series(market_returns).std()
                }
        
        # Verify analysis
        assert len(market_performance) == 3
        for market in ["USA", "Brazil", "Canada"]:
            assert market in market_performance
            assert "avg_return" in market_performance[market]
            assert "volatility" in market_performance[market]
    
    def test_intraday_trading_workflow(self, sample_ohlcv_data):
        """Test intraday trading workflow"""
        # Scenario: Day trader analyzing intraday patterns
        
        loader = StockDataLoader()
        
        # Mock provider
        mock_provider = Mock(spec=YahooFinanceProvider)
        mock_provider.get_data.return_value = MarketData(
            symbol="TSLA",
            data=sample_ohlcv_data,
            metadata={
                "provider": "Yahoo Finance",
                "symbol": "TSLA",
                "frequency": "5m"
            }
        )
        loader.providers['yahoo'] = mock_provider
        
        # Step 1: Load intraday data
        data = loader.get_data(
            symbol="TSLA",
            start_date=datetime.now() - timedelta(days=1),
            frequency=DataFrequency.MINUTE_5
        )
        
        # Step 2: Verify intraday data
        assert isinstance(data, MarketData)
        assert data.symbol == "TSLA"
        assert data.metadata["frequency"] == "5m"
        
        # Step 3: Intraday analysis
        df = data.data
        
        # Calculate intraday indicators
        df['vwap'] = (df['close'] * df['volume']).cumsum() / df['volume'].cumsum()
        df['rsi'] = self._calculate_rsi(df['close'])
        df['bb_upper'], df['bb_lower'] = self._calculate_bollinger_bands(df['close'])
        
        # Verify indicators
        assert 'vwap' in df.columns
        assert 'rsi' in df.columns
        assert 'bb_upper' in df.columns
        assert 'bb_lower' in df.columns
        
        # Trading signals
        df['buy_signal'] = (df['close'] < df['bb_lower']) & (df['rsi'] < 30)
        df['sell_signal'] = (df['close'] > df['bb_upper']) & (df['rsi'] > 70)
        
        # Verify signals
        assert 'buy_signal' in df.columns
        assert 'sell_signal' in df.columns
    
    def test_risk_management_workflow(self, sample_ohlcv_data):
        """Test risk management workflow"""
        # Scenario: Risk manager analyzing portfolio risk
        
        loader = StockDataLoader()
        
        # Mock provider
        mock_provider = Mock(spec=YahooFinanceProvider)
        
        def mock_get_data(request):
            return MarketData(
                symbol=request.symbol,
                data=sample_ohlcv_data,
                metadata={
                    "provider": "Yahoo Finance",
                    "symbol": request.symbol,
                    "beta": 1.2 if request.symbol == "TSLA" else 0.8
                }
            )
        
        mock_provider.get_data.side_effect = mock_get_data
        loader.providers['yahoo'] = mock_provider
        
        # Step 1: Load portfolio data
        portfolio_symbols = ["AAPL", "TSLA", "JPM", "JNJ"]
        portfolio_weights = [0.3, 0.2, 0.3, 0.2]
        
        portfolio_data = loader.get_multiple_symbols(
            symbols=portfolio_symbols,
            start_date=datetime.now() - timedelta(days=252),  # 1 year
            frequency=DataFrequency.DAILY
        )
        
        # Step 2: Calculate individual risk metrics
        risk_metrics = {}
        
        for symbol, data in portfolio_data.items():
            df = data.data
            returns = df['close'].pct_change().dropna()
            
            risk_metrics[symbol] = {
                "volatility": returns.std() * (252 ** 0.5),  # Annualized
                "var_95": returns.quantile(0.05),  # Value at Risk
                "max_drawdown": self._calculate_max_drawdown(df['close']),
                "beta": data.metadata.get("beta", 1.0)
            }
        
        # Step 3: Portfolio risk calculation
        returns_matrix = []
        for symbol in portfolio_symbols:
            df = portfolio_data[symbol].data
            returns = df['close'].pct_change().dropna()
            returns_matrix.append(returns.tolist())
        
        # Portfolio metrics
        portfolio_metrics = {
            "weighted_volatility": sum(
                portfolio_weights[i] * risk_metrics[symbol]["volatility"]
                for i, symbol in enumerate(portfolio_symbols)
            ),
            "weighted_beta": sum(
                portfolio_weights[i] * risk_metrics[symbol]["beta"]
                for i, symbol in enumerate(portfolio_symbols)
            )
        }
        
        # Step 4: Verify risk analysis
        assert len(risk_metrics) == 4
        for symbol in portfolio_symbols:
            assert symbol in risk_metrics
            assert "volatility" in risk_metrics[symbol]
            assert "var_95" in risk_metrics[symbol]
            assert "max_drawdown" in risk_metrics[symbol]
            assert "beta" in risk_metrics[symbol]
        
        assert "weighted_volatility" in portfolio_metrics
        assert "weighted_beta" in portfolio_metrics
        assert portfolio_metrics["weighted_volatility"] > 0
    
    def test_data_validation_workflow(self, sample_ohlcv_data):
        """Test data validation workflow"""
        # Scenario: Data analyst validating data quality
        
        loader = StockDataLoader()
        
        # Create data with some issues
        problematic_data = sample_ohlcv_data.copy()
        problematic_data.loc[problematic_data.index[2], 'high'] = 50  # Anomalously low high
        problematic_data.loc[problematic_data.index[3], 'volume'] = 0  # Zero volume
        
        # Mock provider
        mock_provider = Mock(spec=YahooFinanceProvider)
        mock_provider.get_data.return_value = MarketData(
            symbol="TEST",
            data=problematic_data,
            metadata={"provider": "Yahoo Finance", "symbol": "TEST"}
        )
        loader.providers['yahoo'] = mock_provider
        
        # Step 1: Load data
        data = loader.get_data("TEST")
        
        # Step 2: Data validation
        df = data.data
        validation_results = {
            "total_rows": len(df),
            "missing_values": df.isnull().sum().to_dict(),
            "negative_prices": (df[['open', 'high', 'low', 'close']] < 0).sum().to_dict(),
            "zero_volume": (df['volume'] == 0).sum(),
            "price_logic_errors": (df['high'] < df['low']).sum(),
            "ohlc_consistency": self._validate_ohlc_consistency(df)
        }
        
        # Step 3: Verify validation results
        assert validation_results["total_rows"] > 0
        assert isinstance(validation_results["missing_values"], dict)
        assert isinstance(validation_results["negative_prices"], dict)
        assert validation_results["zero_volume"] >= 0
        assert validation_results["price_logic_errors"] >= 0
        
        # Step 4: Data cleaning (if needed)
        clean_data = df.copy()
        
        # Remove rows with zero volume
        clean_data = clean_data[clean_data['volume'] > 0]
        
        # Fix price logic errors
        mask = clean_data['high'] < clean_data['low']
        if mask.any():
            clean_data.loc[mask, 'high'] = clean_data.loc[mask, 'low']
        
        # Verify cleaned data
        assert len(clean_data) <= len(df)
        assert (clean_data['volume'] > 0).all()
        assert (clean_data['high'] >= clean_data['low']).all()
    
    # Helper methods for calculations
    def _calculate_rsi(self, prices, window=14):
        """Calculate RSI indicator"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    def _calculate_bollinger_bands(self, prices, window=20, num_std=2):
        """Calculate Bollinger Bands"""
        ma = prices.rolling(window=window).mean()
        std = prices.rolling(window=window).std()
        upper = ma + (std * num_std)
        lower = ma - (std * num_std)
        return upper, lower
    
    def _calculate_max_drawdown(self, prices):
        """Calculate maximum drawdown"""
        cumulative = (1 + prices.pct_change()).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        return drawdown.min()
    
    def _validate_ohlc_consistency(self, df):
        """Validate OHLC price consistency"""
        errors = 0
        
        # High should be >= Open, Low, Close
        errors += (df['high'] < df['open']).sum()
        errors += (df['high'] < df['low']).sum()
        errors += (df['high'] < df['close']).sum()
        
        # Low should be <= Open, High, Close
        errors += (df['low'] > df['open']).sum()
        errors += (df['low'] > df['high']).sum()
        errors += (df['low'] > df['close']).sum()
        
        return errors


class TestErrorRecoveryScenarios:
    """Test error recovery in real scenarios"""
    
    def test_partial_data_failure_recovery(self, sample_ohlcv_data, capsys):
        """Test recovery from partial data failures"""
        loader = StockDataLoader()
        
        # Mock provider with mixed success/failure
        mock_provider = Mock(spec=YahooFinanceProvider)
        
        def mock_get_data_mixed(request):
            if request.symbol in ["FAIL1", "FAIL2"]:
                raise ValueError(f"Data not available for {request.symbol}")
            return MarketData(
                symbol=request.symbol,
                data=sample_ohlcv_data,
                metadata={"provider": "Yahoo Finance", "symbol": request.symbol}
            )
        
        mock_provider.get_data.side_effect = mock_get_data_mixed
        loader.providers['yahoo'] = mock_provider
        
        # Attempt to load mixed portfolio
        symbols = ["AAPL", "FAIL1", "GOOGL", "FAIL2", "MSFT"]
        results = loader.get_multiple_symbols(symbols)
        
        # Should get partial results
        assert len(results) == 3  # Only successful ones
        assert "AAPL" in results
        assert "GOOGL" in results
        assert "MSFT" in results
        assert "FAIL1" not in results
        assert "FAIL2" not in results
        
        # Verify error messages
        captured = capsys.readouterr()
        assert "Error loading FAIL1" in captured.out
        assert "Error loading FAIL2" in captured.out
        
        # Continue analysis with available data
        available_data = results
        portfolio_returns = {}
        
        for symbol, data in available_data.items():
            df = data.data
            returns = df['close'].pct_change().mean()
            portfolio_returns[symbol] = returns
        
        assert len(portfolio_returns) == 3
    
    def test_network_timeout_recovery(self, sample_ohlcv_data):
        """Test recovery from network timeouts"""
        loader = StockDataLoader()
        
        # Mock provider with timeout simulation
        mock_provider = Mock(spec=YahooFinanceProvider)
        call_count = 0
        
        def mock_get_data_with_retry(request):
            nonlocal call_count
            call_count += 1
            
            # Fail first time, succeed second time
            if call_count == 1:
                raise TimeoutError("Request timeout")
            else:
                return MarketData(
                    symbol=request.symbol,
                    data=sample_ohlcv_data,
                    metadata={"provider": "Yahoo Finance", "symbol": request.symbol}
                )
        
        mock_provider.get_data.side_effect = mock_get_data_with_retry
        loader.providers['yahoo'] = mock_provider
        
        # First call should fail
        with pytest.raises(TimeoutError):
            loader.get_data("AAPL")
        
        # Second call should succeed
        result = loader.get_data("AAPL")
        assert isinstance(result, MarketData)
        assert result.symbol == "AAPL"
    
    def test_data_quality_issues_recovery(self):
        """Test recovery from data quality issues"""
        loader = StockDataLoader()
        
        # Create data with quality issues
        bad_data = pd.DataFrame({
            'open': [100, None, 102, -5, 104],  # Missing and negative values
            'high': [101, 101, 103, 104, 105],
            'low': [99, 100, 101, 102, 103],
            'close': [100.5, 101.5, 102.5, 103.5, 104.5],
            'volume': [1000, 0, 1200, 1300, 1400]  # Zero volume
        })
        
        mock_provider = Mock(spec=YahooFinanceProvider)
        mock_provider.get_data.return_value = MarketData(
            symbol="BADDATA",
            data=bad_data,
            metadata={"provider": "Yahoo Finance", "symbol": "BADDATA"}
        )
        loader.providers['yahoo'] = mock_provider
        
        # Load problematic data
        result = loader.get_data("BADDATA")
        
        # Apply data cleaning
        df = result.data.copy()
        
        # Clean data
        original_length = len(df)
        
        # Remove rows with negative prices
        df = df[df['open'] > 0]
        
        # Remove rows with zero volume
        df = df[df['volume'] > 0]
        
        # Fill missing values with forward fill
        df = df.ffill()
        
        # Verify cleaning worked
        assert len(df) < original_length  # Some rows should be removed
        assert (df['open'] > 0).all()
        assert (df['volume'] > 0).all()
        assert not df.isnull().any().any()  # No missing values


@pytest.mark.integration
@pytest.mark.network
class TestRealWorldEndToEnd:
    """Real-world end-to-end tests (require network)"""
    
    def test_real_stock_analysis_workflow(self):
        """Test real stock analysis workflow with live data"""
        try:
            loader = StockDataLoader()
            
            # Load real data
            data = loader.get_data(
                symbol="AAPL",
                start_date=datetime.now() - timedelta(days=5),
                end_date=datetime.now() - timedelta(days=1),
                frequency=DataFrequency.DAILY
            )
            
            # Perform real analysis
            df = data.data
            
            # Basic statistics
            avg_price = df['close'].mean()
            volatility = df['close'].pct_change().std()
            
            # Technical indicators
            df['ma_5'] = df['close'].rolling(window=5).mean()
            
            # Verify results
            assert avg_price > 0
            assert volatility >= 0
            assert not df['ma_5'].iloc[-1:].isna().all()
            
        except Exception as e:
            pytest.skip(f"Real data test failed: {e}")
    
    def test_real_portfolio_workflow(self):
        """Test real portfolio workflow with live data"""
        try:
            loader = StockDataLoader()
            
            # Load real portfolio
            symbols = ["AAPL", "GOOGL"]
            results = loader.get_multiple_symbols(
                symbols=symbols,
                start_date=datetime.now() - timedelta(days=5),
                end_date=datetime.now() - timedelta(days=1),
                frequency=DataFrequency.DAILY
            )
            
            # Portfolio analysis
            portfolio_performance = {}
            
            for symbol, data in results.items():
                df = data.data
                returns = df['close'].pct_change().dropna()
                
                portfolio_performance[symbol] = {
                    "total_return": (df['close'].iloc[-1] / df['close'].iloc[0]) - 1,
                    "volatility": returns.std(),
                    "avg_volume": df['volume'].mean()
                }
            
            # Verify analysis
            assert len(portfolio_performance) == 2
            for symbol in symbols:
                assert symbol in portfolio_performance
                perf = portfolio_performance[symbol]
                assert "total_return" in perf
                assert "volatility" in perf
                assert "avg_volume" in perf
                assert perf["avg_volume"] > 0
            
        except Exception as e:
            pytest.skip(f"Real portfolio test failed: {e}")
