"""Pydantic request/response models for the Trace API."""

from datetime import datetime

from pydantic import BaseModel, Field


# ---- auth ----------------------------------------------------------------
class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    username: str


class UserOut(BaseModel):
    username: str
    display_name: str
    role: str
    candidate_code: str | None = None
    center_id: str | None = None

    model_config = {"from_attributes": True}


# ---- exams ---------------------------------------------------------------
class ExamCreate(BaseModel):
    name: str
    subject: str
    center_id: str
    threshold_k: int = Field(ge=1, le=255)
    # Provide exactly one of these to set the release time.
    release_offset_seconds: int | None = Field(
        default=None,
        description="Release this many seconds from now (negative = already open).",
    )
    release_time: datetime | None = None
    # Optional overrides; default paper = sample, default custodians = all custodians.
    paper_text: str | None = None
    custodian_usernames: list[str] | None = None


class ExamOut(BaseModel):
    id: int
    name: str
    subject: str
    center_id: str
    status: str
    threshold_k: int
    num_custodians_n: int
    release_time: datetime
    unlocked_at: datetime | None = None

    model_config = {"from_attributes": True}


class UnlockStatusOut(BaseModel):
    exam_id: int
    status: str
    threshold_k: int
    num_custodians_n: int
    shares_submitted: int
    shares_needed: int
    time_locked: bool
    release_time: str
    seconds_remaining: float
    unlocked_at: str | None = None


class PaperOut(BaseModel):
    exam_id: int
    name: str
    subject: str
    content: str


class MyShareOut(BaseModel):
    exam_id: int
    custodian: str
    x: int
    share: str | None = None  # "xx:hex…" once the window is open, else null
    masked: bool
    window_open: bool
    submitted: bool
    status: str
    release_time: str
    seconds_remaining: float


# ---- watermark / trace ---------------------------------------------------
class TraceMatch(BaseModel):
    center_id: str
    candidate_id: str
    exam_id: int | None = None
    username: str | None = None


class TraceOut(BaseModel):
    watermark_present: bool
    magic_hd: int
    extracted_fingerprint: str
    match: TraceMatch | None = None
    bit_distance: int | None = None
    confidence: float


# ---- audit ---------------------------------------------------------------
class AuditEventOut(BaseModel):
    id: int
    timestamp: str
    actor: str
    action: str
    target: str
    details: str
    prev_hash: str
    hash: str

    model_config = {"from_attributes": True}


class ChainVerifyOut(BaseModel):
    ok: bool
    count: int
    broken: list[int]
    first_broken: int | None = None
