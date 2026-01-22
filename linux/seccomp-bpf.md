# Comprehensive Guide to seccomp-bpf

## Introduction

Seccomp-bpf (secure computing mode with Berkeley Packet Filter) is a Linux kernel security mechanism that allows processes to restrict which system calls they can make. It's a powerful sandboxing tool used in containerization (Docker, LXC), web browsers (Chrome, Firefox), and other security-critical applications.

## What is Seccomp?

Seccomp stands for "secure computing mode." It was introduced in Linux kernel 2.6.12 (2005) as a simple mechanism to restrict processes to a minimal set of system calls: read(), write(), exit(), and sigreturn().

The original seccomp was too restrictive for most applications, so seccomp-bpf was added in Linux 3.5 (2012), allowing fine-grained filtering of system calls using BPF programs.

## Core Concepts

### System Calls

System calls are the interface between user-space applications and the kernel. Every time a program needs kernel services (file I/O, network operations, process creation), it makes a syscall. Seccomp-bpf controls which syscalls a process can execute.

### BPF (Berkeley Packet Filter)

BPF is a virtual machine inside the Linux kernel originally designed for packet filtering. In seccomp context, BPF programs examine syscall metadata and decide whether to allow or deny the call.

### Seccomp Modes

Linux supports three seccomp modes:

**SECCOMP_MODE_DISABLED (0)**: No restrictions (default state).

**SECCOMP_MODE_STRICT (1)**: The original seccomp mode, allowing only read, write, exit, and sigreturn. Rarely used today.

**SECCOMP_MODE_FILTER (2)**: The seccomp-bpf mode, using BPF programs for flexible filtering.

## How Seccomp-bpf Works

When a process makes a system call, the kernel first checks if seccomp filtering is active. If so, it runs the attached BPF program against syscall metadata. The BPF program returns an action code that tells the kernel what to do.

### The Filtering Process

1. Process attempts a system call
2. Kernel suspends syscall execution
3. BPF program examines syscall data (number, arguments, architecture)
4. BPF program returns action code
5. Kernel enforces the action (allow, deny, kill, trace, etc.)

### BPF Program Structure

Seccomp BPF programs operate on a data structure called `struct seccomp_data`, which contains:

- `nr`: The system call number
- `arch`: The architecture identifier (to handle multi-arch systems)
- `instruction_pointer`: Where the syscall was invoked
- `args[6]`: Up to 6 syscall arguments (64-bit values)

The BPF program is an array of `struct sock_filter` instructions that perform comparisons, arithmetic, and jumps to decide the fate of the syscall.

## Return Values (Actions)

BPF programs return 32-bit values where the high 16 bits specify the action and the low 16 bits provide data for certain actions:

**SECCOMP_RET_KILL_PROCESS**: Terminates the entire process immediately. Added in kernel 4.14.

**SECCOMP_RET_KILL_THREAD**: Kills only the thread that made the syscall (legacy SECCOMP_RET_KILL).

**SECCOMP_RET_TRAP**: Sends SIGSYS signal to the process, allowing it to handle the violation.

**SECCOMP_RET_ERRNO**: Causes the syscall to fail with a specified errno value (lower 16 bits).

**SECCOMP_RET_TRACE**: Notifies a tracer (ptrace) to inspect and potentially modify the syscall.

**SECCOMP_RET_LOG**: Logs the syscall but allows it to proceed (kernel 4.14+).

**SECCOMP_RET_ALLOW**: Permits the syscall to execute normally.

When multiple filters are installed, the most restrictive action wins.

## Installing Seccomp Filters

### Using prctl()

The primary interface is the `prctl()` system call with `PR_SET_SECCOMP`:

```c
prctl(PR_SET_SECCOMP, SECCOMP_MODE_FILTER, &prog);
```

Where `prog` is a `struct sock_fprog` containing the BPF program.

### Using seccomp()

The newer `seccomp()` syscall (kernel 3.17+) provides more features:

```c
seccomp(SECCOMP_SET_MODE_FILTER, flags, &prog);
```

### Important Flags

**SECCOMP_FILTER_FLAG_TSYNC**: Synchronizes filter across all threads in the process.

**SECCOMP_FILTER_FLAG_LOG**: Logs actions in the audit log.

