# Fibonacci: Naive vs Memoized - Complete Visual Breakdown

## 🔬 DEEP DIVE: Function Call Mechanics in Memoization

Let me show you **exactly** what happens, call by call, with maximum detail.

---

## 🎯 **THE LINE IN QUESTION**

```python
memo[n] = fib_memo(n - 1, memo) + fib_memo(n - 2, memo)
          └────────┬────────┘     └────────┬────────┘
               Call 1              Call 2
```

### **Critical Understanding:**

```
┌──────────────────────────────────────────────────────────┐
│  EXECUTION ORDER (Left to Right Evaluation)              │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  Step 1: Evaluate fib_memo(n - 1, memo)                 │
│          → This COMPLETES fully before step 2           │
│          → Returns a value                               │
│                                                          │
│  Step 2: Evaluate fib_memo(n - 2, memo)                 │
│          → This runs AFTER step 1 finishes              │
│          → Returns a value                               │
│                                                          │
│  Step 3: Add the two returned values                     │
│          → result = value1 + value2                      │
│                                                          │
│  Step 4: Store in memo[n]                                │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

## 📊 **COMPLETE EXECUTION TRACE: fib_memo(5)**

### **Initial State**
```
Call: fib_memo(5, memo={})
Goal: Compute fib(5)
```

### **THE COMPLETE CALL TREE WITH TIMELINE**

```
                                CALL TREE
                                =========

                            fib_memo(5) ①
                                 |
                    ┌────────────┴────────────┐
                    ↓                         ↓
              fib_memo(4) ②           fib_memo(3) ⑨
                    |                         |
        ┌───────────┴──────────┐         ┌───┴───┐
        ↓                      ↓         ↓       ↓
   fib_memo(3) ③        fib_memo(2) ⑥  [CACHE] [CACHE]
        |                      |         HIT!    HIT!
   ┌────┴────┐            ┌────┴────┐
   ↓         ↓            ↓         ↓
fib_memo(2)④ fib_memo(1)⑤[CACHE]  [CACHE]
   |           BASE=1      HIT!     HIT!
┌──┴──┐
↓     ↓
fib_memo(1) fib_memo(0)
BASE=1      BASE=0

Numbers ①②③④⑤⑥⑦⑧⑩ = Order of execution
```

---

## 🔍 **STEP-BY-STEP EXECUTION (Ultra-Detailed)**

### **CALL ①: fib_memo(5)**

```
┌─────────────────────────────────────────────────────────┐
│ CALL STACK:  [fib_memo(5)]                              │
│ MEMO STATE:  {}                                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ def fib_memo(5, memo={}):                               │
│     if 5 <= 1:  ← FALSE                                 │
│     if 5 in memo:  ← FALSE                              │
│                                                         │
│     # Now execute this line:                            │
│     memo[5] = fib_memo(5-1, memo) + fib_memo(5-2, memo) │
│               └──────┬──────┘                           │
│                      │                                  │
│               Must evaluate FIRST!                      │
│               Pause here, make new call...              │
│                                                         │
└─────────────────────────────────────────────────────────┘
                         ↓
              SPAWNS CALL ② fib_memo(4)
```

---

### **CALL ②: fib_memo(4)**

```
┌─────────────────────────────────────────────────────────┐
│ CALL STACK:  [fib_memo(5), fib_memo(4)]                │
│ MEMO STATE:  {}                                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ def fib_memo(4, memo={}):                               │
│     if 4 <= 1:  ← FALSE                                 │
│     if 4 in memo:  ← FALSE                              │
│                                                         │
│     memo[4] = fib_memo(4-1, memo) + fib_memo(4-2, memo) │
│               └──────┬──────┘                           │
│                      │                                  │
│               Must evaluate FIRST!                      │
│               Pause here, make new call...              │
│                                                         │
└─────────────────────────────────────────────────────────┘
                         ↓
              SPAWNS CALL ③ fib_memo(3)
```

---

### **CALL ③: fib_memo(3)**

```
┌─────────────────────────────────────────────────────────┐
│ CALL STACK:  [fib_memo(5), fib_memo(4), fib_memo(3)]   │
│ MEMO STATE:  {}                                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ def fib_memo(3, memo={}):                               │
│     if 3 <= 1:  ← FALSE                                 │
│     if 3 in memo:  ← FALSE                              │
│                                                         │
│     memo[3] = fib_memo(3-1, memo) + fib_memo(3-2, memo) │
│               └──────┬──────┘                           │
│                      │                                  │
│               Must evaluate FIRST!                      │
│               Pause here, make new call...              │
│                                                         │
└─────────────────────────────────────────────────────────┘
                         ↓
              SPAWNS CALL ④ fib_memo(2)
```

---

### **CALL ④: fib_memo(2)**

```
┌──────────────────────────────────────────────────────────┐
│ CALL STACK:  [fib_memo(5), fib_memo(4), fib_memo(3),    │
│               fib_memo(2)]                               │
│ MEMO STATE:  {}                                          │
├──────────────────────────────────────────────────────────┤
│                                                          │
│ def fib_memo(2, memo={}):                                │
│     if 2 <= 1:  ← FALSE                                  │
│     if 2 in memo:  ← FALSE                               │
│                                                          │
│     memo[2] = fib_memo(2-1, memo) + fib_memo(2-2, memo)  │
│               └──────┬──────┘                            │
│                      │                                   │
│               Must evaluate FIRST!                       │
│               Pause here, make new call...               │
│                                                          │
└──────────────────────────────────────────────────────────┘
                         ↓
              SPAWNS CALL fib_memo(1) - BASE CASE!
