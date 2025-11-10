
from temp_solution import *
import pytest
import re

def test_benchmark():
    assert is_palindrome('racecar') is True
    assert is_palindrome('hello') is False
    assert is_palindrome('') is True
    assert is_palindrome('a') is True
    assert is_palindrome('Aa') is True
