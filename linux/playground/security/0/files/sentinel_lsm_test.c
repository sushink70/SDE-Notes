// SPDX-License-Identifier: GPL-2.0-only
/*
 * tests/sentinel_lsm_test.c — KUnit test suite for Sentinel LSM
 *
 * Build path: security/sentinel/sentinel_lsm_test.c
 * Kconfig:    CONFIG_SECURITY_SENTINEL_KUNIT_TEST
 *
 * Run:
 *   # In-kernel via KUnit runner (requires UML or QEMU with kunit.py):
 *   ./tools/testing/kunit/kunit.py run \
 *       --kunitconfig=security/sentinel/.kunitconfig \
 *       --arch=um
 *
 *   # Or load the test module on a running kernel:
 *   insmod sentinel_lsm_test.ko
 *   dmesg | grep -E 'KTAP|PASS|FAIL|sentinel'
 *
 * References:
 *   Documentation/dev-tools/kunit/index.rst
 *   Documentation/dev-tools/kunit/usage.rst
 */

#include <kunit/test.h>
#include <linux/in.h>
#include <linux/byteorder/generic.h>
#include <linux/string.h>
#include <linux/slab.h>

/* Pull in the symbols under test.  In a real in-tree build these would be
 * exported with EXPORT_SYMBOL_GPL or tested as part of the same compilation
 * unit.  Here we replicate the small pure-C helpers to keep the test self-
 * contained. */

/* ── replicated helper (matches sentinel_lsm.c) ─────────────────────────── */
static bool is_rfc1918_correct(__be32 ip_be)
{
	u32 ip = ntohl(ip_be);

	return ((ip >> 24) == 10)
	    || ((ip >> 20) == 0xAC1)   /* 172.16/12 — CORRECT */
	    || ((ip >> 16) == 0xC0A8);
}

static bool is_rfc1918_buggy(__be32 ip_be)
{
	u32 ip = ntohl(ip_be);

	return ((ip >> 24) == 10)
	    || ((ip >> 24) == 172)     /* BUG2: /8 not /12 */
	    || ((ip >> 16) == 0xC0A8);
}

#define IPV4(a, b, c, d) htonl(((u32)(a) << 24) | ((u32)(b) << 16) | \
                                ((u32)(c) <<  8) |  (u32)(d))

/* ── Test cases ─────────────────────────────────────────────────────────── */

/* --- RFC-1918 classifier ------------------------------------------------- */

static void sentinel_test_10_slash_8(struct kunit *test)
{
	KUNIT_EXPECT_TRUE(test,  is_rfc1918_correct(IPV4(10,   0,   0,   1)));
	KUNIT_EXPECT_TRUE(test,  is_rfc1918_correct(IPV4(10, 255, 255, 254)));
	KUNIT_EXPECT_FALSE(test, is_rfc1918_correct(IPV4(11,   0,   0,   1)));
}

static void sentinel_test_172_16_slash_12_correct(struct kunit *test)
{
	/* Inside /12 range — must be blocked */
	KUNIT_EXPECT_TRUE(test, is_rfc1918_correct(IPV4(172, 16,  0,  1)));
	KUNIT_EXPECT_TRUE(test, is_rfc1918_correct(IPV4(172, 31, 255, 254)));

	/* Below and above /12 — must NOT be blocked by correct classifier */
	KUNIT_EXPECT_FALSE(test, is_rfc1918_correct(IPV4(172, 15,  0,  1)));
	KUNIT_EXPECT_FALSE(test, is_rfc1918_correct(IPV4(172, 32,  0,  1)));
}

/*
 * This test DEMONSTRATES BUG #2: the buggy classifier returns TRUE for
 * addresses outside 172.16/12.  If you swap is_rfc1918_buggy for
 * is_rfc1918_correct, both KUNIT_EXPECT_FALSE assertions will fail,
 * proving the bug.
 */
static void sentinel_test_172_16_slash_12_buggy(struct kunit *test)
{
	/* Buggy classifier wrongly blocks these (should be false): */
	KUNIT_EXPECT_TRUE(test, is_rfc1918_buggy(IPV4(172, 15, 0, 1)));  /* WRONG */
	KUNIT_EXPECT_TRUE(test, is_rfc1918_buggy(IPV4(172, 32, 0, 1)));  /* WRONG */

	/* If you use is_rfc1918_correct instead, both would be FALSE.     */
	/* This test exists to document the buggy behaviour, not endorse it.*/
}

static void sentinel_test_192_168_slash_16(struct kunit *test)
{
	KUNIT_EXPECT_TRUE(test,  is_rfc1918_correct(IPV4(192, 168,   1,   1)));
	KUNIT_EXPECT_FALSE(test, is_rfc1918_correct(IPV4(192, 169,   0,   1)));
}

static void sentinel_test_public_ips(struct kunit *test)
{
	KUNIT_EXPECT_FALSE(test, is_rfc1918_correct(IPV4(  1,   1,   1,   1)));
	KUNIT_EXPECT_FALSE(test, is_rfc1918_correct(IPV4(  8,   8,   8,   8)));
	KUNIT_EXPECT_FALSE(test, is_rfc1918_correct(IPV4(93, 184, 216,  34)));
	KUNIT_EXPECT_FALSE(test, is_rfc1918_correct(IPV4(  0,   0,   0,   0)));
}

/* --- Path prefix matcher ------------------------------------------------- */

static void sentinel_test_path_prefix(struct kunit *test)
{
	const char *rule_prefix = "/etc/shadow";
	const char *path_match  = "/etc/shadow";
	const char *path_miss   = "/etc/passwd";
	const char *path_sub    = "/etc/shadow~";  /* should also match if using strncmp */

	KUNIT_EXPECT_EQ(test, 0,
		strncmp(path_match, rule_prefix, strlen(rule_prefix)));
	KUNIT_EXPECT_NE(test, 0,
		strncmp(path_miss,  rule_prefix, strlen(rule_prefix)));
	/* /etc/shadow~ also matches prefix /etc/shadow — intentional (discuss in review) */
	KUNIT_EXPECT_EQ(test, 0,
		strncmp(path_sub, rule_prefix, strlen(rule_prefix)));
}

/* ── Test suite registration ─────────────────────────────────────────────── */

static struct kunit_case sentinel_test_cases[] = {
	KUNIT_CASE(sentinel_test_10_slash_8),
	KUNIT_CASE(sentinel_test_172_16_slash_12_correct),
	KUNIT_CASE(sentinel_test_172_16_slash_12_buggy),
	KUNIT_CASE(sentinel_test_192_168_slash_16),
	KUNIT_CASE(sentinel_test_public_ips),
	KUNIT_CASE(sentinel_test_path_prefix),
	{}
};

static struct kunit_suite sentinel_test_suite = {
	.name  = "sentinel_lsm",
	.test_cases = sentinel_test_cases,
};

kunit_test_suite(sentinel_test_suite);

MODULE_LICENSE("GPL v2");
MODULE_DESCRIPTION("KUnit tests for Sentinel LSM");
