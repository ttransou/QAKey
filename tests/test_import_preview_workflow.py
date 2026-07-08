"""Workflow tests for spreadsheet import preview using a real XLSX fixture."""

from pathlib import Path

import pytest

from app import app


FIXTURES_DIR = Path(__file__).parent / "fixtures"
FIXTURE_PATH = Path(__file__).parent / "fixtures" / "import_20_qa_pairs.xlsx"


def _resolve_fixture_path() -> Path | None:
    if FIXTURE_PATH.exists():
        return FIXTURE_PATH

    candidates = sorted(FIXTURES_DIR.glob("*.xlsx"))
    if len(candidates) == 1:
        return candidates[0]

    return None


def test_import_preview_accepts_20_row_xlsx_fixture():
    """Validate importer behavior against a maintainer-provided 20-row workbook."""
    fixture_path = _resolve_fixture_path()
    if fixture_path is None:
        pytest.skip(
            "Place one workbook in tests/fixtures/ or use tests/fixtures/import_20_qa_pairs.xlsx"
        )

    client = app.test_client()

    with fixture_path.open("rb") as fh:
        response = client.post(
            "/api/records/import-preview",
            data={
                "default_status": "Draft",
                "default_contributor": "workflow-test",
                "default_tags": "imported|workflow",
                "file": (fh, fixture_path.name),
            },
            content_type="multipart/form-data",
        )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["errors"] == []
    assert payload["count"] == 20
    assert len(payload["records"]) == 20

    for record in payload["records"]:
        assert record["canonical_question"].strip()
        assert record["answer"].strip()
