"""
Tests for the Step class in the stepwise analysis system.
"""

import pytest
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from backtest_lab.analysis.step import Step
from backtest_lab.analysis.exceptions import StepError, DataValidationError


class TestStep:
    """Test cases for the Step class."""

    def setup_method(self):
        """Setup test fixtures."""
        # Create valid OHLC data
        dates = pd.date_range(start='2023-01-01', periods=10, freq='D')
        self.valid_ohlc = pd.DataFrame({
            'open': [100, 102, 101, 103, 105, 104, 106, 105, 107, 108],
            'high': [105, 107, 106, 108, 110, 109, 111, 110, 112, 113],
            'low': [98, 100, 99, 101, 103, 102, 104, 103, 105, 106],
            'close': [102, 101, 103, 105, 104, 106, 105, 107, 108, 110]
        }, index=dates)

        # Create signals
        self.test_signals = {
            'sma': pd.Series([100, 101, 102, 103, 104, 105, 106, 107, 108, 109], index=dates),
            'rsi': pd.Series([50, 55, 45, 60, 40, 65, 35, 70, 30, 75], index=dates)
        }

        # Create metadata
        self.test_metadata = {
            'symbol': 'AAPL',
            'period': '1d',
            'strategy': 'test_strategy'
        }

    def test_step_initialization_basic(self):
        """Test basic step initialization."""
        step = Step(
            ohlc=self.valid_ohlc,
            step_index=0
        )
        
        assert step.step_index == 0
        assert len(step.ohlc) == 10
        assert list(step.ohlc.columns) == ['open', 'high', 'low', 'close']
        assert step.signals == {}
        assert step.metadata == {}
        assert step.previous_step is None
        assert isinstance(step.created_at, datetime)

    def test_step_initialization_with_signals(self):
        """Test step initialization with signals."""
        step = Step(
            ohlc=self.valid_ohlc,
            step_index=1,
            signals=self.test_signals
        )
        
        assert step.step_index == 1
        assert len(step.signals) == 2
        assert 'sma' in step.signals
        assert 'rsi' in step.signals
        pd.testing.assert_series_equal(step.signals['sma'], self.test_signals['sma'])

    def test_step_initialization_with_metadata(self):
        """Test step initialization with metadata."""
        step = Step(
            ohlc=self.valid_ohlc,
            step_index=2,
            metadata=self.test_metadata
        )
        
        assert step.step_index == 2
        assert step.metadata['symbol'] == 'AAPL'
        assert step.metadata['period'] == '1d'
        assert step.metadata['strategy'] == 'test_strategy'

    def test_step_initialization_with_previous_step(self):
        """Test step initialization with previous step reference."""
        previous_step = Step(
            ohlc=self.valid_ohlc,
            step_index=0
        )
        
        current_step = Step(
            ohlc=self.valid_ohlc,
            step_index=1,
            previous_step=previous_step
        )
        
        assert current_step.previous_step is previous_step
        assert current_step.previous_step.step_index == 0

    def test_step_immutability(self):
        """Test that step data is immutable."""
        step = Step(
            ohlc=self.valid_ohlc,
            step_index=0,
            signals=self.test_signals,
            metadata=self.test_metadata
        )
        
        # Test that modifying returned data doesn't affect original
        ohlc_copy = step.ohlc
        ohlc_copy.loc[ohlc_copy.index[0], 'open'] = 999
        
        assert step.ohlc.loc[step.ohlc.index[0], 'open'] != 999
        
        # Test signals immutability
        signals_copy = step.signals
        signals_copy['sma'].iloc[0] = 999
        
        assert step.signals['sma'].iloc[0] != 999

    def test_ohlc_validation_empty_dataframe(self):
        """Test validation with empty OHLC DataFrame."""
        empty_ohlc = pd.DataFrame()
        
        with pytest.raises(StepError, match="Failed to create step.*OHLC data cannot be empty"):
            Step(ohlc=empty_ohlc, step_index=0)

    def test_ohlc_validation_missing_columns(self):
        """Test validation with missing required columns."""
        invalid_ohlc = pd.DataFrame({
            'open': [100, 102],
            'high': [105, 107],
            'low': [98, 100]
            # Missing 'close' column
        })
        
        with pytest.raises(StepError, match="Failed to create step.*Missing required OHLC columns"):
            Step(ohlc=invalid_ohlc, step_index=0)

    def test_ohlc_validation_invalid_relationships(self):
        """Test validation with invalid OHLC relationships."""
        # High lower than low
        invalid_ohlc = pd.DataFrame({
            'open': [100],
            'high': [95],  # High < Low
            'low': [98],
            'close': [102]
        })
        
        with pytest.raises(StepError, match="Failed to create step.*Invalid OHLC relationships"):
            Step(ohlc=invalid_ohlc, step_index=0)

    def test_current_date_property(self):
        """Test current_date property returns last date in OHLC."""
        step = Step(ohlc=self.valid_ohlc, step_index=0)
        
        expected_date = self.valid_ohlc.index[-1]
        assert step.current_date == expected_date

    def test_data_length_property(self):
        """Test data_length property returns correct length."""
        step = Step(ohlc=self.valid_ohlc, step_index=0)
        
        assert step.data_length == 10

    def test_get_signal_existing(self):
        """Test get_signal with existing signal."""
        step = Step(
            ohlc=self.valid_ohlc,
            step_index=0,
            signals=self.test_signals
        )
        
        sma_signal = step.get_signal('sma')
        assert sma_signal is not None
        pd.testing.assert_series_equal(sma_signal, self.test_signals['sma'])

    def test_get_signal_nonexistent(self):
        """Test get_signal with non-existent signal."""
        step = Step(
            ohlc=self.valid_ohlc,
            step_index=0,
            signals=self.test_signals
        )
        
        nonexistent_signal = step.get_signal('nonexistent')
        assert nonexistent_signal is None

    def test_get_signal_immutability(self):
        """Test that get_signal returns immutable copy."""
        step = Step(
            ohlc=self.valid_ohlc,
            step_index=0,
            signals=self.test_signals
        )
        
        signal_copy = step.get_signal('sma')
        signal_copy.iloc[0] = 999
        
        # Original should not be affected
        assert step.signals['sma'].iloc[0] != 999

    def test_step_serialization_with_dict_conversion(self):
        """Test step can be converted to dict-like format for serialization."""
        step = Step(
            ohlc=self.valid_ohlc,
            step_index=0,
            signals=self.test_signals,
            metadata=self.test_metadata
        )
        
        # Test accessing all properties works
        step_data = {
            'step_index': step.step_index,
            'ohlc_length': len(step.ohlc),
            'signals_count': len(step.signals),
            'metadata': step.metadata,
            'created_at': step.created_at,
            'current_date': step.current_date,
            'data_length': step.data_length
        }
        
        assert step_data['step_index'] == 0
        assert step_data['ohlc_length'] == 10
        assert step_data['signals_count'] == 2
        assert step_data['metadata']['symbol'] == 'AAPL'

    def test_step_with_dataframe_signals(self):
        """Test step with DataFrame signals."""
        # Create DataFrame signal
        df_signal = pd.DataFrame({
            'bollinger_upper': [110, 112, 114, 116, 118, 120, 122, 124, 126, 128],
            'bollinger_lower': [90, 92, 94, 96, 98, 100, 102, 104, 106, 108]
        }, index=self.valid_ohlc.index)
        
        signals_with_df = {
            'sma': self.test_signals['sma'],
            'bollinger': df_signal
        }
        
        step = Step(
            ohlc=self.valid_ohlc,
            step_index=0,
            signals=signals_with_df
        )
        
        bollinger_signal = step.get_signal('bollinger')
        assert isinstance(bollinger_signal, pd.DataFrame)
        assert 'bollinger_upper' in bollinger_signal.columns
        assert 'bollinger_lower' in bollinger_signal.columns

    def test_step_error_handling_on_init_failure(self):
        """Test that StepError is raised when initialization fails."""
        # Mock the validation to raise an exception
        with patch.object(Step, '_validate_ohlc') as mock_validate:
            mock_validate.side_effect = Exception("Test validation error")
            
            with pytest.raises(StepError, match="Failed to create step"):
                Step(ohlc=self.valid_ohlc, step_index=0)

    def test_step_with_complex_metadata(self):
        """Test step with complex metadata structures."""
        complex_metadata = {
            'symbol': 'AAPL',
            'nested': {
                'strategy': 'momentum',
                'params': {
                    'period': 14,
                    'threshold': 0.02
                }
            },
            'list_data': [1, 2, 3, 4, 5],
            'datetime': datetime.now()
        }
        
        step = Step(
            ohlc=self.valid_ohlc,
            step_index=0,
            metadata=complex_metadata
        )
        
        metadata = step.metadata
        assert metadata['symbol'] == 'AAPL'
        assert metadata['nested']['strategy'] == 'momentum'
        assert metadata['nested']['params']['period'] == 14
        assert metadata['list_data'] == [1, 2, 3, 4, 5]
        assert isinstance(metadata['datetime'], datetime)

    def test_step_chain_reference(self):
        """Test multiple steps can reference previous steps."""
        step1 = Step(ohlc=self.valid_ohlc, step_index=0)
        step2 = Step(ohlc=self.valid_ohlc, step_index=1, previous_step=step1)
        step3 = Step(ohlc=self.valid_ohlc, step_index=2, previous_step=step2)
        
        assert step3.previous_step is step2
        assert step3.previous_step.previous_step is step1
        assert step3.previous_step.previous_step.step_index == 0

    def test_step_with_edge_case_ohlc_values(self):
        """Test step with edge case OHLC values."""
        # Test with very small values
        small_ohlc = pd.DataFrame({
            'open': [0.001, 0.002],
            'high': [0.002, 0.003],
            'low': [0.0005, 0.0015],
            'close': [0.0015, 0.0025]
        })
        
        step = Step(ohlc=small_ohlc, step_index=0)
        assert step.data_length == 2

    def test_step_properties_immutability_deep_copy(self):
        """Test that properties return deep copies to ensure immutability."""
        nested_metadata = {
            'config': {
                'params': [1, 2, 3]
            }
        }
        
        step = Step(
            ohlc=self.valid_ohlc,
            step_index=0,
            metadata=nested_metadata
        )
        
        # Modify the returned metadata
        returned_metadata = step.metadata
        returned_metadata['config']['params'].append(4)
        
        # Original should not be affected
        assert len(step.metadata['config']['params']) == 3


