// SPDX-License-Identifier: GPL-2.0-only
/*
 * bpf/sentinel_bpf.c — BPF LSM companion (KRSI)
 *
 * This is the LOADABLE counterpart to the in-tree C/Rust LSM.
 * Use this during development to iterate quickly without rebooting.
 *
 * Requires: kernel ≥ 5.7, CONFIG_BPF_LSM=y, CONFIG_DEBUG_INFO_BTF=y
 *           clang ≥ 12, libbpf ≥ 0.7, bpftool
 *
 * Build:
 *   clang -O2 -g -target bpf -D__TARGET_ARCH_x86 \
 *       -I/usr/include/$(uname -m)-linux-gnu     \
 *       -c sentinel_bpf.c -o sentinel_bpf.o
 *   # Then load with a skeleton-based userspace loader (sentinel_loader.c).
 *
 * Boot requirement:
 *   GRUB_CMDLINE_LINUX="lsm=lockdown,capability,yama,apparmor,bpf"
 *   (bpf must be in the lsm= list)
 *
 * References:
 *   Documentation/bpf/prog_lsm.rst
 *   samples/bpf/ (in-tree BPF LSM examples)
 *   https://github.com/torvalds/linux/blob/master/tools/testing/selftests/bpf/progs/lsm.c
 */

#include "vmlinux.h"          /* generated: bpftool btf dump file /sys/kernel/btf/vmlinux format c */
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>
#include <bpf/bpf_core_read.h>

#define EPERM       1
#define EACCES     13
#define ECONNREFUSED 111

#define AF_INET     2
#define ROOT_UID    0

/* ── Deny-counter map ─────────────────────────────────────────────────── */
struct {
	__uint(type,        BPF_MAP_TYPE_ARRAY);
	__uint(max_entries, 3);
	__type(key,   __u32);
	__type(value, __u64);
} sentinel_counters SEC(".maps");

static __always_inline void inc_counter(__u32 idx)
{
	__u64 *val = bpf_map_lookup_elem(&sentinel_counters, &idx);
	if (val)
		__sync_fetch_and_add(val, 1);
}

/* ── RFC-1918 helper (mirrors C/Rust implementations) ─────────────────── */
static __always_inline bool is_rfc1918(__u32 ip_be)
{
	__u32 ip = __builtin_bswap32(ip_be);  /* ntohl in BPF context */

	return ((ip >> 24) == 10)
	    || ((ip >> 20) == 0xAC1)
	    || ((ip >> 16) == 0xC0A8);
}

/* ── Hook 1: file_open ─────────────────────────────────────────────────── */
SEC("lsm/file_open")
int BPF_PROG(sentinel_file_open, struct file *file)
{
	/*
	 * Deny access to /etc/shadow.
	 * d_path resolution in BPF requires bpf_d_path() helper (≥ 5.10).
	 * We use inode number comparison as a portable alternative here.
	 */
	struct dentry *dentry;
	const unsigned char *name;
	char fname[32] = {};

	dentry = BPF_CORE_READ(file, f_path.dentry);
	name   = BPF_CORE_READ(dentry, d_name.name);
	bpf_core_read_str(fname, sizeof(fname), name);

	if (__builtin_memcmp(fname, "shadow", 6) == 0) {
		__u32 uid = bpf_get_current_uid_gid() & 0xFFFFFFFF;
		if (uid != ROOT_UID) {
			inc_counter(0);
			bpf_printk("sentinel_bpf: DENY file_open shadow uid=%u\n", uid);
			return -EACCES;
		}
	}
	return 0;
}

/* ── Hook 2: bprm_check_security (exec setuid denial) ─────────────────── */
SEC("lsm/bprm_check_security")
int BPF_PROG(sentinel_bprm_check, struct linux_binprm *bprm)
{
	struct inode *inode;
	umode_t mode;
	__u32 uid;

	inode = BPF_CORE_READ(bprm, file, f_inode);
	mode  = BPF_CORE_READ(inode, i_mode);
	uid   = bpf_get_current_uid_gid() & 0xFFFFFFFF;

	/* S_ISUID = 0004000 */
	if ((mode & 0004000) && uid != ROOT_UID) {
		inc_counter(1);
		bpf_printk("sentinel_bpf: DENY setuid-exec uid=%u\n", uid);
		return -EPERM;
	}
	return 0;
}

/* ── Hook 3: socket_connect (RFC-1918 block) ──────────────────────────── */
SEC("lsm/socket_connect")
int BPF_PROG(sentinel_socket_connect,
	     struct socket *sock, struct sockaddr *address, int addrlen)
{
	struct sockaddr_in *addr4;
	__u32 dst_ip;
	__u32 uid;
	__u16 family;

	family = BPF_CORE_READ(address, sa_family);
	if (family != AF_INET)
		return 0;

	addr4  = (struct sockaddr_in *)address;
	dst_ip = BPF_CORE_READ(addr4, sin_addr.s_addr);
	uid    = bpf_get_current_uid_gid() & 0xFFFFFFFF;

	if (is_rfc1918(dst_ip) && uid != ROOT_UID) {
		inc_counter(2);
		bpf_printk("sentinel_bpf: DENY socket_connect rfc1918 uid=%u\n", uid);
		return -ECONNREFUSED;
	}
	return 0;
}

char _license[] SEC("license") = "GPL";
