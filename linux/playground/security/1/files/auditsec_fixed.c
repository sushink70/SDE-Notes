// SPDX-License-Identifier: GPL-2.0-only
/*
 * auditsec_fixed.c — bug-free version with annotated fixes
 *
 * Changes from auditsec.c:
 *   FIX-1: NULL-check dentry before calling dentry_path_raw()
 *   FIX-2: Corrected uid comparison from != to ==
 */

#define pr_fmt(fmt) KBUILD_MODNAME ": " fmt

#include <linux/init.h>
#include <linux/module.h>
#include <linux/security.h>
#include <linux/lsm_hooks.h>
#include <linux/fs.h>
#include <linux/binfmts.h>
#include <linux/net.h>
#include <linux/sched.h>
#include <linux/cred.h>
#include <linux/dcache.h>
#include <linux/atomic.h>
#include <linux/sysfs.h>
#include <linux/kobject.h>

MODULE_LICENSE("GPL v2");
MODULE_DESCRIPTION("auditsec LSM — bug-fixed reference version");

static int  auditsec_enabled = 1;
static int  denied_uid       = -1;
static atomic_long_t stat_denied = ATOMIC_LONG_INIT(0);

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
 * FIX-1: NULL-safe file_open hook
 *
 * Root cause analysis:
 *   dentry_path_raw(dentry, buf, buflen) calls dentry->d_op->d_dname()
 *   if set, then walks d_parent chain. When dentry == NULL (anon inodes,
 *   pipes, sockets from socketpair) the very first dereference faults.
 *
 *   Crash trace (without fix):
 *     BUG: kernel NULL pointer dereference, address: 0000000000000048
 *     RIP: 0010:dentry_path_raw+0x18/0x90
 *     Call Trace:
 *       auditsec_file_open+0x3c/0x80 [auditsec]
 *       security_file_open+0x2d/0x50
 *       do_dentry_open+0x1a3/0x3d0
 *       ...
 *
 *   Fix: guard with   if (!file->f_path.dentry)
 *
 * See also: fs/anon_inodes.c, fs/pipe.c — neither sets a real dentry path.
 * =========================================================================*/
static int auditsec_file_open(struct file *file)
{
	char buf[256];
	char *path;

	/* FIX-1: NULL guard — absent in buggy version */
	if (!file->f_path.dentry) {
		auditsec_log("file_open", "<anon/pipe/socket>");
		return 0;
	}

	path = dentry_path_raw(file->f_path.dentry, buf, sizeof(buf));
	if (IS_ERR(path))
		path = "<unknown>";

	auditsec_log("file_open", path);
	return 0;
}

/* =========================================================================
 * FIX-2: Corrected uid comparison (== instead of !=)
 *
 * Root cause analysis:
 *   The inverted != meant: deny every uid that is NOT denied_uid.
 *   In practice, setting denied_uid=1000 caused ALL other processes
 *   (root, daemons, other users) to get -EACCES on exec, but uid 1000
 *   could exec freely — the exact opposite of the policy intent.
 *
 *   Reproduction (with buggy module, denied_uid=1000):
 *     $ sudo -u root ls       → Permission denied   ← wrong: root denied
 *     $ sudo -u user1000 ls   → works fine          ← wrong: target allowed
 *
 *   Fix: change  uid != denied_uid  →  uid == denied_uid
 * =========================================================================*/
static int auditsec_bprm_check(struct linux_binprm *bprm)
{
	uid_t uid = from_kuid_munged(&init_user_ns, current_uid());
	char buf[256];
	char *path;

	if (!bprm->file->f_path.dentry) {
		auditsec_log("bprm_check", "<anon>");
		return 0;
	}

	path = dentry_path_raw(bprm->file->f_path.dentry, buf, sizeof(buf));
	if (IS_ERR(path))
		path = "<binary>";

	auditsec_log("bprm_check", path);

	if (auditsec_enabled == 2 && denied_uid >= 0) {
		/* FIX-2: == instead of != */
		if ((int)uid == denied_uid) {
			atomic_long_inc(&stat_denied);
			pr_warn("auditsec: DENY exec uid=%u path=%s\n", uid, path);
			return -EACCES;
		}
	}

	return 0;
}

static int auditsec_socket_create(int family, int type, int protocol, int kern)
{
	char detail[64];
	if (kern)
		return 0;
	snprintf(detail, sizeof(detail), "family=%d type=%d proto=%d",
		 family, type, protocol);
	auditsec_log("sock_create", detail);
	return 0;
}

static int auditsec_inode_permission(struct inode *inode, int mask)
{
	if (mask & MAY_WRITE) {
		char detail[64];
		snprintf(detail, sizeof(detail), "ino=%lu mask=0x%x",
			 inode->i_ino, mask);
		auditsec_log("inode_perm", detail);
	}
	return 0;
}

static int auditsec_task_kill(struct task_struct *p,
			      struct kernel_siginfo *info,
			      int sig, const struct cred *cred)
{
	char detail[64];
	snprintf(detail, sizeof(detail), "sig=%d target_pid=%d",
		 sig, task_pid_nr(p));
	auditsec_log("task_kill", detail);
	return 0;
}

static struct security_hook_list auditsec_hooks[] __ro_after_init = {
	LSM_HOOK_INIT(file_open,           auditsec_file_open),
	LSM_HOOK_INIT(bprm_check_security, auditsec_bprm_check),
	LSM_HOOK_INIT(socket_create,       auditsec_socket_create),
	LSM_HOOK_INIT(inode_permission,    auditsec_inode_permission),
	LSM_HOOK_INIT(task_kill,           auditsec_task_kill),
};

static const struct lsm_id auditsec_lsmid = {
	.name = "auditsec",
	.id   = LSM_ID_UNDEF,
};

static int __init auditsec_fixed_init(void)
{
	security_add_hooks(auditsec_hooks, ARRAY_SIZE(auditsec_hooks),
			   &auditsec_lsmid);
	pr_info("auditsec (fixed) loaded\n");
	return 0;
}
static void __exit auditsec_fixed_exit(void) {}

module_init(auditsec_fixed_init);
module_exit(auditsec_fixed_exit);