```

---

### **CALL: fib_memo(1) - BASE CASE HIT! 🎯**

```
┌──────────────────────────────────────────────────────────┐
│ CALL STACK:  [fib_memo(5), fib_memo(4), fib_memo(3),    │
│               fib_memo(2), fib_memo(1)]                  │
│ MEMO STATE:  {}                                          │
├──────────────────────────────────────────────────────────┤
│                                                          │
│ def fib_memo(1, memo={}):                                │
│     if 1 <= 1:  ← TRUE! ✓                                │
│         return 1                                         │
│                                                          │
│  ╔════════════════════════════════╗                     │
│  ║  RETURN 1 TO CALLER (fib(2))  ║                     │
│  ╚════════════════════════════════╝                     │
│                                                          │
└──────────────────────────────────────────────────────────┘
                         ↓
              RETURN TO CALL ④ with value = 1
```

---

### **BACK TO CALL ④: fib_memo(2) - First Part Complete**

```
┌──────────────────────────────────────────────────────────┐
│ CALL STACK:  [fib_memo(5), fib_memo(4), fib_memo(3),    │
│               fib_memo(2)]                               │
│ MEMO STATE:  {}                                          │
├──────────────────────────────────────────────────────────┤
│                                                          │
│ def fib_memo(2, memo={}):                                │
│     ...                                                  │
│     memo[2] = fib_memo(1, memo) + fib_memo(0, memo)      │
│               └──────┬──────┘   └──────┬──────┘         │
│                      │                 │                 │
│                   DONE = 1          Need this now!      │
│                                     Make new call...     │
│                                                          │
└──────────────────────────────────────────────────────────┘
                         ↓
              SPAWNS CALL fib_memo(0) - BASE CASE!
```

---

### **CALL: fib_memo(0) - BASE CASE HIT! 🎯**

```
┌──────────────────────────────────────────────────────────┐
│ CALL STACK:  [fib_memo(5), fib_memo(4), fib_memo(3),    │
│               fib_memo(2), fib_memo(0)]                  │
│ MEMO STATE:  {}                                          │
├──────────────────────────────────────────────────────────┤
│                                                          │
│ def fib_memo(0, memo={}):                                │
│     if 0 <= 1:  ← TRUE! ✓                                │
│         return 0                                         │
│                                                          │
│  ╔════════════════════════════════╗                     │
│  ║  RETURN 0 TO CALLER (fib(2))  ║                     │
│  ╚════════════════════════════════╝                     │
│                                                          │
└──────────────────────────────────────────────────────────┘
                         ↓
              RETURN TO CALL ④ with value = 0
```

---

### **BACK TO CALL ④: fib_memo(2) - COMPLETE! ✓**

```
┌──────────────────────────────────────────────────────────┐
│ CALL STACK:  [fib_memo(5), fib_memo(4), fib_memo(3),    │
│               fib_memo(2)]                               │
│ MEMO STATE:  {}  → About to update!                      │
├──────────────────────────────────────────────────────────┤
│                                                          │
│ def fib_memo(2, memo={}):                                │
│     ...                                                  │
│     memo[2] = fib_memo(1, memo) + fib_memo(0, memo)      │
│               └──────┬──────┘   └──────┬──────┘         │
│                   DONE = 1          DONE = 0             │
│                                                          │
│     memo[2] = 1 + 0 = 1                                  │
│                                                          │
│     ╔═══════════════════════════════════════╗           │
│     ║  STORE: memo[2] = 1                   ║           │
│     ║  RETURN 1 TO CALLER (fib(3))          ║           │
│     ╚═══════════════════════════════════════╝           │
│                                                          │
│ MEMO STATE NOW:  {2: 1}  ✓                              │
└──────────────────────────────────────────────────────────┘
                         ↓
              RETURN TO CALL ③ with value = 1
```

---

### **BACK TO CALL ③: fib_memo(3) - First Part Complete**

```
┌──────────────────────────────────────────────────────────┐
│ CALL STACK:  [fib_memo(5), fib_memo(4), fib_memo(3)]    │
│ MEMO STATE:  {2: 1}                                      │
├──────────────────────────────────────────────────────────┤
│                                                          │
│ def fib_memo(3, memo={2: 1}):                            │
│     ...                                                  │
│     memo[3] = fib_memo(2, memo) + fib_memo(1, memo)      │
│               └──────┬──────┘   └──────┬──────┘         │
│                   DONE = 1          Need this now!      │
│                                     Make new call...     │
│                                                          │
└──────────────────────────────────────────────────────────┘
                         ↓
              SPAWNS CALL fib_memo(1) - BASE CASE!
```

---

### **CALL: fib_memo(1) - BASE CASE (Again)**

```
┌──────────────────────────────────────────────────────────┐
│ CALL STACK:  [fib_memo(5), fib_memo(4), fib_memo(3),    │
│               fib_memo(1)]                               │
│ MEMO STATE:  {2: 1}                                      │
├──────────────────────────────────────────────────────────┤
│                                                          │
│ def fib_memo(1, memo={2: 1}):                            │
│     if 1 <= 1:  ← TRUE! ✓                                │
│         return 1                                         │
│                                                          │
│  ╔════════════════════════════════╗                     │
│  ║  RETURN 1 TO CALLER (fib(3))  ║                     │
│  ╚════════════════════════════════╝                     │
│                                                          │
└──────────────────────────────────────────────────────────┘
                         ↓
              RETURN TO CALL ③ with value = 1
```

---

### **BACK TO CALL ③: fib_memo(3) - COMPLETE! ✓**

```
┌──────────────────────────────────────────────────────────┐
│ CALL STACK:  [fib_memo(5), fib_memo(4), fib_memo(3)]    │
│ MEMO STATE:  {2: 1}  → About to update!                  │
├──────────────────────────────────────────────────────────┤
│                                                          │
│ def fib_memo(3, memo={2: 1}):                            │
│     ...                                                  │
│     memo[3] = fib_memo(2, memo) + fib_memo(1, memo)      │
│               └──────┬──────┘   └──────┬──────┘         │
│                   DONE = 1          DONE = 1             │
│                                                          │
│     memo[3] = 1 + 1 = 2                                  │
│                                                          │
│     ╔═══════════════════════════════════════╗           │
│     ║  STORE: memo[3] = 2                   ║           │
│     ║  RETURN 2 TO CALLER (fib(4))          ║           │
│     ╚═══════════════════════════════════════╝           │
│                                                          │
│ MEMO STATE NOW:  {2: 1, 3: 2}  ✓                        │
└──────────────────────────────────────────────────────────┘
                         ↓
              RETURN TO CALL ② with value = 2
