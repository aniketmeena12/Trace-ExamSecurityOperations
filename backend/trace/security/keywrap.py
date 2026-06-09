"""Wrap/unwrap a paper's AES key under the server wrapping key.

Reuses the M1 AES-256-GCM core. Used only AFTER a legitimate, time-gated unlock,
so candidates can be served the released paper without ever persisting the raw
key. Before release, no wrapped key exists — so even the server cannot decrypt.
"""

from ..config import settings
from ..crypto import aes_gcm


def wrap_key(key: bytes) -> bytes:
    ct = aes_gcm.encrypt(key, settings.server_wrap_key())
    return ct.serialize()


def unwrap_key(blob: bytes) -> bytes:
    return aes_gcm.decrypt(aes_gcm.Ciphertext.deserialize(blob), settings.server_wrap_key())
