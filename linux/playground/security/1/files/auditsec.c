// SPDX-License-Identifier: GPL-2.0-only
/*
 * auditsec — a teaching LSM that logs file opens, exec, socket creation,
 * inode permission checks, and task signals.
 *
 * Kernel source refs:
 *   include/linux/lsm_hooks.h        — struct security_hook_list
 *   include/linux/security.h         — LSM API declarations
 *   security/security.c              — call_int_hook(), lsm_add_hooks()
 *   security/Kconfig                 — LSM ordering config
 *   Documentation/security/lsm.rst  — official LSM developer guide
 *
 * Two intentional bugs are embedded and clearly marked:
 *   BUG-1 (code bug)  : missing NULL-check before dentry_path_raw()
 *   BUG-2 (logic bug) : inverted deny logic — allows when should deny
 *
 * Build against kernel tree:
 *   make -C /lib/modules/$(uname -r)/build M=$(pwd) modules
 *
 * Author: auditsec-demo  <kernel-dev@example.org>
 * Tested: v6.8+ (lsm_id added in v6.7; BPF LSM stable since v5.7)
 */

#define pr_fmt(fmt) KBUILD_MODNAME ": " fmt

#include <linux/init.h>
#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/security.h>        /* security_hook_list, lsm_add_hooks   */
#include <linux/lsm_hooks.h>       /* LSM_HOOK_INIT macro                  */
#include <linux/fs.h>              /* struct file, struct inode            */
#include <linux/binfmts.h>         /* struct linux_binprm                  */
#include <linux/net.h>             /* struct socket                        */
#include <linux/sched.h>           /* current, task_struct                 */
#include <linux/cred.h>            /* current_uid(), uid_t                 */
#include <linux/uaccess.h>
#include <linux/dcache.h>          /* dentry_path_raw()                    */
#include <linux/spinlock.h>
#include <linux/atomic.h>
#include <linux/sysfs.h>
#include <linux/kobject.h>

MODULE_LICENSE("GPL v2");
MODULE_AUTHOR("auditsec-demo");
MODULE_DESCRIPTION("Audit-logging LSM for kernel development study");
MODULE_VERSION("0.1");

/* -------------------------------------------------------------------------
 * tunables exposed via /sys/kernel/auditsec/
 * -------------------------------------------------------------------------*/
static int  auditsec_enabled   = 1;  /* 0=off, 1=log-only, 2=enforce      */
static int  denied_uid         = -1; /* deny exec for this uid (-1=off)    */
static atomic_long_t stat_file_opens  = ATOMIC_LONG_INIT(0);
static atomic_long_t stat_exec_checks = ATOMIC_LONG_INIT(0);
static atomic_long_t stat_sock_create = ATOMIC_LONG_INIT(0);
static atomic_long_t stat_denied      = ATOMIC_LONG_INIT(0);

/* sysfs kobject — /sys/kernel/auditsec/ */
static struct kobject *auditsec_kobj;

/*
 * Helper: emit an audit record via pr_info (real LSMs use audit_log_*).
 * See: kernel/audit.c, include/linux/audit.h
 */
static void auditsec_log(const char *hook, const char *detail)
{
	if (!auditsec_enabled)
		return;
	pr_info("[%s] uid=%u pid=%d comm=%.20s :: %s\n",
		hook,
		from_kuid_munged(&init_user_ns, current_uid()),
		task_pid_nr(current),
		current->comm,
		detail);
}

/* =========================================================================
 * HOOK 1 — file_open
 *
 * Called from: fs/open.c → do_dentry_open() → security_file_open()
 * Struct:  include/linux/fs.h  struct file { struct path f_path; ... }
 *          f_path.dentry→d_name.name gives us the filename component
 *
 * BUG-1 (CODE BUG): dentry_path_raw() is called without first checking
 *   that file->f_path.dentry is non-NULL.  On certain synthetic filesystems
 *   (e.g. anon pipes, sockets obtained via socketpair(2)) the dentry can be
 *   NULL, causing a NULL-pointer dereference and kernel oops.
 *
 *   Symptom:  BUG: kernel NULL pointer dereference at 0000000000000000
 *             triggered by any process calling pipe() or socketpair().
 *
 *   FIX: add  if (!file->f_path.dentry) guard (see auditsec_fixed.c).
 * =========================================================================*/
static int auditsec_file_open(struct file *file)
{
	char buf[256];
	char *path;

	atomic_long_inc(&stat_file_opens);

	/* ---- BUG-1 START: missing NULL check ---- */
	path = dentry_path_raw(file->f_path.dentry, buf, sizeof(buf));
	/* ---- BUG-1 END                          ---- */

	if (IS_ERR(path))
		path = "<unknown>";

	auditsec_log("file_open", path);
	return 0;
}

