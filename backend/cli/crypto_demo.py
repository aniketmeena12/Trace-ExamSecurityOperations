#!/usr/bin/env python3
"""Trace — crypto core walkthrough (Milestone 1).

Runs the real end-to-end guarantee with live output so a human (or judge) can
watch it happen:

  1. Generate a 256-bit AES key.
  2. Encrypt a sample exam paper with AES-256-GCM.
  3. Split the key into 5 custodian shares (3-of-5 Shamir).
  4. Reconstruct with 3 shares  -> key matches  -> paper decrypts.
  5. Attempt with only 2 shares  -> wrong key   -> decryption REJECTED.

Nothing here is faked: step 4 succeeds because the shares algebraically rebuild
the key, and step 5 fails because they mathematically cannot.

Usage:
    python -m cli.crypto_demo [path/to/paper.txt]
"""

import itertools
import sys
from pathlib import Path

from trace.crypto import aes_gcm, shamir

# ---- tiny ANSI helpers (no dependencies) ---------------------------------
RESET, BOLD, DIM = "\033[0m", "\033[1m", "\033[2m"
GREEN, RED, CYAN, YELLOW = "\033[32m", "\033[31m", "\033[36m", "\033[33m"


def hdr(text):
    print(f"\n{BOLD}{CYAN}== {text} =={RESET}")


def ok(text):
    print(f"  {GREEN}[OK]{RESET} {text}")


def fail_expected(text):
    print(f"  {RED}[BLOCKED]{RESET} {text}")


def info(text):
    print(f"  {DIM}{text}{RESET}")


AAD = b"center=DEL-01;exam=PHY-2026;session=AM"


def main(argv):
    paper_path = Path(argv[1]) if len(argv) > 1 else (
        Path(__file__).resolve().parents[2] / "sample_data" / "sample_paper.txt"
    )
    paper = paper_path.read_bytes()

    print(f"{BOLD}TRACE — Just-in-Time Multi-Custodian Decryption (crypto core){RESET}")
    info(f"paper: {paper_path}  ({len(paper)} bytes)")
    info(f"bound context (AAD): {AAD.decode()}")

    # 1. Key + 2. encrypt
    hdr("1-2  Encrypt the paper under a fresh AES-256-GCM key")
    key = aes_gcm.generate_key()
    ct = aes_gcm.encrypt(paper, key, aad=AAD)
    ok(f"key generated: {len(key)*8}-bit  ({key.hex()[:16]}… kept secret)")
    ok(f"ciphertext: {len(ct.serialize())} bytes  (nonce {len(ct.nonce)}B + tag "
       f"{len(ct.tag)}B + body)")

    # 3. Split
    hdr("3    Split the key across 5 custodians (3-of-5 Shamir / GF(256))")
    shares = shamir.split(key, n=5, k=3)
    for i, s in enumerate(shares, 1):
        info(f"custodian {i}: share = {s.to_hex()[:22]}…")
    ok("no custodian holds the key — only a point on a secret polynomial")

    # 4. Reconstruct with 3 -> decrypt
    hdr("4    Three custodians (1, 3, 5) combine their shares")
    chosen = [shares[0], shares[2], shares[4]]
    recovered = shamir.combine(chosen)
    assert recovered == key, "reconstruction must match the original key"
    ok("reconstructed key MATCHES the original")
    plaintext = aes_gcm.decrypt(ct, recovered, aad=AAD)
    ok("paper DECRYPTED and authenticated")
    print(f"\n{DIM}  --- first lines of recovered paper ---{RESET}")
    for line in plaintext.decode(errors="replace").splitlines()[:4]:
        print(f"  {YELLOW}|{RESET} {line}")

    # 5. Attempt with 2 -> blocked
    hdr("5    Only two custodians (1, 2) try to open it early")
    wrong = shamir.combine([shares[0], shares[1]])
    ok("2 shares produce *a* key, but it is NOT the real key" if wrong != key
       else "UNEXPECTED: 2 shares matched (astronomically unlikely)")
    try:
        aes_gcm.decrypt(ct, wrong, aad=AAD)
        print(f"  {RED}[ERROR]{RESET} decryption unexpectedly succeeded!")
        return 1
    except ValueError:
        fail_expected("GCM authentication failed — paper stays sealed")

    # Exhaustive proof across all subsets
    hdr("Proof  every 3-subset opens it, every 2-subset is blocked")
    three_ok = sum(
        shamir.combine(list(c)) == key for c in itertools.combinations(shares, 3)
    )
    two_blocked = sum(
        shamir.combine(list(c)) != key for c in itertools.combinations(shares, 2)
    )
    ok(f"3-of-5 subsets that reconstruct the key: {three_ok}/10")
    ok(f"2-of-5 subsets that are blocked:         {two_blocked}/10")

    print(f"\n{BOLD}{GREEN}Crypto core verified end-to-end.{RESET}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
