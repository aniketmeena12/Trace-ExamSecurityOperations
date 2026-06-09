# Trace — Leak-Proof, Traceable Exam Papers

> India's FAR AWAY 2026 · Theme: secure, leak-proof examinations

Exam paper leaks are a recurring, high-impact failure of trust: a single insider
with early access can compromise an entire exam for millions of candidates.
**Trace** makes a paper *impossible to open before the exam* and *traceable to its
exact source if it ever leaks* — backed by three real security guarantees, not
slideware.

## The three guarantees

1. **Just-in-time, multi-custodian decryption.**
   The paper is encrypted with **AES-256-GCM**. The key is never stored whole —
   it is split with **Shamir's Secret Sharing (3-of-5)** across independent
   custodians, *plus* a server-enforced release time. No single insider (and no
   pair) can open it, and nobody can open it before exam start.

2. **Per-candidate invisible watermarking.**
   Each rendered copy carries an invisible **DCT-domain fingerprint** encoding
   center ID + candidate ID. Any leaked image traces back to its exact source.

3. **Tamper-evident audit log.**
   An append-only **SHA-256 hash-chained** log of every access event. Altering
   any entry breaks the chain and is detectable.

## Architecture (target)

```
            custodians (3-of-5 shares)        server release-time gate
                       \                      /
   exam paper ──AES-256-GCM──► encrypted vault ──► JIT decrypt ──► render
                                     │                                │
                                     ▼                       per-candidate DCT
                            hash-chained audit log              watermark
                                                                    │
                                                  leaked image ──► forensic trace
```

- **Backend:** Python · FastAPI · SQLite (SQLAlchemy) · JWT (admin / custodian /
  candidate / investigator roles)
- **Crypto:** `pycryptodome` for AES-GCM; **Shamir implemented from scratch over
  GF(256)** with unit tests (depth over black boxes)
- **Watermarking:** OpenCV + numpy (DCT) + Pillow
- **Frontend:** React · Vite · Tailwind · Framer Motion · react-simple-maps —
  dark "security operations / mission-control" theme. All animations are driven
  by **real backend events**.

## Build status

| Milestone | Scope | Status |
|-----------|-------|--------|
| **M1** | Repo scaffold + crypto core (AES-256-GCM, Shamir 3-of-5, tests, CLI) | ✅ done |
| M2 | Release-time gate, hash-chained audit log, JWT roles, FastAPI endpoints | ⏳ |
| M3 | DCT watermark embed/extract/trace + JPEG-robustness test | ⏳ |
| M4 | Frontend scaffold + 4 role dashboards wired to backend | ⏳ |
| M5 | Hero visuals: forensic leak-trace reveal + time-lock vault | ⏳ |
| M6 | Seed data, one-command demo script, README, architecture diagram | ⏳ |

## Setup (M1)

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run the crypto core demo

```bash
cd backend
python -m cli.crypto_demo
```

You will watch a real run: a paper is encrypted, the key is split into 5
custodian shares, **3 shares reconstruct the key and decrypt the paper**, and
**2 shares are mathematically blocked** — proven exhaustively across all subsets.

## Run the tests

```bash
cd backend
pytest -v
```

Covers GF(256) field laws (associativity, distributivity, inverses, AES test
vectors), Shamir 3-of-5 (every 3-subset reconstructs, no 2-subset does), and
AES-256-GCM (roundtrip, tamper rejection, AAD binding, full key-split flow).

## Project layout

```
trace/
├── backend/
│   ├── trace/crypto/   gf256.py · shamir.py · aes_gcm.py   ← crypto core
│   ├── tests/          test_gf256 · test_shamir · test_aes_gcm
│   └── cli/            crypto_demo.py
├── sample_data/        sample_paper.txt
├── frontend/           (M4)
└── scripts/            (M6) run_demo.sh
```
