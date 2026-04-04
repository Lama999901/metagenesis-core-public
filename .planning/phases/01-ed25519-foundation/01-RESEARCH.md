# Phase 1: Ed25519 Foundation - Research

**Researched:** 2026-03-17
**Domain:** Pure-Python Ed25519 cryptographic signing (RFC 8032 Section 5.1)
**Confidence:** HIGH

## Summary

Phase 1 implements a standalone pure-Python Ed25519 module (`scripts/mg_ed25519.py`) that provides key generation, signing, and verification using only Python 3.11 stdlib. The module must pass all five RFC 8032 Section 7.1 test vectors to prove cryptographic correctness before any integration with bundle signing (Phase 2).

The implementation is straightforward: Ed25519 is built on SHA-512 (available via `hashlib`), modular arithmetic over GF(2^255-19) using Python's arbitrary-precision integers, and Edwards curve point operations. The total implementation is approximately 200-250 lines. The key generation CLI produces two files (private key JSON and public key JSON) following the same format patterns as the existing HMAC key files in `mg_sign.py`.

**Primary recommendation:** Implement Ed25519 from the RFC 8032 Section 5.1 specification directly, using the five test vectors from Section 7.1 as the correctness gate. Do not vendor a third-party library. The RFC provides pseudocode-level detail sufficient for a correct implementation.

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions
- New file `scripts/mg_ed25519.py` -- standalone, next to `mg_sign.py`
- Self-contained: Ed25519 math, key generation, sign, verify all in one module
- Running `python scripts/mg_ed25519.py` directly executes all RFC 8032 Section 7.1 test vectors and prints PASS/FAIL
- ALSO add pytest tests in `tests/` directory for CI integration
- Key file format: JSON with `{version, private_key_hex, public_key_hex, fingerprint, note}`, version field `"ed25519-v1"`
- Store BOTH private and public key in the key file
- Fingerprint: SHA-256 of public key (safe to share)
- keygen auto-generates two files: `key.json` (full private+public) and `key.pub.json` (public only for sharing with auditors)
- Ed25519 only (Section 5.1) -- no Ed25519ph or Ed25519ctx
- All test vectors from RFC 8032 Section 7.1

### Claude's Discretion
- Internal module structure (helper functions, class vs functions)
- Elliptic curve arithmetic implementation details
- Error message wording
- Exact test output format (as long as PASS/FAIL is clear)

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope

</user_constraints>

<phase_requirements>

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| SIGN-01 | Pure-Python Ed25519 implementation based on RFC 8032 with test vector validation | Full RFC 8032 Section 5.1 algorithm documented below; all 5 test vectors from Section 7.1 extracted and verified; implementation uses only hashlib.sha512 + Python int arithmetic |
| SIGN-02 | Ed25519 key pair generation (private key + public key) via CLI command | CLI pattern follows existing mg_sign.py argparse subcommand pattern; key file format parallels HMAC key JSON structure |
| SIGN-05 | Public key export for third-party auditors (standalone file) | keygen produces companion `.pub.json` at generation time; no separate export command needed |

</phase_requirements>

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python | 3.11.0 | Runtime | Already in use; `int.from_bytes`/`int.to_bytes`, `hashlib.sha512`, `secrets` all available |
| hashlib (stdlib) | ships with 3.11 | SHA-512 for Ed25519 internals, SHA-256 for key fingerprint | RFC 8032 mandates SHA-512 for Ed25519; already used throughout codebase |
| secrets (stdlib) | ships with 3.11 | Cryptographic random 32-byte private key generation | Already used in mg_sign.py `generate_key()` |
| json (stdlib) | ships with 3.11 | Key file serialization (JSON format) | Project standard for all config/key/manifest files |
| argparse (stdlib) | ships with 3.11 | CLI subcommands (keygen, test) | Same pattern as mg_sign.py |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest | 8.4.1 (pinned) | CI test integration for Ed25519 correctness | `tests/steward/test_ed25519.py` for CI gate |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Pure-Python Ed25519 | `cryptography` package (PyCA) | Violates stdlib-only constraint; not acceptable for this project |
| Pure-Python Ed25519 | `PyNaCl` (libsodium) | Native C dependency; violates stdlib-only and air-gap deployment model |
| Pure-Python Ed25519 | Vendoring `ed25519` PyPI package | Audit burden; RFC 8032 reference code is cleaner for ~200 lines |

