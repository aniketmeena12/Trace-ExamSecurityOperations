"""Dynamic per-candidate paper assembly (M5).

Proves the leak-resistance properties that make dynamic assembly worthwhile:
  * determinism — a candidate always gets the same paper,
  * distinctness — different candidates get different papers,
  * blueprint fidelity — the right counts per section,
  * no plaintext at rest — question bodies and assembled papers are never stored
    in the clear,
  * release gating — assembly is impossible until the exam key is reconstructed.
"""

import json

import pytest

from tests.conftest import auth, login

BLUEPRINT = {
    "sections": [
        {"name": "A", "topic": "algebra", "difficulty": "easy", "count": 3},
        {"name": "B", "topic": "geometry", "difficulty": "hard", "count": 2},
    ]
}


def _seal_dynamic(client, admin_tok, *, offset=-10, threshold=3):
    body = {
        "name": "Dynamic Math",
        "subject": "MATH-DEMO",
        "center_id": "DEL-01",
        "threshold_k": threshold,
        "release_offset_seconds": offset,
        "assembly_mode": "dynamic",
        "blueprint": BLUEPRINT,
    }
    r = client.post("/exams", json=body, headers=auth(admin_tok))
    assert r.status_code == 201, r.text
    return r.json()["id"]


def _unlock(client, eid, custodians=("cust1", "cust2", "cust3")):
    for u in custodians:
        tok = login(client, u, f"custodian{u[-1]}")
        client.post(f"/exams/{eid}/shares/submit", headers=auth(tok))


# ---- service-level ----------------------------------------------------------
def test_question_body_is_ciphertext_at_rest(db_session):
    """Stored question bytes must not contain the plaintext prompt."""
    from trace.models import Question

    from trace.services import assembly

    q = db_session.query(Question).first()
    assert q is not None
    # The decrypted prompt must NOT appear anywhere in the stored bytes.
    body = assembly.decrypt_question_body(q)
    assert "prompt" in body and isinstance(body["options"], list)
    assert body["prompt"].encode("utf-8") not in q.ciphertext
    assert b"prompt" not in q.ciphertext  # not even the JSON key leaks


def test_blueprint_validation_rejects_understocked_section(db_session):
    from trace.services import assembly

    with pytest.raises(ValueError):
        assembly.validate_blueprint(
            db_session,
            "MATH-DEMO",
            {"sections": [{"name": "A", "topic": "algebra", "difficulty": "easy", "count": 99}]},
        )


# ---- API-level --------------------------------------------------------------
def test_dynamic_paper_is_deterministic_per_candidate(client):
    admin = login(client, "admin", "admin123")
    eid = _seal_dynamic(client, admin)
    _unlock(client, eid)

    cand = login(client, "cand001", "candidate1")
    first = client.get(f"/exams/{eid}/paper", headers=auth(cand))
    second = client.get(f"/exams/{eid}/paper", headers=auth(cand))
    assert first.status_code == 200, first.text
    assert first.json()["content"] == second.json()["content"]


def test_dynamic_papers_differ_across_candidates(client):
    admin = login(client, "admin", "admin123")
    eid = _seal_dynamic(client, admin)
    _unlock(client, eid)

    p1 = client.get(f"/exams/{eid}/paper", headers=auth(login(client, "cand001", "candidate1")))
    p2 = client.get(f"/exams/{eid}/paper", headers=auth(login(client, "cand002", "candidate2")))
    assert p1.status_code == 200 and p2.status_code == 200
    # With a 5-choose-3 and 5-choose-2 bank, two candidates almost surely differ.
    assert p1.json()["content"] != p2.json()["content"]


def test_dynamic_paper_satisfies_blueprint_counts(client):
    admin = login(client, "admin", "admin123")
    eid = _seal_dynamic(client, admin)
    _unlock(client, eid)

    cand = login(client, "cand001", "candidate1")
    content = client.get(f"/exams/{eid}/paper", headers=auth(cand)).json()["content"]
    # 3 + 2 = 5 numbered questions, two section headers.
    assert "— Section A —" in content and "— Section B —" in content
    numbered = [ln for ln in content.splitlines() if ln[:2] in {f"{i}." for i in range(1, 10)}]
    assert len(numbered) == 5


def test_assembly_blocked_before_release(client):
    admin = login(client, "admin", "admin123")
    eid = _seal_dynamic(client, admin, offset=3600)  # time-locked
    _unlock(client, eid)  # shares in, but the gate holds

    cand = login(client, "cand001", "candidate1")
    r = client.get(f"/exams/{eid}/paper", headers=auth(cand))
    assert r.status_code == 403


def test_selection_recorded_not_plaintext(client, db_session):
    admin = login(client, "admin", "admin123")
    eid = _seal_dynamic(client, admin)
    _unlock(client, eid)
    client.get(f"/exams/{eid}/paper", headers=auth(login(client, "cand001", "candidate1")))

    from trace.models import CandidatePaper

    row = db_session.query(CandidatePaper).filter_by(exam_id=eid, username="cand001").first()
    assert row is not None
    ids = json.loads(row.selected_question_ids)
    assert len(ids) == 5  # only the selection (ids), never the assembled text


def test_blueprint_endpoint_reveals_counts_not_content(client):
    admin = login(client, "admin", "admin123")
    eid = _seal_dynamic(client, admin)
    r = client.get(f"/exams/{eid}/blueprint", headers=auth(admin))
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["assembly_mode"] == "dynamic"
    assert data["questions_per_paper"] == 5
    assert data["pool_size"] >= 5


def test_paper_immutable_after_bank_change(client, db_session):
    """Retiring a bank question must not change an already-sealed exam's paper.

    The per-section pools are frozen in the sealed manifest, so selection is
    immune to later edits of the live question bank.
    """
    admin = login(client, "admin", "admin123")
    eid = _seal_dynamic(client, admin)
    _unlock(client, eid)
    cand = login(client, "cand001", "candidate1")
    before = client.get(f"/exams/{eid}/paper", headers=auth(cand)).json()["content"]

    # Retire a question from the live bank after the exam was sealed.
    from trace.models import Question

    q = db_session.query(Question).filter_by(subject="MATH-DEMO").first()
    q.active = 0
    db_session.commit()

    after = client.get(f"/exams/{eid}/paper", headers=auth(cand)).json()["content"]
    assert before == after


def test_question_list_never_exposes_bodies(client):
    admin = login(client, "admin", "admin123")
    r = client.get("/questions?subject=MATH-DEMO", headers=auth(admin))
    assert r.status_code == 200, r.text
    items = r.json()
    assert len(items) >= 10
    for q in items:
        assert "prompt" not in q and "ciphertext" not in q and "answer" not in q
