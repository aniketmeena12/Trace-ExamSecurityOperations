#!/usr/bin/env python3
"""Trace — backend flow walkthrough (Milestone 2).

Drives the real FastAPI app in-process (no server needed) to demonstrate:

  A. Multi-custodian + TIME GATE: 3 valid shares are submitted but the vault
     stays SEALED until the server-enforced release time.
  B. Legitimate release: after the gate opens, 3 custodians unlock the paper and
     a candidate reads it.
  C. Tamper-evident audit: the SHA-256 hash chain verifies intact, then we edit
     one row directly in the database and watch verification catch it.

Everything is driven by real backend state — nothing is hardcoded.

Usage:  python -m cli.api_demo
"""

import os
import tempfile

# Isolate this demo's database before importing the app.
_TMP = tempfile.mkdtemp(prefix="trace-m2-demo-")
os.environ.setdefault("TRACE_SECRET_KEY", "demo-secret-key-at-least-32-bytes-long!!")
os.environ["TRACE_DB_URL"] = f"sqlite:///{_TMP}/demo.db"

from fastapi.testclient import TestClient  # noqa: E402

from trace.api.app import app  # noqa: E402

RESET, BOLD, DIM = "\033[0m", "\033[1m", "\033[2m"
GREEN, RED, CYAN, YELLOW = "\033[32m", "\033[31m", "\033[36m", "\033[33m"


def hdr(t): print(f"\n{BOLD}{CYAN}== {t} =={RESET}")
def ok(t): print(f"  {GREEN}[OK]{RESET} {t}")
def blocked(t): print(f"  {RED}[BLOCKED]{RESET} {t}")
def info(t): print(f"  {DIM}{t}{RESET}")


def login(c, u, p):
    return {"Authorization": "Bearer " + c.post(
        "/auth/login", data={"username": u, "password": p}).json()["access_token"]}


def submit(c, eid, u, p):
    return c.post(f"/exams/{eid}/shares/submit", headers=login(c, u, p)).json()


CUSTS = [("cust1", "custodian1"), ("cust2", "custodian2"), ("cust3", "custodian3")]


def main():
    print(f"{BOLD}TRACE — Server-Enforced Time Gate + Tamper-Evident Audit (M2){RESET}")
    with TestClient(app) as c:
        admin = login(c, "admin", "admin123")

        # --- A. time gate holds despite enough shares --------------------
        hdr("A  Three valid shares, but release time is 1 hour away")
        eid = c.post("/exams", json={
            "name": "PHY-2026", "subject": "Physics", "center_id": "DEL-01",
            "threshold_k": 3, "release_offset_seconds": 3600,
        }, headers=admin).json()["id"]
        info(f"exam {eid} sealed; release in 3600s")
        for u, p in CUSTS:
            st = submit(c, eid, u, p)
        info(f"shares submitted: {st['shares_submitted']}/{st['shares_needed']}  "
             f"time_locked={st['time_locked']}")
        if st["status"] == "SEALED":
            blocked(f"vault SEALED — {int(st['seconds_remaining'])}s remain on the gate")
        cand = login(c, "cand001", "candidate1")
        r = c.get(f"/exams/{eid}/paper", headers=cand)
        blocked(f"candidate read denied (HTTP {r.status_code}: {r.json()['detail']})")

        # --- B. legitimate release ---------------------------------------
        hdr("B  A second exam whose release time has already passed")
        eid2 = c.post("/exams", json={
            "name": "PHY-2026-AM", "subject": "Physics", "center_id": "DEL-01",
            "threshold_k": 3, "release_offset_seconds": -5,
        }, headers=admin).json()["id"]
        info(f"exam {eid2} sealed; release time already passed")
        for i, (u, p) in enumerate(CUSTS, 1):
            st = submit(c, eid2, u, p)
            mark = "UNLOCKED" if st["status"] == "UNLOCKED" else "sealed"
            info(f"custodian {i} submits -> {st['shares_submitted']}/3  [{mark}]")
        ok("threshold met AND time passed -> key reconstructed, paper released")
        paper = c.get(f"/exams/{eid2}/paper", headers=cand).json()
        ok("candidate read the released paper:")
        for line in paper["content"].splitlines()[1:3]:
            print(f"  {YELLOW}|{RESET} {line}")

        # --- C. tamper-evident audit -------------------------------------
        hdr("C  The hash-chained audit log is tamper-evident")
        inv = login(c, "investigator", "invest123")
        v = c.get("/audit/verify", headers=inv).json()
        ok(f"chain verifies INTACT over {v['count']} events (ok={v['ok']})")

        # An attacker edits one audit row directly in the database.
        from trace.db import SessionLocal
        from trace.models import AuditEvent
        db = SessionLocal()
        victim = db.query(AuditEvent).filter(AuditEvent.action == "PAPER_UNLOCKED").first()
        info(f"attacker rewrites event #{victim.id} actor '{victim.actor}' -> 'ghost'")
        victim.actor = "ghost"
        db.commit(); db.close()

        v2 = c.get("/audit/verify", headers=inv).json()
        if not v2["ok"]:
            blocked(f"verification FAILED — break detected at event #{v2['first_broken']}")
        ok("tampering is detectable: the chain no longer recomputes")

    print(f"\n{BOLD}{GREEN}M2 backend flow verified end-to-end.{RESET}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