```

---

### **BACK TO CALL ②: fib_memo(4) - First Part Complete**

```
┌──────────────────────────────────────────────────────────┐
│ CALL STACK:  [fib_memo(5), fib_memo(4)]                 │
│ MEMO STATE:  {2: 1, 3: 2}                                │
├──────────────────────────────────────────────────────────┤
│                                                          │
│ def fib_memo(4, memo={2: 1, 3: 2}):                      │
│     ...                                                  │
│     memo[4] = fib_memo(3, memo) + fib_memo(2, memo)      │
│               └──────┬──────┘   └──────┬──────┘         │
│                   DONE = 2          Need this now!      │
│                                                          │
│                                     Check memo first...  │
│                                                          │
└──────────────────────────────────────────────────────────┘
                         ↓
              CALL fib_memo(2) - CHECK CACHE!
```

---

### **CALL ⑤: fib_memo(2) - CACHE HIT! 🎯✨**

```
┌──────────────────────────────────────────────────────────┐
│ CALL STACK:  [fib_memo(5), fib_memo(4), fib_memo(2)]    │
│ MEMO STATE:  {2: 1, 3: 2}                                │
├──────────────────────────────────────────────────────────┤
│                                                          │
│ def fib_memo(2, memo={2: 1, 3: 2}):                      │
│     if 2 <= 1:  ← FALSE                                  │
│     if 2 in memo:  ← TRUE! ✓✓✓                           │
│         return memo[2]  ← INSTANT RETURN!                │
│                                                          │
│  ╔════════════════════════════════════════════╗         │
│  ║  CACHE HIT! 🎉                             ║         │
│  ║  Already computed: memo[2] = 1             ║         │
│  ║  NO RECURSION NEEDED!                      ║         │
│  ║  RETURN 1 INSTANTLY TO fib(4)              ║         │
│  ╚════════════════════════════════════════════╝         │
│                                                          │
│  This is THE POWER of memoization! ⚡                    │
└──────────────────────────────────────────────────────────┘
                         ↓
              RETURN TO CALL ② with value = 1
```

---

### **BACK TO CALL ②: fib_memo(4) - COMPLETE! ✓**

```
┌──────────────────────────────────────────────────────────┐
│ CALL STACK:  [fib_memo(5), fib_memo(4)]                 │
│ MEMO STATE:  {2: 1, 3: 2}  → About to update!            │
├──────────────────────────────────────────────────────────┤
│                                                          │
│ def fib_memo(4, memo={2: 1, 3: 2}):                      │
│     ...                                                  │
│     memo[4] = fib_memo(3, memo) + fib_memo(2, memo)      │
│               └──────┬──────┘   └──────┬──────┘         │
│                   DONE = 2       DONE = 1 (cached!)     │
│                                                          │
│     memo[4] = 2 + 1 = 3                                  │
│                                                          │
│     ╔═══════════════════════════════════════╗           │
│     ║  STORE: memo[4] = 3                   ║           │
│     ║  RETURN 3 TO CALLER (fib(5))          ║           │
│     ╚═══════════════════════════════════════╝           │
│                                                          │
│ MEMO STATE NOW:  {2: 1, 3: 2, 4: 3}  ✓                  │
└──────────────────────────────────────────────────────────┘
                         ↓
              RETURN TO CALL ① with value = 3
```

---

### **BACK TO CALL ①: fib_memo(5) - First Part Complete**

```
┌──────────────────────────────────────────────────────────┐
│ CALL STACK:  [fib_memo(5)]                               │
│ MEMO STATE:  {2: 1, 3: 2, 4: 3}                          │
├──────────────────────────────────────────────────────────┤
│                                                          │
│ def fib_memo(5, memo={2: 1, 3: 2, 4: 3}):                │
│     ...                                                  │
│     memo[5] = fib_memo(4, memo) + fib_memo(3, memo)      │
│               └──────┬──────┘   └──────┬──────┘         │
│                   DONE = 3          Need this now!      │
│                                                          │
│                                     Check memo first...  │
│                                                          │
└──────────────────────────────────────────────────────────┘
                         ↓
              CALL fib_memo(3) - CHECK CACHE!
```

---

### **CALL ⑥: fib_memo(3) - CACHE HIT! 🎯✨**

```
┌──────────────────────────────────────────────────────────┐
│ CALL STACK:  [fib_memo(5), fib_memo(3)]                 │
│ MEMO STATE:  {2: 1, 3: 2, 4: 3}                          │
├──────────────────────────────────────────────────────────┤
│                                                          │
│ def fib_memo(3, memo={2: 1, 3: 2, 4: 3}):                │
│     if 3 <= 1:  ← FALSE                                  │
│     if 3 in memo:  ← TRUE! ✓✓✓                           │
│         return memo[3]  ← INSTANT RETURN!                │
│                                                          │
│  ╔════════════════════════════════════════════╗         │
│  ║  CACHE HIT AGAIN! 🎉🎉                      ║         │
│  ║  Already computed: memo[3] = 2             ║         │
│  ║  NO RECURSION NEEDED!                      ║         │
│  ║  RETURN 2 INSTANTLY TO fib(5)              ║         │
│  ╚════════════════════════════════════════════╝         │
│                                                          │
│  Saved an ENTIRE subtree of recursion! ⚡⚡             │
└──────────────────────────────────────────────────────────┘
                         ↓
              RETURN TO CALL ① with value = 2
