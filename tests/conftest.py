from __future__ import annotations

import json
from importlib import resources
from pathlib import Path

import pytest

from backMatterBuilder.profile import load_profile


@pytest.fixture
def fixture_dir() -> Path:
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def profile_dict(fixture_dir: Path) -> dict:
    raw = (fixture_dir / "profile_full.json").read_text(encoding="utf-8")
    return json.loads(raw)


@pytest.fixture
def profile_full(fixture_dir: Path):
    return load_profile(fixture_dir / "profile_full.json")


@pytest.fixture
def profile_minimal(fixture_dir: Path):
    return load_profile(fixture_dir / "profile_minimal.json")


@pytest.fixture
def profile_json_file(tmp_path: Path, profile_dict: dict) -> Path:
    path = tmp_path / "profile.json"
    path.write_text(json.dumps(profile_dict), encoding="utf-8")
    return path


@pytest.fixture
def sample_profile(profile_full):
    return profile_full
