import os
import subprocess
import sys

import pytest


@pytest.mark.parametrize(
    "module", ["mathutrice.app", "mathutrice.fonctions_python.main"]
)
def test_module_imports_on_its_own(module, tmp_path):
    env = {
        **os.environ,
        "AUTH_MODE": "dev",
        "SESSION_SECRET": "test",
        "DATABASE_URL": f"sqlite:///{tmp_path / 'test.db'}",
        "LLM_BASE_URL": "http://localhost",
        "LLM_API_KEY": "test",
        "LLM_MODEL": "test",
    }

    completed = subprocess.run(
        [sys.executable, "-c", f"import {module}"],
        env=env,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
