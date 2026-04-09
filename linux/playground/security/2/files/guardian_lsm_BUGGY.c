/*
 * guardian_lsm_BUGGY.c — INTENTIONAL BUGS for learning purposes
 *
 * This file demonstrates two classes of kernel bugs:
 *   BUG 1 (Code Bug):  Stack buffer overflow + wrong string comparison
 *   BUG 2 (Logic Bug): Inverted capability check — allows non-root, blocks root
 *
 * For each bug:
 *   - WHAT: describe the bug
 *   - WHY IT'S DANGEROUS: the consequence
 *   - HOW TO FIND IT: tools and techniques
 *   - FIX: the corrected code
 */

#include <linux/module.h>
#include <linux/lsm_hooks.h>
#include <linux/fs.h>
#include <linux/slab.h>
#include <linux/security.h>

/* ============================================================
 * BUG 1 — Code Bug: Stack buffer overflow + strlen on non-terminated string
 * ============================================================
 *
 * WHAT: `d_name.name` is a kernel string but NOT guaranteed to be
 * null-terminated in all kernel versions. Using `strlen()` on it without
 * a length bound can read past the end of the string = stack/heap corruption.
 * Also: using a fixed-size stack buffer `char buf[32]` for a path that
 * can be up to PATH_MAX (4096) bytes causes stack overflow.
 *
 * DANGEROUS: Stack overflow in kernel = immediate kernel panic (oops).
 * Buffer overread = information leak or kernel crash.
 *
 * HOW TO FIND:
 *   1. KASAN (Kernel Address Sanitizer): CONFIG_KASAN=y
 *      Instruments every memory access. Catches out-of-bounds reads/writes.
 *      Run: ./qemu ... -append "kasan=1"
 *      KASAN will print: "BUG: KASAN: stack-out-of-bounds" with a full trace.
 *   2. Sparse: make C=2 — flags array indexing issues and unbounded strlen.
 *   3. Code review: any time you see strlen() on a kernel string, ask:
 *      "Is this guaranteed null-terminated? What is the max length?"
 */

/* BUGGY VERSION ─────────────────────────────────────────────── */
static int guardian_file_open_BUGGY(struct file *file)
{
    /* BUG: buf is only 32 bytes. d_name.name can be up to NAME_MAX = 255 bytes.
     * If the filename is > 32 chars, we write past buf onto the stack.
     * Stack variables in the kernel sit in the kernel stack (8KB by default).
     * Overwriting them corrupts saved return addresses → control flow hijack. */
    char buf[32];                           /* ← BUG: too small               */
    const char *name = file->f_path.dentry->d_name.name;

    /* BUG: strlen() on `name` has no upper bound.
     * If name is not null-terminated (can happen with certain network filesystems
     * or crafted dentry names), strlen() reads until it finds '\0' — potentially
     * reading into adjacent kernel memory. */
    int len = strlen(name);                 /* ← BUG: no length limit          */

    /* BUG: no bounds check before copy */
    memcpy(buf, name, len);                 /* ← BUG: buf overflow if len > 32 */
    buf[len] = '\0';                        /* ← BUG: buf[32] = out of bounds  */

    pr_info("guardian: file opened: %s\n", buf);
    return 0;
}

/* FIXED VERSION ─────────────────────────────────────────────── */
static int guardian_file_open_FIXED(struct file *file)
{
    const char *name = file->f_path.dentry->d_name.name;

    /* FIX 1: Use strnlen() with an explicit upper bound (NAME_MAX = 255).
     * strnlen() stops at the first '\0' OR at maxlen, whichever comes first.
     * This is always safe regardless of whether name is null-terminated. */
    size_t len = strnlen(name, NAME_MAX);

    /* FIX 2: Use pr_info with %.*s — print exactly `len` characters from `name`.
     * No copy needed at all. This is both safer and more efficient. */
    pr_info("guardian: file opened: %.*s\n", (int)len, name);

    /* Alternative if you truly need a local copy: */
    /* char buf[NAME_MAX + 1];
     * strlcpy(buf, name, sizeof(buf));  // strlcpy always null-terminates */

    return 0;
}


