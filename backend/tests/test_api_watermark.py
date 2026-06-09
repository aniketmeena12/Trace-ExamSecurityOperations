"""Integration tests for the M3.5 watermark/trace API wiring."""

import io

from PIL import Image

from tests.conftest import auth, login


def _seal_and_unlock(client, admin_tok, **overrides):
    body = {
        "name": "PHY-2026",
        "subject": "Physics",
        "center_id": "DEL-01",
        "threshold_k": 3,
        "release_offset_seconds": -10,
    }
    body.update(overrides)
    eid = client.post("/exams", json=body, headers=auth(admin_tok)).json()["id"]
    for u, p in [("cust1", "custodian1"), ("cust2", "custodian2"), ("cust3", "custodian3")]:
        client.post(f"/exams/{eid}/shares/submit", headers=auth(login(client, u, p)))
    return eid


# ---- custodian my-share --------------------------------------------------
def test_my_share_masked_before_window_then_revealed(client):
    admin = login(client, "admin", "admin123")
    # future release -> window closed -> masked
    eid = client.post(
        "/exams",
        json={"name": "X", "subject": "Y", "center_id": "DEL-01",
              "threshold_k": 3, "release_offset_seconds": 3600},
        headers=auth(admin),
    ).json()["id"]
    cust1 = login(client, "cust1", "custodian1")
    r = client.get(f"/exams/{eid}/my-share", headers=auth(cust1)).json()
    assert r["masked"] is True and r["share"] is None and r["x"] >= 1

    # past release -> window open -> share revealed as "xx:hex"
    eid2 = client.post(
        "/exams",
        json={"name": "X2", "subject": "Y", "center_id": "DEL-01",
              "threshold_k": 3, "release_offset_seconds": -5},
        headers=auth(admin),
    ).json()["id"]
    r2 = client.get(f"/exams/{eid2}/my-share", headers=auth(cust1)).json()
    assert r2["masked"] is False and r2["window_open"] is True
    assert r2["share"] and ":" in r2["share"]


def test_my_share_rejects_non_custodian_of_exam(client):
    admin = login(client, "admin", "admin123")
    eid = client.post(
        "/exams",
        json={"name": "X", "subject": "Y", "center_id": "DEL-01",
              "threshold_k": 2, "release_offset_seconds": -5,
              "custodian_usernames": ["cust1", "cust2"]},
        headers=auth(admin),
    ).json()["id"]
    cust5 = login(client, "cust5", "custodian5")
    assert client.get(f"/exams/{eid}/my-share", headers=auth(cust5)).status_code == 403


# ---- candidate watermarked image ----------------------------------------
def test_candidate_gets_watermarked_png_after_unlock(client):
    admin = login(client, "admin", "admin123")
    eid = _seal_and_unlock(client, admin)
    cand = login(client, "cand001", "candidate1")
    r = client.get(f"/exams/{eid}/paper/image", headers=auth(cand))
    assert r.status_code == 200
    assert r.headers["content-type"] == "image/png"
    assert r.content[:8] == b"\x89PNG\r\n\x1a\n"  # valid PNG signature
    assert "X-Trace-Fingerprint" in r.headers
    # It's a real, decodable image.
    img = Image.open(io.BytesIO(r.content))
    assert img.size[0] > 100 and img.size[1] > 100


def test_paper_image_blocked_before_release(client):
    admin = login(client, "admin", "admin123")
    eid = client.post(
        "/exams",
        json={"name": "X", "subject": "Y", "center_id": "DEL-01",
              "threshold_k": 3, "release_offset_seconds": 3600},
        headers=auth(admin),
    ).json()["id"]
    cand = login(client, "cand001", "candidate1")
    assert client.get(f"/exams/{eid}/paper/image", headers=auth(cand)).status_code == 403


# ---- investigator trace --------------------------------------------------
def test_trace_identifies_candidate_from_downloaded_image(client):
    admin = login(client, "admin", "admin123")
    eid = _seal_and_unlock(client, admin)

    # Candidate downloads their watermarked copy (registers the fingerprint).
    cand = login(client, "cand001", "candidate1")
    img = client.get(f"/exams/{eid}/paper/image", headers=auth(cand)).content

    # Investigator uploads that exact image -> exact trace.
    inv = login(client, "investigator", "invest123")
    r = client.post("/investigator/trace", files={"file": ("leak.png", img, "image/png")},
                    headers=auth(inv))
    assert r.status_code == 200
    body = r.json()
    assert body["watermark_present"] is True
    assert body["match"]["candidate_id"] == "R-001"
    assert body["match"]["center_id"] == "DEL-01"
    assert body["confidence"] == 1.0


def test_trace_survives_jpeg_recompression(client):
    admin = login(client, "admin", "admin123")
    eid = _seal_and_unlock(client, admin)
    cand = login(client, "cand002", "candidate2")
    png = client.get(f"/exams/{eid}/paper/image", headers=auth(cand)).content

    # Re-compress to JPEG q60 to simulate a real leak.
    jpg_buf = io.BytesIO()
    Image.open(io.BytesIO(png)).convert("RGB").save(jpg_buf, "JPEG", quality=60)

    inv = login(client, "investigator", "invest123")
    r = client.post(
        "/investigator/trace",
        files={"file": ("leak.jpg", jpg_buf.getvalue(), "image/jpeg")},
        headers=auth(inv),
    ).json()
    assert r["watermark_present"] is True
    assert r["match"]["candidate_id"] == "R-002"


def test_trace_clean_image_reports_no_watermark(client):
    admin = login(client, "admin", "admin123")
    eid = _seal_and_unlock(client, admin)
    # A clean (un-watermarked) image of similar size.
    clean = io.BytesIO()
    Image.new("RGB", (820, 940), (250, 250, 250)).save(clean, "PNG")
    inv = login(client, "investigator", "invest123")
    r = client.post(
        "/investigator/trace",
        files={"file": ("nope.png", clean.getvalue(), "image/png")},
        headers=auth(inv),
    ).json()
    assert r["watermark_present"] is False


def test_candidate_cannot_call_trace(client):
    cand = login(client, "cand001", "candidate1")
    blob = io.BytesIO()
    Image.new("RGB", (820, 940), (250, 250, 250)).save(blob, "PNG")
    r = client.post(
        "/investigator/trace",
        files={"file": ("x.png", blob.getvalue(), "image/png")},
        headers=auth(cand),
    )
    assert r.status_code == 403
