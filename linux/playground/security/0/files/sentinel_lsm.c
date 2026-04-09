// SPDX-License-Identifier: GPL-2.0-only
/*
 * sentinel_lsm.c — Sentinel Linux Security Module
 *
 * Demonstrates a stacked LSM with three hook points:
 *   - file_open:             path-prefix deny-list (per-UID or global)
 *   - bprm_check_security:  deny setuid-exec by non-root
 *   - socket_connect:       block outbound to RFC-1918 ranges by non-root
 *
 * Architecture constraints:
 *   - MUST be compiled IN-TREE (DEFINE_LSM cannot be a loadable .ko).
 *   - Stacks on top of SELinux/AppArmor; does not replace them.
 *   - All policy state protected by a single spinlock (replace with
 *     RCU-list for production scale).
 *
 * Build path:  security/sentinel/sentinel_lsm.c
 * Kconfig:     CONFIG_SECURITY_SENTINEL
 *
 * References:
 *   Documentation/security/lsm.rst
 *   Documentation/security/lsm-development.rst
 *   include/linux/lsm_hooks.h
 *   security/security.c
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

#define SENTINEL_VERSION     "0.2.0"
#define SENTINEL_MAX_RULES   64
#define SENTINEL_PATH_MAX    256
#define SENTINEL_LSM_NAME    "sentinel"

/*
 * Policy rule.  uid == KUIDT_INIT(UINT_MAX) means "any UID".
 * All accesses serialised through sentinel_lock.
 */
struct sentinel_rule {
	char   path_prefix[SENTINEL_PATH_MAX];
	kuid_t deny_uid;        /* INVALID_UID ⟹ deny everyone */
	bool   active;
};

static struct sentinel_rule sentinel_rules[SENTINEL_MAX_RULES];
static int                   sentinel_rule_count;
static DEFINE_SPINLOCK(sentinel_lock);

/* Monotonic counters — never reset, never overflow-checked intentionally
 * (wraps around on 64-bit arch after ~18 × 10^18 events — acceptable). */
static atomic64_t cnt_file_deny   = ATOMIC64_INIT(0);
static atomic64_t cnt_exec_deny   = ATOMIC64_INIT(0);
static atomic64_t cnt_net_deny    = ATOMIC64_INIT(0);

/* =========================================================================
 * Helper: resolve file path into caller-supplied buffer.
 * Returns pointer into buf, or ERR_PTR on failure.
 * =========================================================================*/
static const char *sentinel_resolve_path(struct file *file,
					  char *buf, int bufsz)
{
	return d_path(&file->f_path, buf, bufsz);
}

/* =========================================================================
 * Hook 1: file_open
 *
 * Called on every VFS open.  Walk the deny-list; if prefix matches AND the
 * deny_uid is INVALID_UID (any) or equals current UID, return -EACCES.
 *
 * Performance notes:
 *   - kzalloc with GFP_ATOMIC (we may be in interrupt context).
 *   - Fail-open on allocation failure (log the anomaly; don't brick the
 *     system). Production: pre-allocate a per-CPU buffer.
 * =========================================================================*/
static int sentinel_file_open(struct file *file)
{
	const struct cred *cred;
	char              *buf;
	const char        *path;
	int                i, ret = 0;

	buf = kzalloc(SENTINEL_PATH_MAX, GFP_ATOMIC);
	if (unlikely(!buf)) {
		pr_warn_ratelimited("sentinel: kzalloc failed in file_open — fail-open\n");
		return 0;
	}

	path = sentinel_resolve_path(file, buf, SENTINEL_PATH_MAX);
	if (IS_ERR(path)) {
		/* e.g. path too long; conservative fail-open */
		kfree(buf);
		return 0;
	}

	cred = current_cred();

	spin_lock(&sentinel_lock);
	for (i = 0; i < sentinel_rule_count; i++) {
		const struct sentinel_rule *r = &sentinel_rules[i];

		if (!r->active)
			continue;

		if (strncmp(path, r->path_prefix, strlen(r->path_prefix)) != 0)
			continue;

		if (uid_valid(r->deny_uid) && !uid_eq(r->deny_uid, cred->uid))
			continue;   /* rule targets a different UID */

		/* Match — deny */
		atomic64_inc(&cnt_file_deny);
		pr_warn_ratelimited(
			"sentinel: DENY file_open comm=%s pid=%d uid=%u path=%s\n",
			current->comm, current->pid,
			from_kuid(&init_user_ns, cred->uid), path);
		ret = -EACCES;
		break;
	}
	spin_unlock(&sentinel_lock);

	kfree(buf);
	return ret;
}

/* =========================================================================
 * Hook 2: bprm_check_security
 *
 * Deny execution of setuid/setgid binaries by non-root.
 * In a hardened deployment this would consult a signed binary policy.
 * =========================================================================*/