**SECCOMP_FILTER_FLAG_SPEC_ALLOW**: Allows speculation for allowed syscalls (Spectre mitigation).

**SECCOMP_FILTER_FLAG_NEW_LISTENER**: Returns a file descriptor for user-space notification (kernel 5.0+).

## BPF Instruction Set

Seccomp uses classic BPF (cBPF), not the newer extended BPF (eBPF). The instruction format:

```c
struct sock_filter {
    __u16 code;    /* Opcode */
    __u8  jt;      /* Jump if true */
    __u8  jf;      /* Jump if false */
    __u32 k;       /* Generic multiuse field */
};
```

### Common Opcodes

**LD (Load)**: Load values from seccomp_data into the accumulator.
- `BPF_LD | BPF_W | BPF_ABS`: Load word at absolute offset

**JMP (Jump)**: Conditional and unconditional jumps.
- `BPF_JMP | BPF_JEQ | BPF_K`: Jump if accumulator equals k
- `BPF_JMP | BPF_JGT | BPF_K`: Jump if accumulator greater than k

**RET (Return)**: Return a value (the action code).
- `BPF_RET | BPF_K`: Return constant value k

**ALU (Arithmetic)**: Bitwise and arithmetic operations.
- `BPF_ALU | BPF_AND | BPF_K`: Bitwise AND with k

### Offset Macros

To access fields in `struct seccomp_data`, use offsetof():

```c
offsetof(struct seccomp_data, nr)              // syscall number
offsetof(struct seccomp_data, arch)            // architecture
offsetof(struct seccomp_data, args[0])         // first argument
```

## Writing Seccomp Filters

### Manual BPF Programming

A simple filter to allow only specific syscalls:

```c
struct sock_filter filter[] = {
    /* Load architecture */
    BPF_STMT(BPF_LD | BPF_W | BPF_ABS, offsetof(struct seccomp_data, arch)),
    /* Check if x86_64 */
    BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, AUDIT_ARCH_X86_64, 1, 0),
    /* Wrong architecture, kill */
    BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_KILL_PROCESS),
    
    /* Load syscall number */
    BPF_STMT(BPF_LD | BPF_W | BPF_ABS, offsetof(struct seccomp_data, nr)),
    
    /* Allow read (syscall 0) */
    BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_read, 0, 1),
    BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ALLOW),
    
    /* Allow write (syscall 1) */
    BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_write, 0, 1),
    BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ALLOW),
    
    /* Allow exit_group (syscall 231) */
    BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_exit_group, 0, 1),
    BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ALLOW),
    
    /* Default: deny all other syscalls */
    BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_KILL_PROCESS)
};

struct sock_fprog prog = {
    .len = sizeof(filter) / sizeof(filter[0]),
    .filter = filter
};
```

### Using libseccomp

Libseccomp provides a higher-level API to avoid manual BPF programming:

```c
#include <seccomp.h>

scmp_filter_ctx ctx = seccomp_init(SECCOMP_RET_KILL_PROCESS);
seccomp_rule_add(ctx, SECCOMP_RET_ALLOW, SCMP_SYS(read), 0);
seccomp_rule_add(ctx, SECCOMP_RET_ALLOW, SCMP_SYS(write), 0);
seccomp_rule_add(ctx, SECCOMP_RET_ALLOW, SCMP_SYS(exit_group), 0);
seccomp_load(ctx);
```

Libseccomp handles architecture detection, syscall number translation, and BPF generation automatically.

## Advanced Features

### Argument Filtering

You can filter based on syscall arguments. For example, allowing write only to stdout/stderr:

```c
seccomp_rule_add(ctx, SECCOMP_RET_ALLOW, SCMP_SYS(write), 1,
                 SCMP_A0(SCMP_CMP_EQ, STDOUT_FILENO));
seccomp_rule_add(ctx, SECCOMP_RET_ALLOW, SCMP_SYS(write), 1,
                 SCMP_A0(SCMP_CMP_EQ, STDERR_FILENO));
```

This checks the first argument (file descriptor) of the write syscall.

### Filter Chaining

Multiple filters can be loaded sequentially. They form a chain evaluated in reverse order of installation (last installed runs first). The most restrictive action across all filters wins.

### User Notification (SECCOMP_RET_USER_NOTIF)