```

---

### **BACK TO CALL ①: fib_memo(5) - COMPLETE! ✓✓✓**

```
┌──────────────────────────────────────────────────────────┐
│ CALL STACK:  [fib_memo(5)]                               │
│ MEMO STATE:  {2: 1, 3: 2, 4: 3}  → Final update!         │
├──────────────────────────────────────────────────────────┤
│                                                          │
│ def fib_memo(5, memo={2: 1, 3: 2, 4: 3}):                │
│     ...                                                  │
│     memo[5] = fib_memo(4, memo) + fib_memo(3, memo)      │
│               └──────┬──────┘   └──────┬──────┘         │
│                   DONE = 3       DONE = 2 (cached!)     │
│                                                          │
│     memo[5] = 3 + 2 = 5                                  │
│                                                          │
│     ╔═══════════════════════════════════════╗           │
│     ║  STORE: memo[5] = 5                   ║           │
│     ║  RETURN 5 TO ORIGINAL CALLER          ║           │
│     ╚═══════════════════════════════════════╝           │
│                                                          │
│ FINAL MEMO STATE:  {2: 1, 3: 2, 4: 3, 5: 5}  ✓          │
│                                                          │
│ ╔════════════════════════════════════════════════╗      │
│ ║          🎉 COMPUTATION COMPLETE! 🎉           ║      │
│ ║               fib(5) = 5                       ║      │
│ ╚════════════════════════════════════════════════╝      │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

## 📊 **EXECUTION SUMMARY TABLE**

```
┌──────┬──────────────┬─────────────┬────────────┬─────────────┐
│ Step │ Function     │ Action      │ Returns    │ Memo After  │
├──────┼──────────────┼─────────────┼────────────┼─────────────┤
│  ①   │ fib_memo(5)  │ Call fib(4) │ -          │ {}          │
│  ②   │ fib_memo(4)  │ Call fib(3) │ -          │ {}          │
│  ③   │ fib_memo(3)  │ Call fib(2) │ -          │ {}          │
│  ④   │ fib_memo(2)  │ Call fib(1) │ -          │ {}          │
│  ⑤   │ fib_memo(1)  │ BASE CASE   │ 1          │ {}          │
│  ⑥   │ fib_memo(0)  │ BASE CASE   │ 0          │ {}          │
│  ⑦   │ fib_memo(2)  │ 1+0, store  │ 1          │ {2:1}       │
│  ⑧   │ fib_memo(1)  │ BASE CASE   │ 1          │ {2:1}       │
│  ⑨   │ fib_memo(3)  │ 1+1, store  │ 2          │ {2:1,3:2}   │
│  ⑩   │ fib_memo(2)  │ CACHE HIT!  │ 1          │ {2:1,3:2}   │
│  ⑪   │ fib_memo(4)  │ 2+1, store  │ 3          │ {2:1,3:2,   │
│      │              │             │            │  4:3}       │
│  ⑫   │ fib_memo(3)  │ CACHE HIT!  │ 2          │ {2:1,3:2,   │
│      │              │             │            │  4:3}       │
│  ⑬   │ fib_memo(5)  │ 3+2, store  │ 5          │ {2:1,3:2,   │
│      │              │             │            │  4:3,5:5}   │
└──────┴──────────────┴─────────────┴────────────┴─────────────┘

Total actual recursive calls: 9
Cache hits: 2 (saved multiple recursive calls!)
```

---

## 🆚 **COMPARISON: NAIVE vs MEMOIZED**

### **Naive Recursion Call Tree for fib(5)**

```
                            fib(5)
                          /        \
                         /          \
                    fib(4)            fib(3)
                   /      \          /      \
                  /        \        /        \
             fib(3)      fib(2)  fib(2)    fib(1)
            /      \     /    \   /    \      
           /        \   /      \ /      \     
      fib(2)   fib(1) fib(1) fib(0) fib(1) fib(0)
     /      \           
    /        \          
fib(1)   fib(0)         

TOTAL CALLS: 15
- fib(0): 3 times  ← WASTE!
- fib(1): 5 times  ← WASTE!
- fib(2): 3 times  ← WASTE!
- fib(3): 2 times  ← WASTE!
- fib(4): 1 time
- fib(5): 1 time
```

### **Memoized Call Tree for fib(5)**

```
                            fib(5)
                          /        \
                         /          \
                    fib(4)            fib(3) ← CACHE HIT!
                   /      \              ✓
                  /        \             Returns 2 instantly
             fib(3)      fib(2) ← CACHE HIT!
            /      \        ✓
           /        \       Returns 1 instantly
      fib(2)   fib(1)
     /      \    
    /        \   
fib(1)   fib(0)

TOTAL CALLS: 9
CACHE HITS: 2
- fib(0): 1 time  ✓
- fib(1): 2 times (base case)  ✓
- fib(2): 1 actual + 1 cache hit  ✓
- fib(3): 1 actual + 1 cache hit  ✓
- fib(4): 1 time  ✓
- fib(5): 1 time  ✓

SAVINGS: 15 - 9 = 6 avoided calls!
```

---

## 🎬 **ANIMATION: Call Stack Growth**

