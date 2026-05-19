## `__func__` in Linux Kernel Code

`__func__` is a **predefined identifier in C99/C11** (and GCC as an extension in older standards) that expands to the name of the current function as a string literal.

```c
void my_function(void) {
    printk(KERN_DEBUG "%s: something happened\n", __func__);
    // prints: "my_function: something happened"
}
```

---

### How It Works

It behaves as if the compiler implicitly declares:
```c
static const char __func__[] = "function_name";
```
at the beginning of every function body.

---

### Common Uses in the Kernel

**1. Debug/error logging**
```c
pr_err("%s: failed to allocate memory\n", __func__);
```

**2. Inside macros** — since macros lose their call-site context, `__func__` captures the *caller's* function name:
```c
#define MY_ASSERT(cond) \
    do { if (!(cond)) pr_warn("%s: assertion failed\n", __func__); } while (0)
```

**3. Tracing and WARN macros** — kernel helpers like `WARN_ON()`, `BUG()`, `dev_dbg()` all embed `__func__` internally.

**4. Lock debugging**
```c
mutex_lock(&my_lock);
pr_debug("%s: acquired lock\n", __func__);
```

---

### Related Identifiers

| Identifier | Expands to | Standard |
|---|---|---|
| `__func__` | Current function name | C99 |
| `__FUNCTION__` | Same (GCC extension, older alias) | GCC |
| `__PRETTY_FUNCTION__` | Full signature (useful in C++) | GCC |
| `__LINE__` | Current line number | C89 |
| `__FILE__` | Current filename | C89 |

---

### Note on `__FUNCTION__`

You'll see both in kernel code. `__func__` is the **standard** form and preferred in modern kernel code. `__FUNCTION__` is a legacy GCC-ism that does the same thing — the kernel's coding style guide recommends `__func__` over `__FUNCTION__`.

Great find — I can see the full function in the source. Here's a detailed breakdown:

---

## `icmp_ext_iio_addr4_find()`

```c
static __be32 icmp_ext_iio_addr4_find(const struct net_device *dev)
{
    struct in_device *in_dev;
    struct in_ifaddr *ifa;

    in_dev = __in_dev_get_rcu(dev);
    if (!in_dev)
        return 0;

    /* It is unclear from RFC 5837 which IP address should be chosen, but
     * it makes sense to choose a global unicast address.
     */
    in_dev_for_each_ifa_rcu(ifa, in_dev) {
        if (READ_ONCE(ifa->ifa_flags) & IFA_F_SECONDARY)
            continue;

        if (ifa->ifa_scope != RT_SCOPE_UNIVERSE ||
            ipv4_is_multicast(ifa->ifa_address))
            continue;

        return ifa->ifa_address;
    }

    return 0;
}
```

---

### What it does

This function picks a **representative IPv4 address** for a network interface, to be embedded inside an **ICMP Extended Interface Information Object (IIO)** as defined by **RFC 5837**.

RFC 5837 extends ICMP error messages (like *Time Exceeded* or *Destination Unreachable*) to include extra metadata about the interface(s) involved — things like the interface index, name, MTU, and an **IP address** that identifies that interface. This function finds that IP address.

---

### Breaking down each part

**`static __be32`** — returns a **big-endian 32-bit** IPv4 address (network byte order), only visible within this file.

**`__in_dev_get_rcu(dev)`** — gets the IPv4-specific state (`in_device`) for the net device. The `_rcu` suffix means it must be called inside an RCU read-side critical section (which the caller, `icmp_ext_iio_iif_append()`, does via `rcu_read_lock()`).

**`in_dev_for_each_ifa_rcu(ifa, in_dev)`** — iterates over all IPv4 addresses configured on that interface (a device can have multiple — primary + secondary aliases).

**The filtering logic** skips addresses that are:
| Condition | Reason |
|---|---|
| `IFA_F_SECONDARY` | Secondary/alias addresses (e.g. `eth0:1`) |
| `ifa_scope != RT_SCOPE_UNIVERSE` | Non-global scopes (link-local, loopback, etc.) |
| `ipv4_is_multicast()` | Multicast addresses |

It returns the **first primary, global-scope, unicast address** found, which is the most meaningful address to identify the interface to a remote host.

---

### Where it's called

It's called from `icmp_ext_iio_iif_append()`, which builds the IIO sub-object appended to outgoing ICMP errors:

