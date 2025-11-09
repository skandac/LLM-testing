import pytest
from temp_solution import fib

def test_fib_negative_input():
    with pytest.raises(ValueError, match="Input cannot be negative"):
        fib(-1)
    with pytest.raises(ValueError, match="Input cannot be negative"):
        fib(-10)

def test_fib_non_integer_input():
    with pytest.raises(ValueError, match="Input must be a non-negative integer"):
        fib(5.5)
    with pytest.raises(ValueError, match="Input must be a non-negative integer"):
        fib("hello")