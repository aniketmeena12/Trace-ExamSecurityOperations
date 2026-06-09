"""Integration tests for the full M2 flow over the FastAPI app."""

from tests.conftest import auth, login


def _create_exam(client, admin_tok, **overrides):
    body = {
        "name": "PHY-2026",
        "subject": "Physics",
        "center_id": "DEL-01",
        "threshold_k": 3,
        "release_offset_seconds": -10,  # already releasable by default
    }
    body.update(overrides)
    r = client.post("/exams", json=body, headers=auth(admin_tok))
    assert r.status_code == 201, r.text
    return r.json()


# ---- auth / roles --------------------------------------------------------
def test_health(client):
    assert client.get("/health").json()["status"] == "ok"


def test_login_and_me(client):
    tok = login(client, "admin", "admin123")
    r = client.get("/auth/me", headers=auth(tok))
    assert r.json()["role"] == "admin"


def test_login_bad_password(client):
    r = client.post("/auth/login", data={"username": "admin", "password": "nope"})
    assert r.status_code == 401


def test_candidate_cannot_create_exam(client):
    tok = login(client, "cand001", "candidate1")
    r = client.post(
        "/exams",
        json={
            "name": "X",
            "subject": "Y",
            "center_id": "C",
            "threshold_k": 3,
            "release_offset_seconds": -10,
        },
        headers=auth(tok),
    )
    assert r.status_code == 403


def test_unauthenticated_is_rejected(client):
    assert client.get("/exams").status_code == 401


# ---- full unlock flow ----------------------------------------------------
def test_three_custodians_unlock_then_candidate_reads(client):
    admin = login(client, "admin", "admin123")
    exam = _create_exam(client, admin)
    eid = exam["id"]
    assert exam["status"] == "SEALED"

    # Two custodians submit -> below threshold, still sealed.
    for u, p in [("cust1", "custodian1"), ("cust2", "custodian2")]:
        s = client.post(f"/exams/{eid}/shares/submit", headers=auth(login(client, u, p)))
        assert s.status_code == 200, s.text
        assert s.json()["status"] == "SEALED"
    assert client.get(f"/exams/{eid}/unlock/status", headers=auth(admin)).json()[
        "shares_submitted"
    ] == 2

    # Candidate cannot read yet.
    cand = login(client, "cand001", "candidate1")
    assert client.get(f"/exams/{eid}/paper", headers=auth(cand)).status_code == 403

    # Third custodian submits -> threshold met AND time passed -> UNLOCKED.
    s = client.post(f"/exams/{eid}/shares/submit", headers=auth(login(client, "cust3", "custodian3")))
    assert s.json()["status"] == "UNLOCKED"

    # Candidate can now read the real paper.
    r = client.get(f"/exams/{eid}/paper", headers=auth(cand))
    assert r.status_code == 200
    assert "END OF PAPER" in r.json()["content"]


def test_time_gate_blocks_even_with_enough_shares(client):
    admin = login(client, "admin", "admin123")
    # Release far in the future.
    exam = _create_exam(client, admin, release_offset_seconds=3600)
    eid = exam["id"]

    for u, p in [("cust1", "custodian1"), ("cust2", "custodian2"), ("cust3", "custodian3")]:
        s = client.post(f"/exams/{eid}/shares/submit", headers=auth(login(client, u, p)))
        assert s.status_code == 200

    status = client.get(f"/exams/{eid}/unlock/status", headers=auth(admin)).json()
    assert status["shares_submitted"] == 3
    assert status["time_locked"] is True
    assert status["status"] == "SEALED"  # 3 valid shares, but the gate holds

    # The denial was audited.
    events = client.get("/audit", headers=auth(login(client, "investigator", "invest123"))).json()
    assert any(e["action"] == "UNLOCK_DENIED" for e in events)

    # Candidate still blocked.
    cand = login(client, "cand001", "candidate1")
    assert client.get(f"/exams/{eid}/paper", headers=auth(cand)).status_code == 403


def test_resubmission_is_idempotent(client):
    admin = login(client, "admin", "admin123")
    eid = _create_exam(client, admin)["id"]
    cust1 = login(client, "cust1", "custodian1")
    client.post(f"/exams/{eid}/shares/submit", headers=auth(cust1))
    client.post(f"/exams/{eid}/shares/submit", headers=auth(cust1))  # again
    status = client.get(f"/exams/{eid}/unlock/status", headers=auth(admin)).json()
    assert status["shares_submitted"] == 1  # not double-counted


def test_non_assigned_custodian_cannot_submit(client):
    admin = login(client, "admin", "admin123")
    # Only cust1..cust3 are custodians for this exam.
    exam = _create_exam(
        client, admin, custodian_usernames=["cust1", "cust2", "cust3"]
    )
    eid = exam["id"]
    assert exam["num_custodians_n"] == 3

    cust4 = login(client, "cust4", "custodian4")
    r = client.post(f"/exams/{eid}/shares/submit", headers=auth(cust4))
    assert r.status_code == 403


# ---- audit endpoints -----------------------------------------------------
def test_audit_verify_endpoint_ok(client):
    admin = login(client, "admin", "admin123")
    _create_exam(client, admin)
    inv = login(client, "investigator", "invest123")
    r = client.get("/audit/verify", headers=auth(inv))
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_candidate_cannot_view_audit(client):
    cand = login(client, "cand001", "candidate1")
    assert client.get("/audit", headers=auth(cand)).status_code == 403
