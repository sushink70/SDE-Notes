Here’s your C-dojo: 100+ **bug / typo / UB / logic traps** in C.

Same rules as with Rust/Go/C++:

* Each snippet is **intentionally wrong** (syntax, UB, subtle bug, or nasty trap).
* Your mission:

  1. Predict error / bug.
  2. Fix with **minimal changes** while keeping intent.
  3. Optionally run with `gcc -Wall -Wextra -pedantic` or `clang` and study errors/warnings.

No solutions here; you can always ask later about specific IDs (like `C-H17`) if you want a deep-dive.

---

## EASY (C-E01 – C-E25) — Syntax, basics, missing headers, obvious UB

```c
// C-E01: Missing stdio, printf undeclared
int main(void) {
    printf("Hello, C\n");
}
```

```c
// C-E02: Missing semicolon
#include <stdio.h>

int main(void) {
    int x = 10
    printf("%d\n", x);
}
```

```c
// C-E03: Wrong main signature
#include <stdio.h>

void main() {
    printf("Hi\n");
}
```

```c
// C-E04: Uninitialized variable
#include <stdio.h>

int main(void) {
    int x;
    printf("%d\n", x);
}
```

```c
// C-E05: Using == instead of = in assignment
#include <stdio.h>

int main(void) {
    int x;
    x == 10;
    printf("%d\n", x);
}
```

```c
// C-E06: Type mismatch in initialization
#include <stdio.h>

int main(void) {
    int x = "10";
    printf("%d\n", x);
}
```

```c
// C-E07: Array out of bounds
#include <stdio.h>

int main(void) {
    int a[3] = {1, 2, 3};
    printf("%d\n", a[3]);
}
```

```c
// C-E08: Using single = in if condition by mistake (logic bug)
#include <stdio.h>

int main(void) {
    int x = 0;
    if (x = 5) {
        printf("x is five\n");
    } else {
        printf("x is not five\n");
    }
}
```

```c
// C-E09: Missing return in non-void main
#include <stdio.h>

int main(void) {
    printf("Hello\n");
}
```

```c
// C-E10: Forgetting & for scanf
#include <stdio.h>

int main(void) {
    int x;
    scanf("%d", x);
    printf("%d\n", x);
}
```

```c
// C-E11: puts vs printf format string confusion
#include <stdio.h>

int main(void) {
    puts("Value: %d\n", 10);
    return 0;
}
```

```c
// C-E12: Dangling pointer
#include <stdio.h>

int* get_ptr(void) {
    int x = 10;
    return &x;
}

int main(void) {
    int *p = get_ptr();
    printf("%d\n", *p);
}
```

```c
// C-E13: Missing header for malloc
#include <stdio.h>

int main(void) {
    int *p = malloc(10 * sizeof(int));
    printf("%p\n", (void*)p);
    free(p);
}
```

```c
// C-E14: Wrong comment terminator
#include <stdio.h>

int main(void) {
    /* This is a comment *
    printf("Hello\n");
    return 0;
}
```

```c
// C-E15: for loop syntax error
#include <stdio.h>

int main(void) {
    for (int i = 0; i < 5; i++)
        printf("%d\n", i)
    return 0;
}
```

```c
// C-E16: char vs string confusion
#include <stdio.h>

int main(void) {
    char c = "A";
    printf("%c\n", c);
}
```

```c
// C-E17: String literal to non-const char*
#include <stdio.h>

int main(void) {
    char *s = "hello";
    s[0] = 'H';
    printf("%s\n", s);
}
```

```c
// C-E18: Missing case break (logic bug)
#include <stdio.h>

int main(void) {
    int x = 1;
    switch (x) {
        case 1:
            printf("one\n");
        case 2:
            printf("two\n");
        default:
            printf("other\n");
    }
}
```

```c
// C-E19: Incorrect format specifier
#include <stdio.h>

int main(void) {
    int x = 10;
    printf("%f\n", x);
}
```

```c
// C-E20: Using ++ on array name
#include <stdio.h>

int main(void) {
    int a[3] = {1, 2, 3};
    int *p = a;
    a++;
    printf("%d\n", *a);
}
```

```c
// C-E21: Misplaced braces
#include <stdio.h>

int main(void) 
    printf("Hello\n");
{
    return 0;
}
```

```c
// C-E22: Missing prototype / implicit int (C89 style)
#include <stdio.h>

int main(void) {
    foo();
    return 0;
}

foo() {
    printf("foo\n");
}
```

```c
// C-E23: Using sizeof on function
#include <stdio.h>

int foo(int x) {
    return x + 1;
}

int main(void) {
    printf("%zu\n", sizeof(foo));
}
```

```c
// C-E24: Assignment in declaration with comma confusion
#include <stdio.h>

int main(void) {
    int x = 1, y = 2,;
    printf("%d %d\n", x, y);
}
```

```c
// C-E25: Missing & in pointer initialization
#include <stdio.h>

int main(void) {
    int x = 10;
    int *p;
    p = x;
    printf("%d\n", *p);
}
```

---

## MEDIUM (C-M01 – C-M30) — Pointers, arrays, strings, dynamic memory, function pointers

```c
// C-M01: Off-by-one loop (logic + potential UB)
#include <stdio.h>

int main(void) {
    int a[5] = {1,2,3,4,5};
    for (int i = 0; i <= 5; i++) {
        printf("%d\n", a[i]);
    }
}
```

```c
// C-M02: malloc size of pointer vs object
#include <stdio.h>
#include <stdlib.h>

int main(void) {
    int *p = malloc(sizeof(p) * 10);
    if (!p) return 1;
    for (int i = 0; i < 10; i++) p[i] = i;
    printf("%d\n", p[9]);
    free(p);
}
```

```c
// C-M03: Realloc misuse (leak or crash)
#include <stdio.h>
#include <stdlib.h>

int main(void) {
    int *p = malloc(5 * sizeof(int));
    if (!p) return 1;
    int *q = realloc(p, 10 * sizeof(int));
    if (!q) {
        free(q);
        return 1;
    }
    p[0] = 42;
    printf("%d\n", q[0]);
    free(q);
}
```

```c
// C-M04: strcpy without enough space
#include <stdio.h>
#include <string.h>

int main(void) {
    char buf[5];
    strcpy(buf, "hello");
    printf("%s\n", buf);
}
```

```c
// C-M05: strcat with uninitialized buffer
#include <stdio.h>
#include <string.h>

int main(void) {
    char buf[20];
    strcat(buf, "hello");
    strcat(buf, "world");
    printf("%s\n", buf);
}
```

```c
// C-M06: pointer arithmetic with wrong type
#include <stdio.h>

int main(void) {
    int a[3] = {1,2,3};
    int *p = a;
    p = p + 1;
    char *c = (char*)p;
    c = c + 1;
    printf("%d\n", *(int*)c);
}
```

```c
// C-M07: Returning pointer to local array
#include <stdio.h>

int* get_array(void) {
    int a[3] = {1,2,3};
    return a;
}

int main(void) {
    int *p = get_array();
    printf("%d\n", p[0]);
}
```

