"""
Ed25519 correctness tests -- RFC 8032 Section 7.1 test vectors.

Tests key derivation, signing, and verification against all 5 official
test vectors. Also tests rejection of invalid signatures.
"""

import pytest

from scripts.mg_ed25519 import sign, verify, generate_keypair, run_self_test


# All 5 RFC 8032 Section 7.1 test vectors
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
            "c0618983f8741c5ef68d3a101e8a3b8cac60c905c15fc910840b94c00a0b9d0"
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


class TestEd25519Vectors:
    """Parameterized tests over all 5 RFC 8032 Section 7.1 vectors."""

    @pytest.mark.parametrize("vec", TEST_VECTORS, ids=[v["name"] for v in TEST_VECTORS])
    def test_key_derivation(self, vec):
        """Private seed produces expected public key."""
        private_seed = bytes.fromhex(vec["private"])
        _, public_key = generate_keypair(private_seed)
        assert public_key.hex() == vec["public"], (
            f"Key derivation mismatch for {vec['name']}"
        )

    @pytest.mark.parametrize("vec", TEST_VECTORS, ids=[v["name"] for v in TEST_VECTORS])
    def test_sign(self, vec):
        """Signing produces expected signature."""
        private_seed = bytes.fromhex(vec["private"])
        message = bytes.fromhex(vec["message"])
        sig = sign(private_seed, message)
        assert sig.hex() == vec["signature"], (
            f"Signature mismatch for {vec['name']}"
        )

    @pytest.mark.parametrize("vec", TEST_VECTORS, ids=[v["name"] for v in TEST_VECTORS])
    def test_verify_valid(self, vec):
        """Valid signature verifies True."""
        public_key = bytes.fromhex(vec["public"])
        message = bytes.fromhex(vec["message"])
        signature = bytes.fromhex(vec["signature"])
        assert verify(public_key, message, signature) is True

    @pytest.mark.parametrize("vec", TEST_VECTORS, ids=[v["name"] for v in TEST_VECTORS])
    def test_verify_tampered_signature(self, vec):
        """Flipping one byte of signature causes rejection."""
        public_key = bytes.fromhex(vec["public"])
        message = bytes.fromhex(vec["message"])
        sig_bytes = bytearray(bytes.fromhex(vec["signature"]))
        sig_bytes[0] ^= 0x01  # Flip one bit in first byte
        assert verify(public_key, message, bytes(sig_bytes)) is False

    @pytest.mark.parametrize("vec", TEST_VECTORS, ids=[v["name"] for v in TEST_VECTORS])
    def test_verify_wrong_message(self, vec):
        """Altered message causes rejection."""
        public_key = bytes.fromhex(vec["public"])
        message = bytes.fromhex(vec["message"]) + b"\x00"
        signature = bytes.fromhex(vec["signature"])
        assert verify(public_key, message, signature) is False

    @pytest.mark.parametrize("vec", TEST_VECTORS, ids=[v["name"] for v in TEST_VECTORS])
    def test_verify_wrong_public_key(self, vec):
        """Wrong public key causes rejection."""
        # Use a different vector's public key
        other_idx = (TEST_VECTORS.index(vec) + 1) % len(TEST_VECTORS)
        wrong_key = bytes.fromhex(TEST_VECTORS[other_idx]["public"])
        message = bytes.fromhex(vec["message"])
        signature = bytes.fromhex(vec["signature"])
        assert verify(wrong_key, message, signature) is False


class TestEd25519SelfTest:
    """Test the self-test mode."""

    def test_self_test_passes(self):
        """run_self_test() returns True when all vectors pass."""
        assert run_self_test() is True
