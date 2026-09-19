import json
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

FIXTURE_PATH = pathlib.Path(__file__).parent / "fixtures" / "basemart.json"


@pytest.fixture(scope="session")
def base():
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))