```c
// C-M08: Function pointer mismatch
#include <stdio.h>

int add(int a, int b) {
    return a + b;
}

int main(void) {
    int (*fp)(int) = add;
    printf("%d\n", fp(2, 3));
}
```

```c
// C-M09: scanf buffer overflow
#include <stdio.h>

int main(void) {
    char name[8];
    scanf("%s", name);
    printf("%s\n", name);
}
```

```c
// C-M10: const correctness violation
#include <stdio.h>

void print_str(char *s) {
    printf("%s\n", s);
}

int main(void) {
    const char *msg = "hello";
    print_str(msg);
}
```

```c
// C-M11: Using strtok in nested calls (state corruption)
#include <stdio.h>
#include <string.h>

int main(void) {
    char s1[] = "a,b,c";
    char s2[] = "1,2,3";
    char *t1 = strtok(s1, ",");
    char *t2 = strtok(s2, ",");
    printf("%s %s\n", t1, t2);
}
```

```c
// C-M12: sizeof array vs pointer in function
#include <stdio.h>

void foo(int *a) {
    printf("%zu\n", sizeof(a));
}

int main(void) {
    int a[10];
    printf("%zu\n", sizeof(a));
    foo(a);
}
```

```c
// C-M13: Misusing memset on int array
#include <stdio.h>
#include <string.h>

int main(void) {
    int a[4];
    memset(a, 1, sizeof(a));
    for (int i = 0; i < 4; i++) {
        printf("%d\n", a[i]);
    }
}
```

```c
// C-M14: Returning char* from stack buffer
#include <stdio.h>
#include <string.h>

char* make_msg(void) {
    char buf[32];
    strcpy(buf, "hello");
    return buf;
}

int main(void) {
    char *s = make_msg();
    printf("%s\n", s);
}
```

```c
// C-M15: Integer division where float intended
#include <stdio.h>

int main(void) {
    int a = 1, b = 2;
    float x = a / b;
    printf("%f\n", x);
}
```

```c
// C-M16: switch fallthrough logic bug (intent: no fallthrough)
#include <stdio.h>

int main(void) {
    int x = 2;
    switch (x) {
        case 1:
            printf("one\n");
        case 2:
            printf("two\n");
        case 3:
            printf("three\n");
        default:
            printf("other\n");
    }
}
```

```c
// C-M17: infinite loop due to unsigned wrap
#include <stdio.h>

int main(void) {
    unsigned int i;
    for (i = 10; i >= 0; i--) {
        printf("%u\n", i);
    }
}
```

```c
// C-M18: Misuse of errno without <errno.h> or reset
#include <stdio.h>
#include <math.h>

int main(void) {
    double x = -1.0;
    double y = sqrt(x);
    if (errno != 0) {
        perror("sqrt");
    }
    printf("%f\n", y);
}
```

```c
// C-M19: Macro without parentheses
#include <stdio.h>

#define SQUARE(x) x * x

int main(void) {
    int a = 2;
    int b = SQUARE(a + 1);
    printf("%d\n", b);
}
```

```c
// C-M20: Misusing fgets/gets confusion
#include <stdio.h>

int main(void) {
    char buf[10];
    gets(buf);
    printf("%s\n", buf);
}
```

```c
// C-M21: Struct padding misunderstanding
#include <stdio.h>

struct S {
    char c;
    int x;
};

int main(void) {
    printf("%zu\n", sizeof(struct S));
}
```

```c
// C-M22: Incorrect use of enum as index (logic)
#include <stdio.h>

enum Color { RED = 5, GREEN, BLUE };

int main(void) {
    int a[3] = {1,2,3};
    printf("%d\n", a[RED]);
}
```

```c
// C-M23: Multiple definition of global
#include <stdio.h>

int x = 10;

int main(void) {
    extern int x;
    int x = 5;
    printf("%d\n", x);
}
```

```c
// C-M24: Variadic function wrong va_list usage
#include <stdio.h>
#include <stdarg.h>

int sum(int count, ...) {
    va_list args;
    int s = 0;
    for (int i = 0; i < count; i++) {
        s += va_arg(args, int);
    }
    va_end(args);
    return s;
}

int main(void) {
    printf("%d\n", sum(3, 1, 2, 3));
}
```

```c
// C-M25: memcpy overlapping regions
#include <stdio.h>
#include <string.h>

int main(void) {
    char buf[16] = "abcdefghijkl";
    memcpy(buf + 2, buf, 8);
    printf("%s\n", buf);
}
```

```c
// C-M26: strcmp vs strncmp bug
#include <stdio.h>
#include <string.h>

int main(void) {
    char a[3] = "ab";
    char b[3] = "abc";
    if (strcmp(a, b) == 0) {
        printf("equal\n");
    }
}
```

```c
// C-M27: wrong format for size_t
#include <stdio.h>

int main(void) {
    size_t n = 42;
    printf("%d\n", n);
}
```

```c
// C-M28: Freeing stack memory
#include <stdio.h>
#include <stdlib.h>

int main(void) {
    int x = 10;
    free(&x);
    return 0;
}
```

```c
// C-M29: double free
#include <stdio.h>
#include <stdlib.h>

int main(void) {
    int *p = malloc(sizeof(int));
    free(p);
    free(p);
    return 0;
}
```

```c
// C-M30: Undefined behavior via signed overflow
#include <stdio.h>
#include <limits.h>

int main(void) {
    int x = INT_MAX;
    x = x + 1;
    printf("%d\n", x);
}
```

---

## HARD (C-H01 – C-H25) — Deep pointer traps, aliasing, lifetime bugs, tricky macros, struct+function design

```c
// C-H01: Function pointer with wrong prototype
#include <stdio.h>

int add(int a, int b) { return a + b; }

int main(void) {
    int (*fp)(int) = add;
    printf("%d\n", fp(1, 2));
}
```

```c
// C-H02: Wrong use of realloc with alias
#include <stdio.h>
#include <stdlib.h>

int main(void) {
    int *p = malloc(4 * sizeof(int));
    int *q = p;
    q = realloc(q, 8 * sizeof(int));
    if (!q) {
        free(p);
        return 1;
    }
    p[0] = 42;
    printf("%d\n", q[0]);
    free(q);
}
```

```c
// C-H03: struct with embedded pointer, shallow copy bug
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

struct User {
    char *name;
};

int main(void) {
    struct User u1;
    u1.name = malloc(10);
    strcpy(u1.name, "Anas");

    struct User u2 = u1;
    free(u1.name);
    printf("%s\n", u2.name);
    free(u2.name);
}
```

```c
// C-H04: const pointer vs pointer to const confusion
#include <stdio.h>

int main(void) {
    int x = 1, y = 2;
    int * const p = &x;
    p = &y;
    *p = 5;
    printf("%d %d\n", x, y);
}
```

```c
// C-H05: reusing freed memory
#include <stdio.h>
#include <stdlib.h>

int main(void) {
    int *p = malloc(sizeof(int));
    *p = 42;
    free(p);
    printf("%d\n", *p);
}
```

```c
// C-H06: pointer alias + strict aliasing
#include <stdio.h>

int main(void) {
    float f = 1.0f;
    int *ip = (int*)&f;
    *ip = 0;
    printf("%f\n", f);
}
```

