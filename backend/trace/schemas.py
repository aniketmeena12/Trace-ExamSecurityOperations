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
    # Dynamic assembly (M5): set assembly_mode="dynamic" and provide a blueprint
    # of {"sections": [{"name","topic","difficulty","count"}, ...]}. The paper is
    # then assembled per-candidate from the encrypted question bank.
    assembly_mode: str = "static"
    blueprint: dict | None = None


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
    assembly_mode: str = "static"

    model_config = {"from_attributes": True}


# ---- question bank / dynamic assembly ------------------------------------
class QuestionCreate(BaseModel):
    subject: str
    section: str = ""
    topic: str = ""
    difficulty: str = "medium"
    prompt: str
    options: list[str] = Field(default_factory=list)
    answer: str | None = None  # stored encrypted; never returned to candidates


class QuestionOut(BaseModel):
    """Bank metadata only — the encrypted body is never exposed over the API."""

    id: int
    subject: str
    section: str
    topic: str
    difficulty: str
    contributor: str
    active: int
    created_at: datetime

    model_config = {"from_attributes": True}


class BlueprintOut(BaseModel):
    exam_id: int
    assembly_mode: str
    blueprint: dict | None = None
    pool_size: int  # distinct questions the blueprint can draw from
    questions_per_paper: int  # total selected for each candidate


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


# ---- leak-match detector (text leaks) ------------------------------------
class LeakMatchIn(BaseModel):
    text: str = Field(min_length=1, description="Suspected leaked text to match.")


class MatchedQuestion(BaseModel):
    question_id: int
    subject: str
    topic: str
    difficulty: str
    containment: float
    prompt_preview: str


class LeakSuspect(BaseModel):
    """An implicated candidate with their full identity profile."""

    username: str
    candidate_code: str | None = None
    display_name: str | None = None
    center_id: str | None = None
    exam_id: int | None = None
    fingerprint: str | None = None
    issued_at: str | None = None
    question_ids: list[int] | None = None
    # text-match specifics
    matched_of_leak: int | None = None
    has_all: bool | None = None
    # image-trace specifics
    confidence: float | None = None
    bit_distance: int | None = None


class LeakMatchOut(BaseModel):
    case_id: int
    leaked_chars: int
    matched_questions: list[MatchedQuestion]
    suspects: list[LeakSuspect]
    note: str


# ---- persisted leak cases ------------------------------------------------
class LeakCaseSummary(BaseModel):
    id: int
    kind: str
    created_at: datetime
    created_by: str
    summary: str
    top_candidate: str | None = None
    query_preview: str

    model_config = {"from_attributes": True}


class LeakCaseDetail(LeakCaseSummary):
    suspects: list[LeakSuspect] = []
    matched_questions: list[MatchedQuestion] = []
    note: str | None = None


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
    case_id: int | None = None


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
