#!/usr/bin/env python3
"""
MetaGenesis Core -- Ed25519 Signing (RFC 8032 Section 5.1)

Pure-Python, stdlib only. No external dependencies.

Implements key generation, signing, and verification for Ed25519 as specified
in RFC 8032 Section 5.1. All 5 test vectors from Section 7.1 are embedded
for self-test verification.

Usage:
    python scripts/mg_ed25519.py           # Run self-test (all 5 RFC 8032 vectors)
    python scripts/mg_ed25519.py test      # Same as above
"""

import argparse
import hashlib
import hmac as _hmac
import json
import secrets
import sys
from pathlib import Path

# ---- Ed25519 Constants (RFC 8032 Section 5.1) ----

P = 2**255 - 19  # Field prime
L = 2**252 + 27742317777372353535851937790883648493  # Group order
D = -121665 * pow(121666, P - 2, P) % P  # Curve parameter d
I = pow(2, (P - 1) // 4, P)  # sqrt(-1) mod P

KEY_VERSION = "ed25519-v1"


# ---- Field Arithmetic ----

def inv(x):
    """Modular inverse via Fermat's little theorem."""
    return pow(x, P - 2, P)


def recover_x(y, sign):
    """
    Recover x-coordinate from y-coordinate and sign bit.

    Uses the curve equation: -x^2 + y^2 = 1 + d*x^2*y^2
    Rearranged: x^2 = (y^2 - 1) / (d*y^2 + 1)
    """
    u = (y * y - 1) % P
    v = (D * y * y + 1) % P
    # Compute candidate x = (u/v)^((P+3)/8) mod P
    x = pow(u * inv(v), (P + 3) // 8, P)
    # Check and correct
    if (v * x * x - u) % P != 0:
        x = x * I % P
    if (v * x * x - u) % P != 0:
        raise ValueError("y is not on the curve")
    if x % 2 != sign:
        x = P - x
    return x


# ---- Base Point B ----

BY = 4 * pow(5, P - 2, P) % P  # y = 4/5 mod P
BX = recover_x(BY, 0)
B = (BX, BY, 1, BX * BY % P)  # Extended coordinates (x, y, z, t)

# Identity point (neutral element)
IDENT = (0, 1, 1, 0)


# ---- Edwards Curve Point Operations (Extended Coordinates) ----

def point_add(P1, P2):
    """Edwards curve point addition in extended coordinates (x, y, z, t)."""
    x1, y1, z1, t1 = P1
    x2, y2, z2, t2 = P2
    a = (y1 - x1) * (y2 - x2) % P
    b = (y1 + x1) * (y2 + x2) % P
    c = 2 * t1 * t2 * D % P
    d = 2 * z1 * z2 % P
    e = b - a
    f = d - c
    g = d + c
    h = b + a
    x3 = e * f % P
    y3 = g * h % P
    z3 = f * g % P
    t3 = e * h % P
    return (x3, y3, z3, t3)


def scalar_mult(s, pt):
    """Scalar multiplication using double-and-add."""
    result = IDENT
    current = pt
    s = s % L  # Reduce scalar modulo group order
    while s > 0:
        if s & 1:
            result = point_add(result, current)
        current = point_add(current, current)
        s >>= 1
    return result


# ---- Encoding/Decoding (RFC 8032) ----

def point_encode(pt):
    """Encode a point as 32 bytes (y-coordinate + x sign bit in MSB of byte 31)."""
    x, y, z, _t = pt
    zi = inv(z)
    xn = x * zi % P
    yn = y * zi % P
    encoded = yn.to_bytes(32, "little")
    # Set high bit of last byte to sign of x
    if xn & 1:
        encoded = bytearray(encoded)
        encoded[31] |= 0x80
        encoded = bytes(encoded)
    return encoded


def point_decode(s):
    """Decode 32 bytes to a point in extended coordinates."""
    if len(s) != 32:
        return None
    # Extract sign bit from byte 31 MSB
    sign_bit = (s[31] >> 7) & 1
    # Clear sign bit to get y
    y = int.from_bytes(s, "little") & ((1 << 255) - 1)
    if y >= P:
        return None
    try:
        x = recover_x(y, sign_bit)
    except ValueError:
        return None
    return (x, y, 1, x * y % P)


# ---- Key Generation (RFC 8032 Section 5.1.5) ----

def generate_keypair(private_seed=None):
    """
    Generate Ed25519 key pair.

    Args:
        private_seed: Optional 32-byte seed. If None, generates random.

    Returns:
        (private_seed_32bytes, public_key_32bytes)
    """
    if private_seed is None:
        private_seed = secrets.token_bytes(32)
    h = bytearray(hashlib.sha512(private_seed).digest())
    # Clamping (RFC 8032 Section 5.1.5)
    h[0] &= 248      # Clear lowest 3 bits
    h[31] &= 127     # Clear highest bit
    h[31] |= 64      # Set second highest bit
    scalar = int.from_bytes(bytes(h[:32]), "little")
    public_point = scalar_mult(scalar, B)
    public_key = point_encode(public_point)
    return private_seed, public_key


# ---- Sign (RFC 8032 Section 5.1.6) ----

def sign(private_seed, message):
    """
    Sign message with Ed25519 private seed.

    Args:
        private_seed: 32-byte private seed
        message: bytes to sign

    Returns:
        64-byte signature
    """
    h = hashlib.sha512(private_seed).digest()
    a_bytes = bytearray(h[:32])
    a_bytes[0] &= 248
    a_bytes[31] &= 127
    a_bytes[31] |= 64
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


# ---- Verify (RFC 8032 Section 5.1.7) ----

def verify(public_key, message, signature):
    """
    Verify Ed25519 signature.

    Uses cofactored verification: [8*S]B == [8]R + [8*k]A
    Final comparison uses constant-time hmac.compare_digest on encoded points.

    Args:
        public_key: 32-byte public key
        message: bytes that were signed
        signature: 64-byte signature

    Returns:
        True if valid, False otherwise
    """
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

    # Cofactored verification: [8*S]B == [8]R + [8*k]A
    lhs = scalar_mult(8 * S, B)
    rhs = point_add(scalar_mult(8, R), scalar_mult(8 * k, A))

    # Normalize to affine and use constant-time comparison
    lhs_encoded = point_encode(lhs)
    rhs_encoded = point_encode(rhs)
    return _hmac.compare_digest(lhs_encoded, rhs_encoded)


# ---- RFC 8032 Section 7.1 Test Vectors ----

TEST_VECTORS = [
    {
        "name": "Vector 1 (empty message)",
        "private": "9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60",
        "public": "d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a",
        "message": "",
        "signature": (
            "e5564300c360ac729086e2cc806e828a84877f1eb8e5d974d873e06522490155"
            "5fb8821590a33bacc61e39701cf9b46bd25bf5f0595bbe24655141438e7a100b"
        ),
    },
    {
        "name": "Vector 2 (1 byte)",
        "private": "4ccd089b28ff96da9db6c346ec114e0f5b8a319f35aba624da8cf6ed4fb8a6fb",
        "public": "3d4017c3e843895a92b70aa74d1b7ebc9c982ccf2ec4968cc0cd55f12af4660c",
        "message": "72",
        "signature": (
            "92a009a9f0d4cab8720e820b5f642540a2b27b5416503f8fb3762223ebdb69da"
            "085ac1e43e15996e458f3613d0f11d8c387b2eaeb4302aeeb00d291612bb0c00"
        ),
    },
    {
        "name": "Vector 3 (2 bytes)",
        "private": "c5aa8df43f9f837bedb7442f31dcb7b166d38535076f094b85ce3a2e0b4458f7",
        "public": "fc51cd8e6218a1a38da47ed00230f0580816ed13ba3303ac5deb911548908025",
        "message": "af82",
        "signature": (
            "6291d657deec24024827e69c3abe01a30ce548a284743a445e3680d7db5ac3ac"
            "18ff9b538d16f290ae67f760984dc6594a7c15e9716ed28dc027beceea1ec40a"
        ),
    },
    {
        "name": "Vector 4 (1023 bytes)",
        "private": "f5e5767cf153319517630f226876b86c8160cc583bc013744c6bf255f5cc0ee5",
        "public": "278117fc144c72340f67d0f2316e8386ceffbf2b2428c9c51fef7c597f1d426e",
        "message": (
            "08b8b2b733424243760fe426a4b54908632110a66c2f6591eabd3345e3e4eb98"
            "fa6e264bf09efe12ee50f8f54e9f77b1e355f6c50544e23fb1433ddf73be84d8"
            "79de7c0046dc4996d9e773f4bc9efe5738829adb26c81b37c93a1b270b20329d"
            "658675fc6ea534e0810a4432826bf58c941efb65d57a338bbd2e26640f89ffbc"
            "1a858efcb8550ee3a5e1998bd177e93a7363c344fe6b199ee5d02e82d522c4fe"
            "ba15452f80288a821a579116ec6dad2b3b310da903401aa62100ab5d1a36553e"
            "06203b33890cc9b832f79ef80560ccb9a39ce767967ed628c6ad573cb116dbef"
            "efd75499da96bd68a8a97b928a8bbc103b6621fcde2beca1231d206be6cd9ec7"
            "aff6f6c94fcd7204ed3455c68c83f4a41da4af2b74ef5c53f1d8ac70bdcb7ed1"
            "85ce81bd84359d44254d95629e9855a94a7c1958d1f8ada5d0532ed8a5aa3fb2"
            "d17ba70eb6248e594e1a2297acbbb39d502f1a8c6eb6f1ce22b3de1a1f40cc24"
            "554119a831a9aad6079cad88425de6bde1a9187ebb6092cf67bf2b13fd65f270"
            "88d78b7e883c8759d2c4f5c65adb7553878ad575f9fad878e80a0c9ba63bcbcc"
            "2732e69485bbc9c90bfbd62481d9089beccf80cfe2df16a2cf65bd92dd597b07"
            "07e0917af48bbb75fed413d238f5555a7a569d80c3414a8d0859dc65a46128ba"
            "b27af87a71314f318c782b23ebfe808b82b0ce26401d2e22f04d83d1255dc51a"
            "ddd3b75a2b1ae0784504df543af8969be3ea7082ff7fc9888c144da2af58429e"
            "c96031dbcad3dad9af0dcbaaaf268cb8fcffead94f3c7ca495e056a9b47acdb7"
            "51fb73e666c6c655ade8297297d07ad1ba5e43f1bca32301651339e22904cc8c"
            "42f58c30c04aafdb038dda0847dd988dcda6f3bfd15c4b4c4525004aa06eeff8"
            "ca61783aacec57fb3d1f92b0fe2fd1a85f6724517b65e614ad6808d6f6ee34df"
            "f7310fdc82aebfd904b01e1dc54b2927094b2db68d6f903b68401adebf5a7e08"
            "d78ff4ef5d63653a65040cf9bfd4aca7984a74d37145986780fc0b16ac451649"
            "de6188a7dbdf191f64b5fc5e2ab47b57f7f7276cd419c17a3ca8e1b939ae49e4"
            "88acba6b965610b5480109c8b17b80e1b7b750dfc7598d5d5011fd2dcc5600a3"
            "2ef5b52a1ecc820e308aa342721aac0943bf6686b64b2579376504ccc493d97e"
            "6aed3fb0f9cd71a43dd497f01f17c0e2cb3797aa2a2f256656168e6c496afc5f"
            "b93246f6b1116398a346f1a641f3b041e989f7914f90cc2c7fff357876e506b5"
            "0d334ba77c225bc307ba537152f3f1610e4eafe595f6d9d90d11faa933a15ef1"
            "369546868a7f3a45a96768d40fd9d03412c091c6315cf4fde7cb68606937380d"
            "b2eaaa707b4c4185c32eddcdd306705e4dc1ffc872eeee475a64dfac86aba41c"
            "0618983f8741c5ef68d3a101e8a3b8cac60c905c15fc910840b94c00a0b9d0"
        ),
        "signature": (
            "0aab4c900501b3e24d7cdf4663326a3a87df5e4843b2cbdb67cbf6e460fec350"
            "aa5371b1508f9f4528ecea23c436d94b5e8fcd4f681e30a6ac00a9704a188a03"
        ),
    },
    {
        "name": "Vector 5 (SHA(abc))",
        "private": "833fe62409237b9d62ec77587520911e9a759cec1d19755b7da901b96dca3d42",
        "public": "ec172b93ad5e563bf4932c70e1245034c35467ef2efd4d64ebf819683467e2bf",
        "message": (
            "ddaf35a193617abacc417349ae20413112e6fa4e89a97ea20a9eeee64b55d39a"
            "2192992a274fc1a836ba3c23a3feebbd454d4423643ce80e2a9ac94fa54ca49f"
        ),
        "signature": (
            "dc2a4459e7369633a52b1bf277839a00201009a3efbf3ecb69bea2186c26b589"
            "09351fc9ac90b3ecfdfbc7c66431e0303dca179c138ac17ad9bef1177331a704"
        ),
    },
]


# ---- Self-Test ----

def run_self_test():
    """
    Run all 5 RFC 8032 Section 7.1 test vectors.

    Returns:
        True if all vectors pass, False otherwise.
    """
    all_pass = True
    for vec in TEST_VECTORS:
        private_seed = bytes.fromhex(vec["private"])
        expected_pub = vec["public"]
        message = bytes.fromhex(vec["message"])
        expected_sig = vec["signature"]

        # Key derivation
        _, pub = generate_keypair(private_seed)
        if pub.hex() != expected_pub:
            print(f"  {vec['name']}:  FAIL (key derivation)")
            all_pass = False
            continue

        # Sign
        sig = sign(private_seed, message)
        if sig.hex() != expected_sig:
            print(f"  {vec['name']}:  FAIL (signature)")
            all_pass = False
            continue

        # Verify
        if not verify(pub, message, sig):
            print(f"  {vec['name']}:  FAIL (verification)")
            all_pass = False
            continue

        # Padding for alignment
        label = vec["name"] + ":"
        print(f"  {label:<30s} PASS")

    return all_pass


# ---- Key File Management ----

def generate_key_files(out_path):
    """
    Generate Ed25519 key pair and write to disk as two JSON files.

    Produces:
      - out_path: private key file (private_key_hex + public_key_hex + fingerprint)
      - out_path with .pub.json suffix: public key file (public_key_hex + fingerprint only)

    Args:
        out_path: Path to private key output file (e.g., key.json)

    Returns:
        dict with private key data (version, private_key_hex, public_key_hex, fingerprint, note)
    """
    out_path = Path(out_path)
    private_seed, public_key = generate_keypair()
    fingerprint = hashlib.sha256(public_key).hexdigest()

    key_data = {
        "version": KEY_VERSION,
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

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(key_data, indent=2), encoding="utf-8")

    # Companion public key file: key.json -> key.pub.json
    stem = out_path.stem  # "key" from "key.json"
    pub_path = out_path.parent / f"{stem}.pub.json"
    pub_path.write_text(json.dumps(pub_data, indent=2), encoding="utf-8")

    return key_data


# ---- CLI ----

def cmd_keygen(args):
    """CLI handler for keygen subcommand."""
    out_path = Path(args.out)
    key_data = generate_key_files(out_path)
    stem = out_path.stem
    pub_path = out_path.parent / f"{stem}.pub.json"
    print("Ed25519 key pair generated:")
    print(f"  Private key: {out_path}")
    print(f"  Public key:  {pub_path}")
    print(f"  Fingerprint: {key_data['fingerprint']}")
    print(f"KEEP {out_path} SECRET. Share {pub_path} with auditors.")
    return 0


def cmd_test(_args):
    """CLI handler for test subcommand."""
    print("Ed25519 Self-Test (RFC 8032 Section 7.1)")
    if run_self_test():
        print("\nALL 5 VECTORS PASSED")
        return 0
    else:
        print("\nSELF-TEST FAILED")
        return 1


def main():
    ap = argparse.ArgumentParser(
        description="MetaGenesis Core -- Ed25519 Signing (RFC 8032 Section 5.1)"
    )
    sub = ap.add_subparsers(dest="command")

    # keygen
    kg = sub.add_parser("keygen", help="Generate a new Ed25519 key pair")
    kg.add_argument("--out", "-o", required=True, help="Output key file path (.json)")
    kg.set_defaults(func=cmd_keygen)

    # test
    t = sub.add_parser("test", help="Run RFC 8032 self-test vectors")
    t.set_defaults(func=cmd_test)

    args = ap.parse_args()

    # Default to self-test if no subcommand (backward compatibility)
    if args.command is None:
        return cmd_test(args)

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
