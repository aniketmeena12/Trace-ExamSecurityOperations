"""Unit tests for AES-256-GCM encryption and the Shamir-key integration."""

import itertools
import os

import pytest

from trace.crypto import aes_gcm, shamir


def test_encrypt_decrypt_roundtrip():
    key = aes_gcm.generate_key()
    plaintext = b"EXAM PAPER: Q1. Prove the field GF(256) has 255 nonzero units."
    ct = aes_gcm.encrypt(plaintext, key)
    assert aes_gcm.decrypt(ct, key) == plaintext


def test_key_is_256_bits():
    assert len(aes_gcm.generate_key()) == 32


def test_wrong_key_fails_authentication():
    key = aes_gcm.generate_key()
    ct = aes_gcm.encrypt(b"secret paper", key)
    with pytest.raises(ValueError):
        aes_gcm.decrypt(ct, aes_gcm.generate_key())


def test_tampered_ciphertext_is_rejected():
    key = aes_gcm.generate_key()
    ct = aes_gcm.encrypt(b"original exam content", key)
    flipped = bytearray(ct.data)
    flipped[0] ^= 0x01
    tampered = aes_gcm.Ciphertext(ct.nonce, ct.tag, bytes(flipped))
    with pytest.raises(ValueError):
        aes_gcm.decrypt(tampered, key)


def test_aad_binding():
    key = aes_gcm.generate_key()
    ct = aes_gcm.encrypt(b"paper body", key, aad=b"paper_id=42")
    assert aes_gcm.decrypt(ct, key, aad=b"paper_id=42") == b"paper body"
    with pytest.raises(ValueError):
        aes_gcm.decrypt(ct, key, aad=b"paper_id=99")  # mismatched context


def test_serialize_deserialize_roundtrip():
    key = aes_gcm.generate_key()
    ct = aes_gcm.encrypt(b"some bytes here", key)
    blob = ct.serialize()
    assert aes_gcm.decrypt(aes_gcm.Ciphertext.deserialize(blob), key) == b"some bytes here"


def test_rejects_non_256_bit_key():
    with pytest.raises(ValueError):
        aes_gcm.encrypt(b"x", os.urandom(16))  # AES-128 key not allowed


def test_full_flow_key_split_then_reconstruct_then_decrypt():
    """End-to-end: encrypt with a key, split the key 3-of-5, and prove that
    3 custodians can decrypt the paper while 2 cannot."""
    key = aes_gcm.generate_key()
    paper = b"CONFIDENTIAL EXAM PAPER \x00\x01\x02 ... 100 marks."
    ct = aes_gcm.encrypt(paper, key, aad=b"center=DEL-01;exam=PHY-2026")

    shares = shamir.split(key, n=5, k=3)

    # Any 3 custodians -> correct key -> successful decrypt.
    for subset in itertools.combinations(shares, 3):
        recovered_key = shamir.combine(list(subset))
        assert recovered_key == key
        assert aes_gcm.decrypt(ct, recovered_key, aad=b"center=DEL-01;exam=PHY-2026") == paper

    # Any 2 custodians -> wrong key -> authentication failure (no plaintext).
    for subset in itertools.combinations(shares, 2):
        wrong_key = shamir.combine(list(subset))
        assert wrong_key != key
        with pytest.raises(ValueError):
            aes_gcm.decrypt(ct, wrong_key, aad=b"center=DEL-01;exam=PHY-2026")


def test_file_encrypt_decrypt(tmp_path):
    key = aes_gcm.generate_key()
    src = tmp_path / "paper.txt"
    enc = tmp_path / "paper.enc"
    dec = tmp_path / "paper.out"
    src.write_bytes(b"exam paper file contents, multiple lines\nQ1...\nQ2...\n")

    aes_gcm.encrypt_file(str(src), str(enc), key)
    aes_gcm.decrypt_file(str(enc), str(dec), key)
    assert dec.read_bytes() == src.read_bytes()
