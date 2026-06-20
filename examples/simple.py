"""
examples/simple.py — A simple python script with nested function calls.
Used for tracing and testing Morpheus.
"""


def add(x: int, y: int) -> int:
    return x + y


def multiply(x: int, y: int) -> int:
    result = 0
    for _ in range(y):
        result = add(result, x)
    return result


def calculate(a: int, b: int) -> int:
    sum_val = add(a, b)
    product_val = multiply(a, b)
    return sum_val + product_val


if __name__ == "__main__":
    calculate(3, 4)