/* =========================================================================
 * HOOK 2 — bprm_check_security
 *
 * Called from: fs/exec.c → bprm_execve() → security_bprm_check()
 * Struct:  include/linux/binfmts.h  struct linux_binprm { struct file *file; }
 *
 * Policy intent: deny exec() for the UID stored in `denied_uid` when
 *   auditsec_enabled == 2 (enforce mode).
 *
 * BUG-2 (LOGIC BUG): The comparison is inverted — the condition fires
 *   (returns -EACCES) when the UID *does NOT* match denied_uid, i.e. it
 *   denies every process EXCEPT the one that should be denied.
 *
 *   Symptom: all users except denied_uid get -EACCES on exec() calls,
 *            effectively breaking the entire system. Observed as:
 *            "bash: /bin/ls: Permission denied"  for all users != denied_uid.
 *
 *   FIX: change  != to  ==  in the uid comparison (see auditsec_fixed.c).
 * =========================================================================*/
static int auditsec_bprm_check(struct linux_binprm *bprm)
{
	uid_t uid = from_kuid_munged(&init_user_ns, current_uid());
	char buf[256];
	char *path;

	atomic_long_inc(&stat_exec_checks);

	path = dentry_path_raw(bprm->file->f_path.dentry, buf, sizeof(buf));
	if (IS_ERR(path))
		path = "<binary>";

	auditsec_log("bprm_check", path);

	if (auditsec_enabled == 2 && denied_uid >= 0) {
		/* ---- BUG-2 START: inverted logic ---- */
		if ((int)uid != denied_uid) {          /* WRONG: should be == */
		/* ---- BUG-2 END                   ---- */
			atomic_long_inc(&stat_denied);
			pr_warn("auditsec: DENY exec uid=%u path=%s\n", uid, path);
			return -EACCES;
		}
	}

	return 0;
}

/* =========================================================================
 * HOOK 3 — socket_create
 *
 * Called from: net/socket.c → __sys_socket() → security_socket_create()
 * Args: family (AF_*), type (SOCK_*), protocol, kern (kernel internal?)
 * =========================================================================*/
static int auditsec_socket_create(int family, int type, int protocol, int kern)
{
	char detail[64];

	if (kern)              /* skip kernel-internal socket creation */
		return 0;

	atomic_long_inc(&stat_sock_create);

	snprintf(detail, sizeof(detail), "family=%d type=%d proto=%d",
		 family, type, protocol);
	auditsec_log("sock_create", detail);
	return 0;
}

/* =========================================================================
 * HOOK 4 — inode_permission
 *
 * Called from: fs/namei.c → inode_permission() → security_inode_permission()
 * mask bits: MAY_READ | MAY_WRITE | MAY_EXEC  (include/linux/fs.h)
 * =========================================================================*/
static int auditsec_inode_permission(struct inode *inode, int mask)
{
	/*
	 * Only log write attempts to keep noise down.
	 * In a real LSM you would check inode->i_sb->s_id for the fs name,
	 * inode->i_ino for the inode number, etc.
	 */
	if (mask & MAY_WRITE) {
		char detail[64];
		snprintf(detail, sizeof(detail),
			 "ino=%lu mask=0x%x dev=%u:%u",
			 inode->i_ino, mask,
			 MAJOR(inode->i_sb->s_dev),
			 MINOR(inode->i_sb->s_dev));
		auditsec_log("inode_perm", detail);
	}
	return 0;
}

/* =========================================================================
 * HOOK 5 — task_kill
 *
 * Called from: kernel/signal.c → check_kill_permission()
 *              → security_task_kill()
 * =========================================================================*/
static int auditsec_task_kill(struct task_struct *p,
			      struct kernel_siginfo *info,
			      int sig, const struct cred *cred)
{
	char detail[64];
	snprintf(detail, sizeof(detail),
		 "sig=%d target_pid=%d target_comm=%.20s",
		 sig, task_pid_nr(p), p->comm);
	auditsec_log("task_kill", detail);
	return 0;
}

/* -------------------------------------------------------------------------
 * Hook table registration
 * include/linux/lsm_hooks.h : LSM_HOOK_INIT(HOOK_NAME, handler_fn)
 * security/security.c       : security_add_hooks()
 * -------------------------------------------------------------------------*/
static struct security_hook_list auditsec_hooks[] __ro_after_init = {
	LSM_HOOK_INIT(file_open,         auditsec_file_open),
	LSM_HOOK_INIT(bprm_check_security, auditsec_bprm_check),
	LSM_HOOK_INIT(socket_create,     auditsec_socket_create),
	LSM_HOOK_INIT(inode_permission,  auditsec_inode_permission),
	LSM_HOOK_INIT(task_kill,         auditsec_task_kill),
};

