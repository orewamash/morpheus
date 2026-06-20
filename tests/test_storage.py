"""
tests/test_storage.py — Storage tests for Morpheus.
"""

from __future__ import annotations

import os
import time
from morpheus.storage import RunRecord, MorpheusStorage


def test_save_and_retrieve_run(tmp_path):
    """save_run() then get_run() must return a RunRecord with matching filepath."""
    db_file = tmp_path / "morpheus.db"
    storage = MorpheusStorage(db_path=str(db_file))

    record = RunRecord(
        run_id="",
        filepath="/path/to/test_script.py",
        timestamp=time.time(),
        mode="narrator",
        chapters="[]",
        narrations="[]",
        duration_ms=123.45,
        event_count=10,
        error="",
    )

    run_id = storage.save_run(record)
    assert run_id != ""

    retrieved = storage.get_run(run_id)
    assert retrieved.run_id == run_id
    assert retrieved.filepath == "/path/to/test_script.py"
    assert retrieved.mode == "narrator"
    assert retrieved.duration_ms == 123.45
    assert retrieved.event_count == 10


def test_list_runs_returns_correct_count(tmp_path):
    """After saving 5 runs, list_runs(limit=3) must return exactly 3 records."""
    db_file = tmp_path / "morpheus.db"
    storage = MorpheusStorage(db_path=str(db_file))

    for i in range(5):
        record = RunRecord(
            run_id=f"run-id-{i}",
            filepath=f"/path/to/script_{i}.py",
            timestamp=time.time() + i,
            mode="narrator",
            chapters="[]",
            narrations="[]",
            duration_ms=50.0,
            event_count=5,
            error="",
        )
        storage.save_run(record)

    runs = storage.list_runs(limit=3)
    assert len(runs) == 3

    # Check that they are ordered newest first (timestamp desc)
    # The last runs added have larger timestamps, so they should come first.
    assert runs[0].run_id == "run-id-4"
    assert runs[1].run_id == "run-id-3"
    assert runs[2].run_id == "run-id-2"


def test_db_created_at_path(tmp_path):
    """MorpheusStorage(db_path) must create the SQLite file at the given path."""
    db_file = tmp_path / "nested_dir" / "history.db"
    assert not db_file.exists()

    _ = MorpheusStorage(db_path=str(db_file))
    assert db_file.exists()
    assert os.path.isfile(db_file)
