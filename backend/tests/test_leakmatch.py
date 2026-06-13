"""Leak-match detector (Milestone B).

Proves the detector matches a pasted leak to bank questions and uses the
per-candidate selection records to narrow the source — the forensic payoff of
dynamic assembly.
"""

from tests.conftest import auth, login

BLUEPRINT = {
    "sections": [
        {"name": "A", "topic": "algebra", "difficulty": "easy", "count": 3},
        {"name": "B", "topic": "geometry", "difficulty": "hard", "count": 2},
    ]
}


def _seal_unlock_serve(client):
    """Seal a dynamic exam, unlock it, and have both candidates fetch papers."""
    admin = login(client, "admin", "admin123")
    body = {
        "name": "Dynamic Math",
        "subject": "MATH-DEMO",
        "center_id": "DEL-01",
        "threshold_k": 3,
        "release_offset_seconds": -10,
        "assembly_mode": "dynamic",
        "blueprint": BLUEPRINT,
    }
    eid = client.post("/exams", json=body, headers=auth(admin)).json()["id"]
    for u in ("cust1", "cust2", "cust3"):
        client.post(f"/exams/{eid}/shares/submit", headers=auth(login(client, u, f"custodian{u[-1]}")))
    papers = {}
    for c in ("cand001", "cand002"):
        text = client.get(f"/exams/{eid}/paper", headers=auth(login(client, c, f"candidate{c[-1]}"))).json()["content"]
        papers[c] = text
    return admin, eid, papers


def test_exact_question_text_is_matched(client):
    admin, _, _ = _seal_unlock_serve(client)
    inv = login(client, "investigator", "invest123")
    leak = "Solve for x: 2x + 6 = 14."  # verbatim seeded question
    r = client.post("/investigator/match", json={"text": leak}, headers=auth(inv))
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["matched_questions"], "expected at least one matched question"
    assert data["matched_questions"][0]["containment"] >= 0.9


def test_unrelated_text_matches_nothing(client):
    _seal_unlock_serve(client)
    inv = login(client, "investigator", "invest123")
    r = client.post(
        "/investigator/match",
        json={"text": "the quick brown fox jumps over the lazy dog"},
        headers=auth(inv),
    )
    assert r.status_code == 200
    assert r.json()["matched_questions"] == []


def test_full_paper_leak_points_to_its_owner(client):
    """Pasting a whole candidate's paper should make that candidate the lead.

    The exact match count can include a near-collision on short math prompts, so
    the robust guarantee is the *ranking*: the true owner is the strongest lead
    (highest overlap), and is named in the summary.
    """
    admin, eid, papers = _seal_unlock_serve(client)
    inv = login(client, "investigator", "invest123")

    r = client.post("/investigator/match", json={"text": papers["cand001"]}, headers=auth(inv))
    data = r.json()
    assert len(data["matched_questions"]) >= 5  # at least cand001's five questions
    assert data["suspects"], "expected at least one suspect"
    top = data["suspects"][0]
    assert top["candidate_code"] == "R-001"  # cand001 is the strongest lead
    assert "R-001" in data["note"]


def test_match_requires_investigator_or_admin(client):
    _seal_unlock_serve(client)
    cand = login(client, "cand001", "candidate1")
    r = client.post("/investigator/match", json={"text": "anything"}, headers=auth(cand))
    assert r.status_code == 403


def test_match_is_audited(client):
    admin, _, _ = _seal_unlock_serve(client)
    inv = login(client, "investigator", "invest123")
    client.post("/investigator/match", json={"text": "Solve for x: 2x + 6 = 14."}, headers=auth(inv))
    acts = {e["action"] for e in client.get("/audit", headers=auth(admin)).json()}
    assert "LEAK_MATCHED" in acts
