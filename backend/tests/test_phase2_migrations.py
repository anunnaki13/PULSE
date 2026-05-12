"""Static smoke tests for the Phase 2 Alembic chain.

The live Postgres migration path is covered by the compose/E2E suite. These
tests keep unit-mode fast while still catching broken chain metadata.
"""

from pathlib import Path


VERSIONS = Path(__file__).resolve().parents[1] / "alembic" / "versions"


def test_phase2_migration_chain_files_exist():
    for name in [
        "20260513_100000_0004_periode_and_sessions.py",
        "20260513_110000_0005_recommendation_notification.py",
        "20260513_120000_0006_audit_log.py",
    ]:
        assert (VERSIONS / name).exists()


def test_phase2_migration_chain_is_linear():
    m4 = (VERSIONS / "20260513_100000_0004_periode_and_sessions.py").read_text()
    m5 = (VERSIONS / "20260513_110000_0005_recommendation_notification.py").read_text()
    m6 = (VERSIONS / "20260513_120000_0006_audit_log.py").read_text()
    assert 'revision = "0004_periode_and_sessions"' in m4
    assert 'down_revision = "0003_master_data"' in m4
    assert 'revision = "0005_recommendation_notification"' in m5
    assert 'down_revision = "0004_periode_and_sessions"' in m5
    assert 'revision = "0006_audit_log"' in m6
    assert 'down_revision = "0005_recommendation_notification"' in m6


def test_audit_indexes_declared():
    m6 = (VERSIONS / "20260513_120000_0006_audit_log.py").read_text()
    for name in ["ix_audit_user_created", "ix_audit_entity_created", "ix_audit_created_desc"]:
        assert name in m6