class TestStepAdvancedFunctionality:
    """Test advanced functionality of the Step class"""
    
    @pytest.fixture
    def extended_ohlc(self):
        """Extended OHLC data for date range testing"""
        dates = pd.date_range('2024-01-01', periods=10, freq='D')
        return pd.DataFrame({
            'open': [100, 101, 102, 103, 104, 105, 106, 107, 108, 109],
            'high': [101, 102, 103, 104, 105, 106, 107, 108, 109, 110],
            'low': [99, 100, 101, 102, 103, 104, 105, 106, 107, 108],
            'close': [100.5, 101.5, 102.5, 103.5, 104.5, 105.5, 106.5, 107.5, 108.5, 109.5]
        }, index=dates)
    
    def test_get_metadata_value_existing_key(self, extended_ohlc):
        """Test getting existing metadata value"""
        metadata = {'source': 'yahoo', 'frequency': 'daily'}
        step = Step(
            ohlc=extended_ohlc,
            step_index=0,
            metadata=metadata
        )
        
        assert step.get_metadata_value('source') == 'yahoo'
        assert step.get_metadata_value('frequency') == 'daily'
    
    def test_get_metadata_value_missing_key(self, extended_ohlc):
        """Test getting missing metadata value with default"""
        step = Step(
            ohlc=extended_ohlc,
            step_index=0,
            metadata={'source': 'yahoo'}
        )
        
        assert step.get_metadata_value('missing_key') is None
        assert step.get_metadata_value('missing_key', 'default_value') == 'default_value'
    
    def test_get_price_slice_with_dates(self, extended_ohlc):
        """Test getting price slice with date range"""
        step = Step(
            ohlc=extended_ohlc,
            step_index=0
        )
        
        start_date = datetime(2024, 1, 3)
        end_date = datetime(2024, 1, 6)
        
        price_slice = step.get_price_slice(start_date=start_date, end_date=end_date)
        
        assert len(price_slice) == 4  # 3rd to 6th inclusive
        assert price_slice.index[0].date() == start_date.date()
        assert price_slice.index[-1].date() == end_date.date()
    
    def test_get_price_slice_start_date_only(self, extended_ohlc):
        """Test getting price slice with start date only"""
        step = Step(
            ohlc=extended_ohlc,
            step_index=0
        )
        
        start_date = datetime(2024, 1, 8)
        price_slice = step.get_price_slice(start_date=start_date)
        
        assert len(price_slice) == 3  # Last 3 days
        assert price_slice.index[0].date() == start_date.date()
    
    def test_get_price_slice_end_date_only(self, extended_ohlc):
        """Test getting price slice with end date only"""
        step = Step(
            ohlc=extended_ohlc,
            step_index=0
        )
        
        end_date = datetime(2024, 1, 4)
        price_slice = step.get_price_slice(end_date=end_date)
        
        assert len(price_slice) == 4  # First 4 days
        assert price_slice.index[-1].date() == end_date.date()
    
    def test_get_price_slice_no_dates(self, extended_ohlc):
        """Test getting price slice without date constraints"""
        step = Step(
            ohlc=extended_ohlc,
            step_index=0
        )
        
        price_slice = step.get_price_slice()
        
        assert len(price_slice) == len(extended_ohlc)
        pd.testing.assert_frame_equal(price_slice, extended_ohlc)
    
    def test_get_signal_slice_with_dates(self, extended_ohlc):
        """Test getting signal slice with date range"""
        signal_data = pd.Series(range(10), index=extended_ohlc.index, name='test_signal')
        signals = {'test_signal': signal_data}
        
        step = Step(
            ohlc=extended_ohlc,
            step_index=0,
            signals=signals
        )
        
        start_date = datetime(2024, 1, 3)
        end_date = datetime(2024, 1, 6)
        
        signal_slice = step.get_signal_slice('test_signal', start_date=start_date, end_date=end_date)
        
        assert len(signal_slice) == 4
        assert signal_slice.index[0].date() == start_date.date()
        assert signal_slice.index[-1].date() == end_date.date()
    
    def test_get_signal_slice_nonexistent_signal(self, extended_ohlc):
        """Test getting slice of nonexistent signal"""
        step = Step(
            ohlc=extended_ohlc,
            step_index=0
        )
        
        signal_slice = step.get_signal_slice('nonexistent')
        assert signal_slice is None
    
    def test_step_repr_and_str(self, extended_ohlc):
        """Test string representation of step"""
        step = Step(
            ohlc=extended_ohlc,
            step_index=5,
            metadata={'source': 'test'}
        )
        
        repr_str = repr(step)
        str_str = str(step)
        
        assert 'Step(index=5' in repr_str
        assert 'data_length=10' in repr_str
        assert 'Step 5:' in str_str
        assert '10 data points' in str_str
    
    def test_step_equality(self, extended_ohlc):
        """Test step equality comparison - steps are different objects even with same data"""
        signals = {'signal1': pd.Series([1, 2, 3], name='signal1')}
        metadata = {'source': 'test'}
        
        step1 = Step(
            ohlc=extended_ohlc,
            step_index=1,
            signals=signals,
            metadata=metadata
        )
        
        step2 = Step(
            ohlc=extended_ohlc,
            step_index=1,
            signals=signals,
            metadata=metadata
        )
        
        step3 = Step(
            ohlc=extended_ohlc,
            step_index=2,  # Different index
            signals=signals,
            metadata=metadata
        )
        
        # Steps are different objects even with same data (no equality implemented)
        assert step1 != step2
        assert step1 != step3
        assert step1 != "not a step"
    
    def test_step_hashing(self, extended_ohlc):
        """Test that steps can be hashed and used in sets/dicts"""
        step1 = Step(
            ohlc=extended_ohlc,
            step_index=1
        )
        
        step2 = Step(
            ohlc=extended_ohlc,
            step_index=1
        )
        
        # Should be able to use in set
        step_set = {step1, step2}
        assert len(step_set) >= 1  # May be 1 if hash/eq considers them equal
        
        # Should be able to use as dict key
        step_dict = {step1: 'value1', step2: 'value2'}
        assert isinstance(step_dict, dict)
    
    def test_step_length(self, extended_ohlc):
        """Test step length (__len__ method)"""
        step = Step(
            ohlc=extended_ohlc,
            step_index=0
        )
        
        assert len(step) == 10
        assert step.data_length == len(step)
    
    def test_compare_with_previous(self, extended_ohlc):
        """Test signal comparison between steps"""
        # Create first step
        signal1 = pd.Series(range(10), index=extended_ohlc.index, name='test_signal')
        step1 = Step(
            ohlc=extended_ohlc,
            step_index=0,
            signals={'test_signal': signal1}
        )
        
        # Create second step with modified signal
        signal2 = pd.Series(range(5, 15), index=extended_ohlc.index, name='test_signal')
        step2 = Step(
            ohlc=extended_ohlc,
            step_index=1,
            signals={'test_signal': signal2},
            previous_step=step1
        )
        
        # Test signal comparison
        diff = step2.compare_with_previous('test_signal')
        
        assert diff is not None
        assert 'changed_values' in diff
        assert 'total_changes' in diff
        assert diff['total_changes'] == 10  # All values changed
    
    def test_compare_with_previous_no_previous(self, extended_ohlc):
        """Test signal comparison when no previous step"""
        signal = pd.Series(range(10), index=extended_ohlc.index)
        step = Step(
            ohlc=extended_ohlc,
            step_index=0,
            signals={'test_signal': signal}
        )
        
        diff = step.compare_with_previous('test_signal')
        assert diff is None
    
    def test_summary_dict(self, extended_ohlc):
        """Test step summary as dictionary"""
        signals = {'signal1': pd.Series(range(10), index=extended_ohlc.index)}
        metadata = {'source': 'test', 'version': '1.0'}
        
        step = Step(
            ohlc=extended_ohlc,
            step_index=2,
            signals=signals,
            metadata=metadata
        )
        
        summary = step.summary()
        
        assert summary['step_index'] == 2
        assert summary['data_length'] == 10
        assert 'signal1' in summary['signals']
        assert 'source' in summary['metadata_keys']
        assert 'date_range' in summary
        assert summary['has_previous_step'] is False
    
    def test_step_immutability_enforcement(self, extended_ohlc):
        """Test that step enforces immutability"""
        original_signals = {'signal1': pd.Series(range(10), index=extended_ohlc.index)}
        original_metadata = {'source': 'test'}
        
        step = Step(
            ohlc=extended_ohlc,
            step_index=1,
            signals=original_signals,
            metadata=original_metadata
        )
        
        # Test that we get copies, not references
        retrieved_signals = step.signals
        retrieved_metadata = step.metadata
        retrieved_ohlc = step.ohlc
        
        # Modify retrieved data
        retrieved_signals['signal1'].iloc[0] = 999 if hasattr(retrieved_signals['signal1'], 'iloc') else None
        retrieved_metadata['source'] = 'modified'
        if hasattr(retrieved_ohlc, 'iloc'):
            retrieved_ohlc.iloc[0, 0] = 999
        
        # Original should be unchanged
        assert step.get_metadata_value('source') == 'test'
        original_signal = step.get_signal('signal1')
        if original_signal is not None and hasattr(original_signal, 'iloc'):
            assert original_signal.iloc[0] != 999
    
    def test_get_latest_values(self, extended_ohlc):
        """Test getting latest OHLC values"""
        step = Step(
            ohlc=extended_ohlc,
            step_index=0
        )
        
        # Get latest 3 values
        latest = step.get_latest_values(3)
        
        assert len(latest) == 3
        assert latest.index[-1] == extended_ohlc.index[-1]  # Last date should match
        pd.testing.assert_frame_equal(latest, extended_ohlc.tail(3))
    
    def test_get_latest_signal_values(self, extended_ohlc):
        """Test getting latest signal values"""
        signal = pd.Series(range(10), index=extended_ohlc.index, name='test_signal')
        step = Step(
            ohlc=extended_ohlc,
            step_index=0,
            signals={'test_signal': signal}
        )
        
        # Get latest 2 signal values
        latest_signal = step.get_latest_signal_values('test_signal', 2)
        
        assert len(latest_signal) == 2
        assert latest_signal.iloc[-1] == 9  # Last value should be 9
        
        # Test nonexistent signal
        assert step.get_latest_signal_values('nonexistent') is None


