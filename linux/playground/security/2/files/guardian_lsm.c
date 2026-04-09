// SPDX-License-Identifier: GPL-2.0-only
/*
 * guardian_lsm.c — Guardian Linux Security Module
 *
 * A demonstration LSM that:
 *   1. Audits every file_open event (logs to kernel ring buffer)
 *   2. Blocks file creation in /tmp by non-root processes
 *   3. Audits privilege escalation via task_fix_setuid hook
 *   4. Exposes a /sys/kernel/security/guardian/enabled control file
 *
 * Key concepts used:
 *   - security_hook_list: the linked-list structure that connects your
 *     callback to the kernel's hook dispatch table.
 *   - lsm_id: a struct (Linux 6.1+) that uniquely identifies your LSM.
 *   - struct cred: holds process credentials (uid, gid, capabilities).
 *   - struct path / struct dentry / struct inode: kernel objects
 *     representing filesystem paths, directory entries, and file metadata.
 *   - capable(): checks if the current process has a given capability.
 *   - securityfs_create_file(): creates a file under /sys/kernel/security/
 *   - RCU (Read-Copy-Update): a lock-free synchronization mechanism used
 *     throughout the kernel for performance. We use rcu_read_lock() when
 *     accessing credentials.
 *
 * Build: See Makefile in this directory.
 * Load:  sudo insmod guardian_lsm.ko
 * Check: dmesg | grep guardian
 */

#include <linux/module.h>       /* MODULE_*, module_init/exit             */
#include <linux/lsm_hooks.h>    /* security_hook_list, lsm_id             */
#include <linux/cred.h>         /* struct cred, current_cred(), capable()  */
#include <linux/fs.h>           /* struct file, struct inode, struct path  */
#include <linux/namei.h>        /* struct inode_operations                 */
#include <linux/string.h>       /* strncmp(), strlen()                     */
#include <linux/slab.h>         /* kmalloc(), kfree()                      */
#include <linux/uaccess.h>      /* copy_to_user(), copy_from_user()        */
#include <linux/security.h>     /* securityfs_create_file/dir, lsm_id      */
#include <linux/seq_file.h>     /* seq_read, seq_lseek                     */
#include <linux/atomic.h>       /* atomic_t, atomic_read(), atomic_set()   */

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Guardian LSM Developer");
MODULE_DESCRIPTION("Guardian Linux Security Module — educational demo");
MODULE_VERSION("1.0");

/* =========================================================================
 * GLOBAL STATE
 * =========================================================================
 * atomic_t: a type whose read-modify-write operations are guaranteed to be
 * atomic (uninterruptible). Critical in the kernel because multiple CPUs can
 * run code simultaneously. Never use plain int for shared mutable state.
 */
static atomic_t guardian_enabled = ATOMIC_INIT(1);  /* 1 = enforcement on */

/* Path prefix we block creation in (non-root) */
#define BLOCKED_PATH_PREFIX  "/tmp"
#define BLOCKED_PATH_LEN     4

/* Securityfs directory and file dentries (directory entry pointers) */
static struct dentry *guardian_dir;
static struct dentry *guardian_enabled_file;

/* =========================================================================
 * HOOK IMPLEMENTATIONS
 * =========================================================================
 */

/*
 * guardian_file_open — called by the VFS before any process opens a file.
 *
 * Parameters:
 *   file: kernel object representing the open file request.
 *         file->f_path.dentry->d_name.name = filename (not full path)
 *         file->f_path.dentry->d_inode     = inode of the file
 *
 * Return:
 *   0     = allow the operation to proceed
 *   -EPERM = deny with "Operation not permitted"
 *   -EACCES = deny with "Permission denied"
 *
 * IMPORTANT: This hook is called in every file open in the entire system.
 * Keep it FAST. No sleeping, no blocking I/O. printk is acceptable here
 * because it is designed to be async and non-blocking.
 */
static int guardian_file_open(struct file *file)
{
    const struct cred *cred;   /* process credentials (uid, capabilities) */
    uid_t uid;
    const char *filename;

    /* If enforcement is disabled, allow everything */
    if (!atomic_read(&guardian_enabled))
        return 0;

    /*
     * rcu_read_lock / rcu_read_unlock:
     * Credentials can be updated by other kernel code concurrently.
     * RCU (Read-Copy-Update) is the kernel's preferred lock-free mechanism.
     * Between lock/unlock we can safely read cred without it being freed.
     */
    rcu_read_lock();
    cred = current_cred();      /* credentials of the calling process     */
    uid  = from_kuid(&init_user_ns, cred->uid);  /* convert kuid_t to uid_t */
    rcu_read_unlock();

    filename = file->f_path.dentry->d_name.name;

    /* Audit log: KERN_INFO = log level 6, appears in dmesg */
    pr_info("guardian: file_open pid=%d uid=%u file=%s\n",
            current->pid, uid, filename);

    return 0;  /* allow all opens — we only audit here */
}

