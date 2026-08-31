from __future__ import annotations

import base64
from typing import Tuple

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)


# ============================================================
# KEY GENERATION
# ============================================================

def generate_key_pair() -> Tuple[str, str]:
    """
    Generate an Ed25519 private/public key pair.

    Returns:
        private_key_b64:
            Base64 encoded raw private key bytes.

        public_key_b64:
            Base64 encoded raw public key bytes.
    """

    private_key = Ed25519PrivateKey.generate()

    public_key = private_key.public_key()

    private_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )

    public_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )

    private_key_b64 = base64.b64encode(
        private_bytes
    ).decode("ascii")

    public_key_b64 = base64.b64encode(
        public_bytes
    ).decode("ascii")

    return private_key_b64, public_key_b64


# ============================================================
# SIGN DATA
# ============================================================

def sign_data(
    data: bytes,
    private_key_b64: str,
) -> str:
    """
    Sign arbitrary bytes using an Ed25519 private key.

    Returns:
        Base64 encoded digital signature.
    """

    private_bytes = base64.b64decode(
        private_key_b64
    )

    private_key = Ed25519PrivateKey.from_private_bytes(
        private_bytes
    )

    signature = private_key.sign(data)

    return base64.b64encode(
        signature
    ).decode("ascii")


# ============================================================
# VERIFY SIGNATURE
# ============================================================

def verify_signature(
    data: bytes,
    signature_b64: str,
    public_key_b64: str,
) -> bool:
    """
    Verify an Ed25519 signature.

    Returns:
        True  -> signature is valid
        False -> signature is invalid
    """

    try:

        public_bytes = base64.b64decode(
            public_key_b64
        )

        signature = base64.b64decode(
            signature_b64
        )

        public_key = Ed25519PublicKey.from_public_bytes(
            public_bytes
        )

        public_key.verify(
            signature,
            data
        )

        return True

    except (
        InvalidSignature,
        ValueError,
        TypeError,
    ):

        return False


# ============================================================
# KEY VALIDATION
# ============================================================

def validate_private_key(
    private_key_b64: str,
) -> bool:
    """
    Check whether a Base64 encoded Ed25519 private key
    is structurally valid.
    """

    try:

        private_bytes = base64.b64decode(
            private_key_b64
        )

        Ed25519PrivateKey.from_private_bytes(
            private_bytes
        )

        return True

    except (
        ValueError,
        TypeError,
    ):

        return False


def validate_public_key(
    public_key_b64: str,
) -> bool:
    """
    Check whether a Base64 encoded Ed25519 public key
    is structurally valid.
    """

    try:

        public_bytes = base64.b64decode(
            public_key_b64
        )

        Ed25519PublicKey.from_public_bytes(
            public_bytes
        )

        return True

    except (
        ValueError,
        TypeError,
    ):

        return False