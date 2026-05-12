---
phase: 02-assessment-workflow-pic-asesor
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - backend/app/models/periode.py
  - backend/app/models/assessment_session.py
  - backend/app/models/assessment_session_bidang.py
  - backend/app/models/indikator_applicable_bidang.py
  - backend/app/models/recommendation.py
  - backend/app/models/notification.py
  - backend/app/models/audit_log.py
  - backend/app/schemas/periode.py
  - backend/app/schemas/assessment.py
  - backend/app/schemas/recommendation.py
  - backend/app/schemas/notification.py
  - backend/app/schemas/audit.py
  - backend/alembic/versions/20260513_100000_0004_periode_and_sessions.py
  - backend/alembic/versions/20260513_110000_0005_recommendation_notification.py
  - backend/alembic/versions/20260513_120000_0006_audit_log.py
  - backend/tests/test_phase2_models_import.py
  - backend/tests/test_phase2_migrations.py
autonomous: true
requirements:
  - REQ-periode-lifecycle
  - REQ-self-assessment-kpi-form
  - REQ-self-assessment-ml-form
  - REQ-pic-actions
  - REQ-asesor-review
  - REQ-recommendation-create
  - REQ-recommendation-lifecycle
  - REQ-notifications
  - REQ-audit-log
must_haves:
  truths:
    - "Seven new tables exist on Alembic chain 0001 → 0002 → 0003 → 0004 → 0005 → 0006: `periode`, `assessment_session`, `assessment_session_bidang`, `indikator_applicable_bidang`, `recommendation`, `notification`, `audit_log`"
    - "`periode.status` is a Postgres enum with the six DEC-T1-001 values: `draft | aktif | self_assessment | asesmen | finalisasi | closed`"
    - "**DEC-T1-003 honored:** `assessment_session.bidang_id UUID NULL` (nullable for aggregate); companion table `assessment_session_bidang(session_id, bidang_id, PK(session_id, bidang_id))` enumerates which bidang share an aggregate session"
    - "**DEC-T1-004 honored:** `indikator_applicable_bidang(indikator_id, bidang_id, PK(indikator_id, bidang_id))` mapping table is created and FK-referenced; non-applicable pairs are skipped at session-creation time (logic lives in Plan 02-02)"
    - "`assessment_session.state` enum = `draft | submitted | approved | overridden | revision_requested | abandoned` (DEC-T4-004 abandoned suffix included)"
    - "`assessment_session.payload JSONB` holds the PIC form data; `assessment_session.pencapaian NUMERIC(10,4) NULL` and `nilai NUMERIC(10,4) NULL` carry server-authoritative compute (DEC-T2-005); `nilai_final NUMERIC(10,4) NULL` carries asesor's value on override (DEC-T3-001); `catatan_pic TEXT NULL`, `catatan_asesor TEXT NULL`, `link_eviden TEXT NULL` (URL only — REQ-no-evidence-upload still enforced)"
    - "`recommendation` table has `status` enum `open | in_progress | pending_review | closed | carried_over` (DEC-T4-003), `severity` enum `low | medium | high | critical`, `action_items JSONB NOT NULL` (typed `[{action, deadline?, owner_user_id?}, ...]` per Pydantic schema), `progress_percent INTEGER DEFAULT 0`, `source_assessment_id` FK → assessment_session, `source_periode_id` FK → periode, `target_periode_id` FK → periode, `carried_from_id` + `carried_to_id` self-FK chain (DEC-T4-004)"
    - "`notification` table has `type` enum (six DEC-T5-003 values), `read_at TIMESTAMP NULL`, `payload JSONB`, indexed on `(user_id, read_at, created_at DESC)` for unread-first list"
    - "`audit_log` table is append-only — no UPDATE/DELETE triggers in schema, no PATCH/DELETE routes exposed (Plan 02-03 enforces at router level). Three indexes per DEC-T6-002: `(user_id, created_at DESC)`, `(entity_type, entity_id, created_at DESC)`, `(created_at DESC)`"
    - "`audit_log.before_data JSONB NULL`, `audit_log.after_data JSONB NULL`, `audit_log.action TEXT NOT NULL`, `entity_type TEXT NULL`, `entity_id UUID NULL`, `ip_address INET NULL`, `user_agent TEXT NULL`, `user_id UUID NULL` (NULL on failed login)"
    - "Pydantic v2 schemas (in `backend/app/schemas/`) declare all request/response shapes with `ConfigDict(extra='forbid')`. `RecommendationCreate.action_items: list[ActionItem]` where `ActionItem` has optional `owner_user_id` (DEC-T4-001 — service layer resolves default, NOT validator). `AsesorReview.catatan_asesor: Annotated[str, Field(min_length=20)]` enforced via Pydantic when `decision == 'override'` (DEC-T3-001)"
    - "Phase-1 auto-discovery still works: dropping the seven new model files into `backend/app/models/` and the five new schema files into `backend/app/schemas/` requires zero edits to `app/db/base.py` or `app/main.py`"
    - "REQ-no-evidence-upload contract test still passes: no new multipart endpoints are introduced by this plan (only models + schemas + migrations); the allow-list stays at exactly one entry from Plan 01-06"
  artifacts:
    - path: "backend/app/models/periode.py"
      provides: "Periode model with status enum + tahun/triwulan/semester + tanggal_buka/tanggal_tutup informational fields (DEC-T1-001)"
      contains: "PeriodeStatus"
    - path: "backend/app/models/assessment_session.py"
      provides: "AssessmentSession model with state enum + payload JSONB + nilai/pencapaian/nilai_final + audit cols; bidang_id NULL for aggregate (DEC-T1-003)"
      contains: "bidang_id"
    - path: "backend/app/models/assessment_session_bidang.py"
      provides: "N:N mapping for aggregate sessions (DEC-T1-003)"
      contains: "session_id"
    - path: "backend/app/models/indikator_applicable_bidang.py"
      provides: "N:N mapping declaring which bidang each indikator applies to (DEC-T1-004)"
      contains: "indikator_id"
    - path: "backend/app/models/recommendation.py"
      provides: "Recommendation model with status/severity/action_items JSONB + carried_from_id/carried_to_id self-FK"
      contains: "action_items"
    - path: "backend/app/models/notification.py"
      provides: "Notification with type enum + read_at + payload JSONB"
      contains: "read_at"
    - path: "backend/app/models/audit_log.py"
      provides: "Append-only audit log with before_data/after_data JSONB, three indexes (DEC-T6-002)"
      contains: "before_data"
    - path: "backend/app/schemas/recommendation.py"
      provides: "Pydantic ActionItem + RecommendationCreate with typed action_items (default owner-resolution in service layer, not validator — RESEARCH §11.13)"
      contains: "ActionItem"
    - path: "backend/app/schemas/assessment.py"
      provides: "AssessmentSelfAssessmentPatch + AssessmentSubmit + AsesorReview with min-20-char catatan_asesor for override (DEC-T3-001)"
      contains: "catatan_asesor"
    - path: "backend/alembic/versions/20260513_100000_0004_periode_and_sessions.py"
      provides: "Creates periode + assessment_session + assessment_session_bidang + indikator_applicable_bidang; chains down_revision='0003_master_data'"
      contains: "0003_master_data"
    - path: "backend/alembic/versions/20260513_110000_0005_recommendation_notification.py"
      provides: "Creates recommendation + notification + indexes; chains down_revision='0004_periode_and_sessions'"
      contains: "carried_from_id"
    - path: "backend/alembic/versions/20260513_120000_0006_audit_log.py"
      provides: "Creates audit_log + 3 indexes (DEC-T6-002); chains down_revision='0005_recommendation_notification'"
      contains: "audit_log"
  key_links:
    - from: "backend/app/models/assessment_session.py"
      to: "backend/app/models/bidang.py"
      via: "bidang_id FK to bidang(id) ON DELETE SET NULL, nullable (DEC-T1-003)"
      pattern: "ForeignKey.*bidang"
    - from: "backend/app/models/assessment_session.py"
      to: "backend/app/models/periode.py"
      via: "periode_id FK to periode(id) ON DELETE CASCADE"
      pattern: "periode_id"
    - from: "backend/app/models/assessment_session.py"
      to: "backend/app/models/indikator.py"
      via: "indikator_id FK to indikator(id) ON DELETE RESTRICT"
      pattern: "indikator_id"
    - from: "backend/app/models/recommendation.py"
      to: "backend/app/models/assessment_session.py"
      via: "source_assessment_id FK"
      pattern: "source_assessment_id"
    - from: "backend/app/models/recommendation.py"
      to: "backend/app/models/recommendation.py"
      via: "carried_from_id / carried_to_id self-FK chain (DEC-T4-004)"
      pattern: "carried_from_id"
    - from: "backend/alembic/versions/20260513_100000_0004_periode_and_sessions.py"
      to: "backend/alembic/versions/20260512_140000_0003_master_data.py"
      via: "down_revision chain"
      pattern: "down_revision.*0003"
---

## Revision History

- **Iteration 1 (initial):** Phase 2 backend schema chain — 7 new models, 5 new Pydantic schema files, 3 Alembic migrations (0004 → 0005 → 0006). No routers, no services. Wave 1 sequential per RESEARCH §12. All locked decisions honored verbatim.

<objective>
Lay the Phase 2 data-model foundation: seven new SQLAlchemy models (periode, assessment_session, assessment_session_bidang, indikator_applicable_bidang, recommendation, notification, audit_log), five Pydantic schema files (extra='forbid' everywhere), and three linear Alembic migrations chained off Plan 01-06's `0003_master_data`. Every locked decision (DEC-T1-001..T6-002) is enforced at the column / enum / index level so downstream router plans can not bypass it.

