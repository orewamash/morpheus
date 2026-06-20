// examples/simple.js
// A simple JavaScript script for testing Morpheus Oracle mode.

function add(x, y) {
    return x + y;
}

function multiply(x, y) {
    let result = 0;
    for (let i = 0; i < y; i++) {
        result = add(result, x);
    }
    return result;
}

function calculate(a, b) {
    const sumVal = add(a, b);
    const productVal = multiply(a, b);
    return sumVal + productVal;
}

const result = calculate(3, 4);
console.log("Result: " + result);