/*
 * guardian_inode_create — called before a new file/directory inode is created.
 *
 * Parameters:
 *   mnt_userns: user namespace of the mount (needed for uid translation)
 *   dir:        inode of the parent directory where creation is requested
 *   dentry:     proposed dentry (name + location) for the new file
 *   mode:       file permission bits (0644, 0755, etc.)
 *
 * Security policy enforced here:
 *   Non-root processes cannot create files inside /tmp.
 *   Root = CAP_DAC_OVERRIDE capability.
 *
 * What is a dentry? A "directory entry" — a kernel object mapping a filename
 * to an inode. The dentry tree mirrors the filesystem tree in memory.
 */
static int guardian_inode_create(struct mnt_idmap *idmap,
                                  struct inode *dir,
                                  struct dentry *dentry,
                                  umode_t mode)
{
    char *path_buf;
    char *full_path;
    int ret = 0;

    if (!atomic_read(&guardian_enabled))
        return 0;

    /*
     * capable(CAP_DAC_OVERRIDE):
     * Returns true if the current process has CAP_DAC_OVERRIDE, which
     * traditionally means "can override file read/write/execute checks".
     * Root has this by default; other processes can be granted it via
     * file capabilities (setcap).
     */
    if (capable(CAP_DAC_OVERRIDE))
        return 0;  /* root or privileged process — allow */

    /*
     * Build the full path of the parent directory.
     * d_path() walks the dentry tree upward building a full path string.
     * We allocate a PAGE_SIZE buffer (typically 4096 bytes) from the kernel
     * heap using GFP_KERNEL (may sleep, normal allocation).
     */
    path_buf = kmalloc(PATH_MAX, GFP_KERNEL);
    if (!path_buf)
        return -ENOMEM;  /* Out of memory — fail gracefully */

    /*
     * dentry_path_raw: fills path_buf with the path of `dentry->d_parent`
     * (the directory), returns a pointer into path_buf where the string
     * starts (the buffer is filled from the END, so the returned pointer
     * is somewhere in the middle of path_buf).
     */
    full_path = dentry_path_raw(dentry->d_parent, path_buf, PATH_MAX);
    if (IS_ERR(full_path)) {
        /* IS_ERR() checks if a pointer encodes an error code.
         * Kernel functions often return ERR_PTR(-ENOMEM) instead of NULL. */
        kfree(path_buf);
        return PTR_ERR(full_path);
    }

    /* Check if the parent directory path starts with /tmp */
    if (strncmp(full_path, BLOCKED_PATH_PREFIX, BLOCKED_PATH_LEN) == 0) {
        pr_warn("guardian: BLOCKED inode_create in %s by pid=%d uid=%u file=%s\n",
                full_path,
                current->pid,
                from_kuid(&init_user_ns, current_cred()->uid),
                dentry->d_name.name);
        ret = -EPERM;  /* deny */
    }

    kfree(path_buf);  /* always free what you kmalloc — kernel has no GC */
    return ret;
}

/*
 * guardian_task_fix_setuid — called when a process changes its UID.
 *
 * This covers: setuid(), setreuid(), seteuid(), setresuid().
 * A common privilege escalation vector: a process drops to a low UID
 * to appear safe, then re-elevates. This hook lets us audit every such event.
 *
 * Parameters:
 *   new:  the NEW credentials being applied (where we're going)
 *   old:  the CURRENT credentials (where we are now)
 *   flags: which credential fields changed (LSM_SETID_ID, etc.)
 */
static int guardian_task_fix_setuid(struct cred *new,
                                     const struct cred *old,
                                     int flags)
{
    uid_t old_uid = from_kuid(&init_user_ns, old->uid);
    uid_t new_uid = from_kuid(&init_user_ns, new->uid);

    if (!atomic_read(&guardian_enabled))
        return 0;

    /* Only log if UID is actually changing */
    if (old_uid != new_uid) {
        pr_info("guardian: setuid pid=%d name=%s  uid %u -> %u\n",
                current->pid,
                current->comm,  /* process name, max 16 chars */
                old_uid, new_uid);

        /* Policy: if a non-root process tries to setuid(0) = gain root */
        if (new_uid == 0 && old_uid != 0) {
            pr_warn("guardian: SUSPICIOUS setuid to root by pid=%d (%s)\n",
                    current->pid, current->comm);
            /* NOTE: We log but do not block here.
             * To block, return -EPERM. Blocking setuid(0) would break su/sudo.
             * A real deployment would check capabilities or policy before blocking.
             */
        }
    }

    return 0;
}

/* =========================================================================
 * SECURITYFS INTERFACE
 * =========================================================================
 * securityfs is a special virtual filesystem mounted at
 * /sys/kernel/security/. It lets LSMs expose control files to userspace.
 * Think of it as procfs but specifically for security modules.
 */