Purpose: REQ-periode-lifecycle + REQ-self-assessment-kpi-form + REQ-self-assessment-ml-form + REQ-pic-actions + REQ-asesor-review + REQ-recommendation-create + REQ-recommendation-lifecycle + REQ-notifications + REQ-audit-log — all need this schema before any logic can be written.

Output: 7 models + 5 schemas + 3 migrations + 2 import-smoke / migration-smoke tests. No routers, no business logic. Wave 1 sequential.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/STATE.md
@.planning/phases/02-assessment-workflow-pic-asesor/02-CONTEXT.md
@.planning/phases/02-assessment-workflow-pic-asesor/02-RESEARCH.md
@.planning/phases/01-foundation-master-data-auth/01-03-backend-skeleton-health-SUMMARY.md
@.planning/phases/01-foundation-master-data-auth/01-05-auth-backend-jwt-rbac-SUMMARY.md
@.planning/phases/01-foundation-master-data-auth/01-06-master-data-backend-SUMMARY.md

<interfaces>
<!-- From Phase 1 (already in place) -->
- app.db.base.Base (auto-imports new model modules via pkgutil walk)
- app.deps.db.get_db, app.deps.auth.current_user, app.deps.auth.require_role, app.deps.csrf.require_csrf
- app.models.bidang.Bidang, app.models.indikator.Indikator, app.models.user.User (with bidang_id FK from 0003), app.models.role.Role
- Alembic head = `0003_master_data` (created 2026-05-12 in Plan 01-06)
- backend/tests/conftest.py: client + db_session fixtures + admin_unit_user / pic_user / asesor_user / manajer_user (Plan 05 fixture chain — extended in Plan 02-02 to include sample_periode / sample_session)

<!-- Exposed seams downstream plans (02-02, 02-03) consume -->

# SQLAlchemy models (declarative)
class Periode(Base):
    id: UUID PK
    tahun: int (NOT NULL)
    triwulan: int CHECK 1..4
    semester: int CHECK 1..2
    nama: str(255) NOT NULL  # display label, e.g. "TW2 2026"
    status: PeriodeStatus enum NOT NULL DEFAULT 'draft'
    tanggal_buka: Date NULL    # informational only (DEC-T1-001)
    tanggal_tutup: Date NULL   # informational only
    last_transition_reason: TEXT NULL  # populated on rollback (DEC-T1-002)
    last_transition_by: UUID FK users(id) ON DELETE SET NULL NULL
    last_transition_at: TIMESTAMP WITH TIME ZONE NULL
    # standard audit cols + deleted_at soft delete
    UNIQUE (tahun, triwulan)

class AssessmentSession(Base):
    id: UUID PK
    periode_id: UUID FK periode(id) ON DELETE CASCADE NOT NULL
    indikator_id: UUID FK indikator(id) ON DELETE RESTRICT NOT NULL
    bidang_id: UUID FK bidang(id) ON DELETE SET NULL NULL  # nullable for aggregate sessions (DEC-T1-003)
    state: SessionState enum NOT NULL DEFAULT 'draft'      # draft|submitted|approved|overridden|revision_requested|abandoned
    payload: JSONB NULL                                    # PIC form snapshot
    realisasi: NUMERIC(20,4) NULL                          # KPI form
    target: NUMERIC(20,4) NULL                             # KPI form
    pencapaian: NUMERIC(10,4) NULL                         # server authoritative (DEC-T2-005)
    nilai: NUMERIC(10,4) NULL                              # server authoritative
    nilai_final: NUMERIC(10,4) NULL                        # asesor override value (DEC-T3-001)
    catatan_pic: TEXT NULL
    catatan_asesor: TEXT NULL
    link_eviden: TEXT NULL                                  # URL only — REQ-no-evidence-upload
    submitted_at: TIMESTAMP NULL
    asesor_reviewed_at: TIMESTAMP NULL
    asesor_user_id: UUID FK users(id) ON DELETE SET NULL NULL
    # standard audit cols + deleted_at
    UNIQUE (periode_id, indikator_id, bidang_id)            # per-bidang sessions
    # For aggregate (bidang_id=NULL): UNIQUE constraint allows ONE row per (periode_id, indikator_id, NULL) — Postgres NULLS DISTINCT semantics behave correctly here

class AssessmentSessionBidang(Base):
    session_id: UUID FK assessment_session(id) ON DELETE CASCADE NOT NULL
    bidang_id:  UUID FK bidang(id) ON DELETE CASCADE NOT NULL
    PRIMARY KEY (session_id, bidang_id)

class IndikatorApplicableBidang(Base):
    indikator_id: UUID FK indikator(id) ON DELETE CASCADE NOT NULL
    bidang_id:    UUID FK bidang(id) ON DELETE CASCADE NOT NULL
    is_aggregate: BOOLEAN NOT NULL DEFAULT FALSE             # marks DEC-T1-003 aggregate pair
    PRIMARY KEY (indikator_id, bidang_id)

class Recommendation(Base):
    id: UUID PK
    source_assessment_id: UUID FK assessment_session(id) ON DELETE RESTRICT NOT NULL
    source_periode_id:    UUID FK periode(id) ON DELETE RESTRICT NOT NULL
    target_periode_id:    UUID FK periode(id) ON DELETE RESTRICT NOT NULL
    carried_from_id:      UUID FK recommendation(id) ON DELETE SET NULL NULL
    carried_to_id:        UUID FK recommendation(id) ON DELETE SET NULL NULL
    status: RecommendationStatus enum NOT NULL DEFAULT 'open'  # open|in_progress|pending_review|closed|carried_over
    severity: RecommendationSeverity enum NOT NULL              # low|medium|high|critical
    deskripsi: TEXT NOT NULL
    action_items: JSONB NOT NULL DEFAULT '[]'                   # [{action, deadline?, owner_user_id?}, ...]
    progress_percent: INTEGER NOT NULL DEFAULT 0 CHECK (0..100)
    progress_notes: TEXT NULL
    asesor_close_notes: TEXT NULL
    closed_at: TIMESTAMP NULL
    closed_by: UUID FK users(id) ON DELETE SET NULL NULL
    created_by: UUID FK users(id) ON DELETE SET NULL NULL
    # standard audit cols + deleted_at

class Notification(Base):
    id: UUID PK
    user_id: UUID FK users(id) ON DELETE CASCADE NOT NULL
    type: NotificationType enum NOT NULL                          # assessment_due|review_pending|recommendation_assigned|deadline_approaching|periode_closed|system_announcement
    title: VARCHAR(255) NOT NULL
    body: TEXT NOT NULL
    payload: JSONB NOT NULL DEFAULT '{}'
    read_at: TIMESTAMP WITH TIME ZONE NULL
    created_at: TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
    # index: (user_id, read_at NULLS FIRST, created_at DESC) — for unread-first list

class AuditLog(Base):
    id: UUID PK
    user_id: UUID FK users(id) ON DELETE SET NULL NULL          # NULL on failed login
    action: TEXT NOT NULL                                        # "POST /api/v1/...", "auth.login.success", etc.
    entity_type: TEXT NULL
    entity_id: UUID NULL
    before_data: JSONB NULL
    after_data: JSONB NULL
    ip_address: INET NULL
    user_agent: TEXT NULL
    created_at: TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
    # 3 indexes per DEC-T6-002:
    #   (user_id, created_at DESC)
    #   (entity_type, entity_id, created_at DESC)
    #   (created_at DESC)

# Pydantic schemas (request/response shapes)
class PeriodeCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tahun: int = Field(ge=2024, le=2099)
    triwulan: int = Field(ge=1, le=4)
    semester: int = Field(ge=1, le=2)
    nama: str = Field(min_length=1, max_length=255)
    tanggal_buka: date | None = None
    tanggal_tutup: date | None = None

class PeriodeTransitionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    target_state: Literal["draft","aktif","self_assessment","asesmen","finalisasi","closed"]
    reason: str | None = None       # required on rollback per DEC-T1-002, enforced by router

class AssessmentSelfAssessmentPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    payload: dict | None = None      # JSONB partial — server merges
    realisasi: Decimal | None = None
    target: Decimal | None = None
    catatan_pic: str | None = None
    link_eviden: HttpUrl | None = None    # URL only (REQ-no-evidence-upload)

class AssessmentSubmit(BaseModel):
    model_config = ConfigDict(extra="forbid")
    # No body required; server validates submit gate (DEC-T2-004)

class AsesorReview(BaseModel):
    model_config = ConfigDict(extra="forbid")
    decision: Literal["approve","override","request_revision"]
    nilai_final: Decimal | None = None
    catatan_asesor: str | None = None
    inline_recommendations: list[RecommendationCreate] | None = None
    # @model_validator(mode="after"): if decision=='override', catatan_asesor MUST be >= 20 chars (DEC-T3-001)
    # @model_validator(mode="after"): if decision=='override', nilai_final MUST NOT be None
    # @model_validator(mode="after"): if decision=='approve' or 'request_revision', nilai_final SHOULD be None

