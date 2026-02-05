# Cryptography: A Foundational Deep Dive

**Comprehensive Guide from First Principles to Production Systems**

---

## Table of Contents
1. [Core Foundations](#core-foundations)
2. [Mathematical Primitives](#mathematical-primitives)
3. [Symmetric Cryptography](#symmetric-cryptography)
4. [Asymmetric Cryptography](#asymmetric-cryptography)
5. [Hash Functions & MACs](#hash-functions--macs)
6. [Real-World Protocol Implementations](#real-world-protocol-implementations)
7. [Modern Cryptographic Systems](#modern-cryptographic-systems)

---

## Core Foundations

### What is Cryptography?

**Cryptography** is the science of secure communication in the presence of adversaries. It transforms readable data (**plaintext**) into unreadable data (**ciphertext**) using mathematical operations and secret keys.

**Core Security Properties:**
1. **Confidentiality**: Only authorized parties can read the message
2. **Integrity**: Message cannot be altered without detection
3. **Authentication**: Verify identity of sender
4. **Non-repudiation**: Sender cannot deny sending the message

### Fundamental Terminology

Before diving deep, let's define essential terms:

- **Plaintext**: Original, readable data (e.g., "HELLO")
- **Ciphertext**: Encrypted, unreadable data (e.g., "X4$9K")
- **Encryption**: Process of converting plaintext → ciphertext
- **Decryption**: Process of converting ciphertext → plaintext
- **Key**: Secret parameter used in encryption/decryption algorithms
- **Cipher**: Algorithm for encryption/decryption
- **Keyspace**: Set of all possible keys for a cipher
- **Bit**: Binary digit (0 or 1), fundamental unit in computing
- **Byte**: 8 bits (can represent 0-255 in decimal)
- **XOR (⊕)**: Exclusive OR operation - returns 1 if bits differ, 0 if same
  - `0 ⊕ 0 = 0`, `0 ⊕ 1 = 1`, `1 ⊕ 0 = 1`, `1 ⊕ 1 = 0`
  - Critical property: `A ⊕ B ⊕ B = A` (reversible)

---

## Mathematical Primitives

### Modular Arithmetic

**Modulo operation** (`mod`): Remainder after division.

```
17 mod 5 = 2  (because 17 = 3×5 + 2)
23 mod 7 = 2  (because 23 = 3×7 + 2)
```

**Properties:**
- `(a + b) mod n = ((a mod n) + (b mod n)) mod n`
- `(a × b) mod n = ((a mod n) × (b mod n)) mod n`

**Why it matters**: Modular arithmetic keeps numbers bounded, essential for finite computer arithmetic and creating mathematical "one-way functions."

### Prime Numbers

A **prime number** is divisible only by 1 and itself (2, 3, 5, 7, 11...).

**Why crucial**: 
- Factoring large numbers into primes is computationally hard
- RSA security relies on difficulty of factoring `n = p × q` where p, q are large primes

**Greatest Common Divisor (GCD)**: Largest number dividing both a and b.
- Example: `GCD(48, 18) = 6`
- **Coprime**: Two numbers with `GCD = 1` (e.g., 15 and 28)

### Discrete Logarithm Problem

Given: `g^x mod p = y`
- **Easy**: Compute y given g, x, p (modular exponentiation)
- **Hard**: Find x given g, y, p (discrete logarithm)

This asymmetry powers Diffie-Hellman and ElGamal cryptosystems.

---

## Symmetric Cryptography

**Symmetric encryption**: Same key for encryption and decryption.

```
Encrypt: Ciphertext = E(Key, Plaintext)
Decrypt: Plaintext  = D(Key, Ciphertext)
```

### Stream Ciphers

**Concept**: Combine plaintext with a keystream bit-by-bit using XOR.

```
Keystream: K₁K₂K₃K₄K₅...
Plaintext: P₁P₂P₃P₄P₅...
Ciphertext: C₁=P₁⊕K₁, C₂=P₂⊕K₂, ...
```

**Decryption**: `P₁ = C₁ ⊕ K₁` (because `C₁ ⊕ K₁ = P₁ ⊕ K₁ ⊕ K₁ = P₁`)

#### RC4 (Rivest Cipher 4)

**How it works:**

1. **Key Scheduling Algorithm (KSA)**: Initialize 256-byte state array S
2. **Pseudo-Random Generation Algorithm (PRGA)**: Generate keystream bytes

```rust
// RC4 Implementation in Rust
struct RC4 {
    state: [u8; 256],
    i: u8,
    j: u8,
}

impl RC4 {
    fn new(key: &[u8]) -> Self {
        let mut state = [0u8; 256];
        
        // Initialize state array with 0..255
        for i in 0..256 {
            state[i] = i as u8;
        }
        
        // KSA: Key Scheduling
        let mut j = 0u8;
        for i in 0..256 {
            j = j.wrapping_add(state[i])
                 .wrapping_add(key[i % key.len()]);
            state.swap(i, j as usize);
        }
        
        RC4 { state, i: 0, j: 0 }
    }
    
    fn generate_keystream_byte(&mut self) -> u8 {
        // PRGA: Pseudo-Random Generation
        self.i = self.i.wrapping_add(1);
        self.j = self.j.wrapping_add(self.state[self.i as usize]);
        
        self.state.swap(self.i as usize, self.j as usize);
        
        let k_index = self.state[self.i as usize]
                          .wrapping_add(self.state[self.j as usize]);
        self.state[k_index as usize]
    }
    
    fn encrypt(&mut self, plaintext: &[u8]) -> Vec<u8> {
        plaintext.iter()
                 .map(|&byte| byte ^ self.generate_keystream_byte())
                 .collect()
    }
    
    fn decrypt(&mut self, ciphertext: &[u8]) -> Vec<u8> {
        // Encryption and decryption are identical in stream ciphers
        self.encrypt(ciphertext)
    }
}

// Usage
fn main() {
    let key = b"SecretKey";
    let plaintext = b"ATTACK AT DAWN";
    
    let mut cipher = RC4::new(key);
    let ciphertext = cipher.encrypt(plaintext);
    
    let mut decipher = RC4::new(key);
    let decrypted = decipher.decrypt(&ciphertext);
    
    println!("Plaintext:  {:?}", String::from_utf8_lossy(plaintext));
    println!("Ciphertext: {:x?}", ciphertext);
    println!("Decrypted:  {:?}", String::from_utf8_lossy(&decrypted));
}
```

**Time Complexity**: O(n) for n bytes  
**Space Complexity**: O(1) - fixed 256-byte state

**Security Note**: RC4 has known biases and is deprecated. Modern alternative: **ChaCha20**.

#### ChaCha20

**Modern stream cipher** using ARX operations (Add-Rotate-XOR).

**Core idea**: Use a 512-bit state matrix, apply quarter-round function 20 times (hence "20"), produce 64-byte keystream blocks.

**State Layout** (16 words, 32-bit each):
```
[0-3]:   Constants ("expand 32-byte k")
[4-11]:  256-bit key
[12]:    32-bit block counter
[13-15]: 96-bit nonce
```

```rust
// ChaCha20 Core Quarter Round
fn quarter_round(state: &mut [u32], a: usize, b: usize, c: usize, d: usize) {
    state[a] = state[a].wrapping_add(state[b]);
    state[d] ^= state[a];
    state[d] = state[d].rotate_left(16);
    
    state[c] = state[c].wrapping_add(state[d]);
    state[b] ^= state[c];
    state[b] = state[b].rotate_left(12);
    
    state[a] = state[a].wrapping_add(state[b]);
    state[d] ^= state[a];
    state[d] = state[d].rotate_left(8);
    
    state[c] = state[c].wrapping_add(state[d]);
    state[b] ^= state[c];
    state[b] = state[b].rotate_left(7);
}

struct ChaCha20 {
    key: [u32; 8],
    nonce: [u32; 3],
    counter: u32,
}

impl ChaCha20 {
    fn new(key: &[u8; 32], nonce: &[u8; 12]) -> Self {
        let mut key_words = [0u32; 8];
        let mut nonce_words = [0u32; 3];
        
        for i in 0..8 {
            key_words[i] = u32::from_le_bytes([
                key[i*4], key[i*4+1], key[i*4+2], key[i*4+3]
            ]);
        }
        
        for i in 0..3 {
            nonce_words[i] = u32::from_le_bytes([
                nonce[i*4], nonce[i*4+1], nonce[i*4+2], nonce[i*4+3]
            ]);
        }
        
        ChaCha20 { key: key_words, nonce: nonce_words, counter: 0 }
    }
    
    fn generate_block(&mut self) -> [u8; 64] {
        // Constants
        const CONSTANTS: [u32; 4] = [
            0x61707865, 0x3320646e, 0x79622d32, 0x6b206574
        ];
        
        // Initialize state
        let mut state = [0u32; 16];
        state[0..4].copy_from_slice(&CONSTANTS);
        state[4..12].copy_from_slice(&self.key);
        state[12] = self.counter;
        state[13..16].copy_from_slice(&self.nonce);
        
        let mut working_state = state;
        
        // 20 rounds (10 double rounds)
        for _ in 0..10 {
            // Column rounds
            quarter_round(&mut working_state, 0, 4, 8, 12);
            quarter_round(&mut working_state, 1, 5, 9, 13);
            quarter_round(&mut working_state, 2, 6, 10, 14);
            quarter_round(&mut working_state, 3, 7, 11, 15);
            
            // Diagonal rounds
            quarter_round(&mut working_state, 0, 5, 10, 15);
            quarter_round(&mut working_state, 1, 6, 11, 12);
            quarter_round(&mut working_state, 2, 7, 8, 13);
            quarter_round(&mut working_state, 3, 4, 9, 14);
        }
        
        // Add original state
        for i in 0..16 {
            working_state[i] = working_state[i].wrapping_add(state[i]);
        }
        
        self.counter += 1;
        
        // Serialize to bytes
        let mut output = [0u8; 64];
        for i in 0..16 {
            let bytes = working_state[i].to_le_bytes();
            output[i*4..(i+1)*4].copy_from_slice(&bytes);
        }
        output
    }
    
    fn encrypt(&mut self, plaintext: &[u8]) -> Vec<u8> {
        let mut ciphertext = Vec::with_capacity(plaintext.len());
        let mut keystream_buffer = [0u8; 64];
        let mut buffer_pos = 64; // Force initial block generation
        
        for &byte in plaintext {
            if buffer_pos >= 64 {
                keystream_buffer = self.generate_block();
                buffer_pos = 0;
            }
            ciphertext.push(byte ^ keystream_buffer[buffer_pos]);
            buffer_pos += 1;
        }
        
        ciphertext
    }
}
```

**Performance**: ~2-3 cycles/byte on modern CPUs  
**Security**: 256-bit key, resistant to timing attacks

---

### Block Ciphers

**Concept**: Encrypt fixed-size blocks (typically 128 bits) at a time.

**Problem**: What if message isn't a multiple of block size?  
**Solution**: Padding and modes of operation.

#### AES (Advanced Encryption Standard)

**The gold standard** for symmetric encryption. Winner of NIST competition (2001).

**Key Sizes**: 128, 192, or 256 bits  
**Block Size**: Always 128 bits (16 bytes)

**High-Level Structure**:
1. **SubBytes**: Non-linear substitution using S-box
2. **ShiftRows**: Permute bytes in each row
3. **MixColumns**: Matrix multiplication in Galois Field GF(2⁸)
4. **AddRoundKey**: XOR with round key

**Number of Rounds**:
- AES-128: 10 rounds
- AES-192: 12 rounds
- AES-256: 14 rounds

```
┌─────────────────────────────────────┐
│         Initial Round Key           │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│         Round 1..N-1:               │
│  • SubBytes (S-box substitution)    │
│  • ShiftRows (row permutation)      │
│  • MixColumns (column mixing)       │
│  • AddRoundKey (XOR with key)       │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│         Final Round N:              │
│  • SubBytes                         │
│  • ShiftRows                        │
│  • AddRoundKey (no MixColumns)      │
└─────────────────────────────────────┘
```

**Why AES is secure**:
- **Confusion**: Each output bit depends on multiple input bits (via S-box)
- **Diffusion**: Change in one input bit affects ~50% of output bits (via MixColumns)
- **Key Schedule**: Derives unique round keys from master key

```c
// AES-128 Implementation in C (Educational - Use Production Libraries in Real Code)
#include <stdint.h>
#include <string.h>

// AES S-box (precomputed lookup table)
static const uint8_t sbox[256] = {
    0x63, 0x7c, 0x77, 0x7b, 0xf2, 0x6b, 0x6f, 0xc5,
    0x30, 0x01, 0x67, 0x2b, 0xfe, 0xd7, 0xab, 0x76,
    // ... (full 256 values)
    // Omitted for brevity - in production, include all values
};

// Inverse S-box for decryption
static const uint8_t inv_sbox[256] = {
    0x52, 0x09, 0x6a, 0xd5, 0x30, 0x36, 0xa5, 0x38,
    // ... (full 256 values)
};

// Round constants for key expansion
static const uint8_t rcon[10] = {
    0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80, 0x1b, 0x36
};

typedef struct {
    uint8_t round_keys[11][16]; // 11 round keys for AES-128
} AES128_Context;

// Galois Field multiplication by 2
static uint8_t gmul2(uint8_t a) {
    return (a << 1) ^ (((a >> 7) & 1) * 0x1b);
}

// Galois Field multiplication by 3
static uint8_t gmul3(uint8_t a) {
    return gmul2(a) ^ a;
}

// SubBytes transformation
static void sub_bytes(uint8_t state[16]) {
    for (int i = 0; i < 16; i++) {
        state[i] = sbox[state[i]];
    }
}

// ShiftRows transformation
static void shift_rows(uint8_t state[16]) {
    uint8_t temp;
    
    // Row 1: shift left by 1
    temp = state[1];
    state[1] = state[5];
    state[5] = state[9];
    state[9] = state[13];
    state[13] = temp;
    
    // Row 2: shift left by 2
    temp = state[2];
    state[2] = state[10];
    state[10] = temp;
    temp = state[6];
    state[6] = state[14];
    state[14] = temp;
    
    // Row 3: shift left by 3
    temp = state[15];
    state[15] = state[11];
    state[11] = state[7];
    state[7] = state[3];
    state[3] = temp;
}

// MixColumns transformation
static void mix_columns(uint8_t state[16]) {
    uint8_t temp[16];
    
    for (int i = 0; i < 4; i++) {
        int col = i * 4;
        temp[col]   = gmul2(state[col]) ^ gmul3(state[col+1]) ^ 
                      state[col+2] ^ state[col+3];
        temp[col+1] = state[col] ^ gmul2(state[col+1]) ^ 
                      gmul3(state[col+2]) ^ state[col+3];
        temp[col+2] = state[col] ^ state[col+1] ^ 
                      gmul2(state[col+2]) ^ gmul3(state[col+3]);
        temp[col+3] = gmul3(state[col]) ^ state[col+1] ^ 
                      state[col+2] ^ gmul2(state[col+3]);
    }
    
    memcpy(state, temp, 16);
}

// AddRoundKey transformation
static void add_round_key(uint8_t state[16], const uint8_t round_key[16]) {
    for (int i = 0; i < 16; i++) {
        state[i] ^= round_key[i];
    }
}

// Key expansion for AES-128
void aes128_key_expansion(AES128_Context *ctx, const uint8_t key[16]) {
    memcpy(ctx->round_keys[0], key, 16);
    
    for (int round = 1; round <= 10; round++) {
        uint8_t *prev = ctx->round_keys[round - 1];
        uint8_t *curr = ctx->round_keys[round];
        
        // RotWord and SubWord on last column
        uint8_t temp[4] = {
            sbox[prev[13]],
            sbox[prev[14]],
            sbox[prev[15]],
            sbox[prev[12]]
        };
        
        // XOR with Rcon
        temp[0] ^= rcon[round - 1];
        
        // Generate new round key
        for (int i = 0; i < 4; i++) {
            curr[i] = prev[i] ^ temp[i];
        }
        for (int i = 4; i < 16; i++) {
            curr[i] = curr[i-4] ^ prev[i];
        }
    }
}

// AES-128 encryption of single block
void aes128_encrypt_block(const AES128_Context *ctx, 
                          uint8_t block[16]) {
    // Initial round
    add_round_key(block, ctx->round_keys[0]);
    
    // Main rounds (1-9)
    for (int round = 1; round < 10; round++) {
        sub_bytes(block);
        shift_rows(block);
        mix_columns(block);
        add_round_key(block, ctx->round_keys[round]);
    }
    
    // Final round (no MixColumns)
    sub_bytes(block);
    shift_rows(block);
    add_round_key(block, ctx->round_keys[10]);
}
```

**Time Complexity**: O(1) - fixed 10 rounds for AES-128  
**Space Complexity**: O(1) - fixed state and key size

**Hardware Acceleration**: Modern CPUs have AES-NI instructions, achieving 1-2 cycles/byte.

#### Block Cipher Modes of Operation

**Problem**: How to encrypt messages longer than one block?

##### ECB (Electronic Codebook) - NEVER USE

```
Block 1 → AES → Ciphertext 1
Block 2 → AES → Ciphertext 2
Block 3 → AES → Ciphertext 3
```

**Fatal Flaw**: Identical plaintext blocks → identical ciphertext blocks  
**Security**: Reveals patterns in data (e.g., penguin image remains recognizable)

##### CBC (Cipher Block Chaining)

```
IV → XOR → AES → C₁
      ↑           ↓
     P₁      C₁ → XOR → AES → C₂
                   ↑           ↓
                  P₂      C₂ → XOR → AES → C₃
```

**Encryption**: `C₁ = E(P₁ ⊕ IV)`, `Cᵢ = E(Pᵢ ⊕ Cᵢ₋₁)`  
**Decryption**: `P₁ = D(C₁) ⊕ IV`, `Pᵢ = D(Cᵢ) ⊕ Cᵢ₋₁`

**IV (Initialization Vector)**: Random value for first block, prevents identical plaintexts → identical ciphertexts.

```go
// CBC Mode in Go
package main

import (
    "crypto/aes"
    "crypto/cipher"
    "crypto/rand"
    "fmt"
)

func pkcs7Pad(data []byte, blockSize int) []byte {
    padding := blockSize - (len(data) % blockSize)
    padText := make([]byte, padding)
    for i := range padText {
        padText[i] = byte(padding)
    }
    return append(data, padText...)
}

func pkcs7Unpad(data []byte) []byte {
    length := len(data)
    padding := int(data[length-1])
    return data[:length-padding]
}

func encryptCBC(key, plaintext []byte) ([]byte, error) {
    block, err := aes.NewCipher(key)
    if err != nil {
        return nil, err
    }
    
    // Pad plaintext to block size
    plaintext = pkcs7Pad(plaintext, aes.BlockSize)
    
    // Generate random IV
    ciphertext := make([]byte, aes.BlockSize+len(plaintext))
    iv := ciphertext[:aes.BlockSize]
    if _, err := rand.Read(iv); err != nil {
        return nil, err
    }
    
    // Encrypt
    mode := cipher.NewCBCEncrypter(block, iv)
    mode.CryptBlocks(ciphertext[aes.BlockSize:], plaintext)
    
    return ciphertext, nil // IV prepended to ciphertext
}

func decryptCBC(key, ciphertext []byte) ([]byte, error) {
    block, err := aes.NewCipher(key)
    if err != nil {
        return nil, err
    }
    
    // Extract IV
    iv := ciphertext[:aes.BlockSize]
    ciphertext = ciphertext[aes.BlockSize:]
    
    // Decrypt
    mode := cipher.NewCBCDecrypter(block, iv)
    plaintext := make([]byte, len(ciphertext))
    mode.CryptBlocks(plaintext, ciphertext)
    
    // Remove padding
    return pkcs7Unpad(plaintext), nil
}

func main() {
    key := []byte("AES256Key-32BytesLongForAES256!") // Must be 16, 24, or 32 bytes
    plaintext := []byte("Secret message to encrypt")
    
    encrypted, _ := encryptCBC(key[:16], plaintext) // Use AES-128
    fmt.Printf("Ciphertext: %x\n", encrypted)
    
    decrypted, _ := decryptCBC(key[:16], encrypted)
    fmt.Printf("Decrypted: %s\n", decrypted)
}
```

**Limitations**:
- Sequential: Can't parallelize encryption
- Error propagation: Bit flip in Cᵢ affects Pᵢ and Pᵢ₊₁

##### CTR (Counter Mode) - Recommended

**Concept**: Turn block cipher into stream cipher.

```
Counter 1 → AES → Keystream₁ ⊕ P₁ → C₁
Counter 2 → AES → Keystream₂ ⊕ P₂ → C₂
Counter 3 → AES → Keystream₃ ⊕ P₃ → C₃
```

**Encryption/Decryption**: `Cᵢ = Pᵢ ⊕ E(Nonce || Counter)`

**Advantages**:
- **Parallel**: All blocks independent
- **Random access**: Can decrypt any block without decrypting previous ones
- **No padding needed**: XOR works on any length

```rust
// CTR Mode in Rust (using aes crate)
use aes::Aes128;
use aes::cipher::{BlockEncrypt, KeyInit};
use aes::cipher::generic_array::GenericArray;

struct AesCtr {
    cipher: Aes128,
    nonce: [u8; 8],
    counter: u64,
}

impl AesCtr {
    fn new(key: &[u8; 16], nonce: &[u8; 8]) -> Self {
        AesCtr {
            cipher: Aes128::new(GenericArray::from_slice(key)),
            nonce: *nonce,
            counter: 0,
        }
    }
    
    fn generate_keystream_block(&mut self) -> [u8; 16] {
        let mut block = [0u8; 16];
        block[0..8].copy_from_slice(&self.nonce);
        block[8..16].copy_from_slice(&self.counter.to_be_bytes());
        
        let mut ga_block = GenericArray::clone_from_slice(&block);
        self.cipher.encrypt_block(&mut ga_block);
        
        self.counter += 1;
        ga_block.into()
    }
    
    fn process(&mut self, data: &[u8]) -> Vec<u8> {
        let mut result = Vec::with_capacity(data.len());
        let mut keystream = [0u8; 16];
        let mut ks_pos = 16; // Force initial generation
        
        for &byte in data {
            if ks_pos >= 16 {
                keystream = self.generate_keystream_block();
                ks_pos = 0;
            }
            result.push(byte ^ keystream[ks_pos]);
            ks_pos += 1;
        }
        
        result
    }
    
    fn encrypt(&mut self, plaintext: &[u8]) -> Vec<u8> {
        self.process(plaintext)
    }
    
    fn decrypt(&mut self, ciphertext: &[u8]) -> Vec<u8> {
        self.process(ciphertext) // Identical to encryption
    }
}
```

**Critical**: Never reuse (nonce, counter) pair with same key!

##### GCM (Galois/Counter Mode) - Industry Standard

**GCM = CTR + Authentication**

Provides **both confidentiality and integrity** in one operation.

```
┌─────────────────────────────────┐
│   CTR Mode Encryption           │
│   P₁, P₂, ... → C₁, C₂, ...    │
└─────────────────────────────────┘
              ↓
┌─────────────────────────────────┐
│   GHASH Authentication          │
│   C₁, C₂, ..., AAD → Tag        │
└─────────────────────────────────┘
```

**Components**:
- **CTR**: Encrypts plaintext
- **GHASH**: Computes authentication tag over ciphertext + AAD
- **AAD (Additional Authenticated Data)**: Metadata (not encrypted, but authenticated)
- **Tag**: 128-bit authentication tag

**Why GCM**:
- Single pass: Encrypt + authenticate simultaneously
- Fast: Hardware acceleration (PCLMULQDQ instruction)
- Secure: Prevents tampering

**Real-world use**: TLS 1.3, IPsec, SSH

---

## Asymmetric Cryptography

**Asymmetric encryption**: Different keys for encryption (public) and decryption (private).

```
Public Key (pk)  → Anyone can encrypt
Private Key (sk) → Only owner can decrypt
```

**Mathematical Foundation**: One-way functions with trapdoor.

### RSA (Rivest-Shamir-Adleman)

**Based on**: Difficulty of factoring large semiprimes.

#### Key Generation

1. **Choose primes**: Pick two large primes p, q (typically 1024-2048 bits each)
2. **Compute modulus**: `n = p × q`
3. **Compute totient**: `φ(n) = (p-1)(q-1)`
4. **Choose public exponent**: `e` (commonly 65537), where `GCD(e, φ(n)) = 1`
5. **Compute private exponent**: `d = e⁻¹ mod φ(n)` (modular multiplicative inverse)

**Public Key**: `(n, e)`  
**Private Key**: `(n, d)` or `(p, q, d)` for faster decryption

#### Encryption/Decryption

**Encryption**: `C = M^e mod n`  
**Decryption**: `M = C^d mod n`

**Why it works**:
```
C^d = (M^e)^d = M^(ed) mod n
```
By Euler's theorem: `ed ≡ 1 (mod φ(n))`, so `M^(ed) ≡ M (mod n)`

```rust
// RSA Implementation in Rust (Educational)
use num_bigint::{BigUint, RandBigInt};
use num_traits::{One, Zero};
use rand::thread_rng;

// Extended Euclidean Algorithm for modular inverse
fn mod_inverse(a: &BigUint, m: &BigUint) -> Option<BigUint> {
    fn extended_gcd(a: &BigUint, b: &BigUint) -> (BigUint, BigUint, BigUint) {
        if b.is_zero() {
            return (a.clone(), One::one(), Zero::zero());
        }
        let (gcd, x1, y1) = extended_gcd(b, &(a % b));
        let x = y1.clone();
        let y = if x1 >= (a / b) * &y1 {
            &x1 - (a / b) * &y1
        } else {
            m - ((a / b) * &y1 - &x1)
        };
        (gcd, x, y)
    }
    
    let (gcd, x, _) = extended_gcd(a, m);
    if gcd == One::one() {
        Some(x % m)
    } else {
        None
    }
}

// Miller-Rabin primality test
fn is_probably_prime(n: &BigUint, k: usize) -> bool {
    if n <= &BigUint::from(1u32) { return false; }
    if n <= &BigUint::from(3u32) { return true; }
    if n % 2u32 == Zero::zero() { return false; }
    
    // Write n-1 as 2^r * d
    let n_minus_1 = n - 1u32;
    let mut d = n_minus_1.clone();
    let mut r = 0;
    while &d % 2u32 == Zero::zero() {
        d /= 2u32;
        r += 1;
    }
    
    let mut rng = thread_rng();
    'witness: for _ in 0..k {
        let a = rng.gen_biguint_range(&BigUint::from(2u32), &(n - 2u32));
        let mut x = a.modpow(&d, n);
        
        if x == One::one() || x == n_minus_1 {
            continue 'witness;
        }
        
        for _ in 0..r-1 {
            x = x.modpow(&BigUint::from(2u32), n);
            if x == n_minus_1 {
                continue 'witness;
            }
        }
        return false;
    }
    true
}

struct RSAKeyPair {
    pub n: BigUint,
    pub e: BigUint,
    pub d: BigUint,
}

impl RSAKeyPair {
    fn generate(bits: usize) -> Self {
        let mut rng = thread_rng();
        
        // Generate two distinct primes
        let mut p = rng.gen_biguint(bits / 2);
        while !is_probably_prime(&p, 20) {
            p = rng.gen_biguint(bits / 2);
        }
        
        let mut q = rng.gen_biguint(bits / 2);
        while !is_probably_prime(&q, 20) || p == q {
            q = rng.gen_biguint(bits / 2);
        }
        
        let n = &p * &q;
        let phi = (&p - 1u32) * (&q - 1u32);
        
        // Use e = 65537 (common choice)
        let e = BigUint::from(65537u32);
        
        // Compute d = e^(-1) mod phi(n)
        let d = mod_inverse(&e, &phi).expect("Failed to compute modular inverse");
        
        RSAKeyPair { n, e, d }
    }
    
    fn encrypt(&self, message: &BigUint) -> BigUint {
        message.modpow(&self.e, &self.n)
    }
    
    fn decrypt(&self, ciphertext: &BigUint) -> BigUint {
        ciphertext.modpow(&self.d, &self.n)
    }
}

fn main() {
    let keypair = RSAKeyPair::generate(2048);
    
    let message = BigUint::from(42u32);
    println!("Original: {}", message);
    
    let encrypted = keypair.encrypt(&message);
    println!("Encrypted: {}", encrypted);
    
    let decrypted = keypair.decrypt(&encrypted);
    println!("Decrypted: {}", decrypted);
}
```

**Time Complexity**:
- Key Generation: O(k³) where k = bit length (due to primality testing)
- Encryption: O(log e) modular multiplications
- Decryption: O(log d) modular multiplications

**Security**:
- **2048-bit RSA**: ~112-bit security (factoring difficulty)
- **4096-bit RSA**: ~152-bit security

**Limitations**:
- Slow compared to symmetric encryption (1000x slower than AES)
- Deterministic: Same plaintext → same ciphertext
- Malleable: `Encrypt(m₁) × Encrypt(m₂) = Encrypt(m₁ × m₂)`

**Solution**: Use padding schemes (OAEP) and hybrid encryption.

#### RSA-OAEP (Optimal Asymmetric Encryption Padding)

**Problem**: Raw RSA is deterministic and malleable.

**OAEP adds**:
- Randomness (via hash functions)
- All-or-nothing transform (prevents partial decryption)

```
Message M → Padding → Padded M → RSA → Ciphertext
```

**Used in**: TLS, PGP, S/MIME

### Elliptic Curve Cryptography (ECC)

**Key insight**: Use elliptic curves over finite fields instead of integer factorization.

**Elliptic Curve**: Points (x, y) satisfying `y² = x³ + ax + b mod p`

**Example curve** (secp256k1, used in Bitcoin):
```
y² = x³ + 7 mod p
p = 2²⁵⁶ - 2³² - 977
```

#### Point Addition

**Geometric interpretation**: Draw line through two points, find third intersection, reflect.

```
     y
     │
  P  •
     │\
     │ \
     │  •─── Line through P and Q
     │ /
  Q  •
     │
     └────── x
```

**Algebraic formula**:
- If `P = (x₁, y₁)` and `Q = (x₂, y₂)`:
  - `slope = (y₂ - y₁) / (x₂ - x₁) mod p`
  - `x₃ = slope² - x₁ - x₂ mod p`
  - `y₃ = slope(x₁ - x₃) - y₁ mod p`
  - `R = (x₃, y₃)`

**Scalar Multiplication**: `nP = P + P + ... + P` (n times)

**Hard Problem**: Given P and Q = nP, find n (Elliptic Curve Discrete Log)

#### ECDH (Elliptic Curve Diffie-Hellman)

**Key Exchange Protocol**:

```
Alice:                           Bob:
Private: a                       Private: b
Public:  A = aG                  Public:  B = bG

       A ──────────────────→
       ←────────────────── B

Shared: S = aB = a(bG)          Shared: S = bA = b(aG)
        = abG                           = abG
```

**Security**: Attacker sees A, B, G but can't compute abG (discrete log).

```go
// ECDH Key Exchange in Go
package main

import (
    "crypto/ecdsa"
    "crypto/elliptic"
    "crypto/rand"
    "crypto/sha256"
    "fmt"
    "math/big"
)

func main() {
    // Use P-256 curve (NIST recommended)
    curve := elliptic.P256()
    
    // Alice generates key pair
    alicePrivate, _ := ecdsa.GenerateKey(curve, rand.Reader)
    alicePublic := &alicePrivate.PublicKey
    
    // Bob generates key pair
    bobPrivate, _ := ecdsa.GenerateKey(curve, rand.Reader)
    bobPublic := &bobPrivate.PublicKey
    
    // Alice computes shared secret: alice_private * bob_public
    aliceSharedX, _ := curve.ScalarMult(bobPublic.X, bobPublic.Y, 
                                         alicePrivate.D.Bytes())
    
    // Bob computes shared secret: bob_private * alice_public
    bobSharedX, _ := curve.ScalarMult(alicePublic.X, alicePublic.Y, 
                                       bobPrivate.D.Bytes())
    
    // Derive symmetric key from shared secret
    aliceKey := sha256.Sum256(aliceSharedX.Bytes())
    bobKey := sha256.Sum256(bobSharedX.Bytes())
    
    fmt.Printf("Alice's key: %x\n", aliceKey)
    fmt.Printf("Bob's key:   %x\n", bobKey)
    fmt.Printf("Keys match:  %v\n", aliceKey == bobKey)
}
```

**Advantages over RSA**:
- **Smaller keys**: 256-bit ECC ≈ 3072-bit RSA security
- **Faster**: Scalar multiplication faster than modular exponentiation
- **Bandwidth**: Less data to transmit

**Common Curves**:
- **P-256** (secp256r1): NIST standard, 128-bit security
- **Curve25519**: Modern, side-channel resistant, used in Signal, SSH
- **secp256k1**: Bitcoin, Ethereum

---

## Hash Functions & MACs

### Cryptographic Hash Functions

**Definition**: One-way function `H: {0,1}* → {0,1}ⁿ`

**Properties**:
1. **Deterministic**: Same input → same output
2. **Fast**: Quick to compute
3. **Pre-image resistance**: Given `h`, hard to find `m` where `H(m) = h`
4. **Second pre-image resistance**: Given `m₁`, hard to find `m₂ ≠ m₁` where `H(m₁) = H(m₂)`
5. **Collision resistance**: Hard to find any `m₁ ≠ m₂` where `H(m₁) = H(m₂)`
6. **Avalanche effect**: 1-bit change in input → ~50% bits change in output

### SHA-2 Family

**SHA-256** (Secure Hash Algorithm, 256-bit output)

**Structure**: Merkle-Damgård construction

```
Message → Padding → Split into 512-bit blocks
          ↓
   Block₁ → Compression Function → State₁
          ↓
   Block₂ → Compression Function → State₂
          ↓
        ... → Final State (256 bits)
```

**Compression Function**:
- 64 rounds of operations
- Uses 8 working variables (a, b, c, d, e, f, g, h)
- Mix of bitwise operations: AND, OR, XOR, NOT, rotate, shift
- Constants derived from cube roots of first 64 primes

```c
// SHA-256 Core (Simplified)
#include <stdint.h>
#include <string.h>

// SHA-256 Constants (first 32 bits of fractional parts of cube roots)
static const uint32_t K[64] = {
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5,
    0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
    // ... (64 values total)
};

// Initial hash values (first 32 bits of fractional parts of square roots)
static const uint32_t H0[8] = {
    0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a,
    0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19
};

// Right rotate
#define ROTR(x, n) (((x) >> (n)) | ((x) << (32 - (n))))

// SHA-256 functions
#define CH(x, y, z)  (((x) & (y)) ^ (~(x) & (z)))
#define MAJ(x, y, z) (((x) & (y)) ^ ((x) & (z)) ^ ((y) & (z)))
#define EP0(x) (ROTR(x,2) ^ ROTR(x,13) ^ ROTR(x,22))
#define EP1(x) (ROTR(x,6) ^ ROTR(x,11) ^ ROTR(x,25))
#define SIG0(x) (ROTR(x,7) ^ ROTR(x,18) ^ ((x) >> 3))
#define SIG1(x) (ROTR(x,17) ^ ROTR(x,19) ^ ((x) >> 10))

typedef struct {
    uint8_t data[64];
    uint32_t datalen;
    uint64_t bitlen;
    uint32_t state[8];
} SHA256_CTX;

void sha256_transform(SHA256_CTX *ctx, const uint8_t data[]) {
    uint32_t a, b, c, d, e, f, g, h, t1, t2, w[64];
    int i;
    
    // Prepare message schedule
    for (i = 0; i < 16; i++) {
        w[i] = (data[i*4] << 24) | (data[i*4+1] << 16) | 
               (data[i*4+2] << 8) | (data[i*4+3]);
    }
    for (i = 16; i < 64; i++) {
        w[i] = SIG1(w[i-2]) + w[i-7] + SIG0(w[i-15]) + w[i-16];
    }
    
    // Initialize working variables
    a = ctx->state[0];
    b = ctx->state[1];
    c = ctx->state[2];
    d = ctx->state[3];
    e = ctx->state[4];
    f = ctx->state[5];
    g = ctx->state[6];
    h = ctx->state[7];
    
    // 64 rounds
    for (i = 0; i < 64; i++) {
        t1 = h + EP1(e) + CH(e,f,g) + K[i] + w[i];
        t2 = EP0(a) + MAJ(a,b,c);
        h = g;
        g = f;
        f = e;
        e = d + t1;
        d = c;
        c = b;
        b = a;
        a = t1 + t2;
    }
    
    // Update state
    ctx->state[0] += a;
    ctx->state[1] += b;
    ctx->state[2] += c;
    ctx->state[3] += d;
    ctx->state[4] += e;
    ctx->state[5] += f;
    ctx->state[6] += g;
    ctx->state[7] += h;
}

void sha256_init(SHA256_CTX *ctx) {
    ctx->datalen = 0;
    ctx->bitlen = 0;
    memcpy(ctx->state, H0, sizeof(H0));
}

void sha256_update(SHA256_CTX *ctx, const uint8_t data[], size_t len) {
    for (size_t i = 0; i < len; i++) {
        ctx->data[ctx->datalen] = data[i];
        ctx->datalen++;
        if (ctx->datalen == 64) {
            sha256_transform(ctx, ctx->data);
            ctx->bitlen += 512;
            ctx->datalen = 0;
        }
    }
}

void sha256_final(SHA256_CTX *ctx, uint8_t hash[]) {
    uint32_t i = ctx->datalen;
    
    // Pad with 0x80 followed by zeros
    ctx->data[i++] = 0x80;
    if (ctx->datalen < 56) {
        while (i < 56)
            ctx->data[i++] = 0x00;
    } else {
        while (i < 64)
            ctx->data[i++] = 0x00;
        sha256_transform(ctx, ctx->data);
        memset(ctx->data, 0, 56);
    }
    
    // Append length in bits
    ctx->bitlen += ctx->datalen * 8;
    ctx->data[63] = ctx->bitlen;
    ctx->data[62] = ctx->bitlen >> 8;
    ctx->data[61] = ctx->bitlen >> 16;
    ctx->data[60] = ctx->bitlen >> 24;
    ctx->data[59] = ctx->bitlen >> 32;
    ctx->data[58] = ctx->bitlen >> 40;
    ctx->data[57] = ctx->bitlen >> 48;
    ctx->data[56] = ctx->bitlen >> 56;
    sha256_transform(ctx, ctx->data);
    
    // Produce final hash
    for (i = 0; i < 4; i++) {
        hash[i]    = (ctx->state[0] >> (24-i*8)) & 0xff;
        hash[i+4]  = (ctx->state[1] >> (24-i*8)) & 0xff;
        hash[i+8]  = (ctx->state[2] >> (24-i*8)) & 0xff;
        hash[i+12] = (ctx->state[3] >> (24-i*8)) & 0xff;
        hash[i+16] = (ctx->state[4] >> (24-i*8)) & 0xff;
        hash[i+20] = (ctx->state[5] >> (24-i*8)) & 0xff;
        hash[i+24] = (ctx->state[6] >> (24-i*8)) & 0xff;
        hash[i+28] = (ctx->state[7] >> (24-i*8)) & 0xff;
    }
}
```

**Performance**: ~450 MB/s in software, 3+ GB/s with hardware acceleration

**Use Cases**:
- Password hashing (with salt)
- Digital signatures
- Blockchain (Bitcoin uses SHA-256)
- File integrity (checksums)

### SHA-3 (Keccak)

**Different design**: Sponge construction (not Merkle-Damgård)

```
┌──────────────────────────────────┐
│   Absorbing Phase                │
│   Message → XOR into state       │
│            → Permutation         │
└──────────────────────────────────┘
              ↓
┌──────────────────────────────────┐
│   Squeezing Phase                │
│   Extract hash from state        │
│            → Permutation (repeat)│
└──────────────────────────────────┘
```

**Advantages**:
- Immune to length-extension attacks
- Flexible output length
- Better security margin

**Use**: NIST standard (2015), backup if SHA-2 is broken

### HMAC (Hash-based Message Authentication Code)

**Purpose**: Provide authentication AND integrity (not just hash).

**Construction**:
```
HMAC(K, M) = H((K ⊕ opad) || H((K ⊕ ipad) || M))
```

Where:
- `K` = secret key
- `M` = message
- `ipad` = 0x36 repeated
- `opad` = 0x5c repeated
- `||` = concatenation

**Why two hashes**: Prevents length-extension attacks.

```rust
// HMAC-SHA256 in Rust
use sha2::{Sha256, Digest};

fn hmac_sha256(key: &[u8], message: &[u8]) -> Vec<u8> {
    const BLOCK_SIZE: usize = 64; // SHA-256 block size
    const IPAD: u8 = 0x36;
    const OPAD: u8 = 0x5c;
    
    // Key preprocessing
    let mut key_block = [0u8; BLOCK_SIZE];
    if key.len() > BLOCK_SIZE {
        // Hash long keys
        let hashed_key = Sha256::digest(key);
        key_block[..hashed_key.len()].copy_from_slice(&hashed_key);
    } else {
        key_block[..key.len()].copy_from_slice(key);
    }
    
    // Compute inner hash
    let mut inner_key = [0u8; BLOCK_SIZE];
    for i in 0..BLOCK_SIZE {
        inner_key[i] = key_block[i] ^ IPAD;
    }
    
    let mut inner_hasher = Sha256::new();
    inner_hasher.update(&inner_key);
    inner_hasher.update(message);
    let inner_hash = inner_hasher.finalize();
    
    // Compute outer hash
    let mut outer_key = [0u8; BLOCK_SIZE];
    for i in 0..BLOCK_SIZE {
        outer_key[i] = key_block[i] ^ OPAD;
    }
    
    let mut outer_hasher = Sha256::new();
    outer_hasher.update(&outer_key);
    outer_hasher.update(&inner_hash);
    
    outer_hasher.finalize().to_vec()
}

fn main() {
    let key = b"secret_key";
    let message = b"Important message";
    
    let mac = hmac_sha256(key, message);
    println!("HMAC: {:x?}", mac);
    
    // Verification
    let received_mac = hmac_sha256(key, message);
    let valid = mac == received_mac;
    println!("Valid: {}", valid);
}
```

**Security**: Requires knowing secret key to forge MAC.

**Use Cases**:
- API authentication (e.g., AWS Signature)
- Cookie signing (prevent tampering)
- Challenge-response protocols

---

## Real-World Protocol Implementations

### TLS 1.3 Handshake

**TLS (Transport Layer Security)**: Secures web traffic (HTTPS).

**Goals**:
1. Authenticate server (and optionally client)
2. Establish shared secret
3. Negotiate cipher suite

**Simplified Handshake**:

```
Client                                Server
  │                                      │
  │───── ClientHello ─────────────────→│
  │  (supported ciphers, random, KeyShare) │
  │                                      │
  │←──── ServerHello ─────────────────│
  │  (chosen cipher, random, KeyShare)   │
  │  Certificate                         │
  │  CertificateVerify (signature)       │
  │  Finished (MAC of transcript)        │
  │                                      │
  │───── Finished ────────────────────→│
  │  (MAC of transcript)                 │
  │                                      │
  │←──── Application Data ───────────→│
  │  (encrypted with AES-GCM)            │
```

**Key Derivation** (using ECDH):
1. Client generates ephemeral key pair `(c_priv, c_pub)`
2. Server generates ephemeral key pair `(s_priv, s_pub)`
3. Exchange public keys in `KeyShare`
4. Both compute shared secret: `S = ECDH(c_priv, s_pub) = ECDH(s_priv, c_pub)`
5. Derive encryption keys using HKDF (HMAC-based KDF):
   ```
   Master Secret = HKDF-Extract(Salt, S)
   Client Key = HKDF-Expand(Master Secret, "client key", ...)
   Server Key = HKDF-Expand(Master Secret, "server key", ...)
   ```

**Cipher Suite** (example: `TLS_AES_128_GCM_SHA256`):
- **AES-128-GCM**: Bulk encryption
- **SHA-256**: Hash function for HMAC/HKDF
- **ECDHE**: Key exchange (Elliptic Curve Diffie-Hellman Ephemeral)

**Forward Secrecy**: Ephemeral keys mean compromised long-term key doesn't decrypt past sessions.

### Password Hashing

**Problem**: Never store passwords in plaintext!

**Naive approach** (BAD):
```
Hash(password) → Store in database
```

**Attack**: Rainbow tables (precomputed hash → password mappings)

**Better approach**: **Salt + Hash**

```
Salt = random_bytes(16)
Hash = SHA256(password || salt)
Store (salt, hash)
```

**Why**: Different salt for each user → can't precompute rainbow table.

**Best practice**: Use **password-hashing functions** designed to be slow.

#### bcrypt

**Design**: Based on Blowfish cipher, intentionally slow.

**Cost factor**: `2^cost` iterations (e.g., cost=12 → 4096 iterations)

```go
// bcrypt in Go
package main

import (
    "fmt"
    "golang.org/x/crypto/bcrypt"
)

func main() {
    password := []byte("my_secure_password")
    
    // Hash password (cost = 12)
    hash, err := bcrypt.GenerateFromPassword(password, 12)
    if err != nil {
        panic(err)
    }
    
    fmt.Printf("Hash: %s\n", hash)
    
    // Verify password
    err = bcrypt.CompareHashAndPassword(hash, password)
    if err == nil {
        fmt.Println("Password matches!")
    } else {
        fmt.Println("Invalid password")
    }
}
```

**Time**: ~200ms for cost=12 (adjustable based on hardware)

#### Argon2

**Modern winner**: 2015 Password Hashing Competition.

**Variants**:
- **Argon2i**: Resists side-channel attacks (password hashing)
- **Argon2d**: Resists GPU cracking (cryptocurrency mining)
- **Argon2id**: Hybrid (recommended)

**Parameters**:
- **Memory cost**: MB of RAM required
- **Time cost**: Iterations
- **Parallelism**: Number of threads

```rust
// Argon2 in Rust
use argon2::{
    password_hash::{PasswordHash, PasswordHasher, PasswordVerifier, SaltString},
    Argon2
};
use rand_core::OsRng;

fn main() {
    let password = b"hunter2";
    let salt = SaltString::generate(&mut OsRng);
    
    // Argon2 with default params (Argon2id)
    let argon2 = Argon2::default();
    
    // Hash password
    let password_hash = argon2.hash_password(password, &salt)
                              .unwrap()
                              .to_string();
    
    println!("Hash: {}", password_hash);
    
    // Verify password
    let parsed_hash = PasswordHash::new(&password_hash).unwrap();
    let result = argon2.verify_password(password, &parsed_hash);
    
    match result {
        Ok(_) => println!("Password correct!"),
        Err(_) => println!("Invalid password"),
    }
}
```

**Recommendation**: Argon2id with 64MB memory, 3 iterations, 4 threads.

### Digital Signatures

**Purpose**: Prove message came from specific sender (non-repudiation).

**Scheme**:
```
Sign:   Signature = Sign(private_key, message)
Verify: Valid = Verify(public_key, message, signature)
```

#### RSA Signatures (RSA-PSS)

**Signing**:
1. Hash message: `h = SHA256(message)`
2. Apply PSS padding to hash
3. Sign with private key: `s = h^d mod n`

**Verification**:
1. Recover hash: `h' = s^e mod n`
2. Hash message: `h = SHA256(message)`
3. Check `h == h'` (after removing padding)

#### ECDSA (Elliptic Curve Digital Signature Algorithm)

**Signing** (with private key `d`, public key `Q = dG`):
1. Choose random `k`
2. Compute `R = kG`, take `r = R_x mod n`
3. Compute `s = k^(-1)(H(m) + rd) mod n`
4. Signature = `(r, s)`

**Verification**:
1. Compute `u₁ = H(m)s^(-1) mod n`
2. Compute `u₂ = rs^(-1) mod n`
3. Compute `R' = u₁G + u₂Q`
4. Check `R'_x mod n == r`

```rust
// ECDSA Signing in Rust (using p256 crate)
use p256::ecdsa::{SigningKey, Signature, signature::Signer};
use rand_core::OsRng;

fn main() {
    // Generate key pair
    let signing_key = SigningKey::random(&mut OsRng);
    let verifying_key = signing_key.verifying_key();
    
    let message = b"Important contract";
    
    // Sign
    let signature: Signature = signing_key.sign(message);
    println!("Signature: {:?}", signature);
    
    // Verify
    use p256::ecdsa::signature::Verifier;
    match verifying_key.verify(message, &signature) {
        Ok(_) => println!("Signature valid!"),
        Err(_) => println!("Signature invalid!"),
    }
}
```

**Security**: 256-bit ECDSA ≈ 128-bit security level.

#### Ed25519 (Modern Standard)

**Advantages** over ECDSA:
- Deterministic (no random `k` → no nonce reuse vulnerabilities)
- Faster signing/verification
- Smaller signatures (64 bytes)
- Resistant to side-channel attacks

**Used in**: SSH, cryptocurrencies, Signal Protocol.

---

## Modern Cryptographic Systems

### End-to-End Encryption: Signal Protocol

**Goal**: Secure messaging with perfect forward secrecy and future secrecy.

**Components**:

1. **X3DH (Extended Triple Diffie-Hellman)**: Initial key agreement
   - Uses 3 DH exchanges for authentication + forward secrecy
   
2. **Double Ratchet Algorithm**: Message encryption
   - **DH Ratchet**: Generate new key pair each message
   - **Symmetric Ratchet**: Derive new keys from previous keys

**Message Encryption Flow**:

```
Alice                                   Bob
  │                                      │
  │──── Identity Key (long-term) ───────│
  │──── Signed Prekey ──────────────────│
  │──── Ephemeral Key ──────────────────│
  │                                      │
  │  Perform 3 DH operations:            │
  │  DH(IK_a, SPK_b)                     │
  │  DH(EK_a, IK_b)                      │
  │  DH(EK_a, SPK_b)                     │
  │                                      │
  │  Derive root key & chain key         │
  │                                      │
  │──── Encrypted Message ──────────────→│
  │  Enc(message_key, plaintext)         │
  │  MAC(mac_key, ciphertext)            │
  │                                      │
  │  Ratchet forward:                    │
  │  message_key = KDF(chain_key)        │
  │  chain_key = KDF(chain_key)          │
```

**Perfect Forward Secrecy**: Compromise of long-term keys doesn't decrypt past messages.

**Future Secrecy**: Compromised session key recovered from by next DH ratchet step.

### Zero-Knowledge Proofs

**Concept**: Prove knowledge of secret without revealing it.

**Example**: Prove you know password without sending it.

**zk-SNARK** (Zero-Knowledge Succinct Non-Interactive Argument of Knowledge):
- Used in cryptocurrencies (Zcash)
- Proves computation was done correctly without revealing inputs

**Simple Example - Discrete Log**:

```
Prover knows: x such that y = g^x mod p
Verifier knows: g, y, p

Protocol:
1. Prover picks random r, sends t = g^r mod p
2. Verifier sends random challenge c
3. Prover responds with s = r + cx
4. Verifier checks: g^s == t * y^c mod p
```

**Why it works**:
```
g^s = g^(r+cx) = g^r * g^(cx) = t * (g^x)^c = t * y^c
```

Prover can't fake without knowing x (can't compute s without x).

### Homomorphic Encryption

**Concept**: Compute on encrypted data without decrypting.

**Example**:
```
Enc(a) + Enc(b) = Enc(a + b)
Enc(a) × Enc(b) = Enc(a × b)
```

**Applications**:
- Cloud computing on sensitive data
- Private database queries
- Secure multi-party computation

**Paillier Encryption** (Additive Homomorphic):

```
Public key: (n, g) where n = pq (RSA-like)
Private key: (λ, μ) where λ = lcm(p-1, q-1)

Encrypt(m): c = g^m * r^n mod n²
Decrypt(c): m = L(c^λ mod n²) * μ mod n

Homomorphic property:
Enc(m₁) * Enc(m₂) mod n² = Enc(m₁ + m₂)
```

**Performance**: Very slow (1000x+ slower than normal encryption).

---

## Security Best Practices

### Key Management

1. **Never hardcode keys** in source code
2. **Use key derivation**: Derive keys from master secret
3. **Rotate keys**: Change periodically
4. **Separate keys**: Different keys for different purposes
5. **Use HSMs**: Hardware Security Modules for critical keys

### Common Pitfalls

#### Timing Attacks

**Problem**: Execution time reveals information.

```rust
// VULNERABLE (timing leak)
fn verify_mac_bad(mac1: &[u8], mac2: &[u8]) -> bool {
    if mac1.len() != mac2.len() {
        return false;
    }
    for i in 0..mac1.len() {
        if mac1[i] != mac2[i] {
            return false; // Early return leaks position of mismatch
        }
    }
    true
}

// SECURE (constant time)
fn verify_mac_good(mac1: &[u8], mac2: &[u8]) -> bool {
    if mac1.len() != mac2.len() {
        return false;
    }
    let mut diff = 0u8;
    for i in 0..mac1.len() {
        diff |= mac1[i] ^ mac2[i]; // Always check all bytes
    }
    diff == 0
}
```

#### Nonce Reuse

**ChaCha20/AES-GCM**: NEVER reuse (key, nonce) pair!

**Attack**: XOR two ciphertexts with same nonce → reveals plaintext XOR.

```
C₁ = P₁ ⊕ Keystream(key, nonce)
C₂ = P₂ ⊕ Keystream(key, nonce)
C₁ ⊕ C₂ = P₁ ⊕ P₂  (keystream cancels out!)
```

**Solution**: Use counter-based nonces or random with large nonce space (96+ bits).

#### Weak RNG

**NEVER** use `rand()` for cryptographic keys!

**Use**:
- `/dev/urandom` (Linux)
- `CryptGenRandom` (Windows)
- Language crypto libraries (`crypto/rand` in Go, `OsRng` in Rust)

---

## Performance Comparison

| Algorithm | Key Size | Speed (MB/s) | Security (bits) |
|-----------|----------|--------------|-----------------|
| AES-128   | 128      | 3000+        | 128             |
| ChaCha20  | 256      | 2000+        | 256             |
| RSA-2048  | 2048     | 0.5 (enc)    | 112             |
| ECDH P-256| 256      | 50           | 128             |
| SHA-256   | -        | 450          | 128             |
| Argon2    | -        | 0.01         | -               |

**Hardware acceleration** (AES-NI, SHA extensions) can 10x these speeds.

---

## Conclusion

**Mental Model for Cryptography**:

1. **Symmetric = Fast**: Use for bulk data (AES-GCM)
2. **Asymmetric = Slow**: Use for key exchange and signatures (ECDH, ECDSA)
3. **Hash = One-Way**: Use for integrity and password storage (SHA-256, Argon2)
4. **Hybrid Systems**: Combine all three (like TLS)

**Deliberate Practice Path**:

1. **Implement basics**: Write your own AES, SHA-256 (don't use in production!)
2. **Study attacks**: Learn why ECB fails, timing attacks, padding oracles
3. **Analyze protocols**: Trace TLS handshake, Signal protocol
4. **Side channels**: Study timing, power analysis, fault attacks
5. **Modern primitives**: zk-SNARKs, post-quantum crypto (lattices)

**Critical Principle**: **Never roll your own crypto in production.** Use audited libraries (libsodium, OpenSSL, ring.rs). But understanding internals makes you a better systems programmer.

This foundation gives you the depth to understand any cryptographic system you encounter. The mathematics is elegant, the engineering is subtle, and the security implications are profound. Master these concepts, and you'll think differently about every system you build.

# Cryptographic Attack Vectors: Deep Analysis & Mitigation

**Comprehensive Guide to Real-World Cryptographic Attacks**

---

## Table of Contents
1. [Attack Classification Framework](#attack-classification-framework)
2. [Implementation Attacks](#implementation-attacks)
3. [Protocol-Level Attacks](#protocol-level-attacks)
4. [Mathematical Attacks](#mathematical-attacks)
5. [Side-Channel Attacks](#side-channel-attacks)
6. [Social Engineering & Key Management](#social-engineering--key-management)
7. [Real-World Attack Case Studies](#real-world-attack-case-studies)

---

## Attack Classification Framework

**Attack Categories by Adversary Capability:**

```
┌─────────────────────────────────────────────────────┐
│  Passive Attacks (Eavesdropping)                    │
│  • Ciphertext-only attack                           │
│  • Traffic analysis                                 │
└─────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────┐
│  Active Attacks (Manipulation)                      │
│  • Known-plaintext attack                           │
│  • Chosen-plaintext attack                          │
│  • Chosen-ciphertext attack                         │
│  • Man-in-the-middle                                │
└─────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────┐
│  Implementation Attacks (System Weaknesses)         │
│  • Side-channel attacks                             │
│  • Fault injection                                  │
│  • Poor randomness                                  │
└─────────────────────────────────────────────────────┘
```

**Threat Model Terminology:**

- **Adversary**: Entity attempting to break security
- **Attack Surface**: All points where adversary can interact
- **Attack Vector**: Specific method used to exploit vulnerability
- **Exploit**: Concrete implementation of attack
- **Mitigation**: Defense mechanism against attack

---

## Implementation Attacks

### 1. Timing Attacks

**Concept**: Measure execution time to extract secret information.

**Attack Scenario - Password Comparison:**

```rust
// VULNERABLE: Early-exit comparison
fn verify_password_vulnerable(stored: &[u8], input: &[u8]) -> bool {
    if stored.len() != input.len() {
        return false;
    }
    
    for i in 0..stored.len() {
        if stored[i] != input[i] {
            return false; // ← VULNERABILITY: Early return
        }
    }
    true
}

// Attack simulation
use std::time::Instant;

fn timing_attack_demo() {
    let correct_password = b"SecretPass123";
    let mut guess = vec![0u8; correct_password.len()];
    
    // Attack: For each position, try all bytes and measure time
    for pos in 0..correct_password.len() {
        let mut best_byte = 0u8;
        let mut max_time = std::time::Duration::ZERO;
        
        for byte in 0..=255u8 {
            guess[pos] = byte;
            
            // Measure multiple times and average
            let mut total_time = std::time::Duration::ZERO;
            for _ in 0..1000 {
                let start = Instant::now();
                verify_password_vulnerable(correct_password, &guess);
                total_time += start.elapsed();
            }
            
            // Longer time means more bytes matched before early return
            if total_time > max_time {
                max_time = total_time;
                best_byte = byte;
            }
        }
        
        guess[pos] = best_byte;
        println!("Position {}: found byte {:?}", pos, best_byte as char);
    }
    
    println!("Recovered password: {:?}", String::from_utf8_lossy(&guess));
}
```

**Why This Works:**

```
Attempt: "A???????" → Fails at position 0 → Fast return
Attempt: "S???????" → Fails at position 1 → Slightly slower
Attempt: "Se?????" → Fails at position 2 → Even slower
...
```

Each correct byte adds ~1 comparison operation to execution time.

**Attack Complexity**: O(n × 256) where n = password length (instead of O(256^n) for brute force)

**Mitigation - Constant-Time Comparison:**

```rust
// SECURE: Constant-time comparison
fn verify_password_secure(stored: &[u8], input: &[u8]) -> bool {
    // Length check is unavoidable timing leak, but acceptable
    if stored.len() != input.len() {
        return false;
    }
    
    let mut diff: u8 = 0;
    
    // Always check ALL bytes, never exit early
    for i in 0..stored.len() {
        diff |= stored[i] ^ input[i];
    }
    
    // Constant-time check if diff == 0
    diff == 0
}

// Even better: Use constant-time library
use subtle::ConstantTimeEq;

fn verify_password_best(stored: &[u8], input: &[u8]) -> bool {
    stored.ct_eq(input).into()
}
```

**Additional Mitigation:**
- Add random delay (makes timing measurements noisy)
- Rate limiting (prevents high-volume timing measurements)
- Use cryptographic comparison functions from trusted libraries

**Real-World Example:** 
In 2013, researchers recovered RSA private keys from OpenSSL by measuring cache timing during signature operations.

---

### 2. Cache Timing Attacks

**Concept**: Exploit CPU cache behavior to leak secrets.

**Background - How CPU Caches Work:**

```
CPU wants data → Check L1 cache (1-3 cycles)
                 ↓ miss
                 Check L2 cache (10-20 cycles)
                 ↓ miss
                 Check L3 cache (40-75 cycles)
                 ↓ miss
                 Fetch from RAM (200+ cycles)
```

**Attack Scenario - AES S-box Attack:**

AES uses lookup tables (S-boxes). Memory access patterns reveal which S-box entries were accessed.

```c
// VULNERABLE: Table-based AES implementation
static const uint8_t sbox[256] = { /* ... */ };

uint8_t aes_sub_byte_vulnerable(uint8_t input) {
    return sbox[input]; // ← Memory access reveals 'input'
}

// Attack: Flush cache, trigger encryption, measure which cache lines loaded
void cache_timing_attack() {
    // 1. Flush S-box from cache
    for (int i = 0; i < 256; i++) {
        clflush(&sbox[i]); // x86 cache line flush instruction
    }
    
    // 2. Victim performs encryption (accesses sbox[key_byte])
    // (This would be done by triggering victim process)
    
    // 3. Measure access times to determine which entries were cached
    uint64_t access_times[256];
    for (int i = 0; i < 256; i++) {
        uint64_t start = rdtsc(); // Read CPU timestamp counter
        volatile uint8_t dummy = sbox[i];
        uint64_t end = rdtsc();
        access_times[i] = end - start;
    }
    
    // Entries accessed by victim will be in cache (fast access)
    for (int i = 0; i < 256; i++) {
        if (access_times[i] < 100) { // Fast = was in cache
            printf("S-box[%d] was accessed (possible key byte)\n", i);
        }
    }
}
```

**Why This Works:**

```
Before encryption:  All S-box entries in slow memory
During encryption:  sbox[key ⊕ plaintext] loaded into cache
After encryption:   Fast access reveals which entry was used
                    → Since plaintext is known → reveals key
```

**Famous Attack: FLUSH+RELOAD (2014)**

Used to extract AES keys from OpenSSL by monitoring cache access patterns across processes.

**Mitigation Strategies:**

```rust
// 1. Bitsliced Implementation (No table lookups)
// Implements AES using only bitwise operations
fn aes_sub_byte_secure(input: u8) -> u8 {
    // Compute S-box using Boolean formulas instead of lookup
    // More complex but constant-time and cache-safe
    
    // Inverse in GF(2^8)
    let inv = gf256_inverse_bitsliced(input);
    
    // Affine transformation
    let mut output = inv;
    for _ in 0..4 {
        output ^= (output << 1) | (output >> 7);
    }
    output ^= 0x63;
    
    output
}

fn gf256_inverse_bitsliced(x: u8) -> u8 {
    // Complex bitwise operations that don't use memory lookups
    // Implementation uses Galois field arithmetic in binary representation
    // Each operation takes same time regardless of input
    // (Full implementation omitted for brevity - involves ~100 bitwise ops)
    x // Placeholder
}

// 2. Use hardware AES instructions (AES-NI on x86)
#[cfg(target_feature = "aes")]
fn aes_encrypt_hardware(block: &mut [u8; 16], key: &[u8; 16]) {
    use core::arch::x86_64::*;
    unsafe {
        let mut state = _mm_loadu_si128(block.as_ptr() as *const __m128i);
        let round_key = _mm_loadu_si128(key.as_ptr() as *const __m128i);
        
        // Hardware AES round (constant-time, no cache access)
        state = _mm_aesenc_si128(state, round_key);
        
        _mm_storeu_si128(block.as_mut_ptr() as *mut __m128i, state);
    }
}
```

**3. Cache Partitioning (OS-level)**

```bash
# Intel CAT (Cache Allocation Technology)
# Partition L3 cache to isolate security-critical processes
intel-cmt-cat -e "llc:1=0x0f;llc:2=0xf0"
# Process 1 gets cache ways 0-3, Process 2 gets ways 4-7
```

**4. Disable Shared Caches**

On some CPUs, disable hyperthreading to prevent cross-thread cache attacks:
```bash
echo off > /sys/devices/system/cpu/smt/control
```

---

### 3. Power Analysis Attacks

**Concept**: Measure power consumption during cryptographic operations to extract keys.

**Simple Power Analysis (SPA):**

Observe power traces directly to identify operations.

```
Power Trace Visualization:
     
  ^
P |     ╱╲        ╱╲
o |    ╱  ╲      ╱  ╲     ← Multiply operation (high power)
w |___╱____╲____╱____╲___
e |                       ← Square operation (low power)
r |
  +────────────────────────→ Time

This reveals exponent bits in RSA: 1 = square-and-multiply, 0 = square-only
```

**Attack on RSA Modular Exponentiation:**

```c
// VULNERABLE: Square-and-multiply algorithm
uint64_t modular_exp_vulnerable(uint64_t base, uint64_t exp, uint64_t mod) {
    uint64_t result = 1;
    base = base % mod;
    
    while (exp > 0) {
        if (exp % 2 == 1) {  // ← Power spike when bit = 1
            result = (result * base) % mod;
        }
        exp = exp >> 1;
        base = (base * base) % mod;
    }
    return result;
}

/*
Power trace reveals:
High-Low-High-High-Low = Binary exponent: 11011
*/
```

**Differential Power Analysis (DPA):**

Statistical analysis of many power traces to extract key bits.

```
Attack Process:
1. Collect power traces for many encryptions
2. For each key bit hypothesis (0 or 1):
   - Partition traces into two groups
   - Compute average power for each group
3. Correct hypothesis shows statistical difference
```

**Mitigation - Constant-Power Operations:**

```rust
// 1. Always perform same operations (no branching on secrets)
fn modular_exp_secure(base: u64, exp: u64, modulus: u64) -> u64 {
    let mut result = 1u64;
    let mut base_pow = base % modulus;
    
    // Process all bits, even if exp bit is 0
    for i in 0..64 {
        let bit = (exp >> i) & 1;
        
        // Constant-time conditional: compute both, select one
        let mult_result = (result.wrapping_mul(base_pow)) % modulus;
        
        // Branchless selection (same operations regardless of bit)
        result = constant_time_select(bit, mult_result, result);
        
        base_pow = (base_pow.wrapping_mul(base_pow)) % modulus;
    }
    
    result
}

// Constant-time selection without branching
fn constant_time_select(condition: u64, true_val: u64, false_val: u64) -> u64 {
    let mask = condition.wrapping_neg(); // 0 → 0x0000, 1 → 0xFFFF
    (true_val & mask) | (false_val & !mask)
}

// 2. Use blinding for RSA
fn rsa_decrypt_with_blinding(
    ciphertext: &BigUint,
    d: &BigUint,
    n: &BigUint
) -> BigUint {
    use rand::Rng;
    let mut rng = rand::thread_rng();
    
    // Generate random blinding factor
    let r: BigUint = rng.gen_biguint(256);
    let r_inv = r.modinv(n).unwrap();
    
    // Blind ciphertext: C' = C * r^e mod n
    let e = BigUint::from(65537u32);
    let blinded_c = (ciphertext * r.modpow(&e, n)) % n;
    
    // Decrypt blinded: M' = (C')^d mod n
    let blinded_m = blinded_c.modpow(d, n);
    
    // Unblind: M = M' * r^(-1) mod n
    (blinded_m * r_inv) % n
    // Power traces now depend on random r, not the key!
}
```

**3. Hardware Countermeasures:**

- **Noise generators**: Add random power fluctuations
- **Dual-rail logic**: Every computation performs complementary operation
- **Randomized clock**: Vary clock frequency during crypto operations

---

### 4. Fault Injection Attacks

**Concept**: Introduce hardware faults (voltage glitches, electromagnetic pulses) to cause computational errors that leak secrets.

**Attack Scenario - Bellcore Attack on RSA-CRT:**

RSA uses **Chinese Remainder Theorem (CRT)** for faster decryption:

```
Instead of: M = C^d mod n
Compute:    M_p = C^d_p mod p
            M_q = C^d_q mod q
            M = CRT(M_p, M_q)  ← 4x faster!
```

**Attack Process:**

```c
// Normal RSA-CRT decryption
BigInt rsa_crt_decrypt_vulnerable(BigInt C, BigInt d_p, BigInt d_q, 
                                   BigInt p, BigInt q) {
    // 1. Compute M_p = C^d_p mod p
    BigInt M_p = mod_exp(C, d_p, p);  // ← Inject fault here!
    
    // 2. Compute M_q = C^d_q mod q (correct)
    BigInt M_q = mod_exp(C, d_q, q);
    
    // 3. Combine using CRT
    BigInt M = chinese_remainder_theorem(M_p, M_q, p, q);
    return M;
}

/*
Fault Attack:
1. Attacker causes glitch during M_p computation → M_p' (incorrect)
2. M_q remains correct
3. Output: M' = CRT(M_p', M_q) is incorrect
4. Compute: GCD(M' - M, n) = GCD(M' - M, p*q) = q
5. Factor n: p = n / q
6. Private key recovered!
*/
```

**Attack Implementation:**

```rust
use num_bigint::BigUint;
use num_traits::One;

fn bellcore_attack_demo() {
    // Setup (attacker knows these)
    let n = BigUint::parse_bytes(b"123456789...", 10).unwrap(); // Public modulus
    let e = BigUint::from(65537u32); // Public exponent
    
    // Attacker encrypts known message
    let plaintext = BigUint::from(42u32);
    let ciphertext = plaintext.modpow(&e, &n);
    
    // Victim decrypts normally
    let correct_decryption = plaintext.clone(); // Simulate correct decryption
    
    // Attacker induces fault, gets faulty decryption
    let faulty_decryption = simulate_faulty_decryption(); // Different value
    
    // Attack: Compute GCD
    let diff = if faulty_decryption > correct_decryption {
        &faulty_decryption - &correct_decryption
    } else {
        &correct_decryption - &faulty_decryption
    };
    
    let factor = diff.gcd(&n);
    
    if factor != One::one() && &factor != &n {
        println!("FACTOR FOUND: {}", factor);
        let other_factor = &n / &factor;
        println!("n factored as: {} * {}", factor, other_factor);
        // Private key can now be computed!
    }
}

fn simulate_faulty_decryption() -> BigUint {
    // In real attack, this is caused by hardware fault
    BigUint::from(1337u32) // Random incorrect value
}
```

**Mitigation Strategies:**

```rust
// 1. Verify decryption result
fn rsa_crt_decrypt_secure(
    ciphertext: &BigUint,
    d_p: &BigUint,
    d_q: &BigUint,
    p: &BigUint,
    q: &BigUint,
    n: &BigUint,
    e: &BigUint
) -> Result<BigUint, &'static str> {
    // Perform CRT decryption
    let m_p = ciphertext.modpow(d_p, p);
    let m_q = ciphertext.modpow(d_q, q);
    
    // CRT combination
    let h = (((&m_q - &m_p) * p.modinv(q).unwrap()) % q);
    let plaintext = &m_p + &h * p;
    
    // VERIFICATION: Re-encrypt and check
    let verification = plaintext.modpow(e, n);
    if &verification != ciphertext {
        return Err("Decryption verification failed - possible fault attack");
    }
    
    Ok(plaintext)
}

// 2. Compute twice and compare
fn rsa_crt_decrypt_redundant(/* ... */) -> Result<BigUint, &'static str> {
    let result1 = rsa_crt_decrypt_once(/* ... */);
    let result2 = rsa_crt_decrypt_once(/* ... */);
    
    if result1 != result2 {
        return Err("Results don't match - possible fault attack");
    }
    
    Ok(result1)
}

// 3. Use infective computation
fn rsa_crt_decrypt_infective(/* ... */) -> BigUint {
    // If fault detected, randomize output instead of returning faulty value
    let m_p = ciphertext.modpow(d_p, p);
    let m_q = ciphertext.modpow(d_q, q);
    
    // Check for faults by verifying intermediate properties
    if !verify_crt_consistency(&m_p, &m_q, /* ... */) {
        // Return random garbage instead of exploitable faulty output
        return random_bigint();
    }
    
    chinese_remainder_theorem(m_p, m_q, p, q)
}
```

**Hardware Countermeasures:**

- **Voltage sensors**: Detect and reject operations under abnormal voltage
- **Frequency sensors**: Detect clock glitching
- **Light sensors**: Detect laser fault injection
- **Mesh shields**: Detect physical tampering

---

### 5. Random Number Generator Attacks

**Concept**: Weak randomness makes cryptographic keys predictable.

**Attack Scenario - Predictable PRNG:**

```c
// VULNERABLE: Using standard library rand()
#include <stdlib.h>
#include <time.h>

void generate_aes_key_vulnerable(uint8_t key[16]) {
    srand(time(NULL)); // ← VULNERABILITY: Predictable seed!
    
    for (int i = 0; i < 16; i++) {
        key[i] = rand() % 256;
    }
}

/*
Attack:
1. Attacker knows approximate time key was generated (e.g., ±1 hour)
2. Try all possible time(NULL) values in that range
3. For each seed, generate key and test if it decrypts data
4. Keyspace: ~3600 seconds instead of 2^128 keys
*/
```

**Real-World Attack - Debian OpenSSL (2008):**

Bug caused OpenSSL to use only process ID as entropy source:
```c
// Debian's broken code (simplified)
int pid = getpid(); // Only ~32000 possible values
RAND_seed(&pid, sizeof(pid));
// Generated keys had only ~15 bits of entropy!
```

**Attack Implementation:**

```rust
use aes::Aes128;
use aes::cipher::{BlockEncrypt, KeyInit};
use aes::cipher::generic_array::GenericArray;

fn weak_rng_attack() {
    // Victim generates key with weak RNG (using timestamp)
    let victim_timestamp = 1234567890u64; // Example: known approximate time
    let victim_key = generate_key_from_timestamp(victim_timestamp);
    
    // Victim encrypts data
    let plaintext = b"Secret data here";
    let ciphertext = encrypt_with_key(&victim_key, plaintext);
    
    // Attacker tries all timestamps in ±1 hour range
    let search_range = 3600; // 1 hour = 3600 seconds
    
    for timestamp_guess in (victim_timestamp - search_range)..=(victim_timestamp + search_range) {
        let guessed_key = generate_key_from_timestamp(timestamp_guess);
        let decrypted = decrypt_with_key(&guessed_key, &ciphertext);
        
        // Check if decryption looks valid (e.g., valid UTF-8)
        if is_likely_plaintext(&decrypted) {
            println!("KEY FOUND! Timestamp: {}", timestamp_guess);
            println!("Key: {:02x?}", guessed_key);
            println!("Decrypted: {}", String::from_utf8_lossy(&decrypted));
            break;
        }
    }
}

fn generate_key_from_timestamp(timestamp: u64) -> [u8; 16] {
    // Simulates weak RNG using timestamp as seed
    let mut key = [0u8; 16];
    let mut state = timestamp;
    for i in 0..16 {
        // Simple LCG (Linear Congruential Generator)
        state = state.wrapping_mul(1103515245).wrapping_add(12345);
        key[i] = (state >> 16) as u8;
    }
    key
}

fn is_likely_plaintext(data: &[u8]) -> bool {
    // Heuristic: Check if looks like English text
    data.iter().all(|&b| b.is_ascii_graphic() || b.is_ascii_whitespace())
}
```

**Mitigation - Cryptographically Secure RNG:**

```rust
// SECURE: Use OS-provided CSPRNG
use rand::RngCore;
use rand::rngs::OsRng;

fn generate_aes_key_secure() -> [u8; 16] {
    let mut key = [0u8; 16];
    OsRng.fill_bytes(&mut key); // Uses /dev/urandom on Linux
    key
}

// Alternative: Use hardware RNG
#[cfg(target_arch = "x86_64")]
fn generate_key_hardware() -> Option<[u8; 16]> {
    use core::arch::x86_64::*;
    let mut key = [0u8; 16];
    
    unsafe {
        for i in (0..16).step_by(8) {
            let mut random_u64: u64 = 0;
            // RDRAND instruction (Intel/AMD hardware RNG)
            if _rdrand64_step(&mut random_u64) == 0 {
                return None; // Hardware RNG failed
            }
            key[i..i+8].copy_from_slice(&random_u64.to_le_bytes());
        }
    }
    
    Some(key)
}
```

**RNG Testing:**

```rust
use std::collections::HashMap;

fn test_rng_quality(rng_func: fn() -> u8, sample_size: usize) {
    let mut counts = HashMap::new();
    
    // Collect samples
    for _ in 0..sample_size {
        let value = rng_func();
        *counts.entry(value).or_insert(0) += 1;
    }
    
    // Chi-square test for uniformity
    let expected = sample_size as f64 / 256.0;
    let mut chi_square = 0.0;
    
    for i in 0u8..=255 {
        let observed = *counts.get(&i).unwrap_or(&0) as f64;
        chi_square += (observed - expected).powi(2) / expected;
    }
    
    println!("Chi-square statistic: {:.2}", chi_square);
    println!("Expected for good RNG: ~255 (256 degrees of freedom)");
    
    if chi_square < 200.0 || chi_square > 310.0 {
        println!("WARNING: RNG may not be uniformly distributed!");
    }
}
```

**Additional Mitigations:**

1. **Entropy pooling**: Combine multiple sources
   ```rust
   fn combine_entropy_sources() -> [u8; 32] {
       let mut entropy = [0u8; 32];
       
       // Source 1: OS RNG
       OsRng.fill_bytes(&mut entropy[0..16]);
       
       // Source 2: Hardware RNG (if available)
       if let Some(hw_rand) = generate_key_hardware() {
           for i in 0..16 {
               entropy[i + 16] = hw_rand[i];
           }
       }
       
       // Source 3: System entropy (timing, etc.)
       // Mix all sources with hash
       use sha2::{Sha256, Digest};
       let final_entropy = Sha256::digest(&entropy);
       final_entropy.into()
   }
   ```

2. **Continuous testing**: Monitor RNG health
   ```rust
   fn continuous_rng_test(rng: &mut impl RngCore) -> bool {
       // FIPS 140-2 continuous test
       let mut prev = [0u8; 16];
       rng.fill_bytes(&mut prev);
       
       for _ in 0..1000 {
           let mut curr = [0u8; 16];
           rng.fill_bytes(&mut curr);
           
           if curr == prev {
               return false; // RNG stuck - FAILURE
           }
           prev = curr;
       }
       true
   }
   ```

---

## Protocol-Level Attacks

### 6. Padding Oracle Attack

**Concept**: Exploit error messages to decrypt ciphertext without knowing the key.

**Background - PKCS#7 Padding:**

When encrypting with block ciphers (like AES-CBC), plaintext must be multiple of block size (16 bytes).

```
Message: "HELLO" (5 bytes)
Padded:  "HELLO\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b\x0b" (16 bytes)
         ^^^^^^ message  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ padding

Padding rules:
- If need N bytes of padding, add N bytes each with value N
- Always add padding (even if message is already multiple of block size)
```

**The Oracle:**

A server that returns different errors for invalid padding vs. invalid MAC:

```go
// VULNERABLE: Padding oracle
func decryptAndVerify(ciphertext []byte, key []byte) ([]byte, error) {
    // Decrypt
    plaintext, err := decryptCBC(ciphertext, key)
    if err != nil {
        return nil, err
    }
    
    // Remove padding
    paddingLen := int(plaintext[len(plaintext)-1])
    
    // Check padding validity
    for i := 0; i < paddingLen; i++ {
        if plaintext[len(plaintext)-1-i] != byte(paddingLen) {
            return nil, errors.New("Invalid padding") // ← LEAKS INFO!
        }
    }
    
    plaintext = plaintext[:len(plaintext)-paddingLen]
    
    // Verify MAC
    if !verifyMAC(plaintext) {
        return nil, errors.New("Invalid MAC") // ← Different error
    }
    
    return plaintext, nil
}
```

**Attack Process:**

```
Goal: Decrypt ciphertext block C₂ (which decrypts to P₂)

CBC Decryption: P₂ = D(C₂) ⊕ C₁
               Intermediate = D(C₂)
               P₂ = Intermediate ⊕ C₁

Attack:
1. Create modified C₁' = C₁ ⊕ guess ⊕ 0x01
2. Send (C₁', C₂) to oracle
3. If oracle says "valid padding":
   - Last byte of P₂' = 0x01
   - Intermediate_last = C₁'_last ⊕ 0x01
   - P₂_last = Intermediate_last ⊕ C₁_last
4. Repeat for all bytes
```

**Attack Implementation:**

```rust
use aes::Aes128;
use aes::cipher::{BlockDecrypt, KeyInit};
use aes::cipher::generic_array::GenericArray;

// Simulated padding oracle (returns true if padding valid)
fn padding_oracle(ciphertext: &[u8], key: &[u8; 16]) -> bool {
    let cipher = Aes128::new(GenericArray::from_slice(key));
    
    if ciphertext.len() != 32 { // Two blocks
        return false;
    }
    
    let iv = &ciphertext[0..16];
    let ct_block = &ciphertext[16..32];
    
    // Decrypt block
    let mut decrypted = GenericArray::clone_from_slice(ct_block);
    cipher.decrypt_block(&mut decrypted);
    
    // XOR with IV to get plaintext
    let mut plaintext = [0u8; 16];
    for i in 0..16 {
        plaintext[i] = decrypted[i] ^ iv[i];
    }
    
    // Check padding validity
    let padding_len = plaintext[15] as usize;
    if padding_len == 0 || padding_len > 16 {
        return false;
    }
    
    for i in 0..padding_len {
        if plaintext[15 - i] != padding_len as u8 {
            return false; // Invalid padding
        }
    }
    
    true // Valid padding
}

// Padding oracle attack
fn padding_oracle_attack(ciphertext: &[u8], key: &[u8; 16]) -> Vec<u8> {
    assert_eq!(ciphertext.len(), 32); // Two blocks for simplicity
    
    let iv = &ciphertext[0..16];
    let ct_block = &ciphertext[16..32];
    
    let mut plaintext = vec![0u8; 16];
    
    // Attack each byte from right to left
    for byte_pos in (0..16).rev() {
        let padding_value = (16 - byte_pos) as u8;
        
        println!("Attacking byte position {}...", byte_pos);
        
        // Try all possible byte values
        for guess in 0u8..=255 {
            // Create modified IV
            let mut modified_iv = [0u8; 16];
            modified_iv.copy_from_slice(iv);
            
            // Set known bytes to produce correct padding
            for known_pos in (byte_pos + 1)..16 {
                modified_iv[known_pos] = iv[known_pos] 
                    ^ plaintext[known_pos] 
                    ^ padding_value;
            }
            
            // Set current byte to guess
            modified_iv[byte_pos] = iv[byte_pos] ^ guess ^ padding_value;
            
            // Create attack ciphertext
            let mut attack_ct = vec![];
            attack_ct.extend_from_slice(&modified_iv);
            attack_ct.extend_from_slice(ct_block);
            
            // Query oracle
            if padding_oracle(&attack_ct, key) {
                plaintext[byte_pos] = guess;
                println!("  Found byte: 0x{:02x} ('{}')", 
                         guess, 
                         if guess.is_ascii_graphic() { guess as char } else { '.' });
                break;
            }
        }
    }
    
    // Remove padding
    let padding_len = plaintext[15] as usize;
    plaintext.truncate(16 - padding_len);
    
    plaintext
}

fn main() {
    let key = b"YELLOW SUBMARINE";
    
    // Encrypt a message
    let plaintext = b"Secret message!!";
    let ciphertext = encrypt_cbc_manual(plaintext, key);
    
    println!("Original: {}", String::from_utf8_lossy(plaintext));
    println!("Ciphertext: {:02x?}\n", ciphertext);
    
    // Perform padding oracle attack
    let recovered = padding_oracle_attack(&ciphertext, key);
    println!("\nRecovered: {}", String::from_utf8_lossy(&recovered));
}
```

**Attack Complexity**: O(n × 256) where n = ciphertext length (very fast!)

**Real-World Examples:**
- **ASP.NET** (2010): Padding oracle in web crypto
- **TLS** (2002-2013): Multiple variants (BEAST, Lucky13)
- **XML Encryption** (2011): SOAP message decryption

**Mitigation Strategies:**

```rust
// 1. Use Encrypt-then-MAC (not MAC-then-Encrypt)
fn encrypt_then_mac_secure(plaintext: &[u8], enc_key: &[u8], mac_key: &[u8]) -> Vec<u8> {
    // Encrypt first
    let ciphertext = encrypt_aes_cbc(plaintext, enc_key);
    
    // MAC the ciphertext
    let mac = hmac_sha256(mac_key, &ciphertext);
    
    // Return ciphertext || MAC
    let mut result = ciphertext;
    result.extend_from_slice(&mac);
    result
}

fn decrypt_then_verify_secure(data: &[u8], enc_key: &[u8], mac_key: &[u8]) 
    -> Result<Vec<u8>, &'static str> {
    
    if data.len() < 32 {
        return Err("Data too short");
    }
    
    let ciphertext = &data[..data.len() - 32];
    let received_mac = &data[data.len() - 32..];
    
    // VERIFY MAC FIRST (before any decryption)
    let computed_mac = hmac_sha256(mac_key, ciphertext);
    
    if !constant_time_compare(received_mac, &computed_mac) {
        return Err("Authentication failed"); // Same error for all failures!
    }
    
    // Only decrypt if MAC valid
    let plaintext = decrypt_aes_cbc(ciphertext, enc_key)?;
    
    Ok(plaintext)
}

// 2. Use AEAD (Authenticated Encryption with Associated Data)
use aes_gcm::{Aes256Gcm, Key, Nonce};
use aes_gcm::aead::{Aead, KeyInit};

fn aead_encrypt_secure(plaintext: &[u8], key: &[u8; 32], nonce: &[u8; 12]) 
    -> Result<Vec<u8>, &'static str> {
    
    let cipher = Aes256Gcm::new(Key::<Aes256Gcm>::from_slice(key));
    let nonce = Nonce::from_slice(nonce);
    
    cipher.encrypt(nonce, plaintext)
          .map_err(|_| "Encryption failed")
}

fn aead_decrypt_secure(ciphertext: &[u8], key: &[u8; 32], nonce: &[u8; 12]) 
    -> Result<Vec<u8>, &'static str> {
    
    let cipher = Aes256Gcm::new(Key::<Aes256Gcm>::from_slice(key));
    let nonce = Nonce::from_slice(nonce);
    
    // GCM automatically verifies authentication tag
    // Returns error if tampered - NO PADDING ORACLE!
    cipher.decrypt(nonce, ciphertext)
          .map_err(|_| "Decryption or authentication failed") // Single error
}

// 3. Return same error for ALL decryption failures
fn decrypt_no_oracle(data: &[u8], key: &[u8]) -> Result<Vec<u8>, &'static str> {
    // All error paths return same message
    const ERROR: &str = "Decryption failed";
    
    let plaintext = decrypt_internal(data, key).map_err(|_| ERROR)?;
    verify_padding(&plaintext).map_err(|_| ERROR)?;
    verify_mac(&plaintext).map_err(|_| ERROR)?;
    
    Ok(remove_padding(plaintext))
}
```

---

### 7. Replay Attacks

**Concept**: Capture and retransmit valid messages to repeat actions.

**Attack Scenario - Bank Transfer:**

```
Alice → Bank: "Transfer $1000 to Bob" [Signed with Alice's key]
Attacker captures message
Attacker → Bank: [Replays exact same message]
Bank transfers another $1000 to Bob!
```

**Implementation:**

```go
// VULNERABLE: No replay protection
type Transaction struct {
    From      string
    To        string
    Amount    int
    Signature []byte
}

func (bank *Bank) ProcessTransactionVulnerable(tx Transaction) error {
    // Verify signature (correct!)
    if !VerifySignature(tx.From, tx.Signature, tx.Data()) {
        return errors.New("Invalid signature")
    }
    
    // Process transaction
    return bank.Transfer(tx.From, tx.To, tx.Amount)
    // ← VULNERABILITY: No check if transaction already processed
}

// Attack demonstration
func replayAttack() {
    // 1. Legitimate transaction
    tx := Transaction{
        From: "Alice",
        To: "Bob",
        Amount: 1000,
    }
    tx.Signature = Sign(alicePrivateKey, tx.Data())
    
    bank.ProcessTransactionVulnerable(tx) // $1000 transferred
    
    // 2. Attacker captures and replays
    time.Sleep(1 * time.Hour)
    bank.ProcessTransactionVulnerable(tx) // Another $1000 transferred!
}
```

**Mitigation Strategies:**

```rust
use std::collections::HashSet;
use std::time::{SystemTime, UNIX_EPOCH};

// 1. Sequence numbers
struct TransactionV1 {
    from: String,
    to: String,
    amount: u64,
    sequence_number: u64, // ← Incrementing counter
    signature: Vec<u8>,
}

struct BankV1 {
    last_sequence: HashMap<String, u64>,
}

impl BankV1 {
    fn process_transaction(&mut self, tx: &TransactionV1) -> Result<(), String> {
        // Verify signature
        if !verify_signature(&tx.from, &tx.signature, &tx.data()) {
            return Err("Invalid signature".to_string());
        }
        
        // Check sequence number
        let last_seq = self.last_sequence.get(&tx.from).unwrap_or(&0);
        if tx.sequence_number <= *last_seq {
            return Err("Replay attack detected: old sequence number".to_string());
        }
        
        // Update sequence number
        self.last_sequence.insert(tx.from.clone(), tx.sequence_number);
        
        // Process transaction
        self.transfer(&tx.from, &tx.to, tx.amount)
    }
}

// 2. Timestamps with window
struct TransactionV2 {
    from: String,
    to: String,
    amount: u64,
    timestamp: u64, // Unix timestamp
    signature: Vec<u8>,
}

impl BankV2 {
    fn process_transaction(&mut self, tx: &TransactionV2) -> Result<(), String> {
        // Verify signature
        if !verify_signature(&tx.from, &tx.signature, &tx.data()) {
            return Err("Invalid signature".to_string());
        }
        
        // Check timestamp freshness (5-minute window)
        let now = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_secs();
        
        const WINDOW: u64 = 300; // 5 minutes
        if tx.timestamp < now.saturating_sub(WINDOW) || tx.timestamp > now + WINDOW {
            return Err("Timestamp out of acceptable range".to_string());
        }
        
        // Process transaction
        self.transfer(&tx.from, &tx.to, tx.amount)
    }
}

// 3. Nonces (number used once) with cache
use std::sync::Mutex;
use lru::LruCache;

struct TransactionV3 {
    from: String,
    to: String,
    amount: u64,
    nonce: [u8; 16], // Random value
    signature: Vec<u8>,
}

struct BankV3 {
    seen_nonces: Mutex<LruCache<[u8; 16], ()>>,
}

impl BankV3 {
    fn new() -> Self {
        BankV3 {
            seen_nonces: Mutex::new(LruCache::new(10000)), // Keep last 10k nonces
        }
    }
    
    fn process_transaction(&mut self, tx: &TransactionV3) -> Result<(), String> {
        // Verify signature
        if !verify_signature(&tx.from, &tx.signature, &tx.data()) {
            return Err("Invalid signature".to_string());
        }
        
        // Check nonce hasn't been seen
        let mut cache = self.seen_nonces.lock().unwrap();
        if cache.contains(&tx.nonce) {
            return Err("Replay attack detected: nonce reused".to_string());
        }
        
        // Store nonce
        cache.put(tx.nonce, ());
        
        // Process transaction
        self.transfer(&tx.from, &tx.to, tx.amount)
    }
}

// 4. Challenge-response (for interactive protocols)
fn challenge_response_protocol() {
    // Server → Client: Random challenge
    let challenge: [u8; 32] = generate_random();
    
    // Client → Server: Sign(private_key, challenge || transaction_data)
    let response = sign_data(private_key, &[&challenge, &transaction_data].concat());
    
    // Server verifies signature includes fresh challenge
    // Cannot replay because challenge is different each time
}
```

**TLS Session Resumption Attack:**

```
TLS 1.2 allows session resumption with session IDs:

Normal:
Client → Server: ClientHello [session_id: 0x1234]
Server → Server: Looks up session 0x1234, resumes encrypted session

Attack:
Attacker captures session_id: 0x1234
Attacker → Server: ClientHello [session_id: 0x1234]
Server resumes Alice's session for attacker!

Mitigation (TLS 1.3):
- Session tickets encrypted with server key
- Includes timestamp, expires after short period
- Can only be used once (nonce in ticket)
```

---

### 8. Man-in-the-Middle (MITM) Attacks

**Concept**: Attacker intercepts and potentially alters communication between two parties.

**Attack Scenario - Diffie-Hellman MITM:**

```
Normal DH:
Alice                                    Bob
  ↓                                       ↓
Pick a, compute A = g^a            Pick b, compute B = g^b
      ─────── A ───────→
      ←────── B ────────
Compute K = B^a                    Compute K = A^b
      Both have K = g^(ab)


MITM Attack:
Alice            Attacker                Bob
  ↓                 ↓                     ↓
A = g^a         Pick m, n              B = g^b
      ─ A →    ← A ─╳── M = g^m →       
      ← M ─    ← B ──── N = g^n ─→   ← B
K_am = M^a    K_am = A^m          K_bn = B^n
                K_bn = N^b

Alice thinks she shares K_am with Bob
Bob thinks he shares K_bn with Alice  
Attacker decrypts with both keys, reads/modifies, re-encrypts
```

**Implementation:**

```c
// VULNERABLE: Unauthenticated Diffie-Hellman
#include <stdio.h>
#include <stdint.h>

typedef struct {
    uint64_t p;  // Prime modulus
    uint64_t g;  // Generator
} DHParams;

typedef struct {
    uint64_t private_key;
    uint64_t public_key;
} DHKeyPair;

uint64_t mod_exp(uint64_t base, uint64_t exp, uint64_t mod) {
    uint64_t result = 1;
    base %= mod;
    while (exp > 0) {
        if (exp & 1) result = (result * base) % mod;
        base = (base * base) % mod;
        exp >>= 1;
    }
    return result;
}

DHKeyPair dh_generate_keypair(DHParams params) {
    DHKeyPair kp;
    kp.private_key = rand() % (params.p - 2) + 1; // Random private key
    kp.public_key = mod_exp(params.g, kp.private_key, params.p);
    return kp;
}

uint64_t dh_compute_shared_secret(uint64_t their_public, uint64_t my_private, uint64_t p) {
    return mod_exp(their_public, my_private, p);
}

void vulnerable_key_exchange() {
    DHParams params = { .p = 23, .g = 5 }; // Small for demonstration
    
    // Alice
    DHKeyPair alice = dh_generate_keypair(params);
    printf("Alice sends public key: %lu\n", alice.public_key);
    
    // ← VULNERABILITY: Alice has no way to verify this is actually Bob's key!
    uint64_t received_public = /* ... receive from network ... */;
    
    // Alice computes shared secret
    uint64_t alice_secret = dh_compute_shared_secret(received_public, 
                                                      alice.private_key, 
                                                      params.p);
}

// MITM Attack simulation
void mitm_attack_demo() {
    DHParams params = { .p = 23, .g = 5 };
    
    // Alice generates keypair
    DHKeyPair alice = dh_generate_keypair(params);
    printf("[Alice] Public key: %lu\n", alice.public_key);
    
    // Attacker intercepts, generates own keypairs
    DHKeyPair attacker_to_alice = dh_generate_keypair(params);
    DHKeyPair attacker_to_bob = dh_generate_keypair(params);
    
    printf("[Attacker] To Alice: %lu, To Bob: %lu\n", 
           attacker_to_alice.public_key,
           attacker_to_bob.public_key);
    
    // Bob generates keypair
    DHKeyPair bob = dh_generate_keypair(params);
    printf("[Bob] Public key: %lu\n", bob.public_key);
    
    // Alice receives attacker's key (thinking it's Bob's)
    uint64_t alice_secret = dh_compute_shared_secret(
        attacker_to_alice.public_key, 
        alice.private_key, 
        params.p
    );
    
    // Bob receives attacker's key (thinking it's Alice's)
    uint64_t bob_secret = dh_compute_shared_secret(
        attacker_to_bob.public_key, 
        bob.private_key, 
        params.p
    );
    
    // Attacker can compute both shared secrets
    uint64_t attacker_alice_secret = dh_compute_shared_secret(
        alice.public_key, 
        attacker_to_alice.private_key, 
        params.p
    );
    
    uint64_t attacker_bob_secret = dh_compute_shared_secret(
        bob.public_key, 
        attacker_to_bob.private_key, 
        params.p
    );
    
    printf("\n[Alice thinks shared secret is: %lu]\n", alice_secret);
    printf("[Bob thinks shared secret is: %lu]\n", bob_secret);
    printf("[Attacker knows both: %lu and %lu]\n", 
           attacker_alice_secret, 
           attacker_bob_secret);
    
    // Attacker can now decrypt all messages from both parties!
}
```

**Mitigation - Authenticated Key Exchange:**

```rust
use ed25519_dalek::{Keypair, PublicKey, Signature, Signer, Verifier};
use x25519_dalek::{EphemeralSecret, PublicKey as X25519PublicKey};
use rand::rngs::OsRng;

// Station-to-Station Protocol (STS)
struct STSParticipant {
    identity_keypair: Keypair,  // Long-term signing key
    dh_secret: EphemeralSecret, // Ephemeral DH key
    dh_public: X25519PublicKey,
}

impl STSParticipant {
    fn new() -> Self {
        let mut csprng = OsRng;
        let identity_keypair = Keypair::generate(&mut csprng);
        let dh_secret = EphemeralSecret::new(&mut csprng);
        let dh_public = X25519PublicKey::from(&dh_secret);
        
        STSParticipant {
            identity_keypair,
            dh_secret,
            dh_public,
        }
    }
    
    fn create_signed_exchange(&self, their_dh_public: &X25519PublicKey) 
        -> (X25519PublicKey, Signature) {
        
        // Sign: Sign(my_dh_public || their_dh_public)
        let mut message = Vec::new();
        message.extend_from_slice(self.dh_public.as_bytes());
        message.extend_from_slice(their_dh_public.as_bytes());
        
        let signature = self.identity_keypair.sign(&message);
        
        (self.dh_public, signature)
    }
    
    fn verify_exchange(
        &self,
        their_identity: &PublicKey,
        their_dh_public: X25519PublicKey,
        their_signature: &Signature
    ) -> Result<[u8; 32], &'static str> {
        
        // Verify: Verify(their_dh_public || my_dh_public, signature, their_identity)
        let mut message = Vec::new();
        message.extend_from_slice(their_dh_public.as_bytes());
        message.extend_from_slice(self.dh_public.as_bytes());
        
        their_identity.verify(&message, their_signature)
            .map_err(|_| "Signature verification failed - possible MITM!")?;
        
        // Compute shared secret (only if signature valid)
        let shared_secret = self.dh_secret.diffie_hellman(&their_dh_public);
        
        Ok(*shared_secret.as_bytes())
    }
}

// Demonstration
fn authenticated_dh_exchange() {
    // Alice and Bob create participants
    let alice = STSParticipant::new();
    let bob = STSParticipant::new();
    
    // Assume Alice and Bob have each other's long-term public keys
    // (obtained through trusted channel, e.g., certificate authority)
    let alice_identity = alice.identity_keypair.public;
    let bob_identity = bob.identity_keypair.public;
    
    // Exchange 1: Alice → Bob
    let (alice_dh, alice_sig) = alice.create_signed_exchange(&bob.dh_public);
    
    // Exchange 2: Bob → Alice
    let (bob_dh, bob_sig) = bob.create_signed_exchange(&alice.dh_public);
    
    // Alice verifies Bob
    let alice_secret = alice.verify_exchange(
        &bob_identity,
        bob_dh,
        &bob_sig
    ).expect("Bob verification failed");
    
    // Bob verifies Alice
    let bob_secret = bob.verify_exchange(
        &alice_identity,
        alice_dh,
        &alice_sig
    ).expect("Alice verification failed");
    
    // Both have same secret, and both verified each other's identity
    assert_eq!(alice_secret, bob_secret);
    println!("Secure key exchange completed!");
    
    // If MITM attempts attack:
    // - Attacker can't forge Alice's or Bob's signatures
    // - Even if attacker replaces DH public keys, signature won't verify
}

// MITM attempt on STS
fn mitm_attempt_on_sts() {
    let alice = STSParticipant::new();
    let bob = STSParticipant::new();
    let attacker = STSParticipant::new();
    
    let alice_identity = alice.identity_keypair.public;
    let bob_identity = bob.identity_keypair.public;
    
    // Attacker tries to intercept
    let (alice_dh, alice_sig) = alice.create_signed_exchange(&bob.dh_public);
    
    // Attacker tries to replace Alice's DH key with their own
    let (attacker_dh, attacker_sig) = attacker.create_signed_exchange(&bob.dh_public);
    
    // Bob receives attacker's message (attacker_dh, attacker_sig)
    // Bob tries to verify using Alice's identity key
    let result = bob.verify_exchange(
        &alice_identity,  // Expecting Alice's signature
        attacker_dh,
        &attacker_sig     // But this is attacker's signature!
    );
    
    // Verification FAILS - attacker's signature doesn't match Alice's key
    assert!(result.is_err());
    println!("MITM attack detected and prevented!");
}
```

**Certificate Pinning (for TLS):**

```rust
use rustls::{ClientConfig, RootCertStore};
use webpki::DNSNameRef;
use std::sync::Arc;

// Pin expected certificate
fn create_pinned_client_config(expected_cert_der: &[u8]) -> Arc<ClientConfig> {
    let mut config = ClientConfig::new();
    
    // Custom certificate verifier
    struct PinnedVerifier {
        expected_cert: Vec<u8>,
    }
    
    impl rustls::ServerCertVerifier for PinnedVerifier {
        fn verify_server_cert(
            &self,
            _roots: &RootCertStore,
            presented_certs: &[rustls::Certificate],
            _dns_name: DNSNameRef,
            _ocsp_response: &[u8],
        ) -> Result<rustls::ServerCertVerified, rustls::TLSError> {
            
            // Check if presented certificate matches pinned certificate
            if presented_certs.is_empty() {
                return Err(rustls::TLSError::NoCertificatesPresented);
            }
            
            if presented_certs[0].0 != self.expected_cert {
                return Err(rustls::TLSError::WebPKIError(
                    webpki::Error::UnknownIssuer
                ));
            }
            
            Ok(rustls::ServerCertVerified::assertion())
        }
    }
    
    config.dangerous().set_certificate_verifier(Arc::new(PinnedVerifier {
        expected_cert: expected_cert_der.to_vec(),
    }));
    
    Arc::new(config)
}
```

**Additional Mitigations:**

1. **Public Key Infrastructure (PKI)**: Certificate authorities sign public keys
2. **Key Fingerprint Verification**: Users manually verify key fingerprints (SSH)
3. **Trust on First Use (TOFU)**: Accept first key, alert on changes
4. **Certificate Transparency**: Public logs of all certificates issued

---

### 9. Downgrade Attacks

**Concept**: Force use of weaker cryptographic algorithms by manipulating negotiation.

**Attack Scenario - TLS Protocol Downgrade:**

```
Normal TLS Handshake:
Client → Server: "I support TLS 1.3, 1.2, 1.1"
Server → Client: "Let's use TLS 1.3"

Downgrade Attack:
Client → Server: "I support TLS 1.3, 1.2, 1.1"
         ↓ (Attacker modifies in transit)
         "I support TLS 1.0" ← Vulnerable version
Server → Client: "Let's use TLS 1.0"
         Attacker can now exploit TLS 1.0 vulnerabilities!
```

**FREAK Attack (2015):**

```go
// Simplified TLS negotiation (vulnerable)
type CipherSuite uint16

const (
    TLS_RSA_WITH_AES_256_GCM_SHA384 CipherSuite = 0x009D // Strong
    TLS_RSA_EXPORT_WITH_RC4_40_MD5  CipherSuite = 0x0003 // Weak (40-bit key!)
)

type ClientHello struct {
    Version uint16
    SupportedCiphers []CipherSuite
}

type ServerHello struct {
    Version uint16
    ChosenCipher CipherSuite
}

// VULNERABLE: Server accepts export-grade cipher
func serverChooseCipher(clientHello ClientHello) ServerHello {
    // Check if client supports any cipher
    for _, cipher := range clientHello.SupportedCiphers {
        // Server accepts even weak 40-bit export cipher!
        if cipher == TLS_RSA_EXPORT_WITH_RC4_40_MD5 {
            return ServerHello{
                Version: 0x0301, // TLS 1.0
                ChosenCipher: TLS_RSA_EXPORT_WITH_RC4_40_MD5,
            }
        }
    }
    // ... check other ciphers
}

// Attack: Attacker modifies ClientHello to include only weak cipher
func freakAttack() {
    // Original ClientHello
    original := ClientHello{
        Version: 0x0303, // TLS 1.2
        SupportedCiphers: []CipherSuite{
            TLS_RSA_WITH_AES_256_GCM_SHA384, // Strong
        },
    }
    
    // Attacker intercepts and modifies
    modified := ClientHello{
        Version: 0x0301, // Downgraded to TLS 1.0
        SupportedCiphers: []CipherSuite{
            TLS_RSA_EXPORT_WITH_RC4_40_MD5, // Only weak cipher
        },
    }
    
    // Server accepts weak cipher
    response := serverChooseCipher(modified)
    
    // Now attacker can brute-force 40-bit key in hours!
    println("Server chose 40-bit cipher - vulnerable to brute force!")
}
```

**Mitigation - Downgrade Protection:**

```rust
use sha2::{Sha256, Digest};

// TLS 1.3 Downgrade Protection
const TLS_12_DOWNGRADE_SENTINEL: [u8; 8] = [
    0x44, 0x4F, 0x57, 0x4E, 0x47, 0x52, 0x44, 0x01
]; // "DOWNGRD\x01"

const TLS_11_DOWNGRADE_SENTINEL: [u8; 8] = [
    0x44, 0x4F, 0x57, 0x4E, 0x47, 0x52, 0x44, 0x00
]; // "DOWNGRD\x00"

struct SecureServerHello {
    version: u16,
    random: [u8; 32],
    cipher_suite: u16,
}

impl SecureServerHello {
    fn new(client_max_version: u16, actual_version: u16) -> Self {
        let mut random = [0u8; 32];
        rand::RngCore::fill_bytes(&mut rand::rngs::OsRng, &mut random);
        
        // If downgrading, embed sentinel in random bytes
        if client_max_version == 0x0304 && actual_version <= 0x0303 {
            // Client supports TLS 1.3, but we're using TLS 1.2 or lower
            // Embed downgrade sentinel
            random[24..32].copy_from_slice(&TLS_12_DOWNGRADE_SENTINEL);
        } else if client_max_version >= 0x0303 && actual_version <= 0x0302 {
            // Client supports TLS 1.2+, but we're using TLS 1.1 or lower
            random[24..32].copy_from_slice(&TLS_11_DOWNGRADE_SENTINEL);
        }
        
        SecureServerHello {
            version: actual_version,
            random,
            cipher_suite: 0x009D, // Strong cipher
        }
    }
}

// Client verification
fn verify_no_downgrade(
    server_hello: &SecureServerHello,
    client_max_version: u16
) -> Result<(), &'static str> {
    
    let last_8 = &server_hello.random[24..32];
    
    // Check for downgrade sentinels
    if client_max_version >= 0x0304 && last_8 == &TLS_12_DOWNGRADE_SENTINEL {
        return Err("Downgrade attack detected: Server supports TLS 1.3 but negotiated lower");
    }
    
    if client_max_version >= 0x0303 && last_8 == &TLS_11_DOWNGRADE_SENTINEL {
        return Err("Downgrade attack detected: Server supports TLS 1.2 but negotiated lower");
    }
    
    Ok(())
}

// 2. Signature over entire handshake (TLS 1.3)
fn verify_handshake_signature(
    handshake_messages: &[Vec<u8>],
    signature: &[u8],
    server_pubkey: &PublicKey
) -> Result<(), &'static str> {
    
    // Hash all handshake messages
    let mut hasher = Sha256::new();
    for message in handshake_messages {
        hasher.update(message);
    }
    let transcript_hash = hasher.finalize();
    
    // Verify signature
    use ed25519_dalek::Verifier;
    let sig = ed25519_dalek::Signature::from_bytes(signature)
        .map_err(|_| "Invalid signature format")?;
    
    server_pubkey.verify(&transcript_hash, &sig)
        .map_err(|_| "Signature verification failed - possible tampering")?;
    
    // If attacker modified any handshake message (including version/ciphers),
    // the transcript hash won't match and signature verification fails
    
    Ok(())
}

// 3. Strict cipher suite enforcement
fn enforce_minimum_security(cipher_suite: u16) -> Result<(), &'static str> {
    const MINIMUM_KEY_SIZE: u16 = 128;
    const FORBIDDEN_CIPHERS: &[u16] = &[
        0x0003, // RSA_EXPORT_WITH_RC4_40_MD5
        0x0006, // RSA_EXPORT_WITH_RC2_CBC_40_MD5
        // ... all export and weak ciphers
    ];
    
    if FORBIDDEN_CIPHERS.contains(&cipher_suite) {
        return Err("Cipher suite does not meet minimum security requirements");
    }
    
    // Additional checks: no NULL encryption, no anonymous DH, etc.
    
    Ok(())
}
```

**POODLE Attack (2014):**

Forces downgrade to SSL 3.0, then exploits padding oracle vulnerability.

**Mitigation:**
```rust
// Disable all old protocol versions
fn create_secure_tls_config() -> rustls::ClientConfig {
    let mut config = rustls::ClientConfig::new();
    
    // Only allow TLS 1.2 and 1.3
    config.versions = vec![
        rustls::ProtocolVersion::TLSv1_3,
        rustls::ProtocolVersion::TLSv1_2,
    ];
    
    // Restrict to strong cipher suites
    config.ciphersuites = vec![
        rustls::CipherSuite::TLS13_AES_256_GCM_SHA384,
        rustls::CipherSuite::TLS13_CHACHA20_POLY1305_SHA256,
        // No TLS 1.2 ciphers - force upgrade to 1.3
    ];
    
    config
}
```

---

(Continued in next response due to length...)

Would you like me to continue with the remaining attack vectors including:
- Length extension attacks
- Birthday attacks
- Meet-in-the-middle attacks
- Quantum computing threats
- Social engineering attacks
- Real-world case studies

I can provide equally detailed analysis for each, with code examples in Rust/C/Go demonstrating both the attacks and mitigations.