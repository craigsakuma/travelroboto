"""
Helpers for handling sensitive values.

Provides a safe utility to unwrap Pydantic `SecretStr` only when a plain string
is required. No logging is performed.
"""

from pydantic import SecretStr


def secret_to_str(v: str | SecretStr | None) -> str | None:
    """Return the underlying string for a SecretStr, or None."""
    return v.get_secret_value() if isinstance(v, SecretStr) else v
