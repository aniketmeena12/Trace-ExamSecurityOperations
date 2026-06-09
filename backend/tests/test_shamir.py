"""Unit tests for Shamir's Secret Sharing over GF(256).

The headline guarantee for Trace: ANY 3 of 5 shares reconstruct the key, and
NO 2 shares ever do.
"""

import itertools

import pytest

from trace.crypto import shamir


def test_roundtrip_all_three_share_subsets():
    """Every one of the C(5,3)=10 triples must reconstruct the exact secret."""
    secret = b"AES-256 key material \x00\x01\x02\xff and then some"
    shares = shamir.split(secret, n=5, k=3)
    assert len(shares) == 5

    triples = list(itertools.combinations(shares, 3))
    assert len(triples) == 10
    for subset in triples:
        assert shamir.combine(list(subset)) == secret


def test_four_and_five_shares_also_reconstruct():
    secret = b"thirty-two-byte-key-padded__!!!!"
    assert len(secret) == 32
    shares = shamir.split(secret, n=5, k=3)
    for r in (4, 5):
        for subset in itertools.combinations(shares, r):
            assert shamir.combine(list(subset)) == secret


def test_two_shares_never_reconstruct_the_secret():
    """Below threshold: reconstruction must NOT return the real secret.

    With a degree-2 polynomial, 2 points define a *different* degree-1 curve;
    its value at x=0 equals the secret only with probability 256**-len(secret).
    For a 32-byte key that is ~10**-77 — never in practice.
    """
    secret = b"thirty-two-byte-key-padded__!!!!"
    shares = shamir.split(secret, n=5, k=3)
    for subset in itertools.combinations(shares, 2):
        assert shamir.combine(list(subset)) != secret


def test_single_share_does_not_leak_secret():
    secret = b"top-secret-exam-key-0123456789ab"
    shares = shamir.split(secret, n=5, k=3)
    for s in shares:
        assert shamir.combine([s]) != secret


def test_share_serialization_roundtrip():
    secret = b"\x00\xff\x10\x20hello world"
    shares = shamir.split(secret, n=5, k=3)
    rehydrated = [shamir.Share.from_hex(s.to_hex()) for s in shares]
    assert shamir.combine(rehydrated[:3]) == secret


def test_threshold_equals_n():
    secret = b"need-everyone"
    shares = shamir.split(secret, n=3, k=3)
    assert shamir.combine(shares) == secret
    for subset in itertools.combinations(shares, 2):
        assert shamir.combine(list(subset)) != secret


def test_single_byte_secret():
    for value in (0, 1, 127, 255):
        shares = shamir.split(bytes([value]), n=5, k=3)
        for subset in itertools.combinations(shares, 3):
            assert shamir.combine(list(subset)) == bytes([value])


@pytest.mark.parametrize(
    "n,k",
    [(5, 6), (0, 0), (256, 3), (5, 0)],
)
def test_invalid_parameters_raise(n, k):
    with pytest.raises(ValueError):
        shamir.split(b"x", n=n, k=k)


def test_empty_secret_raises():
    with pytest.raises(ValueError):
        shamir.split(b"", n=5, k=3)


def test_combine_rejects_duplicate_x():
    secret = b"abc"
    shares = shamir.split(secret, n=5, k=3)
    with pytest.raises(ValueError):
        shamir.combine([shares[0], shares[0], shares[1]])


def test_combine_rejects_mismatched_lengths():
    with pytest.raises(ValueError):
        shamir.combine([shamir.Share(1, b"\x01\x02"), shamir.Share(2, b"\x03")])