**Installation:**
```bash
# No new packages needed. Zero dependency additions.
# Ed25519 uses only Python stdlib: hashlib, secrets, json, argparse
```

## Architecture Patterns

### Recommended Module Structure

```
scripts/
  mg_ed25519.py          # NEW: Ed25519 implementation + CLI + self-test
tests/
  steward/
    test_ed25519.py      # NEW: pytest CI tests for Ed25519 correctness
```

### Pattern 1: Ed25519 Module Layout

**What:** Single-file module with clear sections: constants, field arithmetic, curve operations, encoding, key generation, sign, verify, CLI, self-test.

**When to use:** All Ed25519 operations in Phase 1.

**Example structure:**
```python
#!/usr/bin/env python3
"""
MetaGenesis Core -- Ed25519 Signing (RFC 8032 Section 5.1)
Pure-Python, stdlib only. No external dependencies.
"""
import argparse
import hashlib
import json
import secrets
import sys
from pathlib import Path

# ---- Ed25519 Constants (RFC 8032 Section 5.1) ----
P = 2**255 - 19                                           # Field prime
L = 2**252 + 27742317777372353535851937790883648493        # Group order
D = -121665 * pow(121666, P - 2, P) % P                   # Curve parameter
I = pow(2, (P - 1) // 4, P)                               # sqrt(-1) mod P

# Base point B
BY = 4 * pow(5, P - 2, P) % P   # y = 4/5
BX = ...                         # recovered from curve equation

KEY_VERSION = "ed25519-v1"

# ---- Field Arithmetic ----
# Modular inverse, square root mod p

# ---- Edwards Curve Point Operations ----
# Point addition, scalar multiplication (double-and-add)

# ---- Encoding/Decoding (RFC 8032) ----
# Point encoding (32 bytes), point decoding, scalar encoding

# ---- Key Generation (RFC 8032 Section 5.1.5) ----
def generate_keypair() -> tuple[bytes, bytes]:
    """Generate Ed25519 key pair. Returns (private_key_32bytes, public_key_32bytes)."""

# ---- Sign (RFC 8032 Section 5.1.6) ----
def sign(private_key: bytes, message: bytes) -> bytes:
    """Sign message with Ed25519 private key. Returns 64-byte signature."""

# ---- Verify (RFC 8032 Section 5.1.7) ----
def verify(public_key: bytes, message: bytes, signature: bytes) -> bool:
    """Verify Ed25519 signature. Returns True if valid."""

# ---- Key File Management ----
def generate_key_files(out_path: Path) -> dict:
    """Generate key pair and write key.json + key.pub.json."""

# ---- CLI ----
def cmd_keygen(args): ...
def cmd_test(args): ...   # self-test with RFC 8032 vectors
def main(): ...

# ---- Self-Test (RFC 8032 Section 7.1) ----
def run_self_test() -> bool:
    """Run all RFC 8032 test vectors. Returns True if all pass."""

if __name__ == "__main__":
    sys.exit(main())
```

### Pattern 2: Key File Format (Parallel to HMAC)

**What:** JSON key files with `version` field as discriminator, following mg_sign.py pattern.

**Example -- Private key file (`key.json`):**
```json
{
  "version": "ed25519-v1",
  "private_key_hex": "<64 hex chars, 32 bytes>",
  "public_key_hex": "<64 hex chars, 32 bytes>",
  "fingerprint": "<sha256 of public key bytes>",
  "note": "KEEP THIS FILE SECRET. Share key.pub.json with auditors."
}
```

