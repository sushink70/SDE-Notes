// SPDX-License-Identifier: GPL-2.0-only
/*
 * sentinel_lsm_buggy.c — INTENTIONALLY BUGGY version for training.
 *
 * BUG #1 (Code / Memory-Safety):
 *   sentinel_file_open() calls kfree(buf) BEFORE using `path`, which is a
 *   pointer INTO buf.  After kfree, `path` is a dangling pointer → UAF.
 *   Grep marker: BUG1_UAF
 *
 * BUG #2 (Logic / Security):
 *   is_rfc1918() inverts the 172.16/12 bitmask comparison — it admits a
 *   superset of addresses (172.0.0.0/8) instead of 172.16.0.0/12, letting
 *   traffic to 172.0–172.15 and 172.32–172.255 bypass the firewall rule.
 *   Grep marker: BUG2_LOGIC
 *
 * How to spot them:
 *   - BUG1: KASAN will report "use-after-free on address ..." in file_open.
 *           Also visible under kmemleak and valgrind (in UML builds).
 *   - BUG2: Unit test sentinel_test_rfc1918() fails on 172.15.0.1 and
 *           172.32.0.1 (both blocked when they should not be in fixed ver).
 *
 * DO NOT merge this file.  It exists solely as a diff/exercise target.
 */

#include <linux/lsm_hooks.h>
#include <linux/security.h>
#include <linux/fs.h>
#include <linux/binfmts.h>
#include <linux/net.h>
#include <linux/socket.h>
#include <linux/in.h>
#include <linux/slab.h>
#include <linux/spinlock.h>
#include <linux/seq_file.h>
#include <linux/proc_fs.h>
#include <linux/module.h>
#include <linux/cred.h>
#include <linux/uidgid.h>
#include <linux/atomic.h>
#include <linux/string.h>

#define SENTINEL_VERSION     "0.2.0-buggy"
#define SENTINEL_MAX_RULES   64
#define SENTINEL_PATH_MAX    256
#define SENTINEL_LSM_NAME    "sentinel"

struct sentinel_rule {
	char   path_prefix[SENTINEL_PATH_MAX];
	kuid_t deny_uid;
	bool   active;
};

static struct sentinel_rule sentinel_rules[SENTINEL_MAX_RULES];
static int                   sentinel_rule_count;
static DEFINE_SPINLOCK(sentinel_lock);
static atomic64_t cnt_file_deny   = ATOMIC64_INIT(0);
static atomic64_t cnt_exec_deny   = ATOMIC64_INIT(0);
static atomic64_t cnt_net_deny    = ATOMIC64_INIT(0);

/* =========================================================================
 * BUG #1: Use-After-Free in sentinel_file_open
 *
 * WHAT HAPPENS:
 *   d_path() returns a pointer INTO the buffer `buf`.
 *   kfree(buf) is called before `path` is used in the strncmp loop.
 *   The kernel slab allocator may immediately reuse that memory.
 *   Any subsequent read of `path` accesses freed memory.
 *
 * FIX (see sentinel_lsm.c — correct version):
 *   Move kfree(buf) to AFTER the spin_lock / comparison block.
 *   i.e. call kfree only once, at the very end of the function.
 *
 * KASAN output you will see:
 *   BUG: KASAN: use-after-free in sentinel_file_open+0x...
 *   Read of size 1 at addr ffff... by task <comm>/pid
 *
 * HOW TO TRIGGER:
 *   echo "open /etc/shadow" > /proc/sentinel_trigger  (or just: cat /etc/shadow)
 * =========================================================================*/
static int sentinel_file_open(struct file *file) /* BUG1_UAF */
{
	const struct cred *cred;
	char              *buf;
	const char        *path;
	int                i, ret = 0;

	buf = kzalloc(SENTINEL_PATH_MAX, GFP_ATOMIC);
	if (unlikely(!buf))
		return 0;

	path = d_path(&file->f_path, buf, SENTINEL_PATH_MAX);
	if (IS_ERR(path)) {
		kfree(buf);
		return 0;
	}

	/*
	 * ❌ BUG1: kfree(buf) called here — path now dangles into freed memory.
	 *    The correct location is AFTER the loop below.
	 */
	kfree(buf);          /* <— BUG1_UAF: dangling pointer from here on */

	cred = current_cred();

	spin_lock(&sentinel_lock);
	for (i = 0; i < sentinel_rule_count; i++) {
		const struct sentinel_rule *r = &sentinel_rules[i];

		if (!r->active)
			continue;
		/*
		 * strncmp reads from `path` which points into freed `buf`.
		 * KASAN will catch this on first dereference.
		 */
		if (strncmp(path, r->path_prefix, strlen(r->path_prefix)) != 0)
			continue;

		if (uid_valid(r->deny_uid) && !uid_eq(r->deny_uid, cred->uid))
			continue;

		atomic64_inc(&cnt_file_deny);
		ret = -EACCES;
		break;
	}
	spin_unlock(&sentinel_lock);

	return ret;
}