/* ============================================================
 * BUG 2 — Logic Bug: Inverted capability check
 * ============================================================
 *
 * WHAT: The condition is ! (NOT) capable() — meaning:
 *   "if the process DOES have CAP_DAC_OVERRIDE, BLOCK it"
 *   "if the process does NOT have CAP_DAC_OVERRIDE (non-root), ALLOW it"
 *
 * This is exactly backwards. Non-root processes sail through.
 * Root processes get blocked. The security policy is inverted.
 *
 * DANGEROUS: This is a SECURITY BYPASS. An attacker who is non-root can
 * freely create files in /tmp. Privileged system daemons (running as root)
 * get denied legitimate operations and crash/fail in unexpected ways.
 *
 * WHY THIS IS HARD TO FIND:
 *   - The code compiles perfectly — no warnings.
 *   - The kernel boots fine — no crash at load time.
 *   - The bug only manifests under specific conditions (file creation in /tmp).
 *   - In log-only mode (before enforcement was added) this was invisible.
 *
 * HOW TO FIND:
 *   1. Unit test with both root and non-root processes:
 *        touch /tmp/test_as_root       # should succeed if not in policy
 *        su nobody -c "touch /tmp/x"  # should be blocked
 *   2. Systematic test: write a test script that verifies each policy decision.
 *   3. Code review: whenever you see `if (!capable(...)) { allow }`, question it.
 *      The normal pattern is `if (!capable(...)) { block }`.
 *   4. Fuzzing: syzkaller (kernel fuzzer) generates syscall sequences and
 *      checks for inconsistent policy enforcement.
 */

/* BUGGY VERSION ─────────────────────────────────────────────── */
static int guardian_inode_create_BUGGY(struct mnt_idmap *idmap,
                                        struct inode *dir,
                                        struct dentry *dentry,
                                        umode_t mode)
{
    char *path_buf;
    char *full_path;
    int ret = 0;

    /* BUG: condition is inverted!
     * `!capable(CAP_DAC_OVERRIDE)` is TRUE when the process is NON-ROOT.
     * So we return 0 (allow) for NON-ROOT, and fall through to the block
     * check only for ROOT. This is a privilege escalation vulnerability. */
    if (!capable(CAP_DAC_OVERRIDE))        /* ← BUG: inverted logic            */
        return 0;

    path_buf = kmalloc(PATH_MAX, GFP_KERNEL);
    if (!path_buf)
        return -ENOMEM;

    full_path = dentry_path_raw(dentry->d_parent, path_buf, PATH_MAX);
    if (IS_ERR(full_path)) {
        kfree(path_buf);
        return PTR_ERR(full_path);
    }

    if (strncmp(full_path, "/tmp", 4) == 0) {
        pr_warn("guardian: BLOCKED (root?) creation in %s\n", full_path);
        ret = -EPERM;
    }

    kfree(path_buf);
    return ret;
}

/* FIXED VERSION ─────────────────────────────────────────────── */
static int guardian_inode_create_FIXED(struct mnt_idmap *idmap,
                                        struct inode *dir,
                                        struct dentry *dentry,
                                        umode_t mode)
{
    char *path_buf;
    char *full_path;
    int ret = 0;

    /* FIX: The correct logic is:
     * "If the process HAS the privilege (is root/capable), ALLOW it (return 0)."
     * "If the process does NOT have the privilege, CHECK the policy." */
    if (capable(CAP_DAC_OVERRIDE))         /* ← FIX: no ! operator             */
        return 0;

    path_buf = kmalloc(PATH_MAX, GFP_KERNEL);
    if (!path_buf)
        return -ENOMEM;

    full_path = dentry_path_raw(dentry->d_parent, path_buf, PATH_MAX);
    if (IS_ERR(full_path)) {
        kfree(path_buf);
        return PTR_ERR(full_path);
    }

    if (strncmp(full_path, "/tmp", 4) == 0) {
        pr_warn("guardian: BLOCKED non-root creation in %s by pid=%d\n",
                full_path, current->pid);
        ret = -EPERM;
    }

    kfree(path_buf);
    return ret;
}

/*
 * SUMMARY OF FIXES:
 *
 * Bug 1 (Code bug — buffer overflow):
 *   Root cause: fixed-size stack buffer + unbounded string operation.
 *   Fix: use pr_info with %.*s and strnlen(), eliminating the copy entirely.
 *   Detection: KASAN, sparse, careful code review.
 *
 * Bug 2 (Logic bug — inverted capability check):
 *   Root cause: off-by-one logical inversion (`!` in wrong place).
 *   Fix: remove the `!` from the capability check.
 *   Detection: functional testing with root/non-root users, syzkaller, audit.
 *
 * Mental model: Every kernel security check follows this pattern:
 *   if (process_is_allowed())
 *       return 0;   // fast path: trusted process, skip expensive check
 *   // slow path: run full policy check
 *   if (operation_is_blocked())
 *       return -EPERM;
 *   return 0;
 */
