"""
Unit tests for the retry decorator.
"""

import pytest
import time
from unittest.mock import patch, MagicMock
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ekko_prototype.pages.tools.retry import retry


class TestRetryDecorator:
    """Test suite for retry decorator."""
    
    def test_successful_function_no_retry(self):
        """Test that successful function doesn't retry."""
        call_count = 0
        
        @retry(num_retries=3, sleep_between=0.01)
        def successful_func():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = successful_func()
        assert result == "success"
        assert call_count == 1
    
    def test_function_fails_then_succeeds(self):
        """Test function that fails once then succeeds."""
        call_count = 0
        
        @retry(num_retries=3, sleep_between=0.01)
        def eventually_succeeds():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Temporary failure")
            return "success"
        
        result = eventually_succeeds()
        assert result == "success"
        assert call_count == 2
    
    def test_function_always_fails(self):
        """Test function that always fails exhausts retries."""
        call_count = 0
        
        @retry(num_retries=3, sleep_between=0.01)
        def always_fails():
            nonlocal call_count
            call_count += 1
            raise ValueError("Always fails")
        
        with pytest.raises(ValueError, match="Always fails"):
            always_fails()
        
        assert call_count == 3
    
    def test_retry_with_arguments(self):
        """Test retry decorator with function arguments."""
        call_count = 0
        
        @retry(num_retries=2, sleep_between=0.01)
        def func_with_args(x, y, z=None):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("First attempt fails")
            return x + y + (z or 0)
        
        result = func_with_args(1, 2, z=3)
        assert result == 6
        assert call_count == 2
    
    def test_retry_sleep_between_attempts(self):
        """Test that retry sleeps between attempts."""
        @retry(num_retries=2, sleep_between=0.1)
        def always_fails():
            raise ValueError("Fail")
        
        start_time = time.time()
        with pytest.raises(ValueError):
            always_fails()
        elapsed = time.time() - start_time
        
        # Should have slept at least once (0.1 seconds)
        assert elapsed >= 0.1
    
    def test_retry_preserves_function_metadata(self):
        """Test that retry decorator preserves function metadata."""
        @retry(num_retries=2, sleep_between=0.01)
        def documented_func():
            """This is a documented function."""
            return "result"
        
        assert documented_func.__name__ == "documented_func"
        assert documented_func.__doc__ == "This is a documented function."
    
    def test_different_exception_types(self):
        """Test retry with different exception types."""
        call_count = 0
        
        @retry(num_retries=3, sleep_between=0.01)
        def throws_different_exceptions():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ValueError("First error")
            elif call_count == 2:
                raise TypeError("Second error")
            return "success"
        
        result = throws_different_exceptions()
        assert result == "success"
        assert call_count == 3
    
    @patch('ekko_prototype.pages.tools.retry.print')
    def test_retry_prints_attempts(self, mock_print):
        """Test that retry prints retry attempts."""
        @retry(num_retries=2, sleep_between=0.01)
        def fails_once():
            if not hasattr(fails_once, 'called'):
                fails_once.called = True
                raise ValueError("First attempt")
            return "success"
        
        result = fails_once()
        assert result == "success"
        
        # Check that retry message was printed
        mock_print.assert_called_with("Retrying... Attempt 2/2")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])