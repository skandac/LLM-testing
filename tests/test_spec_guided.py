import pytest
from src.solutions import is_palindrome, fib

# ==============================================================================
# Problem 1: HumanEval/12 (is_palindrome)
# Specifications derived from: assertions.md
# ==============================================================================

def test_spec_palindrome_normalization():
    """
    Derived from Corrected Spec #3 & #5: 
    Verifies that the function correctly normalizes string inputs 
    (removing punctuation and ignoring case) before checking equality.
    """
    # Test case: Mixed case and punctuation
    # "Madam, I'm Adam" -> "madamiimadam" (Palindrome)
    assert is_palindrome("Madam, I'm Adam") is True
    
    # Test case: Spaces and casing
    # "Race car" -> "racecar" (Palindrome)
    assert is_palindrome("Race car") is True
    
    # Test case: Valid string that is NOT a palindrome
    assert is_palindrome("Hello World") is False

def test_spec_palindrome_input_validation():
    """
    Derived from Spec #2: 
    Verifies that non-string inputs return False immediately 
    rather than raising an error.
    """
    # Test integer input
    assert is_palindrome(12345) is False
    
    # Test None input
    assert is_palindrome(None) is False
    
    # Test List input
    assert is_palindrome(['a', 'b', 'a']) is False

def test_spec_palindrome_empty_string():
    """
    Derived from Spec #4:
    An empty string is technically a palindrome (reads same forwards/backwards).
    """
    assert is_palindrome("") is True

def test_spec_palindrome_return_type():
    """
    Derived from Spec #1:
    The return value must always be a boolean.
    """
    res = is_palindrome("test")
    assert isinstance(res, bool)


# ==============================================================================
# Problem 2: HumanEval/100 (fib)
# Specifications derived from: assertions.md
# ==============================================================================

def test_spec_fib_base_cases():
    """
    Derived from Spec #2:
    Base cases for 0 and 1 must return the input value.
    """
    assert fib(0) == 0
    assert fib(1) == 1

def test_spec_fib_growth_property():
    """
    Derived from Spec #5:
    For n > 1, the result must be positive (fib numbers grow).
    """
    assert fib(5) > 0
    assert fib(10) == 55

def test_spec_fib_negative_value_error():
    """
    Derived from Corrected Spec #3: 
    Verifies that negative integers raise a ValueError with specific message.
    """
    with pytest.raises(ValueError, match="Input cannot be negative"):
        fib(-1)
        
    with pytest.raises(ValueError, match="Input cannot be negative"):
        fib(-100)

def test_spec_fib_type_error():
    """
    Derived from Corrected Spec #4: 
    Verifies that non-integer inputs raise a ValueError with specific message.
    """
    # Test float
    with pytest.raises(ValueError, match="Input must be a non-negative integer"):
        fib(3.5)
        
    # Test string
    with pytest.raises(ValueError, match="Input must be a non-negative integer"):
        fib("10")
        
    # Test None
    with pytest.raises(ValueError, match="Input must be a non-negative integer"):
        fib(None)