```
TIME PROGRESSION (Left to Right):
================================

t=0: START
Stack: []
Memo: {}

t=1: Call fib(5)
Stack: [5]
Memo: {}

t=2: Call fib(4) from fib(5)
Stack: [5, 4]
Memo: {}

t=3: Call fib(3) from fib(4)
Stack: [5, 4, 3]
Memo: {}

t=4: Call fib(2) from fib(3)
Stack: [5, 4, 3, 2]
Memo: {}

t=5: Call fib(1) from fib(2)  ← DEEPEST POINT
Stack: [5, 4, 3, 2, 1]
Memo: {}

t=6: fib(1) returns 1
Stack: [5, 4, 3, 2]
Memo: {}

t=7: Call fib(0) from fib(2)
Stack: [5, 4, 3, 2, 0]
Memo: {}

t=8: fib(0) returns 0
Stack: [5, 4, 3, 2]
Memo: {}

t=9: fib(2) completes, returns 1
Stack: [5, 4, 3]
Memo: {2: 1}  ← FIRST CACHE ENTRY!

t=10: Call fib(1) from fib(3)
Stack: [5, 4, 3, 1]
Memo: {2: 1}

t=11: fib(1) returns 1
Stack: [5, 4, 3]
Memo: {2: 1}

t=12: fib(3) completes, returns 2
Stack: [5, 4]
Memo: {2: 1, 3: 2}  ← GROWING!

t=13: Call fib(2) from fib(4)
Stack: [5, 4, 2]
Memo: {2: 1, 3: 2}
      ↑
      CACHE HIT! Returns 1 immediately ⚡

t=14: fib(4) completes, returns 3
Stack: [5]
Memo: {2: 1, 3: 2, 4: 3}

t=15: Call fib(3) from fib(5)
Stack: [5, 3]
Memo: {2: 1, 3: 2, 4: 3}
         ↑
         CACHE HIT! Returns 2 immediately ⚡

t=16: fib(5) completes, returns 5
Stack: []
Memo: {2: 1, 3: 2, 4: 3, 5: 5}

DONE! ✓
```

---

## 🧩 **THE CRITICAL LINE EXPLAINED**

```python
memo[n] = fib_memo(n - 1, memo) + fib_memo(n - 2, memo)
```

### **Detailed Breakdown:**

```
┌─────────────────────────────────────────────────────────┐
│  OPERATOR PRECEDENCE & EVALUATION ORDER                 │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Python evaluates expressions LEFT TO RIGHT             │
│                                                         │
│  STEP 1: Evaluate "fib_memo(n - 1, memo)"              │
│          → This makes a COMPLETE recursive call         │
│          → It goes all the way down until it returns    │
│          → Result stored in temporary variable          │
│                                                         │
│  STEP 2: Evaluate "fib_memo(n - 2, memo)"              │
│          → This makes another COMPLETE recursive call   │
│          → But now memo has values from step 1!         │
│          → May hit cache!                               │
│          → Result stored in another temporary           │
│                                                         │
│  STEP 3: Add the two results                            │
│          → temp1 + temp2                                │
│                                                         │
│  STEP 4: Assign to memo[n]                              │
│          → Store for future use                         │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### **What Actually Happens in Memory:**

```
When executing: memo[5] = fib_memo(4, memo) + fib_memo(3, memo)

PHASE 1: Evaluate fib_memo(4, memo)
┌──────────────────────────────────┐
│ Call fib_memo(4)                 │
│   Call fib_memo(3)               │
│     Call fib_memo(2)             │
│       Call fib_memo(1) → 1       │
│       Call fib_memo(0) → 0       │
│     Returns 1, memo[2] = 1       │
│     Call fib_memo(1) → 1         │
│   Returns 2, memo[3] = 2         │
│   Call fib_memo(2) → CACHE! = 1  │ ← Saved work!
│ Returns 3, memo[4] = 3           │
└──────────────────────────────────┘
Result: temp_left = 3

Memo state: {2: 1, 3: 2, 4: 3}

PHASE 2: Evaluate fib_memo(3, memo)
┌──────────────────────────────────┐
│ Call fib_memo(3)                 │
│   Check memo: 3 in memo? YES!    │ ← Massive savings!
│   Return memo[3] = 2 immediately │ ← No recursion!
└──────────────────────────────────┘
Result: temp_right = 2

PHASE 3: Addition
temp_left + temp_right = 3 + 2 = 5

PHASE 4: Storage
memo[5] = 5

Final memo: {2: 1, 3: 2, 4: 3, 5: 5}
```

---

## 🎯 **KEY INSIGHTS**

```
┌──────────────────────────────────────────────────────────┐
│         CRITICAL UNDERSTANDING POINTS                     │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  1. SEQUENTIAL EVALUATION                                │
│     The + operator doesn't execute "in parallel"        │
│     Left side COMPLETES before right side starts        │
│                                                          │
│  2. SHARED MEMO                                          │
│     Both calls share the SAME memo dictionary           │
│     Left call populates memo                            │
│     Right call BENEFITS from left's work                │
│                                                          │
│  3. CACHE ACCUMULATION                                   │
│     Each completed call adds to memo                    │
│     Later calls find more and more cached values        │
│     The memo GROWS as recursion unwinds                 │
│                                                          │
│  4. ASYMMETRIC BENEFIT                                   │
│     fib(n-1) does more work (fills cache)              │
│     fib(n-2) benefits (uses cache)                     │
│                                                          │
│  5. NO PARALLEL EXECUTION                                │
│     These are not two independent computations          │
│     They are sequential with shared state               │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

## 🔬 **PROOF: Add Print Statements**

```python
def fib_memo_debug(n, memo=None, indent=0):
    """Version with detailed printing"""
    prefix = "  " * indent
    print(f"{prefix}→ CALL fib({n})")
    
    if memo is None:
        memo = {}
    
    if n <= 1:
        print(f"{prefix}← BASE CASE: return {n}")
        return n
    
    if n in memo:
        print(f"{prefix}← CACHE HIT! return memo[{n}] = {memo[n]}")
        return memo[n]
    
    print(f"{prefix}  Computing fib({n-1})...")
    left = fib_memo_debug(n - 1, memo, indent + 1)
    print(f"{prefix}  fib({n-1}) returned {left}")
    
    print(f"{prefix}  Computing fib({n-2})...")
    right = fib_memo_debug(n - 2, memo, indent + 1)
    print(f"{prefix}  fib({n-2}) returned {right}")
    
    result = left + right
    memo[n] = result
    print(f"{prefix}  memo[{n}] = {result}")
    print(f"{prefix}← RETURN {result}")
    
    return result

# Run it!
fib_memo_debug(5)
```