```c
// C-H07: macro side effects
#include <stdio.h>

#define INC(x) (++x)

int main(void) {
    int i = 0;
    int r = INC(i) + INC(i);
    printf("%d %d\n", i, r);
}
```

```c
// C-H08: flexible array member misuse
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

struct Buffer {
    size_t len;
    char data[];
};

int main(void) {
    struct Buffer *b = malloc(sizeof(struct Buffer));
    b->len = 5;
    strcpy(b->data, "hello");
    printf("%s\n", b->data);
    free(b);
}
```

```c
// C-H09: copying struct with FILE* (non-portable, logic)
#include <stdio.h>
#include <string.h>

struct S {
    FILE *fp;
};

int main(void) {
    struct S a, b;
    a.fp = fopen("test.txt", "w");
    b = a;
    fprintf(b.fp, "hello\n");
    fclose(a.fp);
    fclose(b.fp);
}
```

```c
// C-H10: recursion with missing base case (stack overflow)
#include <stdio.h>

void f(int n) {
    printf("%d\n", n);
    f(n+1);
}

int main(void) {
    f(0);
}
```

```c
// C-H11: signed/unsigned comparison bug
#include <stdio.h>

int main(void) {
    int n = -1;
    unsigned int m = 1;
    if (n < m) {
        printf("n < m\n");
    } else {
        printf("n >= m\n");
    }
}
```

```c
// C-H12: using local pointer after function ends (indirect)
#include <stdio.h>

void set_ptr(int **p) {
    int x = 10;
    *p = &x;
}

int main(void) {
    int *p = NULL;
    set_ptr(&p);
    printf("%d\n", *p);
}
```

```c
// C-H13: function returning struct by pointer vs value confusion
#include <stdio.h>

struct Pair {
    int x, y;
};

struct Pair* make_pair(int a, int b) {
    struct Pair p = {a, b};
    return &p;
}

int main(void) {
    struct Pair *q = make_pair(1, 2);
    printf("%d %d\n", q->x, q->y);
}
```

```c
// C-H14: calloc overflow (concept bug)
#include <stdio.h>
#include <stdlib.h>
#include <limits.h>

int main(void) {
    size_t n = SIZE_MAX / 2;
    int *p = calloc(n, 2);
    if (!p) {
        printf("alloc failed\n");
    } else {
        p[0] = 1;
        printf("%d\n", p[0]);
        free(p);
    }
}
```

```c
// C-H15: use-after-free via alias
#include <stdio.h>
#include <stdlib.h>

int main(void) {
    int *p = malloc(sizeof(int));
    int *q = p;
    *p = 10;
    free(p);
    *q = 20;
    printf("%d\n", *q);
}
```

```c
// C-H16: missing return in non-void function, UB use
#include <stdio.h>

int f(int x) {
    if (x > 0) return x + 1;
}

int main(void) {
    int y = f(0);
    printf("%d\n", y);
}
```

```c
// C-H17: `static` local variable and reentrancy
#include <stdio.h>

int counter(void) {
    static int c = 0;
    return ++c;
}

int main(void) {
    printf("%d\n", counter());
    printf("%d\n", counter());
}
```

```c
// C-H18: incorrect use of qsort comparator
#include <stdio.h>
#include <stdlib.h>

int cmp(const void *a, const void *b) {
    int x = *(const int*)a;
    int y = *(const int*)b;
    return x - y;
}

int main(void) {
    int a[] = {1000000000, -1000000000};
    qsort(a, 2, sizeof(int), cmp);
    printf("%d %d\n", a[0], a[1]);
}
```

```c
// C-H19: storing pointer to local array in global
#include <stdio.h>

int *gp;

void set(void) {
    int a[3] = {1,2,3};
    gp = a;
}

int main(void) {
    set();
    printf("%d\n", gp[0]);
}
```

```c
// C-H20: recursion with static buffer (thread-unsafe reentrancy)
#include <stdio.h>
#include <string.h>

char* f(int n) {
    static char buf[32];
    sprintf(buf, "%d", n);
    if (n == 0) return buf;
    return f(n-1);
}

int main(void) {
    printf("%s\n", f(5));
}
```

```c
// C-H21: wrong use of offsetof with non-standard type
#include <stdio.h>
#include <stddef.h>

struct S {
    int x;
    double y;
};

int main(void) {
    size_t off = offsetof(struct S, z);
    printf("%zu\n", off);
}
```

```c
// C-H22: pointer to struct member, then realloc
#include <stdio.h>
#include <stdlib.h>

struct S {
    int x;
    int y;
};

int main(void) {
    struct S *arr = malloc(2 * sizeof(struct S));
    arr[0].x = 1;
    int *px = &arr[0].x;
    arr = realloc(arr, 10 * sizeof(struct S));
    *px = 42;
    printf("%d\n", arr[0].x);
    free(arr);
}
```

```c
// C-H23: union type punning without care
#include <stdio.h>

union U {
    int i;
    float f;
};

int main(void) {
    union U u;
    u.f = 1.0f;
    printf("%d\n", u.i);
}
```

```c
// C-H24: Macro generating invalid code with comma operator
#include <stdio.h>

#define LOG(x, y) printf(#x "=%d " #y "=%d\n", x, y)

int main(void) {
    int a = 1, b = 2;
    if (a > 0)
        LOG(a++, b++);
    else
        printf("no\n");
    printf("%d %d\n", a, b);
}
```

```c
// C-H25: Using setjmp/longjmp with local objects
#include <stdio.h>
#include <setjmp.h>

jmp_buf buf;

void f(void) {
    int x = 10;
    longjmp(buf, 1);
    printf("%d\n", x);
}

int main(void) {
    if (setjmp(buf) == 0) {
        f();
    } else {
        printf("returned\n");
    }
}
```

---

## INSANE (C-I01 – C-I20) — Advanced UB, concurrency (POSIX), aliasing, lifetime puzzles

```c
// C-I01: Self-referential struct logically okay but risky pattern
#include <stdio.h>

struct Node {
    int value;
    struct Node *next;
};

int main(void) {
    struct Node n;
    n.value = 1;
    n.next = &n;
    printf("%d\n", n.next->next->next->value);
}
```

```c
// C-I02: pthreads data race (no synchronization)
#include <stdio.h>
#include <pthread.h>

int x = 0;

void* worker(void *arg) {
    for (int i = 0; i < 100000; i++) {
        x++;
    }
    return NULL;
}

int main(void) {
    pthread_t t1, t2;
    pthread_create(&t1, NULL, worker, NULL);
    pthread_create(&t2, NULL, worker, NULL);
    pthread_join(t1, NULL);
    pthread_join(t2, NULL);
    printf("%d\n", x);
}
```

```c
// C-I03: pthread mutex misuse (not initialized)
#include <stdio.h>
#include <pthread.h>

pthread_mutex_t m;

int main(void) {
    pthread_mutex_lock(&m);
    printf("locked\n");
    pthread_mutex_unlock(&m);
    return 0;
}
```