Kernel 5.0+ allows delegating syscall decisions to a user-space supervisor. When SECCOMP_RET_USER_NOTIF is returned, the syscall is suspended and a notification is sent via a file descriptor. The supervisor can then:

- Allow the syscall
- Deny with an errno
- Allow with modified return value
- Continue the syscall under supervision

This enables sophisticated sandboxing where privileged operations can be mediated by a trusted process.

```c
int listener = seccomp(SECCOMP_SET_MODE_FILTER, 
                       SECCOMP_FILTER_FLAG_NEW_LISTENER, &prog);
// listener is a fd for receiving notifications
```

### Synchronization Across Threads

By default, seccomp filters apply only to the calling thread. Use SECCOMP_FILTER_FLAG_TSYNC to apply to all threads:

```c
seccomp(SECCOMP_SET_MODE_FILTER, SECCOMP_FILTER_FLAG_TSYNC, &prog);
```

## Architecture Considerations

### Multi-architecture Support

On systems supporting multiple architectures (like x86_64 with 32-bit compatibility), you must handle both:

```c
BPF_STMT(BPF_LD | BPF_W | BPF_ABS, offsetof(struct seccomp_data, arch)),
BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, AUDIT_ARCH_X86_64, 0, 2),
/* x86_64 specific filter */
BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, AUDIT_ARCH_I386, 0, 2),
/* i386 specific filter */
```

Different architectures have different syscall numbers for the same operation.

### Syscall Number Portability

Syscall numbers vary across architectures. Always validate the architecture field before checking syscall numbers, or use libseccomp which handles this.

## Security Considerations

### Bypasses and Pitfalls

**Time-of-check-time-of-use (TOCTOU)**: Seccomp checks arguments by value at syscall entry. Pointers cannot be dereferenced, so you cannot filter based on pointed-to content reliably.

**Inherited File Descriptors**: Seccomp cannot restrict operations on already-open file descriptors. Open dangerous files before installing filters, or use other mechanisms (namespaces, capabilities).

**Indirect Syscalls**: Some syscalls can indirectly invoke others (ioctl, fcntl, prctl). Block these or carefully whitelist specific operations.

**Architecture Confusion**: Failing to validate architecture can allow 32-bit syscalls to bypass 64-bit filters.

**Incomplete Coverage**: Missing essential syscalls (like rt_sigreturn for signal handling) can break your program.

### Defense in Depth

Seccomp works best combined with other security mechanisms:

- **Namespaces**: Isolate resources (PID, network, mount, etc.)
- **Capabilities**: Drop unnecessary privileges
- **AppArmor/SELinux**: Mandatory access control
- **Chroot/pivot_root**: Filesystem isolation
- **Resource limits (rlimit)**: Prevent resource exhaustion

### One-Way Door

Once installed, seccomp filters cannot be removed or relaxed by the filtered process. This is fundamental to seccomp's security model. Child processes inherit filters. The only way to escape is to exec() a new program (if allowed), which preserves filters, or to have never installed them.

## Debugging Seccomp Filters

### Common Issues

**Program Dies Immediately**: Likely blocking essential syscalls (rt_sigreturn, exit, exit_group).

**Segmentation Faults**: May be blocked syscalls like mmap, brk, or signal handling syscalls.

**Mysterious Errors**: Use strace to see which syscalls are being denied.

### Debugging Techniques

**strace**: Trace system calls to see what your program needs:
```bash
strace -f ./your_program 2>&1 | grep -v ENOSYS
```

**Audit Logs**: With SECCOMP_FILTER_FLAG_LOG, denials appear in the kernel audit log:
```bash
ausearch -m SECCOMP
```

**SECCOMP_RET_TRACE**: Use with ptrace to intercept and inspect denied syscalls without killing the process.

**Incremental Development**: Start with SECCOMP_RET_LOG to observe syscall patterns, then tighten to SECCOMP_RET_ERRNO or SECCOMP_RET_KILL.

## Practical Examples

### Minimal Sandbox

A process that only prints to stdout and exits:

```c
#include <stdio.h>
#include <seccomp.h>

int main() {
    scmp_filter_ctx ctx = seccomp_init(SECCOMP_RET_KILL);
    
    seccomp_rule_add(ctx, SECCOMP_RET_ALLOW, SCMP_SYS(write), 0);
    seccomp_rule_add(ctx, SECCOMP_RET_ALLOW, SCMP_SYS(exit_group), 0);
    seccomp_rule_add(ctx, SECCOMP_RET_ALLOW, SCMP_SYS(exit), 0);
    
    seccomp_load(ctx);
    
    printf("Hello, sandboxed world!\n");  // Will work
    // Any other syscall will kill the process
    
    return 0;
}
```