**Example -- Public key file (`key.pub.json`):**
```json
{
  "version": "ed25519-v1",
  "public_key_hex": "<64 hex chars, 32 bytes>",
  "fingerprint": "<sha256 of public key bytes>",
  "note": "Public key for Ed25519 signature verification. Safe to share."
}
```

### Pattern 3: Self-Test Mode (Mirrors deep_verify.py)

**What:** Running `python scripts/mg_ed25519.py` with no subcommand (or a `test` subcommand) executes all RFC 8032 test vectors and prints PASS/FAIL.

**Example output:**
```
Ed25519 Self-Test (RFC 8032 Section 7.1)
  Vector 1 (empty message):     PASS
  Vector 2 (1 byte):            PASS
  Vector 3 (2 bytes):           PASS
  Vector 4 (1023 bytes):        PASS
  Vector 5 (SHA(abc)):          PASS

ALL 5 VECTORS PASSED
```

### Anti-Patterns to Avoid

- **Importing from `cryptography` or any non-stdlib package:** Violates the project's zero-dependency constraint. Every import must be stdlib.
- **Branching key generation based on runtime `cryptography` availability:** The CONTEXT.md decision is pure-Python, not optional-dependency. No fallback patterns.
- **Modifying mg_sign.py in Phase 1:** Integration is Phase 2. mg_ed25519.py must be standalone and importable but does not touch mg_sign.py.
- **Using variable-time comparisons for signature verification:** Use `hmac.compare_digest()` or equivalent constant-time comparison for the final signature check in verify.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| SHA-512 hashing | Custom hash function | `hashlib.sha512` | RFC 8032 mandates SHA-512; hashlib wraps OpenSSL, battle-tested |
| Cryptographic random bytes | `os.urandom` or `random` | `secrets.token_bytes(32)` | `secrets` is the stdlib CSPRNG module; already used in mg_sign.py |
| JSON serialization | Custom file format | `json.dumps` with `indent=2` | Project standard; same as HMAC key files |
| CLI argument parsing | Manual sys.argv parsing | `argparse` with subcommands | Same pattern as mg_sign.py |

**Key insight:** The only custom cryptographic code is the Ed25519 curve arithmetic itself (~150 lines). Everything else (hashing, randomness, serialization, CLI) uses stdlib.

## Common Pitfalls

### Pitfall 1: Clamping the Private Key Scalar Incorrectly

**What goes wrong:** Ed25519 key generation requires "pruning" (clamping) the SHA-512 hash of the private seed: clear the lowest 3 bits of byte 0, clear the highest bit of byte 31, set the second-highest bit of byte 31. Getting the bit manipulation wrong produces keys that generate valid-looking but incorrect signatures.

**Why it happens:** The clamping is specified in RFC 8032 Section 5.1.5 but is easy to misread. The "first octet" in the RFC is the lowest byte (index 0) in little-endian.

**How to avoid:** Implement clamping exactly as:
```python
h = bytearray(hashlib.sha512(private_seed).digest())
h[0] &= 248      # Clear lowest 3 bits
h[31] &= 127     # Clear highest bit
h[31] |= 64      # Set second highest bit
```
Verify against test vector 1: private seed `9d61...7f60` must produce public key `d75a...511a`.

**Warning signs:** Test vector 1 passes but vector 4 or 5 fails (subtle clamping error masked by specific bit patterns).

### Pitfall 2: Point Decoding Sign Bit

**What goes wrong:** Ed25519 encodes points as 32 bytes where the high bit of byte 31 carries the sign of the x-coordinate. When decoding, extracting and clearing this bit incorrectly leads to the wrong point, which silently produces wrong signatures.