/* -------------------------------------------------------------------------
 * sysfs attributes under /sys/kernel/auditsec/
 * -------------------------------------------------------------------------*/
static ssize_t enabled_show(struct kobject *kobj,
			    struct kobj_attribute *attr, char *buf)
{
	return sysfs_emit(buf, "%d\n", auditsec_enabled);
}
static ssize_t enabled_store(struct kobject *kobj,
			     struct kobj_attribute *attr,
			     const char *buf, size_t count)
{
	int val;
	if (kstrtoint(buf, 10, &val) || val < 0 || val > 2)
		return -EINVAL;
	auditsec_enabled = val;
	return count;
}
static struct kobj_attribute attr_enabled =
	__ATTR(enabled, 0644, enabled_show, enabled_store);

static ssize_t denied_uid_show(struct kobject *kobj,
			       struct kobj_attribute *attr, char *buf)
{
	return sysfs_emit(buf, "%d\n", denied_uid);
}
static ssize_t denied_uid_store(struct kobject *kobj,
				struct kobj_attribute *attr,
				const char *buf, size_t count)
{
	int val;
	if (kstrtoint(buf, 10, &val))
		return -EINVAL;
	denied_uid = val;
	return count;
}
static struct kobj_attribute attr_denied_uid =
	__ATTR(denied_uid, 0644, denied_uid_show, denied_uid_store);

static ssize_t stats_show(struct kobject *kobj,
			  struct kobj_attribute *attr, char *buf)
{
	return sysfs_emit(buf,
		"file_opens:  %ld\n"
		"exec_checks: %ld\n"
		"sock_creates:%ld\n"
		"denied:      %ld\n",
		atomic_long_read(&stat_file_opens),
		atomic_long_read(&stat_exec_checks),
		atomic_long_read(&stat_sock_create),
		atomic_long_read(&stat_denied));
}
static struct kobj_attribute attr_stats =
	__ATTR(stats, 0444, stats_show, NULL);

static struct attribute *auditsec_attrs[] = {
	&attr_enabled.attr,
	&attr_denied_uid.attr,
	&attr_stats.attr,
	NULL,
};
static const struct attribute_group auditsec_attr_group = {
	.attrs = auditsec_attrs,
};

/* -------------------------------------------------------------------------
 * LSM ID — required since v6.7 (commit a04a1985)
 * include/linux/lsm_hooks.h : struct lsm_id
 * -------------------------------------------------------------------------*/
static const struct lsm_id auditsec_lsmid = {
	.name = "auditsec",
	.id   = LSM_ID_UNDEF,     /* use UNDEF for out-of-tree LSMs           */
};

/* -------------------------------------------------------------------------
 * Module init / exit
 * -------------------------------------------------------------------------*/
static int __init auditsec_init(void)
{
	int ret;

	pr_info("auditsec LSM initialising (enabled=%d)\n", auditsec_enabled);

	/* Register sysfs node */
	auditsec_kobj = kobject_create_and_add("auditsec", kernel_kobj);
	if (!auditsec_kobj)
		return -ENOMEM;

	ret = sysfs_create_group(auditsec_kobj, &auditsec_attr_group);
	if (ret) {
		kobject_put(auditsec_kobj);
		return ret;
	}

	/*
	 * security_add_hooks() — registers our hook list.
	 * In-tree LSMs call this from their _init function, which is invoked
	 * by do_security_initcalls() before any process runs.
	 *
	 * Out-of-tree modules calling this from module_init() are supported
	 * on kernels built with CONFIG_SECURITY_LOADABLE (non-upstream feature)
	 * or via CONFIG_BPF_LSM for the BPF pathway.
	 *
	 * Reference: security/security.c
	 */
	security_add_hooks(auditsec_hooks, ARRAY_SIZE(auditsec_hooks),
			   &auditsec_lsmid);

	pr_info("auditsec: %zu hooks registered\n", ARRAY_SIZE(auditsec_hooks));
	return 0;
}

static void __exit auditsec_exit(void)
{
	/*
	 * NOTE: security_add_hooks() does NOT provide a removal API.
	 * Hook removal after registration is intentionally unsupported upstream
	 * because stale hook pointers create race conditions.
	 * This module is intended to be loaded once per boot, not reloaded.
	 *
	 * See: Documentation/security/lsm.rst §"LSM hooks and removal"
	 */
	sysfs_remove_group(auditsec_kobj, &auditsec_attr_group);
	kobject_put(auditsec_kobj);
	pr_info("auditsec: unloaded (hooks remain registered — reboot to clear)\n");
}

module_init(auditsec_init);
module_exit(auditsec_exit);