### **Output:**

```
→ CALL fib(5)
  Computing fib(4)...
  → CALL fib(4)
    Computing fib(3)...
    → CALL fib(3)
      Computing fib(2)...
      → CALL fib(2)
        Computing fib(1)...
        → CALL fib(1)
        ← BASE CASE: return 1
        fib(1) returned 1
        Computing fib(0)...
        → CALL fib(0)
        ← BASE CASE: return 0
        fib(0) returned 0
        memo[2] = 1
      ← RETURN 1
      fib(2) returned 1
      Computing fib(1)...
      → CALL fib(1)
      ← BASE CASE: return 1
      fib(1) returned 1
      memo[3] = 2
    ← RETURN 2
    fib(3) returned 2
    Computing fib(2)...
    → CALL fib(2)
    ← CACHE HIT! return memo[2] = 1
    fib(2) returned 1
    memo[4] = 3
  ← RETURN 3
  fib(4) returned 3
  Computing fib(3)...
  → CALL fib(3)
  ← CACHE HIT! return memo[3] = 2
  fib(3) returned 2
  memo[5] = 5
← RETURN 5
```

**See how clear it is? Left evaluates FULLY, then right evaluates!**

---

## 🧠 **MENTAL MODEL: The "Recursive Descent and Memoized Ascent"**

```
          START: fib(5)
               |
               ↓
        Go DOWN recursively
    (Compute, building stack)
               |
               ↓
          Reach BASE
        (fib(1), fib(0))
               |
               ↓
        Come UP with values
      (Store in memo as you return)
               |
               ↓
        Finish with answer
      (memo filled, fib(5) computed)


DESCENT Phase: Expanding the problem
  - Breaking down n → n-1, n-2
  - Call stack grows
  - Memo empty initially

ASCENT Phase: Building the solution
  - Computing values
  - Storing in memo
  - Call stack shrinks
  - Memo fills up

Cache hits happen on ASCENT when we try to
go down again but find value already there!
```

---

**This is the COMPLETE picture of how memoization works!** Every function call, every memo update, every cache hit - you now understand it all at the deepest level. 🎯⚡

The key takeaway: **Sequential left-to-right evaluation with shared state (memo) that accumulates knowledge as recursion unwinds.**

Let me show you the **profound difference** between these two approaches. This is your first encounter with **Dynamic Programming** - one of the most powerful paradigm shifts in algorithm design.

---

## 🧠 **Key Concepts First** (Building Your Foundation)

### **Recursion Tree**
A visual representation of all function calls made during recursive execution. Each node = one function call.

### **Overlapping Subproblems**
When the same calculation is performed multiple times. This is **waste** in naive recursion.

### **Memoization** (from Latin "memorandum" - to be remembered)
A technique where we **cache** (store) results of expensive function calls and return the cached result when the same inputs occur again.

### **Call Stack**
The memory structure that tracks active function calls. Each recursive call adds a frame; returning removes it.

---

## 📊 **VISUALIZATION 1: Naive Recursive `fib(5)`**

```
                                    fib(5)
                                   /      \
                                  /        \
                           fib(4)            fib(3)
                          /      \          /      \
                         /        \        /        \
                    fib(3)      fib(2)  fib(2)    fib(1)
                   /      \     /    \   /    \      |
                  /        \   /      \ /      \     |
             fib(2)   fib(1) fib(1) fib(0) fib(1) fib(0)  [1]
            /      \    |      |      |      |      |
           /        \   |      |      |      |      |
       fib(1)   fib(0) [1]    [1]   [0]    [1]    [0]
          |        |
         [1]      [0]

CALL COUNT:
fib(5) = 1 call
fib(4) = 1 call
fib(3) = 2 calls  ← REDUNDANT!
fib(2) = 3 calls  ← REDUNDANT!
fib(1) = 5 calls  ← REDUNDANT!
fib(0) = 3 calls  ← REDUNDANT!

Total calls = 15 calls for just fib(5)!
```

### **The Problem:**
Notice `fib(3)` is calculated **2 times**, `fib(2)` is calculated **3 times**! 

**Every repeated calculation = wasted CPU cycles.**

---

## 📊 **VISUALIZATION 2: Memoized `fib_memo(5)`**

```
MEMO = {}  ← Our cache (initially empty)

                                    fib(5)
                                   /      \
                                  /        \
                           fib(4)            fib(3) ← CACHE HIT! ✓
                          /      \              
                         /        \             
                    fib(3)      fib(2) ← CACHE HIT! ✓
                   /      \         
                  /        \        
             fib(2)   fib(1) ← CACHE HIT! ✓
            /      \    
           /        \   
       fib(1)   fib(0)
          |        |
         [1]      [0]

EXECUTION TIMELINE:
Step 1: fib(5) → not in memo, compute
Step 2: fib(4) → not in memo, compute
Step 3: fib(3) → not in memo, compute
Step 4: fib(2) → not in memo, compute
Step 5: fib(1) → BASE CASE, return 1, store memo[1]=1
Step 6: fib(0) → BASE CASE, return 0, store memo[0]=0
Step 7: memo[2] = memo[1] + memo[0] = 1
Step 8: memo[3] = memo[2] + memo[1] = 2  ← fib(1) reused!
Step 9: fib(2) → FOUND IN MEMO! Return 1 instantly ✓
Step 10: memo[4] = memo[3] + memo[2] = 3  ← fib(2) reused!
Step 11: fib(3) → FOUND IN MEMO! Return 2 instantly ✓
Step 12: memo[5] = memo[4] + memo[3] = 5  ← fib(3) reused!

CALL COUNT:
fib(5) = 1 call
fib(4) = 1 call
fib(3) = 1 call (1 real + 1 cache hit)
fib(2) = 1 call (1 real + 2 cache hits)
fib(1) = 1 call (1 real + 4 cache hits)
fib(0) = 1 call

Total ACTUAL computations = 6 calls (vs 15 in naive!)
```

