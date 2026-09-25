import os
import subprocess
import sys

from sqlmodel import Session, create_engine, select

from mathutrice import models
from mathutrice.referentiel import REFERENTIEL


def start_and_stop_app(tmp_path, **env_overrides):
    """Runs the app's startup and shutdown in a fresh interpreter, returns its DB."""
    database_url = f"sqlite:///{tmp_path / 'test.db'}"
    env = {
        **os.environ,
        "AUTH_MODE": "dev",
        "SESSION_SECRET": "test",
        "DATABASE_URL": database_url,
        "LLM_BASE_URL": "http://localhost",
        "LLM_API_KEY": "test",
        "LLM_MODEL": "test",
        **env_overrides,
    }
    script = (
        "from fastapi.testclient import TestClient\n"
        "from mathutrice.app import app\n"
        "with TestClient(app):\n"
        "    pass\n"
    )

    completed = subprocess.run(
        [sys.executable, "-c", script], env=env, capture_output=True, text=True
    )

    assert completed.returncode == 0, completed.stderr
    return create_engine(database_url)


def test_startup_seeds_the_referentiel(tmp_path):
    engine = start_and_stop_app(tmp_path)

    with Session(engine) as session:
        keys = set(session.exec(select(models.Notion.referentiel_key)).all())
        codes = set(session.exec(select(models.Competence.referentiel_code)).all())

    assert keys == set(REFERENTIEL)
    assert codes == {
        c["code"] for n in REFERENTIEL.values() for c in n["competences"]
    }


def test_startup_in_dev_mode_seeds_one_user_per_role(tmp_path):
    engine = start_and_stop_app(tmp_path)

    with Session(engine) as session:
        roles = sorted(session.exec(select(models.User.role)).all())

    assert roles == ["Admin", "Student", "Teacher"]


def test_startup_in_entra_mode_seeds_no_user(tmp_path):
    engine = start_and_stop_app(
        tmp_path,
        AUTH_MODE="entra",
        CLIENT_ID="test",
        CLIENT_SECRET="test",
        TENANT_ID="test",
        REDIRECT_URL="http://localhost/auth",
        POST_LOGOUT_REDIRECT_URL="http://localhost/",
    )

    with Session(engine) as session:
        assert session.exec(select(models.User)).all() == []
