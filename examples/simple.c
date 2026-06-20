// examples/simple.c
// A simple C program for testing Morpheus Oracle mode.

#include <stdio.h>

int add(int x, int y) {
    return x + y;
}

int multiply(int x, int y) {
    int result = 0;
    for (int i = 0; i < y; i++) {
        result = add(result, x);
    }
    return result;
}

int calculate(int a, int b) {
    int sum_val = add(a, b);
    int product_val = multiply(a, b);
    return sum_val + product_val;
}

int main() {
    int result = calculate(3, 4);
    printf("Result: %d\n", result);
    return 0;
}
