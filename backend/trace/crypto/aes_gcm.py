"""AES-256-GCM authenticated encryption for exam paper files.

GCM gives us confidentiality *and* integrity in one pass: decryption verifies a
128-bit authentication tag, so any tampering with the ciphertext (or with the
associated data, e.g. the paper/exam identifiers) is detected and rejected
rather than silently producing garbage plaintext.

The 256-bit key produced here is exactly what Trace hands to Shamir's Secret
Sharing — it is never stored whole anywhere.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from Crypto.Cipher import AES

KEY_LEN = 32    # AES-256
NONCE_LEN = 12  # 96-bit nonce, the GCM-recommended size
TAG_LEN = 16    # 128-bit authentication tag


@dataclass(frozen=True)
class Ciphertext:
    """An encrypted blob: nonce + auth tag + ciphertext bytes."""

    nonce: bytes
    tag: bytes
    data: bytes

    def serialize(self) -> bytes:
        """Pack as nonce || tag || data for storage on disk."""
        return self.nonce + self.tag + self.data

    @classmethod
    def deserialize(cls, blob: bytes) -> "Ciphertext":
        if len(blob) < NONCE_LEN + TAG_LEN:
            raise ValueError("blob too short to be a valid ciphertext")
        nonce = blob[:NONCE_LEN]
        tag = blob[NONCE_LEN:NONCE_LEN + TAG_LEN]
        data = blob[NONCE_LEN + TAG_LEN:]
        return cls(nonce, tag, data)


def generate_key() -> bytes:
    """Return a fresh random 256-bit key."""
    return os.urandom(KEY_LEN)


def encrypt(plaintext: bytes, key: bytes, aad: bytes = b"") -> Ciphertext:
    """Encrypt ``plaintext`` under ``key`` with optional associated data."""
    if len(key) != KEY_LEN:
        raise ValueError(f"AES-256 requires a {KEY_LEN}-byte key")
    nonce = os.urandom(NONCE_LEN)
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    if aad:
        cipher.update(aad)
    data, tag = cipher.encrypt_and_digest(plaintext)
    return Ciphertext(nonce=nonce, tag=tag, data=data)


def decrypt(ct: Ciphertext, key: bytes, aad: bytes = b"") -> bytes:
    """Decrypt and verify. Raises ValueError if the tag/AAD doesn't check out."""
    if len(key) != KEY_LEN:
        raise ValueError(f"AES-256 requires a {KEY_LEN}-byte key")
    cipher = AES.new(key, AES.MODE_GCM, nonce=ct.nonce)
    if aad:
        cipher.update(aad)
    # decrypt_and_verify raises ValueError on a bad tag — i.e. on tampering.
    return cipher.decrypt_and_verify(ct.data, ct.tag)


def encrypt_file(in_path: str, out_path: str, key: bytes, aad: bytes = b"") -> Ciphertext:
    with open(in_path, "rb") as f:
        plaintext = f.read()
    ct = encrypt(plaintext, key, aad)
    with open(out_path, "wb") as f:
        f.write(ct.serialize())
    return ct


def decrypt_file(in_path: str, out_path: str, key: bytes, aad: bytes = b"") -> bytes:
    with open(in_path, "rb") as f:
        blob = f.read()
    plaintext = decrypt(Ciphertext.deserialize(blob), key, aad)
    with open(out_path, "wb") as f:
        f.write(plaintext)
    return plaintext
