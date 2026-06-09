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
| **M2** | Release-time gate, hash-chained audit log, JWT roles, FastAPI endpoints | ✅ done |
| M3 | DCT watermark embed/extract/trace + JPEG-robustness test | ⏳ |
| M4 | Frontend scaffold + 4 role dashboards wired to backend | ⏳ |
| M5 | Hero visuals: forensic leak-trace reveal + time-lock vault | ⏳ |
| M6 | Seed data, one-command demo script, README, architecture diagram | ⏳ |

## Setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run the demos

```bash
cd backend
python -m cli.crypto_demo   # M1: encrypt -> split -> 3-of-5 reconstruct, 2 blocked
python -m cli.api_demo      # M2: time gate holds 3 shares; release; audit tamper caught
```

`crypto_demo` is a real run: a paper is encrypted, the key is split into 5
custodian shares, **3 shares reconstruct the key and decrypt the paper**, and
**2 shares are mathematically blocked** — proven exhaustively across all subsets.

`api_demo` drives the actual FastAPI app in-process: three valid shares are
submitted but the **server-enforced time gate** keeps the vault sealed; a second
exam whose release time has passed unlocks and serves a candidate; then one
audit row is edited in the DB and the **SHA-256 hash chain detects the break**.

## Run the API server

```bash
cd backend
uvicorn trace.api.app:app --reload      # http://127.0.0.1:8000
# interactive docs at http://127.0.0.1:8000/docs
```

On first start the DB is created and demo accounts are seeded (passwords are
dev-only): `admin/admin123`, `investigator/invest123`, `cust1..cust5 /
custodian1..5`, `cand001/candidate1`.

### Key endpoints

| Method | Path | Role | Purpose |
|--------|------|------|---------|
| POST | `/auth/login` | any | OAuth2 password login → JWT |
| GET | `/auth/me` | any | current user |
| POST | `/exams` | admin | seal a paper (encrypt + Shamir-split the key) |
| GET | `/exams` · `/exams/{id}` | any | list / inspect exams |
| GET | `/exams/{id}/unlock/status` | any | live unlock progress (drives M5 vault UI) |
| POST | `/exams/{id}/shares/submit` | custodian | authorize release of one share |
| GET | `/exams/{id}/paper` | candidate/admin | read released paper (post-gate only) |
| GET | `/audit` | investigator/admin | the append-only event log |
| GET | `/audit/verify` | investigator/admin | recompute the hash chain → intact? |

## Run the tests

```bash
cd backend
pytest -v
```

Covers GF(256) field laws + AES vectors, Shamir 3-of-5 (every 3-subset
reconstructs, no 2-subset does), AES-256-GCM (roundtrip/tamper/AAD), the
hash-chained audit log (linkage + tamper detection), and the full API flow
(role enforcement, the time gate blocking 3 valid shares, legitimate unlock,
and candidate access).

## Security model & trust boundary (M2)

Trace defends against the two threats that cause real exam leaks:

- **A single malicious insider** — no one custodian (or pair) can open a paper:
  the key only exists after `k` distinct custodians authorize *and* the server
  reconstructs it via Shamir. The key is never stored whole.
- **Early opening** — the release-time gate is enforced server-side and is
  unconditional: even with every valid share present, decryption is refused
  until `release_time`.

In this single-node demo the server is the trusted enforcement point and holds
custodian shares in escrow (the released key is wrapped under a server secret so
a raw DB dump cannot decrypt a sealed paper). Hardening against a *fully
compromised server* — HSM-held or client-custodied shares — is called out as
future work rather than faked.

## Project layout

```
trace/
├── backend/
│   ├── trace/
│   │   ├── crypto/     gf256 · shamir · aes_gcm            ← M1 crypto core
│   │   ├── security/   passwords · tokens(JWT) · deps · keywrap
│   │   ├── audit/      chain.py  (SHA-256 hash chain)
│   │   ├── services/   exams.py  (seal · unlock ceremony · serve)
│   │   ├── api/        app.py + routers/ (auth · exams · audit)
│   │   ├── models.py · schemas.py · db.py · config.py · bootstrap.py
│   ├── tests/          gf256 · shamir · aes_gcm · audit_chain · api
│   └── cli/            crypto_demo.py · api_demo.py
├── sample_data/        sample_paper.txt
├── frontend/           (M4)
└── scripts/            (M6) run_demo.sh
```
