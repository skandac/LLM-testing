import pytest
from temp_solution import is_palindrome

def test_is_palindrome_non_string():
    assert is_palindrome(12321) is False
    assert is_palindrome(None) is False
    assert is_palindrome([1, 2, 3]) is False
    assert is_palindrome({"a": 1}) is False