---

## 🔄 **SIDE-BY-SIDE EXECUTION FLOW**

```
┌─────────────────────────────────────┬─────────────────────────────────────┐
│     NAIVE fib(5)                    │     MEMOIZED fib_memo(5)           │
├─────────────────────────────────────┼─────────────────────────────────────┤
│ Call: fib(5)                        │ Call: fib_memo(5)                  │
│   Call: fib(4)                      │   Call: fib_memo(4)                │
│     Call: fib(3)                    │     Call: fib_memo(3)              │
│       Call: fib(2)                  │       Call: fib_memo(2)            │
│         Call: fib(1) → 1            │         Call: fib_memo(1) → 1      │
│         Call: fib(0) → 0            │         memo[1] = 1                │
│       Return: 1                     │         Call: fib_memo(0) → 0      │
│       Call: fib(1) → 1              │         memo[0] = 0                │
│     Return: 2                       │       memo[2] = 1                  │
│     Call: fib(2)  ← RECOMPUTE!      │       Call: fib_memo(1)            │
│       Call: fib(1) → 1              │       → Cache hit! Return 1 ✓      │
│       Call: fib(0) → 0              │     memo[3] = 2                    │
│     Return: 1                       │     Call: fib_memo(2)              │
│   Return: 3                         │     → Cache hit! Return 1 ✓        │
│   Call: fib(3) ← RECOMPUTE!         │   memo[4] = 3                      │
│     Call: fib(2) ← RECOMPUTE!       │   Call: fib_memo(3)                │
│       Call: fib(1) → 1              │   → Cache hit! Return 2 ✓          │
│       Call: fib(0) → 0              │ memo[5] = 5                        │
│     Return: 1                       │ Return: 5                          │
│     Call: fib(1) → 1                │                                    │
│   Return: 2                         │ MEMO STATE:                        │
│ Return: 5                           │ {0:0, 1:1, 2:1, 3:2, 4:3, 5:5}    │
│                                     │                                     │
│ Depth: O(n) stack frames            │ Depth: O(n) stack frames           │
│ Total calls: O(2^n) exponential!    │ Total calls: O(n) linear!          │
└─────────────────────────────────────┴─────────────────────────────────────┘
```

---

## 📈 **COMPLEXITY ANALYSIS FLOWCHART**

```
┌──────────────────────────────────────────────────────────────────┐
│                    COMPLEXITY DECISION TREE                       │
└──────────────────────────────────────────────────────────────────┘

                        fib(n) approach?
                              |
                ┌─────────────┴─────────────┐
                ↓                           ↓
            NAIVE                      MEMOIZED
                |                           |
    ┌───────────┴──────────┐    ┌──────────┴──────────┐
    ↓                      ↓    ↓                     ↓
TIME: O(2^n)         SPACE: O(n)   TIME: O(n)    SPACE: O(n)
exponential!         recursion     linear!       memo + recursion
    |                stack            |           stack
    ↓                      |           ↓                |
Growth rate:              |     Each problem         |
n=10 → 1,024 calls       |     solved ONCE          |
n=20 → 1,048,576 calls   |     Reuse results        |
n=30 → 1B+ calls         |     Cache lookups O(1)   |
n=40 → 1 TRILLION calls  ↓                          ↓
                    Stack depth = n           Stack depth = n
                    (max recursion)           memo size = n
```

---

## 🧩 **MENTAL MODEL: The "Computation vs Memory" Trade-off**

```
          COMPUTATION (CPU Time)
                 ↑
                 │     ╔═══════════════╗
    Naive        │     ║               ║
    (wasteful)   │     ║   NAIVE FIB   ║  ← Keeps recomputing
                 │     ║   O(2^n)      ║
                 │     ╚═══════════════╝
                 │
                 │
                 │            ╔════════════════╗
    Memoized     │            ║                ║
    (smart)      │            ║  MEMOIZED FIB  ║  ← Trades memory
                 │            ║  O(n)          ║     for speed
                 │            ╚════════════════╝
                 │
                 └─────────────────────────────────→
                              MEMORY (Space)
```

### **The Key Insight:**
**Memoization = Trading O(n) space to reduce O(2^n) time to O(n)**

This is **exponential → linear transformation**. For n=40:
- Naive: 1+ trillion operations ❌
- Memoized: 40 operations ✓

---

## 🎯 **EXECUTION TIMELINE (Call Stack Visualization)**

### **Naive Recursion Stack Growth:**

```
Time →
t1:  [fib(5)]
t2:  [fib(5), fib(4)]
t3:  [fib(5), fib(4), fib(3)]
t4:  [fib(5), fib(4), fib(3), fib(2)]
t5:  [fib(5), fib(4), fib(3), fib(2), fib(1)]  ← Base case
t6:  [fib(5), fib(4), fib(3), fib(2)]          ← Return 1
t7:  [fib(5), fib(4), fib(3), fib(2), fib(0)]  ← Base case
t8:  [fib(5), fib(4), fib(3), fib(2)]          ← Return 0
t9:  [fib(5), fib(4), fib(3)]                  ← Return 1
t10: [fib(5), fib(4), fib(3), fib(1)]          ← RECOMPUTE!
...  (continues with redundant calls)
```

### **Memoized Stack (with Cache State):**