**Why it happens:** The encoding packs the x-coordinate sign into the y-coordinate's representation. The sign bit is bit 255 (the MSB of byte 31), which must be extracted before interpreting the remaining 255 bits as the y-coordinate.

**How to avoid:**
```python
def point_decode(s: bytes):
    # Extract sign bit from byte 31
    sign_bit = (s[31] >> 7) & 1
    # Clear sign bit to get y
    y = int.from_bytes(s, "little") & ((1 << 255) - 1)
    # Recover x from curve equation, select correct sign
    ...
```
Verify: decoding the base point B from its encoding must round-trip correctly.

### Pitfall 3: Modular Square Root (Recovery of x from y)

**What goes wrong:** Recovering the x-coordinate from y requires computing a modular square root. For p = 2^255 - 19, this uses `x = u^((p+3)/8) mod p` with a correction factor. Missing the correction (when `x^2 != u mod p` but `x^2 = -u mod p`) silently breaks point decoding for approximately half of all points.

**Why it happens:** The square root formula has two cases and the second case requires multiplying by sqrt(-1) mod p. Forgetting this case means half the RFC test vectors fail.

**How to avoid:** Implement the full recovery:
```python
def recover_x(y, sign):
    # u = y^2 - 1, v = d*y^2 + 1
    u = (y * y - 1) % P
    v = (D * y * y + 1) % P
    x = pow(u * v, (P + 3) // 8, P) * u % P  # candidate
    # Check and correct
    if (v * x * x - u) % P != 0:
        x = x * I % P  # I = sqrt(-1) mod p
    if (v * x * x - u) % P != 0:
        raise ValueError("invalid point")
    if x % 2 != sign:
        x = P - x
    return x
```

### Pitfall 4: Scalar Reduction Modulo L in Signing

**What goes wrong:** During signing, the hash output (64 bytes = 512 bits) must be reduced modulo L (the group order). If the reduction is done incorrectly (e.g., using P instead of L, or truncating instead of reducing), signatures will be wrong.

**Why it happens:** Two different moduli are used: P for field arithmetic and L for scalar arithmetic. Confusing them is easy.

**How to avoid:** Be explicit about which modulus:
```python
# Field operations use P = 2^255 - 19
# Scalar operations use L = 2^252 + 27742317777372353535851937790883648493
r = int.from_bytes(sha512_hash, "little") % L   # Scalar reduction
```

### Pitfall 5: Breaking 295 Existing Tests

**What goes wrong:** Adding a new file to `scripts/` or `tests/` could theoretically interfere with existing imports or test collection. More likely: an accidental edit to an existing file while working on Ed25519.

**How to avoid:** The new module is standalone. Do not modify any existing file. Run `python -m pytest tests/ -q` before and after every change to verify 295 tests still pass.

**Warning signs:** Any test failure not in the new Ed25519 test file.

## Code Examples

### Ed25519 Constants (from RFC 8032 Section 5.1)

```python
# Source: RFC 8032 Section 5.1
P = 2**255 - 19
L = 2**252 + 27742317777372353535851937790883648493
D = -121665 * pow(121666, P - 2, P) % P
I = pow(2, (P - 1) // 4, P)  # sqrt(-1) mod P

# Base point B (y = 4/5 mod P)
BY = 4 * pow(5, P - 2, P) % P
BX = recover_x(BY, 0)  # recover_x implements the sqrt formula
B = (BX, BY, 1, BX * BY % P)  # Extended coordinates (x, y, z, t)
```

### Key Generation (RFC 8032 Section 5.1.5)

```python
# Source: RFC 8032 Section 5.1.5
def generate_keypair():
    private_seed = secrets.token_bytes(32)
    h = bytearray(hashlib.sha512(private_seed).digest())
    # Clamp
    h[0] &= 248
    h[31] &= 127
    h[31] |= 64
    scalar = int.from_bytes(h[:32], "little")
    public_point = scalar_mult(scalar, B)
    public_key = point_encode(public_point)
    return private_seed, public_key
```

