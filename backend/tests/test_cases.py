"""Persisted forensic leak cases.

A detection (text match or image trace) must create a retrievable case that
carries the full candidate profile, so an investigator can reopen it later from
the audit event's case_id without re-supplying the leaked artifact.
"""

from tests.conftest import auth, login

BLUEPRINT = {
    "sections": [
        {"name": "A", "topic": "algebra", "difficulty": "easy", "count": 3},
        {"name": "B", "topic": "geometry", "difficulty": "hard", "count": 2},
    ]
}


def _seal_unlock_serve(client):
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
    cand = login(client, "cand001", "candidate1")
    # Fetch the watermarked image first so the fingerprint is registered (this is
    # the real leak vector), then grab the text to use as the leaked artifact.
    client.get(f"/exams/{eid}/paper/image", headers=auth(cand))
    text = client.get(f"/exams/{eid}/paper", headers=auth(cand)).json()["content"]
    return admin, eid, text


def test_text_match_creates_retrievable_case(client):
    admin, _, text = _seal_unlock_serve(client)
    inv = login(client, "investigator", "invest123")

    match = client.post("/investigator/match", json={"text": text}, headers=auth(inv)).json()
    case_id = match["case_id"]
    assert isinstance(case_id, int)

    # Reopen the case from its id — full candidate profile must be present.
    case = client.get(f"/investigator/cases/{case_id}", headers=auth(inv))
    assert case.status_code == 200, case.text
    data = case.json()
    assert data["kind"] == "text"
    assert data["suspects"], "case must carry the implicated candidates"
    s = data["suspects"][0]
    # "All the details": roll number, name, centre, exam, fingerprint.
    assert s["candidate_code"] == "R-001"
    assert s["display_name"] == "Candidate 001"
    assert s["center_id"] == "DEL-01"
    assert s["exam_id"] is not None
    assert s["fingerprint"]


def test_case_id_is_stamped_on_the_audit_event(client):
    admin, _, text = _seal_unlock_serve(client)
    inv = login(client, "investigator", "invest123")
    case_id = client.post("/investigator/match", json={"text": text}, headers=auth(inv)).json()["case_id"]

    events = client.get("/audit", headers=auth(admin)).json()
    matched = [e for e in events if e["action"] == "LEAK_MATCHED"]
    assert matched, "expected a LEAK_MATCHED event"
    assert f'"case_id":{case_id}' in matched[-1]["details"]


def test_cases_list_shows_newest_first(client):
    _, _, text = _seal_unlock_serve(client)
    inv = login(client, "investigator", "invest123")
    client.post("/investigator/match", json={"text": "Solve for x: 2x + 6 = 14."}, headers=auth(inv))
    client.post("/investigator/match", json={"text": text}, headers=auth(inv))

    cases = client.get("/investigator/cases", headers=auth(inv)).json()
    assert len(cases) >= 2
    assert cases[0]["id"] > cases[1]["id"]  # newest first
    assert {"kind", "summary", "top_candidate", "query_preview"} <= cases[0].keys()


def test_cases_require_investigator_or_admin(client):
    cand = login(client, "cand001", "candidate1")
    assert client.get("/investigator/cases", headers=auth(cand)).status_code == 403


def test_missing_case_is_404(client):
    inv = login(client, "investigator", "invest123")
    assert client.get("/investigator/cases/99999", headers=auth(inv)).status_code == 404