```c
// C-I04: deadlock with mutexes
#include <stdio.h>
#include <pthread.h>

pthread_mutex_t m1 = PTHREAD_MUTEX_INITIALIZER;
pthread_mutex_t m2 = PTHREAD_MUTEX_INITIALIZER;

void* t1(void *arg) {
    pthread_mutex_lock(&m1);
    pthread_mutex_lock(&m2);
    pthread_mutex_unlock(&m2);
    pthread_mutex_unlock(&m1);
    return NULL;
}

void* t2(void *arg) {
    pthread_mutex_lock(&m2);
    pthread_mutex_lock(&m1);
    pthread_mutex_unlock(&m1);
    pthread_mutex_unlock(&m2);
    return NULL;
}

int main(void) {
    pthread_t a, b;
    pthread_create(&a, NULL, t1, NULL);
    pthread_create(&b, NULL, t2, NULL);
    pthread_join(a, NULL);
    pthread_join(b, NULL);
}
```

```c
// C-I05: signal handler doing non-async-signal-safe things
#include <stdio.h>
#include <signal.h>

void handler(int sig) {
    printf("signal %d\n", sig);
}

int main(void) {
    signal(SIGINT, handler);
    for (;;);
}
```

```c
// C-I06: volatile misuse (thinking it fixes races)
#include <stdio.h>
#include <pthread.h>

volatile int done = 0;

void* worker(void *arg) {
    for (volatile int i = 0; i < 1000000; i++);
    done = 1;
    return NULL;
}

int main(void) {
    pthread_t t;
    pthread_create(&t, NULL, worker, NULL);
    while (!done);
    printf("done\n");
    pthread_join(t, NULL);
}
```

```c
// C-I07: longjmp across threads (undefined)
#include <stdio.h>
#include <setjmp.h>
#include <pthread.h>

jmp_buf buf;

void* worker(void *arg) {
    longjmp(buf, 1);
    return NULL;
}

int main(void) {
    pthread_t t;
    if (setjmp(buf) == 0) {
        pthread_create(&t, NULL, worker, NULL);
        pthread_join(t, NULL);
    } else {
        printf("jumped\n");
    }
}
```

```c
// C-I08: custom allocator wrong alignment
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>

void* my_alloc(size_t n) {
    void *p = malloc(n + 1);
    return (void*)((uintptr_t)p + 1);
}

int main(void) {
    double *d = my_alloc(sizeof(double));
    *d = 3.14;
    printf("%f\n", *d);
}
```

```c
// C-I09: pointer arithmetic beyond object
#include <stdio.h>

int main(void) {
    int a[3] = {1,2,3};
    int *p = &a[2];
    p++;
    printf("%d\n", *p);
}
```

```c
// C-I10: undefined behavior with memcpy of overlapping regions (big)
#include <stdio.h>
#include <string.h>

int main(void) {
    char s[32] = "abcdefghijklmnopqrstuvwxyz";
    memcpy(s + 5, s, 20);
    printf("%s\n", s);
}
```

```c
// C-I11: function pointer cast to incompatible type
#include <stdio.h>

int add(int a, int b) { return a + b; }

int main(void) {
    int (*fp)(double) = (int(*)(double))add;
    printf("%d\n", fp(3.14));
}
```

```c
// C-I12: strict-aliasing with unions depending on implementation
#include <stdio.h>

union U {
    int i;
    float f;
};

int main(void) {
    union U u;
    u.i = 0x3f800000;
    printf("%f\n", u.f);
}
```

```c
// C-I13: Dangling pointer via realloc shrink / pointer out of range
#include <stdio.h>
#include <stdlib.h>

int main(void) {
    int *p = malloc(10 * sizeof(int));
    for (int i = 0; i < 10; i++) p[i] = i;
    int *q = p + 9;
    p = realloc(p, 5 * sizeof(int));
    printf("%d\n", *q);
    free(p);
}
```

```c
// C-I14: Stack overflow via huge array on stack
#include <stdio.h>

int main(void) {
    int a[100000000];
    a[0] = 42;
    printf("%d\n", a[0]);
}
```

```c
// C-I15: UB: modifying string literal through cast
#include <stdio.h>

int main(void) {
    const char *s = "hello";
    char *p = (char*)s;
    p[0] = 'H';
    printf("%s\n", p);
}
```

```c
// C-I16: lifetime bug with returned pointer to VLA
#include <stdio.h>

int* make(int n) {
    int a[n];
    for (int i = 0; i < n; i++) a[i] = i;
    return a;
}

int main(void) {
    int *p = make(5);
    printf("%d\n", p[0]);
}
```

```c
// C-I17: recursion + static buffer + concurrency (conceptual)
#include <stdio.h>
#include <pthread.h>
#include <string.h>

char* strrev_recursive(char *s) {
    static char buf[256];
    size_t n = strlen(s);
    if (n == 0) {
        buf[0] = '\0';
        return buf;
    }
    buf[0] = s[n-1];
    buf[1] = '\0';
    strcat(buf, strrev_recursive(strndup(s, n-1)));
    return buf;
}

void* worker(void *arg) {
    printf("%s\n", strrev_recursive("hello"));
    return NULL;
}

int main(void) {
    pthread_t t1, t2;
    pthread_create(&t1, NULL, worker, NULL);
    pthread_create(&t2, NULL, worker, NULL);
    pthread_join(t1, NULL);
    pthread_join(t2, NULL);
}
```

```c
// C-I18: using uninitialized automatic struct with padding
#include <stdio.h>

struct S {
    int x;
    char c;
    int y;
};

int main(void) {
    struct S s;
    printf("%d %c %d\n", s.x, s.c, s.y);
}
```

```c
// C-I19: setjmp/longjmp skipping destructors in C++-style thinking (but here: resource leak logic)
#include <stdio.h>
#include <setjmp.h>

jmp_buf env;

void f(void) {
    FILE *fp = fopen("test.txt", "w");
    if (!fp) return;
    longjmp(env, 1);
    fprintf(fp, "hello\n");
    fclose(fp);
}

int main(void) {
    if (setjmp(env) == 0) {
        f();
    } else {
        printf("jumped\n");
    }
}
```

```c
// C-I20: aliasing via char* and writing past effective type region
#include <stdio.h>

int main(void) {
    int x = 0;
    char *p = (char*)&x;
    p[0] = 1;
    p[1] = 2;
    p[2] = 3;
    p[3] = 4;
    printf("%d\n", x);
}
```

---

## How to use this to level up in C

For each snippet:

1. **Prediction pass**
   Before compiling, say what’s wrong:

   * “This is UB because…”
   * “This is a strict-aliasing violation.”
   * “This will compile but has a data race / memory bug.”

2. **Compiler pass**
   Compile with **maximum warnings**:
   `gcc -Wall -Wextra -pedantic -std=c11 file.c`
   Read every warning/error slowly.

3. **Repair pass**
   Fix with **minimal edits** that preserve the author’s obvious intent.

4. **Abstraction pass**
   Write down the rule you violated:

   * “Never return pointer to stack.”
   * “Always use `&` with `scanf` for non-array scalars.”
   * “Realloc pattern: use temp pointer, only overwrite on success.”

Repeat that loop and your C brain will start auto-detecting UB, memory bugs, and type issues by *sight*, which is exactly what high-level DSA + systems interviews silently test.