static int sentinel_bprm_check_security(struct linux_binprm *bprm)
{
	const struct cred *cred = current_cred();

	if (!bprm->file)
		return 0;

	if (IS_SUID(file_inode(bprm->file)) &&
	    !uid_eq(cred->uid, GLOBAL_ROOT_UID)) {
		atomic64_inc(&cnt_exec_deny);
		return -EPERM;
	}
	return 0;
}

/* =========================================================================
 * BUG #2: Logic error in RFC-1918 detection
 *
 * WHAT HAPPENS:
 *   The 172.16.0.0/12 range should test:
 *       (ip >> 20) == 0xAC1   i.e. top 12 bits equal to 172.16
 *
 *   The buggy code tests:
 *       (ip >> 24) == 172     i.e. top 8 bits (entire 172.0.0.0/8)
 *
 *   Effect:  172.0.x.x – 172.15.x.x  → wrongly BLOCKED (172.0 not RFC-1918)
 *            172.32.x.x– 172.255.x.x → wrongly BLOCKED (not RFC-1918)
 *            172.16.x.x– 172.31.x.x  → correctly blocked
 *
 *   Security impact: denial-of-service (false positives) for traffic to
 *   publicly-routable 172.x/8 addresses, and the boundary is wrong.
 *
 * FIX:
 *   Replace the 172 arm with:
 *       ((ip >> 20) == (0xAC10 >> 4))   →  (ip >> 20) == 0xAC1
 *   (shift 32-20=12 positions to isolate the top 12 bits, compare to
 *    0b1010_1100_0001 = 0xAC1)
 *
 * UNIT TEST to catch it:
 *   KUNIT_EXPECT_FALSE(test, is_rfc1918(htonl(0xAC0F0001))); // 172.15.0.1
 *   KUNIT_EXPECT_TRUE (test, is_rfc1918(htonl(0xAC100001))); // 172.16.0.1
 *   KUNIT_EXPECT_FALSE(test, is_rfc1918(htonl(0xAC200001))); // 172.32.0.1
 * =========================================================================*/
static bool is_rfc1918(__be32 ip_be) /* BUG2_LOGIC */
{
	u32 ip = ntohl(ip_be);

	return ((ip >> 24) == 10)             ||   /* 10.0.0.0/8   — CORRECT  */
	       ((ip >> 24) == 172)            ||   /* ❌ BUG2: should be /12 check */
	       ((ip >> 16) == 0xC0A8);             /* 192.168.0.0/16— CORRECT  */
}

static int sentinel_socket_connect(struct socket *sock,
				    struct sockaddr *address, int addrlen)
{
	const struct cred  *cred;
	struct sockaddr_in *addr4;

	if (address->sa_family != AF_INET)
		return 0;

	if ((size_t)addrlen < sizeof(*addr4))
		return -EINVAL;

	addr4 = (struct sockaddr_in *)address;

	if (!is_rfc1918(addr4->sin_addr.s_addr))
		return 0;

	cred = current_cred();
	if (uid_eq(cred->uid, GLOBAL_ROOT_UID))
		return 0;

	atomic64_inc(&cnt_net_deny);
	return -ECONNREFUSED;
}

static struct security_hook_list sentinel_hooks[] __lsm_ro_after_init = {
	LSM_HOOK_INIT(file_open,            sentinel_file_open),
	LSM_HOOK_INIT(bprm_check_security,  sentinel_bprm_check_security),
	LSM_HOOK_INIT(socket_connect,       sentinel_socket_connect),
};

static int sentinel_proc_show(struct seq_file *m, void *v)
{
	seq_printf(m, "sentinel-buggy v%s\n", SENTINEL_VERSION);
	seq_printf(m, "deny_file: %lld\n", atomic64_read(&cnt_file_deny));
	seq_printf(m, "deny_exec: %lld\n", atomic64_read(&cnt_exec_deny));
	seq_printf(m, "deny_net:  %lld\n", atomic64_read(&cnt_net_deny));
	return 0;
}

static int sentinel_proc_open(struct inode *inode, struct file *file)
{
	return single_open(file, sentinel_proc_show, NULL);
}

static const struct proc_ops sentinel_proc_ops = {
	.proc_open    = sentinel_proc_open,
	.proc_read    = seq_read,
	.proc_lseek   = seq_lseek,
	.proc_release = single_release,
};

static int __init sentinel_init(void)
{
	spin_lock(&sentinel_lock);
	strscpy(sentinel_rules[0].path_prefix, "/etc/shadow",
		sizeof(sentinel_rules[0].path_prefix));
	sentinel_rules[0].deny_uid = INVALID_UID;
	sentinel_rules[0].active   = true;
	sentinel_rule_count = 1;
	spin_unlock(&sentinel_lock);

	security_add_hooks(sentinel_hooks, ARRAY_SIZE(sentinel_hooks),
			   SENTINEL_LSM_NAME);
	proc_create(SENTINEL_LSM_NAME, 0444, NULL, &sentinel_proc_ops);

	pr_info("sentinel-buggy: LSM initialised — DO NOT USE IN PRODUCTION\n");
	return 0;
}

DEFINE_LSM(sentinel) = {
	.name  = SENTINEL_LSM_NAME,
	.init  = sentinel_init,
};
