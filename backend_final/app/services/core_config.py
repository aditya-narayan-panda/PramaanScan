"""
Core configuration helpers.
"""
import os


def get_key_encryption_secret() -> str | None:
    """Return the key encryption secret from environment, or None."""
    return os.environ.get("KEY_ENCRYPTION_SECRET") or None