```c
data = icmp_ext_iio_addr4_find(dev);
if (data) {
    addr4_subobj = skb_put_zero(skb, sizeof(*addr4_subobj));
    addr4_subobj->afi = htons(ICMP_AFI_IP);
    addr4_subobj->addr4 = data;
    objh->class_type |= ICMP_EXT_CTYPE_IIO_IPADDR;
}
```

So the returned address gets embedded as the **Interface Address Sub-Object** inside the ICMP extension, allowing the receiver of the ICMP error to identify exactly which interface on a router caused the error. This is useful for network diagnostics tools like `traceroute`.

Based on the uploaded file containing **"predefined identifier"** — here's what that means in C:

---

## Predefined Identifiers in C

A **predefined identifier** is a name that the compiler (or C standard) automatically defines for you — you don't declare it yourself, it just exists in every scope.

### The main one: `__func__`

Defined by **C99** — in every function, the compiler implicitly creates:

```c
static const char __func__[] = "function_name";
```

So you can use it without declaring it:

```c
void foo(void) {
    printf("%s\n", __func__);  // prints "foo"
}
```

---

### Predefined vs. similar concepts

| Term | Example | Who defines it |
|---|---|---|
| **Predefined identifier** | `__func__` | C standard (compiler inserts it) |
| **Predefined macro** | `__FILE__`, `__LINE__`, `__DATE__` | C preprocessor |
| **Reserved identifier** | `_Foo`, `__bar` | Names reserved for the implementation |
| **Standard library identifier** | `printf`, `NULL` | Standard library headers |

---

### Key distinction

- **Predefined macros** like `__FILE__` and `__LINE__` are handled by the **preprocessor** — they're textually substituted before compilation.
- **`__func__`** is a **predefined identifier** — it's a real `const char[]` variable inserted by the **compiler** itself, not the preprocessor. That's why `"hello " __func__` (string concatenation) doesn't work — it's not a string literal.

This distinction came up in the earlier discussion about `__func__` in Linux kernel code.

## RCU — Read-Copy-Update

RCU is a **synchronization mechanism** used heavily in the Linux kernel. It's designed to allow **many concurrent readers** with **no locking overhead**, while still allowing writers to safely update shared data.

---

### The core idea

Instead of locking data when reading, RCU lets readers access data **freely and locklessly**. When a writer wants to update something, it:

1. **Copies** the data structure
2. **Modifies** the copy
3. **Atomically replaces** the pointer to point to the new version
4. **Waits** until all ongoing readers are done with the old version
5. **Frees** the old version

```
Before update:        After update:

ptr ──► [old data]    ptr ──► [new data]
                               [old data]  ← freed after grace period
```

---

### The three primitives

```c
// READER SIDE — very cheap, disables preemption
rcu_read_lock();
    p = rcu_dereference(ptr);   // safe pointer read
    // use p...
rcu_read_unlock();

// WRITER SIDE
new = kmalloc(...);
*new = *old;           // copy
new->field = new_val;  // modify
rcu_assign_pointer(ptr, new);   // atomic replace
synchronize_rcu();     // wait for all readers to finish
kfree(old);            // now safe to free
```

---

### Why it's fast

| Aspect | Mutex/Spinlock | RCU |
|---|---|---|
| Reader cost | Lock + unlock | Nearly zero |
| Reader blocking | Can block | Never blocks |
| Writer cost | Low | Higher (must wait) |
| Use case | Read/write balanced | Read-heavy data |

---

### The `_rcu` naming convention

In the kernel, the `_rcu` suffix signals RCU usage — as seen in the `icmp.c` code earlier:

```c
in_dev = __in_dev_get_rcu(dev);     // must be called under rcu_read_lock()
in_dev_for_each_ifa_rcu(ifa, in_dev); // RCU-safe iteration
rcu_read_lock();                    // start of read-side critical section
dev = dev_get_by_index_rcu(net, iif);
rcu_read_unlock();
```

The `_rcu` suffix is a **contract**: "you must hold the RCU read lock when calling this." The kernel relies on naming conventions because there's no compiler enforcement.

---

### The "grace period"

The key concept is the **grace period** — the time the writer waits before freeing old data. RCU guarantees that after `synchronize_rcu()` returns, **no reader still holds a reference to the old data**, making it safe to free. Readers never block writers; they just need to finish their current read-side critical section.

This makes RCU ideal for the kernel's networking code, where routing tables and interface addresses are read millions of times per second but updated rarely.