```
Time →
t1:  [fib(5)]                              memo = {}
t2:  [fib(5), fib(4)]                      memo = {}
t3:  [fib(5), fib(4), fib(3)]              memo = {}
t4:  [fib(5), fib(4), fib(3), fib(2)]      memo = {}
t5:  [fib(5), fib(4), fib(3), fib(2), fib(1)] memo = {}
t6:  [fib(5), fib(4), fib(3), fib(2)]      memo = {1:1}
t7:  [fib(5), fib(4), fib(3), fib(2), fib(0)] memo = {1:1}
t8:  [fib(5), fib(4), fib(3), fib(2)]      memo = {0:0, 1:1}
t9:  [fib(5), fib(4), fib(3)]              memo = {0:0, 1:1, 2:1}
t10: [fib(5), fib(4), fib(3), fib(1)]      → CACHE HIT! No recursion
t11: [fib(5), fib(4)]                      memo = {0:0, 1:1, 2:1, 3:2}
t12: [fib(5), fib(4), fib(2)]              → CACHE HIT! No recursion
t13: [fib(5)]                              memo = {0:0, 1:1, 2:1, 3:2, 4:3}
t14: [fib(5), fib(3)]                      → CACHE HIT! No recursion
t15: []                                    memo = {0:0, 1:1, 2:1, 3:2, 4:3, 5:5}
                                           Result: 5 ✓
```

---

## 🔬 **DEEP INSIGHT: Why This Matters**

### **Pattern Recognition Skill You're Building:**

```
┌───────────────────────────────────────────────────────────────┐
│  RECOGNIZE THIS PATTERN IN FUTURE PROBLEMS:                   │
│                                                                │
│  1. OVERLAPPING SUBPROBLEMS                                   │
│     → Same calculation repeated multiple times                │
│                                                                │
│  2. OPTIMAL SUBSTRUCTURE                                      │
│     → Solution built from solutions to subproblems            │
│                                                                │
│  IF BOTH EXIST → Use Dynamic Programming (DP)                 │
│                                                                │
│  Memoization = TOP-DOWN DP (recursive with cache)             │
│  Tabulation = BOTTOM-UP DP (iterative, fills table)           │
└───────────────────────────────────────────────────────────────┘
```

---

## 💡 **COGNITIVE PRINCIPLE: Chunking**

Your brain is learning to **recognize DP patterns**:

1. **Naive thinking:** "Break problem down recursively" (correct but incomplete)
2. **Expert thinking:** "Break down recursively + identify reusable subproblems + cache results"

This is **chunking** - combining multiple concepts into one pattern you'll recognize instantly in future problems (Longest Common Subsequence, Coin Change, etc.).

---

## 🚀 **NEXT LEVEL: Rust/Go Implementation Challenge**

Want to see how this looks in your other languages? Try implementing:

**Rust:** Using `HashMap` for memo
**Go:** Using `map[int]int` for memo
**Python:** Using `@lru_cache` decorator (built-in memoization!)

**Question for you:** Can you convert the memoized version to **iterative** (bottom-up tabulation)? That's your next evolution! 🎯

---

**You've just witnessed the birth of Dynamic Programming in your mind.** This mental shift - from "compute everything" to "remember and reuse" - will unlock entire categories of problems. 

Keep this visualization in your mental library. You'll recognize this pattern **everywhere** now. 🧠⚡

In Python, the expression `fib_memo(n - 1, memo) + fib_memo(n - 2, memo)` follows **left-to-right evaluation order** for the operands of the `+` operator. This means:

- `fib_memo(n - 1, memo)` (the left operand) is **fully evaluated first**—it recurses down its entire branch, computes the result (potentially filling the memo along the way), and returns before the `+` can proceed.
- Only then does `fib_memo(n - 2, memo)` (the right operand) get evaluated—it often benefits from the memo populated by the left call, leading to cache hits and minimal/no further recursion.
- Finally, the two returned values are added, and the sum is assigned to `memo[n]`.

### Visual Trace for `fib_memo(5)` (Confirming Order)
Using prints to log execution (as simulated via code execution), here's the step-by-step flow. Note how the "left" call for each n fully resolves before the "right" one begins:

```
Enter fib_memo(5) → Miss → Print "Computing fib(5)"
├── Evaluate LEFT: fib_memo(4) → Miss → Print "Computing fib(4)"
│   ├── Evaluate LEFT: fib_memo(3) → Miss → Print "Computing fib(3)"
│   │   ├── Evaluate LEFT: fib_memo(2) → Miss → Print "Computing fib(2)"
│   │   │   ├── Evaluate LEFT: fib_memo(1) → Base: return 1 (no print)
│   │   │   └── Print "Left done for 2, now right"
│   │   │       └── Evaluate RIGHT: fib_memo(0) → Base: return 0
│   │   │   → memo[2] = 1 + 0 = 1; return 1
│   │   └── Print "Left done for 3, now right"
│   │       └── Evaluate RIGHT: fib_memo(1) → Base: return 1
│   │   → memo[3] = 1 + 1 = 2; return 2
│   └── Print "Left done for 4, now right"
│       └── Evaluate RIGHT: fib_memo(2) → Hit memo[2]=1; return 1 (no recurse!)
│   → memo[4] = 2 + 1 = 3; return 3
└── Print "Left done for 5, now right"
    └── Evaluate RIGHT: fib_memo(3) → Hit memo[3]=2; return 2 (no recurse!)
→ memo[5] = 3 + 2 = 5; return 5
```

**Key Observation**: Every `n-1` call (left) completes its full recursion before the corresponding `n-2` (right) starts. This top-down, left-first order ensures the memo is filled progressively (e.g., by the time we reach `fib_memo(5)`'s right branch, `memo[3]` is already stored from the left branch).

If Python evaluated right-to-left (like some languages), the tree would flip, and memoization would still work but fill differently (e.g., smaller values first). However, left-to-right is the rule here—consistent and predictable.

For a hands-on test, add prints to your code as shown above and run `fib_memo(5)`; the output will mirror this trace.