### Signing (RFC 8032 Section 5.1.6)

```python
# Source: RFC 8032 Section 5.1.6
def sign(private_seed: bytes, message: bytes) -> bytes:
    h = hashlib.sha512(private_seed).digest()
    a_bytes = bytearray(h[:32])
    a_bytes[0] &= 248; a_bytes[31] &= 127; a_bytes[31] |= 64
    a = int.from_bytes(bytes(a_bytes), "little")
    prefix = h[32:]
    public_key = point_encode(scalar_mult(a, B))

    r_hash = hashlib.sha512(prefix + message).digest()
    r = int.from_bytes(r_hash, "little") % L
    R = scalar_mult(r, B)
    R_bytes = point_encode(R)

    k_hash = hashlib.sha512(R_bytes + public_key + message).digest()
    k = int.from_bytes(k_hash, "little") % L
    S = (r + k * a) % L

    return R_bytes + S.to_bytes(32, "little")
```

### Verification (RFC 8032 Section 5.1.7)

```python
# Source: RFC 8032 Section 5.1.7
def verify(public_key: bytes, message: bytes, signature: bytes) -> bool:
    if len(signature) != 64 or len(public_key) != 32:
        return False
    R_bytes = signature[:32]
    S = int.from_bytes(signature[32:], "little")
    if S >= L:
        return False
    A = point_decode(public_key)
    R = point_decode(R_bytes)
    if A is None or R is None:
        return False
    k_hash = hashlib.sha512(R_bytes + public_key + message).digest()
    k = int.from_bytes(k_hash, "little") % L
    # Check: [8*S]B == [8]R + [8*k]A
    lhs = scalar_mult(8 * S, B)
    rhs = point_add(scalar_mult(8, R), scalar_mult(8 * k, A))
    return lhs == rhs  # Compare in extended coordinates (normalize first)
```

### RFC 8032 Section 7.1 Test Vectors (All 5)