class TestStepErrorHandling:
    """Test error handling in Step class"""
    
    def test_step_creation_with_invalid_data_types(self):
        """Test step creation with invalid data types"""
        # Test with non-DataFrame ohlc
        with pytest.raises(StepError):
            Step(
                ohlc="not a dataframe",
                step_index=0
            )
        
        # Step accepts string step_index (gets converted internally)
        valid_ohlc = pd.DataFrame({
            'open': [100], 'high': [101], 'low': [99], 'close': [100.5]
        })
        
        # This should work - step_index gets converted
        step = Step(
            ohlc=valid_ohlc,
            step_index="0"  # String step_index
        )
        
        assert step.step_index == "0"
    
    def test_step_frozen_after_creation(self):
        """Test that step attributes cannot be modified after creation"""
        valid_ohlc = pd.DataFrame({
            'open': [100], 'high': [101], 'low': [99], 'close': [100.5]
        })
        
        step = Step(ohlc=valid_ohlc, step_index=0)
        
        # Should not be able to modify internal attributes
        with pytest.raises(StepError, match="immutable"):
            step._step_index = 5
        
        with pytest.raises(StepError, match="immutable"):
            step._ohlc = valid_ohlc
    
    def test_signal_immutability_through_methods(self):
        """Test that signals remain immutable when accessed through methods"""
        valid_ohlc = pd.DataFrame({
            'open': [100, 101], 'high': [101, 102], 'low': [99, 100], 'close': [100.5, 101.5]
        }, index=pd.date_range('2024-01-01', periods=2))
        
        original_signal = pd.Series([1, 2], index=valid_ohlc.index, name='test')
        
        step = Step(
            ohlc=valid_ohlc,
            step_index=0,
            signals={'test': original_signal}
        )
        
        # Get signal and modify it
        retrieved_signal = step.get_signal('test')
        retrieved_signal.iloc[0] = 999
        
        # Original should be unchanged
        assert step.get_signal('test').iloc[0] == 1
