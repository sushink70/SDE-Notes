# Chained Rust code

Chained Rust code is hard to trace because it's a different kind of execution than a loop. Paste the exact code you're stuck on and I'll trace that. In the meantime, here is the mental model and a tracing technique that work for any chain.

## Mental model: a pipeline pulled from the end

```rust
let nums = vec![1, 2, 3, 4, 5, 6];

let result: Vec<i32> = nums
    .iter()                      // 1
    .filter(|&&x| x % 2 == 0)    // 2
    .map(|&x| x * x)             // 3
    .collect();                  // 4
```

Each `.method()` wraps the previous stage in a new iterator. **Nothing runs until `collect()`** (iterators are *lazy*). Then `collect()` pulls values backward through the pipeline, **one element at a time**:

```text
 nums      .iter()      .filter()      .map()       .collect()
[1..6] --> yields &i32 --> keeps evens --> squares --> pushes into Vec

 collect: "give me next" ---------------------------------+
                                                          |
   <----- map: "give me next" <---- filter: "give me next" <---- iter: next element
```

The common misconception is that `filter` runs over the whole list first and then `map` runs over the result. It doesn't. Each element travels through the whole pipeline before the next one starts.

## Dry run

| Element | filter (`x % 2 == 0`) | map (`x * x`) | collect's Vec |
|---|---|---|---|
| 1 | false → dropped | (skipped) | `[]` |
| 2 | true | 4 | `[4]` |
| 3 | false → dropped | (skipped) | `[4]` |
| 4 | true | 16 | `[4, 16]` |
| 5 | false → dropped | (skipped) | `[4, 16]` |
| 6 | true | 36 | `[4, 16, 36]` |

## Technique 1: track the type after every dot

Most confusion is really about *what flows between the stages*:

```text
nums                  : Vec<i32>
.iter()               : yields &i32          (borrowed refs, not values)
.filter(|&&x| ...)    : yields &i32          (closure receives &&i32!)
.map(|&x| x * x)      : yields i32           (closure receives &i32, returns a new value)
.collect()            : Vec<i32>             (type comes from the annotation)
```

This explains the odd `|&&x|` pattern:

- `iter()` yields `&i32`.
- `filter` passes the closure a *reference to the item*, so it gets `&&i32`.
- `&&x` is a pattern that destructures both layers, so `x` is a plain `i32`.
- In `map`, the closure gets `&i32`, so one `&x` is enough.

If the `&` symbols confuse you, write `|x| **x % 2 == 0` instead. Same meaning, and the dereferences are visible.

## Technique 2: break the chain into named steps

```rust
let it1 = nums.iter();
let it2 = it1.filter(|&&x| x % 2 == 0);
let it3 = it2.map(|&x| x * x);
let result: Vec<i32> = it3.collect();   // only now does work happen
```

Nothing happens on the first three lines. They only build the pipeline.

## Technique 3: spy on the pipeline with `inspect`

```rust
let result: Vec<i32> = nums
    .iter()
    .inspect(|x| println!("iter   -> {x}"))
    .filter(|&&x| x % 2 == 0)
    .inspect(|x| println!("passed -> {x}"))
    .map(|&x| x * x)
    .collect();
```

The output interleaves per element (`iter -> 1`, `iter -> 2`, `passed -> 2`, `iter -> 3`, ...), which confirms the one-at-a-time model.

## Go comparison

Go has no lazy chaining, so the same logic is a loop:

```go
result := []int{}
for _, x := range nums {
    if x%2 != 0 { continue }   // filter
    result = append(result, x*x) // map + collect
}
```

A Rust chain is this loop, with each stage as a named piece. The compiler fuses them into essentially the same machine code.

## Quick check (predict, then reply)

For `vec![1, 2, 3, 4].iter().map(|&x| x * 10).filter(|&x| x > 15).collect::<Vec<i32>>()`:

1. What is the type flowing out of `map`?
2. What is the final Vec?

Then paste the chained code you're struggling with and tell me which part loses you: the types, the `&` patterns in closures, or the order of execution. I'll trace it using this method.

Almost, but with one important catch. There are two different "orders" here, and mixing them up causes the confusion.

**1. For a single element, yes: it flows top to bottom.** Each value goes through `iter` → `filter` → `map` → `collect`, in the order you wrote them.

**2. For the whole list, no: it is not "all elements through stage 1, then all through stage 2".** The bottom of the chain (`collect`) is what starts the work, and it asks for one element at a time.

```text
WRONG model (stage by stage):          RIGHT model (element by element):

 [1,2,3,4]                              1 -> filter -> (dropped)
    | filter all                        2 -> filter -> map -> collect
 [2,4]                                  3 -> filter -> (dropped)
    | map all                           4 -> filter -> map -> collect
 [4,16]
    | collect
```

Here is the same thing as a trace of what actually happens, for `[1, 2, 3, 4]` with `.filter(even).map(square)`:

| Order | What runs | Result |
|---|---|---|
| 1 | `collect` asks for next | pulls from `map` → pulls from `filter` → pulls from `iter` |
| 2 | `iter` gives 1 | `filter` rejects it, asks `iter` again |
| 3 | `iter` gives 2 | `filter` accepts, `map` makes 4, `collect` stores 4 |
| 4 | `collect` asks again | `iter` gives 3, `filter` rejects, `iter` gives 4 |
| 5 | `filter` accepts 4 | `map` makes 16, `collect` stores 16 |
| 6 | `collect` asks again | `iter` is empty, so the chain ends |

So the best way to say it:

- **Written order:** top to bottom.
- **Data flow:** top to bottom, *per element*.
- **What triggers it:** the bottom (`collect`) pulls, and nothing runs before that.

A handy shortcut is that a chain is a `for` loop whose body is the stages in order:

```rust
for x in nums {
    // filter stage
    if x % 2 != 0 { continue; }
    // map stage
    let y = x * x;
    // collect stage
    result.push(y);
}
```

Now a quick check. For this chain, in what order are the `println!`s printed?

```rust
let v: Vec<i32> = vec![1, 2, 3]
    .into_iter()
    .map(|x| { println!("map {x}"); x * 2 })
    .filter(|&x| { println!("filter {x}"); x > 2 })
    .collect();
```

Will it print `map 1, map 2, map 3` first and then all the `filter` lines? Or will they be interleaved? Write out the exact sequence, and I'll check it with you.

Here is the exact call order, as numbered calls, for this code:

```rust
let v: Vec<i32> = vec![1, 2, 3]
    .into_iter()
    .map(|x| { println!("map {x}"); x * 2 })
    .filter(|&x| { println!("filter {x}"); x > 2 })
    .collect();
```

## Step 0: building the chain (no closures run)

```text
into_iter()  -> creates IntoIter      (holds 1,2,3)
.map(f)      -> creates Map { inner: IntoIter, f }
.filter(g)   -> creates Filter { inner: Map, g }
.collect()   -> NOW work starts
```

The final object is nested like this:

```text
Filter { g,
   inner: Map { f,
      inner: IntoIter [1,2,3] } }
```

## The key idea: every stage has a `next()` that calls the `next()` below it

Simplified versions of what the standard library does:

```rust
// Map::next
fn next(&mut self) -> Option<B> {
    let x = self.inner.next()?;   // ask the stage below
    Some((self.f)(x))             // then apply my closure
}

// Filter::next
fn next(&mut self) -> Option<T> {
    loop {
        let x = self.inner.next()?;   // ask the stage below
        if (self.g)(&x) { return Some(x); }   // keep it
        // otherwise loop and ask again
    }
}
```

`collect()` is just: `loop { match filter.next() { Some(x) => vec.push(x), None => break } }`.

## Exact sequence of calls

Indentation shows "who called whom". A call returns to the line above it.

```text
 1. collect() calls Filter::next()                    [outer call A]
 2.     Filter::next() calls Map::next()
 3.         Map::next() calls IntoIter::next()   -> returns Some(1)
 4.         Map::next() calls f(1)               -> prints "map 1",   returns 2
 5.     Map::next() returns Some(2)
 6.     Filter::next() calls g(&2)               -> prints "filter 2", false
 7.     (rejected, so Filter loops and asks again)
 8.     Filter::next() calls Map::next()
 9.         Map::next() calls IntoIter::next()   -> returns Some(2)
10.         Map::next() calls f(2)               -> prints "map 2",   returns 4
11.     Map::next() returns Some(4)
12.     Filter::next() calls g(&4)               -> prints "filter 4", true
13. Filter::next() returns Some(4)
14. collect() pushes 4          Vec = [4]

15. collect() calls Filter::next()                    [outer call B]
16.     Filter::next() calls Map::next()
17.         Map::next() calls IntoIter::next()   -> returns Some(3)
18.         Map::next() calls f(3)               -> prints "map 3",   returns 6
19.     Map::next() returns Some(6)
20.     Filter::next() calls g(&6)               -> prints "filter 6", true
21. Filter::next() returns Some(6)
22. collect() pushes 6          Vec = [4, 6]

23. collect() calls Filter::next()                    [outer call C]
24.     Filter::next() calls Map::next()
25.         Map::next() calls IntoIter::next()   -> returns None
26.     Map::next() returns None   (f is NOT called)
27. Filter::next() returns None  (g is NOT called)
28. collect() sees None, stops
```

## What gets printed

```text
map 1
filter 2
map 2
filter 4
map 3
filter 6
```

Final result: `[4, 6]`.

## How to read this

```text
call direction (down):   collect -> Filter -> Map -> IntoIter
value direction (up):    IntoIter -> Map -> Filter -> collect
```

- **Calls go down** the chain, from the last method to the first.
- **Values come back up** in the written order (`map` first, then `filter`).
- A stage that rejects a value (`filter`) makes the call go down again **without returning to `collect`**. That is lines 7-8 above.

This is a simplified model of the standard library's internals (for example, the real `Filter::next` uses `find`), but the order of closure calls and printed output is exactly what real Rust does.

If you paste the specific chained code you're stuck on, I'll write out the numbered call sequence for that one.