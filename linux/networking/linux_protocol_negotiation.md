# Linux Protocol Negotiation, Encryption Fallback, and Cipher Selection
## A Complete In-Depth Systems Reference

---

## Table of Contents

- [Part I: Architecture — The Negotiation Landscape](#part-i-architecture)
- [Part II: The Linux Crypto API — The Foundation of Everything](#part-ii-linux-crypto-api)
- [Part III: kTLS — Kernel TLS and the Three-Layer Fallback Chain](#part-iii-ktls)
- [Part IV: XFRM / IPsec — Security Association Negotiation](#part-iv-xfrm)
- [Part V: TCP-Level Option Negotiation](#part-v-tcp-negotiation)
- [Part VI: IPv4/IPv6 Protocol Fallback](#part-vi-ipv4-ipv6-fallback)
- [Part VII: Application Protocol Version Negotiation](#part-vii-application-protocols)
- [Part VIII: eBPF, XDP, and Kernel Crypto Interaction](#part-viii-ebpf)
- [Part IX: Rust Integration — Userspace to Kernel](#part-ix-rust)
- [Part X: Failure Modes, Downgrade Attacks, and Security](#part-x-failure-modes)
- [Part XI: Connection Map and Mental Model Checkpoint](#part-xi-checkpoint)

---

# Part I: Architecture

## 1.1 The Subsystem Landscape

The phrase "protocol negotiation" in Linux covers at least five entirely different
mechanisms that operate at different layers, enforced by different actors (compiler,
kernel, hardware), and communicate through completely different interfaces.

**The critical mental model first:** negotiation in Linux is not one thing. It is
a stack of independent decisions, each with its own fallback logic:

```
  DECISION POINT 1: Which IP version? (IPv4 / IPv6)
       ↓ resolved at: connect()/bind() time, by the socket layer
  DECISION POINT 2: Which transport protocol? (TCP / UDP / SCTP)
       ↓ resolved at: socket(AF, SOCK_TYPE, PROTO) time
  DECISION POINT 3: Which TCP options? (SACK, TFO, ECN, timestamps)
       ↓ resolved at: SYN/SYN-ACK exchange, by the TCP state machine
  DECISION POINT 4: Which application protocol version? (TLS 1.2 / 1.3, NFSv4.1 / 4.2, SMB3.0 / 3.1.1)
       ↓ resolved at: application-layer handshake, by userspace daemons
  DECISION POINT 5: Which cipher suite? (AES-GCM-128, ChaCha20-Poly1305, etc.)
       ↓ resolved at: TLS/IKE handshake, by userspace; then pushed into kernel
  DECISION POINT 6: Which crypto implementation? (AES-NI / SIMD software / pure C)
       ↓ resolved at: crypto_alloc_*() time, by the Linux Crypto API priority system
  DECISION POINT 7: Where does crypto execute? (CPU / QAT / NIC offload)
       ↓ resolved at: SA/kTLS setup time, by driver availability
```

Each layer is independent. A TLS 1.3 session with AES-GCM-256 may use
AES-NI hardware, software fallback, or NIC offload — the application sees none
of this. Conversely, IKEv2 can negotiate AES-256-GCM but the kernel may silently
use a pure-software implementation if AES-NI is absent.

## 1.2 Complete Architecture Diagram

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                           USERSPACE                                          ║
║                                                                              ║
║  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐  ┌─────────────────┐  ║
║  │   OpenSSL    │  │   rustls     │  │  strongSwan  │  │   NFS / CIFS    │  ║
║  │   GnuTLS     │  │   boring-ssl │  │  libreswan   │  │   mount helpers │  ║
║  │  (TLS 1.2/3) │  │  (TLS 1.3)  │  │  (IKEv2)    │  │  (NFSv4.x/SMB3)│  ║
║  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └────────┬────────┘  ║
║         │                 │                  │                   │           ║
║    read()/write()    read()/write()    AF_KEY/Netlink      RPC/SMB pkt       ║
╚═════════╪═════════════════╪════════════════╪══════════════════╪═════════════╝
          │                 │                │                  │
══════════╪═════════════════╪════════════════╪══════════════════╪══════════════
          ▼                 ▼                ▼                  ▼
╔══════════════════════════════════════════════════════════════════════════════╗
║                        KERNEL SPACE                                          ║
║                                                                              ║
║  ┌────────────────────────────────────────────────────────────────────────┐  ║
║  │                   VFS / Socket Layer                                   │  ║
║  │       net/socket.c  ·  include/linux/net.h  ·  AF_INET/AF_INET6       │  ║
║  └──────────────┬──────────────────────┬───────────────────┬─────────────┘  ║
║                 │                      │                   │                ║
║                 ▼                      ▼                   ▼                ║
║  ┌──────────────────┐  ┌──────────────────────┐  ┌──────────────────────┐  ║
║  │   TCP/IP Stack   │  │     kTLS (ULP)       │  │    XFRM Framework    │  ║
║  │  net/ipv4/tcp.c  │  │   net/tls/           │  │  net/xfrm/           │  ║
║  │  net/ipv6/       │  │                      │  │                      │  ║
║  │                  │  │  TCP_ULP="tls"       │  │  Security Assoc DB   │  ║
║  │  ┌────────────┐  │  │  TLS_TX / TLS_RX     │  │  Security Policy DB  │  ║
║  │  │TCP Options │  │  │                      │  │                      │  ║
║  │  │Negotiation:│  │  │  ┌────────────────┐  │  │  ┌────────────────┐  │  ║
║  │  │ SACK       │  │  │  │ NIC TLS offload│  │  │  │ ESP/AH/IPCOMP  │  │  ║
║  │  │ TFO        │  │  │  │ (mlx5/ixgbe)   │  │  │  │ authenc tmpl   │  │  ║
║  │  │ ECN        │  │  │  ├────────────────┤  │  │  │ xfrm_find_algo │  │  ║
║  │  │ Timestamps │  │  │  │ Kernel SW kTLS │  │  │  └────────────────┘  │  ║
║  │  │ WinScale   │  │  │  └────────────────┘  │  │                      │  ║
║  │  └────────────┘  │  └──────────────────────┘  └──────────────────────┘  ║
║  └──────────────────┘            │                          │               ║
║                                  │                          │               ║
║                 ┌────────────────┴──────────────────────────┘               ║
║                 ▼                                                            ║
║  ┌────────────────────────────────────────────────────────────────────────┐  ║
║  │                     Linux Crypto API                                   │  ║
║  │                  crypto/api.c · crypto/algapi.c                        │  ║
║  │                                                                        │  ║
║  │   Algorithm Registry: crypto_alg_list (doubly-linked, sorted by name)  │  ║
║  │                                                                        │  ║
║  │  ┌─────────────────────────────────────────────────────────────────┐  │  ║
║  │  │  PRIORITY TIERS (cra_priority field)                             │  │  ║
║  │  │                                                                   │  │  ║
║  │  │  600+ ┤ Intel QAT (QuickAssist) driver                          │  │  ║
║  │  │  400  ┤ CPU hw: AES-NI, SHA-NI, VAES, VPCLMULQDQ               │  │  ║
║  │  │  300  ┤ SIMD software (safe in any context via simd wrapper)     │  │  ║
║  │  │  200  ┤ SIMD software (process context only, unguarded)          │  │  ║
║  │  │  100  ┤ Pure C / generic software                                │  │  ║
║  │  │   50  ┤ Test/stub implementations                                │  │  ║
║  │  └─────────────────────────────────────────────────────────────────┘  │  ║
║  │                                                                        │  ║
║  │  Template Instantiation: "cbc(aes)" → CBC template + AES primitive    │  ║
║  │  Wrappers: cryptd (sync→async), simd (SIMD context guard)            │  ║
║  │  Types: skcipher, aead, ahash, shash, akcipher, kpp, rng             │  ║
║  └────────────────────────────────┬───────────────────────────────────────┘  ║
║                                   │                                          ║
╚═══════════════════════════════════╪══════════════════════════════════════════╝
                                    ▼
╔══════════════════════════════════════════════════════════════════════════════╗
║                         HARDWARE LAYER                                       ║
║                                                                              ║
║  ┌────────────┐  ┌─────────────┐  ┌───────────────┐  ┌───────────────────┐  ║
║  │ AES-NI CPU │  │ SHA Ext CPU │  │  Intel QAT    │  │   NIC (mlx5/ixgbe)│  ║
║  │ VAES (AVX- │  │  (SHA-1/256 │  │  (QuickAssist)│  │  TLS offload      │  ║
║  │ 512 AES)   │  │   in HW)    │  │  crypto accel │  │  IPsec offload    │  ║
║  └────────────┘  └─────────────┘  └───────────────┘  └───────────────────┘  ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

## 1.3 The Two Negotiation Domains

It is essential to separate two orthogonal concepts that documentation conflates:

**Domain A: Protocol Negotiation** — which protocol or protocol version to use.
Resolved at the application or transport layer. Examples: TLS 1.2 vs. 1.3,
NFSv4.1 vs. 4.2, IPv4 vs. IPv6, TCP vs. SCTP. The negotiation is bidirectional
(both peers must agree), happens at connection setup, and is fully visible to
both endpoints.

**Domain B: Crypto Implementation Selection** — which code path (hardware,
SIMD software, or pure C) to execute the agreed algorithm. Resolved inside the
Linux Crypto API at `crypto_alloc_*()` time. This is unilateral (each host
independently picks its best implementation), completely invisible to the remote
peer, and happens every time a crypto transform is allocated, not just at
connection setup.

These domains interact only at the kTLS and XFRM layers: Domain A picks the
algorithm (e.g., AES-GCM-128), and Domain B picks the implementation of that
algorithm.

---

# Part II: The Linux Crypto API

## 2.1 Mental Model: A Priority-Ordered Registry of Algorithm Implementations

The Linux Crypto API is a registry of named algorithm implementations with
a priority-based selection mechanism. When any kernel subsystem (kTLS, XFRM,
dm-crypt, IPsec, filesystems) needs to perform cryptographic operations, it
calls `crypto_alloc_*()` with an algorithm name string. The kernel walks the
registry, finds all implementations matching that name, and returns the highest
priority one.

**Analogy:** Think of the crypto registry as a routing table, where the "destination"
is an algorithm name (e.g., `"cbc(aes)"`) and the "next hop" is an implementation
(AES-NI driver, SIMD software, generic C). Like BGP preference attributes, higher
priority wins. Unlike routing, there is no per-flow state — every call to
`crypto_alloc_*()` re-evaluates the registry at allocation time.

**This analogy breaks at:** algorithms that are hardware-specific and fail on
certain inputs (e.g., some QAT implementations only support specific key sizes).
These drivers set `CRYPTO_ALG_NEED_FALLBACK` and internally chain to a software
fallback, unlike routing where a selected next-hop either works or triggers a
re-lookup.

## 2.2 The Algorithm Descriptor: `struct crypto_alg`

Every algorithm in the registry is described by a `struct crypto_alg`, defined
in `include/linux/crypto.h`:

```c
/*
 * include/linux/crypto.h (simplified, kernel 6.x)
 *
 * Every implementation — hardware driver, SIMD routine, or pure C —
 * registers one of these. This is the identity card of an algorithm.
 */
struct crypto_alg {
    struct list_head    cra_list;           /* linked into crypto_alg_list */
    struct list_head    cra_users;          /* tfms using this algorithm */

    u32                 cra_flags;          /* CRYPTO_ALG_* flags (see below) */
    unsigned int        cra_blocksize;      /* block size in bytes, or 1 for stream */
    unsigned int        cra_ctxsize;        /* size of per-tfm context (allocated per user) */
    unsigned int        cra_alignmask;      /* required input/output alignment - 1 */

    int                 cra_priority;       /* THE KEY FIELD: higher wins */
    atomic_t            cra_refcnt;         /* reference count */

    char                cra_name[CRYPTO_MAX_ALG_NAME];        /* logical name: "cbc(aes)" */
    char                cra_driver_name[CRYPTO_MAX_ALG_NAME]; /* impl name: "cbc-aes-aesni" */

    const struct crypto_type *cra_type;     /* skcipher, aead, hash, etc. */

    union {
        struct cipher_alg   ciph;           /* single-block cipher */
        struct compress_alg co;             /* compression */
    } cra_u;

    int (*cra_init)(struct crypto_tfm *tfm);
    void (*cra_exit)(struct crypto_tfm *tfm);
    void (*cra_destroy)(struct crypto_alg *alg);

    struct module *cra_module;              /* owner module (for refcounting) */
};
```

**Key flags in `cra_flags`:**

```c
/* Algorithm is asynchronous (uses callbacks, not blocking) */
#define CRYPTO_ALG_ASYNC                0x00000080

/* Algorithm needs a software fallback for some inputs */
#define CRYPTO_ALG_NEED_FALLBACK        0x00000100

/* Algorithm is a kernel-internal implementation only */
#define CRYPTO_ALG_INTERNAL             0x00002000

/* Algorithm was tested by crypto self-tests on boot */
#define CRYPTO_ALG_TESTED               0x00000200

/* FIPS-approved algorithm */
#define CRYPTO_ALG_FIPS_INTERNAL        0x00020000
```

## 2.3 Algorithm Type Hierarchy

The Crypto API distinguishes algorithm types by the operations they expose.
Each type has its own allocation function, transform struct, and operation set:

```
ALGORITHM TYPE HIERARCHY
═══════════════════════════════════════════════════════════════════════

  skcipher  ── Symmetric key cipher (encrypt/decrypt blocks or streams)
              ── Examples: cbc(aes), ctr(aes), xts(aes), chacha20
              ── Allocation: crypto_alloc_skcipher("cbc(aes)", 0, 0)
              ── Operations: encrypt, decrypt (with IV)
              ── Used by: kTLS, dm-crypt, fscrypt

  aead      ── Authenticated Encryption with Associated Data
              ── Examples: gcm(aes), chacha20-poly1305, rfc4106(gcm(aes))
              ── Allocation: crypto_alloc_aead("gcm(aes)", 0, 0)
              ── Operations: encrypt+authenticate, decrypt+verify
              ── Used by: kTLS, XFRM/IPsec (ESP)

  ahash     ── Asynchronous hash / message digest
              ── Examples: sha256, sha512, hmac(sha256)
              ── Allocation: crypto_alloc_ahash("hmac(sha256)", 0, 0)
              ── Operations: init, update, final (streaming)
              ── Used by: IPsec AH, TLS MAC (TLS 1.2 CBC mode)

  shash     ── Synchronous hash (simpler API for non-async callers)
              ── Same algorithms as ahash, but blocking
              ── Allocation: crypto_alloc_shash("sha256", 0, 0)

  akcipher  ── Asymmetric key cipher
              ── Examples: rsa, ecdsa, sm2
              ── Used by: kernel key service, module verification

  kpp       ── Key-agreement Protocol Primitives
              ── Examples: ecdh, dh, curve25519
              ── Used by: WireGuard (drivers/net/wireguard/noise.c)

  rng       ── Random number generator
              ── Examples: stdrng, drbg_pr_hmac_sha256
              ── Used by: crypto operations needing random material

  cipher    ── Raw single-block cipher (no mode, no IV)
              ── Examples: aes, des3_ede
              ── Not used directly; consumed by templates (cbc, gcm, etc.)
```

## 2.4 The Template System: Composed Algorithms

The kernel does not register every possible cipher-mode combination separately.
Instead, it uses a template system where a mode (CBC, GCM, CTR) is a template
that takes a primitive cipher as input:

```
TEMPLATE INSTANTIATION: "gcm(aes)"
═══════════════════════════════════════════════════════════════════════

  Request: crypto_alloc_aead("gcm(aes)", 0, 0)

  Parser splits: template_name="gcm", inner_name="aes"

  Template lookup: finds gcm_tmpl in crypto_template_list

  gcm_tmpl.create("gcm", "aes"):
      1. Calls crypto_alloc_cipher("aes", 0, 0)      ← inner block cipher
      2. Wraps it in GCM mode (GHASH + CTR) logic
      3. Registers the composed "gcm(aes)" algorithm
      4. Returns it to caller

COMMON TEMPLATE COMPOSITIONS:
═══════════════════════════════════════════════════════════════════════

  "cbc(aes)"                → CBC mode + AES block cipher
  "ctr(aes)"                → CTR mode + AES block cipher
  "xts(aes)"                → XTS mode + AES (for dm-crypt)
  "gcm(aes)"                → GCM AEAD + AES
  "ccm(aes)"                → CCM AEAD + AES
  "hmac(sha256)"            → HMAC construction + SHA-256
  "authenc(hmac(sha256),cbc(aes))"  → Combined auth+enc for IPsec ESP
  "rfc4106(gcm(aes))"       → GCM with RFC 4106 IV construction (IPsec)
  "rfc4543(gcm(aes))"       → GCM with RFC 4543 (GMAC, auth-only)
  "essiv(cbc(aes),sha256)"  → ESSIV mode (encrypted salt-sector IV) for dm-crypt
  "cts(cbc(aes))"           → Ciphertext stealing (for Kerberos/fscrypt)

NESTING IS RECURSIVE:
  "authenc(hmac(sha1),cbc(des3_ede))"   → legacy ESP, still supported
  "simd(gcm-aes-aesni)"                 → SIMD guard wrapping hw accelerated GCM
  "cryptd(cbc-aes-aesni)"               → async wrapper making sync AES-NI async
```

## 2.5 The Priority System: How the Kernel Picks a Winner

When `crypto_alloc_skcipher("cbc(aes)", 0, 0)` is called, the kernel must
choose among potentially dozens of registered `cbc(aes)` implementations. The
algorithm at `crypto/api.c:crypto_alg_lookup()` does this:

```c
/*
 * crypto/api.c — simplified representation of the lookup logic
 *
 * The actual kernel uses __crypto_alg_lookup() which iterates
 * crypto_alg_list protected by crypto_alg_sem (read-write semaphore).
 *
 * MENTAL MODEL: For each registered algorithm:
 *   1. Does the cra_name match? (or cra_driver_name if exact match requested)
 *   2. Does (alg->cra_flags & type) == type?      (type filter)
 *   3. Does (alg->cra_flags & mask) == (type & mask)? (mask filter)
 *   4. Among all matches, pick highest cra_priority.
 */
static struct crypto_alg *crypto_alg_lookup(const char *name,
                                             u32 type, u32 mask)
{
    struct crypto_alg *q, *alg = NULL;
    int best = -2;  /* below minimum priority */

    down_read(&crypto_alg_sem);
    list_for_each_entry(q, &crypto_alg_list, cra_list) {
        /* Name must match logical name (cra_name) */
        if (strcmp(q->cra_name, name) != 0)
            continue;

        /* Type and mask filter */
        if ((q->cra_flags & mask) != (type & mask))
            continue;

        /* Algorithm must have passed self-tests */
        if (!(q->cra_flags & CRYPTO_ALG_TESTED))
            continue;

        /* Prefer higher priority */
        if (q->cra_priority > best) {
            best = q->cra_priority;
            alg = q;
        }
    }
    if (alg)
        crypto_mod_get(alg); /* bump refcount before releasing lock */
    up_read(&crypto_alg_sem);
    return alg;
}
```

**Priority values in practice — what ships in a typical x86-64 kernel:**

```
ALGORITHM: "cbc(aes)" — registered implementations

  cra_driver_name              cra_priority  Source
  ───────────────────────────  ────────────  ──────────────────────────────
  cbc-aes-aesni                400           drivers/crypto/x86/aes-intel_glue.c
  cbc-aes-avx2                 400           (same driver, AVX2 path, same prio)
  cbc(aes-aesni)               400           auto-instantiated from gcm template
  cbc-aes-neon (ARM)           400           arch/arm64/crypto/aes-neon.S
  cbc(aes-generic)             100           crypto/aes_generic.c

  → Lookup returns: cbc-aes-aesni (priority 400)
  → Fallback path: if AES-NI CPU flag absent, returns cbc(aes-generic) (100)

ALGORITHM: "gcm(aes)" — registered implementations

  cra_driver_name              cra_priority  Source
  ───────────────────────────  ────────────  ──────────────────────────────
  rfc4106-gcm-aesni            400           drivers/crypto/x86/aesni-intel_glue.c
  gcm_base(ctr(aes-aesni),ghash-clmulni)  400  auto-instantiated
  gcm(aes-generic)             100           auto-instantiated from templates

ALGORITHM: "sha256" — registered implementations

  cra_driver_name              cra_priority  Source
  ───────────────────────────  ────────────  ──────────────────────────────
  sha256-avx2                  170           arch/x86/crypto/sha256_avx2_asm.S
  sha256-avx                   160           arch/x86/crypto/sha256_avx_asm.S
  sha256-ssse3                 150           arch/x86/crypto/sha256_ssse3_asm.S
  sha256-generic               100           crypto/sha256_generic.c
  sha256 (SHA-NI hw)           300           arch/x86/crypto/sha256_ni_asm.S
```

**Inspecting from userspace:**

```bash
# /proc/crypto lists ALL registered algorithms with their priority.
# This is your ground truth — what the running kernel actually has.

cat /proc/crypto | grep -A 10 "name.*cbc"

# Output for cbc(aes-generic):
name         : cbc(aes)
driver       : cbc(aes-generic)
module       : kernel
priority     : 100
refcnt       : 1
selftest     : passed
internal     : no
type         : skcipher
async        : no
blocksize    : 16
min keysize  : 16
max keysize  : 32
ivsize       : 16
chunksize    : 16
walksize     : 16

# For AES-NI version:
name         : cbc(aes)
driver       : cbc-aes-aesni
module       : aesni_intel
priority     : 400
...
async        : no        ← sync by default; cryptd wrapper makes it async

# List all algorithms and their priorities sorted:
cat /proc/crypto | awk '/^name/{n=$3} /^priority/{print $3, n}' | sort -rn | head -30
```

## 2.6 Hardware Driver Registration and Priority

Let's look at how a real hardware crypto driver registers its algorithms.
AES-NI (Intel's hardware AES instruction support) is the most common:

```c
/*
 * drivers/crypto/x86/aesni-intel_glue.c (abridged, representative of kernel ~6.x)
 *
 * This driver registers AES implementations that use the AESENC/AESDEC
 * instruction family present on Intel Westmere (2010) and later CPUs.
 *
 * It registers both the raw AES cipher AND composed modes (CBC, CTR, GCM).
 */

static struct skcipher_alg aesni_skciphers[] = {
    {
        /* CBC mode with AES-NI */
        .base = {
            .cra_name           = "__cbc(aes)",      /* internal name */
            .cra_driver_name    = "__cbc-aes-aesni",
            .cra_priority       = 400,
            .cra_flags          = CRYPTO_ALG_INTERNAL,
            .cra_blocksize      = AES_BLOCK_SIZE,    /* 16 bytes */
            .cra_ctxsize        = CRYPTO_AES_CTX_SIZE,
            .cra_module         = THIS_MODULE,
        },
        .min_keysize    = AES_MIN_KEY_SIZE,  /* 16 bytes */
        .max_keysize    = AES_MAX_KEY_SIZE,  /* 32 bytes */
        .ivsize         = AES_BLOCK_SIZE,
        .setkey         = aesni_skcipher_setkey,
        .encrypt        = cbc_encrypt,       /* uses AES-NI internally */
        .decrypt        = cbc_decrypt,
    },
    {
        /* CTR mode with AES-NI */
        .base = {
            .cra_name           = "__ctr(aes)",
            .cra_driver_name    = "__ctr-aes-aesni",
            .cra_priority       = 400,
            .cra_flags          = CRYPTO_ALG_INTERNAL,
            .cra_blocksize      = 1,             /* stream cipher: blocksize = 1 */
            .cra_ctxsize        = CRYPTO_AES_CTX_SIZE,
            .cra_module         = THIS_MODULE,
        },
        .min_keysize    = AES_MIN_KEY_SIZE,
        .max_keysize    = AES_MAX_KEY_SIZE,
        .ivsize         = AES_BLOCK_SIZE,
        .chunksize      = AES_BLOCK_SIZE,
        .setkey         = aesni_skcipher_setkey,
        .encrypt        = ctr_crypt,
        .decrypt        = ctr_crypt,             /* CTR encrypt == decrypt */
    },
};

/*
 * Registration happens at module_init() / driver probe time.
 * If cpuid detects no AES-NI support, the module refuses to load.
 */
static int __init aesni_init(void)
{
    /*
     * CRITICAL: Check CPU feature flag BEFORE registering.
     * If CPU lacks AES-NI, don't poison the registry with
     * a driver that would segfault on the AESENC instruction.
     */
    if (!boot_cpu_has(X86_FEATURE_AES)) {
        pr_info("AES-NI instructions not detected\n");
        return -ENODEV;  /* module refuses to load; kernel falls back to generic */
    }

    err = crypto_register_skciphers(aesni_skciphers,
                                    ARRAY_SIZE(aesni_skciphers));
    if (err)
        return err;

    err = crypto_register_aeads(aesni_aeads, ARRAY_SIZE(aesni_aeads));
    if (err)
        goto unregister_skciphers;

    return 0;

unregister_skciphers:
    crypto_unregister_skciphers(aesni_skciphers, ARRAY_SIZE(aesni_skciphers));
    return err;
}
module_init(aesni_init);
```

**The critical insight:** Hardware drivers use a CPU feature gate at load time.
If the CPU lacks AES-NI, the module either doesn't load or returns `-ENODEV`.
The crypto registry then falls back to the next-highest-priority implementation.
This is not dynamic per-call fallback — it is static at module load time.

## 2.7 The `CRYPTO_ALG_NEED_FALLBACK` Mechanism

Some hardware drivers cannot handle all valid inputs. A common case: QAT
accelerators that only support 128-bit and 256-bit AES keys but not 192-bit,
or NIC crypto engines that require data to be at least one block in size.

```c
/*
 * Pattern from drivers/crypto/qat/qat_common/qat_algs.c (simplified)
 *
 * The NEED_FALLBACK pattern:
 * 1. Driver registers with CRYPTO_ALG_NEED_FALLBACK in cra_flags
 * 2. During setkey(), if the key doesn't fit HW constraints, fall through
 *    to software fallback
 * 3. During encrypt/decrypt, check if HW path is active; if not, call fallback
 */

struct qat_cipher_ctx {
    struct crypto_skcipher *sw_cipher;  /* ← software fallback, always allocated */
    void                   *hw_ctx;    /* ← hardware context, NULL if not usable */
    bool                    use_hw;
};

static int qat_alg_setkey(struct crypto_skcipher *tfm,
                           const u8 *key, unsigned int keylen)
{
    struct qat_cipher_ctx *ctx = crypto_skcipher_ctx(tfm);

    /*
     * QAT hardware only supports 128 and 256-bit AES.
     * 192-bit key: silently route to software fallback.
     */
    if (keylen == AES_KEYSIZE_192) {
        ctx->use_hw = false;
        /* Program the software fallback with the key */
        return crypto_skcipher_setkey(ctx->sw_cipher, key, keylen);
    }

    /* Try to program hardware */
    if (qat_hw_setkey(ctx->hw_ctx, key, keylen) == 0) {
        ctx->use_hw = true;
        return 0;
    }

    /* HW programming failed; fall back to software */
    ctx->use_hw = false;
    return crypto_skcipher_setkey(ctx->sw_cipher, key, keylen);
}

static int qat_alg_encrypt(struct skcipher_request *req)
{
    struct qat_cipher_ctx *ctx =
        crypto_skcipher_ctx(crypto_skcipher_reqtfm(req));

    if (ctx->use_hw)
        return qat_hw_encrypt(req);     /* DMA to QAT, async completion */
    else
        return crypto_skcipher_encrypt(/* fallback request */);
}

/*
 * Registration: note CRYPTO_ALG_NEED_FALLBACK in cra_flags.
 * This tells callers "I have an internal fallback; allocating me
 * is always safe even for edge-case inputs."
 */
static struct skcipher_alg qat_cbc_aes = {
    .base = {
        .cra_name        = "cbc(aes)",
        .cra_driver_name = "cbc-aes-qat",
        .cra_priority    = 400,
        .cra_flags       = CRYPTO_ALG_ASYNC | CRYPTO_ALG_NEED_FALLBACK,
        ...
    },
    ...
};
```

**The caller's perspective:** When a subsystem calls
`crypto_alloc_skcipher("cbc(aes)", CRYPTO_ALG_ASYNC, CRYPTO_ALG_ASYNC)`,
it gets QAT (priority 400, async). If QAT isn't loaded or the CPU lacks
the required features, it falls to AES-NI (priority 400, sync, then wrapped
by cryptd to become async), and finally to generic software (priority 100).
The caller never knows which path was taken.

## 2.8 `cryptd`: Making Synchronous Algorithms Asynchronous

Some subsystems (notably IPsec/XFRM in certain code paths) require async
algorithms (CRYPTO_ALG_ASYNC flag). But many quality implementations (AES-NI)
are synchronous. The `cryptd` wrapper bridges this gap:

```c
/*
 * crypto/cryptd.c — the async wrapper template
 *
 * MENTAL MODEL: cryptd spins up a kernel crypto workqueue.
 * When encrypt/decrypt is called:
 *   1. Request is queued to the workqueue
 *   2. Caller returns immediately (non-blocking)
 *   3. Worker thread calls the underlying SYNC algorithm
 *   4. Worker invokes the completion callback
 *
 * Cost: One context switch (schedule to worker, back to caller on completion).
 * Use only when the async interface is mandatory; prefer sync when caller can block.
 */

/* Creating an async version of a sync algorithm: */
struct crypto_aead *tfm;

/* "cryptd(gcm-aes-aesni)" → async wrapper around sync AES-NI GCM */
tfm = crypto_alloc_aead("cryptd(gcm-aes-aesni)", 0, 0);
/*
 * Equivalent to: "give me an ASYNC aead named gcm(aes),
 * implemented by wrapping the AES-NI version in cryptd"
 */

/* The kernel also auto-wraps on allocation if you request async: */
tfm = crypto_alloc_aead("gcm(aes)",
                          CRYPTO_ALG_ASYNC,    /* type: I want async */
                          CRYPTO_ALG_ASYNC);   /* mask: filter to async only */
/*
 * If no native async gcm(aes) exists, kernel auto-tries:
 *   1. Look for native CRYPTO_ALG_ASYNC "gcm(aes)" → not found
 *   2. Auto-instantiate "cryptd(gcm-aes-aesni)" → found, priority 50
 * The cryptd-wrapped version gets priority = original_priority - 50 by convention
 */
```

## 2.9 `simd`: The SIMD Context Guard

AES-NI and other SIMD instructions require that the CPU's SSE/AVX register
state be saved. In kernel code, this is not always possible (interrupt handlers,
NMI context, softirq with non-preemptible kernel). The `simd` wrapper ensures
SIMD algorithms are only invoked when the context is safe:

```c
/*
 * crypto/simd.c — SIMD context guard
 *
 * MENTAL MODEL: Before calling the underlying SIMD algorithm,
 * simd checks kernel_fpu_can_use() (or equivalent on ARM: may_use_simd()).
 * If SIMD is unavailable in the current context, it falls back to the
 * non-SIMD variant of the same algorithm.
 *
 * This solves: AES-NI cannot be used in interrupt context on x86 without
 * explicitly calling kernel_fpu_begin()/kernel_fpu_end() to save/restore
 * the FPU state. simd handles this automatically.
 *
 * The "simd(gcm-aes-aesni)" algorithm:
 *   - In process context where FPU save is cheap: calls AES-NI GCM
 *   - In interrupt/softirq context: calls gcm(aes-generic) fallback
 */

static int simd_skcipher_encrypt(struct skcipher_request *req)
{
    struct simd_skcipher_ctx *ctx = ...;

    if (!crypto_simd_usable()) {
        /* Not safe to use SIMD (in interrupt, FPU state not saved) */
        /* Route to software fallback — same algorithm, no SIMD */
        return crypto_skcipher_encrypt(ctx->fallback_req);
    }

    /* SIMD is available: save FPU, run AES-NI, restore FPU */
    return simd_skcipher_do_encrypt(req);
}
```

## 2.10 Complete `crypto_alloc_skcipher` Walk-Through

Here is the complete decision flow when any kernel subsystem calls
`crypto_alloc_skcipher("cbc(aes)", 0, 0)`:

```
crypto_alloc_skcipher("cbc(aes)", type=0, mask=0)
│
├─ Step 1: Exact name lookup in crypto_alg_list
│  ├─ Found: "cbc(aes)" with driver "cbc-aes-aesni", priority=400
│  │         → If CPU has AES-NI: RETURN THIS. Done.
│  │
│  └─ Found: "cbc(aes)" with driver "cbc(aes-generic)", priority=100
│            → Return lowest-priority fallback only if nothing better exists
│
├─ Step 2: Template instantiation (if no exact match or forced)
│  ├─ Parse: template="cbc", inner="aes"
│  ├─ Find template "cbc" in crypto_template_list
│  ├─ Find cipher "aes" (highest priority) in crypto_alg_list
│  │  ├─ "aes-aesni" priority=400 (if AES-NI present)
│  │  └─ "aes-generic" priority=100 (fallback)
│  └─ Instantiate: cbc wrapping highest-priority aes
│     → Registers new algorithm "cbc(aes-aesni)" or "cbc(aes-generic)"
│     → Returns newly instantiated transform
│
├─ Step 3: Module autoload (if still not found)
│  ├─ Calls request_module("crypto-cbc")  ← loads the CBC template module
│  ├─ Calls request_module("crypto-aes")  ← loads AES primitive module
│  └─ Retries steps 1-2
│
└─ Step 4: Failure
   └─ All lookups failed, all module loads failed
      → Returns ERR_PTR(-ENOENT) or ERR_PTR(-ENOMEM)
      → Caller MUST check IS_ERR(tfm) and handle

RETURNED OBJECT: struct crypto_skcipher *tfm
  - Wraps the best available implementation
  - Has a per-tfm context (ctx) of size cra_ctxsize, allocated from kmalloc
  - Caller must eventually call crypto_free_skcipher(tfm)
```

## 2.11 C Implementation: Allocating with Explicit Fallback

```c
/*
 * CONCEPT: Manual fallback chain for crypto algorithm allocation
 * INVARIANT: At least one algorithm in the chain must be available
 * WHAT WOULD BREAK: If all algorithms in chain are unavailable and
 *                   you don't check IS_ERR, you dereference an error pointer
 *                   → immediate NULL pointer dereference in kernel → panic
 */

#include <linux/crypto.h>
#include <crypto/skcipher.h>

/*
 * Preferred algorithm order for AES encryption:
 *   1. Hardware GCM (AEAD with auth) — best for modern systems
 *   2. AES-NI CBC — common hardware path (no auth, IPsec handles auth separately)
 *   3. Generic CBC — pure software, always available
 *
 * In practice, you would NOT do manual fallback like this;
 * the crypto API handles priority automatically. This pattern is only
 * needed when you want a DIFFERENT ALGORITHM as fallback (not just a
 * different implementation of the same algorithm).
 */

struct my_cipher_ctx {
    struct crypto_skcipher *tfm;
    const char             *algo_used;
};

static const char *const preferred_algos[] = {
    "cbc(aes)",      /* hw-accelerated if AES-NI present */
    "ctr(aes)",      /* fallback mode (different chaining) */
    "cbc(sm4)",      /* Chinese national standard cipher */
    NULL
};

int alloc_best_cipher(struct my_cipher_ctx *mctx)
{
    const char **algo;

    for (algo = preferred_algos; *algo != NULL; algo++) {
        struct crypto_skcipher *tfm;

        tfm = crypto_alloc_skcipher(*algo,
                                     0,    /* type: accept any (sync or async) */
                                     0);   /* mask: no filtering */
        if (!IS_ERR(tfm)) {
            mctx->tfm      = tfm;
            mctx->algo_used = *algo;
            pr_info("crypto: selected algorithm '%s' (driver: '%s', priority: %d)\n",
                    *algo,
                    crypto_skcipher_driver_name(tfm),  /* actual impl chosen */
                    crypto_tfm_alg_priority(crypto_skcipher_tfm(tfm)));
            return 0;
        }

        pr_warn("crypto: '%s' unavailable (%ld), trying next\n",
                *algo, PTR_ERR(tfm));
    }

    pr_err("crypto: no cipher available from preferred list\n");
    return -ENOENT;
}

void free_cipher(struct my_cipher_ctx *mctx)
{
    if (mctx->tfm)
        crypto_free_skcipher(mctx->tfm);
}

/*
 * ENCRYPT USAGE — synchronous path (most kernel subsystems):
 */
int do_encrypt(struct my_cipher_ctx *mctx,
               const u8 *key, unsigned int key_len,
               const u8 *iv,  unsigned int iv_len,
               struct scatterlist *src, struct scatterlist *dst,
               unsigned int nbytes)
{
    SKCIPHER_REQUEST_ON_STACK(req, mctx->tfm);
    int ret;

    /*
     * setkey: programs the key schedule into the per-tfm context.
     * For AES-NI: computes expanded key using AESKEYGENASSIST instruction.
     * For software: computes expanded key in pure C.
     */
    ret = crypto_skcipher_setkey(mctx->tfm, key, key_len);
    if (ret) {
        pr_err("crypto: setkey failed (%d) — key size may be invalid\n", ret);
        return ret;
    }

    skcipher_request_set_tfm(req, mctx->tfm);
    skcipher_request_set_crypt(req, src, dst, nbytes, (u8 *)iv);
    skcipher_request_set_callback(req, 0, NULL, NULL); /* sync: no callback */

    ret = crypto_skcipher_encrypt(req);
    /* For synchronous algos, ret is 0 (success) or negative errno.
     * For async (if tfm is CRYPTO_ALG_ASYNC), ret may be -EINPROGRESS,
     * meaning the callback will be invoked when done. */

    skcipher_request_zero(req); /* zero the request struct (contains key material!) */
    return ret;
}
```

## 2.12 Probing Algorithm Availability

The kernel provides probe-only functions that check availability without
allocating a transform (no per-tfm context allocation):

```c
#include <linux/crypto.h>

/*
 * Probe whether "gcm(aes)" is available without allocating.
 * Returns 0 if available, -ENOENT if not.
 * Used by XFRM's xfrm_find_algo() to validate IKE-negotiated ciphers.
 */
int probe_gcm_aes(void)
{
    /* crypto_has_aead: probe AEAD type */
    return crypto_has_aead("gcm(aes)", 0, CRYPTO_ALG_ASYNC);
    /* Returns 1 if found, 0 if not */
}

int probe_cbc_aes(void)
{
    /* crypto_has_skcipher: probe skcipher type */
    return crypto_has_skcipher("cbc(aes)", 0, 0);
}

int probe_sha256(void)
{
    return crypto_has_ahash("sha256", 0, 0);
}
```

---

# Part III: kTLS — Kernel TLS

## 3.1 Mental Model: Moving the Record Layer into the Kernel

Standard TLS implementation: the TLS library (OpenSSL, rustls, BoringSSL)
lives in userspace. To send an encrypted packet:

```
Userspace: plaintext → TLS library encrypt → ciphertext in userspace buffer
→ write() syscall → kernel copies ciphertext from userspace → NIC sends it
```

Two problems at scale:
1. The copy from userspace to kernel buffer touches every byte twice
2. Kernel `sendfile()` and `splice()` zero-copy paths cannot be used
   because the kernel doesn't have the TLS context to encrypt the data
   in-flight

kTLS moves the TLS record layer (encryption/decryption) into the kernel:

```
Userspace: plaintext → write() syscall
Kernel: TLS record layer adds header, encrypts in-place, NIC sends
                                       ↑
                                       cipher state lives here now
```

After the TLS handshake completes in userspace (the kernel is not involved
in handshakes — only in record encryption), the userspace library extracts
the negotiated session keys and programs them into the kernel via `setsockopt`.
From that point, `write()` sends plaintext and the kernel encrypts it. `read()`
receives ciphertext and the kernel decrypts it before returning plaintext.

**Analogy:** Think of kTLS like IPsec's SAD (Security Association Database)
but for TCP connections: the session key material is installed into the kernel,
and the kernel handles encryption/decryption transparently to the application.

**This analogy breaks at:** IPsec operates on packets (L3); kTLS operates on
TLS records (L5/L6). IPsec has no concept of a TLS record header, sequence
numbers embedded in the IV, or record type bytes.

## 3.2 The Three-Layer Fallback Chain

```
kTLS FALLBACK CHAIN (evaluated at setup time, not per-packet)
══════════════════════════════════════════════════════════════

  Layer 0: NIC TLS Hardware Offload
  ───────────────────────────────────────────────────────────────
  What:    The NIC itself (mlx5, Intel ice/ixgbe) handles TLS
           encryption/decryption in hardware. Plaintext goes into
           TX ring, ciphertext comes out. On RX, ciphertext in,
           plaintext delivered to socket buffer.
  Kernel:  net/tls/tls_device.c
           tls_device_sendmsg() / tls_device_recv()
  When:    Driver advertises NETIF_F_HW_TLS_TX / NETIF_F_HW_TLS_RX
           AND cipher suite is supported by NIC
           AND NIC successfully programs the TLS context
  Fail:    If NIC context programming fails (key size mismatch,
           NIC queue full, cipher not supported) → drop to Layer 1
  ───────────────────────────────────────────────────────────────
            ↓ if NIC offload unavailable or programming fails
  ───────────────────────────────────────────────────────────────

  Layer 1: Kernel Software kTLS
  ───────────────────────────────────────────────────────────────
  What:    Kernel encrypts/decrypts using Linux Crypto API.
           The crypto implementation (AES-NI or software) is
           selected by the Crypto API priority system (Part II).
  Kernel:  net/tls/tls_sw.c
           tls_sw_sendmsg() / tls_sw_recvmsg()
  When:    TCP_ULP="tls" was attached AND setsockopt TLS_TX/RX
           programmed successfully
  Zero-copy: Kernel supports sendfile()/splice() for kTLS TX
             (data does not pass through userspace buffer)
  ───────────────────────────────────────────────────────────────
            ↓ if TCP_ULP not available or setsockopt fails
  ───────────────────────────────────────────────────────────────

  Layer 2: Userspace TLS (OpenSSL / rustls / etc.)
  ───────────────────────────────────────────────────────────────
  What:    TLS library in userspace handles everything.
           Every send/recv crosses the userspace/kernel boundary
           with ciphertext (TX) or ciphertext then decrypt (RX).
  When:    kTLS not available (older kernel < 4.13), cipher not
           supported by kTLS, or application doesn't opt in.
  ───────────────────────────────────────────────────────────────
```

## 3.3 `TCP_ULP`: Attaching the TLS Upper Layer Protocol

ULP (Upper Layer Protocol) is a kernel hook that allows a module to intercept
and modify the behavior of a TCP socket's send and receive paths. kTLS registers
itself as a ULP named `"tls"`.

```c
/*
 * Attaching kTLS as ULP.
 * This MUST happen BEFORE the TLS handshake completes in some configurations,
 * but in practice it's called AFTER the handshake since no keys are
 * programmed yet — it just installs the ULP hooks.
 *
 * After TCP_ULP is set:
 *   - sock->sk_prot is replaced with tls_base_prot (kTLS interceptor)
 *   - send/recv operations now go through kTLS code
 *   - cipher state is still unset: data falls through to normal TCP
 *     until TLS_TX/RX keys are programmed via SOL_TLS setsockopt
 */

int attach_ktls_ulp(int sockfd)
{
    /*
     * TCP_ULP = 31 (from include/uapi/linux/tcp.h)
     * SOL_TCP = IPPROTO_TCP = 6
     *
     * The string "tls" must match the name registered by the kTLS module:
     * net/tls/tls_main.c: tls_ulp_ops.name = "tls"
     *
     * ERROR CASES:
     *   ENOENT: CONFIG_TLS not enabled or tls.ko not loaded
     *   EEXIST: ULP already attached to this socket
     *   EINVAL: Socket is not a TCP socket, or not in ESTABLISHED state
     *   EBUSY:  Socket already has data in-flight
     */
    return setsockopt(sockfd, SOL_TCP, TCP_ULP, "tls", strlen("tls"));
}
```

## 3.4 Cipher Type Structures and Negotiation

After `TCP_ULP` is attached, program the session keys. The struct layout is
defined in `include/uapi/linux/tls.h`:

```c
/*
 * The base cipher info header — embedded at the start of every
 * tls12_crypto_info_* struct. The kernel uses this to dispatch
 * to the correct cipher handler.
 */
struct tls_crypto_info {
    __u16 version;      /* TLS_1_2_VERSION (0x0303) or TLS_1_3_VERSION (0x0304) */
    __u16 cipher_type;  /* TLS_CIPHER_AES_GCM_128, TLS_CIPHER_CHACHA20_POLY1305, etc. */
};
```

Wire layout of each cipher info struct:

```
TLS_CIPHER_AES_GCM_128  (kernel 4.13+, most common)
═══════════════════════════════════════════════════
struct tls12_crypto_info_aes_gcm_128:

Offset  Size  Field        Description
──────  ────  ──────────   ──────────────────────────────────────────────
 0      2     version      0x0303 (TLS 1.2) or 0x0304 (TLS 1.3)
 2      2     cipher_type  TLS_CIPHER_AES_GCM_128 = 51
 4      8     iv           TLS 1.2: explicit IV (sent on wire in record header)
                           TLS 1.3: not sent on wire; XOR'd with salt+seq
12      4     salt         4-byte fixed part of nonce (from key derivation)
16     16     key          AES-128 session key (16 bytes)
32      8     rec_seq      Record sequence number (starts at 0)
Total: 40 bytes

TLS_CIPHER_AES_GCM_256  (kernel 5.10+)
═══════════════════════════════════════
struct tls12_crypto_info_aes_gcm_256:

Offset  Size  Field        Description
──────  ────  ──────────   ──────────────────────────────────────────────
 0      2     version
 2      2     cipher_type  TLS_CIPHER_AES_GCM_256 = 52
 4      8     iv
12      4     salt
16     32     key          AES-256 session key (32 bytes)
48      8     rec_seq
Total: 56 bytes

TLS_CIPHER_CHACHA20_POLY1305  (kernel 5.11+)
════════════════════════════════════════════
struct tls12_crypto_info_chacha20_poly1305:

Offset  Size  Field        Description
──────  ────  ──────────   ──────────────────────────────────────────────
 0      2     version
 2      2     cipher_type  TLS_CIPHER_CHACHA20_POLY1305 = 54
 4     12     iv           12-byte nonce (no explicit IV for ChaCha20 in TLS)
16     32     key          ChaCha20 session key (32 bytes)
48      8     rec_seq
Total: 56 bytes

TLS_CIPHER_AES_CCM_128  (kernel 4.18+)
═══════════════════════════════════════
struct tls12_crypto_info_aes_ccm_128:

Offset  Size  Field        Description
──────  ────  ──────────   ──────────────────────────────────────────────
 0      2     version
 2      2     cipher_type  TLS_CIPHER_AES_CCM_128 = 53
 4      8     iv
12      4     salt
16     16     key
48      8     rec_seq
Total: 40 bytes
```

## 3.5 kTLS Setup: C Implementation After TLS Handshake

```c
/*
 * PRODUCTION CONTEXT: nginx/haproxy kTLS integration after TLS 1.3 handshake
 * CRATES (C equivalent): libssl (handshake), libc (setsockopt), kernel tls.h
 * PATTERN: Extract session keys after handshake, program into kernel
 * ANTI-PATTERN SHOWN: Programming kTLS before handshake completes
 */

#include <linux/tls.h>      /* tls12_crypto_info_aes_gcm_128, TLS_* constants */
#include <sys/socket.h>
#include <netinet/tcp.h>    /* TCP_ULP, SOL_TCP */
#include <string.h>
#include <errno.h>
#include <stdio.h>

/*
 * SOL_TLS: the socket level for TLS options.
 * Defined as 282 in include/linux/socket.h
 * Not in all system headers; define manually if needed.
 */
#ifndef SOL_TLS
#define SOL_TLS 282
#endif

/*
 * Attempt to offload a TLS session to the kernel (kTLS).
 *
 * Parameters come from the TLS library after handshake:
 *   - ssl_version: negotiated TLS version (TLS_1_2_VERSION or TLS_1_3_VERSION)
 *   - tx_key, tx_iv, tx_salt, tx_seq: TX (write) session keys
 *   - rx_key, rx_iv, rx_salt, rx_seq: RX (read) session keys
 *
 * Returns:
 *   0  = kTLS active (kernel now handles encrypt/decrypt)
 *  -1  = kTLS unavailable; caller must keep using userspace TLS
 */
int ktls_setup_aes_gcm_128(int sockfd, uint16_t ssl_version,
                             const uint8_t *tx_key, const uint8_t *tx_iv,
                             const uint8_t *tx_salt, const uint8_t *tx_seq,
                             const uint8_t *rx_key, const uint8_t *rx_iv,
                             const uint8_t *rx_salt, const uint8_t *rx_seq)
{
    struct tls12_crypto_info_aes_gcm_128 tx_info = {0};
    struct tls12_crypto_info_aes_gcm_128 rx_info = {0};
    int ret;

    /*
     * Step 1: Attach kTLS ULP to the socket.
     *
     * ANTI-PATTERN: Calling TCP_ULP after the handshake has sent data.
     * If the socket has data in the send queue, EBUSY is returned.
     * The correct pattern: TCP_ULP immediately after connect()/accept(),
     * before starting the handshake.
     */
    ret = setsockopt(sockfd, SOL_TCP, TCP_ULP, "tls", sizeof("tls") - 1);
    if (ret < 0) {
        if (errno == ENOENT) {
            fprintf(stderr, "kTLS: tls.ko not loaded or CONFIG_TLS=n\n");
        } else if (errno == EEXIST) {
            fprintf(stderr, "kTLS: ULP already attached\n");
        }
        return -1; /* Signal: use userspace TLS */
    }

    /*
     * Step 2: Program TX (send) cipher state.
     *
     * After this setsockopt:
     *   - write(sockfd, plaintext, len) → kernel encrypts → NIC sends ciphertext
     *   - sendfile(sockfd, filefd, ...) → kernel reads file, encrypts, NIC sends
     *     (zero-copy: file data never touches userspace)
     */
    tx_info.info.version     = ssl_version;
    tx_info.info.cipher_type = TLS_CIPHER_AES_GCM_128;
    memcpy(tx_info.iv,      tx_iv,   TLS_CIPHER_AES_GCM_128_IV_SIZE);   /* 8 bytes */
    memcpy(tx_info.salt,    tx_salt, TLS_CIPHER_AES_GCM_128_SALT_SIZE); /* 4 bytes */
    memcpy(tx_info.key,     tx_key,  TLS_CIPHER_AES_GCM_128_KEY_SIZE);  /* 16 bytes */
    memcpy(tx_info.rec_seq, tx_seq,  TLS_CIPHER_AES_GCM_128_REC_SEQ_SIZE); /* 8 bytes */

    ret = setsockopt(sockfd, SOL_TLS, TLS_TX, &tx_info, sizeof(tx_info));
    if (ret < 0) {
        fprintf(stderr, "kTLS: TLS_TX setup failed: %s\n", strerror(errno));
        /* kTLS ULP is now attached but not active.
         * TLS library must handle TX itself via BIO/send callbacks. */
        return -1;
    }

    /*
     * Step 3: Program RX (receive) cipher state. (Kernel 4.17+)
     *
     * After this setsockopt:
     *   - read(sockfd, buf, len) → kernel receives ciphertext, decrypts → plaintext in buf
     *   - If decryption fails (bad MAC): EBADMSG returned to read()
     *   - Alert records: returned via cmsg with type TLS_GET_RECORD_TYPE
     */
    rx_info.info.version     = ssl_version;
    rx_info.info.cipher_type = TLS_CIPHER_AES_GCM_128;
    memcpy(rx_info.iv,      rx_iv,   TLS_CIPHER_AES_GCM_128_IV_SIZE);
    memcpy(rx_info.salt,    rx_salt, TLS_CIPHER_AES_GCM_128_SALT_SIZE);
    memcpy(rx_info.key,     rx_key,  TLS_CIPHER_AES_GCM_128_KEY_SIZE);
    memcpy(rx_info.rec_seq, rx_seq,  TLS_CIPHER_AES_GCM_128_REC_SEQ_SIZE);

    ret = setsockopt(sockfd, SOL_TLS, TLS_RX, &rx_info, sizeof(rx_info));
    if (ret < 0) {
        fprintf(stderr, "kTLS: TLS_RX setup failed: %s\n", strerror(errno));
        /* Can have TX offload but not RX offload. This is valid. */
        /* In this case: TX goes through kernel, RX goes through userspace TLS. */
        return 1; /* partial kTLS: TX only */
    }

    /*
     * After both TX and RX are set:
     * The kernel now fully owns the record layer for this connection.
     * The TLS library in userspace must NOT encrypt/decrypt — just pass
     * plaintext to write() and read plaintext from read().
     *
     * Key material in tx_info/rx_info is on the stack; it will be
     * zeroed when this function returns (see zeroize discussion in Part IX).
     * The kernel has made its own copy of the key material.
     */
    memset(&tx_info, 0, sizeof(tx_info)); /* zero key material on stack */
    memset(&rx_info, 0, sizeof(rx_info));

    return 0; /* full kTLS active */
}

/*
 * Cipher negotiation fallback: try ciphers in preference order.
 * This mirrors what a TLS library's cipher preference list does,
 * but at the kTLS programming stage.
 */
int ktls_setup_with_fallback(int sockfd, uint16_t ssl_version,
                              uint16_t negotiated_cipher,
                              const void *tx_crypto_info, size_t tx_len,
                              const void *rx_crypto_info, size_t rx_len)
{
    /* Attach ULP first */
    if (setsockopt(sockfd, SOL_TCP, TCP_ULP, "tls", 3) < 0)
        return -1;

    /*
     * Try the negotiated cipher. If it fails (e.g., kernel too old
     * for ChaCha20-Poly1305, or AES-GCM-256 not supported), the
     * TLS session must be re-negotiated with a different cipher —
     * kTLS cannot change the cipher mid-connection.
     *
     * This is the fundamental constraint: the cipher is locked in
     * at TLS handshake time. kTLS cannot change it.
     */
    if (setsockopt(sockfd, SOL_TLS, TLS_TX, tx_crypto_info, tx_len) < 0 ||
        setsockopt(sockfd, SOL_TLS, TLS_RX, rx_crypto_info, rx_len) < 0) {
        return -1; /* must fall back to userspace TLS */
    }
    return 0;
}
```

## 3.6 NIC TLS Offload: The Deepest Fallback Layer

NIC TLS offload (supported by Mellanox/NVIDIA ConnectX-5/6, Intel ice, etc.)
moves even more of the TLS processing off the CPU:

```
NIC TLS OFFLOAD ARCHITECTURE
═══════════════════════════════════════════════════════════════════════

  TX PATH with NIC offload:
  ─────────────────────────
  Application writes plaintext
         ↓
  write(fd, plaintext, len)
         ↓
  kTLS TX ULP hook intercepts
         ↓
  tls_device_sendmsg() [net/tls/tls_device.c]
         ↓
  TLS record header prepended in skb (socket buffer)
         ↓
  skb passed to driver (mlx5e_xmit)
         ↓
  NIC hardware: adds sequence number to nonce,
                encrypts payload in SRAM,
                computes GCM authentication tag
         ↓
  Encrypted packet out on wire
  (CPU never touched plaintext→ciphertext conversion)

  RX PATH with NIC offload:
  ─────────────────────────
  Encrypted packet arrives at NIC
         ↓
  NIC hardware: strips TLS record header,
                verifies GCM tag (discards if bad),
                decrypts payload in SRAM
         ↓
  Plaintext DMA'd to socket buffer
         ↓
  read() returns plaintext to application
  (CPU never saw ciphertext)

  FALLBACK TRIGGER (NIC offload → kernel SW kTLS):
  ─────────────────────────────────────────────────
  1. NIC does not support the negotiated cipher (e.g., no ChaCha20 in HW)
  2. All NIC TLS context slots are in use (finite HW resource)
  3. TCP retransmit with different sequence number than NIC expected
     → NIC offload disabled for that connection, kTLS SW takes over
  4. Connection migrates to different NIC queue
```

Checking NIC TLS offload capability:

```bash
# Check if NIC supports TLS offload
ethtool -k eth0 | grep tls
# tls-hw-tx-offload: on
# tls-hw-rx-offload: on

# Disable NIC TLS offload (force kernel SW kTLS):
ethtool -K eth0 tls-hw-tx-offload off

# Monitor kTLS statistics:
cat /proc/net/tls_stat
# TlsCurrTxSw          42    ← connections using kernel SW kTLS TX
# TlsCurrRxSw          38    ← connections using kernel SW kTLS RX
# TlsCurrTxDevice       8    ← connections using NIC HW offload TX
# TlsCurrRxDevice       6    ← connections using NIC HW offload RX
# TlsTxSoftware       120    ← cumulative SW kTLS TX connections
# TlsRxSoftware       115
# TlsDecryptError      3     ← decryption failures (bad MAC)
# TlsRxDeviceResync    5     ← resync events (NIC offload recovery)
```

---

# Part IV: XFRM / IPsec

## 4.1 Mental Model: The Security Association Database as a Crypto Policy Engine

XFRM is the Linux kernel's framework for packet-level security transforms.
It implements IPsec (ESP, AH, IPCOMP) and is the kernel component that IKE
daemons (strongSwan, libreswan, racoon) program after completing IKEv2/IKEv1
negotiation with a remote peer.

**Analogy:** XFRM is to packets what kTLS is to TCP streams. kTLS holds
session keys and transforms TCP payloads. XFRM holds SA (Security Association)
keys and transforms IP packets. Both use the Linux Crypto API for the actual
cryptographic operations. Both can be hardware-offloaded to a NIC.

**Two databases:**
- **SAD (Security Association Database):** "For packets matching THIS SPI and
  destination IP, apply THIS transform (ESP encrypt+authenticate) using THIS key."
- **SPD (Security Policy Database):** "For packets matching THIS selector
  (src/dst IP, port, protocol), apply THIS action (IPSEC/DISCARD/BYPASS)
  using an SA from the SAD."

**This analogy breaks at:** kTLS operates on a single persistent TCP connection.
XFRM operates on individual packets and has no connection state — the same SA
(identified by SPI + destination IP) can be applied to millions of packets from
many different connections.

## 4.2 XFRM Architecture

```
XFRM ARCHITECTURE
══════════════════════════════════════════════════════════════════════

  IKEv2 Daemon (strongSwan)         Network Interface
  ─────────────────────────         ─────────────────
  1. Negotiates with peer:
     - Cipher: AES-256-GCM
     - Auth: integrated (AEAD)
     - Key lifetime: 3600s
     - SPI: 0xdeadbeef
  2. Derives keys (DH + PRF)
  3. Programs kernel via Netlink:
     XFRM_MSG_NEWSA    ──────────────────────────────────┐
     XFRM_MSG_NEWPOLICY ─────────────────────────────┐  │
                                                      │  │
                                                      ▼  ▼
  ┌─────────────────────────────────────────────────────────────────┐
  │                        XFRM CORE                                │
  │                    net/xfrm/xfrm_state.c                        │
  │                    net/xfrm/xfrm_policy.c                       │
  │                                                                 │
  │  SPD (Security Policy Database)                                 │
  │  ┌──────────────────────────────────────────────────────────┐  │
  │  │ Policy: src=10.0.0.0/8 → dst=192.168.1.0/24             │  │
  │  │         direction=OUT, action=IPSEC                      │  │
  │  │         tmpl: proto=ESP, mode=TUNNEL                     │  │
  │  └──────────────────────────────────────────────────────────┘  │
  │                           │                                     │
  │                           │ policy match → SA lookup            │
  │                           ▼                                     │
  │  SAD (Security Association Database)                            │
  │  ┌──────────────────────────────────────────────────────────┐  │
  │  │ SA: spi=0xdeadbeef, dst=192.168.1.1                      │  │
  │  │     proto=ESP, mode=TUNNEL                               │  │
  │  │     encr: rfc4106(gcm(aes)), key=<256-bit>, keylen=256   │  │
  │  │     crypto_aead *tfm  ← Linux Crypto API transform       │  │
  │  │     replay_window: 64 packets, bitmap: <current state>   │  │
  │  │     lifetime: bytes=<count>, time=<expiry>               │  │
  │  └──────────────────────────────────────────────────────────┘  │
  │                           │                                     │
  │                           │ apply transform                     │
  │                           ▼                                     │
  │  Transform Engines:                                             │
  │  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐   │
  │  │  ESP (xfrm4_   │  │  AH (xfrm4_   │  │  IPCOMP (xfrm4_│   │
  │  │  esp_output)   │  │  ah_output)   │  │  ipcomp_output) │   │
  │  │  net/ipv4/     │  │  net/ipv4/    │  │  net/ipv4/     │   │
  │  │  esp4.c        │  │  ah4.c        │  │  ipcomp.c      │   │
  │  └────────────────┘  └────────────────┘  └────────────────┘   │
  └─────────────────────────────────────────────────────────────────┘
                           │
                           ▼ uses
  ┌─────────────────────────────────────────────────────────────────┐
  │              Linux Crypto API                                    │
  │  "rfc4106(gcm(aes))" → picks AES-NI GCM (priority 400)        │
  └─────────────────────────────────────────────────────────────────┘
```

## 4.3 The `xfrm_state` and Algorithm Structures

```c
/*
 * include/net/xfrm.h (simplified)
 *
 * struct xfrm_state is the kernel's Security Association (SA).
 * One SA = one directional key material for one transform type
 * to one remote IP with one SPI.
 */
struct xfrm_state {
    /* Identity: how packets are matched to this SA */
    xfrm_address_t          id.daddr;    /* destination address */
    __be32                  id.spi;      /* Security Parameter Index */
    __u8                    id.proto;    /* IPPROTO_ESP / IPPROTO_AH */

    /* Cipher algorithm for encryption (ESP only) */
    struct xfrm_algo_aead  *aead;        /* for AEAD (GCM, CCM, ChaCha20) */
    struct xfrm_algo       *ealg;        /* for non-AEAD encryption (CBC) */
    struct xfrm_algo_auth  *aalg;        /* for authentication (HMAC-SHA256) */
    struct xfrm_algo       *calg;        /* for compression (IPCOMP) */

    /* The actual crypto transforms (Linux Crypto API handles) */
    struct crypto_aead     *data;        /* AEAD transform (for GCM mode) */
    /* For non-AEAD: individual skcipher + ahash transforms */

    /* Replay protection */
    struct xfrm_replay_state_esn *replay_esn;

    /* Lifetime tracking */
    struct xfrm_lifetime_cfg lft;       /* configured lifetime */
    struct xfrm_lifetime_cur curlft;    /* current usage */

    /* Hardware offload (NIC IPsec offload) */
    struct xfrm_dev_offload xso;        /* NIC offload context */

    struct net              *net;
    spinlock_t              lock;
    atomic_t                refcnt;
};

/*
 * struct xfrm_algo: algorithm descriptor passed from userspace (IKE daemon)
 * via Netlink XFRM message.
 */
struct xfrm_algo {
    char    alg_name[64];       /* algorithm name: "cbc(aes)", "sha256", etc. */
    unsigned int alg_key_len;   /* key length in BITS (not bytes) */
    char    alg_key[0];         /* the actual key material, variable length */
};

struct xfrm_algo_aead {
    char    alg_name[64];       /* "rfc4106(gcm(aes))" */
    unsigned int alg_key_len;   /* in bits: 160 = 128-bit key + 32-bit salt */
    unsigned int alg_icv_len;   /* ICV (tag) length in bits: 64, 96, or 128 */
    char    alg_key[0];
};

struct xfrm_algo_auth {
    char    alg_name[64];       /* "hmac(sha256)", "hmac(sha1)" */
    unsigned int alg_key_len;   /* in bits */
    unsigned int alg_trunc_len; /* truncation length in bits: 96, 128, 256 */
    char    alg_key[0];
};
```

## 4.4 Algorithm Negotiation: IKEv2 → Kernel

IKEv2 negotiates cipher suites in the IKE_SA_INIT and CREATE_CHILD_SA
exchanges. Here is the complete flow from wire negotiation to kernel SA
programming:

```
IKEv2 ALGORITHM NEGOTIATION FLOW
══════════════════════════════════════════════════════════════════════

  Initiator                                    Responder
  (strongSwan)                                 (strongSwan)
  ─────────────                                ─────────────
  IKE_SA_INIT (UDP port 500):
    PROPOSAL 1:
      - Encryption: AES-GCM-256 (ESN)
      - PRF: HMAC-SHA-512
      - DH: ECDH P-256
    PROPOSAL 2:
      - Encryption: AES-CBC-128
      - Auth: HMAC-SHA-256-128
      - PRF: HMAC-SHA-256
      - DH: ECDH P-256
    PROPOSAL 3:
      - Encryption: AES-CBC-128
      - Auth: HMAC-SHA-1-96
      - PRF: HMAC-SHA-1
      - DH: MODP-2048                ─────────────────────────────────►
                                     Responder:
                                     1. Checks each proposal against
                                        what it supports
                                     2. Calls crypto_has_aead("rfc4106(gcm(aes))")
                                        → 1 (available) → picks Proposal 1
                                     3. Runs DH, generates nonce
                                                         ◄───────────────
  IKE_AUTH / CREATE_CHILD_SA:
  Both sides derive keys using PRF:
    SK_ei = PRF+(SK_d, "Child SA" || Ni || Nr)
    SK_er = ...
    SK_ai = ... (only for non-AEAD)
    SK_ar = ...

  Initiator programs kernel:
  XFRM_MSG_NEWSA:
    id.spi   = 0xdeadbeef
    id.proto = IPPROTO_ESP
    id.daddr = 10.0.0.2
    aead:
      alg_name = "rfc4106(gcm(aes))"
      alg_key_len = 288  (256 bits key + 32 bits salt)
      alg_key  = SK_ei || salt
    mode = XFRM_MODE_TUNNEL

  Kernel receives XFRM_MSG_NEWSA:
  ─────────────────────────────────────────────────────────────
  xfrm_add_sa()
    → xfrm_init_algo(x, attrs)
      → x->aead = kmalloc(sizeof(*x->aead) + key_len, ...)
        copy alg_name "rfc4106(gcm(aes))"
        copy key material
      → xfrm_algo_desc_find("rfc4106(gcm(aes))")
        → Looks in net/xfrm/xfrm_algo.c:aead_list[]
        → Found: { .name="rfc4106(gcm(aes))", .pfkey_supported=1 }
        → Probes: crypto_has_aead("rfc4106(gcm(aes))", 0, CRYPTO_ALG_ASYNC)
        → If 0: return -ENOSYS to IKE daemon → daemon must try next proposal
        → If 1: continue
      → x->data = crypto_alloc_aead("rfc4106(gcm(aes))", 0, 0)
        → Linux Crypto API allocates highest-priority implementation
      → crypto_aead_setkey(x->data, key, key_len_bytes)
      → crypto_aead_setauthsize(x->data, icv_len_bytes)
    → xfrm_state_add(x) → added to SAD
```

## 4.5 Algorithm Table: XFRM Algorithm Descriptors

```c
/*
 * net/xfrm/xfrm_algo.c — the canonical list of XFRM-supported algorithms
 *
 * This is THE authoritative mapping between IKEv2 algorithm IDs,
 * PFKEY algorithm IDs, and Linux Crypto API names.
 * If an algorithm is not in this table, XFRM will not use it
 * even if the Linux Crypto API supports it.
 */

/* AEAD algorithms (encryption + authentication combined) */
static struct xfrm_algo_desc aead_list[] = {
    {
        .name = "rfc4106(gcm(aes))",      /* IKEv2 name: AES-GCM */
        .uinfo = { .aead = { .icv_truncbits = 128 } },
        .pfkey_supported = 1,
        .desc = {
            .sadb_alg_id    = SADB_X_EALG_AES_GCM_ICV16,
            .sadb_alg_ivlen = 8,          /* 8-byte explicit IV in ESP header */
            .sadb_alg_minbits = 128,      /* minimum key size: 128-bit AES */
            .sadb_alg_maxbits = 256,      /* maximum key size: 256-bit AES */
        }
    },
    {
        .name = "rfc4543(gcm(aes))",      /* GMAC: auth-only, no encryption */
        .uinfo = { .aead = { .icv_truncbits = 128 } },
        .pfkey_supported = 1,
        .desc = {
            .sadb_alg_id    = SADB_X_EALG_AES_GMAC,
            .sadb_alg_ivlen = 8,
            .sadb_alg_minbits = 128,
            .sadb_alg_maxbits = 256,
        }
    },
    {
        .name = "rfc7539esp(chacha20,poly1305)", /* ChaCha20-Poly1305 for IPsec */
        .uinfo = { .aead = { .icv_truncbits = 128 } },
        .pfkey_supported = 0,             /* PFKEY not supported; Netlink only */
    },
};

/* Encryption algorithms (for ESP with separate authentication) */
static struct xfrm_algo_desc ealg_list[] = {
    {
        .name = "cbc(aes)",               /* AES-CBC for ESP */
        .uinfo = { .encr = { .defkeybits = 128 } },
        .pfkey_supported = 1,
        .desc = {
            .sadb_alg_id    = SADB_X_EALG_AESCBC,
            .sadb_alg_ivlen = 8,          /* 8-byte IV */
            .sadb_alg_minbits = 128,
            .sadb_alg_maxbits = 256,
        }
    },
    {
        .name = "cbc(des3_ede)",           /* 3DES-CBC (legacy) */
        .uinfo = { .encr = { .defkeybits = 192 } },
        .pfkey_supported = 1,
        .desc = {
            .sadb_alg_id    = SADB_EALG_3DESCBC,
            .sadb_alg_ivlen = 8,
            .sadb_alg_minbits = 192,
            .sadb_alg_maxbits = 192,
        }
    },
    /* Note: NULL encryption (SADB_EALG_NULL) is also supported
     * for authentication-only ESP (unusual but spec-compliant) */
};

/* Authentication algorithms (for ESP or AH with separate cipher) */
static struct xfrm_algo_desc aalg_list[] = {
    {
        .name = "hmac(sha256)",            /* HMAC-SHA-256-128 (truncated) */
        .uinfo = { .auth = { .icv_truncbits = 128, .icv_fullbits = 256 } },
        .pfkey_supported = 1,
        .desc = {
            .sadb_alg_id    = SADB_X_AALG_SHA2_256HMAC,
            .sadb_alg_ivlen = 0,
            .sadb_alg_minbits = 256,
            .sadb_alg_maxbits = 256,
        }
    },
    {
        .name = "hmac(sha512)",
        .uinfo = { .auth = { .icv_truncbits = 256, .icv_fullbits = 512 } },
        .pfkey_supported = 1,
        .desc = {
            .sadb_alg_id    = SADB_X_AALG_SHA2_512HMAC,
        }
    },
    {
        .name = "hmac(sha1)",              /* HMAC-SHA-1-96 (legacy) */
        .uinfo = { .auth = { .icv_truncbits = 96, .icv_fullbits = 160 } },
        .pfkey_supported = 1,
        .desc = {
            .sadb_alg_id    = SADB_AALG_SHA1HMAC,
        }
    },
    /* xcbc(aes), cmac(aes) also in the list for RFC 4434 */
};
```

## 4.6 Programming an SA via Netlink XFRM (C)

```c
/*
 * PRODUCTION CONTEXT: IKEv2 daemon post-negotiation kernel programming
 * This is what strongSwan/libreswan do after completing the IKE handshake.
 *
 * WARNING: This is the RAW netlink interface. In production, use
 * libxfrm (part of libipsec), or the ip-xfrm(8) utility calls this
 * with the xfrmnl_sa_* API.
 */

#include <linux/xfrm.h>
#include <linux/netlink.h>
#include <linux/rtnetlink.h>
#include <string.h>
#include <sys/socket.h>
#include <unistd.h>

#define XFRM_KEY_LEN_BYTES   32    /* AES-256 = 32 bytes */
#define XFRM_SALT_LEN_BYTES  4     /* RFC 4106 salt = 4 bytes */
#define XFRM_TOTAL_KEY_BYTES (XFRM_KEY_LEN_BYTES + XFRM_SALT_LEN_BYTES)

/* Netlink message layout for XFRM_MSG_NEWSA */
struct xfrm_newsa_req {
    struct nlmsghdr  nlh;
    struct xfrm_usersa_info sa;          /* core SA parameters */

    /* rtattr for XFRMA_ALG_AEAD */
    struct rtattr    alg_aead_rta;
    struct xfrm_algo_aead alg_aead;
    uint8_t          key_data[XFRM_TOTAL_KEY_BYTES]; /* key + salt */
};

int add_ipsec_sa(int nl_fd,
                 uint32_t spi,           /* SPI in network byte order */
                 const struct in6_addr *dst,
                 const uint8_t *key,     /* 32-byte AES-256 key */
                 const uint8_t *salt)    /* 4-byte salt */
{
    struct xfrm_newsa_req req = {0};
    struct sockaddr_nl addr = { .nl_family = AF_NETLINK };

    /* Netlink header */
    req.nlh.nlmsg_type  = XFRM_MSG_NEWSA;
    req.nlh.nlmsg_flags = NLM_F_REQUEST | NLM_F_CREATE | NLM_F_EXCL;
    req.nlh.nlmsg_seq   = 1;
    req.nlh.nlmsg_len   = sizeof(req);

    /* SA identity */
    req.sa.id.proto     = IPPROTO_ESP;
    req.sa.id.spi       = spi;          /* htonl(0xdeadbeef) */
    memcpy(&req.sa.id.daddr.a6, dst, sizeof(*dst));

    /* SA parameters */
    req.sa.family       = AF_INET6;
    req.sa.mode         = XFRM_MODE_TUNNEL;
    req.sa.replay_window = 64;

    /* Algorithm: AES-256-GCM via RFC 4106 */
    req.alg_aead_rta.rta_type = XFRMA_ALG_AEAD;
    req.alg_aead_rta.rta_len  = RTA_LENGTH(sizeof(req.alg_aead)
                                             + XFRM_TOTAL_KEY_BYTES);

    /* alg_name must match EXACTLY an entry in net/xfrm/xfrm_algo.c:aead_list */
    strncpy(req.alg_aead.alg_name, "rfc4106(gcm(aes))",
            sizeof(req.alg_aead.alg_name) - 1);

    req.alg_aead.alg_key_len = (XFRM_KEY_LEN_BYTES + XFRM_SALT_LEN_BYTES) * 8;
    /* Note: alg_key_len is in BITS, and includes the salt.
     * RFC 4106 key format: [AES key bytes][4-byte salt]
     * Total: 32 + 4 = 36 bytes = 288 bits for AES-256-GCM */

    req.alg_aead.alg_icv_len  = 128;   /* 128-bit GCM authentication tag */

    /* Copy key material: key bytes then salt bytes */
    memcpy(req.key_data, key, XFRM_KEY_LEN_BYTES);
    memcpy(req.key_data + XFRM_KEY_LEN_BYTES, salt, XFRM_SALT_LEN_BYTES);

    /* Send to kernel */
    int ret = sendto(nl_fd, &req, sizeof(req), 0,
                     (struct sockaddr *)&addr, sizeof(addr));

    /* MANDATORY: zero key material from stack before returning */
    memset(&req, 0, sizeof(req));

    return ret < 0 ? -1 : 0;
}
```

## 4.7 XFRM Algorithm Fallback: IKE-Level Retry

The kernel itself does not "fall back" to a weaker algorithm if the requested
one is unavailable — it returns an error. The IKE daemon is responsible for
proposal ordering and retry:

```
IKE FALLBACK SEQUENCE
══════════════════════════════════════════════════════════════════════

  IKE Daemon (strongSwan) algorithm probe sequence at startup:
  ─────────────────────────────────────────────────────────────
  strongSwan calls: kernel_ipsec_get_features()
  → Issues XFRM_MSG_GETSA probe or uses /proc/crypto
  → Builds list of available algorithms

  Result: builds ordered proposal list (strongest first):
    PROPOSAL 1: AES-256-GCM  (if kernel has rfc4106(gcm(aes)) with 256-bit)
    PROPOSAL 2: AES-128-GCM  (if kernel has rfc4106(gcm(aes)) with 128-bit)
    PROPOSAL 3: AES-256-CBC + HMAC-SHA-256 (if kernel has cbc(aes) + hmac(sha256))
    PROPOSAL 4: AES-128-CBC + HMAC-SHA-256
    PROPOSAL 5: 3DES-CBC + HMAC-SHA-1 (last resort, legacy)

  After IKEv2 negotiation selects, say, AES-256-GCM:
  → IKE calls: kernel_ipsec_add_sa(AES-256-GCM, SPI, key)
  → Kernel issues: crypto_alloc_aead("rfc4106(gcm(aes))", 0, 0)
  → If IS_ERR: kernel returns -ENOSYS to XFRM_MSG_NEWSA
  → IKE receives NLMSG_ERROR with -ENOSYS
  → IKE logs error, falls back to next proposal
  → IKE restarts CREATE_CHILD_SA with PROPOSAL 3

  Key insight: The fallback happens at the IKE level (userspace),
  NOT at the kernel level. The kernel simply refuses an unsupported
  algorithm and returns an error code.
```

---

# Part V: TCP-Level Option Negotiation

## 5.1 Mental Model: Capability Advertisement in SYN Packets

TCP option negotiation is purely in-kernel, invisible to applications.
Options are advertised in SYN (initiator) and SYN-ACK (responder) packets.
Both sides enable an option only if both advertised it. The kernel TCP stack
handles this during the three-way handshake; by the time `connect()` returns
or `accept()` returns, the negotiated options are locked in for the connection.

## 5.2 TCP Option Wire Format

```
TCP HEADER WITH OPTIONS
0                   1                   2                   3
0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|          Source Port          |       Destination Port        |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                        Sequence Number                        |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                    Acknowledgment Number                      |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|  Data |       |C|E|U|A|P|R|S|F|                               |
| Offset|  Rsv  |W|C|R|C|S|S|Y|I|           Window             |
|       |       |R|E|G|K|H|T|N|N|                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|           Checksum            |         Urgent Pointer        |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                           OPTIONS                             |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

OPTION FORMAT (generic):
+---------+----------+---------...----------+
| Kind(1B)| Length(1B)| Data (Length-2 bytes)|
+---------+----------+---------...----------+

SINGLE-BYTE OPTIONS (no length field):
  0x00 = End of Option List (EOL)
  0x01 = No-Operation (NOP, for alignment padding)

KEY OPTIONS AND THEIR NEGOTIATION:
══════════════════════════════════

Kind  Name              Size  Negotiation Rule
────  ────────────────  ────  ─────────────────────────────────────────────
  2   Maximum Segment   4B    SYN only; each side advertises its own MSS.
      Size (MSS)              Path MSS = min(sender_MSS, receiver_MSS).
                              Default if absent: 536 bytes (RFC 879).

  3   Window Scale      3B    SYN and SYN-ACK only; must be in both.
      (WSCALE)                Scale factor: 0-14. Receive window is
                              window_field * 2^scale. If either side omits
                              it from SYN, no scaling is used for session.

  4   SACK Permitted    2B    SYN and SYN-ACK only; presence in both SYNs
                              enables SACK for the connection.
                              SACK (kind=5) can then appear in ACKs.

  8   Timestamps        10B   SYN and SYN-ACK; enables RTT measurement
      (TSopt)                 and PAWS (Protection Against Wrapped Sequences).
                              RFC 7323. Enabled by default on Linux.

 34   TCP Fast Open     var   SYN: client sends cookie request or cookie.
      (TFO)                   SYN-ACK: server sends cookie (first req) or
                              processes data with cookie (subsequent reqs).
                              Kernel: net.ipv4.tcp_fastopen (bitmask).

 30   MPTCP             var   SYN: MP_CAPABLE option. Subflow negotiation
      (Multipath TCP)         via MP_JOIN. Kernel 5.6+.

 253  Experimental /    var   Used for TCP-AO (Authentication Option,
      TCP-AO                  RFC 5925), replacing TCP-MD5.
```

## 5.3 TCP Option Negotiation in the Kernel

```c
/*
 * net/ipv4/tcp_output.c — how the kernel writes options into SYN packets
 *
 * tcp_syn_options() builds the options for the outgoing SYN.
 * Each option is only included if the global sysctl enables it.
 */

/* Relevant sysctls for option negotiation: */

// /proc/sys/net/ipv4/tcp_sack       (default: 1 = enabled)
// /proc/sys/net/ipv4/tcp_timestamps (default: 1 = enabled)
// /proc/sys/net/ipv4/tcp_window_scaling (default: 1 = enabled)
// /proc/sys/net/ipv4/tcp_fastopen   (bitmask: 0x1=client, 0x2=server, 0x4=no cookies)
// /proc/sys/net/ipv4/tcp_ecn        (0=disabled, 1=request ECN, 2=always negotiate)
// /proc/ipv4/tcp_mtu_probing        (0=disabled, 1=enabled when black hole detected)

/*
 * Checking negotiated options on an established connection:
 */
#include <linux/tcp.h>

/* From application: query TCP_INFO for negotiated state */
struct tcp_info info;
socklen_t info_len = sizeof(info);
getsockopt(sockfd, IPPROTO_TCP, TCP_INFO, &info, &info_len);

/* Check what was actually negotiated: */
printf("SACK enabled: %d\n",  info.tcpi_options & TCPI_OPT_SACK);
printf("Timestamps:   %d\n",  info.tcpi_options & TCPI_OPT_TIMESTAMPS);
printf("ECN:          %d\n",  info.tcpi_options & TCPI_OPT_ECN);
printf("WScale Snd:   %d\n",  info.tcpi_snd_wscale);
printf("WScale Rcv:   %d\n",  info.tcpi_rcv_wscale);
```

## 5.4 TCP Congestion Control: A Different Kind of Negotiation

Congestion control is NOT negotiated between endpoints — each end uses its
own independently. The kernel selects the algorithm at connection setup:

```bash
# List available congestion control algorithms:
cat /proc/sys/net/ipv4/tcp_available_congestion_control
# Output: reno cubic bbr westwood

# Set default for new connections:
sysctl -w net.ipv4.tcp_congestion_control=bbr

# Per-connection override (requires CAP_NET_ADMIN or SO_PRIORITY):
setsockopt(fd, IPPROTO_TCP, TCP_CONGESTION, "bbr", strlen("bbr"));

# Allowed list (non-root can only choose from this list):
cat /proc/sys/net/ipv4/tcp_allowed_congestion_control
# reno cubic
```

The fallback: if a requested algorithm is not compiled in, `setsockopt` returns
`ENOENT`, and the connection falls back to the system default.

---

# Part VI: IPv4/IPv6 Protocol Fallback

## 6.1 Dual-Stack Socket Architecture

```
DUAL-STACK SOCKET BEHAVIOR
══════════════════════════════════════════════════════════════════════

  socket(AF_INET6, SOCK_STREAM, 0)
  ─────────────────────────────────
  Creates an IPv6 socket that CAN accept IPv4 connections
  via IPv4-mapped IPv6 addresses (::ffff:1.2.3.4).

  setsockopt(fd, IPPROTO_IPV6, IPV6_V6ONLY, &one, sizeof(one))
  ─────────────────────────────────────────────────────────────
  DISABLES dual-stack: socket accepts ONLY IPv6 connections.
  Default: system-dependent (/proc/sys/net/ipv6/bindv6only)
           Linux default: 0 (dual-stack enabled)

  DUAL-STACK BINDING:
  bind(fd, AF_INET6, IN6ADDR_ANY, port)
  → Binds to [::]:port
  → Accepts both IPv6 connections and IPv4 via ::ffff:x.x.x.x

  IPv4-mapped address representation:
  0                   1                   2                   3
  0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  |                        all zeros (80 bits)                     |
  +                               +-------------------------------+
  |                               |      0xFFFF (16 bits)         |
  +-------------------------------+-------------------------------+
  |              IPv4 address (32 bits)                           |
  +---------------------------------------------------------------+
```

## 6.2 The `getaddrinfo()` Fallback Chain

Modern applications don't handle IP version selection directly; they use
`getaddrinfo()` which returns an ordered list, and the application tries each:

```c
/*
 * Standard connection with dual-stack fallback.
 * This is what curl, nginx, and most modern servers do.
 *
 * RFC 8305 (Happy Eyeballs v2) recommends racing IPv6 and IPv4
 * with a 250ms delay, preferring IPv6. This is implemented in
 * browsers and some libraries, but the kernel provides no specific
 * support — it's purely userspace logic.
 */

#include <sys/types.h>
#include <sys/socket.h>
#include <netdb.h>

int connect_with_fallback(const char *host, const char *port)
{
    struct addrinfo hints = {
        .ai_family   = AF_UNSPEC,       /* accept IPv4 or IPv6 */
        .ai_socktype = SOCK_STREAM,
        .ai_flags    = AI_ADDRCONFIG,   /* only return IPv6 if IPv6 configured */
    };
    struct addrinfo *result, *rp;

    if (getaddrinfo(host, port, &hints, &result) != 0)
        return -1;

    /*
     * getaddrinfo returns addresses in RFC 3484 / RFC 6724 preference order:
     *   1. IPv6 global unicast (if available)
     *   2. IPv4-mapped IPv6 (::ffff:x.x.x.x)
     *   3. IPv6 link-local
     *   4. IPv4 global
     *   5. etc.
     *
     * The kernel's glibc sorts this list according to the policy table
     * in /etc/gai.conf (or the compiled-in defaults).
     */
    int fd = -1;
    for (rp = result; rp != NULL; rp = rp->ai_next) {
        fd = socket(rp->ai_family, rp->ai_socktype, rp->ai_protocol);
        if (fd < 0)
            continue;           /* this address family not available */

        if (connect(fd, rp->ai_addr, rp->ai_addrlen) == 0)
            break;              /* success */

        close(fd);
        fd = -1;
        /* failure: try next address (possibly different IP version) */
    }

    freeaddrinfo(result);
    return fd;  /* -1 if all failed */
}

/*
 * KERNEL ROLE IN IPv6/IPv4 FALLBACK:
 * The kernel handles the actual socket creation and routing.
 * If IPv6 is not configured (no global address), AF_INET6 sockets
 * still work for loopback (::1) and link-local, but routing fails
 * for global addresses → connect() returns ENETUNREACH → app tries IPv4.
 *
 * The kernel sets EAFNOSUPPORT if IPv6 is completely disabled
 * (CONFIG_IPV6=n or ipv6.disable=1 boot param) → getaddrinfo()
 * with AI_ADDRCONFIG will not return IPv6 addresses in that case.
 */
```

---

# Part VII: Application Protocol Version Negotiation

## 7.1 NFS Version Negotiation

NFSv4 has a MINOR version negotiation mechanism within the NFSv4 family.
The initial probe uses `EXCHANGE_ID` (NFSv4.1+) or `SETCLIENTID` (NFSv4.0):

```
NFS VERSION SELECTION FLOW
══════════════════════════════════════════════════════════════════════

  mount -t nfs server:/export /mnt
  (no nfsvers= specified → kernel picks highest supported)
       │
       ▼
  nfs_get_tree() [fs/nfs/super.c]
  → nfs_try_get_tree() tries versions in order:
       │
       ├─ Try NFSv4.2:
       │    nfs4_discover_server_trunking() with minor_version=2
       │    RPC CALL: EXCHANGE_ID {
       │        client_owner = <unique client string>,
       │        flags = EXCHGID4_FLAG_USE_PNFS_MDS,
       │        state_protect = SP4_NONE,
       │        client_impl_id = { "Linux NFSv4.2 client", ... }
       │    }
       │    Server response: eir_flags shows supported features
       │    If server returns NFS4ERR_MINOR_VERS_MISMATCH → try 4.1
       │    If server accepts → proceed with NFSv4.2
       │
       ├─ Try NFSv4.1 (if 4.2 failed):
       │    Same EXCHANGE_ID but minor_version=1 in CREATE_SESSION
       │    NFSv4.1 features: sessions, pNFS, backchannel
       │
       ├─ Try NFSv4.0 (if 4.1 failed):
       │    SETCLIENTID (not EXCHANGE_ID — different operation)
       │    NFSv4.0: stateful, single connection, no sessions
       │
       └─ Mount fails with EPROTONOSUPPORT if all fail

  KERNEL SYSCTL CONTROL:
  # Minimum NFS minor version:
  cat /proc/sys/fs/nfs/nfs4_minor_version    # currently used
  echo 2 > /proc/sys/fs/nfs/nfs4_minor_version  # force 4.2 minimum

  # Force specific version via mount option:
  mount -t nfs -o vers=4.1 server:/export /mnt
```

## 7.2 SMB/CIFS Dialect Negotiation

```
SMB PROTOCOL NEGOTIATION (CIFS kernel client: fs/smb/client/)
══════════════════════════════════════════════════════════════════════

  NEGOTIATE Request (client → server):
  ─────────────────────────────────────
  SMB2 NEGOTIATE request (Command: 0x0000)

  0                   1                   2                   3
  0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  |        StructureSize=36       |     DialectCount (N)          |
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  |     SecurityMode              |      Reserved                 |
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  |                     Capabilities                              |
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  |                   ClientGuid (16 bytes)                       |
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  |                   NegotiateContextOffset                      |
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  |  NegotiateContextCount        |    Reserved2                  |
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  |  Dialects[0]: 0x0202 (SMB 2.0.2)                             |
  |  Dialects[1]: 0x0210 (SMB 2.1)                               |
  |  Dialects[2]: 0x0300 (SMB 3.0)                               |
  |  Dialects[3]: 0x0302 (SMB 3.0.2)                             |
  |  Dialects[4]: 0x0311 (SMB 3.1.1) ← highest, preferred        |
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

  NEGOTIATE Response (server → client):
  ──────────────────────────────────────
  Server picks the highest mutually supported dialect.
  Response includes:
  - DialectRevision: 0x0311 (SMB 3.1.1 selected)
  - SecurityMode: SMB2_NEGOTIATE_SIGNING_REQUIRED
  - Capabilities: SMB2_GLOBAL_CAP_ENCRYPTION (AES-128-CCM or AES-128-GCM)
  - NegotiateContextList:
      - SMB2_ENCRYPTION_CAPABILITIES: [AES-128-GCM, AES-128-CCM]
      - SMB2_SIGNING_CAPABILITIES: [AES-128-GMAC, HMAC-SHA-256]
      - SMB2_COMPRESSION_CAPABILITIES: [LZ4, LZNT1, LZ77+Huffman]

  KERNEL CODE PATH: fs/smb/client/smb2pdu.c
    SMB2_negotiate()
    → smb2_select_sectype() for authentication
    → smb311_update_preauth_hash() for pre-auth integrity hash (SMB 3.1.1)

  FALLBACK CHAIN:
  SMB 3.1.1 → SMB 3.0.2 → SMB 3.0 → SMB 2.1 → SMB 2.0.2 → fail
  (SMB1/CIFS is compiled out in modern kernels: CONFIG_CIFS_ALLOW_INSECURE_LEGACY=n)

  ENCRYPTION NEGOTIATION (SMB 3.0+):
  Client capabilities: SMB2_GLOBAL_CAP_ENCRYPTION
  Server response: selects AES-128-GCM (preferred, SMB 3.1.1) or AES-128-CCM
  Encrypted sessions use: HMAC-SHA-256 for signing, AES-GCM/CCM for payload
```

## 7.3 WireGuard: The Anti-Negotiation Design

WireGuard deliberately eliminates all cryptographic negotiation. This is
a security design choice, not a limitation:

```
WIREGUARD NOISE_IKpsk2 HANDSHAKE
══════════════════════════════════════════════════════════════════════

  FIXED ALGORITHMS (no negotiation possible):
  ────────────────────────────────────────────
  Key Exchange:   Curve25519 (ECDH)        drivers/net/wireguard/curve25519.c
  AEAD:           ChaCha20-Poly1305        drivers/net/wireguard/chacha20poly1305.c
  Hash:           BLAKE2s                  drivers/net/wireguard/blake2s.c
  PRF:            BLAKE2s (keyed)
  MAC:            SipHash (for cookie DoS protection)

  HANDSHAKE WIRE FORMAT:

  Initiator → Responder (msg type 1, 148 bytes):
  ╔═══════════════════════════════════════════════════════════════╗
  ║ type[4] | sender_index[4] | unencrypted_ephemeral[32]       ║
  ║ encrypted_static[48] | encrypted_timestamp[28] | mac1[16]   ║
  ║ mac2[16]                                                     ║
  ╚═══════════════════════════════════════════════════════════════╝
  - unencrypted_ephemeral: fresh Curve25519 public key (Epk_i)
  - encrypted_static: initiator's static public key, encrypted with
    ChaCha20-Poly1305 using DH(Epk_i, Rs) as key material
  - encrypted_timestamp: TAI64N timestamp, prevents replay
  - mac1: BLAKE2s of entire message minus mac1/mac2, keyed with
    BLAKE2s(LABEL_MAC1 || responder_static_pub)
  - mac2: BLAKE2s for cookie (DoS protection), zero if no cookie

  WHY NO NEGOTIATION:
  1. Downgrade prevention: no negotiation = no downgrade attack surface
  2. Simplicity: implementation is ~4000 lines vs OpenVPN's ~70000
  3. Ossification resistance: when you can negotiate, implementations
     leave old algorithms in "for compatibility" forever (see TLS 3DES)
  4. Formal verification: fixed algorithms can be verified (WireGuard
     has formal proof via the ProVerif tool)

  KERNEL CRYPTO API USAGE:
  drivers/net/wireguard/noise.c uses crypto API but with:
    - crypto_chacha20poly1305_encrypt() (direct, no alloc/free cycle)
    - Not crypto_alloc_aead("chacha20poly1305") — WireGuard uses
      its own optimized arch-specific implementations and calls them
      directly, bypassing the priority system for performance
```

---

# Part VIII: eBPF, XDP, and Kernel Crypto Interaction

## 8.1 XDP Protocol Classification and Fallback

XDP (eXpress Data Path) programs run at the earliest point in the RX path,
before the kernel's networking stack processes the packet. They can implement
protocol detection and fast-path routing:

```c
/*
 * eBPF/XDP program: classify packets by protocol and
 * implement fast-path vs. fallback routing.
 *
 * SEC("xdp") tells the eBPF loader this is an XDP program.
 */

#include <linux/bpf.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_endian.h>
#include <linux/if_ether.h>
#include <linux/ip.h>
#include <linux/ipv6.h>
#include <linux/tcp.h>
#include <linux/udp.h>

/* Map: per-packet protocol stats for monitoring */
struct {
    __uint(type, BPF_MAP_TYPE_PERCPU_ARRAY);
    __uint(max_entries, 256);
    __type(key, __u32);
    __type(value, __u64);
} proto_stats SEC(".maps");

/* Map: fast-path decision for known flows */
struct flow_key {
    __be32 src_ip;
    __be32 dst_ip;
    __be16 src_port;
    __be16 dst_port;
    __u8   protocol;
    __u8   pad[3];
};

struct {
    __uint(type, BPF_MAP_TYPE_LRU_HASH);
    __uint(max_entries, 65536);
    __type(key, struct flow_key);
    __type(value, __u32);   /* XDP_TX, XDP_PASS, XDP_DROP */
} flow_table SEC(".maps");

SEC("xdp")
int xdp_protocol_classifier(struct xdp_md *ctx)
{
    void *data     = (void *)(long)ctx->data;
    void *data_end = (void *)(long)ctx->data_end;

    /* Parse Ethernet header */
    struct ethhdr *eth = data;
    if ((void *)(eth + 1) > data_end)
        return XDP_PASS;  /* malformed: pass to kernel for handling */

    __u16 eth_proto = bpf_ntohs(eth->h_proto);

    /* Handle 802.1Q VLAN tags */
    if (eth_proto == ETH_P_8021Q || eth_proto == ETH_P_8021AD) {
        struct vlan_hdr {
            __be16 h_vlan_TCI;
            __be16 h_vlan_encapsulated_proto;
        } *vlan = (void *)(eth + 1);
        if ((void *)(vlan + 1) > data_end)
            return XDP_PASS;
        eth_proto = bpf_ntohs(vlan->h_vlan_encapsulated_proto);
        /* adjust data pointer past VLAN header */
        data = (void *)(vlan + 1);
    }

    __u8 ip_proto = 0;
    struct flow_key fk = {};

    if (eth_proto == ETH_P_IP) {
        struct iphdr *iph = data;
        if ((void *)(iph + 1) > data_end)
            return XDP_PASS;
        if (iph->ihl < 5)  /* minimum IP header = 5 * 4 = 20 bytes */
            return XDP_DROP;

        fk.src_ip  = iph->saddr;
        fk.dst_ip  = iph->daddr;
        ip_proto   = iph->protocol;

        data = (void *)iph + (iph->ihl * 4);  /* skip IP options */

    } else if (eth_proto == ETH_P_IPV6) {
        struct ipv6hdr *ip6h = data;
        if ((void *)(ip6h + 1) > data_end)
            return XDP_PASS;

        /* For simplicity: skip extension headers
         * Production code: parse extension header chain */
        ip_proto = ip6h->nexthdr;
        data     = (void *)(ip6h + 1);

        /* Note: IPv6 src/dst are 16 bytes each — store in map differently */

    } else {
        /* Not IP: pass to kernel */
        return XDP_PASS;
    }

    fk.protocol = ip_proto;

    /* Parse transport header */
    if (ip_proto == IPPROTO_TCP) {
        struct tcphdr *tcph = data;
        if ((void *)(tcph + 1) > data_end)
            return XDP_PASS;
        fk.src_port = tcph->source;
        fk.dst_port = tcph->dest;

        /* PROTOCOL FALLBACK DECISION:
         * If the flow is in our fast-path table, use cached decision.
         * If not, pass to kernel's full TCP stack for classification. */
        __u32 *action = bpf_map_lookup_elem(&flow_table, &fk);
        if (action)
            return *action;   /* fast path: cached decision */

        /* New flow: pass to kernel. Kernel will install it in flow_table
         * via a BPF_MAP_TYPE_LRU_HASH update from a tc/socket filter. */
        return XDP_PASS;

    } else if (ip_proto == IPPROTO_UDP) {
        struct udphdr *udph = data;
        if ((void *)(udph + 1) > data_end)
            return XDP_PASS;
        fk.src_port = udph->source;
        fk.dst_port = udph->dest;

        /* Check for QUIC (UDP port 443) */
        if (bpf_ntohs(fk.dst_port) == 443 || bpf_ntohs(fk.src_port) == 443) {
            /* QUIC: pass to userspace (QUIC stack is userspace in Linux) */
            return XDP_PASS;
        }

        /* Check for WireGuard (UDP port 51820) */
        if (bpf_ntohs(fk.dst_port) == 51820) {
            /* WireGuard handles its own decryption in kernel */
            return XDP_PASS;
        }

        return XDP_PASS;

    } else if (ip_proto == IPPROTO_ESP) {
        /* IPsec ESP: pass to XFRM framework */
        /* XDP cannot decrypt ESP — that requires XFRM SA lookup */
        return XDP_PASS;

    } else if (ip_proto == IPPROTO_AH) {
        /* IPsec AH: pass to XFRM framework */
        return XDP_PASS;
    }

    /* Unknown protocol: pass to kernel for handling */
    return XDP_PASS;
}

char _license[] SEC("license") = "GPL";
```

## 8.2 `bpf_crypto`: Kernel 6.10 Crypto Helpers

Kernel 6.10 (2024) introduced `bpf_crypto` — the ability to use crypto
operations directly in eBPF programs:

```c
/*
 * bpf_crypto: new in kernel 6.10
 * Allows eBPF programs to encrypt/decrypt data in the datapath.
 *
 * Primary use case: XDP-based encryption for custom protocols,
 * lightweight VPN-like applications, or network function offload.
 *
 * The crypto context is created and managed via a BPF map:
 * BPF_MAP_TYPE_STRUCT_OPS for the crypto context.
 *
 * From include/linux/bpf_crypto.h:
 */

struct bpf_crypto_params {
    char    type[14];       /* algorithm type: "skcipher", "aead" */
    char    algo[128];      /* algorithm name: "cbc(aes)", "gcm(aes)" */
    __u8    key[256];       /* key material */
    __u32   key_len;        /* key length in bytes */
    __u32   authsize;       /* authentication tag size (AEAD only) */
};

/*
 * BPF crypto helper calls (from eBPF program):
 */

/* Create a crypto context (called once, stored in BPF_TYPE_PTR map) */
struct bpf_crypto_ctx *ctx;
ctx = bpf_crypto_ctx_create(&params, sizeof(params), &err);
if (!ctx) {
    /* crypto context creation failed — algorithm not available */
    return XDP_PASS;
}

/* Encrypt a buffer (can be called per-packet) */
int ret = bpf_crypto_encrypt(ctx,
                              src,      /* source data (BPF_DYNPTR) */
                              dst,      /* destination (BPF_DYNPTR) */
                              &iv,      /* IV/nonce (BPF_DYNPTR) */
                              iv_len);

/* Decrypt a buffer */
ret = bpf_crypto_decrypt(ctx, src, dst, &iv, iv_len);

/* Release context (when BPF program/map is destroyed) */
bpf_crypto_ctx_release(ctx);

/*
 * CRITICAL CONSTRAINT: bpf_crypto operates synchronously.
 * The verifier enforces that crypto contexts are never shared
 * between CPUs without proper synchronization (they are per-CPU
 * by design in most implementations).
 *
 * FALLBACK: If the requested algorithm is not supported by the
 * kernel's crypto API, bpf_crypto_ctx_create() returns NULL and
 * sets err = -ENOENT. The eBPF program must handle this gracefully —
 * typically by passing the packet to userspace for processing.
 */
```

---

# Part IX: Rust Integration

## 9.1 kTLS from Rust: Post-Handshake Kernel Offload

```toml
# Cargo.toml
[dependencies]
# libc for low-level syscalls (setsockopt)
libc = "0.2"
# tokio for async runtime
tokio = { version = "1", features = ["net", "io-util"] }
# rustls for TLS handshake
rustls = { version = "0.23", features = ["std"] }
# For extracting session keys from rustls (requires internal access)
# Note: rustls does not expose raw session keys by default for security reasons.
# kTLS integration requires a custom KeyLog or special build.
```

```rust
// PRODUCTION CONTEXT: nginx-rs or custom TLS server using kTLS for zero-copy TX
// CRATES: libc (setsockopt), rustls (TLS handshake + key extraction)
// PATTERN: rustls handshake → extract session keys → offload to kTLS
// ANTI-PATTERN: calling TCP_ULP after data has been written to the socket

use libc::{setsockopt, IPPROTO_TCP};
use std::os::unix::io::AsRawFd;
use std::io;

// These match include/uapi/linux/tls.h
const SOL_TLS: libc::c_int = 282;
const TLS_TX: libc::c_int = 1;
const TLS_RX: libc::c_int = 2;
const TCP_ULP: libc::c_int = 31;

// TLS cipher type IDs (from uapi/linux/tls.h)
const TLS_CIPHER_AES_GCM_128: u16 = 51;
const TLS_CIPHER_AES_GCM_256: u16 = 52;
const TLS_CIPHER_CHACHA20_POLY1305: u16 = 54;

// TLS versions
const TLS_1_2_VERSION: u16 = 0x0303;
const TLS_1_3_VERSION: u16 = 0x0304;

// MUST match struct tls12_crypto_info_aes_gcm_128 in include/uapi/linux/tls.h
// #[repr(C)] is mandatory: this struct is passed directly to the kernel
// via setsockopt. Any padding or field reordering would corrupt the syscall.
#[repr(C)]
struct TlsCryptoInfoAesGcm128 {
    version:     u16,
    cipher_type: u16,
    iv:          [u8; 8],
    salt:        [u8; 4],
    key:         [u8; 16],
    rec_seq:     [u8; 8],
}

#[repr(C)]
struct TlsCryptoInfoAesGcm256 {
    version:     u16,
    cipher_type: u16,
    iv:          [u8; 8],
    salt:        [u8; 4],
    key:         [u8; 32],
    rec_seq:     [u8; 8],
}

#[repr(C)]
struct TlsCryptoInfoChacha20Poly1305 {
    version:     u16,
    cipher_type: u16,
    iv:          [u8; 12],
    key:         [u8; 32],
    rec_seq:     [u8; 8],
}

#[derive(Debug)]
pub enum KtlsError {
    UlpAttach(io::Error),
    TxSetup(io::Error),
    RxSetup(io::Error),
    UnsupportedCipher(u16),
    KernelTooOld,
}

/// Attempt to offload TLS record layer to the kernel (kTLS).
///
/// # Safety
/// The caller must ensure:
/// - `fd` is a valid TCP socket in ESTABLISHED state
/// - `tx_key` / `rx_key` slices have the correct length for the cipher
/// - This is called BEFORE any TLS-layer data is written
/// - `fd` is not shared across threads while this is executing
///
/// # Key Material
/// The key material in the parameters is zeroed after being copied
/// to the kernel via setsockopt. The kernel holds its own copy.
pub fn ktls_setup(
    fd: std::os::unix::io::RawFd,
    tls_version: u16,
    cipher_type: u16,
    tx_key: &[u8],
    tx_iv: &[u8],
    tx_salt: &[u8],
    tx_seq: u64,
    rx_key: &[u8],
    rx_iv: &[u8],
    rx_salt: &[u8],
    rx_seq: u64,
) -> Result<KtlsMode, KtlsError> {
    // Step 1: Attach TLS ULP
    // ANTI-PATTERN: Doing this after any write() to the socket.
    // The ULP must be attached before the handshake writes data,
    // but keys are only programmed after the handshake completes.
    let ulp_name = b"tls\0";
    let ret = unsafe {
        setsockopt(
            fd,
            IPPROTO_TCP,
            TCP_ULP,
            ulp_name.as_ptr() as *const libc::c_void,
            (ulp_name.len() - 1) as libc::socklen_t, // strlen("tls") = 3
        )
    };
    if ret != 0 {
        let err = io::Error::last_os_error();
        if err.raw_os_error() == Some(libc::ENOENT) {
            return Err(KtlsError::KernelTooOld); // tls.ko not loaded
        }
        return Err(KtlsError::UlpAttach(err));
    }

    // Step 2: Program TX cipher state
    let tx_ok = program_cipher(fd, TLS_TX, tls_version, cipher_type,
                                tx_key, tx_iv, tx_salt, tx_seq);
    // Step 3: Program RX cipher state
    let rx_ok = program_cipher(fd, TLS_RX, tls_version, cipher_type,
                                rx_key, rx_iv, rx_salt, rx_seq);

    match (tx_ok, rx_ok) {
        (Ok(()), Ok(())) => Ok(KtlsMode::Full),
        (Ok(()), Err(_)) => Ok(KtlsMode::TxOnly),    // partial kTLS
        (Err(e), _)      => Err(KtlsError::TxSetup(e)),
    }
}

#[derive(Debug, PartialEq)]
pub enum KtlsMode {
    Full,    // both TX and RX offloaded
    TxOnly,  // only TX offloaded (RX stays in userspace)
}

fn program_cipher(
    fd: std::os::unix::io::RawFd,
    direction: libc::c_int,  // TLS_TX or TLS_RX
    version: u16,
    cipher_type: u16,
    key: &[u8],
    iv: &[u8],
    salt: &[u8],
    seq: u64,
) -> io::Result<()> {
    let ret = match cipher_type {
        TLS_CIPHER_AES_GCM_128 => {
            // INVARIANT: key must be exactly 16 bytes
            // INVARIANT: iv must be exactly 8 bytes
            // INVARIANT: salt must be exactly 4 bytes
            assert_eq!(key.len(), 16, "AES-128 key must be 16 bytes");
            assert_eq!(iv.len(), 8);
            assert_eq!(salt.len(), 4);

            let mut info = TlsCryptoInfoAesGcm128 {
                version,
                cipher_type,
                iv:      [0u8; 8],
                salt:    [0u8; 4],
                key:     [0u8; 16],
                rec_seq: seq.to_be_bytes(),
            };
            info.iv.copy_from_slice(iv);
            info.salt.copy_from_slice(salt);
            info.key.copy_from_slice(key);

            let ret = unsafe {
                setsockopt(
                    fd,
                    SOL_TLS,
                    direction,
                    &info as *const _ as *const libc::c_void,
                    std::mem::size_of::<TlsCryptoInfoAesGcm128>() as libc::socklen_t,
                )
            };

            // MANDATORY: zero the info struct immediately after the syscall.
            // The key is now in kernel memory. Zeroing the stack copy prevents
            // key material from lingering in stack frames during stack traces
            // or core dumps. This is the Rust equivalent of explicit_bzero().
            // Note: use zeroize crate in production to prevent compiler optimization.
            unsafe {
                std::ptr::write_volatile(&mut info as *mut _ as *mut u8,
                                          0u8);
                // In production: use zeroize::Zeroize::zeroize(&mut info)
            }
            ret
        }

        TLS_CIPHER_AES_GCM_256 => {
            assert_eq!(key.len(), 32, "AES-256 key must be 32 bytes");
            let mut info = TlsCryptoInfoAesGcm256 {
                version, cipher_type,
                iv:      [0u8; 8],
                salt:    [0u8; 4],
                key:     [0u8; 32],
                rec_seq: seq.to_be_bytes(),
            };
            info.iv.copy_from_slice(iv);
            info.salt.copy_from_slice(salt);
            info.key.copy_from_slice(key);
            let ret = unsafe {
                setsockopt(fd, SOL_TLS, direction,
                    &info as *const _ as *const libc::c_void,
                    std::mem::size_of_val(&info) as libc::socklen_t)
            };
            // zero key material
            ret
        }

        TLS_CIPHER_CHACHA20_POLY1305 => {
            assert_eq!(key.len(), 32, "ChaCha20 key must be 32 bytes");
            assert_eq!(iv.len(), 12, "ChaCha20 nonce must be 12 bytes");
            let mut info = TlsCryptoInfoChacha20Poly1305 {
                version, cipher_type,
                iv:      [0u8; 12],
                key:     [0u8; 32],
                rec_seq: seq.to_be_bytes(),
            };
            info.iv.copy_from_slice(iv);
            info.key.copy_from_slice(key);
            let ret = unsafe {
                setsockopt(fd, SOL_TLS, direction,
                    &info as *const _ as *const libc::c_void,
                    std::mem::size_of_val(&info) as libc::socklen_t)
            };
            ret
        }

        _ => return Err(io::Error::from_raw_os_error(libc::ENOTSUP)),
    };

    if ret != 0 {
        Err(io::Error::last_os_error())
    } else {
        Ok(())
    }
}
```

## 9.2 `rustls` Cipher Suite Negotiation Internals

```rust
// rustls cipher suite negotiation — how the library selects and falls back
// rustls 0.23 with the default ring provider

use rustls::{
    ClientConfig, ServerConfig,
    crypto::{ring, CryptoProvider},
    version::{TLS12, TLS13},
    CipherSuite,
};

// CONCEPT: rustls separates cipher suites by TLS version.
// TLS 1.3 cipher suites: defined by RFC 8446, 5 suites total
// TLS 1.2 cipher suites: hundreds possible; rustls supports ~7 safe ones

// Default rustls 0.23 cipher suite preference list (from ring provider):
// TLS 1.3 (preferred):
//   TLS13_AES_256_GCM_SHA384     (AES-256-GCM + SHA-384)
//   TLS13_AES_128_GCM_SHA256     (AES-128-GCM + SHA-256)
//   TLS13_CHACHA20_POLY1305_SHA256 (ChaCha20-Poly1305 + SHA-256)
// TLS 1.2 (fallback):
//   TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384
//   TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384
//   TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256
//   TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256
//   TLS_ECDHE_ECDSA_WITH_CHACHA20_POLY1305_SHA256
//   TLS_ECDHE_RSA_WITH_CHACHA20_POLY1305_SHA256

/// Build a client config that negotiates TLS 1.3 only, with
/// AES-GCM preferred over ChaCha20 (for kTLS compatibility —
/// kTLS ChaCha20 requires kernel 5.11+).
pub fn build_ktls_compatible_client_config() -> Result<ClientConfig, rustls::Error> {
    let provider = CryptoProvider {
        // Order matters: client sends this list to server;
        // server picks first suite from this list that IT supports.
        // kTLS preferred order: AES-GCM-128 first (widest kernel support)
        cipher_suites: vec![
            ring::cipher_suite::TLS13_AES_128_GCM_SHA256,   // kTLS: kernel 4.13+
            ring::cipher_suite::TLS13_AES_256_GCM_SHA384,   // kTLS: kernel 5.10+
            ring::cipher_suite::TLS13_CHACHA20_POLY1305_SHA256, // kTLS: kernel 5.11+
        ],
        ..ring::default_provider()
    };

    // Install as the global provider (process-wide, call once)
    // or use with_custom_certificate_verifier for per-config

    let config = ClientConfig::builder_with_provider(provider.into())
        .with_protocol_versions(&[&TLS13])? // TLS 1.3 only — no TLS 1.2 fallback
        .with_native_roots()?               // use system CA bundle
        .with_no_client_auth();

    Ok(config)
}

/// Server-side: restrict to ciphers that the kernel kTLS supports.
/// This matters when you want sendfile() zero-copy on all connections.
pub fn build_ktls_server_config(
    cert_chain: Vec<rustls::pki_types::CertificateDer<'static>>,
    private_key: rustls::pki_types::PrivateKeyDer<'static>,
) -> Result<ServerConfig, rustls::Error> {
    // Server-side cipher suite list determines what gets accepted
    // when client offers multiple options.
    let provider = CryptoProvider {
        cipher_suites: vec![
            // AES-GCM-128: safest kTLS choice (kernel 4.13+, NIC offload common)
            ring::cipher_suite::TLS13_AES_128_GCM_SHA256,
            ring::cipher_suite::TLS13_AES_256_GCM_SHA384,
        ],
        ..ring::default_provider()
    };

    ServerConfig::builder_with_provider(provider.into())
        .with_protocol_versions(&[&TLS13])?
        .with_no_client_auth()
        .with_single_cert(cert_chain, private_key)
}
```

## 9.3 `aya` for eBPF Crypto Interaction from Rust

```rust
// Cargo.toml additions for aya:
// aya = "0.13"
// aya-log = "0.2"

use aya::{
    Bpf,
    maps::{HashMap, RingBuf},
    programs::{Xdp, XdpFlags},
};
use std::collections::HashMap as StdHashMap;

/// Load and attach the XDP protocol classifier from Part VIII.
pub async fn run_xdp_classifier(iface: &str) -> anyhow::Result<()> {
    // Load the compiled eBPF object file.
    // The eBPF bytecode was compiled from the C program in Part VIII
    // using clang -target bpf -O2 -c xdp_classifier.c -o xdp_classifier.o
    let mut bpf = Bpf::load_file("xdp_classifier.o")?;

    // Get reference to the XDP program by section name
    let program: &mut Xdp = bpf.program_mut("xdp_protocol_classifier").unwrap().try_into()?;
    program.load()?;

    // Attach to network interface
    // XdpFlags::SKB_MODE: software XDP (universal, any driver)
    // XdpFlags::DRV_MODE: native XDP (requires driver support, faster)
    // XdpFlags::HW_MODE:  hardware XDP (requires NIC support, fastest)
    //
    // FALLBACK CHAIN: HW_MODE → DRV_MODE → SKB_MODE
    // Try hardware first, fall back if driver doesn't support:
    let flags = if let Err(_) = program.attach(iface, XdpFlags::HW_MODE) {
        if let Err(_) = program.attach(iface, XdpFlags::DRV_MODE) {
            XdpFlags::SKB_MODE  // always works
        } else {
            XdpFlags::DRV_MODE
        }
    } else {
        XdpFlags::HW_MODE
    };

    program.attach(iface, flags)?;
    tracing::info!(?iface, ?flags, "XDP program attached");

    // Access the flow_table map to read/write fast-path decisions
    let mut flow_table: HashMap<_, [u8; 12], u32> =
        HashMap::try_from(bpf.map_mut("flow_table").unwrap())?;

    // Example: pre-populate known flow decisions
    // This would normally come from a control plane component
    let flow_key: [u8; 12] = /* src_ip, dst_ip, ports, proto */ [0u8; 12];
    flow_table.insert(flow_key, aya::maps::MapData::XDP_PASS, 0)?;

    // Keep running until signal
    tokio::signal::ctrl_c().await?;
    Ok(())
}
```

## 9.4 Key Material Handling with `zeroize`

```rust
// CONCEPT: Preventing key material from leaking in memory
// INVARIANT: Key material must be zeroed when no longer needed
// WHAT WOULD BREAK: Without zeroize, compiler may optimize away the zeroing;
//                   keys persist in stack/heap until overwritten by future allocations

use zeroize::{Zeroize, ZeroizeOnDrop};

/// Session key material container.
/// ZeroizeOnDrop ensures the key is zeroed when this struct is dropped —
/// even if dropping happens due to a panic or early return.
#[derive(ZeroizeOnDrop)]
pub struct SessionKeys {
    #[zeroize(drop)]
    pub tx_key:  Vec<u8>,
    #[zeroize(drop)]
    pub tx_iv:   Vec<u8>,
    #[zeroize(drop)]
    pub tx_salt: Vec<u8>,
    #[zeroize(drop)]
    pub rx_key:  Vec<u8>,
    #[zeroize(drop)]
    pub rx_iv:   Vec<u8>,
    #[zeroize(drop)]
    pub rx_salt: Vec<u8>,
    pub tx_seq:  u64,     // sequence number: not secret, no need to zeroize
    pub rx_seq:  u64,
}

impl SessionKeys {
    /// After programing kTLS, explicitly zero the keys.
    /// This is defense-in-depth: ZeroizeOnDrop handles the Drop case,
    /// but explicit zeroing ensures keys are gone immediately after use.
    pub fn zero_now(&mut self) {
        self.tx_key.zeroize();
        self.tx_iv.zeroize();
        self.tx_salt.zeroize();
        self.rx_key.zeroize();
        self.rx_iv.zeroize();
        self.rx_salt.zeroize();
    }
}

// ANTI-PATTERN: Storing keys in a plain Vec<u8> or [u8; N]
// without ZeroizeOnDrop. The allocator will reuse the memory
// and the key bytes will be present until overwritten.
// In a memory-safe language like Rust this is subtler but still dangerous:
//   - Stack inspector or debugger can read the key
//   - Core dump captures the key
//   - Speculative execution may expose it (Spectre variant)
//   - Swap/hibernation writes it to disk

// CORRECT pattern: always use zeroize for key material
fn process_tls_session(keys: SessionKeys) {
    let fd = connect_to_server().unwrap();
    let result = ktls_setup(
        fd,
        TLS_1_3_VERSION,
        TLS_CIPHER_AES_GCM_128,
        &keys.tx_key, &keys.tx_iv, &keys.tx_salt, keys.tx_seq,
        &keys.rx_key, &keys.rx_iv, &keys.rx_salt, keys.rx_seq,
    );
    // `keys` is dropped here → ZeroizeOnDrop zeroes all key material
    // Even if ktls_setup panics, Drop is called and keys are zeroed
    drop(keys); // explicit is better than implicit
}
```

---

# Part X: Failure Modes, Downgrade Attacks, and Security

## 10.1 Downgrade Attacks: Protocol and Cipher

A downgrade attack forces two parties that support a strong protocol to negotiate
a weaker one, which the attacker can then break.

```
DOWNGRADE ATTACK TAXONOMY
══════════════════════════════════════════════════════════════════════

  TYPE 1: Protocol Version Downgrade
  ────────────────────────────────────────────────────────────────
  Attack:  MitM drops ClientHello with TLS 1.3 support;
           client sees no response → retries with TLS 1.2 only
  Defense: TLS 1.3 ServerHello sentinel (RFC 8446 §4.1.3):
           If server returns TLS 1.2 ServerHello in response to
           TLS 1.3 ClientHello, the last 8 bytes of the server
           random field must NOT contain:
             44 4F 57 4E 47 52 44 01  ← "DOWNGRD\1" TLS 1.2 sentinel
             44 4F 57 4E 47 52 44 00  ← "DOWNGRD\0" TLS 1.1 sentinel
           A TLS 1.3 client checks for these sentinels; if present,
           it MUST abort. This is baked into the Finished message
           using the full handshake transcript.
  Kernel role: None. This is entirely a userspace TLS library concern.

  TYPE 2: Cipher Suite Downgrade (TLS 1.2)
  ────────────────────────────────────────────────────────────────
  Attack:  MitM removes strong ciphers from ClientHello;
           server picks the weakest remaining cipher
  Defense: Extended Master Secret (RFC 7627); TLS 1.3 eliminates
           this entirely by hashing the full handshake transcript
           into the Finished message
  Historical examples: FREAK (RSA_EXPORT forced), POODLE (SSLv3)
  Kernel role: None.

  TYPE 3: IKEv2 Algorithm Downgrade
  ────────────────────────────────────────────────────────────────
  Attack:  MitM drops IKE_SA_INIT and replays with stripped proposals
  Defense: IKEv2 Notify: INVALID_SYNTAX on unrecognized proposals;
           strongSwan uses signed-by-PSK/PKI proposals so an attacker
           cannot fake them; the AUTH payload covers the SA payload
           in IKE_AUTH, binding the agreed algorithms to authentication
  Kernel role: None. Kernel trusts what IKE programs into XFRM.

  TYPE 4: XDP/eBPF Protocol Misclassification
  ────────────────────────────────────────────────────────────────
  Attack:  Craft packet that XDP classifies as a different protocol,
           routing it to a less-secure path (bypassing XFRM)
  Defense: XFRM policies (SPD) enforce security independently of XDP;
           XDP can only affect routing, not security policy enforcement.
           An XDP XDP_PASS decision still goes through XFRM policy check.
  Kernel role: XFRM policy is the security enforcement point.

  TYPE 5: NIC TLS Offload Sequence Number Mismatch
  ────────────────────────────────────────────────────────────────
  Attack:  Force a TCP retransmit that confuses the NIC's sequence
           number tracking; NIC encrypts with wrong sequence number
           (wrong nonce) → nonce reuse in AES-GCM → catastrophic
           loss of confidentiality and integrity
  Defense: Kernel detects sequence number mismatch and forces
           resynchronization (KERN_RESYNC event); the NIC offload
           is disabled for that connection and kTLS SW takes over.
           Monitor: /proc/net/tls_stat TlsRxDeviceResync counter
  Kernel role: net/tls/tls_device.c handles resync events.
```

## 10.2 Compile-Time Failure Modes

```rust
// COMPILE-TIME FAILURE: repr(C) missing on crypto info struct
// The kernel reads the struct layout directly from the setsockopt buffer.
// Without repr(C), Rust's default layout is undefined (the compiler
// can reorder fields). This compiles but corrupts the syscall silently.

// WON'T WORK AS INTENDED (no compile error, but runtime corruption):
struct TlsCryptoInfoBad {  // ← missing #[repr(C)]
    version:     u16,
    cipher_type: u16,
    iv:          [u8; 8],
    salt:        [u8; 4],
    key:         [u8; 16],
    rec_seq:     [u8; 8],
}
// The kernel reads version at offset 0 and cipher_type at offset 2.
// Without repr(C), Rust may insert padding or reorder these.
// setsockopt succeeds (kernel copies the bytes blindly) but the kernel
// interprets cipher_type as the wrong value → EINVAL on next operation.

// CORRECT: always #[repr(C)] for kernel-interface structs
#[repr(C)]
struct TlsCryptoInfoGood { /* same fields */ }
```

## 10.3 Runtime Failure Modes

```
RUNTIME FAILURE: AES-GCM NONCE REUSE
══════════════════════════════════════════════════════════════════════
The nonce for AES-GCM-128 in TLS is:
  nonce = salt (4 bytes) XOR (IV || seq_num) (8 bytes)
         → 12 bytes total

TLS 1.3 prohibits explicit IV; nonce = salt XOR seq_num.
The sequence number MUST be monotonically increasing.

If rec_seq is programmed incorrectly (e.g., starts at wrong value,
or is not incremented by the kernel for each record):
  → Same nonce used for two different records
  → GCM authentication tag can be broken algebraically
  → Full plaintext recovery possible with two known-plaintext records
  → Complete loss of both confidentiality and integrity

Detection: kernel tracks rec_seq internally after TLS_TX is set.
The rec_seq in the setsockopt struct is the STARTING sequence number.
Kernel increments it for each record. Application never sees it.

Security consequence: catastrophic — worse than using no encryption.
Nonce reuse allows offline key recovery.

RUNTIME FAILURE: kTLS RX EBADMSG
══════════════════════════════════════════════════════════════════════
If the received TLS record fails authentication tag verification:
  read() returns -1 with errno = EBADMSG

Application MUST handle EBADMSG:
  - Close the connection immediately
  - Do NOT retry the read (the record is permanently invalid)
  - Log the event (may indicate active MitM attack)
  - For TLS 1.3: send an alert (decrypt_error) before closing
    (though with kTLS, the kernel sends the alert automatically
     if SO_TXREHASH is not set)

ANTI-PATTERN: Ignoring EBADMSG and retrying read()
→ Application hangs (no more valid data will arrive from the kernel)
→ Connection is effectively broken with no error propagation

RUNTIME FAILURE: XFRM SA EXPIRY
══════════════════════════════════════════════════════════════════════
When an IPsec SA expires (byte limit or time limit):
  - Kernel sends XFRM_MSG_EXPIRE Netlink message to IKE daemon
  - Kernel DROPS packets using the expired SA (hard limit)
    or WARNS but continues (soft limit)
  - If IKE daemon is not listening (dead): all IPsec traffic drops silently
  - Application sees: connection timeout or EHOSTUNREACH
  - No TLS-layer error: XFRM drops at L3, TLS layer is unaware

Detection: ip xfrm monitor → shows XFRM_MSG_EXPIRE events
```

## 10.4 Performance Failure Modes

```
PERFORMANCE ANTI-PATTERN 1: crypto_alloc_skcipher in the hot path
══════════════════════════════════════════════════════════════════
crypto_alloc_skcipher() allocates:
  - A per-transform context (cra_ctxsize bytes, from kmalloc)
  - Locks crypto_alg_sem (read semaphore, but still a lock)
  - May trigger module autoload (extremely slow)

CORRECT: Allocate once at connection setup, reuse for all records.
WRONG:   Call crypto_alloc_skcipher() for each packet/record.

PERFORMANCE ANTI-PATTERN 2: Synchronous crypto in softirq context
══════════════════════════════════════════════════════════════════
The Linux networking stack processes packets in softirq context.
Synchronous AES-NI involves saving/restoring the FPU state
(kernel_fpu_begin/end). This is expensive (hundreds of nanoseconds)
and disables preemption for its duration.

kTLS and XFRM handle this correctly by deferring crypto to process
context (workqueue) when necessary. User eBPF programs using
bpf_crypto should not call bpf_crypto_encrypt in tight loops
on the XDP fast path — batch processing is preferred.

PERFORMANCE ANTI-PATTERN 3: Using HMAC+CBC instead of AEAD
══════════════════════════════════════════════════════════════════
TLS 1.2 with AES-128-CBC + HMAC-SHA-256 requires:
  1. AES-CBC encryption: ~1 cycle/byte on AES-NI
  2. HMAC-SHA-256 computation: ~0.5 cycles/byte on SHA-NI
  3. Two separate kernel crypto calls

TLS 1.3 with AES-128-GCM requires:
  1. AES-GCM (AEAD): ~0.6 cycles/byte on VAES+CLMULQDQ
  2. One kernel crypto call
  3. Fully pipelined with NIC offload

Use AEAD (GCM, ChaCha20-Poly1305) exclusively for new code.
The authenc(hmac(sha256),cbc(aes)) template in XFRM is legacy.
```

---

# Part XI: Connection Map and Mental Model Checkpoint

## 11.1 The Decision Tree: Which Mechanism Handles What

```
DECISION TREE: Which Linux subsystem handles your negotiation?
══════════════════════════════════════════════════════════════════

  Q: What are you trying to negotiate?

  IPv4 vs IPv6?
  → Socket layer: AF_INET6 dual-stack, IPV6_V6ONLY sysctl, getaddrinfo

  TCP options (SACK, TFO, ECN, window scaling)?
  → TCP stack: net/ipv4/tcp_options.c, tcp_sysctl.c
  → Control: /proc/sys/net/ipv4/tcp_*
  → Observe: getsockopt(TCP_INFO)

  Which TLS version + cipher suite?
  → Userspace TLS library (rustls, OpenSSL, BoringSSL)
  → rustls: ClientConfig::cipher_suites, protocol_versions
  → Fallback: per preference list sent in ClientHello

  TLS session key offload to kernel?
  → kTLS: TCP_ULP + SOL_TLS setsockopt
  → Cipher type determines kernel support (check kernel version)
  → Fallback chain: NIC HW → kernel SW → userspace

  IPsec tunnel cipher suite?
  → IKEv2 daemon (strongSwan) negotiates, then programs XFRM
  → XFRM: XFRM_MSG_NEWSA via AF_NETLINK socket
  → Cipher must be in net/xfrm/xfrm_algo.c tables
  → Algorithm probe: crypto_has_aead() / crypto_has_skcipher()

  Which crypto implementation (HW vs SW)?
  → Linux Crypto API: automatic, via cra_priority
  → Hardware: module must load (CPU feature check at load time)
  → Inspect: /proc/crypto (priority, driver name, availability)

  NFS protocol version?
  → NFS kernel client: nfs_get_tree() auto-probe
  → Control: mount -o vers=4.2

  SMB dialect?
  → CIFS kernel client: SMB2_negotiate() dialect list
  → Server picks highest mutually supported

  WireGuard crypto?
  → Fixed, no negotiation by design: Curve25519, ChaCha20-Poly1305, BLAKE2s
```

## 11.2 Connection Map

This concept connects to:

- **`zeroize` crate** because crypto key material passed to kTLS via `setsockopt` must be zeroed immediately after the syscall; the kernel has its own copy, and the stack/heap copy is a liability.
- **`#[repr(C)]` and alignment** because every struct passed to `setsockopt` for kTLS and every struct in XFRM Netlink messages must have the exact memory layout the kernel expects — `repr(C)` is not optional, it is a safety invariant.
- **`CRYPTO_ALG_ASYNC` and `cryptd`** because XFRM's ESP processing uses asynchronous crypto ops in some code paths, requiring algorithms to have the `CRYPTO_ALG_ASYNC` flag; `cryptd` wraps sync AES-NI to satisfy this requirement without a separate async implementation.
- **RFC 8446 §4.2.2 (Supported Versions extension)** because TLS version negotiation is handled by this extension in TLS 1.3; the client sends `supported_versions` and the server picks — this is what rustls implements in `ClientHello::extensions`.
- **RFC 4301 §4.1 (SPD)** because the XFRM Security Policy Database is the kernel's implementation of the IPsec SPD defined in this RFC; `XFRM_MSG_NEWPOLICY` programs it.
- **Timing side-channels** because algorithm fallback that takes a different code path for different inputs (e.g., QAT → software due to key size) can create timing oracles if the code paths have measurably different latencies.
- **eBPF `BPF_MAP_TYPE_LRU_HASH`** because XDP protocol classification uses this map type for flow table storage; the LRU eviction policy means rarely-seen protocols are eventually dropped from the fast path — a form of implicit fallback to the kernel's full networking stack.
- **`SO_TXREHASH` socket option** because when kTLS is active, this option controls whether the kernel sends TLS alerts automatically on authentication failure — relevant to how EBADMSG errors are surfaced to the application.
- **`net.core.devconf_inherit_init_net`** and network namespaces because XFRM policies are per-network-namespace; in Kubernetes, each pod has its own network namespace, so IPsec SAs programmed by a node-level IKE daemon must use the correct namespace fd.
- **WireGuard's Noise protocol** because it demonstrates the security argument AGAINST negotiation: every negotiation mechanism is a potential downgrade surface; WireGuard's security proof is possible precisely because the algorithm is fixed and formally specified.

## 11.3 Layer 7 Checkpoint Questions

These questions require application of the concepts above to new scenarios.
Do not look up answers — work through the mental model first.

---

**Question 1 (Crypto API + kTLS interaction):**

You are deploying a TLS termination proxy on a server with an Intel CPU from 2008
(Penryn microarchitecture — no AES-NI, no CLMULQDQ). A client connects and
negotiates TLS 1.3 with `TLS_AES_128_GCM_SHA256`. You attempt to set up kTLS with
`TLS_CIPHER_AES_GCM_128`.

Trace the complete path: What crypto implementation does the kernel select for the
GCM encryption? What is its `cra_driver_name` and priority? Will NIC TLS offload
work? What is the performance implication, and is there a cipher you could negotiate
instead that would perform better on this CPU?

---

**Question 2 (XFRM fallback + security implication):**

Your strongSwan deployment sends `XFRM_MSG_NEWSA` with algorithm `"rfc4106(gcm(aes))"`,
key length 288 bits (256-bit key + 32-bit salt), ICV length 128 bits.

The kernel returns `NLMSG_ERROR` with `-ENOSYS`.

What does this error mean at each level: kernel crypto API, XFRM, and IKE daemon?
What happens to the network traffic while the IKE daemon is retrying? What algorithm
should the IKE daemon try next, and what changes in the `xfrm_algo_aead.alg_key_len`
field when it does?

---

**Question 3 (eBPF + XFRM + security):**

You write an XDP program that inspects the first 4 bytes of the UDP payload. If they
match the WireGuard handshake type byte (0x01), the program returns `XDP_TX`
(immediately bounce the packet back) to implement a port reflection defense.

A security reviewer says this creates a security vulnerability in an environment
where you also have IPsec ESP policies (`IPPROTO_ESP = 50`) protecting traffic
to/from the same server.

Explain precisely why `XDP_TX` returning a packet before XFRM policy evaluation is
dangerous, what traffic could bypass your IPsec policy, and how to fix the XDP
program to preserve both the reflection defense and IPsec enforcement.

---

*End of document. Word count: approximately 11,500 words.*
*Kernel version baseline: 6.x (notation for version-specific features included inline)*
*Last updated reference: Linux kernel 6.10 for bpf_crypto; kernel 5.11 for ChaCha20-Poly1305 kTLS*
