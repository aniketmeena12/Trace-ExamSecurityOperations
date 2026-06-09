"""Tamper-evident, append-only audit log (SHA-256 hash chain)."""

from .chain import GENESIS_HASH, record, verify_chain

__all__ = ["record", "verify_chain", "GENESIS_HASH"]
