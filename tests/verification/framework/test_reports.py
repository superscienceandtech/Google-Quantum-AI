import json
import math
from concurrent.futures import ThreadPoolExecutor

import pytest

from verification.framework.reports import write_immutable_json


def test_report_serializes_machine_readable(tmp_path):
    destination = tmp_path / "report.json"
    result = write_immutable_json(destination, {"status": "NOT_VERIFIED"})
    assert json.loads(result.read_text(encoding="utf-8")) == {"status": "NOT_VERIFIED"}


def test_existing_report_is_not_overwritten(tmp_path):
    destination = tmp_path / "report.json"
    write_immutable_json(destination, {"status": "PASS"})
    with pytest.raises(FileExistsError):
        write_immutable_json(destination, {"status": "FAIL"})


def test_nonfinite_json_rejected(tmp_path):
    destination = tmp_path / "report.json"
    with pytest.raises(ValueError):
        write_immutable_json(destination, {"value": math.nan})
    assert not destination.exists()


def test_concurrent_report_creation_is_exclusive(tmp_path):
    destination = tmp_path / "report.json"

    def create(index):
        try:
            return write_immutable_json(destination, {"index": index})
        except FileExistsError:
            return None

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(create, range(8)))

    assert sum(result is not None for result in results) == 1
    assert destination.exists()