class ActionItem(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action: Annotated[str, Field(min_length=1, max_length=2000)]
    deadline: date | None = None
    owner_user_id: UUID | None = None       # default-resolved in service layer (RESEARCH §6 + §11.13)

class RecommendationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source_assessment_id: UUID
    severity: Literal["low","medium","high","critical"]
    deskripsi: Annotated[str, Field(min_length=10, max_length=10_000)]
    action_items: Annotated[list[ActionItem], Field(min_length=1)]
    target_periode_id: UUID

class NotificationPublic(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: UUID
    type: Literal[...]   # six values
    title: str
    body: str
    payload: dict
    read_at: datetime | None
    created_at: datetime

# Enums (in models/enums.py or inline)
class PeriodeStatus(StrEnum):
    DRAFT="draft"; AKTIF="aktif"; SELF_ASSESSMENT="self_assessment"
    ASESMEN="asesmen"; FINALISASI="finalisasi"; CLOSED="closed"

class SessionState(StrEnum):
    DRAFT="draft"; SUBMITTED="submitted"; APPROVED="approved"
    OVERRIDDEN="overridden"; REVISION_REQUESTED="revision_requested"; ABANDONED="abandoned"

class RecommendationStatus(StrEnum):
    OPEN="open"; IN_PROGRESS="in_progress"; PENDING_REVIEW="pending_review"
    CLOSED="closed"; CARRIED_OVER="carried_over"

class RecommendationSeverity(StrEnum):
    LOW="low"; MEDIUM="medium"; HIGH="high"; CRITICAL="critical"

class NotificationType(StrEnum):
    ASSESSMENT_DUE="assessment_due"; REVIEW_PENDING="review_pending"
    RECOMMENDATION_ASSIGNED="recommendation_assigned"
    DEADLINE_APPROACHING="deadline_approaching"
    PERIODE_CLOSED="periode_closed"; SYSTEM_ANNOUNCEMENT="system_announcement"
</interfaces>
</context>

<tasks>

<task type="auto">
  <name>Task 1: Seven SQLAlchemy models + Alembic 0004 migration (periode + assessment_session + assessment_session_bidang + indikator_applicable_bidang)</name>
  <files>
    backend/app/models/periode.py,
    backend/app/models/assessment_session.py,
    backend/app/models/assessment_session_bidang.py,
    backend/app/models/indikator_applicable_bidang.py,
    backend/alembic/versions/20260513_100000_0004_periode_and_sessions.py
  </files>
  <action>
    Every model uses Phase-1 conventions: UUID PK with `server_default=text("uuid_generate_v4()")`; audit cols `created_at, updated_at, created_by, updated_by` (created_by/updated_by are UUID nullable FKs to `users.id` with `ON DELETE SET NULL`); `deleted_at TIMESTAMP WITH TIME ZONE NULL` soft-delete on entities that need it (periode + assessment_session + recommendation — NOT on the N:N tables, NOT on notification/audit_log).

    Enum strategy: use Python `enum.StrEnum` for the Python side and `sa.Enum(..., name="enum_name", create_type=True)` on the SQLAlchemy column with the EXACT lowercase string values from CONTEXT.md verbatim. Postgres enum types are created in the migration via `op.execute("CREATE TYPE ...")` before the table that uses them, then referenced via `sa.Enum(..., name=..., create_type=False)` in `op.create_table` to avoid re-create. Down-revision drops in reverse order.

    1. `backend/app/models/periode.py`:
       ```python
       from __future__ import annotations
       import enum, uuid
       from datetime import datetime, date
       from sqlalchemy import String, Integer, Date, DateTime, Text, ForeignKey, Enum as SAEnum, UniqueConstraint, CheckConstraint, text
       from sqlalchemy.dialects.postgresql import UUID as PGUUID
       from sqlalchemy.orm import Mapped, mapped_column
       from app.db.base import Base

       class PeriodeStatus(str, enum.Enum):
           DRAFT = "draft"
           AKTIF = "aktif"
           SELF_ASSESSMENT = "self_assessment"
           ASESMEN = "asesmen"
           FINALISASI = "finalisasi"
           CLOSED = "closed"

       class Periode(Base):
           __tablename__ = "periode"
           __table_args__ = (
               UniqueConstraint("tahun", "triwulan", name="uq_periode_tahun_triwulan"),
               CheckConstraint("triwulan BETWEEN 1 AND 4", name="ck_periode_triwulan"),
               CheckConstraint("semester BETWEEN 1 AND 2", name="ck_periode_semester"),
           )
           id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
           tahun: Mapped[int] = mapped_column(Integer, nullable=False)
           triwulan: Mapped[int] = mapped_column(Integer, nullable=False)
           semester: Mapped[int] = mapped_column(Integer, nullable=False)
           nama: Mapped[str] = mapped_column(String(255), nullable=False)
           status: Mapped[PeriodeStatus] = mapped_column(
               SAEnum(PeriodeStatus, name="periode_status", values_callable=lambda e: [m.value for m in e], create_type=False),
               nullable=False, server_default=text("'draft'::periode_status"),
           )
           tanggal_buka: Mapped[date | None] = mapped_column(Date, nullable=True)
           tanggal_tutup: Mapped[date | None] = mapped_column(Date, nullable=True)
           last_transition_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
           last_transition_by: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
           last_transition_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
           created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"), nullable=False)
           updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"), nullable=False)
           created_by: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
           updated_by: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
           deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
       ```
       The `last_transition_reason` field captures DEC-T1-002 mandatory rollback reasons; the router (Plan 02-02) requires reason >=20 chars when transitioning backwards.

    2. `backend/app/models/assessment_session.py`:
       ```python
       class SessionState(str, enum.Enum):
           DRAFT = "draft"; SUBMITTED = "submitted"; APPROVED = "approved"
           OVERRIDDEN = "overridden"; REVISION_REQUESTED = "revision_requested"
           ABANDONED = "abandoned"   # DEC-T4-004 sentinel for drafts at periode close

       class AssessmentSession(Base):
           __tablename__ = "assessment_session"
           __table_args__ = (
               UniqueConstraint("periode_id", "indikator_id", "bidang_id", name="uq_session_periode_indikator_bidang"),
               CheckConstraint("progress_percent BETWEEN 0 AND 100", name="ck_session_progress_unused"),  # leftover-safe — but we don't have progress here; drop this CHECK
           )
           id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
           periode_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("periode.id", ondelete="CASCADE"), nullable=False)
           indikator_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("indikator.id", ondelete="RESTRICT"), nullable=False)
           bidang_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("bidang.id", ondelete="SET NULL"), nullable=True)
           state: Mapped[SessionState] = mapped_column(SAEnum(SessionState, name="session_state", values_callable=lambda e: [m.value for m in e], create_type=False), nullable=False, server_default=text("'draft'::session_state"))
           payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
           realisasi: Mapped[Decimal | None] = mapped_column(NUMERIC(20, 4), nullable=True)
           target:    Mapped[Decimal | None] = mapped_column(NUMERIC(20, 4), nullable=True)
           pencapaian: Mapped[Decimal | None] = mapped_column(NUMERIC(10, 4), nullable=True)
           nilai:      Mapped[Decimal | None] = mapped_column(NUMERIC(10, 4), nullable=True)
           nilai_final: Mapped[Decimal | None] = mapped_column(NUMERIC(10, 4), nullable=True)
           catatan_pic:   Mapped[str | None] = mapped_column(Text, nullable=True)
           catatan_asesor: Mapped[str | None] = mapped_column(Text, nullable=True)
           link_eviden:   Mapped[str | None] = mapped_column(Text, nullable=True)   # URL — Pydantic validates format=uri
           submitted_at:        Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
           asesor_reviewed_at:  Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
           asesor_user_id:      Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
           # standard audit cols + deleted_at (same template as Periode above)
       ```
       Drop the leftover CheckConstraint pasted above — it's not relevant for AssessmentSession. The UNIQUE constraint with three nullable-bearing columns relies on Postgres's default NULLS DISTINCT (8.x default; 15+ has explicit knob): aggregate sessions store `bidang_id=NULL`, and Postgres treats two NULL `bidang_id` rows as distinct, but the `(periode_id, indikator_id)` pair plus the application-level "one aggregate session per indikator" invariant (Plan 02-02 service-layer logic) keeps uniqueness. Explicitly add a partial unique index in the migration: `CREATE UNIQUE INDEX uq_session_aggregate ON assessment_session (periode_id, indikator_id) WHERE bidang_id IS NULL`.

    3. `backend/app/models/assessment_session_bidang.py`:
       ```python
       class AssessmentSessionBidang(Base):
           __tablename__ = "assessment_session_bidang"
           session_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("assessment_session.id", ondelete="CASCADE"), primary_key=True)
           bidang_id:  Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("bidang.id", ondelete="CASCADE"), primary_key=True)
           created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"), nullable=False)
       ```

    4. `backend/app/models/indikator_applicable_bidang.py`:
       ```python
       class IndikatorApplicableBidang(Base):
           __tablename__ = "indikator_applicable_bidang"
           indikator_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("indikator.id", ondelete="CASCADE"), primary_key=True)
           bidang_id:    Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("bidang.id", ondelete="CASCADE"), primary_key=True)
           is_aggregate: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("FALSE"))
           created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"), nullable=False)
       ```
       `is_aggregate=True` on a row means "for this indikator, this bidang is part of an aggregate session pool" (DEC-T1-003). Plan 02-02's `session_creator` reads this column to decide whether to spawn one shared session vs N per-bidang sessions.

    5. `backend/alembic/versions/20260513_100000_0004_periode_and_sessions.py`:
       ```python
       """0004 periode and assessment sessions"""
       from alembic import op
       import sqlalchemy as sa
       from sqlalchemy.dialects import postgresql
       revision = "0004_periode_and_sessions"
       down_revision = "0003_master_data"
       branch_labels = None
       depends_on = None

       def upgrade():
           # Postgres enums
           op.execute("CREATE TYPE periode_status AS ENUM ('draft','aktif','self_assessment','asesmen','finalisasi','closed')")
           op.execute("CREATE TYPE session_state AS ENUM ('draft','submitted','approved','overridden','revision_requested','abandoned')")
           # periode
           op.create_table(
               "periode",
               sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("uuid_generate_v4()"), primary_key=True),
               sa.Column("tahun", sa.Integer, nullable=False),
               sa.Column("triwulan", sa.Integer, nullable=False),
               sa.Column("semester", sa.Integer, nullable=False),
               sa.Column("nama", sa.String(255), nullable=False),
               sa.Column("status", postgresql.ENUM(name="periode_status", create_type=False), nullable=False, server_default=sa.text("'draft'::periode_status")),
               sa.Column("tanggal_buka", sa.Date, nullable=True),
               sa.Column("tanggal_tutup", sa.Date, nullable=True),
               sa.Column("last_transition_reason", sa.Text, nullable=True),
               sa.Column("last_transition_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
               sa.Column("last_transition_at", sa.DateTime(timezone=True), nullable=True),
               sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
               sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
               sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
               sa.Column("updated_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
               sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
               sa.UniqueConstraint("tahun", "triwulan", name="uq_periode_tahun_triwulan"),
               sa.CheckConstraint("triwulan BETWEEN 1 AND 4", name="ck_periode_triwulan"),
               sa.CheckConstraint("semester BETWEEN 1 AND 2", name="ck_periode_semester"),
           )
           # assessment_session
           op.create_table(
               "assessment_session",
               sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("uuid_generate_v4()"), primary_key=True),
               sa.Column("periode_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("periode.id", ondelete="CASCADE"), nullable=False),
               sa.Column("indikator_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("indikator.id", ondelete="RESTRICT"), nullable=False),
               sa.Column("bidang_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("bidang.id", ondelete="SET NULL"), nullable=True),
               sa.Column("state", postgresql.ENUM(name="session_state", create_type=False), nullable=False, server_default=sa.text("'draft'::session_state")),
               sa.Column("payload", postgresql.JSONB, nullable=True),
               sa.Column("realisasi",   sa.Numeric(20, 4), nullable=True),
               sa.Column("target",      sa.Numeric(20, 4), nullable=True),
               sa.Column("pencapaian",  sa.Numeric(10, 4), nullable=True),
               sa.Column("nilai",       sa.Numeric(10, 4), nullable=True),
               sa.Column("nilai_final", sa.Numeric(10, 4), nullable=True),
               sa.Column("catatan_pic",    sa.Text, nullable=True),
               sa.Column("catatan_asesor", sa.Text, nullable=True),
               sa.Column("link_eviden",    sa.Text, nullable=True),
               sa.Column("submitted_at",       sa.DateTime(timezone=True), nullable=True),
               sa.Column("asesor_reviewed_at", sa.DateTime(timezone=True), nullable=True),
               sa.Column("asesor_user_id",     postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
               sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
               sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
               sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
               sa.Column("updated_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
               sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
           )
           # Two uniqueness rules. (a) per-bidang sessions: when bidang_id IS NOT NULL, unique by (periode, indikator, bidang). (b) aggregate sessions: when bidang_id IS NULL, exactly one session per (periode, indikator).
           op.execute("CREATE UNIQUE INDEX uq_session_per_bidang ON assessment_session (periode_id, indikator_id, bidang_id) WHERE bidang_id IS NOT NULL")
           op.execute("CREATE UNIQUE INDEX uq_session_aggregate  ON assessment_session (periode_id, indikator_id)            WHERE bidang_id IS NULL")
           op.create_index("ix_session_state",        "assessment_session", ["state"])
           op.create_index("ix_session_periode",      "assessment_session", ["periode_id"])
           op.create_index("ix_session_asesor",       "assessment_session", ["asesor_user_id"])
           # assessment_session_bidang
           op.create_table(
               "assessment_session_bidang",
               sa.Column("session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("assessment_session.id", ondelete="CASCADE"), primary_key=True),
               sa.Column("bidang_id",  postgresql.UUID(as_uuid=True), sa.ForeignKey("bidang.id",            ondelete="CASCADE"), primary_key=True),
               sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
           )
           op.create_index("ix_assbidang_bidang", "assessment_session_bidang", ["bidang_id"])
           # indikator_applicable_bidang
           op.create_table(
               "indikator_applicable_bidang",
               sa.Column("indikator_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("indikator.id", ondelete="CASCADE"), primary_key=True),
               sa.Column("bidang_id",    postgresql.UUID(as_uuid=True), sa.ForeignKey("bidang.id",    ondelete="CASCADE"), primary_key=True),
               sa.Column("is_aggregate", sa.Boolean, nullable=False, server_default=sa.text("FALSE")),
               sa.Column("created_at",   sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
           )
           op.create_index("ix_iapb_bidang", "indikator_applicable_bidang", ["bidang_id"])

       def downgrade():
           op.drop_index("ix_iapb_bidang", table_name="indikator_applicable_bidang")
           op.drop_table("indikator_applicable_bidang")
           op.drop_index("ix_assbidang_bidang", table_name="assessment_session_bidang")
           op.drop_table("assessment_session_bidang")
           op.drop_index("ix_session_asesor", table_name="assessment_session")
           op.drop_index("ix_session_periode", table_name="assessment_session")
           op.drop_index("ix_session_state", table_name="assessment_session")
           op.execute("DROP INDEX IF EXISTS uq_session_aggregate")
           op.execute("DROP INDEX IF EXISTS uq_session_per_bidang")
           op.drop_table("assessment_session")
           op.drop_table("periode")
           op.execute("DROP TYPE IF EXISTS session_state")
           op.execute("DROP TYPE IF EXISTS periode_status")
       ```

    Commit message: `feat(02-01): periode + assessment_session models + alembic 0004 (DEC-T1-001..004)`.
  </action>
  <verify>
    <automated>
      pwsh -NoProfile -Command "
        $files = 'backend/app/models/periode.py','backend/app/models/assessment_session.py','backend/app/models/assessment_session_bidang.py','backend/app/models/indikator_applicable_bidang.py','backend/alembic/versions/20260513_100000_0004_periode_and_sessions.py';
        foreach ($f in $files) { if (-not (Test-Path $f)) { Write-Output ('missing: ' + $f); exit 1 } };
        $p = Get-Content 'backend/app/models/periode.py' -Raw;
        # All six PeriodeStatus values present verbatim (DEC-T1-001)
        foreach ($v in 'draft','aktif','self_assessment','asesmen','finalisasi','closed') {
          if ($p -notmatch ('\"' + $v + '\"')) { Write-Output ('DEC-T1-001: missing status ' + $v); exit 2 }
        };
        # last_transition_reason field for DEC-T1-002
        if ($p -notmatch 'last_transition_reason') { Write-Output 'DEC-T1-002: last_transition_reason missing'; exit 3 };
        $s = Get-Content 'backend/app/models/assessment_session.py' -Raw;
        # bidang_id nullable (DEC-T1-003)
        if ($s -notmatch 'bidang_id') { exit 4 };
        if ($s -notmatch 'nullable=True') { Write-Output 'DEC-T1-003: bidang_id must allow NULL'; exit 5 };
        foreach ($v in 'draft','submitted','approved','overridden','revision_requested','abandoned') {
          if ($s -notmatch ('\"' + $v + '\"')) { Write-Output ('SessionState missing ' + $v); exit 6 }
        };
        $sb = Get-Content 'backend/app/models/assessment_session_bidang.py' -Raw;
        if ($sb -notmatch 'session_id' -or $sb -notmatch 'bidang_id') { exit 7 };
        if ($sb -notmatch 'primary_key=True') { Write-Output 'session_id+bidang_id must be composite PK'; exit 8 };
        $ia = Get-Content 'backend/app/models/indikator_applicable_bidang.py' -Raw;
        if ($ia -notmatch 'indikator_id' -or $ia -notmatch 'bidang_id') { exit 9 };
        if ($ia -notmatch 'is_aggregate') { Write-Output 'DEC-T1-003 marker missing'; exit 10 };
        # Migration chains on 0003
        $m4 = Get-Content 'backend/alembic/versions/20260513_100000_0004_periode_and_sessions.py' -Raw;
        if ($m4 -notmatch 'down_revision\s*=\s*\"0003_master_data\"') { Write-Output 'alembic 0004 must chain off 0003_master_data'; exit 11 };
        if ($m4 -notmatch 'revision\s*=\s*\"0004_periode_and_sessions\"') { exit 12 };
        if ($m4 -notmatch 'CREATE TYPE periode_status') { exit 13 };
        if ($m4 -notmatch 'CREATE TYPE session_state') { exit 14 };
        # Aggregate-session uniqueness partial index (DEC-T1-003)
        if ($m4 -notmatch 'uq_session_aggregate') { Write-Output 'DEC-T1-003: aggregate partial unique index missing'; exit 15 };
        if ($m4 -notmatch 'WHERE bidang_id IS NULL') { exit 16 };
        # Import smoke via WSL
        wsl -d Ubuntu-22.04 -- bash -lc 'cd /mnt/c/Users/ANUNNAKI/projects/PULSE/backend && python3.11 -c \"from app.models.periode import Periode, PeriodeStatus; from app.models.assessment_session import AssessmentSession, SessionState; from app.models.assessment_session_bidang import AssessmentSessionBidang; from app.models.indikator_applicable_bidang import IndikatorApplicableBidang; print(Periode.__tablename__, AssessmentSession.__tablename__, AssessmentSessionBidang.__tablename__, IndikatorApplicableBidang.__tablename__)\"' 2>&1 | Out-String | Write-Output
        if ($LASTEXITCODE -ne 0) { Write-Output 'model import smoke failed'; exit 17 };
        Write-Output 'pass'
      "
    </automated>
  </verify>
  <done>
    Four models exist (periode + assessment_session + assessment_session_bidang + indikator_applicable_bidang) with verbatim CONTEXT.md enum values; Alembic 0004 chains off 0003_master_data, creates two Postgres enums, both unique indexes (per-bidang + aggregate partial WHERE bidang_id IS NULL), and the two N:N tables; all four model modules import cleanly under WSL Python 3.11.
  </done>
</task>

<task type="auto">
  <name>Task 2: Recommendation + Notification + AuditLog models + Alembic 0005 (recommendation+notification) + Alembic 0006 (audit_log) + indexes</name>
  <files>
    backend/app/models/recommendation.py,
    backend/app/models/notification.py,
    backend/app/models/audit_log.py,
    backend/alembic/versions/20260513_110000_0005_recommendation_notification.py,
    backend/alembic/versions/20260513_120000_0006_audit_log.py
  </files>
  <action>
    Same enum strategy (Python StrEnum + Postgres ENUM with `create_type=False` referenced from the migration). Same audit cols + soft delete on `recommendation` only — `notification` and `audit_log` are append-only-ish entities where soft delete doesn't apply.

    1. `backend/app/models/recommendation.py`:
       ```python
       class RecommendationStatus(str, enum.Enum):
           OPEN = "open"; IN_PROGRESS = "in_progress"
           PENDING_REVIEW = "pending_review"; CLOSED = "closed"
           CARRIED_OVER = "carried_over"

       class RecommendationSeverity(str, enum.Enum):
           LOW = "low"; MEDIUM = "medium"; HIGH = "high"; CRITICAL = "critical"

       class Recommendation(Base):
           __tablename__ = "recommendation"
           __table_args__ = (
               CheckConstraint("progress_percent BETWEEN 0 AND 100", name="ck_rec_progress"),
           )
           id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
           source_assessment_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("assessment_session.id", ondelete="RESTRICT"), nullable=False)
           source_periode_id:    Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("periode.id",            ondelete="RESTRICT"), nullable=False)
           target_periode_id:    Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("periode.id",            ondelete="RESTRICT"), nullable=False)
           carried_from_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("recommendation.id",   ondelete="SET NULL"), nullable=True)
           carried_to_id:   Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("recommendation.id",   ondelete="SET NULL"), nullable=True)
           status:   Mapped[RecommendationStatus]   = mapped_column(SAEnum(RecommendationStatus,   name="recommendation_status",   values_callable=lambda e: [m.value for m in e], create_type=False), nullable=False, server_default=text("'open'::recommendation_status"))
           severity: Mapped[RecommendationSeverity] = mapped_column(SAEnum(RecommendationSeverity, name="recommendation_severity", values_callable=lambda e: [m.value for m in e], create_type=False), nullable=False)
           deskripsi: Mapped[str] = mapped_column(Text, nullable=False)
           action_items: Mapped[list] = mapped_column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
           progress_percent: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
           progress_notes:   Mapped[str | None] = mapped_column(Text, nullable=True)
           asesor_close_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
           closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
           closed_by: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
           # standard audit cols + deleted_at
       ```

    2. `backend/app/models/notification.py`:
       ```python
       class NotificationType(str, enum.Enum):
           ASSESSMENT_DUE = "assessment_due"
           REVIEW_PENDING = "review_pending"
           RECOMMENDATION_ASSIGNED = "recommendation_assigned"
           DEADLINE_APPROACHING = "deadline_approaching"
           PERIODE_CLOSED = "periode_closed"
           SYSTEM_ANNOUNCEMENT = "system_announcement"

       class Notification(Base):
           __tablename__ = "notification"
           id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
           user_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
           type: Mapped[NotificationType] = mapped_column(SAEnum(NotificationType, name="notification_type", values_callable=lambda e: [m.value for m in e], create_type=False), nullable=False)
           title: Mapped[str] = mapped_column(String(255), nullable=False)
           body: Mapped[str] = mapped_column(Text, nullable=False)
           payload: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
           read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
           created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"), nullable=False)
       ```

    3. `backend/app/models/audit_log.py`:
       ```python
       class AuditLog(Base):
           __tablename__ = "audit_log"
           id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
           user_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
           action: Mapped[str] = mapped_column(Text, nullable=False)
           entity_type: Mapped[str | None] = mapped_column(Text, nullable=True)
           entity_id:   Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)   # NOT a FK — entity may be soft-deleted later
           before_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
           after_data:  Mapped[dict | None] = mapped_column(JSONB, nullable=True)
           ip_address:  Mapped[str | None] = mapped_column(INET, nullable=True)
           user_agent:  Mapped[str | None] = mapped_column(Text, nullable=True)
           created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"), nullable=False)
       ```
       `entity_id` is intentionally NOT an FK — DEC-T6-002 retention is forever, so audit rows must outlive any cascade-deleted entity.

    4. `backend/alembic/versions/20260513_110000_0005_recommendation_notification.py`:
       ```python
       revision = "0005_recommendation_notification"
       down_revision = "0004_periode_and_sessions"

       def upgrade():
           op.execute("CREATE TYPE recommendation_status AS ENUM ('open','in_progress','pending_review','closed','carried_over')")
           op.execute("CREATE TYPE recommendation_severity AS ENUM ('low','medium','high','critical')")
           op.execute("CREATE TYPE notification_type AS ENUM ('assessment_due','review_pending','recommendation_assigned','deadline_approaching','periode_closed','system_announcement')")

           op.create_table(
               "recommendation",
               sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("uuid_generate_v4()"), primary_key=True),
               sa.Column("source_assessment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("assessment_session.id", ondelete="RESTRICT"), nullable=False),
               sa.Column("source_periode_id",    postgresql.UUID(as_uuid=True), sa.ForeignKey("periode.id",            ondelete="RESTRICT"), nullable=False),
               sa.Column("target_periode_id",    postgresql.UUID(as_uuid=True), sa.ForeignKey("periode.id",            ondelete="RESTRICT"), nullable=False),
               sa.Column("carried_from_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("recommendation.id", ondelete="SET NULL"), nullable=True),
               sa.Column("carried_to_id",   postgresql.UUID(as_uuid=True), sa.ForeignKey("recommendation.id", ondelete="SET NULL"), nullable=True),
               sa.Column("status",   postgresql.ENUM(name="recommendation_status",   create_type=False), nullable=False, server_default=sa.text("'open'::recommendation_status")),
               sa.Column("severity", postgresql.ENUM(name="recommendation_severity", create_type=False), nullable=False),
               sa.Column("deskripsi", sa.Text, nullable=False),
               sa.Column("action_items", postgresql.JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")),
               sa.Column("progress_percent", sa.Integer, nullable=False, server_default=sa.text("0")),
               sa.Column("progress_notes",   sa.Text, nullable=True),
               sa.Column("asesor_close_notes", sa.Text, nullable=True),
               sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
               sa.Column("closed_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
               sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
               sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
               sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
               sa.Column("updated_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
               sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
               sa.CheckConstraint("progress_percent BETWEEN 0 AND 100", name="ck_rec_progress"),
           )
           op.create_index("ix_rec_source_assessment", "recommendation", ["source_assessment_id"])
           op.create_index("ix_rec_target_periode",    "recommendation", ["target_periode_id"])
           op.create_index("ix_rec_status",            "recommendation", ["status"])
           op.create_index("ix_rec_carried_chain",     "recommendation", ["carried_from_id", "carried_to_id"])

           op.create_table(
               "notification",
               sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("uuid_generate_v4()"), primary_key=True),
               sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
               sa.Column("type", postgresql.ENUM(name="notification_type", create_type=False), nullable=False),
               sa.Column("title", sa.String(255), nullable=False),
               sa.Column("body", sa.Text, nullable=False),
               sa.Column("payload", postgresql.JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
               sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
               sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
           )
           # Unread-first ordering: NULLS FIRST on read_at, then created_at DESC
           op.execute("CREATE INDEX ix_notif_user_unread ON notification (user_id, read_at NULLS FIRST, created_at DESC)")

       def downgrade():
           op.drop_index("ix_notif_user_unread", table_name="notification")
           op.drop_table("notification")
           op.drop_index("ix_rec_carried_chain", table_name="recommendation")
           op.drop_index("ix_rec_status",        table_name="recommendation")
           op.drop_index("ix_rec_target_periode", table_name="recommendation")
           op.drop_index("ix_rec_source_assessment", table_name="recommendation")
           op.drop_table("recommendation")
           op.execute("DROP TYPE IF EXISTS notification_type")
           op.execute("DROP TYPE IF EXISTS recommendation_severity")
           op.execute("DROP TYPE IF EXISTS recommendation_status")
       ```

    5. `backend/alembic/versions/20260513_120000_0006_audit_log.py`:
       ```python
       revision = "0006_audit_log"
       down_revision = "0005_recommendation_notification"

       def upgrade():
           op.create_table(
               "audit_log",
               sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("uuid_generate_v4()"), primary_key=True),
               sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
               sa.Column("action",      sa.Text, nullable=False),
               sa.Column("entity_type", sa.Text, nullable=True),
               sa.Column("entity_id",   postgresql.UUID(as_uuid=True), nullable=True),     # NOT a FK
               sa.Column("before_data", postgresql.JSONB, nullable=True),
               sa.Column("after_data",  postgresql.JSONB, nullable=True),
               sa.Column("ip_address",  postgresql.INET, nullable=True),
               sa.Column("user_agent",  sa.Text, nullable=True),
               sa.Column("created_at",  sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
           )
           # DEC-T6-002 three indexes verbatim
           op.execute("CREATE INDEX ix_audit_user_created    ON audit_log (user_id, created_at DESC)")
           op.execute("CREATE INDEX ix_audit_entity_created  ON audit_log (entity_type, entity_id, created_at DESC)")
           op.execute("CREATE INDEX ix_audit_created_desc    ON audit_log (created_at DESC)")

       def downgrade():
           op.execute("DROP INDEX IF EXISTS ix_audit_created_desc")
           op.execute("DROP INDEX IF EXISTS ix_audit_entity_created")
           op.execute("DROP INDEX IF EXISTS ix_audit_user_created")
           op.drop_table("audit_log")
       ```

    Commit messages: one per model+migration pair — `feat(02-01): recommendation + notification + alembic 0005` and `feat(02-01): audit_log + alembic 0006 (DEC-T6-002 three indexes)`.
  </action>
  <verify>
    <automated>
      pwsh -NoProfile -Command "
        $files = 'backend/app/models/recommendation.py','backend/app/models/notification.py','backend/app/models/audit_log.py','backend/alembic/versions/20260513_110000_0005_recommendation_notification.py','backend/alembic/versions/20260513_120000_0006_audit_log.py';
        foreach ($f in $files) { if (-not (Test-Path $f)) { Write-Output ('missing: ' + $f); exit 1 } };
        # Recommendation: all five status values present verbatim (DEC-T4-003)
        $r = Get-Content 'backend/app/models/recommendation.py' -Raw;
        foreach ($v in 'open','in_progress','pending_review','closed','carried_over') {
          if ($r -notmatch ('\"' + $v + '\"')) { Write-Output ('DEC-T4-003: missing status ' + $v); exit 2 }
        };
        # Carry-over self-FK (DEC-T4-004)
        if ($r -notmatch 'carried_from_id') { exit 3 };
        if ($r -notmatch 'carried_to_id')   { exit 4 };
        # action_items JSONB
        if ($r -notmatch 'action_items') { exit 5 };
        if ($r -notmatch 'JSONB') { Write-Output 'action_items must be JSONB'; exit 6 };
        # Notification: six types verbatim (DEC-T5-003)
        $n = Get-Content 'backend/app/models/notification.py' -Raw;
        foreach ($v in 'assessment_due','review_pending','recommendation_assigned','deadline_approaching','periode_closed','system_announcement') {
          if ($n -notmatch ('\"' + $v + '\"')) { Write-Output ('DEC-T5-003: missing notif type ' + $v); exit 7 }
        };
        # AuditLog: before_data + after_data JSONB + INET ip + user_agent (DEC-T6-001)
        $al = Get-Content 'backend/app/models/audit_log.py' -Raw;
        foreach ($f in 'before_data','after_data','ip_address','user_agent','entity_type','entity_id','action','user_id') {
          if ($al -notmatch $f) { Write-Output ('DEC-T6-001: missing field ' + $f); exit 8 }
        };
        if ($al -notmatch 'INET') { Write-Output 'ip_address must be INET'; exit 9 };
        # Migrations chain on prior
        $m5 = Get-Content 'backend/alembic/versions/20260513_110000_0005_recommendation_notification.py' -Raw;
        if ($m5 -notmatch 'down_revision\s*=\s*\"0004_periode_and_sessions\"') { exit 10 };
        if ($m5 -notmatch 'revision\s*=\s*\"0005_recommendation_notification\"') { exit 11 };
        $m6 = Get-Content 'backend/alembic/versions/20260513_120000_0006_audit_log.py' -Raw;
        if ($m6 -notmatch 'down_revision\s*=\s*\"0005_recommendation_notification\"') { exit 12 };
        if ($m6 -notmatch 'revision\s*=\s*\"0006_audit_log\"') { exit 13 };
        # DEC-T6-002 three indexes
        if ($m6 -notmatch 'ix_audit_user_created')   { Write-Output 'DEC-T6-002: index (user_id, created_at) missing'; exit 14 };
        if ($m6 -notmatch 'ix_audit_entity_created') { Write-Output 'DEC-T6-002: index (entity_type, entity_id, created_at) missing'; exit 15 };
        if ($m6 -notmatch 'ix_audit_created_desc')   { Write-Output 'DEC-T6-002: index (created_at DESC) missing'; exit 16 };
        # Import smoke
        wsl -d Ubuntu-22.04 -- bash -lc 'cd /mnt/c/Users/ANUNNAKI/projects/PULSE/backend && python3.11 -c \"from app.models.recommendation import Recommendation, RecommendationStatus, RecommendationSeverity; from app.models.notification import Notification, NotificationType; from app.models.audit_log import AuditLog; print(Recommendation.__tablename__, Notification.__tablename__, AuditLog.__tablename__)\"' 2>&1 | Out-String | Write-Output
        if ($LASTEXITCODE -ne 0) { Write-Output 'model import smoke failed'; exit 17 };
        Write-Output 'pass'
      "
    </automated>
  </verify>
  <done>
    Three models exist with verbatim enum values; Alembic 0005 chains off 0004 and creates 3 ENUMs + recommendation + notification + indexes; 0006 chains off 0005 and creates audit_log with DEC-T6-002's three indexes verbatim; all three model files import cleanly.
  </done>
</task>

<task type="auto">
  <name>Task 3: Pydantic schemas + migration smoke test + model import smoke test (Wave 0 test bootstrap for Phase 2)</name>
  <files>
    backend/app/schemas/periode.py,
    backend/app/schemas/assessment.py,
    backend/app/schemas/recommendation.py,
    backend/app/schemas/notification.py,
    backend/app/schemas/audit.py,
    backend/tests/test_phase2_models_import.py,
    backend/tests/test_phase2_migrations.py
  </files>
  <action>
    All schemas use `ConfigDict(extra="forbid")` (DEC §V5 hardening) and Pydantic v2 idioms only — no v1 `@validator`.

    1. `backend/app/schemas/periode.py`:
       ```python
       from __future__ import annotations
       from datetime import date, datetime
       from typing import Literal
       from uuid import UUID
       from pydantic import BaseModel, ConfigDict, Field

       PeriodeStatusLit = Literal["draft","aktif","self_assessment","asesmen","finalisasi","closed"]

       class PeriodeCreate(BaseModel):
           model_config = ConfigDict(extra="forbid")
           tahun: int = Field(ge=2024, le=2099)
           triwulan: int = Field(ge=1, le=4)
           semester: int = Field(ge=1, le=2)
           nama: str = Field(min_length=1, max_length=255)
           tanggal_buka: date | None = None
           tanggal_tutup: date | None = None

       class PeriodeUpdate(BaseModel):
           model_config = ConfigDict(extra="forbid")
           nama: str | None = Field(default=None, min_length=1, max_length=255)
           tanggal_buka: date | None = None
           tanggal_tutup: date | None = None

       class PeriodeTransitionRequest(BaseModel):
           model_config = ConfigDict(extra="forbid")
           target_state: PeriodeStatusLit
           # Required on rollback (DEC-T1-002 mandatory reason >= 20 chars) — router validates the >=20 rule
           # because the validator needs to know the CURRENT state.
           reason: str | None = Field(default=None, max_length=2000)

       class PeriodePublic(BaseModel):
           model_config = ConfigDict(extra="forbid", from_attributes=True)
           id: UUID
           tahun: int
           triwulan: int
           semester: int
           nama: str
           status: PeriodeStatusLit
           tanggal_buka: date | None
           tanggal_tutup: date | None
           created_at: datetime
           updated_at: datetime
       ```

    2. `backend/app/schemas/assessment.py`:
       ```python
       from __future__ import annotations
       from datetime import datetime
       from decimal import Decimal
       from typing import Literal
       from uuid import UUID
       from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator

       SessionStateLit = Literal["draft","submitted","approved","overridden","revision_requested","abandoned"]

       class AssessmentSelfAssessmentPatch(BaseModel):
           """PIC auto-save / save-draft body. Partial — all fields optional."""
           model_config = ConfigDict(extra="forbid")
           payload: dict | None = None                     # JSONB partial — server merges
           realisasi: Decimal | None = None
           target: Decimal | None = None
           catatan_pic: str | None = Field(default=None, max_length=10_000)
           link_eviden: HttpUrl | None = None              # URL only — REQ-no-evidence-upload

       class AssessmentSubmit(BaseModel):
           model_config = ConfigDict(extra="forbid")
           # Empty body — server validates submit gate (DEC-T2-004)

       class InlineRecommendationCreate(BaseModel):
           """Embeddable variant — source_assessment_id is supplied by the router from the path."""
           model_config = ConfigDict(extra="forbid")
           severity: Literal["low","medium","high","critical"]
           deskripsi: str = Field(min_length=10, max_length=10_000)
           action_items: list["ActionItem"] = Field(min_length=1)
           target_periode_id: UUID

       class AsesorReview(BaseModel):
           model_config = ConfigDict(extra="forbid")
           decision: Literal["approve","override","request_revision"]
           nilai_final: Decimal | None = None
           catatan_asesor: str | None = Field(default=None, max_length=10_000)
           inline_recommendations: list[InlineRecommendationCreate] | None = None

           @model_validator(mode="after")
           def _check_override_constraints(self):
               # DEC-T3-001: override requires nilai_final + catatan_asesor.length >= 20
               if self.decision == "override":
                   if self.nilai_final is None:
                       raise ValueError("nilai_final is required when decision='override'")
                   if not self.catatan_asesor or len(self.catatan_asesor) < 20:
                       raise ValueError("catatan_asesor must be >= 20 chars when decision='override'")
               elif self.decision == "approve":
                   # nilai_final is server-set from PIC's nilai — if provided, it MUST match (router checks)
                   pass
               elif self.decision == "request_revision":
                   # nilai_final stays NULL on revision_requested
                   if self.nilai_final is not None:
                       raise ValueError("nilai_final must be omitted when decision='request_revision'")
               return self

       class AssessmentSessionPublic(BaseModel):
           model_config = ConfigDict(extra="forbid", from_attributes=True)
           id: UUID
           periode_id: UUID
           indikator_id: UUID
           bidang_id: UUID | None
           state: SessionStateLit
           payload: dict | None
           realisasi: Decimal | None
           target: Decimal | None
           pencapaian: Decimal | None
           nilai: Decimal | None
           nilai_final: Decimal | None
           catatan_pic: str | None
           catatan_asesor: str | None
           link_eviden: str | None
           submitted_at: datetime | None
           asesor_reviewed_at: datetime | None
           updated_at: datetime
       ```

    3. `backend/app/schemas/recommendation.py` — **RESEARCH §11.13 honored**: typed `List[ActionItem]`, no DB lookups in validators:
       ```python
       from __future__ import annotations
       from datetime import date, datetime
       from typing import Annotated, Literal
       from uuid import UUID
       from pydantic import BaseModel, ConfigDict, Field

       class ActionItem(BaseModel):
           model_config = ConfigDict(extra="forbid")
           action: Annotated[str, Field(min_length=1, max_length=2000)]
           deadline: date | None = None
           owner_user_id: UUID | None = None     # default-resolved in service layer (DEC-T4-001, RESEARCH §11.13)

       class RecommendationCreate(BaseModel):
           model_config = ConfigDict(extra="forbid")
           source_assessment_id: UUID
           severity: Literal["low","medium","high","critical"]
           deskripsi: Annotated[str, Field(min_length=10, max_length=10_000)]
           action_items: Annotated[list[ActionItem], Field(min_length=1)]
           target_periode_id: UUID

       class RecommendationProgressUpdate(BaseModel):
           model_config = ConfigDict(extra="forbid")
           progress_percent: Annotated[int, Field(ge=0, le=100)] | None = None
           progress_notes: str | None = Field(default=None, max_length=10_000)

       class RecommendationMarkCompleted(BaseModel):
           model_config = ConfigDict(extra="forbid")
           # Empty — only the route action matters

       class RecommendationVerifyClose(BaseModel):
           model_config = ConfigDict(extra="forbid")
           asesor_close_notes: str = Field(min_length=1, max_length=10_000)

       class RecommendationPublic(BaseModel):
           model_config = ConfigDict(extra="forbid", from_attributes=True)
           id: UUID
           source_assessment_id: UUID
           source_periode_id: UUID
           target_periode_id: UUID
           carried_from_id: UUID | None
           carried_to_id: UUID | None
           status: Literal["open","in_progress","pending_review","closed","carried_over"]
           severity: Literal["low","medium","high","critical"]
           deskripsi: str
           action_items: list[ActionItem]
           progress_percent: int
           progress_notes: str | None
           asesor_close_notes: str | None
           closed_at: datetime | None
           created_at: datetime
           updated_at: datetime
       ```

    4. `backend/app/schemas/notification.py`:
       ```python
       from __future__ import annotations
       from datetime import datetime
       from typing import Literal
       from uuid import UUID
       from pydantic import BaseModel, ConfigDict

       NotificationTypeLit = Literal[
           "assessment_due","review_pending","recommendation_assigned",
           "deadline_approaching","periode_closed","system_announcement",
       ]

       class NotificationPublic(BaseModel):
           model_config = ConfigDict(extra="forbid", from_attributes=True)
           id: UUID
           user_id: UUID
           type: NotificationTypeLit
           title: str
           body: str
           payload: dict
           read_at: datetime | None
           created_at: datetime
       ```

    5. `backend/app/schemas/audit.py`:
       ```python
       from __future__ import annotations
       from datetime import datetime
       from uuid import UUID
       from pydantic import BaseModel, ConfigDict

       class AuditLogPublic(BaseModel):
           model_config = ConfigDict(extra="forbid", from_attributes=True)
           id: UUID
           user_id: UUID | None
           action: str
           entity_type: str | None
           entity_id: UUID | None
           before_data: dict | None
           after_data: dict | None
           ip_address: str | None
           user_agent: str | None
           created_at: datetime
       ```

    6. `backend/tests/test_phase2_models_import.py`:
       ```python
       """Wave 0 — Phase 2 models + schemas import smoke."""
       import importlib

       def test_phase2_models_import():
           # Every new model module must import via auto-discovery
           for mod in [
               "app.models.periode",
               "app.models.assessment_session",
               "app.models.assessment_session_bidang",
               "app.models.indikator_applicable_bidang",
               "app.models.recommendation",
               "app.models.notification",
               "app.models.audit_log",
           ]:
               importlib.import_module(mod)

       def test_phase2_schemas_import():
           for mod in [
               "app.schemas.periode",
               "app.schemas.assessment",
               "app.schemas.recommendation",
               "app.schemas.notification",
               "app.schemas.audit",
           ]:
               importlib.import_module(mod)

       def test_action_item_extra_forbid():
           from app.schemas.recommendation import ActionItem
           import pydantic
           try:
               ActionItem(action="do x", unknown_field="boom")
           except pydantic.ValidationError as e:
               assert "extra_forbidden" in str(e).lower() or "unknown" in str(e).lower() or "extra inputs" in str(e).lower()
               return
           raise AssertionError("extra='forbid' not enforced on ActionItem")

       def test_asesor_review_override_min20_chars():
           from app.schemas.assessment import AsesorReview
           import pydantic
           from decimal import Decimal
           # 19 chars < 20 — must fail (DEC-T3-001)
           try:
               AsesorReview(decision="override", nilai_final=Decimal("85.50"), catatan_asesor="x" * 19)
           except pydantic.ValidationError:
               pass
           else:
               raise AssertionError("DEC-T3-001: override <20 chars must reject")
           # 20 chars + nilai_final → OK
           AsesorReview(decision="override", nilai_final=Decimal("85.50"), catatan_asesor="x" * 20)
           # override without nilai_final → must fail
           try:
               AsesorReview(decision="override", catatan_asesor="x" * 25)
           except pydantic.ValidationError:
               pass
           else:
               raise AssertionError("DEC-T3-001: override without nilai_final must reject")

       def test_recommendation_action_items_min_length():
           from app.schemas.recommendation import RecommendationCreate
           import pydantic
           from uuid import uuid4
           try:
               RecommendationCreate(
                   source_assessment_id=uuid4(),
                   severity="medium",
                   deskripsi="x" * 10,
                   action_items=[],
                   target_periode_id=uuid4(),
               )
           except pydantic.ValidationError:
               pass
           else:
               raise AssertionError("action_items must reject empty list")
       ```

    7. `backend/tests/test_phase2_migrations.py` — **B-06 real migration smoke**: spins an ephemeral Postgres via docker on host port 5499 (mirror Plan 01-05 SUMMARY ephemeral test stack pattern). Skipped if docker daemon unreachable from the WSL bridge (the no-stack fallback is the model-import smoke above).
       ```python
       """B-06 real migration smoke. Runs `alembic upgrade head` against an ephemeral
       Postgres and verifies the seven Phase 2 tables exist plus the three audit indexes.

       Skipped when docker is unreachable from WSL — Plan 02-06 (E2E) provides the
       compose-driven coverage in that case.
       """
       import os
       import subprocess
       import time
       import pytest

       DOCKER_CMD = ["wsl", "-d", "Ubuntu-22.04", "--", "docker"]
       PG_NAME = "pulse-test-pg-phase2"
       PG_PORT = "5499"
       PG_PASS = "phase2test"

       def _docker_available() -> bool:
           try:
               r = subprocess.run([*DOCKER_CMD, "info"], capture_output=True, timeout=10)
               return r.returncode == 0
           except Exception:
               return False

       pytestmark = pytest.mark.skipif(not _docker_available(), reason="docker unreachable; rely on Plan 02-06 e2e")

       @pytest.fixture(scope="module")
       def ephemeral_pg():
           subprocess.run([*DOCKER_CMD, "rm", "-f", PG_NAME], capture_output=True)
           r = subprocess.run([
               *DOCKER_CMD, "run", "-d", "--name", PG_NAME,
               "-e", f"POSTGRES_PASSWORD={PG_PASS}",
               "-e", "POSTGRES_DB=pulse_test",
               "-e", "POSTGRES_USER=pulse",
               "-p", f"{PG_PORT}:5432",
               "pgvector/pgvector:pg16",
           ], capture_output=True)
           assert r.returncode == 0, r.stderr.decode()
           # Wait for ready
           for _ in range(30):
               ready = subprocess.run([*DOCKER_CMD, "exec", PG_NAME, "pg_isready", "-U", "pulse"], capture_output=True)
               if ready.returncode == 0:
                   break
               time.sleep(1)
           # uuid-ossp extension for migrations
           subprocess.run([*DOCKER_CMD, "exec", PG_NAME, "psql", "-U", "pulse", "-d", "pulse_test", "-c", "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";"], capture_output=True)
           yield f"postgresql+asyncpg://pulse:{PG_PASS}@127.0.0.1:{PG_PORT}/pulse_test"
           subprocess.run([*DOCKER_CMD, "rm", "-f", PG_NAME], capture_output=True)

       def test_alembic_upgrade_head_to_0006(ephemeral_pg, monkeypatch):
           monkeypatch.setenv("DATABASE_URL", ephemeral_pg)
           monkeypatch.setenv("POSTGRES_PASSWORD", PG_PASS)
           monkeypatch.setenv("POSTGRES_HOST", "127.0.0.1")
           monkeypatch.setenv("POSTGRES_PORT", PG_PORT)
           monkeypatch.setenv("POSTGRES_DB", "pulse_test")
           monkeypatch.setenv("POSTGRES_USER", "pulse")
           r = subprocess.run(["wsl","-d","Ubuntu-22.04","--","bash","-lc",
                               "cd /mnt/c/Users/ANUNNAKI/projects/PULSE/backend && alembic upgrade head"],
                              capture_output=True, text=True)
           assert r.returncode == 0, f"alembic failed: {r.stdout}\n{r.stderr}"
           # Verify the seven Phase-2 tables and three audit indexes exist
           q = subprocess.run([*DOCKER_CMD, "exec", PG_NAME, "psql", "-U", "pulse", "-d", "pulse_test", "-At", "-c",
                              "SELECT tablename FROM pg_tables WHERE schemaname='public' AND tablename IN "
                              "('periode','assessment_session','assessment_session_bidang','indikator_applicable_bidang','recommendation','notification','audit_log') ORDER BY 1"],
                              capture_output=True, text=True)
           assert "periode" in q.stdout and "assessment_session" in q.stdout and "audit_log" in q.stdout, q.stdout
           idx = subprocess.run([*DOCKER_CMD, "exec", PG_NAME, "psql", "-U", "pulse", "-d", "pulse_test", "-At", "-c",
                                "SELECT indexname FROM pg_indexes WHERE tablename='audit_log' ORDER BY 1"],
                                capture_output=True, text=True)
           for nm in ("ix_audit_user_created","ix_audit_entity_created","ix_audit_created_desc"):
               assert nm in idx.stdout, f"DEC-T6-002 index missing: {nm}\nGot: {idx.stdout}"
       ```

    Commit: `feat(02-01): Pydantic schemas + phase-2 model/migration smoke tests`.
  </action>
  <verify>
    <automated>
      pwsh -NoProfile -Command "
        $files = 'backend/app/schemas/periode.py','backend/app/schemas/assessment.py','backend/app/schemas/recommendation.py','backend/app/schemas/notification.py','backend/app/schemas/audit.py','backend/tests/test_phase2_models_import.py','backend/tests/test_phase2_migrations.py';
        foreach ($f in $files) { if (-not (Test-Path $f)) { Write-Output ('missing: ' + $f); exit 1 } };
        # extra=forbid everywhere (V5 hardening)
        foreach ($p in 'periode','assessment','recommendation','notification','audit') {
          $c = Get-Content ('backend/app/schemas/' + $p + '.py') -Raw
          if ($c -notmatch 'extra=\"forbid\"') { Write-Output ('schema ' + $p + '.py missing extra=forbid'); exit 2 }
        };
        # DEC-T3-001 server-side validator
        $a = Get-Content 'backend/app/schemas/assessment.py' -Raw;
        if ($a -notmatch 'model_validator') { Write-Output 'DEC-T3-001: model_validator missing on AsesorReview'; exit 3 };
        if ($a -notmatch '>= 20') { Write-Output 'DEC-T3-001: 20-char rule not enforced'; exit 4 };
        # RESEARCH §11.13: no DB lookups in validators (heuristic — schema files must not import AsyncSession or get_db)
        foreach ($p in 'periode','assessment','recommendation','notification','audit') {
          $c = Get-Content ('backend/app/schemas/' + $p + '.py') -Raw
          if ($c -match 'AsyncSession' -or $c -match 'get_db') {
            Write-Output ('RESEARCH §11.13 violation: schema ' + $p + '.py imports AsyncSession or get_db'); exit 5
          }
        };
        # Real pytest run on the unit-mode tests (no docker needed)
        wsl -d Ubuntu-22.04 -- bash -lc 'cd /mnt/c/Users/ANUNNAKI/projects/PULSE/backend && python3.11 -m pytest tests/test_phase2_models_import.py -x -q' 2>&1 | Out-String | Write-Output
        if ($LASTEXITCODE -ne 0) { Write-Output 'phase2 model+schema unit tests failed'; exit 6 };
        # No new multipart endpoints introduced by Phase 2 schemas
        wsl -d Ubuntu-22.04 -- bash -lc 'cd /mnt/c/Users/ANUNNAKI/projects/PULSE/backend && python3.11 -m pytest tests/test_no_upload_policy.py -x -q' 2>&1 | Out-String | Write-Output
        if ($LASTEXITCODE -ne 0) { Write-Output 'no-upload contract regressed'; exit 7 };
        Write-Output 'pass'
      "
    </automated>
  </verify>
  <done>
    All five Pydantic schema files exist with `extra='forbid'`; `AsesorReview` model_validator enforces DEC-T3-001 (override needs nilai_final + catatan_asesor >= 20 chars); no schema imports AsyncSession (RESEARCH §11.13); `test_phase2_models_import.py` passes (all seven model modules + five schema modules import cleanly + the four assertion-tests on extra='forbid', override-validator, and action_items min_length); the no-upload contract test still passes.
  </done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| HTTP client → FastAPI router | Untrusted JSON body crosses here — Pydantic + `extra='forbid'` is the parse-time gate |
| Application code → Postgres | Migrations write schema; FK + CHECK constraints are the runtime gate |
| Audit log row insert | Append-only — no UPDATE/DELETE path (enforced at router level in Plan 02-03) |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-02-01-T-01 | Tampering | Pydantic request schemas | mitigate | Every request schema declares `ConfigDict(extra='forbid')` — unknown keys raise 422 at parse time (V5). Verified by `test_action_item_extra_forbid`. |
| T-02-01-T-02 | Tampering | DEC-T3-001 override path | mitigate | `AsesorReview.@model_validator(mode='after')` enforces `len(catatan_asesor) >= 20 AND nilai_final is not None` when `decision=='override'`. Server-side; cannot be skipped by manipulating the client. Verified by `test_asesor_review_override_min20_chars`. |
| T-02-01-T-03 | Tampering | Pydantic validators with DB lookups | mitigate | RESEARCH §11.13 anti-pattern: validators are pure. ActionItem.owner_user_id stays `None` at parse time; service layer (Plan 02-02) resolves it. Verified by grep: no `AsyncSession`/`get_db` import in `app/schemas/*.py`. |
| T-02-01-I-01 | Info disclosure | audit_log.before_data containing PIC notes | accept | DEC-T6-001 documents this risk; `audit_log` reads are gated `require_role('super_admin')` only in Plan 02-03. Phase 6 may add an `auditor` role. |
| T-02-01-D-01 | DOS | Large `payload JSONB` on assessment_session | mitigate | Pydantic field `payload: dict` has no explicit cap, but nginx limits request body to 25 MB (Plan 01-02). Audit-log JSONB columns store deltas only (RESEARCH §10 + Pitfall 9), not full row dumps. |
| T-02-01-R-01 | Repudiation | Append-only audit_log | mitigate | Schema has no UPDATE / DELETE triggers; Plan 02-03 enforces no PATCH/DELETE routes on `/audit-logs`. No `deleted_at` column. |
| T-02-01-E-01 | EoP | Migration ordering | mitigate | Linear chain 0003 → 0004 → 0005 → 0006. FK targets exist before the referencing table is created (periode + assessment_session in 0004 → recommendation references them in 0005). |
</threat_model>

<verification>
After this plan executes, the following must hold:

1. `wsl -d Ubuntu-22.04 -- python3.11 -m pytest backend/tests/test_phase2_models_import.py -x -q` passes 4/4.
2. `wsl -d Ubuntu-22.04 -- python3.11 -m pytest backend/tests/test_no_upload_policy.py -x -q` still passes (no new multipart endpoints introduced).
3. All seven new model modules and five new schema modules import cleanly under WSL Python 3.11.
4. Alembic chain is linear: `head` revision is `0006_audit_log`; downgrade to `base` and re-upgrade succeeds (covered by `test_phase2_migrations.py` when docker is available, otherwise deferred to Plan 02-06 E2E).
5. No string `"siskonkin"` (any case) appears in any of the seventeen files this plan creates: `grep -ri 'siskonkin' backend/app/models/periode.py backend/app/models/assessment_session.py ... = 0`.
6. Auto-discovery still works: `from app.routers import api_router; from app.db.base import Base; print(sorted(Base.metadata.tables.keys()))` lists `audit_log, assessment_session, assessment_session_bidang, indikator_applicable_bidang, notification, periode, recommendation` plus the Phase-1 tables.
</verification>

<success_criteria>
- [ ] All seven new model files exist with verbatim CONTEXT.md enum values (DEC-T1-001..T6-002)
- [ ] All five new Pydantic schema files exist with `ConfigDict(extra='forbid')`
- [ ] `AsesorReview.@model_validator` enforces DEC-T3-001 (override needs nilai_final + catatan_asesor >= 20 chars)
- [ ] No schema imports `AsyncSession` or `get_db` (RESEARCH §11.13)
- [ ] Alembic chain 0003 → 0004 → 0005 → 0006 is linear; each `down_revision` matches the previous file's `revision` exactly
- [ ] DEC-T6-002 three indexes on `audit_log` are created verbatim: `(user_id, created_at DESC)`, `(entity_type, entity_id, created_at DESC)`, `(created_at DESC)`
- [ ] DEC-T1-003 aggregate sessions: partial unique index `uq_session_aggregate ... WHERE bidang_id IS NULL` is present
- [ ] `test_phase2_models_import.py` runs green (4/4 assertions)
- [ ] `test_no_upload_policy.py` still passes (no new multipart routes)
- [ ] No `aiosmtplib` / `celery` / `apscheduler` / `transitions` added to `pyproject.toml` (DEC-T5-001 + RESEARCH §11.11 + §5)
</success_criteria>

<output>
After completion, write `.planning/phases/02-assessment-workflow-pic-asesor/02-01-backend-schema-and-migrations-SUMMARY.md` using the template at `$HOME/.claude/get-shit-done/templates/summary.md`. Include the full enum value lists (so Plan 02-02 can grep them) and an explicit "auto-discovery confirmed" line.
</output>
