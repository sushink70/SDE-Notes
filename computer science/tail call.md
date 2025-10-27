A **tail call** is a function call where the last operation in a function is a call to another function (or itself, in the case of recursion), and no further computation is performed after the call returns. This allows certain optimizations, like **tail call optimization (TCO)**, where the call stack is reused, preventing stack overflow in deeply recursive functions.

### How Tail Calls Work
In a tail call, the calling function delegates its final action to the called function, meaning the caller doesn't need to keep its stack frame active. This is key for optimization, as it allows the runtime to replace the caller's stack frame with the called function's stack frame.

#### Example of a Tail Call
Consider a recursive function for calculating the factorial of a number:

```javascript
// Non-tail recursive factorial
function factorial(n) {
  if (n === 0) return 1;
  return n * factorial(n - 1); // Multiplication happens after the recursive call
}
```

In this version, the function is **not** tail recursive because after the recursive call to `factorial(n - 1)`, the result is multiplied by `n`. The stack frame of each call must be retained to perform the multiplication.

Now, a **tail recursive** version:

```javascript
function factorial(n, acc = 1) {
  if (n === 0) return acc;
  return factorial(n - 1, n * acc); // Last operation is the recursive call
}
```

Here, the last operation is the recursive call to `factorial`. The multiplication `n * acc` is computed *before* the recursive call, and the result is passed as an accumulator (`acc`). This makes it a tail call.

### How Tail Call Optimization (TCO) Works
When a language or runtime supports TCO:
1. The compiler or interpreter recognizes that the last operation is a function call.
2. Instead of creating a new stack frame for the called function, it reuses the current stack frame.
3. The called function's execution replaces the caller's context, reducing memory usage.

This is particularly useful in recursive functions, as it prevents stack overflow for large inputs. For example, without TCO, the non-tail recursive `factorial(10000)` might crash due to excessive stack frames. With TCO, the tail recursive version reuses a single stack frame, making it as efficient as a loop.

### Example in Action
Here’s how the tail recursive `factorial` works step-by-step for `factorial(3, 1)`:
1. `n = 3, acc = 1`: Not base case, call `factorial(2, 3 * 1 = 3)`.
2. `n = 2, acc = 3`: Not base case, call `factorial(1, 2 * 3 = 6)`.
3. `n = 1, acc = 6`: Not base case, call `factorial(0, 1 * 6 = 6)`.
4. `n = 0, acc = 6`: Base case, return `acc = 6`.

With TCO, each recursive call reuses the stack frame, so the memory usage remains constant.

### Support for Tail Calls
- **JavaScript**: ECMAScript 6 (ES6) specifies tail call optimization, but not all JavaScript engines implement it (e.g., V8 in Node.js and Chrome does not, as of 2025). Safari and some other engines support it.
- **Other Languages**: Functional languages like Scheme, Haskell, and Erlang heavily rely on TCO. Some imperative languages like C and Python may support it in specific compilers or not at all (e.g., Python does not optimize tail calls).

### When to Use Tail Calls
- Use tail calls in recursive algorithms to optimize memory usage, especially for deep recursion (e.g., tree traversals, large computations).
- They’re most effective in languages with guaranteed TCO.
- In languages without TCO, you can rewrite recursive functions as loops to achieve similar efficiency.

### Limitations
- If the language or runtime doesn’t support TCO, tail recursive functions still consume stack space, negating the benefit.
- Debugging can be harder with TCO, as stack traces may not show the full call history.
- Not all recursive functions can be easily rewritten as tail recursive (e.g., tree recursions may require additional effort).

In summary, tail calls enable efficient recursion by ensuring the last operation is a function call, allowing stack frame reuse with TCO. They’re a powerful tool in functional programming but depend on language support for maximum benefit. If you’re working in JavaScript, you may need to use loops or other techniques in environments without TCO support.