# C Language Mastery: 100+ Bug Hunt & Typo Challenges

## **Leveling System**
- **Easy (1-30)**: Syntax errors, typos, basic logic bugs
- **Medium (31-60)**: Pointer arithmetic, type casting, operator precedence
- **Hard (61-85)**: Undefined behavior, memory aliasing, subtle UB traps
- **Insane (86-100+)**: Multi-layered bugs, race conditions, portability nightmares

**Rule**: Find ALL bugs. Explain the fix. Predict the behavior.

---

## **EASY LEVEL (1-30): Warmup**

### **E1: Missing Semicolon**
```c
#include <stdio.h>
int main(void) {
    int x = 5
    printf("%d\n", x);
    return 0;
}
```
**Bug**: Missing semicolon after `int x = 5`  
**Fix**: `int x = 5;`

---

### **E2: Typo in Function Name**
```c
#include <stdio.h>
int main(void) {
    prinft("Hello\n");
    return 0;
}
```
**Bug**: `prinft` → should be `printf`  
**Fix**: Correct spelling

---

### **E3: Array Index Out of Bounds**
```c
#include <stdio.h>
int main(void) {
    int arr[5] = {1, 2, 3, 4, 5};
    printf("%d\n", arr[5]);
    return 0;
}
```
**Bug**: Valid indices are 0-4, accessing `arr[5]` is undefined behavior  
**Fix**: Use `arr[4]` or adjust logic

---

### **E4: Uninitialized Variable**
```c
#include <stdio.h>
int main(void) {
    int x;
    printf("%d\n", x);
    return 0;
}
```
**Bug**: Reading uninitialized variable (undefined behavior)  
**Fix**: Initialize `int x = 0;`

---

### **E5: Missing Return Type**
```c
#include <stdio.h>
main(void) {
    printf("Test\n");
    return 0;
}
```
**Bug**: Implicit `int` return (pre-C99), but bad practice  
**Fix**: Explicitly `int main(void)`

---

### **E6: Wrong Format Specifier**
```c
#include <stdio.h>
int main(void) {
    double x = 3.14;
    printf("%d\n", x);
    return 0;
}
```
**Bug**: `%d` for `double` → undefined behavior  
**Fix**: Use `%f` or `%lf`

---

### **E7: String Not Null-Terminated**
```c
#include <stdio.h>
int main(void) {
    char str[5] = {'H', 'e', 'l', 'l', 'o'};
    printf("%s\n", str);
    return 0;
}
```
**Bug**: No null terminator, `printf` reads past array  
**Fix**: `char str[6]` or `char str[] = "Hello"`

---

### **E8: Mismatched Braces**
```c
#include <stdio.h>
int main(void) {
    if (1) {
        printf("Yes\n");
    return 0;
}
```
**Bug**: Missing closing brace for `if`  
**Fix**: Add `}` before `return 0;`

---

### **E9: Assignment in Condition**
```c
#include <stdio.h>
int main(void) {
    int x = 5;
    if (x = 0) {
        printf("Zero\n");
    }
    return 0;
}
```
**Bug**: Assignment `=` instead of comparison `==`  
**Fix**: `if (x == 0)`

---

### **E10: Infinite Loop**
```c
#include <stdio.h>
int main(void) {
    int i = 0;
    while (i < 10);
        i++;
    printf("%d\n", i);
    return 0;
}
```
**Bug**: Semicolon after `while` creates infinite loop  
**Fix**: Remove semicolon or add braces

---

### **E11: Pointer Without Dereference**
```c
#include <stdio.h>
int main(void) {
    int x = 10;
    int *p = &x;
    printf("%d\n", p);
    return 0;
}
```
**Bug**: Printing pointer address instead of value  
**Fix**: `printf("%d\n", *p);`

---

### **E12: Division by Zero**
```c
#include <stdio.h>
int main(void) {
    int x = 10;
    int y = 0;
    printf("%d\n", x / y);
    return 0;
}
```
**Bug**: Division by zero (undefined behavior)  
**Fix**: Check `if (y != 0)` before division

---

### **E13: Off-by-One in Loop**
```c
#include <stdio.h>
int main(void) {
    int arr[5] = {1, 2, 3, 4, 5};
    for (int i = 0; i <= 5; i++) {
        printf("%d ", arr[i]);
    }
    return 0;
}
```
**Bug**: Loop goes to `i = 5`, accessing `arr[5]` (out of bounds)  
**Fix**: `i < 5`

---

### **E14: Missing Header**
```c
int main(void) {
    printf("Hello\n");
    return 0;
}
```
**Bug**: Missing `#include <stdio.h>`  
**Fix**: Add header

---

