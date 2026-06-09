"""GF(2^8) finite-field arithmetic for Shamir's Secret Sharing.

The field is GF(256) defined by the AES irreducible polynomial
    x^8 + x^4 + x^3 + x + 1   (0x11B).

We precompute exponential/logarithm tables using the generator 0x03, which is
a primitive element of this field. With those tables, multiplication and
inversion become O(1) lookups instead of bit-by-bit loops.

Why from scratch (and not a library): Shamir's scheme is only as trustworthy as
the field it runs over. Implementing and unit-testing the field ourselves means
every algebraic law the secret-sharing math relies on (associativity,
distributivity, inverses) is demonstrably true in *this* code, not assumed.

In a characteristic-2 field:
  * addition and subtraction are both XOR,
  * the additive identity is 0 and additive inverse of a is a itself.
"""

AES_POLY = 0x11B  # x^8 + x^4 + x^3 + x + 1
GENERATOR = 0x03  # primitive element used to seed the log/exp tables


def _mul_bootstrap(a: int, b: int) -> int:
    """Multiply two field elements via Russian-peasant + reduction.

    Used only to build the exp/log tables. This is the slow, obviously-correct
    reference; the rest of the module relies on the tables it produces.
    """
    product = 0
    for _ in range(8):
        if b & 1:
            product ^= a
        high_bit_set = a & 0x80
        a = (a << 1) & 0xFF
        if high_bit_set:
            a ^= (AES_POLY & 0xFF)  # subtract x^8 term: 0x11B mod 2^8 == 0x1B
        b >>= 1
    return product


def _build_tables():
    exp = [0] * 512  # doubled so exp[i + j] never needs a modulo
    log = [0] * 256
    x = 1
    for i in range(255):
        exp[i] = x
        log[x] = i
        x = _mul_bootstrap(x, GENERATOR)
    # The cycle length is 255; mirror it so indices up to 510 are valid.
    for i in range(255, 512):
        exp[i] = exp[i - 255]
    return exp, log


EXP, LOG = _build_tables()


def add(a: int, b: int) -> int:
    """Field addition (== subtraction) in characteristic 2."""
    return a ^ b


def mul(a: int, b: int) -> int:
    """Field multiplication via log/exp tables."""
    if a == 0 or b == 0:
        return 0
    return EXP[LOG[a] + LOG[b]]


def div(a: int, b: int) -> int:
    """Field division a / b."""
    if b == 0:
        raise ZeroDivisionError("division by zero in GF(256)")
    if a == 0:
        return 0
    # LOG[a] - LOG[b] taken mod 255; + 255 keeps the index in [1, 509].
    return EXP[LOG[a] - LOG[b] + 255]


def inverse(a: int) -> int:
    """Multiplicative inverse of a (a != 0)."""
    if a == 0:
        raise ZeroDivisionError("0 has no inverse in GF(256)")
    return EXP[255 - LOG[a]]