```python
# Source: RFC 8032 Section 7.1 (fetched from rfc-editor.org)
TEST_VECTORS = [
    {
        "name": "Vector 1 (empty message)",
        "private": "9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60",
        "public":  "d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a",
        "message": "",
        "signature": "e5564300c360ac729086e2cc806e828a84877f1eb8e5d974d873e06522490155"
                     "5fb8821590a33bacc61e39701cf9b46bd25bf5f0595bbe24655141438e7a100b",
    },
    {
        "name": "Vector 2 (1 byte)",
        "private": "4ccd089b28ff96da9db6c346ec114e0f5b8a319f35aba624da8cf6ed4fb8a6fb",
        "public":  "3d4017c3e843895a92b70aa74d1b7ebc9c982ccf2ec4968cc0cd55f12af4660c",
        "message": "72",
        "signature": "92a009a9f0d4cab8720e820b5f642540a2b27b5416503f8fb3762223ebdb69da"
                     "085ac1e43e15996e458f3613d0f11d8c387b2eaeb4302aeeb00d291612bb0c00",
    },
    {
        "name": "Vector 3 (2 bytes)",
        "private": "c5aa8df43f9f837bedb7442f31dcb7b166d38535076f094b85ce3a2e0b4458f7",
        "public":  "fc51cd8e6218a1a38da47ed00230f0580816ed13ba3303ac5deb911548908025",
        "message": "af82",
        "signature": "6291d657deec24024827e69c3abe01a30ce548a284743a445e3680d7db5ac3ac"
                     "18ff9b538d16f290ae67f760984dc6594a7c15e9716ed28dc027beceea1ec40a",
    },
    {
        "name": "Vector 4 (1023 bytes)",
        "private": "f5e5767cf153319517630f226876b86c8160cc583bc013744c6bf255f5cc0ee5",
        "public":  "278117fc144c72340f67d0f2316e8386ceffbf2b2428c9c51fef7c597f1d426e",
        "message": "08b8b2b733424243760fe426a4b54908632110a66c2f6591eabd3345e3e4eb98"
                   "fa6e264bf09efe12ee50f8f54e9f77b1e355f6c50544e23fb1433ddf73be84d8"
                   "879de7c0046dc4996d9e773f4bc9efe5738829adb26c81b37c93a1b270b20329"
                   "d658675fc6ea534e0810a4432826bf58c941efb65d57a338bbd2e26640f89ffb"
                   "c1a858efcb8550ee3a5e1998bd177e93a7363c344fe6b199ee5d02e82d522c4f"
                   "eba15452f80288a821a579116ec6dad2b3b310da903401aa62100ab5d1a36553"
                   "e06203b33890cc9b832f79ef80560ccb9a39ce767967ed628c6ad573cb116dbe"
                   "ffefd75499da96bd68a8a97b928a8bbc103b6621fcde2beca1231d206be6cd9e"
                   "c7aff6f6c94fcd7204ed3455c68c83f4a41da4af2b74ef5c53f1d8ac70bdcb7e"
                   "d185ce81bd84359d44254d95629e9855a94a7c1958d1f8ada5d0532ed8a5aa3f"
                   "b2d17ba70eb6248e594e1a2297acbbb39d502f1a8c6eb6f1ce22b3de1a1f40cc"
                   "24554119a831a9aad6079cad88425de6bde1a9187ebb6092cf67bf2b13fd65f2"
                   "7088d78b7e883c8759d2c4f5c65adb7553878ad575f9fad878e80a0c9ba63bcb"
                   "cc2732e69485bbc9c90bfbd62481d9089beccf80cfe2df16a2cf65bd92dd597b"
                   "0707e0917af48bbb75fed413d238f5555a7a569d80c3414a8d0859dc65a46128"
                   "bab27af87a71314f318c782b23ebfe808b82b0ce26401d2e22f04d83d1255dc5"
                   "1addd3b75a2b1ae0784504df543af8969be3ea7082ff7fc9888c144da2af5842"
                   "9ec96031dbcad3dad9af0dcbaaaf268cb8fcffead94f3c7ca495e056a9b47acdb"
                   "751fb73e666c6c655ade8297297d07ad1ba5e43f1bca32301651339e22904cc8"
                   "c42f58c30c04aafdb038dda0847dd988dcda6f3bfd15c4b4c4525004aa06eeff"
                   "8ca61783aacec57fb3d1f92b0fe2fd1a85f6724517b65e614ad6808d6f6ee34d"
                   "ff7310fdc82aebfd904b01e1dc54b2927094b2db68d6f903b68401adebf5a7e0"
                   "8d78ff4ef5d63653a65040cf9bfd4aca7984a74d37145986780fc0b16ac45164"
                   "9de6188a7dbdf191f64b5fc5e2ab47b57f7f7276cd419c17a3ca8e1b939ae49e"
                   "488acba6b965610b5480109c8b17b80e1b7b750dfc7598d5d5011fd2dcc56009"
                   "a32ef5b52a1ecc820e308aa342721aac0943bf6686b64b2579376504ccc493d9"
                   "7e6aed3fb0f9cd71a43dd497f01f17c0e2cb3797aa2a2f256656168e6c496afc"
                   "5fb93246f6b1116398a346f1a641f3b041e989f7914f90cc2c7fff357876e506"
                   "b50d334ba77c225bc307ba537152f3f1610e4eafe595f6d9d90d11faa933a15e"
                   "f1369546868a7f3a45a96768d40fd9d03412c091c6315cf4fde7cb68606937380"
                   "db2eaaa707b4c4185c32eddcdd306705e4dc1ffc872eeee475a64dfac86aba41"
                   "c0618983f8741c5ef68d3a101e8a3b8cac60c905c15fc910840b94c00a0b9d0",
        "signature": "0aab4c900501b3e24d7cdf4663326a3a87df5e4843b2cbdb67cbf6e460fec350"
                     "aa5371b1508f9f4528ecea23c436d94b5e8fcd4f681e30a6ac00a9704a188a03",
    },
    {
        "name": "Vector 5 (SHA(abc))",
        "private": "833fe62409237b9d62ec77587520911e9a759cec1d19755b7da901b96dca3d42",
        "public":  "ec172b93ad5e563bf4932c70e1245034c35467ef2efd4d64ebf819683467e2bf",
        "message": "ddaf35a193617abacc417349ae20413112e6fa4e89a97ea20a9eeee64b55d39a"
                   "2192992a274fc1a836ba3c23a3feebbd454d4423643ce80e2a9ac94fa54ca49f",
        "signature": "dc2a4459e7369633a52b1bf277839a00201009a3efbf3ecb69bea2186c26b589"
                     "09351fc9ac90b3ecfdfbc7c66431e0303dca179c138ac17ad9bef1177331a704",
    },
]
```