static int sentinel_bprm_check_security(struct linux_binprm *bprm)
{
	const struct cred *cred = current_cred();

	if (!bprm->file)
		return 0;

	if (IS_SUID(file_inode(bprm->file)) &&
	    !uid_eq(cred->uid, GLOBAL_ROOT_UID)) {
		atomic64_inc(&cnt_exec_deny);
		pr_warn_ratelimited(
			"sentinel: DENY setuid-exec comm=%s pid=%d uid=%u file=%s\n",
			current->comm, current->pid,
			from_kuid(&init_user_ns, cred->uid),
			bprm->filename);
		return -EPERM;
	}
	return 0;
}

/* =========================================================================
 * Hook 3: socket_connect
 *
 * Block outbound TCP/UDP to RFC-1918 ranges (10/8, 172.16/12, 192.168/16)
 * for non-root processes.  IPv4 only for brevity; extend to IPv6 for prod.
 * =========================================================================*/
static bool is_rfc1918(__be32 ip_be)
{
	u32 ip = ntohl(ip_be);

	return ((ip >> 24) == 10)                     ||   /* 10.0.0.0/8     */
	       ((ip >> 20) == (0xAC10 >> 4))           ||   /* 172.16.0.0/12  */
	       ((ip >> 16) == 0xC0A8);                       /* 192.168.0.0/16 */
}

static int sentinel_socket_connect(struct socket *sock,
				    struct sockaddr *address, int addrlen)
{
	const struct cred   *cred;
	struct sockaddr_in  *addr4;

	if (address->sa_family != AF_INET)
		return 0;

	if ((size_t)addrlen < sizeof(*addr4))
		return -EINVAL;

	addr4 = (struct sockaddr_in *)address;

	if (!is_rfc1918(addr4->sin_addr.s_addr))
		return 0;

	cred = current_cred();
	if (uid_eq(cred->uid, GLOBAL_ROOT_UID))
		return 0;   /* root may connect anywhere */

	atomic64_inc(&cnt_net_deny);
	pr_warn_ratelimited(
		"sentinel: DENY socket_connect comm=%s pid=%d uid=%u dst=%pI4:%u\n",
		current->comm, current->pid,
		from_kuid(&init_user_ns, cred->uid),
		&addr4->sin_addr.s_addr,
		ntohs(addr4->sin_port));
	return -ECONNREFUSED;
}

/* =========================================================================
 * LSM hook table — __lsm_ro_after_init places it in read-only memory after
 * init, preventing post-boot hook tampering (KASLR + WX protections apply).
 * =========================================================================*/
static struct security_hook_list sentinel_hooks[] __lsm_ro_after_init = {
	LSM_HOOK_INIT(file_open,            sentinel_file_open),
	LSM_HOOK_INIT(bprm_check_security,  sentinel_bprm_check_security),
	LSM_HOOK_INIT(socket_connect,       sentinel_socket_connect),
};

/* =========================================================================
 * /proc/sentinel — runtime stats + rule dump
 * Write interface omitted for brevity; production would use securityfs.
 * =========================================================================*/
static int sentinel_proc_show(struct seq_file *m, void *v)
{
	int i;

	seq_printf(m, "sentinel v%s\n", SENTINEL_VERSION);
	seq_printf(m, "deny_file:   %lld\n", atomic64_read(&cnt_file_deny));
	seq_printf(m, "deny_exec:   %lld\n", atomic64_read(&cnt_exec_deny));
	seq_printf(m, "deny_net:    %lld\n", atomic64_read(&cnt_net_deny));
	seq_puts(m,   "rules:\n");

	spin_lock(&sentinel_lock);
	for (i = 0; i < sentinel_rule_count; i++) {
		const struct sentinel_rule *r = &sentinel_rules[i];

		if (!r->active)
			continue;
		seq_printf(m, "  [%2d] prefix=%-40s uid=%s\n",
			   i, r->path_prefix,
			   uid_valid(r->deny_uid) ? "specific" : "any");
	}
	spin_unlock(&sentinel_lock);
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

/* =========================================================================
 * DEFINE_LSM — must be in-tree.  Runs during early boot (before SMP).
 * =========================================================================*/
static int __init sentinel_init(void)
{
	/* Seed a default rule: block /etc/shadow for all UIDs */
	spin_lock(&sentinel_lock);
	strscpy(sentinel_rules[0].path_prefix, "/etc/shadow",
		sizeof(sentinel_rules[0].path_prefix));
	sentinel_rules[0].deny_uid = INVALID_UID;   /* any UID */
	sentinel_rules[0].active   = true;
	sentinel_rule_count = 1;
	spin_unlock(&sentinel_lock);

	security_add_hooks(sentinel_hooks, ARRAY_SIZE(sentinel_hooks),
			   SENTINEL_LSM_NAME);

	proc_create(SENTINEL_LSM_NAME, 0444, NULL, &sentinel_proc_ops);

	pr_info("sentinel: LSM initialised (version %s, hooks=%zu)\n",
		SENTINEL_VERSION, ARRAY_SIZE(sentinel_hooks));
	return 0;
}

DEFINE_LSM(sentinel) = {
	.name  = SENTINEL_LSM_NAME,
	.init  = sentinel_init,
};
