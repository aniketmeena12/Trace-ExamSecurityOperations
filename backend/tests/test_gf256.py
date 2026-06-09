"""Unit tests for GF(256) field arithmetic.

These verify the field laws the secret-sharing math depends on. If any of these
fail, Shamir reconstruction cannot be trusted.
"""

import pytest

from trace.crypto import gf256


def test_tables_are_complete_and_bijective():
    # Every nonzero element appears exactly once as an exponent (1..254 -> log).
    seen = {gf256.EXP[i] for i in range(255)}
    assert seen == set(range(1, 256))  # all 255 nonzero elements, no repeats
    # log and exp are inverses on the nonzero elements.
    for a in range(1, 256):
        assert gf256.EXP[gf256.LOG[a]] == a


def test_addition_is_xor_and_self_inverse():
    for a in range(256):
        assert gf256.add(a, a) == 0           # a + a == 0 (char 2)
        for b in (0, 1, 17, 200, 255):
            assert gf256.add(a, b) == a ^ b


def test_multiplicative_identity_and_zero():
    for a in range(256):
        assert gf256.mul(a, 1) == a
        assert gf256.mul(a, 0) == 0
        assert gf256.mul(0, a) == 0


def test_multiplication_is_commutative():
    for a in (0, 1, 2, 53, 127, 255):
        for b in (0, 1, 7, 99, 200, 255):
            assert gf256.mul(a, b) == gf256.mul(b, a)


def test_multiplication_is_associative_and_distributive():
    sample = (1, 2, 3, 17, 53, 128, 200, 255)
    for a in sample:
        for b in sample:
            for c in sample:
                assert gf256.mul(gf256.mul(a, b), c) == gf256.mul(a, gf256.mul(b, c))
                assert gf256.mul(a, gf256.add(b, c)) == gf256.add(
                    gf256.mul(a, b), gf256.mul(a, c)
                )


def test_inverse_and_division():
    for a in range(1, 256):
        inv = gf256.inverse(a)
        assert gf256.mul(a, inv) == 1
        assert gf256.div(a, a) == 1
    for a in range(256):
        for b in (1, 2, 99, 255):
            # (a / b) * b == a
            assert gf256.mul(gf256.div(a, b), b) == a


def test_known_answer_xtime():
    # Classic AES test vector: 0x57 * 0x13 == 0xFE in GF(2^8)/0x11B.
    assert gf256.mul(0x57, 0x13) == 0xFE
    # 0x57 * 0x02 (xtime) == 0xAE.
    assert gf256.mul(0x57, 0x02) == 0xAE


def test_division_by_zero_raises():
    with pytest.raises(ZeroDivisionError):
        gf256.div(1, 0)
    with pytest.raises(ZeroDivisionError):
        gf256.inverse(0)