### Key File Generation Pattern

```python
# Follows mg_sign.py generate_key() pattern
def generate_key_files(out_path: Path) -> dict:
    private_seed, public_key = generate_keypair()
    fingerprint = hashlib.sha256(public_key).hexdigest()

    key_data = {
        "version": KEY_VERSION,  # "ed25519-v1"
        "private_key_hex": private_seed.hex(),
        "public_key_hex": public_key.hex(),
        "fingerprint": fingerprint,
        "note": "KEEP THIS FILE SECRET. Share the .pub.json with auditors.",
    }

    pub_data = {
        "version": KEY_VERSION,
        "public_key_hex": public_key.hex(),
        "fingerprint": fingerprint,
        "note": "Public key for Ed25519 signature verification. Safe to share.",
    }

    # Write private key file
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(key_data, indent=2), encoding="utf-8")

    # Write public key file (companion)
    pub_path = out_path.with_suffix("").with_suffix(".pub.json")
    # If out_path is "key.json", pub_path is "key.pub.json"
    pub_path.write_text(json.dumps(pub_data, indent=2), encoding="utf-8")

    return key_data
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| HMAC-SHA256 symmetric signing | Ed25519 asymmetric signing | This phase (v0.4.0) | Third-party auditors verify without seeing private key |
| `cryptography` package for Ed25519 | Pure-Python Ed25519 (stdlib only) | Design decision for v0.4.0 | Zero dependencies; works on air-gapped systems |

**Not deprecated:**
- HMAC-SHA256 signing remains for backward compatibility with v0.3.0 bundles (Phase 2 handles dual-algorithm dispatch)

## Open Questions

1. **Point comparison normalization**
   - What we know: Extended coordinates use (X, Y, Z, T) where the actual point is (X/Z, Y/Z). Two representations of the same point may differ.
   - What's unclear: Whether to normalize to affine (X/Z mod P, Y/Z mod P) before comparison or use cross-multiplication.
   - Recommendation: Normalize to affine coordinates for the final equality check in verify. This is simpler and avoids subtle bugs. Performance is not a concern (one verification per bundle).

2. **Public key file naming convention**
   - What we know: CONTEXT.md says `key.pub.json` as companion to `key.json`.
   - What's unclear: If the user specifies `--out my_signing_key.json`, should the public file be `my_signing_key.pub.json`?
   - Recommendation: Yes -- strip `.json` suffix, append `.pub.json`. If the output path has no `.json` suffix, append `.pub.json` directly.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 8.4.1 |
| Config file | None in repo root (uses defaults) |
| Quick run command | `python -m pytest tests/steward/test_ed25519.py -x -q` |
| Full suite command | `python -m pytest tests/ -q` |

### Phase Requirements to Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SIGN-01 | Ed25519 passes all RFC 8032 test vectors | unit | `python scripts/mg_ed25519.py` (self-test) + `python -m pytest tests/steward/test_ed25519.py -x -q` | No -- Wave 0 |
| SIGN-01 | Key derivation: private seed produces correct public key | unit | `python -m pytest tests/steward/test_ed25519.py::TestEd25519Vectors -x` | No -- Wave 0 |
| SIGN-01 | Signing: correct signature for each test vector | unit | `python -m pytest tests/steward/test_ed25519.py::TestEd25519Vectors -x` | No -- Wave 0 |
| SIGN-01 | Verification: valid signatures verify True | unit | `python -m pytest tests/steward/test_ed25519.py::TestEd25519Vectors -x` | No -- Wave 0 |
| SIGN-01 | Verification: invalid signatures verify False | unit | `python -m pytest tests/steward/test_ed25519.py::TestEd25519Verify -x` | No -- Wave 0 |
| SIGN-02 | CLI keygen produces key file with correct format | unit | `python -m pytest tests/steward/test_ed25519.py::TestEd25519Keygen -x` | No -- Wave 0 |
| SIGN-02 | Generated key pair works for sign+verify round-trip | unit | `python -m pytest tests/steward/test_ed25519.py::TestEd25519Keygen -x` | No -- Wave 0 |
| SIGN-05 | keygen produces companion .pub.json file | unit | `python -m pytest tests/steward/test_ed25519.py::TestEd25519Keygen -x` | No -- Wave 0 |
| SIGN-05 | Public key file contains only public key (no private) | unit | `python -m pytest tests/steward/test_ed25519.py::TestEd25519Keygen -x` | No -- Wave 0 |
| REGR | All 295 existing tests still pass | regression | `python -m pytest tests/ -q` | Yes (existing) |

### Sampling Rate

- **Per task commit:** `python -m pytest tests/steward/test_ed25519.py -x -q` + `python scripts/mg_ed25519.py` (self-test)
- **Per wave merge:** `python -m pytest tests/ -q` (full 295+ suite)
- **Phase gate:** Full suite green + `python scripts/steward_audit.py` + `python scripts/deep_verify.py` before verify-work

### Wave 0 Gaps

- [ ] `tests/steward/test_ed25519.py` -- covers SIGN-01, SIGN-02, SIGN-05
- [ ] No framework install needed (pytest 8.4.1 already present)
- [ ] No conftest changes needed (new tests are self-contained)

## Sources

### Primary (HIGH confidence)
- RFC 8032 (rfc-editor.org) -- Ed25519 algorithm specification Section 5.1, test vectors Section 7.1 (fetched and extracted)
- `scripts/mg_sign.py` -- existing HMAC signing module (read directly, patterns documented)
- `tests/steward/test_cert07_bundle_signing.py` -- existing signing test patterns (read directly)
- `CLAUDE.md` -- project constraints, sealed files, verification gates (read directly)

### Secondary (MEDIUM confidence)
- `.planning/research/STACK.md` -- stack research (read directly, conducted 2026-03-16)
- `.planning/research/PITFALLS.md` -- pitfalls research (read directly, conducted 2026-03-16)

### Tertiary (LOW confidence)
- None -- all findings verified against RFC or codebase

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- stdlib-only, no version questions, Python 3.11 confirmed
- Architecture: HIGH -- module structure follows existing mg_sign.py pattern exactly; RFC 8032 algorithm is well-specified
- Pitfalls: HIGH -- Ed25519 implementation pitfalls are well-documented in RFC 8032 and cryptographic literature; clamping, point decoding, and modular sqrt are the known danger areas
- Test vectors: HIGH -- extracted directly from RFC 8032 via rfc-editor.org

**Research date:** 2026-03-17
**Valid until:** 2026-04-17 (stable domain; RFC 8032 is final, Python 3.11 stdlib is frozen)

---
*Phase: 01-ed25519-foundation*
*Research completed: 2026-03-17*