### **E15: Wrong Increment Operator**
```c
#include <stdio.h>
int main(void) {
    int x = 5;
    x++++;
    printf("%d\n", x);
    return 0;
}
```
**Bug**: `x++++` invalid (can't increment rvalue)  
**Fix**: `x++; x++;` or `x += 2;`

---

### **E16: Mismatched Parentheses**
```c
#include <stdio.h>
int main(void) {
    int x = (5 + 3 * 2;
    printf("%d\n", x);
    return 0;
}
```
**Bug**: Missing closing parenthesis  
**Fix**: `(5 + 3 * 2)`

---

### **E17: Modifying String Literal**
```c
#include <stdio.h>
int main(void) {
    char *str = "Hello";
    str[0] = 'h';
    printf("%s\n", str);
    return 0;
}
```
**Bug**: Modifying string literal (undefined behavior)  
**Fix**: Use `char str[] = "Hello";`

---

### **E18: Wrong Operator Priority**
```c
#include <stdio.h>
int main(void) {
    int x = 5;
    if (x & 1 == 1) {
        printf("Odd\n");
    }
    return 0;
}
```
**Bug**: `==` has higher precedence than `&`  
**Fix**: `if ((x & 1) == 1)`

---

### **E19: Unclosed Comment**
```c
#include <stdio.h>
/* This is a comment
int main(void) {
    printf("Test\n");
    return 0;
}
```
**Bug**: Comment not closed  
**Fix**: Add `*/` before `int main`

---

### **E20: Double Semicolon**
```c
#include <stdio.h>
int main(void) {
    int x = 5;;
    printf("%d\n", x);
    return 0;
}
```
**Bug**: Extra semicolon (harmless but sloppy)  
**Fix**: Remove one semicolon

---

### **E21-E30: Quick Fire**

**E21**: `scanf("%d" &x);` → Missing comma: `scanf("%d", &x);`  
**E22**: `int arr[5]; arr = {1,2,3,4,5};` → Can't assign like this after declaration  
**E23**: `for (int i=0, i<10, i++)` → Use semicolons: `for (int i=0; i<10; i++)`  
**E24**: `int *p = NULL; *p = 5;` → Dereferencing NULL pointer  
**E25**: `char c = '65';` → `'65'` is multi-char constant (implementation-defined)  
**E26**: `int x = 5.5;` → Implicit truncation, use `int x = (int)5.5;` or `double`  
**E27**: `sizeof(x)` where `x` is array parameter → Decays to pointer, use length param  
**E28**: `switch (x) { case 1: ... }` missing `break;` → Fall-through  
**E29**: `unsigned int x = -1;` → Wraps to `UINT_MAX`, might be intentional but check  
**E30**: `gets(buffer);` → Unsafe, use `fgets()`

---

## **MEDIUM LEVEL (31-60): Pointer & Type Traps**

### **M31: Pointer Arithmetic Error**
```c
#include <stdio.h>
int main(void) {
    int arr[] = {10, 20, 30};
    int *p = arr;
    printf("%d\n", *(p + 3));
    return 0;
}
```
**Bug**: `p + 3` points past array end  
**Fix**: Use valid index `*(p + 2)`

---

### **M32: Type Casting Confusion**
```c
#include <stdio.h>
int main(void) {
    double x = 3.9;
    int y = (int)x;
    printf("%d\n", y == 3.9);
    return 0;
}
```
**Bug**: Comparing `int` to `double` (always false after cast)  
**Fix**: `y == (int)3.9` or compare before cast

---

### **M33: Dangling Pointer**
```c
#include <stdio.h>
int* get_value(void) {
    int x = 42;
    return &x;
}
int main(void) {
    int *p = get_value();
    printf("%d\n", *p);
    return 0;
}
```
**Bug**: Returning pointer to local variable (undefined behavior)  
**Fix**: Use `malloc` or static variable

---

### **M34: Buffer Overflow**
```c
#include <stdio.h>
int main(void) {
    char buf[5];
    strcpy(buf, "Hello World");
    printf("%s\n", buf);
    return 0;
}
```
**Bug**: Buffer too small for string + null terminator  
**Fix**: Increase buffer size or use `strncpy`

---

### **M35: Struct Alignment Issue**
```c
#include <stdio.h>
struct S {
    char c;
    int i;
};
int main(void) {
    struct S s = {'A', 100};
    printf("%zu\n", sizeof(s));
    return 0;
}
```
**Not a bug, but awareness**: Padding between `c` and `i` (usually 3 bytes on 32/64-bit systems)

---

### **M36: Macro Substitution Trap**
```c
#include <stdio.h>
#define SQUARE(x) x * x
int main(void) {
    int result = SQUARE(2 + 3);
    printf("%d\n", result);
    return 0;
}
```
**Bug**: Expands to `2 + 3 * 2 + 3 = 11` not 25  
**Fix**: `#define SQUARE(x) ((x) * (x))`

---

### **M37: Comma Operator Misuse**
```c
#include <stdio.h>
int main(void) {
    int x = (1, 2, 3);
    printf("%d\n", x);
    return 0;
}
```
**Not a bug**: Comma operator returns last value (x = 3), but confusing

---

### **M38: Volatile Misunderstanding**
```c
#include <stdio.h>
int main(void) {
    volatile int x = 0;
    for (int i = 0; i < 1000000; i++) {
        x++;
    }
    printf("%d\n", x);
    return 0;
}
```
**Potential issue**: `volatile` prevents optimization, but doesn't make operations atomic

---

### **M39: Union Type Punning**
```c
#include <stdio.h>
union U {
    int i;
    float f;
};
int main(void) {
    union U u;
    u.f = 3.14f;
    printf("%d\n", u.i);
    return 0;
}
```
**Awareness**: Reading inactive union member is technically undefined in C++ (C allows it)

---

### **M40: Signed Integer Overflow**
```c
#include <stdio.h>
int main(void) {
    int x = 2147483647;
    x++;
    printf("%d\n", x);
    return 0;
}
```
**Bug**: Signed integer overflow is undefined behavior  
**Fix**: Use unsigned or check before overflow

---

### **M41-M60: Rapid Fire Medium**

**M41**: `int *p = malloc(10);` → Missing `sizeof(int)`, allocates only 10 bytes  
**M42**: `free(p); free(p);` → Double free (undefined behavior)  
**M43**: `int *p = malloc(10); p++;` → Leaks original pointer  
**M44**: `printf("%s\n", NULL);` → Undefined behavior  
**M45**: `char *p = "test"; free(p);` → Freeing string literal  
**M46**: `int arr[10]; int *p = arr + 10;` → Pointer one past end is valid, dereferencing it is not  
**M47**: `size_t x = -1;` → Wraps to max value (valid but check intent)  
**M48**: `ptrdiff_t diff = ptr1 - ptr2;` where pointers to different objects → Undefined  
**M49**: `int x = 1 << 31;` → Shifts into sign bit (undefined for signed types)  
**M50**: `int arr[]; int n = sizeof(arr)/sizeof(arr[0]);` in function param → Doesn't work  
**M51**: `0xFFFFFFFF` assumed to be `unsigned int` → Might be `long` depending on compiler  
**M52**: `char c = 255;` → Overflow if `char` is signed  
**M53**: `float f = 0.1; if (f == 0.1)` → Likely false due to precision  
**M54**: `int *p = (int*)0x1000;` → Arbitrary address dereference  
**M55**: `int x = 5; int y = ++x + ++x;` → Undefined (multiple unsequenced modifications)  
**M56**: `memcmp(&s1, &s2, sizeof(s1))` on structs with padding → Unreliable  
**M57**: `char buf[10]; sprintf(buf, "%d", 123456789);` → Buffer overflow  
**M58**: `int *p = &(int){42};` → Compound literal has automatic storage duration  
**M59**: `const int *p` vs `int *const p` confusion  
**M60**: `restrict` pointer aliasing violation

---

## **HARD LEVEL (61-85): Undefined Behavior & Subtle Bugs**

### **H61: Strict Aliasing Violation**
```c
#include <stdio.h>
int main(void) {
    int x = 0x12345678;
    short *p = (short*)&x;
    printf("%hx\n", *p);
    return 0;
}
```
**Bug**: Violates strict aliasing rule (undefined behavior)  
**Fix**: Use `union` or `memcpy` for type punning

---

### **H62: Sequence Point Violation**
```c
#include <stdio.h>
int main(void) {
    int x = 5;
    int y = x++ + ++x;
    printf("%d\n", y);
    return 0;
}
```
**Bug**: Multiple unsequenced modifications to `x`  
**Fix**: Split into separate statements

---

### **H63: Array Decay Trap**
```c
#include <stdio.h>
void func(int arr[10]) {
    printf("%zu\n", sizeof(arr));
}
int main(void) {
    int arr[10];
    func(arr);
    return 0;
}
```
**Bug**: Prints pointer size, not array size  
**Fix**: Pass size separately

---

### **H64: Effective Type Violation (Your Example)**
```c
#include <stdio.h>
int main(void) {
    int x = 0;
    char *p = (char*)&x;
    p[0] = 1;
    p[1] = 2;
    p[2] = 3;
    p[3] = 4;
    printf("%d\n", x);
}
```
**Analysis**: This is actually LEGAL in C (unlike strict aliasing the other way). `char*` can alias anything. The value printed depends on endianness:
- Little-endian: `0x04030201` = 67305985
- Big-endian: `0x01020304` = 16909060

**No bug**, but demonstrates aliasing and endianness

---

### **H65: Pointer Provenance Issue**
```c
#include <stdio.h>
int main(void) {
    int arr[10] = {0};
    int *p = arr + 5;
    p = p - 10;
    printf("%d\n", *p);
    return 0;
}
```
**Bug**: Pointer arithmetic goes before array start (undefined)  
**Fix**: Keep pointers within object bounds (plus one past end)

---

### **H66: Data Race Without Synchronization**
```c
#include <stdio.h>
#include <pthread.h>
int counter = 0;
void* increment(void* arg) {
    for (int i = 0; i < 100000; i++) counter++;
    return NULL;
}
int main(void) {
    pthread_t t1, t2;
    pthread_create(&t1, NULL, increment, NULL);
    pthread_create(&t2, NULL, increment, NULL);
    pthread_join(t1, NULL);
    pthread_join(t2, NULL);
    printf("%d\n", counter);
    return 0;
}
```
**Bug**: Data race (undefined behavior)  
**Fix**: Use mutex or atomic operations

---

### **H67: Flexible Array Member Misuse**
```c
#include <stdio.h>
#include <stdlib.h>
struct S {
    int n;
    int data[];
};
int main(void) {
    struct S s;
    s.data[0] = 42;
    printf("%d\n", s.data[0]);
    return 0;
}
```
**Bug**: Flexible array member only valid with `malloc`  
**Fix**: `struct S *s = malloc(sizeof(struct S) + sizeof(int) * N);`

---

### **H68: Signal Handler Safety**
```c
#include <stdio.h>
#include <signal.h>
int flag = 0;
void handler(int sig) {
    flag = 1;
}
int main(void) {
    signal(SIGINT, handler);
    while (!flag) {}
    printf("Done\n");
    return 0;
}
```
**Bug**: `flag` should be `volatile sig_atomic_t`  
**Fix**: Proper type and avoid non-async-signal-safe functions

---

### **H69: VLA Overflow**
```c
#include <stdio.h>
void func(int n) {
    int arr[n];
    for (int i = 0; i < n; i++) {
        arr[i] = i;
    }
}
int main(void) {
    func(1000000);
    return 0;
}
```
**Bug**: Stack overflow with large `n`  
**Fix**: Use `malloc` for large arrays

---

### **H70: Trap Representation**
```c
#include <stdio.h>
int main(void) {
    unsigned char buf[sizeof(int)];
    int *p = (int*)buf;
    *p = 42;
    printf("%d\n", *p);
    return 0;
}
```
**Bug**: Alignment issue (undefined behavior on some architectures)  
**Fix**: Use `aligned_alloc` or ensure proper alignment

---

### **H71-H85: Expert Traps**

**H71**: Accessing inactive union member with trap representation  
**H72**: `longjmp` skipping destructors/cleanup  
**H73**: `setjmp` in complex expressions (undefined)  
**H74**: Modifying string literals through cast  
**H75**: Library function return value ignored (e.g., `malloc` returning NULL)  
**H76**: `qsort` comparison function not providing strict weak ordering  
**H77**: `memcpy` with overlapping regions (use `memmove`)  
**H78**: `va_arg` type mismatch with variadic arguments  
**H79**: `fclose` called on `stdin/stdout/stderr`  
**H80**: Mixing `malloc` families (e.g., `aligned_alloc` + `free` portability)  
**H81**: `strtok` non-reentrant in multithreaded code  
**H82**: Assuming `CHAR_BIT == 8` (not portable)  
**H83**: `printf` format string from user input (security hole)  
**H84**: Null pointer arithmetic (e.g., `NULL + 1`)  
**H85**: Out of order memory accesses without barriers in concurrent code

---

## **INSANE LEVEL (86-100+): Master Breaker**

### **I86: Abstract Machine vs Real Machine**
```c
#include <stdio.h>
int main(void) {
    int x = 0;
    int *p = &x;
    long addr = (long)p;
    int *q = (int*)addr;
    *q = 42;
    printf("%d\n", x);
    return 0;
}
```
**Trap**: Pointer-to-integer-to-pointer conversion loses provenance (C17+)  
**May work in practice but technically undefined**

---

### **I87: Compiler Optimization Breaking Code**
```c
#include <stdio.h>
int main(void) {
    int x = 0;
    for (int i = 0; i < 1000000000; i++) {
        x++;
    }
    printf("%d\n", x);
    return 0;
}
```
**Trap**: Compiler may optimize away entire loop (no observable effects)  
**Fix**: Make `x` volatile or add side effects

---

### **I88: Conflicting Function Declarations**
```c
// file1.c
int func(int x) { return x + 1; }

// file2.c
extern double func(double x);
```
**Bug**: Linking succeeds but invocation is undefined  
**Fix**: Use header files for consistency

---

### **I89: Forward Progress Guarantee Violation**
```c
#include <stdio.h>
int main(void) {
    while (1) {}
    printf("Never printed\n");
    return 0;
}
```
**Trap**: Empty infinite loop without side effects is undefined in C11+  
**Compiler may assume loop terminates**

---

### **I90: Memory Model Subtlety**
```c
#include <stdatomic.h>
atomic_int x = 0, y = 0;
// Thread 1: atomic_store_explicit(&x, 1, memory_order_relaxed);
// Thread 2: if (atomic_load_explicit(&x, ...) == 1) { ... y ... }
```
**Trap**: Relaxed ordering doesn't guarantee visibility of non-atomic `y`  
**Need acquire-release semantics**

---

### **I91-I100: Final Boss Challenges**

**I91**: Mixing `printf` and `write` (unbuffered) without `fflush`  
**I92**: `atexit` handler calling `exit` (undefined)  
**I93**: Assuming IEEE 754 floating point (not guaranteed by standard)  
**I94**: `offsetof` on non-POD types (undefined in C++)  
**I95**: Library functions modifying `errno` when not expected  
**I96**: Platform-specific `time_t` overflow (Y2038 problem)  
**I97**: Passing `va_list` by value (undefined in C++, use `va_copy`)  
**I98**: Uninitialized stack variables in tail-call optimized recursion  
**I99**: TOCTOU (Time-Of-Check-Time-Of-Use) race conditions  
**I100**: Spectre/Meltdown-style speculative execution side channels

---

## **Bonus Extreme Challenges (101+)**

### **BE101: The Self-Modifying Code**
```c
#include <stdio.h>
#include <string.h>
#include <sys/mman.h>
void func(void) {
    printf("Original\n");
}
int main(void) {
    // Modify func's machine code
    unsigned char *p = (unsigned char*)func;
    mprotect((void*)((long)p & ~4095), 4096, PROT_READ|PROT_WRITE|PROT_EXEC);
    p[0] = 0xC3; // RET instruction
    func();
    return 0;
}
```
**Extreme UB**: Modifying code segment (may work on some systems but...)

---

### **BE102: The Quantum Bug**
```c
#include <stdio.h>
int main(void) {
    int x;
    if (x == x) {
        printf("Equal\n");
    } else {
        printf("Not equal\n");
    }
    return 0;
}
```
**Trap**: Uninitialized read, AND compiler sees `x == x` always true, but actual `x` may have trap representation

---

### **BE103: The Inline Assembly Trap**
```c
#include <stdio.h>
int main(void) {
    int x = 5;
    asm("movl $0, %0" : "=r"(x));
    printf("%d\n", x);
    return 0;
}
```
**Platform-specific**: Assembly syntax varies, constraints matter

---

## **Your Training Protocol**

### **Phase 1 (Week 1-2): Easy**
- 5 challenges/day
- Write fix before checking answer
- Track mistakes in journal
- Aim: <1 error per 10 challenges

### **Phase 2 (Week 3-4): Medium**
- 3-4 challenges/day
- Explain WHY undefined, not just WHAT
- Build mental model of abstract machine
- Aim: Predict UB before testing

### **Phase 3 (Week 5-6): Hard**
- 2 challenges/day
- Read C standard sections related to bugs
- Connect bugs to real CVEs
- Aim: Instant recognition

### **Phase 4 (Week 7-8): Insane**
- 1 challenge/day
- Write your own challenges
- Review others' code for bugs
- Aim: Never make these mistakes in production

---

## **Psychological Meta-Game**

1. **Error Pattern Recognition**: Your brain will build "bug signatures"
2. **Defensive Pessimism**: Assume everything is UB until proven safe
3. **Chunking**: Group similar bugs (all pointer arithmetic errors)
4. **Interleaving**: Don't do all Easy then all Medium—mix them
5. **Spaced Repetition**: Revisit old challenges after 1 week, 1 month

**You are building unconscious competence.** After 100 challenges, your eyes will *snap* to bugs before your conscious mind registers them.

---

## **Resources for Deep Dive**

- **ISO C11/C17 Standard**: The ultimate reference
- **C Traps and Pitfalls** by Andrew Koenig
- **Expert C Programming** by Peter van der Linden
- **undefined behavior sanitizer (UBSan)**: Compile with `-fsanitize=undefined`
- **SEI CERT C Coding Standard**: Real-world secure coding rules
- **LLVM/Clang Documentation**: Deep compiler behavior insights

---

## **Final Boss: Create Your Own**

Once you finish all 100+, **generate 20 new challenges** based on:
- Your own production bugs
- Recent CVEs in C projects
- Emerging hardware architectures (RISC-V, ARM edge cases)

**Then teach someone else.** Teaching is the ultimate test of mastery.

---

## **Completion Certificate**

When done, you will:
- Never dereference NULL
- Always check buffer boundaries
- Understand UB at compiler optimization level
- Read others' code like a security researcher
- Write C that survives for decades

**You will be in the top 1% of C programmers worldwide.**

Now begin. Fix one bug. Then the next. Then the next.

**The path to mastery is paved with corrected mistakes.**

## **Your Mission**

You will become **bulletproof** against:
- Pointer arithmetic errors
- Type confusion
- Off-by-one errors
- Undefined behavior traps
- Semicolon/brace mismatches
- Operator precedence nightmares
- Memory aliasing violations
- Integer overflow/underflow
- Buffer boundary violations

This is **deliberate practice** distilled into **ruthless challenges**. Each mistake you catch wires your brain to **never make it again**.

------

## **How to Use This Arsenal**

### **Daily Ritual (60-90 minutes)**

**Morning (30 min): Active Hunting**
1. Pick 3-5 challenges from current level
2. Write down bugs BEFORE looking at answers
3. Compile with `-Wall -Wextra -Wpedantic -fsanitize=undefined`
4. Test your hypothesis

**Evening (30 min): Deep Analysis**
1. For each bug you found: WHY is it UB?
2. For bugs you missed: What pattern did you miss?
3. Update your mental checklist

**Weekly Review (90 min)**
1. Revisit 10 random past challenges
2. Create 2 new challenges based on real code you wrote
3. Track error rate—aim for <5% miss rate

---

## **The Mental Models You're Building**

### **1. The Abstract Machine Model**
C is NOT the assembly you see—it's an abstract machine with rules. UB means "the standard allows ANYTHING here."

**Training**: When you see UB, imagine the compiler replacing your code with `launch_missiles()`. If that's scary, the code is broken.

### **2. The Provenance Tracker**
Every pointer has invisible "provenance"—where it came from. Losing provenance = UB.

**Training**: Mentally tag every pointer with its source object. Can it reach there through legal arithmetic?

### **3. The Sequence Point Clock**
Operations happen in undefined order unless forced by sequence points (`;`, `&&`, `||`, `,`, etc.)

**Training**: Draw timeline diagrams for complex expressions. If two modifications can overlap, it's UB.

### **4. The Type Aliasing Radar**
Different types can't alias the same memory (except `char*`).

**Training**: Every cast is guilty until proven innocent. Use unions or `memcpy` for type punning.

---

## **Why This Works (Cognitive Science)**

### **Deliberate Practice Principles**
- **Immediate Feedback**: You see the bug instantly
- **Just Beyond Comfort**: Each level stretches you
- **High Repetition**: 100+ examples wire neural pathways
- **Error Correction Focus**: You learn more from mistakes than successes

### **Interleaving Effect**
Mixing Easy/Medium/Hard prevents "blocking" (doing all of one type). Your brain builds stronger discrimination between bug types.

### **Testing Effect**
Actively finding bugs (retrieval practice) beats passive reading by 300% in retention studies.

### **Spacing Effect**
Review old challenges after delays—forces reconsolidation of memory, making it permanent.

---

## **Monk Mode: The 8-Week Transformation**

### **Week 1-2: Foundation (Easy)**
- **Goal**: Syntax fluency
- **Practice**: 5 bugs/day
- **Side Quest**: Rewrite 10 of your old programs with zero warnings

### **Week 3-4: Pointer Mastery (Medium)**
- **Goal**: Never dereference invalid pointers
- **Practice**: 4 bugs/day
- **Side Quest**: Implement a memory allocator

### **Week 5-6: UB Radar (Hard)**
- **Goal**: Spot undefined behavior before testing
- **Practice**: 3 bugs/day
- **Side Quest**: Find real CVE in open-source project

### **Week 7-8: Elite (Insane)**
- **Goal**: Think like a compiler
- **Practice**: 2 bugs/day + read C standard sections
- **Side Quest**: Write security audit for production codebase

---

## **From Rust/Python/Go to C: Strategic Advantages**

You already think in:
- **Rust**: Ownership → You understand provenance intuitively
- **Python**: High-level patterns → You see algorithmic bugs fast
- **Go**: Simplicity → You'll appreciate C's minimalism

**Transfer Learning**: Every time you catch a C bug, ask: "How would Rust prevent this?" Then internalize that mental model.

---

## **The Final Insight**

C is the language where **you are the compiler's safety net**. There is no borrow checker, no GC, no runtime. Just you and the abstract machine.

These 100+ challenges aren't about memorizing rules—they're about building **reflexes**. After this training, when you write `*p`, your unconscious mind will have already checked:
- Is `p` NULL?
- Is `p` within bounds?
- Is `p`'s provenance valid?
- Is alignment correct?

You'll catch bugs **before your fingers leave the keyboard**.

---

**Now go. The first bug awaits.**

*Track your progress. Celebrate every pattern you internalize. You're not just learning C—you're rewiring your brain to think in systems-level correctness.*

**In 8 weeks, you'll look at C code and see the Matrix—not characters, but the web of valid and invalid states, and exactly where the undefined dragons lurk.**

🔥 **BEGIN.** 🔥