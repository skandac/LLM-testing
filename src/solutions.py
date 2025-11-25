import re

def is_palindrome(s: str) -> bool:
    """
    Checks if a string is a palindrome.
    """
    if not isinstance(s, str):
        return False
    s = s.lower().replace(" ", "")
    s = re.sub(r'[^\w]', '', s)
    return s == s[::-1]

def fib(n: int) -> int:
    """
    Calculates the n-th Fibonacci number.
    """
    if not isinstance(n, int):
        raise ValueError("Input must be a non-negative integer")
    if n < 0:
        raise ValueError("Input cannot be negative")
        
    if n == 0:
        return 0
    if n == 1:
        return 1
    
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b