### Restricting Network Access

Block all socket operations:

```c
seccomp_rule_add(ctx, SECCOMP_RET_ERRNO(EACCES), SCMP_SYS(socket), 0);
seccomp_rule_add(ctx, SECCOMP_RET_ERRNO(EACCES), SCMP_SYS(connect), 0);
seccomp_rule_add(ctx, SECCOMP_RET_ERRNO(EACCES), SCMP_SYS(bind), 0);
```

### Read-Only Filesystem Access

Allow only read operations, deny write/create:

```c
seccomp_rule_add(ctx, SECCOMP_RET_ALLOW, SCMP_SYS(open), 1,
                 SCMP_A1(SCMP_CMP_MASKED_EQ, O_WRONLY | O_RDWR | O_CREAT, 0));
seccomp_rule_add(ctx, SECCOMP_RET_ALLOW, SCMP_SYS(openat), 1,
                 SCMP_A2(SCMP_CMP_MASKED_EQ, O_WRONLY | O_RDWR | O_CREAT, 0));
```

## Real-World Usage

### Docker/Containers

Docker uses seccomp to restrict container capabilities. The default profile blocks around 44 syscalls out of 300+, including those for kernel module loading, system time modification, and other privileged operations.

### Chrome/Chromium

Each renderer process runs in a tight seccomp sandbox, dramatically reducing the attack surface for exploited web content. The sandbox is combined with namespaces and other isolation techniques.

### systemd

Systemd services can specify seccomp filters via `SystemCallFilter=` directives in unit files:

```ini
[Service]
SystemCallFilter=@system-service
SystemCallFilter=~@privileged @resources
```

### SSH

OpenSSH uses seccomp to sandbox the pre-authentication phase, limiting what attackers can do before logging in.

## Performance Implications

Seccomp-bpf has minimal performance overhead. The BPF program runs in kernel space without context switches. Typical overhead is single-digit microseconds per syscall, negligible for most applications. Complex filters with many rules may add slight latency.

## Limitations

**No Pointer Dereferencing**: BPF cannot follow pointers, limiting argument-based filtering to scalar values.

**Limited State**: BPF programs cannot maintain state across syscalls (no memory/variables).

**Complexity**: Manual BPF programming is error-prone; use libseccomp when possible.

**Syscall Coverage**: New syscalls require filter updates. Consider default-deny policies.

**No Revocation**: Filters cannot be removed, making development and testing challenging.

## Best Practices

1. **Default Deny**: Start with SECCOMP_RET_KILL or SECCOMP_RET_ERRNO and whitelist needed syscalls.

2. **Test Thoroughly**: Test on all target architectures and kernel versions.

3. **Use libseccomp**: Avoid manual BPF unless you need features libseccomp doesn't support.

4. **Validate Architecture**: Always check the architecture field first.

5. **Essential Syscalls**: Always allow rt_sigreturn, sigreturn, exit, exit_group, and restart_syscall.

6. **Logging First**: Use SECCOMP_RET_LOG during development to identify needed syscalls.

7. **Combine Defenses**: Layer seccomp with namespaces, capabilities, and MAC systems.

8. **Document Filters**: Clearly document why each syscall is allowed or denied.

9. **Version Awareness**: Check kernel version for feature availability.

10. **Graceful Degradation**: Consider SECCOMP_RET_ERRNO instead of killing for non-critical denials.

## Future Developments

The seccomp ecosystem continues evolving. Recent additions include user-space notification (allowing sophisticated mediation), better logging, and integration with other security frameworks. eBPF may eventually replace cBPF for seccomp, offering more expressiveness, though this faces security review challenges.

## Conclusion

Seccomp-bpf is a powerful, flexible sandboxing mechanism that significantly reduces attack surface by restricting system call access. While it requires careful implementation and cannot prevent all attacks, it's an essential tool in modern security architectures. Combined with other isolation techniques, seccomp enables building robust, defense-in-depth systems that limit damage from compromised processes.