static ssize_t guardian_enabled_read(struct file *file,
                                      char __user *buf,
                                      size_t count,
                                      loff_t *ppos)
{
    char tmp[4];
    int len;

    len = snprintf(tmp, sizeof(tmp), "%d\n", atomic_read(&guardian_enabled));
    /*
     * simple_read_from_buffer: copies from a kernel buffer to a userspace
     * buffer, handling the offset (*ppos) correctly for repeated reads.
     * __user annotation tells the compiler/sparse that `buf` is a userspace
     * pointer — never dereference it directly, always use copy_to_user().
     */
    return simple_read_from_buffer(buf, count, ppos, tmp, len);
}

static ssize_t guardian_enabled_write(struct file *file,
                                       const char __user *buf,
                                       size_t count,
                                       loff_t *ppos)
{
    char tmp[4];
    unsigned long val;

    if (count >= sizeof(tmp))
        return -EINVAL;

    /* copy_from_user: safely copies from userspace to kernel space.
     * Direct dereference of __user pointers can cause kernel oops. */
    if (copy_from_user(tmp, buf, count))
        return -EFAULT;

    tmp[count] = '\0';

    /* kstrtoul: kernel-safe string-to-unsigned-long.
     * Do NOT use sscanf in the kernel — it has known safety issues. */
    if (kstrtoul(tmp, 10, &val))
        return -EINVAL;

    atomic_set(&guardian_enabled, val ? 1 : 0);
    pr_info("guardian: enforcement %s by pid=%d\n",
            val ? "ENABLED" : "DISABLED", current->pid);

    return count;
}

static const struct file_operations guardian_fops = {
    .read  = guardian_enabled_read,
    .write = guardian_enabled_write,
    .llseek = default_llseek,
};

/* =========================================================================
 * LSM REGISTRATION
 * =========================================================================
 *
 * security_hook_list: each element links one of your callbacks into a
 * specific hook's list. The LSM framework walks these lists on every hook call.
 *
 * LSM_HOOK_INIT(hook_name, callback): a macro that initializes a
 * security_hook_list entry binding hook_name to your callback function.
 */
static struct security_hook_list guardian_hooks[] __ro_after_init = {
    LSM_HOOK_INIT(file_open,       guardian_file_open),
    LSM_HOOK_INIT(inode_create,    guardian_inode_create),
    LSM_HOOK_INIT(task_fix_setuid, guardian_task_fix_setuid),
};

/*
 * lsm_id: uniquely identifies this LSM to the kernel (required Linux 6.1+).
 * lsm_id.id must be registered in include/uapi/linux/lsm.h for mainline.
 * For out-of-tree modules, use LSM_ID_UNDEF.
 */
static const struct lsm_id guardian_lsm_id = {
    .name = "guardian",
    .id   = LSM_ID_UNDEF,
};

/* =========================================================================
 * MODULE INIT / EXIT
 * =========================================================================
 */

static int __init guardian_init(void)
{
    /*
     * security_add_hooks: registers your hook list with the LSM framework.
     * After this call, every matching kernel event triggers your callbacks.
     *
     * Parameters:
     *   hooks:     your security_hook_list array
     *   count:     ARRAY_SIZE() of the array (number of hooks)
     *   lsm_id:    pointer to your lsm_id struct
     */
    security_add_hooks(guardian_hooks,
                       ARRAY_SIZE(guardian_hooks),
                       &guardian_lsm_id);

    /*
     * Create /sys/kernel/security/guardian/ directory
     * and /sys/kernel/security/guardian/enabled file
     */
    guardian_dir = securityfs_create_dir("guardian", NULL);
    if (IS_ERR(guardian_dir)) {
        pr_err("guardian: failed to create securityfs dir: %ld\n",
               PTR_ERR(guardian_dir));
        return PTR_ERR(guardian_dir);
    }

    /*
     * 0644 = owner read+write, group read, others read
     * NULL = no seq_file operations needed (using custom fops instead)
     * &guardian_fops = our read/write handlers
     */
    guardian_enabled_file = securityfs_create_file("enabled", 0644,
                                                    guardian_dir,
                                                    NULL,
                                                    &guardian_fops);
    if (IS_ERR(guardian_enabled_file)) {
        securityfs_remove(guardian_dir);
        return PTR_ERR(guardian_enabled_file);
    }

    pr_info("guardian: LSM initialized. Hooks: file_open, inode_create, task_fix_setuid\n");
    pr_info("guardian: Control: echo 0 > /sys/kernel/security/guardian/enabled\n");
    return 0;
}

static void __exit guardian_exit(void)
{
    securityfs_remove(guardian_enabled_file);
    securityfs_remove(guardian_dir);
    pr_info("guardian: LSM unloaded\n");
}

/*
 * SECURITY_LSM_EARLY: marks this as an early LSM, initialized before most
 * kernel subsystems. This ensures hooks are in place before any userspace
 * process runs.
 */
DEFINE_LSM(guardian) = {
    .name    = "guardian",
    .init    = guardian_init,
    .order   = LSM_ORDER_MUTABLE,
};

module_exit(guardian_exit);
